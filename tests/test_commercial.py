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
        os.environ['BR_COMMERCIAL_EMAIL'] = 'lucas@example.org'
        self.batch = control.batch('chaveiros', 'Bauru, SP', 1)['id']

    def tearDown(self):
        control.DB = self.old_db
        if self.old_email is None: os.environ.pop('BR_COMMERCIAL_EMAIL',None)
        else: os.environ['BR_COMMERCIAL_EMAIL'] = self.old_email
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

    def valid_email_contacts(self):
        checked = control.now()[:10]
        return {'email': {'status':'encontrado', 'value':'public@example.org', 'source':'https://example.org/contato', 'checked_at':checked},
                'form': {'status':'nao_encontrado', 'source':'https://example.org/contato', 'checked_at':checked}}

    def add_old_phone(self, jid):
        with control.connect() as con:
            data = json.loads(con.execute('SELECT data FROM jobs WHERE id=?', (jid,)).fetchone()['data'])
            data['commercial_contact']['message'] += '\n+55 11 90000-0000'
            con.execute('UPDATE jobs SET data=? WHERE id=?', (json.dumps(data), jid))
        return data['commercial_contact']['message']

    def test_explicit_regeneration_preserves_route_and_audit(self):
        jid = self.job(contacts=self.valid_email_contacts())
        original = control.prepare_commercial(jid)
        old_message = self.add_old_phone(jid)
        before = control.snapshot()
        self.assertTrue(before['jobs'][0]['commercial_requires_review'])
        self.assertTrue(before['jobs'][0]['commercial_can_regenerate'])
        with self.assertRaisesRegex(ValueError, 'already prepared'):
            control.prepare_commercial(jid)
        refreshed = control.regenerate_commercial(jid)
        self.assertEqual((refreshed['channel'], refreshed['destination']), (original['channel'], original['destination']))
        self.assertEqual(refreshed['message'], original['message'])
        self.assertFalse(commercial.message_has_phone(refreshed['message']))
        after = control.snapshot()
        self.assertFalse(after['jobs'][0]['commercial_requires_review'])
        self.assertFalse(after['jobs'][0]['commercial_can_regenerate'])
        self.assertEqual(after['jobs'][0]['contact_status'], 'prepared')
        self.assertEqual(after['commercial_attempts'], before['commercial_attempts'])
        self.assertIn('prior_sha256=', after['events'][0]['message'])
        self.assertIn('new_sha256=', after['events'][0]['message'])
        self.assertNotIn(old_message, after['events'][0]['message'])
        with self.assertRaisesRegex(ValueError, 'Only a prepared message'):
            control.regenerate_commercial(jid)

    def test_regeneration_rejects_changed_route_and_invalid_preview_or_contacts(self):
        jid = self.job(contacts=self.valid_email_contacts())
        control.prepare_commercial(jid)
        old_message = self.add_old_phone(jid)
        with control.connect() as con:
            data = json.loads(con.execute('SELECT data FROM jobs WHERE id=?',(jid,)).fetchone()['data'])
            data['contacts']['email']['value'] = 'changed@example.org'
            con.execute('UPDATE jobs SET data=? WHERE id=?',(json.dumps(data),jid))
        self.assertFalse(control.snapshot()['jobs'][0]['commercial_can_regenerate'])
        with self.assertRaisesRegex(ValueError, 'channel and recipient'):
            control.regenerate_commercial(jid)
        with control.connect() as con:
            data['contacts']['email']['value'] = 'public@example.org'
            data['contacts']['email']['source'] = ''
            con.execute('UPDATE jobs SET data=? WHERE id=?',(json.dumps(data),jid))
        with self.assertRaisesRegex(ValueError, 'contacts'):
            control.regenerate_commercial(jid)
        with control.connect() as con:
            data['contacts']['email']['source'] = 'https://example.org/contato'
            con.execute('UPDATE jobs SET preview_url=?,data=? WHERE id=?', ('http://preview.example',json.dumps(data),jid))
        with self.assertRaisesRegex(ValueError, 'verified public preview'):
            control.regenerate_commercial(jid)
        self.assertEqual(control.snapshot()['jobs'][0]['data']['commercial_contact']['message'], old_message)

    def test_regeneration_rejects_sent_uncertain_pending_and_optout_history(self):
        for prior_status in ('sent', 'uncertain', 'attempting', 'opted_out', 'failed_no_send'):
            with self.subTest(status=prior_status):
                jid = self.job(contacts=self.valid_email_contacts())
                control.prepare_commercial(jid)
                old_message = self.add_old_phone(jid)
                with control.connect() as con:
                    con.execute('INSERT INTO commercial_attempts(job_id,channel,status,message,evidence,created_at) VALUES(?,?,?,?,?,?)',
                                (jid,'email',prior_status,old_message,'Histórico preservado',control.now()))
                before = control.snapshot()
                with self.assertRaisesRegex(ValueError, 'attempt|recipient'):
                    control.regenerate_commercial(jid)
                after = control.snapshot()
                self.assertEqual(after['jobs'][0]['data']['commercial_contact']['message'],old_message)
                self.assertEqual(after['commercial_attempts'],before['commercial_attempts'])
                self.assertFalse(after['jobs'][0]['commercial_can_regenerate'])

    def test_regeneration_keeps_prior_failed_attempt_and_email_priority(self):
        contacts = self.valid_email_contacts()
        contacts['form'] = {'status':'encontrado', 'eligible':True, 'purpose':'contato comercial',
                            'url':'https://example.org/form', 'source':'https://example.org/form',
                            'checked_at':control.now()[:10], 'restrictions':[]}
        jid = self.job(contacts=contacts)
        self.assertEqual(control.prepare_commercial(jid)['channel'], 'form')
        control.record_commercial(jid, 'failed_no_send', 'Falhou antes do envio')
        prepared = control.prepare_commercial(jid)
        self.assertEqual(prepared['channel'], 'email')
        self.add_old_phone(jid)
        prior = control.snapshot()['commercial_attempts']
        regenerated = control.regenerate_commercial(jid)
        self.assertEqual((regenerated['channel'],regenerated['destination']), ('email','public@example.org'))
        self.assertEqual(control.snapshot()['commercial_attempts'],prior)

    def test_regeneration_rejects_legacy_submission(self):
        jid = self.job(contacts=self.valid_email_contacts())
        control.prepare_commercial(jid)
        old_message = self.add_old_phone(jid)
        with control.connect() as con:
            con.execute('INSERT INTO submissions VALUES(?,?,?,?,?,?,?)',
                        (jid,old_message,'old-hash','https://example.org/form','attempting',None,control.now()))
        with self.assertRaisesRegex(ValueError, 'submission'):
            control.regenerate_commercial(jid)
        state = control.snapshot()
        self.assertEqual(state['jobs'][0]['data']['commercial_contact']['message'],old_message)
        self.assertFalse(state['jobs'][0]['commercial_can_regenerate'])

    def test_regeneration_uses_current_redesign_and_inoperante_models(self):
        for presence in ('site_confirmado', 'site_inoperante'):
            with self.subTest(presence=presence):
                jid = self.job(presence=presence, contacts=self.valid_email_contacts())
                observation = ''
                if presence == 'site_inoperante':
                    observation = 'HTTP 503 em duas tentativas'
                    with control.connect() as con:
                        data = json.loads(con.execute('SELECT data FROM jobs WHERE id=?',(jid,)).fetchone()['data'])
                        data['verification']['technical_failure'] = {'checked_at':control.now()[:10],
                            'source':'https://example.org/site', 'result':observation, 'attempts':2}
                        con.execute('UPDATE jobs SET data=? WHERE id=?',(json.dumps(data),jid))
                expected = control.prepare_commercial(jid, observation)
                self.add_old_phone(jid)
                regenerated = control.regenerate_commercial(jid)
                self.assertEqual(regenerated['template'],expected['template'])
                self.assertEqual(regenerated['message'],expected['message'])
                self.assertFalse(commercial.message_has_phone(regenerated['message']))

    def test_regeneration_never_changes_a_confirmed_send(self):
        jid = self.job(contacts=self.valid_email_contacts())
        control.prepare_commercial(jid)
        old_message = self.add_old_phone(jid)
        with control.connect() as con:
            con.execute('UPDATE jobs SET contact_status=? WHERE id=?', ('sent',jid))
        with self.assertRaisesRegex(ValueError, 'Only a prepared message'):
            control.regenerate_commercial(jid)
        self.assertEqual(control.snapshot()['jobs'][0]['data']['commercial_contact']['message'],old_message)

    def test_catalog_all_segments_and_messages(self):
        self.assertEqual(set(commercial.SEARCHES), set(control.TEMPLATES))
        values = {'empresa':'Empresa Exemplo','cidade':'Bauru','segmento':'chaveiro',
                  'busca_exemplo':'chaveiro perto de mim','preview_url':'https://preview.example',
                  'observacao_verificada':'HTTP 503 em duas sondagens',
                  'email_comercial':'lucas@example.org'}
        for template in commercial.COPY:
            for variant in ('short','full','subject'):
                rendered = commercial.render(template,variant,values)
                self.assertIn('Empresa Exemplo',rendered)
                self.assertNotRegex(rendered,r'\{[^{}]+\}')
            short = commercial.render(template,'short',values)
            for word in ('serviços','confiança','contato','não oficial'):
                self.assertIn(word,short)
            full = commercial.render(template,'full',values)
            self.assertIn('Lucas Scaranello\nscarasoft\nlucas@example.org',full)
            self.assertFalse(commercial.message_has_phone(full))
            self.assertNotIn('+5514999999999',full)
        self.assertTrue(commercial.message_has_phone('Fale comigo pelo (11) 98888-7777.'))
        self.assertFalse(commercial.message_has_phone('https://preview.example/11988887777'))
        self.assertIn('chaveiro perto de mim',commercial.render('redesign','short',values))
        for segment, (_, query) in commercial.SEARCHES.items():
            self.assertTrue(query.replace('{cidade}','Bauru'))
        with self.assertRaisesRegex(ValueError,'Missing'):
            commercial.render('primeiro_site','short',{'empresa':'Empresa Exemplo'})

    def test_routing_and_fallback(self):
        contacts = {'form':{'status':'encontrado','eligible':False,'purpose':'orçamento','url':'https://example.org/form'},
                    'email':{'status':'encontrado','value':'public@example.org'},
                    'phone':{'value':'+5514999999999','source':'https://example.org/ficha','checked_at':control.now()[:10]}}
        self.assertEqual(commercial.route(contacts)[0],'email')
        self.assertEqual(commercial.route({**contacts,'email':{'status':'nao_encontrado'}})[0],'whatsapp_manual')
        self.assertEqual(commercial.route({'phone':contacts['phone'],'whatsapp':{'status':'presumido'}})[0],'whatsapp_manual')
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

    def test_form_and_whatsapp_signatures_have_only_commercial_email(self):
        form_contacts = {'form': {'status':'encontrado','eligible':True,'purpose':'contato comercial','url':'https://example.org/contato'}}
        jid = self.job(contacts=form_contacts)
        form = control.prepare_commercial(jid)
        self.assertEqual(form['channel'],'form')
        self.assertTrue(form['message'].endswith('Lucas Scaranello\nscarasoft\nlucas@example.org'))
        self.assertNotIn('+5514999999999',form['message'])
        control.record_commercial(jid,'failed_no_send','Nenhum envio ocorreu')
        with control.connect() as con:
            data = json.loads(con.execute('SELECT data FROM jobs WHERE id=?',(jid,)).fetchone()['data'])
            data['contacts'] = {'phone':{'value':'+5514999999999','source':'https://example.org/ficha','checked_at':control.now()[:10]}}
            con.execute('UPDATE jobs SET data=? WHERE id=?',(json.dumps(data),jid))
        whatsapp = control.prepare_commercial(jid)
        self.assertEqual(whatsapp['channel'],'whatsapp_manual')
        self.assertTrue(whatsapp['message'].endswith('Lucas Scaranello\nscarasoft\nlucas@example.org'))
        self.assertNotIn('+5514999999999',whatsapp['message'])
        self.assertIn('wa.me/5514999999999',whatsapp['whatsapp_url'])

    def test_local_env_loader_ignores_legacy_commercial_phone(self):
        old_root = control.ROOT
        old_email = os.environ.pop('BR_COMMERCIAL_EMAIL', None)
        old_phone = os.environ.pop('BR_COMMERCIAL_PHONE', None)
        try:
            control.ROOT = Path(self.tmp.name)
            (control.ROOT / '.env').write_text('BR_COMMERCIAL_EMAIL=contato@scarasoft.com.br\nBR_COMMERCIAL_PHONE=+5511900000000\n')
            control.load_commercial_env()
            self.assertEqual(os.environ['BR_COMMERCIAL_EMAIL'],'contato@scarasoft.com.br')
            self.assertNotIn('BR_COMMERCIAL_PHONE',os.environ)
        finally:
            control.ROOT = old_root
            if old_email is not None: os.environ['BR_COMMERCIAL_EMAIL'] = old_email
            if old_phone is not None: os.environ['BR_COMMERCIAL_PHONE'] = old_phone

    def test_manual_whatsapp_not_sent_and_opt_out(self):
        jid = self.job(contacts={'phone':{'value':'+5514999999999','source':'https://example.org/ficha','checked_at':control.now()[:10]},'whatsapp':{'status':'presumido'}})
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

    def test_whatsapp_requires_traceable_public_number_and_respects_contrary_evidence(self):
        phone = {'value':'+5514999999999','source':'https://example.org/ficha','checked_at':control.now()[:10]}
        self.assertEqual(commercial.route({'phone':phone})[0],'whatsapp_manual')
        for invalid in ({'value':phone['value']},{**phone,'source':'javascript:bad'},
                        {**phone,'source':'http://localhost/ficha'},
                        {**phone,'checked_at':'2026-02-30'},{**phone,'value':'123'}):
            self.assertEqual(commercial.route({'phone':invalid})[0],'no_channel')
        for contrary in (False,{'status':'nao_utiliza'}):
            self.assertEqual(commercial.route({'phone':phone,'whatsapp':contrary})[0],'no_channel')
        confirmed = {'status':'confirmado','value':'+5514888888888',
                     'source':'https://example.org/whatsapp','checked_at':control.now()[:10]}
        self.assertEqual(commercial.route({'phone':phone,'whatsapp':confirmed}),('whatsapp_manual',confirmed['value']))
        self.assertEqual(commercial.route({'phone':phone,'whatsapp':{**confirmed,'source':''}})[0],'no_channel')

    def test_response_requires_confirmed_contact_and_external_proof(self):
        jid = self.job(contacts={'email':{'status':'encontrado','value':'public@example.org'}})
        control.prepare_commercial(jid)
        for response in ('replied','interested','not_interested'):
            with self.assertRaisesRegex(ValueError,'confirmed prior contact'):
                control.record_commercial(jid,response,'Empresa respondeu')
        with self.assertRaisesRegex(ValueError,'reference'):
            control.record_commercial(jid,'sent','Envio observado')
        result = control.record_commercial(jid,'sent_external','Envio feito fora do dashboard',
                                            'email','id:message-12345678')
        self.assertEqual(result['contact_status'],'sent')
        with self.assertRaisesRegex(ValueError,'duplicate contact'):
            control.record_commercial(jid,'sent_external','Segundo envio','email','id:message-87654321')
        control.record_commercial(jid,'replied','Resposta recebida por e-mail')
        control.record_commercial(jid,'interested','Empresa pediu detalhes')
        job = control.snapshot()['jobs'][0]
        self.assertEqual((job['stage'],job['contact_status']),('ready','interested'))
        self.assertEqual(job['preview_url'],'https://preview.example')
        self.assertEqual(control.snapshot()['commercial_attempts'][-1]['status'],'sent_external')

    def test_explicit_external_contact_from_pending_and_opt_out(self):
        jid = self.job()
        with self.assertRaisesRegex(ValueError,'confirmed prior contact'):
            control.record_commercial(jid,'replied','Resposta sem contato')
        with self.assertRaisesRegex(ValueError,'channel'):
            control.record_commercial(jid,'sent_external','Envio fora do sistema',proof='id:message-12345678')
        with self.assertRaisesRegex(ValueError,'reference'):
            control.record_commercial(jid,'sent_external','Envio fora do sistema',channel='email')
        control.record_commercial(jid,'sent_external','Comprovante do contato feito fora do sistema',
                                  'email','https://example.org/comprovante')
        control.record_commercial(jid,'opted_out','Solicitou exclusão da lista')
        with self.assertRaisesRegex(ValueError,'Opt-out'):
            control.record_commercial(jid,'sent_external','Novo envio','email','id:message-87654321')

    def test_prepared_send_requires_proof_and_legacy_send_supports_response(self):
        jid = self.job(contacts={'email':{'status':'encontrado','value':'public@example.org'}})
        control.prepare_commercial(jid)
        control.record_commercial(jid,'sent','Envio observado no e-mail','', 'id:message-12345678')
        control.record_commercial(jid,'replied','Resposta observada no e-mail')
        self.assertEqual(control.snapshot()['jobs'][0]['contact_status'],'replied')
        with self.assertRaisesRegex(ValueError,'duplicate contact'):
            control.record_commercial(jid,'sent_external','Nova tentativa','email','id:message-87654321')

        other = control.add(self.batch,'Outra Empresa')['id']
        with control.connect() as con:
            con.execute("UPDATE jobs SET stage='sent',contact_status='sent' WHERE id=?",(other,))
        with self.assertRaisesRegex(ValueError,'recorded send confirmation'):
            control.record_commercial(other,'replied','Resposta sem envio comprovado')
        with control.connect() as con:
            con.execute('INSERT INTO submissions VALUES(?,?,?,?,?,?,?)',
                        (other,'Mensagem legada','hash','https://example.org/contato','sent','Comprovante legado',control.now()))
        control.record_commercial(other,'replied','Resposta ao envio legado')

    def test_version_two_migration_adds_history_without_losing_rows(self):
        jid = self.job()
        with control.connect() as con:
            con.execute('DROP TABLE commercial_attempts')
            con.execute('PRAGMA user_version=2')
        with control.connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],control.SCHEMA_VERSION)
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
