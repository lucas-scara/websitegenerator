import argparse
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import digital_presence as presence
import check_urls


class PresenceTests(unittest.TestCase):
    def record(self, *results, status='concluida'):
        return {'consultas': ['"MetalArt Vidros"'], 'status': status, 'fonte': 'navegador_iab',
                'pesquisado_em': '2026-10-10T12:00:00Z', 'resultados': list(results)}

    def item(self, kind, title='MetalArt Vidros Bauru', city='Bauru, SP'):
        urls = {'instagram': 'https://www.instagram.com/metalartvidros/',
                'facebook': 'https://www.facebook.com/metalartvidros/',
                'google_business': '', 'diretorio': 'https://diretorio.example/metalartvidros'}
        return {'tipo': kind, 'titulo': title, 'cidade': city, 'url': urls[kind]}

    def test_social_platforms_and_multiple_signals(self):
        data = presence.classify_search(self.record(self.item('instagram'), self.item('facebook'),
                                                    self.item('google_business'), self.item('diretorio')),
                                        'MetalArt Vidros', 'Bauru, SP')
        for field in presence.SIGNAL_FIELDS:
            self.assertEqual(data[field], 'sim')
        self.assertEqual(len(json.loads(data['referencias_busca'])), 4)

    def test_google_only_directory_only_and_none(self):
        for kind, field in [('google_business', 'google_business_observado'),
                            ('diretorio', 'presenca_diretorio_observada')]:
            data = presence.classify_search(self.record(self.item(kind)), 'MetalArt Vidros', 'Bauru, SP')
            self.assertEqual(data[field], 'sim')
            self.assertEqual(data['presenca_social_observada'], 'nao_observado')
        empty = presence.classify_search(self.record(), 'MetalArt Vidros', 'Bauru, SP')
        self.assertTrue(all(empty[field] == 'nao_observado' for field in presence.SIGNAL_FIELDS))

    def test_homonym_weak_match_and_unavailable(self):
        other_city = presence.classify_search(self.record(self.item('instagram', city='Campinas, SP')),
                                              'MetalArt Vidros', 'Bauru, SP')
        weak = presence.classify_search(self.record(self.item('facebook', title='Vidros em Bauru')),
                                        'MetalArt Vidros', 'Bauru, SP')
        unavailable = presence.classify_search(self.record(status='indisponivel'), 'MetalArt Vidros', 'Bauru, SP')
        self.assertEqual(other_city['presenca_social_observada'], 'nao_observado')
        self.assertEqual(weak['presenca_social_observada'], 'nao_observado')
        self.assertEqual(unavailable['presenca_social_observada'], 'nao_verificado')
        with self.assertRaises(ValueError):
            presence.classify_search({'consultas': ['a', 'b', 'c'], 'status': 'concluida'}, 'MetalArt Vidros', 'Bauru')

    def test_new_site_stays_pending_and_prior_source_is_explicit(self):
        item = {'tipo': 'site_proprio', 'titulo': 'MetalArt Vidros', 'cidade': 'Bauru, SP',
                'url': 'https://metalart.example/', 'origem': 'navegador_iab'}
        data = presence.classify_search(self.record(item), 'MetalArt Vidros', 'Bauru, SP')
        self.assertEqual(data['url_candidata_pendente'], 'https://metalart.example/')
        prior = presence.prior_scout_observation({'resultado_busca': 'ficha_local',
                                                   'consulta_usada': 'vidros Bauru',
                                                   'fonte_url': 'https://google.com/search?q=vidros'})
        self.assertEqual(prior['google_business_observado'], 'sim')
        self.assertEqual(prior['status_pesquisa_presenca'], 'evidencia_anterior')
        uncertain = presence.prior_scout_observation({'resultado_busca': 'ficha_local',
                                                       'notas': 'Nome genérico; revisar identidade'})
        self.assertEqual(uncertain['google_business_observado'], 'nao_verificado')

    def test_no_social_page_access_and_operator_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'input.csv'; out = root / 'out.csv'; report = root / 'report.json'; structured = root / 'results.json'; plan = root / 'plan.csv'
            with source.open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=['id', 'empresa', 'cidade', 'site_identificado',
                                                             'google_business_observado', 'fonte_sinal'])
                writer.writeheader()
                writer.writerow({'id': 'x', 'empresa': 'MetalArt Vidros', 'cidade': 'Bauru, SP',
                                 'site_identificado': '', 'google_business_observado': 'sim',
                                 'fonte_sinal': 'operador'})
            structured.write_text(json.dumps([{'id': 'x', **self.record(self.item('instagram'))}]))
            args = argparse.Namespace(input=str(source), output=str(out), report=str(report), search_plan=str(plan),
                                      search_results=str(structured), use_existing_observations=False,
                                      name_column=None, url_column=None, id_column=None, workers=5,
                                      timeout=8, byte_limit=1024, redirects=4, retries=0, reuse_hours=0)
            summary = check_urls.run(args, probe=lambda *_: self.fail('No URL or social page should be fetched'))
            self.assertEqual(summary['contagens']['sem_url'], 1)
            with out.open(newline='') as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row['encaminhamento'], 'primeiro_site_potencial')
            self.assertEqual(row['fonte_sinal'], 'operador')
            self.assertEqual(row['google_business_observado'], 'sim')
            self.assertEqual(row['instagram_observado'], 'sim')
            with plan.open(newline='') as handle:
                planned = next(csv.DictReader(handle))
            self.assertEqual(planned['consulta_1'], '"MetalArt Vidros"')
            self.assertEqual(planned['consulta_2'], '"MetalArt Vidros" Bauru, SP')


if __name__ == '__main__':
    unittest.main()
