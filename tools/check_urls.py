#!/usr/bin/env python3
"""Check candidate business URLs without changing the prospecting ledger."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import socket
import ssl
import subprocess
import sys
import time
import unicodedata
from urllib.parse import urlsplit, urlunsplit

from site_assets import clean_url, fetch, ResponseLimitError

NAME_COLUMNS = ('empresa', 'nome_empresa', 'nome', 'business_name', 'name')
URL_COLUMNS = ('site_identificado', 'url_candidata', 'site', 'website', 'url', 'site_url')
ID_COLUMNS = ('id', 'identificador', 'empresa_id', 'job_id')
EXTRA_COLUMNS = ('url_original', 'url_final', 'status_url', 'http_status', 'motivo',
                 'identidade_correspondente', 'evidencia_resumida', 'verificado_em',
                 'tentativas', 'tempo_ms', 'encaminhamento', 'google_business_observado',
                 'presenca_social_observada', 'presenca_diretorio_observada',
                 'fonte_sinal', 'revisao_humana', 'reutilizado')
SIGNALS = {'sim', 'nao_observado', 'nao_verificado'}
ROUTES = {'confirmada': 'auditoria_visual_futura',
          'acessivel_inconclusiva': 'revisao_pendente',
          'falha_tecnica': 'avaliar_site_inoperante',
          'sem_url': 'avaliar_primeiro_site'}
PARKED = ('domain parked', 'parked domain', 'dominio estacionado', 'account suspended',
          'site suspended', 'conta suspensa', 'hosting suspended', 'website is unavailable',
          'this domain is for sale', 'dominio a venda', 'default web site page',
          '404 not found', '403 forbidden', 'page not found')
TRANSIENT = {'timeout', 'erro_conexao', 'http_502', 'http_503', 'http_504'}


def normalized(value):
    value = unicodedata.normalize('NFKD', value.casefold())
    return re.sub(r'[^a-z0-9]+', ' ', ''.join(c for c in value if not unicodedata.combining(c))).strip()


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript', 'svg'):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript', 'svg') and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def classify_html(content, company):
    parser = PageText()
    parser.feed(content.decode('utf-8', errors='replace') if isinstance(content, bytes) else content)
    text = normalized(' '.join(parser.parts))
    if any(normalized(marker) in text for marker in PARKED):
        return 'falha_tecnica', 'pagina_generica_hospedagem', 'Sinal de estacionamento, suspensão ou erro de hospedagem'
    if len(text) < 20:
        return 'falha_tecnica', 'html_sem_conteudo', 'HTML sem texto utilizável'
    name = normalized(company)
    if len(name) >= 5 and len(name.split()) >= 2 and f' {name} ' in f' {text} ':
        return 'confirmada', 'nome_correspondente', 'Nome da empresa encontrado no texto HTML'
    return 'acessivel_inconclusiva', 'identidade_nao_confirmada', 'HTML utilizável; nome completo não encontrado'


def display_url(url):
    """Keep audit URLs useful without copying credentials, queries or fragments."""
    if not url:
        return ''
    try:
        p = urlsplit(url)
        if p.scheme not in ('http', 'https') or not p.hostname:
            return ''
        host = p.hostname.lower()
        netloc = f'[{host}]' if ':' in host else host
        if p.port:
            netloc += f':{p.port}'
        return urlunsplit((p.scheme, netloc, p.path or '/', '', ''))
    except ValueError:
        return ''


def probe_direct(url, timeout, byte_limit, redirects):
    try:
        content, kind, final, status = fetch(
            url, limit=byte_limit, redirects=redirects, timeout=timeout,
            include_status=True, allow_http_errors=True,
            accepted_types={'text/html', 'application/xhtml+xml'}, forbid_downgrade=True,
            reject_credentials=True,
            headers={'Accept': 'text/html,application/xhtml+xml'})
        return {'content': content.decode('utf-8', errors='replace'), 'content_type': kind,
                'final': display_url(final), 'http_status': status}
    except socket.gaierror:
        return {'error': 'erro_dns'}
    except (socket.timeout, TimeoutError):
        return {'error': 'timeout'}
    except ssl.SSLError:
        return {'error': 'erro_tls'}
    except (ConnectionError, OSError):
        return {'error': 'erro_conexao'}
    except ValueError as exc:
        message = str(exc)
        if 'byte limit' in message:
            code = 'limite_bytes'
        elif 'Redirect' in message or 'redirect' in message:
            code = 'redirecionamento_bloqueado'
        elif 'Non-public' in message:
            code = 'destino_nao_publico'
        else:
            code = 'url_ou_destino_invalido'
        result = {'error': code}
        if isinstance(exc, ResponseLimitError):
            result['http_status'] = exc.status
            result['final'] = display_url(exc.url)
        return result


def probe_subprocess(url, timeout, byte_limit, redirects):
    payload = json.dumps({'url': url, 'timeout': timeout, 'byte_limit': byte_limit,
                          'redirects': redirects})
    try:
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--probe-worker'],
                                input=payload, text=True, capture_output=True,
                                timeout=timeout + 0.5, check=False)
    except subprocess.TimeoutExpired:
        return {'error': 'timeout'}
    except OSError:
        return {'error': 'erro_worker'}
    if result.returncode or not result.stdout:
        return {'error': 'erro_worker'}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {'error': 'erro_worker'}


def verify(url, company, *, timeout=8, byte_limit=262144, redirects=4,
           retries=1, probe=probe_subprocess):
    started = time.monotonic()
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    original = display_url(url)
    base = {'url_original': original, 'url_final': '', 'http_status': '',
            'verificado_em': stamp, 'tentativas': 0}
    if not url or not url.strip():
        base.update(status_url='sem_url', motivo='sem_url', identidade_correspondente='nao_verificada',
                    evidencia_resumida='Nenhuma URL candidata', tentativas=0)
    else:
        try:
            parts = urlsplit(url.strip())
            if parts.username or parts.password:
                raise ValueError('credentials')
            target = clean_url(url.strip())
        except ValueError:
            base.update(status_url='falha_tecnica', motivo='url_invalida',
                        identidade_correspondente='nao_verificada',
                        evidencia_resumida='URL inválida ou com credenciais')
        else:
            for attempt in range(1, retries + 2):
                response = probe(target, timeout, byte_limit, redirects)
                base['tentativas'] = attempt
                code = response.get('http_status')
                error = response.get('error') or (f'http_{code}' if code != 200 else '')
                if error in TRANSIENT and attempt <= retries:
                    continue
                base['url_final'] = response.get('final', '')
                base['http_status'] = code or ''
                if error:
                    base.update(status_url='falha_tecnica', motivo=error,
                                identidade_correspondente='nao_verificada',
                                evidencia_resumida=f'Falha técnica: {error}')
                elif response.get('content_type', '').split(';', 1)[0].strip().lower() not in ('text/html', 'application/xhtml+xml'):
                    base.update(status_url='falha_tecnica', motivo='conteudo_nao_html',
                                identidade_correspondente='nao_verificada',
                                evidencia_resumida='Resposta não contém HTML')
                else:
                    status, reason, evidence = classify_html(response.get('content', ''), company)
                    base.update(status_url=status, motivo=reason,
                                identidade_correspondente='sim' if status == 'confirmada' else 'nao_verificada',
                                evidencia_resumida=evidence)
                break
    base['encaminhamento'] = ROUTES[base['status_url']]
    base['tempo_ms'] = round((time.monotonic() - started) * 1000)
    return base


def column(fields, choice, aliases, label):
    if choice:
        if choice not in fields:
            raise ValueError(f'Coluna {label} não encontrada: {choice}')
        return choice
    found = next((name for name in aliases if name in fields), None)
    if found is None:
        raise ValueError(f'Coluna {label} não encontrada; use --{label}-column')
    return found


def run(args, probe=probe_subprocess):
    source = Path(args.input)
    output = Path(args.output)
    report = Path(args.report)
    if source.resolve() in (output.resolve(), report.resolve()) or output.resolve() == report.resolve():
        raise ValueError('Entrada, CSV de saída e JSON devem ter caminhos distintos')
    with source.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        name_col = column(fields, args.name_column, NAME_COLUMNS, 'name')
        url_col = column(fields, args.url_column, URL_COLUMNS, 'url')
        if args.id_column:
            column(fields, args.id_column, ID_COLUMNS, 'id')
        rows = list(reader)
    cache = {}
    reuse_hours = getattr(args, 'reuse_hours', 24)
    if reuse_hours and output.exists():
        with output.open(newline='', encoding='utf-8-sig') as handle:
            for old in csv.DictReader(handle):
                if old.get('status_url') not in ('confirmada', 'acessivel_inconclusiva'):
                    continue
                try:
                    age = (datetime.now(timezone.utc) - datetime.fromisoformat(old['verificado_em'])).total_seconds()
                except (KeyError, ValueError):
                    continue
                if 0 <= age <= reuse_hours * 3600:
                    raw = (old.get(url_col) or '').strip()
                    try:
                        parts = urlsplit(raw)
                        key = raw if parts.username or parts.password else clean_url(raw) if raw else ''
                    except ValueError:
                        key = raw
                    cache[(key, old.get(name_col) or '')] = old
    for row in rows:
        for signal in ('google_business_observado', 'presenca_social_observada', 'presenca_diretorio_observada'):
            if row.get(signal) and row[signal] not in SIGNALS:
                raise ValueError(f'Valor inválido em {signal}; use sim, nao_observado ou nao_verificado')
    started = time.monotonic()
    keys = []
    for row in rows:
        raw = (row.get(url_col) or '').strip()
        try:
            parts = urlsplit(raw)
            key = raw if parts.username or parts.password else clean_url(raw) if raw else ''
        except ValueError:
            key = raw
        keys.append(key)
    unique = {}
    for key, row in zip(keys, rows):
        if key:
            unique.setdefault(key, row.get(name_col) or '')
    reused = {}
    for key, name in unique.items():
        old = cache.get((key, name))
        if old:
            reused[key] = {field: old.get(field, '') for field in EXTRA_COLUMNS}
            reused[key]['reutilizado'] = 'sim'
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {key: pool.submit(verify, key, name, timeout=args.timeout,
                                    byte_limit=args.byte_limit, redirects=args.redirects,
                                    retries=args.retries, probe=probe)
                   for key, name in unique.items() if key not in reused}
        results = {**reused, **{key: future.result() for key, future in futures.items()}}
    enriched = []
    for row, key in zip(rows, keys):
        result = dict(results[key]) if key else verify('', row.get(name_col) or '', probe=probe)
        result.setdefault('reutilizado', 'nao')
        if key and (row.get(name_col) or '') != unique[key] and result['status_url'] in ('confirmada', 'acessivel_inconclusiva'):
            # One fetch per URL; evaluate the same returned HTML against each company's name.
            # A repeated URL cannot automatically confirm a different business.
            result.update(status_url='acessivel_inconclusiva', motivo='url_compartilhada',
                          identidade_correspondente='nao_verificada',
                          evidencia_resumida='URL compartilhada; identidade requer revisão',
                          encaminhamento='revisao_pendente')
        result['url_original'] = display_url(row.get(url_col) or '')
        merged = dict(row)
        merged.update(result)
        for signal in ('google_business_observado', 'presenca_social_observada', 'presenca_diretorio_observada'):
            merged[signal] = row.get(signal) or 'nao_verificado'
        merged['fonte_sinal'] = row.get('fonte_sinal') or ''
        merged['revisao_humana'] = row.get('revisao_humana') or 'pendente'
        enriched.append(merged)
    out_fields = list(dict.fromkeys(fields + list(EXTRA_COLUMNS)))
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(enriched)
    counts = {state: sum(row['status_url'] == state for row in enriched) for state in ROUTES}
    errors = {}
    for row in enriched:
        if row['status_url'] == 'falha_tecnica':
            errors[row['motivo']] = errors.get(row['motivo'], 0) + 1
    summary = {'entrada': str(source), 'saida_csv': str(output), 'total': len(enriched),
               'urls_unicas': len(unique), 'urls_reutilizadas': len(reused),
               'contagens': counts, 'erros': errors,
               'tempo_total_ms': round((time.monotonic() - started) * 1000)}
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return summary


def main():
    if sys.argv[1:] == ['--probe-worker']:
        payload = json.load(sys.stdin)
        print(json.dumps(probe_direct(**payload)))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--name-column')
    parser.add_argument('--url-column')
    parser.add_argument('--id-column')
    parser.add_argument('--timeout', type=float, default=8)
    parser.add_argument('--workers', type=int, default=5)
    parser.add_argument('--retries', type=int, default=1)
    parser.add_argument('--redirects', type=int, default=4)
    parser.add_argument('--byte-limit', type=int, default=262144)
    parser.add_argument('--reuse-hours', type=float, default=24,
                        help='Reutilizar resultados acessíveis recentes do CSV de saída; 0 desativa')
    args = parser.parse_args()
    if not (0 < args.timeout <= 30 and 1 <= args.workers <= 5 and 0 <= args.retries <= 1
            and 0 <= args.redirects <= 4 and 1024 <= args.byte_limit <= 1048576
            and 0 <= args.reuse_hours <= 168):
        parser.error('Limites inválidos: timeout 0–30, workers 1–5, retries 0–1, redirects 0–4, bytes 1024–1048576')
    print(json.dumps(run(args), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
