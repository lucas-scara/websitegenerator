import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('control', Path(__file__).parents[1] / 'tools/control.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)
commercial = control.commercial

class CommercialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = control.DB
        control.DB = Path(self.tmp.name) / 'ledger.sqlite3'
        self.old_email = os.environ.get('BR_COMMERCIAL_EMAIL')
        self.old_phone = os.environ.get('BR_COMMERCIAL_PHONE')
        os.environ['BR_COMMERCIAL_EMAIL'] = 'lucas@example.org'
        os.environ['BR_COMMERCIAL_PHONE'] = '+5514999999999'
        self.batch = control.batch('chaveiros', 'Bauru, SP', 1)['id']

    def tearDown(self):
        control.DB = self.old_db
        for key, value in [('BR_COMMERCIAL_EMAIL',self.old_email),('BR_COMMERCIAL_PHONE',self.old_phone)]:
            if value is None: os.environ.pop(key,None)
            else: os.environ[key] = value
        self.tmp.cleanup()

    def job(self, presence='sem_site_confirmado', contacts=None):
        jid = control.add(self.batch, 'Empresa Exemplo')['id']
        data = {'template':'chaveiros','preview_verified':True,'qa_passed':True,
                'presence_status':presence,'contacts': contacts or {},
                'verification': {'checked_at':control.now()[:10], 'sources':['https://example.org/verificacao']}}
        with control.connect() as con:
            con.execute('UPDATE jobs SET stage=?,preview_url=?,data=? WHERE id=?',
                        ('ready','https://preview.example',json.dumps(data),jid))
        return jid

    def test_catalog_all_segments_and_messages(self):
        self.assertEqual(set(commercial.SEARCHES), set(control.TEMPLATES))
        values = {'empresa':'Empresa Exemplo','cidade':'Bauru','segmento':'chaveiro',
                  'busca_exemplo':'chaveiro perto de mim','preview_url':'https://preview.example',
                  'observacao_verificada':'HTTP 503 em duas sondagens',
                  'assinatura':'scarasoft — Lucas Scaranello','email_comercial':'lucas@example.org',
                  'telefone_comercial':'+5514999999999'}
        for template in commercial.COPY:
            for variant in ('short','full','subject'):
                rendered = commercial.render(template,variant,values)
                self.assertIn('Empresa Exemplo',rendered)
                self.assertNotRegex(rendered,r'\{[^{}]+\}')
        for segment, (_, query) in commercial.SEARCHES.items():
            self.assertTrue(query.replace('{cidade}','Bauru'))
        with self.assertRaisesRegex(ValueError,'Missing'):
            commercial.render('primeiro_site','short',{'empresa':'Empresa Exemplo'})

    def test_routing_and_fallback(self):
        contacts = {'form':{'status':'encontrado','eligible':False,'purpose':'orçamento','url':'https://example.org/form'},
                    'email':{'status':'encontrado','value':'public@example.org'},
                    'phone':{'value':'+5514999999999'}}
        self.assertEqual(commercial.route(contacts)[0],'email')
        self.assertEqual(commercial.route({**contacts,'email':{'status':'nao_encontrado'}})[0],'whatsapp_manual')
        self.assertEqual(commercial.route({'phone':{'value':'+5514999999999'},'whatsapp':{'status':'presumido'}})[0],'whatsapp_manual')
        self.assertEqual(commercial.route({})[0],'no_channel')
        contacts['form'].update(eligible=True,purpose='contato comercial')
        self.assertEqual(commercial.route(contacts)[0],'form')
        jid = self.job(contacts=contacts)
        self.assertEqual(control.prepare_commercial(jid)['channel'],'form')
        control.record_commercial(jid,'failed_no_send','Falha observada antes de clicar em enviar')
        self.assertEqual(control.prepare_commercial(jid)['channel'],'email')
        control.record_commercial(jid,'uncertain','Janela fechou após clicar')
        with self.assertRaisesRegex(ValueError,'review'):
            control.prepare_commercial(jid)
        self.assertEqual(control.snapshot()['jobs'][0]['stage'],'ready')
        self.assertEqual(len(control.snapshot()['commercial_attempts']),2)

    def test_manual_whatsapp_not_sent_and_opt_out(self):
        jid = self.job(contacts={'phone':{'value':'+5514999999999'},'whatsapp':{'status':'presumido'}})
        prepared = control.prepare_commercial(jid)
        self.assertEqual(prepared['channel'],'whatsapp_manual')
        self.assertIn('text=',prepared['whatsapp_url'])
        self.assertEqual(control.snapshot()['jobs'][0]['contact_status'],'prepared')
        control.record_commercial(jid,'opted_out','Empresa pediu para não receber propostas')
        with self.assertRaisesRegex(ValueError,'review'):
            control.prepare_commercial(jid)

    def test_no_channel_and_missing_commercial_identity(self):
        jid = self.job()
        self.assertEqual(control.prepare_commercial(jid)['channel'],'no_channel')
        with control.connect() as con:
            data = json.loads(con.execute('SELECT data FROM jobs WHERE id=?',(jid,)).fetchone()['data'])
            data['contacts'] = {'email':{'status':'encontrado','value':'public@example.org'}}
            con.execute('UPDATE jobs SET data=? WHERE id=?',(json.dumps(data),jid))
        os.environ.pop('BR_COMMERCIAL_EMAIL')
        with self.assertRaisesRegex(ValueError,'Missing message values'):
            control.prepare_commercial(jid)
        os.environ['BR_COMMERCIAL_EMAIL'] = 'lucas@example.org'
        control.record_commercial(jid,'opted_out','Recusa explícita informada pela empresa')
        with self.assertRaisesRegex(ValueError,'review'):
            control.prepare_commercial(jid)

    def test_version_two_migration_adds_history_without_losing_rows(self):
        jid = self.job()
        with control.connect() as con:
            con.execute('DROP TABLE commercial_attempts')
            con.execute('PRAGMA user_version=2')
        with control.connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],3)
            self.assertIsNotNone(con.execute('SELECT id FROM jobs WHERE id=?',(jid,)).fetchone())
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_inoperant_requires_recent_technical_evidence(self):
        jid = self.job('site_inoperante',{'email':{'status':'encontrado','value':'public@example.org'}})
        with self.assertRaisesRegex(ValueError,'technical evidence'):
            control.prepare_commercial(jid)
        with control.connect() as con:
            row = con.execute('SELECT data FROM jobs WHERE id=?',(jid,)).fetchone()
            data = json.loads(row['data'])
            data['verification']['technical_failure'] = {'checked_at':control.now()[:10],
                'source':'https://example.org/verificacao','result':'HTTP 503 em duas sondagens','attempts':2}
            con.execute('UPDATE jobs SET data=? WHERE id=?',(json.dumps(data),jid))
        prepared = control.prepare_commercial(jid,'HTTP 503 em duas sondagens')
        self.assertIn('HTTP 503',prepared['message'])
        self.assertIn('lucas@example.org',prepared['message'])

    def test_legacy_submission_blocks_new_preparation(self):
        jid = self.job(contacts={'email':{'status':'encontrado','value':'public@example.org'}})
        with control.connect() as con:
            con.execute('INSERT INTO submissions VALUES(?,?,?,?,?,?,?)',
                        (jid,'legacy message','hash','https://example.org/form','uncertain','timeout',control.now()))
        with self.assertRaisesRegex(ValueError,'Legacy submission'):
            control.prepare_commercial(jid)
        self.assertEqual(len(control.snapshot()['legacy_submissions']),1)

if __name__ == '__main__': unittest.main()
