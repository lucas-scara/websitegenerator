import argparse
import csv
import importlib.util
import json
from pathlib import Path
import socket
import ssl
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_urls', ROOT / 'tools/check_urls.py')
import sys
sys.path.insert(0, str(ROOT / 'tools'))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
import site_assets


class URLTests(unittest.TestCase):
    def test_classification_and_routing(self):
        html = '<html><title>Chaveiro Bandeirantes</title><body>Serviços de chaves e fechaduras em Bauru</body></html>'
        def probe(*_):
            return {'content': html, 'content_type': 'text/html', 'final': 'https://example.com/', 'http_status': 200}
        good = check.verify('https://example.com', 'Chaveiro Bandeirantes', probe=probe)
        self.assertEqual((good['status_url'], good['encaminhamento'], good['identidade_correspondente']),
                         ('confirmada', 'auditoria_visual_futura', 'sim'))
        unknown = check.verify('https://example.com', 'Destak Vidros', probe=probe)
        self.assertEqual(unknown['status_url'], 'acessivel_inconclusiva')
        self.assertEqual(unknown['identidade_correspondente'], 'nao_verificada')
        parked = check.verify('https://example.com', 'Chaveiro Bandeirantes',
                              probe=lambda *_: {**probe(), 'content': '<html><body>Account suspended. Please contact your hosting provider.</body></html>'})
        self.assertEqual((parked['status_url'], parked['motivo']), ('falha_tecnica', 'pagina_generica_hospedagem'))

    def test_status_errors_and_retry(self):
        for code in (404, 503):
            calls = []
            def probe(*_):
                calls.append(1)
                return {'content': '', 'content_type': 'text/html', 'final': 'https://example.com/', 'http_status': code}
            result = check.verify('https://example.com', 'Empresa Teste', probe=probe)
            self.assertEqual(result['motivo'], f'http_{code}')
            self.assertEqual(result['http_status'], code)
            self.assertEqual(len(calls), 2 if code == 503 else 1)
        for exception, reason in ((socket.timeout(), 'timeout'), (socket.gaierror(), 'erro_dns'),
                                  (ssl.SSLError(), 'erro_tls')):
            with patch.object(check, 'fetch', side_effect=exception):
                self.assertEqual(check.probe_direct('https://example.com', 8, 1024, 4)['error'], reason)

    def test_invalid_missing_and_size(self):
        self.assertEqual(check.verify('', 'Empresa')['status_url'], 'sem_url')
        self.assertEqual(check.verify('file:///etc/passwd', 'Empresa')['motivo'], 'url_invalida')
        self.assertEqual(check.verify('https://user:password@example.com', 'Empresa')['motivo'], 'url_invalida')
        with patch.object(check, 'fetch', side_effect=ValueError('Response exceeds byte limit')):
            self.assertEqual(check.probe_direct('https://example.com', 8, 1024, 4)['error'], 'limite_bytes')
        with patch.object(check, 'fetch', side_effect=site_assets.ResponseLimitError(200, 'https://example.com/')):
            limited = check.verify('https://example.com/', 'Oficina Atlas', retries=0, probe=check.probe_direct)
        self.assertEqual((limited['status_url'], limited['motivo'], limited['http_status'], limited['encaminhamento']),
                         ('acessivel_inconclusiva', 'limite_bytes', 200, 'revisao_pendente'))

    def test_abbreviated_name_and_generic_words(self):
        shortened = '<html><title>Chaveiro Especialista</title><body>Chaveiro Especialista atende Bauru com serviços automotivos.</body></html>'
        self.assertEqual(check.classify_html(shortened, 'Chaveiro Especialista Automotivo de Bauru')[0], 'confirmada')
        generic = '<html><title>Chaveiro Bauru</title><body>Somos um chaveiro em Bauru para todas as pessoas.</body></html>'
        self.assertEqual(check.classify_html(generic, 'Chaveiro Especialista Automotivo de Bauru')[0], 'acessivel_inconclusiva')
        self.assertEqual(check.classify_html(generic, 'Chaveiro Bauru')[0], 'acessivel_inconclusiva')
        self.assertEqual(check.classify_html('<html><body>Outra empresa em Bauru com serviços diversos.</body></html>',
                                             'Oficina Atlas')[0], 'acessivel_inconclusiva')

    def test_batch_preserves_columns_and_failure_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / 'in.csv'; out = Path(folder) / 'out.csv'; report = Path(folder) / 'report.json'
            with src.open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=['id', 'empresa', 'site_identificado', 'notas'])
                writer.writeheader()
                writer.writerows([
                    {'id': '1', 'empresa': 'Oficina Atlas', 'site_identificado': 'https://example.com/', 'notas': 'operator note'},
                    {'id': '2', 'empresa': 'Oficina Atlas', 'site_identificado': 'https://example.com/', 'notas': 'duplicate'},
                    {'id': '3', 'empresa': 'Empresa Dois', 'site_identificado': 'https://fail.example/', 'notas': 'keep'},
                    {'id': '4', 'empresa': 'Sem Site', 'site_identificado': '', 'notas': 'keep'}])
            calls = []
            def probe(url, *_):
                calls.append(url)
                if 'fail' in url:
                    return {'error': 'erro_dns'}
                return {'content': '<html><body>Oficina Atlas atende toda a cidade.</body></html>',
                        'content_type': 'text/html', 'final': url, 'http_status': 200}
            args = argparse.Namespace(input=str(src), output=str(out), report=str(report), name_column=None,
                                      url_column=None, id_column=None, workers=5, timeout=8, byte_limit=1024,
                                      redirects=4, retries=1)
            summary = check.run(args, probe=probe)
            self.assertEqual(len(calls), 2)
            self.assertEqual(summary['contagens'], {'confirmada': 2, 'acessivel_inconclusiva': 0,
                                                    'falha_tecnica': 1, 'sem_url': 1})
            with out.open(newline='') as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]['notas'], 'operator note')
            self.assertEqual(rows[2]['notas'], 'keep')
            self.assertEqual(rows[3]['encaminhamento'], 'avaliar_primeiro_site')
            self.assertEqual(rows[2]['google_business_observado'], 'nao_verificado')
            self.assertEqual(json.loads(report.read_text())['erros'], {'erro_dns': 1})
            calls.clear()
            again = check.run(args, probe=probe)
            self.assertEqual(again['urls_reutilizadas'], 1)
            self.assertEqual(calls, ['https://fail.example/'])
            with out.open(newline='') as handle:
                reused_rows = list(csv.DictReader(handle))
            self.assertEqual(reused_rows[0]['reutilizado'], 'sim')

    def test_worker_deadline(self):
        with patch.object(check.subprocess, 'run', side_effect=subprocess.TimeoutExpired('probe', 8)):
            self.assertEqual(check.probe_subprocess('https://example.com/', 8, 1024, 4), {'error': 'timeout'})

    def test_safe_redirects_and_http_adapter(self):
        def response(status, location=None):
            item = MagicMock(status=status)
            item.getheader.side_effect = lambda key, default='': location if key == 'Location' else ('text/html' if key == 'Content-Type' else default)
            item.read.return_value = b'<html>Example Business in Bauru</html>'
            return item
        first = MagicMock(); first.getresponse.return_value = response(302, 'https://other.example/')
        second = MagicMock(); second.getresponse.return_value = response(200)
        with patch.object(site_assets, 'public_target', side_effect=lambda u: (site_assets.clean_url(u), '93.184.216.34', 443)), \
             patch.object(site_assets, 'PinnedHTTPS', side_effect=[first, second]):
            self.assertEqual(site_assets.fetch('https://example.com/', limit=1024, include_status=True,
                                               allow_http_errors=True, accepted_types={'text/html'})[3], 200)
        with patch.object(site_assets, 'public_target', side_effect=lambda u: (site_assets.clean_url(u), '93.184.216.34', 443)), \
             patch.object(site_assets, 'PinnedHTTPS', return_value=first):
            first.getresponse.return_value = response(302, 'http://127.0.0.1/')
            with self.assertRaisesRegex(ValueError, 'Insecure redirect'):
                site_assets.fetch('https://example.com/', limit=1024, forbid_downgrade=True)
            first.getresponse.return_value = response(302, 'https://example.com/')
            with self.assertRaisesRegex(ValueError, 'Redirect'):
                site_assets.fetch('https://example.com/', limit=1024, redirects=0)


if __name__ == '__main__':
    unittest.main()
