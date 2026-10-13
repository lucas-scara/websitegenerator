"""Isolated durability and concurrency tests for preview operations."""
import concurrent.futures
import importlib.util
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
import control
import preview_ops


class FakeVercel:
    def __init__(self, match=True):
        self.deploy_calls = 0
        self.match = match
        self.remote = None

    def deploy(self, site, key):
        self.deploy_calls += 1
        self.remote = {'uid': 'dpl_stable', 'url': 'preview.example', 'target': 'preview',
                       'readyState': 'READY', 'meta': {preview_ops.META_KEY: key}}
        return 'https://preview.example'

    def find(self, key, started_at):
        if not self.match or not self.remote or self.remote['meta'][preview_ops.META_KEY] != key:
            return None
        return self.remote


class PreviewOperationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db, self.old_root = control.DB, control.ROOT
        control.DB = Path(self.temp.name) / 'ledger.sqlite3'
        control.ROOT = Path(self.temp.name) / 'project'
        control.ROOT.mkdir()
        (control.ROOT / 'settings.json').write_text(json.dumps({
            'max_concurrent_businesses': 4,
            'external_operations': {'max_concurrent_calls': 4},
            'deployment': {'max_concurrent_deployments': 4},
        }))
        preview_ops.control = control
        self.batch_id = control.batch('electrician', 'Bauru, SP', 4)['id']
        with control.connect() as con:
            con.execute("UPDATE config SET value='4' WHERE key='max_workers'")
            con.execute("UPDATE config SET value='4' WHERE key='max_deploys'")

    def tearDown(self):
        control.DB, control.ROOT = self.old_db, self.old_root
        self.temp.cleanup()

    def add_jobs(self, count=4):
        return [control.add(self.batch_id, f'Empresa {n}', f'https://empresa{n}.example')['id']
                for n in range(count)]

    def claim_four(self, count=4):
        jobs = self.add_jobs(count)
        barrier = threading.Barrier(count)

        def claim(index):
            barrier.wait()
            return control.claim(self.batch_id, f'worker-{index}')['job']['id']

        with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
            claimed = list(pool.map(claim, range(count)))
        self.assertEqual(len(set(claimed)), count)
        self.assertEqual(set(claimed), set(jobs))
        assignments = {row['worker']: row['id'] for row in control.snapshot()['jobs'] if row['worker']}
        return [assignments[f'worker-{n}'] for n in range(count)]

    def fields(self, n):
        return {'presence_status': 'site_confirmado', 'commercial_category': 'A_prioritaria',
                'commercial_reason': 'Evidência pública documentada.', 'opportunity_type': 'redesign',
                'qualification': {'findings': ['Ponto visual observado']},
                'screenshots': ['runs/evidence.png'],
                'verification': {'checked_at': '2026-10-11', 'sources': ['https://source.example']},
                'contacts': {'phone': {'value': f'+55149999999{n:02d}', 'source': 'https://source.example',
                                       'checked_at': '2026-10-11'},
                             'email': {'status': 'nao_encontrado', 'source': 'https://source.example',
                                       'checked_at': '2026-10-11'},
                             'form': {'status': 'nao_encontrado', 'source': 'https://source.example',
                                      'checked_at': '2026-10-11'}}}

    def make_building(self, jid, worker, n=0):
        control.update(jid, worker, 'verified', fields=self.fields(n))
        control.update(jid, worker, 'qualified')
        control.update(jid, worker, 'extracting')
        control.update(jid, worker, 'building')

    def make_deployable(self, jid='site-test', worker='worker'):
        jid = control.add(self.batch_id, 'Deploy fixture', 'https://deploy-fixture.example')['id']
        control.claim(self.batch_id, worker)
        self.make_building(jid, worker)
        folder = preview_ops.job_dir(jid) / 'generated' / 'fixture'
        site = folder / 'site'
        site.mkdir(parents=True)
        (site / 'index.html').write_text('<h1>preview</h1>')
        manifest = folder / 'website.json'
        manifest.write_text(json.dumps({'site': str(site)}))
        key = 'a' * 64
        control.operation_begin(jid, worker, 'generate', key)
        control.operation_finish(jid, worker, 'generate', key, artifact=str(manifest))
        control.update(jid, worker, 'checking')
        control.update(jid, worker, 'deploying', fields={'qa_passed': True, 'qa_evidence': ['qa.json']})
        return jid, worker

    def test_four_jobs_claim_and_sqlite_operations_complete_under_contention(self):
        jobs = self.claim_four()

        def write(index):
            jid, worker = jobs[index], f'worker-{index}'
            key = f'{index + 1:064x}'
            control.operation_begin(jid, worker, 'external', key)
            return control.operation_finish(jid, worker, 'external', key, usage={'source': 'test'})['status']

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            statuses = list(pool.map(write, range(4)))
        self.assertEqual(statuses, ['complete'] * 4)
        with control.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM operations WHERE status='complete'").fetchone()[0], 4)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM stage_runs WHERE stage='reviewing' AND status='running'").fetchone()[0], 4)

    def test_partial_failure_does_not_stop_other_jobs(self):
        jobs = self.claim_four()
        control.recover(jobs[0], 'Injected worker failure')

        def proceed(index):
            jid, worker = jobs[index], f'worker-{index}'
            if index == 0:
                return 'recovered'
            key = f'{index + 1:064x}'
            control.operation_begin(jid, worker, 'external', key)
            control.operation_finish(jid, worker, 'external', key)
            return 'complete'

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(proceed, range(4))), ['recovered', 'complete', 'complete', 'complete'])

    def test_verified_agent_metadata_records_only_source_token_counters(self):
        jid = self.add_jobs(1)[0]
        control.claim(self.batch_id, 'worker-0')
        result = control.record_agent_execution(jid, 'worker-0',
            '0199aabb-ccdd-7000-aabb-112233445566', 'gpt-6-luna', 'medium',
            {'input_tokens': 11, 'output_tokens': 3, 'prompt': 'must not persist'})
        self.assertTrue(result['usage_available'])
        stage = control.snapshot()['stage_runs'][0]
        self.assertEqual(stage['model'], 'gpt-6-luna')
        self.assertEqual(stage['effort'], 'medium')
        self.assertEqual(json.loads(stage['usage_json']), {'input_tokens': 11, 'output_tokens': 3})
        with self.assertRaisesRegex(ValueError, 'own'):
            control.record_agent_execution(jid, 'wrong-worker',
                '0199aabb-ccdd-7000-aabb-112233445566', 'gpt-6-luna', 'medium')

    def test_sequential_capacity_one_remains_available(self):
        jobs = self.add_jobs(2)
        with control.connect() as con:
            con.execute("UPDATE config SET value='1' WHERE key='max_workers'")
        first = control.claim(self.batch_id, 'sequential')['job']['id']
        self.assertIn(first, jobs)
        with self.assertRaisesRegex(ValueError, 'capacity'):
            control.claim(self.batch_id, 'second')
        control.update(first, 'sequential', 'blocked', detail='Test releases the claim')
        second = control.claim(self.batch_id, 'sequential')['job']['id']
        self.assertNotEqual(first, second)

    def test_external_operation_limit_is_separate_from_businesses(self):
        jobs = self.claim_four()
        with control.connect() as con:
            con.execute("UPDATE config SET value='2' WHERE key='max_external_calls'")
        first, second, third = ('1' * 64, '2' * 64, '3' * 64)
        control.operation_begin(jobs[0], 'worker-0', 'external', first)
        control.operation_begin(jobs[1], 'worker-1', 'external', second)
        with self.assertRaisesRegex(ValueError,'capacity'):
            control.operation_begin(jobs[2], 'worker-2', 'external', third)
        control.operation_finish(jobs[0], 'worker-0', 'external', first)
        self.assertEqual(control.operation_begin(jobs[2], 'worker-2', 'external', third)['status'],'running')

    def test_generation_retry_reconciles_existing_artifact_without_regeneration(self):
        jobs = self.add_jobs(1)
        jid = jobs[0]
        control.claim(self.batch_id, 'worker-0')
        self.make_building(jid, 'worker-0')
        def generated(record, output_root, operation_key):
            folder = Path(output_root) / 'fixture'
            (folder / 'site').mkdir(parents=True)
            result = {'id':'fixture','site':str(folder / 'site'),'operation_key':operation_key,'seconds':0.1}
            (folder / 'website.json').write_text(json.dumps(result))
            return result
        with patch.object(preview_ops.quick_site, 'create', side_effect=generated) as create, \
                patch.object(control, 'operation_finish', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                preview_ops.generate(jid, 'worker-0')
            self.assertEqual(create.call_count, 1)
        self.assertEqual(control.recover(jid, 'Process stopped after artifact write')['stage'], 'queued')
        control.claim(self.batch_id, 'worker-1')
        with patch.object(preview_ops.quick_site, 'create', side_effect=AssertionError('must reuse artifact')):
            result = preview_ops.generate(jid, 'worker-1')
        self.assertTrue(Path(result['site']).is_dir())
        self.assertEqual(control.operation_get(jid, 'generate', result['operation_key'])['status'], 'complete')

    def test_deploy_recovery_after_remote_success_never_deploys_twice(self):
        jid, worker = self.make_deployable()
        client = FakeVercel()
        with patch.object(control, 'operation_finish', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                preview_ops.deploy(jid, worker, client)
        self.assertEqual(client.deploy_calls, 1)
        self.assertEqual(control.recover(jid, 'Stopped after remote deploy')['stage'], 'queued')
        control.claim(self.batch_id, 'worker-retry')
        result = preview_ops.deploy(jid, 'worker-retry', client)
        self.assertTrue(result['reused'])
        self.assertEqual(result['id'], 'dpl_stable')
        self.assertEqual(client.deploy_calls, 1)

    def test_reconciliation_without_remote_match_fails_closed(self):
        jid, worker = self.make_deployable()
        key = 'b' * 64
        control.operation_begin(jid, worker, 'deploy', key)
        control.operation_finish(jid, worker, 'deploy', key, status='uncertain', failure='interrupted')
        with self.assertRaisesRegex(ValueError, 'No matching remote deployment'):
            preview_ops.reconcile_deploy(jid, worker, key, FakeVercel(match=False))
        self.assertEqual(control.operation_get(jid, 'deploy', key)['status'], 'uncertain')

    def test_uncertain_deploy_frees_global_slot_but_blocks_new_key_for_same_job(self):
        first, first_worker = self.make_deployable()
        second = control.add(self.batch_id, 'Second deployment', 'https://second-deployment.example')['id']
        control.claim(self.batch_id, 'worker-second')
        self.make_building(second, 'worker-second', 1)
        control.update(second, 'worker-second', 'checking')
        control.update(second, 'worker-second', 'deploying', fields={'qa_passed': True, 'qa_evidence': ['qa.json']})
        with control.connect() as con:
            con.execute("UPDATE config SET value='1' WHERE key='max_deploys'")
        key = 'd' * 64
        control.operation_begin(first, first_worker, 'deploy', key)
        with self.assertRaisesRegex(ValueError, 'capacity'):
            control.operation_begin(second, 'worker-second', 'deploy', 'e' * 64)
        self.assertEqual(control.recover(first, 'Worker stopped with unknown remote result')['stage'], 'queued')
        with control.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM workers WHERE status='running'").fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT status FROM operations WHERE job_id=? AND kind='deploy'", (first,)).fetchone()[0], 'uncertain')
        self.assertEqual(control.operation_begin(second, 'worker-second', 'deploy', 'e' * 64)['status'], 'running')
        control.claim(self.batch_id, 'worker-retry')
        client = FakeVercel(match=False)
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, 'No matching remote deployment'):
                preview_ops.reconcile_deploy(first, 'worker-retry', key, client)
        with self.assertRaisesRegex(ValueError, 'Another deploy outcome'):
            control.operation_begin(first, 'worker-retry', 'deploy', 'f' * 64)
        self.assertEqual(client.deploy_calls, 0)
        self.assertEqual(control.operation_get(first, 'deploy', key)['status'], 'uncertain')

    def test_vercel_lookup_matches_project_and_stable_operation_key(self):
        client = preview_ops.VercelClient.__new__(preview_ops.VercelClient)
        client.project_id, client.team_id = 'prj_approved', 'team_approved'
        key = 'c' * 64
        seen = []
        def request(path, params):
            seen.append((path, dict(params)))
            return {'deployments': [
                {'uid':'wrong-project','projectId':'prj_other','meta':{preview_ops.META_KEY:key}},
                {'uid':'wrong-key','projectId':'prj_approved','meta':{preview_ops.META_KEY:'x'}},
                {'uid':'dpl_match','projectId':'prj_approved','meta':{preview_ops.META_KEY:key}}],
                'pagination': {'next': None}}
        client.request = request
        found = client.find(key, '2026-10-12T12:00:00+00:00')
        self.assertEqual(found['uid'],'dpl_match')
        self.assertEqual(seen[0][1]['projectId'],'prj_approved')
        self.assertEqual(seen[0][1]['teamId'],'team_approved')

    def test_static_site_uses_only_approved_existing_project_link(self):
        client = preview_ops.VercelClient.__new__(preview_ops.VercelClient)
        client.project_id, client.team_id = 'prj_approved', 'team_approved'
        site = Path(self.temp.name) / 'site'
        site.mkdir()
        (site / 'index.html').write_text('test')
        before = preview_ops.site_digest(site)
        client.link_site(site)
        self.assertEqual(preview_ops.site_digest(site), before)
        self.assertEqual(json.loads((site / '.vercel' / 'project.json').read_text())['projectId'], 'prj_approved')
        (site / '.vercel' / 'project.json').write_text(json.dumps({'projectId':'wrong','orgId':'team_approved'}))
        with self.assertRaisesRegex(ValueError,'different Vercel project'):
            client.link_site(site)

    def test_schema_three_migration_preserves_commercial_history(self):
        jid = control.add(self.batch_id, 'Historical', 'https://historical.example')['id']
        with control.connect() as con:
            con.execute("INSERT INTO commercial_attempts(job_id,channel,status,message,evidence,created_at) VALUES(?,?,?,?,?,?)",
                        (jid, 'email', 'failed_no_send', 'historic message', '{"source":"fixture"}', 'historic-time'))
            expected = tuple(con.execute('SELECT * FROM commercial_attempts WHERE job_id=?', (jid,)).fetchone())
            con.execute('DROP TABLE operations')
            con.execute('PRAGMA user_version=3')
        with control.connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], control.SCHEMA_VERSION)
            self.assertEqual(tuple(con.execute('SELECT * FROM commercial_attempts WHERE job_id=?', (jid,)).fetchone()), expected)
            self.assertIsNotNone(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='operations'").fetchone())
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_previously_migrated_capacity_requires_expected_value(self):
        historical = control.add(self.batch_id, 'Historical capacity', 'https://capacity.example')['id']
        with control.connect() as con:
            con.execute("UPDATE config SET value='3' WHERE key='max_workers'")
            con.execute('DROP TABLE operations')
            con.execute('DROP TABLE stage_runs')
            con.execute('PRAGMA user_version=3')
        with control.connect() as con:
            self.assertEqual(con.execute("SELECT value FROM config WHERE key='max_workers'").fetchone()[0], '3')
            self.assertEqual(con.execute('SELECT name FROM jobs WHERE id=?', (historical,)).fetchone()[0], 'Historical capacity')
        self.assertEqual(control.set_capacity(4, expected=3), {'previous_max_workers':3, 'max_workers':4})
        with control.connect() as con:
            con.execute("UPDATE config SET value='2' WHERE key='max_workers'")
        with self.assertRaisesRegex(ValueError, 'customized'):
            control.set_capacity(4, expected=3)
        with control.connect() as con:
            self.assertEqual(con.execute("SELECT value FROM config WHERE key='max_workers'").fetchone()[0], '2')


if __name__ == '__main__':
    unittest.main()
