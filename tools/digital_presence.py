"""Deterministic signals from structured search results; never opens result pages."""
import json
import re
import unicodedata
from urllib.parse import urlsplit

SIGNALS = {'sim', 'nao_observado', 'nao_verificado'}
SIGNAL_FIELDS = ('google_business_observado', 'presenca_social_observada',
                 'presenca_diretorio_observada', 'instagram_observado', 'facebook_observado')
GENERIC = {'bauru', 'sp', 'sao', 'paulo', 'de', 'da', 'do', 'dos', 'das', 'e', 'em',
           'chaveiro', 'chaveiros', 'vidros', 'vidracaria', 'eletricista', 'eletrica',
           'serralheria', 'desentupidora', 'refrigeracao', 'climatizacao',
           'automotivo', 'servicos', 'comercio', 'empresa', 'toldos', 'coberturas',
           'plantao', 'horas', '24',
           'portoes', 'estruturas', 'metalicas', 'engenharia', 'ar', 'condicionado'}


def normalized(value):
    value = unicodedata.normalize('NFKD', str(value).casefold())
    return re.sub(r'[^a-z0-9]+', ' ', ''.join(c for c in value if not unicodedata.combining(c))).strip()


def strong_name_match(company, candidate):
    """Require a distinctive brand token and a contiguous commercial-name phrase."""
    words = normalized(company).split()
    text = f' {normalized(candidate)} '
    significant = [word for word in words if word not in {'de', 'da', 'do', 'dos', 'das', 'e', 'em'}]
    if len(significant) < 2 or not any(w not in GENERIC and len(w) >= 3 for w in significant):
        return False
    phrases = [normalized(company), ' '.join(significant)]
    for size in range(len(significant) - 1, 1, -1):
        prefix = significant[:size]
        if any(w not in GENERIC and len(w) >= 3 for w in prefix):
            phrases.append(' '.join(prefix))
    return any(len(phrase) >= 8 and f' {phrase} ' in text for phrase in phrases)


def prepared_queries(company, city):
    quoted = '"' + company.strip().replace('"', '') + '"'
    return [quoted, quoted + ' ' + city.strip()] if city.strip() else [quoted]


def result_kind(item):
    url = item.get('url') or ''
    try:
        parts = urlsplit(url)
        host = (parts.hostname or '').lower()
    except ValueError:
        host = ''
    displayed = (item.get('dominio_exibido') or '').lower().removeprefix('www.')
    if displayed and host and host != 'google.com' and not host.endswith('.google.com') and host != displayed and not host.endswith('.' + displayed):
        return ''
    if (item.get('tipo') == 'site_proprio' and host and parts.scheme in ('http', 'https')
            and not any(host == domain or host.endswith('.' + domain)
                        for domain in ('google.com', 'instagram.com', 'facebook.com'))):
        return 'site_proprio'
    if host == 'instagram.com' or host.endswith('.instagram.com') or displayed == 'instagram.com':
        return 'instagram'
    if host == 'facebook.com' or host.endswith('.facebook.com') or host == 'fb.com' or displayed == 'facebook.com':
        return 'facebook'
    if item.get('tipo') == 'google_business' and (not url or host.endswith('.google.com')):
        return 'google_business'
    if item.get('tipo') == 'diretorio' and (host or displayed) and (not url or parts.scheme in ('http', 'https')):
        return 'diretorio'
    return ''


def classify_search(record, company, city):
    """Use up to ten supplied results from at most two recorded queries."""
    queries = record.get('consultas') or []
    if len(queries) > 2:
        raise ValueError('No máximo duas consultas por empresa')
    status = record.get('status') or 'nao_executada'
    if status not in ('concluida', 'indisponivel', 'nao_executada'):
        raise ValueError('Status de pesquisa inválido')
    default = 'nao_observado' if status == 'concluida' else 'nao_verificado'
    found = {field: default for field in SIGNAL_FIELDS}
    references = []
    candidate = ''
    if status == 'concluida':
        for item in (record.get('resultados') or [])[:10]:
            if not isinstance(item, dict) or not strong_name_match(company, item.get('titulo') or ''):
                continue
            locality = normalized(item.get('cidade') or '')
            expected = normalized(city)
            if locality and expected and locality not in expected and expected not in locality:
                continue
            kind = result_kind(item)
            if not kind:
                continue
            if kind == 'site_proprio':
                candidate = candidate or item.get('url') or ''
            elif kind == 'instagram':
                found['instagram_observado'] = found['presenca_social_observada'] = 'sim'
            elif kind == 'facebook':
                found['facebook_observado'] = found['presenca_social_observada'] = 'sim'
            elif kind == 'google_business':
                found['google_business_observado'] = 'sim'
            else:
                found['presenca_diretorio_observada'] = 'sim'
            references.append({'tipo': kind, 'titulo': item.get('titulo') or '',
                               'url': item.get('url') or '', 'cidade': item.get('cidade') or '',
                               'dominio_exibido': item.get('dominio_exibido') or '',
                               'fonte_url': item.get('fonte_url') or '',
                               'origem': item.get('origem') or record.get('fonte') or ''})
    return {**found, 'url_candidata_pendente': candidate,
            'consulta_presenca': json.dumps(queries, ensure_ascii=False),
            'data_pesquisa_presenca': record.get('pesquisado_em') or '',
            'status_pesquisa_presenca': status,
            'fonte_busca': record.get('fonte') or '',
            'referencias_busca': json.dumps(references, ensure_ascii=False)}


def prior_scout_observation(row):
    """Carry forward explicit scouting categories without inventing new SERP results."""
    kind = row.get('resultado_busca') or ''
    observed = kind == 'ficha_local' and 'revisar identidade' not in normalized(row.get('notas') or '')
    found = {field: 'nao_verificado' for field in SIGNAL_FIELDS}
    if observed:
        found['google_business_observado'] = 'sim'
    return {**found, 'url_candidata_pendente': '',
            'consulta_presenca': json.dumps([row.get('consulta_usada') or ''], ensure_ascii=False),
            'data_pesquisa_presenca': row.get('data_coleta') or '',
            'status_pesquisa_presenca': 'evidencia_anterior',
            'fonte_busca': 'levantamento_anterior: ' + kind,
            'referencias_busca': json.dumps([{'tipo': 'pagina_de_busca',
                                              'url': row.get('fonte_url') or ''}], ensure_ascii=False)}
