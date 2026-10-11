import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('control', Path(__file__).parents[1] / 'tools/control.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = control.DB
        control.DB = Path(self.tmp.name) / 'ledger.db'
        self.bid = control.batch('electrician', 'Bauru, SP', 1)['id']

    def tearDown(self):
        control.DB = self.old_db
        self.tmp.cleanup()

    def add(self, name='Ficticia Eletrica', url='https://ficticia.example', aliases=()):
        return control.add(self.bid, name, url, aliases)['id']

    def fields(self, presence='site_confirmado', category='A_prioritaria', opportunity='redesign'):
        return {'presence_status': presence, 'commercial_category': category,
                'commercial_reason': 'Empresa e oportunidade confirmadas por fonte e data.',
                'opportunity_type': opportunity,
                'qualification': {'findings': ['Navigation is clipped in captured viewport']},
                'screenshots': ['runs/test/screenshot.png'],
                'verification': {'checked_at': '2026-10-11', 'sources': ['https://source.example'], 'queries': ['Ficticia Eletrica Bauru site']},
                'contacts': {'phone': {'value': '+5514999999999', 'source': 'https://source.example'},
                             'email': {'status': 'encontrado', 'source': 'https://source.example'},
                             'form': {'status': 'nao_encontrado', 'eligible': False}}}

    def qualified(self, jid, presence='site_confirmado', category='A_prioritaria', opportunity='redesign'):
        control.claim(self.bid, 'codex')
        control.update(jid, 'codex', 'verified', fields=self.fields(presence, category, opportunity))
        control.update(jid, 'codex', 'qualified')
        control.update(jid, 'codex', 'extracting')

    def publish(self, jid):
        self.qualified(jid)
        control.update(jid, 'codex', 'building')
        control.update(jid, 'codex', 'checking')
        control.update(jid, 'codex', 'deploying', fields={'qa_passed': True, 'qa_evidence': ['qa.json']})
        control.update(jid, 'codex', 'ready', fields={'preview_verified': True,
            'preview_url': 'https://preview.example',
            'deployment': {'id': 'dpl_test', 'project': 'scarasoft-previas'}})

    def test_redesign_no_contact_reaches_goal(self):
        jid = self.add()
        self.publish(jid)
        control.preview_finish(jid, 'codex')
        progress = control.batch_status(self.bid, 'complete')
        self.assertEqual((progress['published_count'], progress['remaining_count']), (1, 0))
        self.assertEqual(control.snapshot()['jobs'][0]['contact_status'], 'not_sent')
        with control.connect() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM submissions').fetchone()[0], 0)

    def test_first_site_null_domain(self):
        jid = self.add(url='', aliases=['phone:+5514999999999'])
        with control.connect() as con:
            self.assertIsNone(con.execute('SELECT domain FROM jobs WHERE id=?', (jid,)).fetchone()[0])
        self.qualified(jid, 'sem_site_confirmado', opportunity='primeiro_site')
        self.assertEqual(control.snapshot()['batches'][0]['qualified_count'], 1)

    def test_inaccessible_site_is_opportunity(self):
        jid = self.add()
        self.qualified(jid, 'site_inoperante')
        self.assertEqual(control.snapshot()['batches'][0]['verified_count'], 1)

    def test_inconclusive_site_blocks_generation(self):
        jid = self.add()
        control.claim(self.bid, 'codex')
        fields = self.fields('presenca_inconclusiva', 'D_pendente')
        control.update(jid, 'codex', 'verified', fields=fields)
        with self.assertRaises(ValueError): control.update(jid, 'codex', 'qualified')

    def test_email_without_form_and_ineligible_form(self):
        jid = self.add()
        self.qualified(jid)
        self.assertEqual(control.snapshot()['jobs'][0]['data']['contacts']['form']['status'], 'nao_encontrado')
        control.update(jid, 'codex', fields={'contacts': {'email': {'status': 'encontrado', 'source': 'https://source.example'},
            'form': {'status': 'encontrado', 'url': 'https://source.example/orcamento', 'purpose': 'orcamento', 'eligible': False, 'restrictions': ['clientes'], 'source': 'https://source.example'}}})
        self.assertEqual(control.snapshot()['jobs'][0]['data']['contacts']['form']['eligible'], False)

    def test_prior_batch_and_source_alias_dedupe(self):
        self.add(aliases=['phone:+5514999999999'])
        other = control.batch('electrician', 'Bauru, SP')['id']
        with self.assertRaises(sqlite3.IntegrityError): control.add(other, 'Ficticia Eletrica', '')
        with self.assertRaises(sqlite3.IntegrityError): control.add(other, 'Outra Fonte', '', ['phone:+5514999999999'])

    def test_partial_services_quick_site_contract(self):
        from tools.quick_site import profile, validate
        catalog = profile('electrician')['catalog']
        first = next(iter(catalog))
        template, business = validate({'template': 'electrician', 'name': 'Empresa Ficticia',
            'phone': '+55 14 99999-9999', 'city': 'Bauru', 'state': 'SP',
            'enabled_services': [first], 'preview': True})
        self.assertEqual(template, 'electrician')
        self.assertEqual(business['enabled_services'], [first])

    def test_site_input_uses_verified_contacts_and_service_evidence(self):
        jid = self.add()
        self.qualified(jid)
        from tools.quick_site import profile
        defaults = profile('electrician')['segment']['default_services']
        additional = next(x for x in profile('electrician')['catalog'] if x not in defaults)
        control.update(jid, 'codex', fields={'services': {
            'excluded': [defaults[0]], 'confirmed': [additional],
            'evidence': {additional: {'source': 'https://ficticia.example', 'observation': 'Service listed'}}}})
        output = control.ROOT / 'runs' / 'test-private-site-input.json'
        try:
            result = control.site_input(jid, output)
            record = json.loads(output.read_text())[0]
            self.assertEqual(result['template'], 'electrician')
            self.assertNotIn(defaults[0], record['enabled_services'])
            self.assertIn(additional, record['enabled_services'])
            self.assertEqual(record['phone'], '+5514999999999')
            self.assertTrue(record['preview'])
        finally:
            output.unlink(missing_ok=True)

    def test_blocked_and_discarded_pending(self):
        jid = self.add()
        control.claim(self.bid, 'codex')
        fields = self.fields('sem_site_potencial', 'D_pendente', 'primeiro_site')
        control.update(jid, 'codex', 'verified', fields=fields)
        control.update(jid, 'codex', 'blocked', detail='Missing corroboration')
        self.assertEqual(control.snapshot()['batches'][0]['pending_count'], 1)
        other = self.add('Outra Ficticia', '')
        control.claim(self.bid, 'codex')
        fields = self.fields('site_confirmado', 'descartada')
        fields['discard_reason'] = 'Service outside catalog'
        control.update(other, 'codex', 'skipped', fields=fields)
        self.assertEqual(control.snapshot()['batches'][0]['pending_count'], 2)

    def test_resume_keeps_history_and_preview(self):
        jid = self.add()
        self.publish(jid)
        with control.connect() as con:
            con.execute('INSERT INTO events(job_id,message,created_at) VALUES(?,?,?)', (jid, 'historical note', control.now()))
        self.assertEqual(control.recover(jid, 'Worker stopped')['stage'], 'ready')
        self.assertEqual(control.snapshot()['jobs'][0]['data']['deployment']['id'], 'dpl_test')
        self.assertEqual(control.snapshot()['jobs'][0]['contact_status'], 'not_sent')
        with control.connect() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM identities').fetchone()[0], 2)
            self.assertGreaterEqual(con.execute('SELECT COUNT(*) FROM events').fetchone()[0], 2)

    def test_all_segments_and_dashboard_contract(self):
        batch = control.batch('all', 'Bauru, SP', 2)['id']
        with self.assertRaises(ValueError): control.add(batch, 'Teste', '')
        jid = control.add(batch, 'Teste', '', template='serralheria')['id']
        state = control.snapshot()
        self.assertEqual(next(j for j in state['jobs'] if j['id'] == jid)['data']['template'], 'serralheria')
        self.assertEqual({x['id'] for x in state['templates']}, set(control.TEMPLATES))

    def test_migrate_old_schema_without_data_loss(self):
        legacy = Path(self.tmp.name) / 'legacy.db'
        with sqlite3.connect(legacy) as con:
            con.executescript('''CREATE TABLE batches(id TEXT PRIMARY KEY,industry TEXT NOT NULL,city TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,requested_count INTEGER NOT NULL DEFAULT 3);
            CREATE TABLE jobs(id TEXT PRIMARY KEY,batch_id TEXT NOT NULL REFERENCES batches(id),name TEXT NOT NULL,url TEXT NOT NULL,domain TEXT UNIQUE NOT NULL,stage TEXT NOT NULL,worker TEXT,detail TEXT DEFAULT '',reason TEXT DEFAULT '',preview_url TEXT DEFAULT '',contact_status TEXT DEFAULT 'not_sent',data TEXT NOT NULL DEFAULT '{}',updated_at TEXT NOT NULL);
            CREATE TABLE identities(identity TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id));
            CREATE TABLE submissions(job_id TEXT PRIMARY KEY REFERENCES jobs(id),message TEXT NOT NULL,message_hash TEXT NOT NULL,form_url TEXT NOT NULL,status TEXT NOT NULL,evidence TEXT,created_at TEXT NOT NULL);
            INSERT INTO batches VALUES('b','electrician','Bauru','running','date',1);
            INSERT INTO jobs VALUES('j','b','Old','https://old.example','old.example','sent',NULL,'','','https://preview.example','sent','{}','date');
            INSERT INTO identities VALUES('domain:old.example','j');
            INSERT INTO submissions VALUES('j','message','hash','https://old.example/contact','sent','evidence','date');''')
        control.DB = legacy
        with control.connect() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM submissions').fetchone()[0], 1)
            self.assertEqual(con.execute('SELECT domain FROM jobs').fetchone()[0], 'old.example')
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(next(row for row in con.execute('PRAGMA table_info(jobs)') if row['name'] == 'domain')['notnull'], 0)


if __name__ == '__main__': unittest.main()
