import concurrent.futures
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
        self.old_auth = control.OUTREACH_AUTH_FILE
        self.old_email = os.environ.get('BR_COMMERCIAL_EMAIL')
        self.old_phone = os.environ.get('BR_COMMERCIAL_PHONE')
        control.DB = Path(self.tmp.name) / 'ledger.db'
        control.OUTREACH_AUTH_FILE = Path(self.tmp.name) / 'authorization.json'
        os.environ['BR_COMMERCIAL_EMAIL'] = 'scarasoft@example.org'
        os.environ['BR_COMMERCIAL_PHONE'] = '+55 14 90000-0000'
        self.bid = control.batch('electrician', 'Bauru, SP', 1)['id']

    def tearDown(self):
        control.DB = self.old_db
        control.OUTREACH_AUTH_FILE = self.old_auth
        for key, value in (('BR_COMMERCIAL_EMAIL', self.old_email), ('BR_COMMERCIAL_PHONE', self.old_phone)):
            if value is None: os.environ.pop(key, None)
            else: os.environ[key] = value
        self.tmp.cleanup()

    def add(self, name='Ficticia Eletrica', url='https://ficticia.example', aliases=()):
        return control.add(self.bid, name, url, aliases)['id']

    def fields(self, presence='site_confirmado', category='A_prioritaria', opportunity='redesign', phone='+5514999999999'):
        return {'presence_status': presence, 'commercial_category': category,
                'commercial_reason': 'Empresa e oportunidade confirmadas por fonte e data.',
                'opportunity_type': opportunity,
                'qualification': {'findings': ['Navigation is clipped in captured viewport']},
                'screenshots': ['runs/test/screenshot.png'],
                'verification': {'checked_at': '2026-10-11', 'sources': ['https://source.example'], 'queries': ['Ficticia Eletrica Bauru site']},
                'contacts': {'phone': {'value': phone, 'source': 'https://source.example', 'checked_at': '2026-10-11'},
                             'email': {'status': 'encontrado', 'value': f'contato{phone[-3:]}@ficticia.example', 'source': 'https://source.example', 'checked_at': '2026-10-11'},
                             'form': {'status': 'nao_encontrado', 'eligible': False, 'source': 'https://source.example', 'checked_at': '2026-10-11'}}}

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
        self.add('Other Candidate', 'https://other-candidate.example')
        self.publish(jid)
        control.preview_finish(jid, 'codex')
        progress = control.batch_status(self.bid, 'complete')
        self.assertEqual((progress['published_count'], progress['remaining_count']), (1, 0))
        self.assertEqual(progress['evaluating_count'], 1)
        self.assertEqual(progress['pending_count'], 1)
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
        control.update(jid, 'codex', fields={'contacts': {'email': {'status': 'encontrado', 'value': 'contato@ficticia.example', 'source': 'https://source.example', 'checked_at': '2026-10-11'},
            'form': {'status': 'encontrado', 'url': 'https://source.example/orcamento', 'purpose': 'orcamento', 'eligible': False, 'restrictions': ['clientes'], 'source': 'https://source.example', 'checked_at': '2026-10-11'}}})
        self.assertEqual(control.snapshot()['jobs'][0]['data']['contacts']['form']['eligible'], False)

    def test_missing_email_and_form_do_not_disqualify(self):
        jid = self.add()
        control.claim(self.bid, 'codex')
        fields = self.fields()
        fields['contacts']['email'] = {'status': 'nao_encontrado', 'source': 'https://source.example', 'checked_at': '2026-10-11'}
        fields['contacts']['form'] = {'status': 'nao_encontrado', 'source': 'https://source.example', 'checked_at': '2026-10-11'}
        fields['contacts']['whatsapp'] = {'status': 'presumido'}
        control.update(jid, 'codex', 'verified', fields=fields)
        self.assertEqual(control.update(jid, 'codex', 'qualified')['stage'], 'qualified')
        output = control.ROOT / 'runs' / 'test-private-whatsapp.json'
        try:
            control.site_input(jid, output)
            record = json.loads(output.read_text())[0]
            self.assertNotIn('whatsapp', record)
            from tools.quick_site import validate
            self.assertEqual(validate(record)[1]['whatsapp'], '5514999999999')
            self.assertEqual(record['enabled_services'], control.profile('electrician')['segment']['default_services'])
        finally:
            output.unlink(missing_ok=True)

    def test_rejects_unverified_facts_and_unsupported_service_evidence(self):
        jid = self.add()
        control.claim(self.bid, 'codex')
        fields = self.fields()
        fields['verification']['sources'] = []
        with self.assertRaises(ValueError): control.update(jid, 'codex', 'verified', fields=fields)
        fields = self.fields()
        fields['contacts']['phone'].pop('source')
        with self.assertRaises(ValueError): control.update(jid, 'codex', 'verified', fields=fields)
        fields = self.fields()
        fields['contacts']['form'] = {'status': 'encontrado', 'url': 'https://source.example/form', 'source': 'https://source.example', 'checked_at': '2026-10-11'}
        with self.assertRaises(ValueError): control.update(jid, 'codex', 'verified', fields=fields)
        fields = self.fields()
        fields['contacts']['whatsapp'] = {'status': 'nao_utiliza'}
        with self.assertRaises(ValueError): control.update(jid, 'codex', 'verified', fields=fields)
        control.update(jid, 'codex', 'verified', fields=self.fields())
        from tools.quick_site import profile
        default = profile('electrician')['segment']['default_services'][0]
        with self.assertRaises(ValueError):
            control.update(jid, 'codex', fields={'services': {'excluded': [default]}})
        with self.assertRaises(ValueError):
            control.update(jid, 'codex', fields={'services': {'confirmed': ['outside-catalog']}})

    def test_missing_all_public_contacts_remains_pending(self):
        jid = self.add()
        control.claim(self.bid, 'codex')
        fields = self.fields()
        fields['contacts'] = {'email': {'status': 'nao_verificado'}, 'form': {'status': 'nao_verificado'}}
        control.update(jid, 'codex', 'verified', fields=fields)
        with self.assertRaisesRegex(ValueError, 'public contact'):
            control.update(jid, 'codex', 'qualified')

    def test_prior_batch_and_source_alias_dedupe(self):
        self.add(aliases=['phone:+5514999999999'])
        other = control.batch('electrician', 'Bauru, SP')['id']
        ambiguous = control.add(other, 'Ficticia Eletrica', '')
        self.assertEqual(ambiguous['identity_review']['status'], 'pending')
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
            'evidence': {additional: {'source': 'https://ficticia.example', 'observation': 'Service listed'},
                         defaults[0]: {'source': 'https://ficticia.example', 'observation': 'Business explicitly excludes it', 'contradiction': True}}}})
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

    def test_unconfirmed_defaults_remain_enabled_and_unsupported_additions_are_removed(self):
        jid = self.add()
        self.qualified(jid)
        from tools.quick_site import profile
        defaults = profile('electrician')['segment']['default_services']
        additional = next(x for x in profile('electrician')['catalog'] if x not in defaults)
        with self.assertRaisesRegex(ValueError, 'observed evidence'):
            control.update(jid, 'codex', fields={'services': {'confirmed': [additional]}})
        control.update(jid, 'codex', fields={'services': {'confirmed': [], 'excluded': [], 'evidence': {}}})
        output = control.ROOT / 'runs' / 'test-default-site-input.json'
        try:
            control.site_input(jid, output)
            self.assertEqual(json.loads(output.read_text())[0]['enabled_services'], defaults)
            self.assertNotIn(additional, json.loads(output.read_text())[0]['enabled_services'])
        finally:
            output.unlink(missing_ok=True)

    def test_default_exclusion_requires_documented_contradiction(self):
        jid = self.add()
        self.qualified(jid)
        from tools.quick_site import profile
        default = profile('electrician')['segment']['default_services'][0]
        source = 'https://ficticia.example/services'
        with self.assertRaisesRegex(ValueError, 'explicit documented contradiction'):
            control.update(jid, 'codex', fields={'services': {'excluded': [default],
                'evidence': {default: {'source': source, 'observation': 'No mention of this service'}}}})
        control.update(jid, 'codex', fields={'services': {'excluded': [default],
            'evidence': {default: {'source': source, 'observation': 'Business explicitly says this service is unavailable', 'contradiction': True}}}})
        output = control.ROOT / 'runs' / 'test-contradiction-site-input.json'
        try:
            control.site_input(jid, output)
            self.assertNotIn(default, json.loads(output.read_text())[0]['enabled_services'])
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
        fields = self.fields('site_confirmado', 'descartada', phone='+5514999999901')
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
            self.assertEqual(con.execute('SELECT COUNT(*) FROM identities').fetchone()[0], 3)
            self.assertGreaterEqual(con.execute('SELECT COUNT(*) FROM events').fetchone()[0], 2)

    def test_all_segments_and_dashboard_contract(self):
        batch = control.batch('all', 'Bauru, SP', 2)['id']
        with self.assertRaises(ValueError): control.add(batch, 'Teste', '')
        jid = control.add(batch, 'Teste', '', template='serralheria')['id']
        state = control.snapshot()
        self.assertEqual(next(j for j in state['jobs'] if j['id'] == jid)['data']['template'], 'serralheria')
        self.assertEqual({x['id'] for x in state['templates']}, set(control.TEMPLATES))

    def legacy_db(self):
        legacy = Path(self.tmp.name) / 'legacy.db'
        legacy.unlink(missing_ok=True)
        with sqlite3.connect(legacy) as con:
            con.executescript('''CREATE TABLE batches(id TEXT PRIMARY KEY,industry TEXT NOT NULL,city TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,requested_count INTEGER NOT NULL DEFAULT 3);
            CREATE TABLE jobs(id TEXT PRIMARY KEY,batch_id TEXT NOT NULL REFERENCES batches(id),name TEXT NOT NULL,url TEXT NOT NULL,domain TEXT UNIQUE NOT NULL,stage TEXT NOT NULL,worker TEXT,detail TEXT DEFAULT '',reason TEXT DEFAULT '',preview_url TEXT DEFAULT '',contact_status TEXT DEFAULT 'not_sent',data TEXT NOT NULL DEFAULT '{}',updated_at TEXT NOT NULL);
            CREATE TABLE identities(identity TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id));
            CREATE TABLE events(id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT,message TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE workers(id TEXT PRIMARY KEY,job_id TEXT,status TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE TABLE submissions(job_id TEXT PRIMARY KEY REFERENCES jobs(id),message TEXT NOT NULL,message_hash TEXT NOT NULL,form_url TEXT NOT NULL,status TEXT NOT NULL,evidence TEXT,created_at TEXT NOT NULL);
            CREATE TABLE config(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            INSERT INTO batches VALUES('b','electrician','Bauru','running','date',1);
            INSERT INTO jobs VALUES('j','b','Old','https://old.example','old.example','sent',NULL,'','','https://preview.example','sent','{}','date');
            INSERT INTO identities VALUES('domain:old.example','j');
            INSERT INTO events(job_id,message,created_at) VALUES('j','historical event','date');
            INSERT INTO workers VALUES('w','j','idle','date');
            INSERT INTO config VALUES('max_workers','2');
            INSERT INTO submissions VALUES('j','message','hash','https://old.example/contact','sent','evidence','date');''')
        return legacy

    def test_migrate_old_schema_without_data_loss(self):
        legacy = self.legacy_db()
        control.DB = legacy
        tables = ('batches','jobs','identities','events','workers','submissions','config')
        with sqlite3.connect(legacy) as raw:
            before = {table: [tuple(row) for row in raw.execute('SELECT * FROM ' + table)] for table in tables}
        with control.connect() as con:
            after = {table: [tuple(row) for row in con.execute('SELECT * FROM ' + table)] for table in tables}
            self.assertEqual(before, after)
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(next(row for row in con.execute('PRAGMA table_info(jobs)') if row['name'] == 'domain')['notnull'], 0)
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], control.SCHEMA_VERSION)
            self.assertEqual(con.execute('PRAGMA foreign_keys').fetchone()[0], 1)
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO identities VALUES('email:bad@example.org','missing')")
        with control.connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], control.SCHEMA_VERSION)
            self.assertEqual({table: [tuple(row) for row in con.execute('SELECT * FROM ' + table)] for table in tables}, before)

    def test_legacy_verified_preview_counts_without_new_deployment_field(self):
        legacy = self.legacy_db()
        with sqlite3.connect(legacy) as con:
            con.execute("DELETE FROM submissions WHERE job_id='j'")
            con.execute("UPDATE jobs SET stage='ready',contact_status='not_sent',data=? WHERE id='j'",
                        (json.dumps({'qa_passed': True, 'preview_verified': True}),))
        control.DB = legacy
        with control.connect() as con:
            self.assertEqual(control.batch_progress(con, 'b')['published_count'], 1)

    def test_migration_rolls_back_each_interruption_and_retries(self):
        for stage in ('copied','dropped','before_commit'):
            with self.subTest(stage=stage):
                legacy = self.legacy_db()
                con = sqlite3.connect(legacy, isolation_level=None)
                con.row_factory = sqlite3.Row
                con.execute('PRAGMA foreign_keys=ON')
                def fail(current):
                    if current == stage: raise RuntimeError('injected interruption')
                with self.assertRaisesRegex(RuntimeError, 'injected'):
                    control.migrate(con, fail)
                self.assertEqual(con.execute('PRAGMA foreign_keys').fetchone()[0], 1)
                self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 0)
                self.assertEqual(next(row for row in con.execute('PRAGMA table_info(jobs)') if row['name'] == 'domain')['notnull'], 1)
                self.assertIsNone(con.execute("SELECT 1 FROM sqlite_master WHERE name='jobs_new'").fetchone())
                self.assertEqual(con.execute('SELECT COUNT(*) FROM submissions').fetchone()[0], 1)
                control.migrate(con)
                self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], control.SCHEMA_VERSION)
                self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(), [])
                con.close()

    def authorize(self, limit=1):
        control.OUTREACH_AUTH_FILE.write_text(json.dumps({'mode': 'live', 'approved_by': 'Lucas Scaranello',
            'batch_id': self.bid, 'industry': 'electrician', 'city': 'Bauru, SP', 'max_contacts': limit}))

    def message(self):
        return 'Proposta\nhttps://preview.example\nscarasoft@example.org\n+55 14 90000-0000\nscarasoft — Lucas Scaranello'

    def contact_ready(self):
        jid = self.add()
        self.publish(jid)
        control.update(jid, 'codex', fields={'reason': 'Observed navigation overlap',
            'qualification': {'findings': ['Navigation overlap', 'Unreadable menu']},
            'source_urls': ['https://ficticia.example']})
        return jid

    def test_contact_authorization_scope_and_message(self):
        jid = self.contact_ready()
        with self.assertRaisesRegex(ValueError, 'disabled'):
            control.contact_begin(jid, 'codex', self.message(), 'https://ficticia.example/contato')
        self.authorize()
        auth = json.loads(control.OUTREACH_AUTH_FILE.read_text()); auth['city'] = 'Outra'
        control.OUTREACH_AUTH_FILE.write_text(json.dumps(auth))
        with self.assertRaisesRegex(ValueError, 'scope'):
            control.contact_begin(jid, 'codex', self.message(), 'https://ficticia.example/contato')
        self.authorize()
        with self.assertRaisesRegex(ValueError, 'signature'):
            control.contact_begin(jid, 'codex', 'https://preview.example', 'https://ficticia.example/contato')
        with control.connect() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM submissions').fetchone()[0], 0)

    def test_single_submission_uncertain_never_retried(self):
        jid = self.contact_ready(); self.authorize()
        with self.assertRaises(ValueError):
            control.contact_begin(jid, 'codex', self.message(), 'https://unrelated.example/contato')
        control.contact_begin(jid, 'codex', self.message(), 'https://ficticia.example/contato')
        with self.assertRaises(ValueError):
            control.contact_begin(jid, 'codex', self.message(), 'https://ficticia.example/contato')
        control.contact_finish(jid, 'codex', 'uncertain', 'Browser timed out after click')
        self.assertEqual(control.recover(jid, 'Worker stopped')['stage'], 'uncertain')
        with control.connect() as con:
            self.assertEqual(con.execute('SELECT status FROM submissions WHERE job_id=?', (jid,)).fetchone()[0], 'uncertain')
        with self.assertRaises(ValueError):
            control.contact_begin(jid, 'codex', self.message(), 'https://ficticia.example/contato')

    def test_simulation_does_not_create_submission(self):
        jid = self.contact_ready()
        result = control.contact_simulate(jid, 'codex', self.message(), 'https://ficticia.example/contato')
        self.assertEqual(result['stage'], 'simulated')
        with control.connect() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM submissions').fetchone()[0], 0)
        with self.assertRaisesRegex(ValueError, 'disabled'):
            control.resume_simulated(jid, 'other')
        self.authorize()
        self.assertEqual(control.resume_simulated(jid, 'other')['stage'], 'ready')

    def test_manual_contact_record_keeps_published_preview_unsent(self):
        jid = self.contact_ready()
        with self.assertRaises(ValueError):
            control.manual_outreach(jid, 'wrong', 'No eligible form', self.message())
        control.manual_outreach(jid, 'codex', 'No eligible form', self.message(),
                                'contato@ficticia.example', '+5514999999999')
        job = control.snapshot()['jobs'][0]
        self.assertEqual((job['stage'], job['contact_status']), ('manual', 'manual_required'))
        self.assertEqual(control.snapshot()['batches'][0]['published_count'], 1)
        with control.connect() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM submissions').fetchone()[0], 0)

    def test_worker_ownership_transition_and_capacity(self):
        self.bid = control.batch('electrician', 'Outra cidade', 3)['id']
        ids = [self.add(f'Empresa {n}', f'https://empresa{n}.example') for n in range(4)]
        def claim(n):
            try: return control.claim(self.bid, f'w{n}')['job']['id']
            except ValueError: return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            claimed = [x for x in pool.map(claim, range(4)) if x]
        self.assertEqual(len(claimed), 3)
        self.assertEqual(len(set(claimed)), 3)
        self.assertTrue(set(claimed) <= set(ids))
        with self.assertRaises(ValueError): control.update(claimed[0], 'wrong', 'verified')
        with self.assertRaises(ValueError): control.update(claimed[0], 'w0', 'ready')
        with self.assertRaises(ValueError): control.update(claimed[0], 'w0', 'building')
        owner = next(j['worker'] for j in control.snapshot()['jobs'] if j['id'] == claimed[0])
        control.update(claimed[0], owner, 'blocked', detail='Evidence missing')
        with self.assertRaises(ValueError): control.update(claimed[0], owner, detail='Late update')
        self.assertEqual(control.claim(self.bid, 'replacement')['job']['id'], ids[3])

    def test_cancel_and_recover_preserve_records(self):
        jid = self.contact_ready(); self.authorize()
        control.contact_begin(jid, 'codex', self.message(), 'https://ficticia.example/contato')
        result = control.cancel_batch(self.bid, 'Operator stopped test batch')
        self.assertEqual(result['status'], 'cancelled')
        with control.connect() as con:
            self.assertEqual(con.execute('SELECT status FROM submissions WHERE job_id=?', (jid,)).fetchone()[0], 'uncertain')
            self.assertEqual(con.execute('SELECT COUNT(*) FROM identities').fetchone()[0], 3)
            self.assertGreater(con.execute('SELECT COUNT(*) FROM events').fetchone()[0], 0)
        self.assertEqual(control.snapshot()['jobs'][0]['contact_status'], 'uncertain')

    def test_clear_all_protection_and_disposable_only(self):
        disposable = control.DB
        control.DB = control.ROOT / 'data/revamp.sqlite3'
        try:
            with self.assertRaisesRegex(ValueError, 'disabled'):
                control.clear_all('Never clear durable ledger')
        finally:
            control.DB = disposable
        self.add()
        result = control.clear_all('Disposable test only')
        self.assertEqual(result['cleared']['jobs'], 1)

    def test_ambiguous_name_requires_review_but_reliable_keys_dedupe(self):
        self.add(aliases=['phone:+5514999999999'])
        second = control.batch('electrician', 'Bauru, SP')['id']
        result = control.add(second, 'Ficticia Eletrica', '')
        self.assertEqual(result['identity_review']['status'], 'pending')
        self.assertEqual(next(b for b in control.snapshot()['batches'] if b['id'] == second)['pending_count'], 1)
        control.claim(second, 'reviewer')
        distinct_fields = self.fields('sem_site_confirmado', opportunity='primeiro_site', phone='+5514999999902')
        control.update(result['id'], 'reviewer', 'verified', fields=distinct_fields)
        with self.assertRaises(ValueError):
            control.update(result['id'], 'reviewer', 'qualified')
        control.update(result['id'], 'reviewer', fields={'identity_review': {'status': 'distinct',
            'reason': 'Different address and public registration', 'sources': ['https://source.example']}})
        self.assertEqual(control.update(result['id'], 'reviewer', 'qualified')['stage'], 'qualified')
        with self.assertRaises(sqlite3.IntegrityError):
            control.add(second, 'Other', '', ['phone:+5514999999999'])

    def test_verified_contact_identity_conflict_rolls_back_update(self):
        first = self.add('First', 'https://first.example')
        second = self.add('Second', 'https://second.example')
        control.claim(self.bid, 'worker')
        control.update(first, 'worker', 'verified', fields=self.fields())
        control.update(first, 'worker', 'blocked', detail='Test replacement')
        control.claim(self.bid, 'worker')
        with self.assertRaisesRegex(ValueError, 'already belongs'):
            control.update(second, 'worker', 'verified', fields=self.fields(phone='+5514999999999'))
        with control.connect() as con:
            self.assertEqual(con.execute('SELECT stage FROM jobs WHERE id=?', (second,)).fetchone()[0], 'reviewing')
            self.assertEqual(con.execute('SELECT job_id FROM identities WHERE identity=?', ('phone:+5514999999999',)).fetchone()[0], first)

    def test_production_capacity_separates_candidates_and_slots(self):
        self.bid = control.batch('electrician', 'Bauru, SP', 2)['id']
        jobs = [self.add(f'Candidate {n}', f'https://candidate{n}.example') for n in range(5)]
        progress = next(b for b in control.snapshot()['batches'] if b['id'] == self.bid)
        self.assertEqual((progress['candidate_count'], progress['evaluating_count'], progress['available_count']), (5,5,2))
        control.claim(self.bid, 'w1'); control.claim(self.bid, 'w2')
        with self.assertRaisesRegex(ValueError, 'capacity'):
            control.claim(self.bid, 'w3')
        for index, (worker, jid) in enumerate([('w1', jobs[0]), ('w2', jobs[1])]):
            control.update(jid, worker, 'verified', fields=self.fields(phone=f'+551499999990{index}'))
            control.update(jid, worker, 'qualified')
            control.update(jid, worker, 'extracting')
            control.update(jid, worker, 'building')
        progress = next(b for b in control.snapshot()['batches'] if b['id'] == self.bid)
        self.assertEqual((progress['production_count'], progress['available_count'], progress['worker_count']), (2,0,2))


if __name__ == '__main__': unittest.main()
