import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
import base64
from email import message_from_bytes, policy

spec = importlib.util.spec_from_file_location('control', Path(__file__).parents[1] / 'tools/control.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)
gmail = control.gmail_outreach

class FakeGmail:
    def __init__(self, response=None, error=None, account='scarasoftbauru@gmail.com'):
        self.response = response or {'id':'gmail12345678','threadId':'thread12345678'}
        self.error = error
        self.account = account
        self.calls = 0
        self.last_send = None
    def verify_identity(self, expected, sender):
        if self.account != expected:
            raise gmail.PreSendError('Authenticated Google account does not match authorized mailbox')
    def send(self, recipient, sender, subject, body, preview_url=None, **kwargs):
        self.calls += 1
        self.last_send = (recipient, sender, subject, body, preview_url, kwargs)
        if self.error: raise self.error
        return self.response

class GmailTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = control.DB
        self.old_files = (gmail.AUTH_FILE, gmail.SENDER_FILE)
        self.old_env = (os.environ.get('BR_COMMERCIAL_EMAIL'), os.environ.get('BR_COMMERCIAL_PHONE'))
        control.DB = Path(self.tmp.name) / 'ledger.sqlite3'
        gmail.AUTH_FILE = Path(self.tmp.name) / 'gmail-authorization.json'
        gmail.SENDER_FILE = Path(self.tmp.name) / 'gmail-sender.json'
        os.environ['BR_COMMERCIAL_EMAIL'] = 'lucas@example.org'
        os.environ['BR_COMMERCIAL_PHONE'] = '+5514999999999'
        self.batch = control.batch('chaveiros', 'Bauru, SP', 3)['id']
        self.job = self.new_job('Empresa Um', 'first@example.org')
    def tearDown(self):
        control.DB = self.old_db
        gmail.AUTH_FILE, gmail.SENDER_FILE = self.old_files
        for key, value in zip(('BR_COMMERCIAL_EMAIL','BR_COMMERCIAL_PHONE'),self.old_env):
            if value is None: os.environ.pop(key,None)
            else: os.environ[key] = value
        self.tmp.cleanup()
    def private(self, path, data):
        path.write_text(json.dumps(data))
        path.chmod(0o600)
    def authorize(self, jobs=None, max_contacts=3, daily_limit=5, sender='scarasoftbauru@gmail.com'):
        self.private(gmail.AUTH_FILE, {'mode':'live','approved_by':'Lucas Scaranello',
                     'approved_at':control.now(),'batch_id':self.batch,'job_ids':jobs or [self.job],
                     'sender':sender,'max_contacts':max_contacts,'daily_limit':daily_limit})
        self.private(gmail.SENDER_FILE, {'oauth_email':'scarasoftbauru@gmail.com','sender':sender})
    def new_job(self, name, email, form=None):
        jid = control.add(self.batch, name)['id']
        contacts = {'email':{'status':'encontrado','value':email,'source':'https://example.org/ficha','checked_at':control.now()[:10]},
                    'form':form or {'status':'nao_encontrado'}}
        data = {'template':'chaveiros','preview_verified':True,'qa_passed':True,
                'presence_status':'sem_site_confirmado','contacts':contacts,
                'verification':{'checked_at':control.now()[:10],'sources':['https://example.org/ficha']}}
        with control.connect() as c:
            c.execute('UPDATE jobs SET stage=?,preview_url=?,data=? WHERE id=?',
                      ('ready','https://preview.example',json.dumps(data),jid))
        return jid
    def prepare(self, jid=None):
        return control.prepare_commercial(jid or self.job)
    def dispatch(self, jid=None, client=None):
        return gmail.dispatch(control.gmail_ledger(), jid or self.job, client or FakeGmail())

    def test_dry_run_and_missing_authorization(self):
        self.prepare()
        result = gmail.simulate(control.gmail_ledger(),self.job)
        self.assertEqual(result['mode'],'dry_run')
        self.assertTrue(result['would_send'])
        self.assertEqual(result['preview_url'], 'https://preview.example')
        self.assertEqual(control.snapshot()['commercial_attempts'],[])
        with self.assertRaisesRegex(ValueError,'disabled'): self.dispatch()
        self.assertEqual(control.snapshot()['commercial_attempts'],[])
    def test_valid_authorization_and_confirmed_send(self):
        self.prepare(); self.authorize()
        fake = FakeGmail()
        result = self.dispatch(client=fake)
        self.assertEqual(result['status'],'sent')
        self.assertEqual(result['gmail_message_id'],'gmail12345678')
        self.assertEqual(result['gmail_thread_id'],'thread12345678')
        self.assertEqual(fake.calls,1)
        state = control.snapshot()
        self.assertEqual(state['jobs'][0]['stage'],'ready')
        self.assertEqual(state['jobs'][0]['contact_status'],'sent')
        self.assertEqual(state['commercial_attempts'][0]['source'],'gmail_api')
        with self.assertRaises(ValueError): self.dispatch(client=fake)
    def test_approval_must_include_company_and_sender(self):
        self.prepare(); self.authorize(jobs=['other-job'])
        with self.assertRaisesRegex(ValueError,'scope'): self.dispatch()
        self.authorize(sender='other@example.org')
        with self.assertRaisesRegex(ValueError,'scope'): self.dispatch()
        self.authorize()
        self.private(gmail.SENDER_FILE, {'oauth_email':'wrong@example.org','sender':'scarasoftbauru@gmail.com'})
        with self.assertRaisesRegex(ValueError,'sender'): self.dispatch()
    def test_daily_and_batch_limits(self):
        other = self.new_job('Empresa Dois','second@example.org')
        self.prepare(); self.prepare(other)
        self.authorize(jobs=[self.job,other],daily_limit=1)
        self.dispatch()
        with self.assertRaisesRegex(ValueError,'daily'): self.dispatch(other)
        self.authorize(jobs=[self.job,other],daily_limit=5,max_contacts=1)
        with self.assertRaisesRegex(ValueError,'batch'): self.dispatch(other)
    def test_optout_prior_contact_and_form_priority(self):
        self.prepare(); self.authorize()
        control.record_commercial(self.job,'opted_out','Empresa recusou')
        with self.assertRaises(ValueError): self.dispatch()
        other = self.new_job('Empresa Dois','second@example.org',
                             {'status':'encontrado','url':'https://example.org/contact','purpose':'contato comercial','eligible':True})
        self.assertEqual(self.prepare(other)['channel'],'form')
        with self.assertRaises(ValueError): self.dispatch(other)
    def test_failed_before_send_and_invalid_identity(self):
        self.prepare(); self.authorize()
        fake = FakeGmail(error=gmail.PreSendError('HTTP 403 quota'))
        result = self.dispatch(client=fake)
        self.assertEqual(result['status'],'failed_no_send')
        self.assertEqual(control.snapshot()['jobs'][0]['contact_status'],'pending')
        with self.assertRaises(ValueError): self.dispatch(client=fake)
        other = self.new_job('Empresa Dois','second@example.org')
        self.prepare(other); self.authorize(jobs=[self.job,other])
        bad = FakeGmail(account='wrong@example.org')
        result = self.dispatch(other,bad)
        self.assertEqual(result['status'],'failed_no_send')
        self.assertEqual(bad.calls,0)
    def test_invalid_or_expired_token_is_failed_without_send(self):
        self.prepare(); self.authorize()
        class ExpiredToken(FakeGmail):
            def verify_identity(self, expected, sender):
                raise gmail.PreSendError('Gmail OAuth token is invalid or expired')
        client = ExpiredToken()
        self.assertEqual(self.dispatch(client=client)['status'],'failed_no_send')
        self.assertEqual(client.calls,0)
    def test_utf8_mail_has_one_recipient_and_no_attachments(self):
        class Response:
            status_code = 200
            def json(self): return {'id':'gmail12345678'}
        class Session:
            def post(self, url, json, timeout):
                raw = base64.urlsafe_b64decode(json['raw'] + '===')
                msg = message_from_bytes(raw, policy=policy.default)
                self_outer.assertEqual(msg['To'],'empresa@example.org')
                self_outer.assertIn('scarasoftbauru@gmail.com',msg['From'])
                self_outer.assertIsNone(msg['Cc'])
                self_outer.assertIsNone(msg['Bcc'])
                self_outer.assertEqual(len(list(msg.iter_attachments())),0)
                self_outer.assertIn('prévia',msg.get_content())
                return Response()
        self_outer = self
        client = gmail.GmailClient.__new__(gmail.GmailClient)
        client.session = Session()
        self.assertEqual(client.send('empresa@example.org','scarasoftbauru@gmail.com','Proposta','Veja a prévia')['id'],'gmail12345678')
    def test_named_preview_link_has_safe_html_and_plain_fallback(self):
        prepared = self.prepare()
        self.assertIn('Ver a prévia do site', prepared['message'])
        self.assertNotIn('https://preview.example', prepared['message'])
        class Response:
            status_code = 200
            def json(self): return {'id':'gmail12345678'}
        class Session:
            def post(self, url, json, timeout):
                msg = message_from_bytes(base64.urlsafe_b64decode(json['raw'] + '==='), policy=policy.default)
                self_outer.assertTrue(msg.is_multipart())
                plain, html = list(msg.iter_parts())
                self_outer.assertIn('Ver a prévia do site: https://preview.example',plain.get_content())
                self_outer.assertIn('<a href="https://preview.example">Ver a prévia do site</a>',html.get_content())
                self_outer.assertNotIn('https://preview.example</p>',html.get_content())
                self_outer.assertIsNone(msg['Cc'])
                self_outer.assertIsNone(msg['Bcc'])
                return Response()
        self_outer = self
        client = gmail.GmailClient.__new__(gmail.GmailClient)
        client.session = Session()
        client.send('empresa@example.org','scarasoftbauru@gmail.com',prepared['subject'],
                    prepared['message'],'https://preview.example')
    def test_followup_mime_replies_in_original_gmail_thread(self):
        class Response:
            status_code = 200
            def json(self): return {'id':'gmail12345678','threadId':'thread12345678'}
        class Session:
            def post(self, url, json, timeout):
                self_outer.assertEqual(json['threadId'], 'thread12345678')
                msg = message_from_bytes(base64.urlsafe_b64decode(json['raw'] + '==='), policy=policy.default)
                self_outer.assertEqual(msg['Message-ID'], '<followup@scarasoft.com.br>')
                self_outer.assertEqual(msg['In-Reply-To'], '<first@scarasoft.com.br>')
                self_outer.assertEqual(msg['References'], '<first@scarasoft.com.br>')
                self_outer.assertEqual(msg['To'], 'empresa@example.org')
                self_outer.assertIsNone(msg['Cc'])
                self_outer.assertIsNone(msg['Bcc'])
                return Response()
        self_outer = self
        client = gmail.GmailClient.__new__(gmail.GmailClient)
        client.session = Session()
        client.send('empresa@example.org','scarasoftbauru@gmail.com','Assunto',
                    gmail.followup_message('Empresa Um', 1),
                    message_id='<followup@scarasoft.com.br>', thread_id='thread12345678',
                    in_reply_to='<first@scarasoft.com.br>', references='<first@scarasoft.com.br>')
    def test_gmail_quota_rejection_is_definite_and_server_error_uncertain(self):
        class Response:
            def __init__(self, code): self.status_code = code
        class Session:
            def __init__(self, code): self.code = code
            def post(self, url, json, timeout): return Response(self.code)
        client = gmail.GmailClient.__new__(gmail.GmailClient)
        for code in (401,403,429):
            client.session = Session(code)
            with self.assertRaises(gmail.PreSendError):
                client.send('empresa@example.org','scarasoftbauru@gmail.com','Proposta','Corpo')
        client.session = Session(503)
        with self.assertRaises(gmail.UncertainError):
            client.send('empresa@example.org','scarasoftbauru@gmail.com','Proposta','Corpo')
    def test_timeout_uncertain_and_explicit_reconciliation(self):
        self.prepare(); self.authorize()
        result = self.dispatch(client=FakeGmail(error=TimeoutError()))
        self.assertEqual(result['status'],'uncertain')
        with self.assertRaises(ValueError): self.dispatch()
        self.assertEqual(control.snapshot()['jobs'][0]['stage'],'ready')
        reconciled = gmail.reconcile(control.gmail_ledger(),result['attempt_id'],'sent',
                                      'Confirmação manual no Gmail enviado','confirmed12345')
        self.assertEqual(reconciled['status'],'sent')
    def test_optout_recorded_during_send_is_preserved(self):
        self.prepare(); self.authorize()
        class OptOutDuringSend(FakeGmail):
            def send(self, recipient, sender, subject, body, preview_url=None, **kwargs):
                control.record_commercial(self_outer.job,'opted_out','Pedido recebido durante a tentativa')
                return super().send(recipient,sender,subject,body,preview_url,**kwargs)
        self_outer = self
        self.assertEqual(self.dispatch(client=OptOutDuringSend())['status'],'sent')
        self.assertEqual(control.snapshot()['jobs'][0]['contact_status'],'opted_out')
    def age_first_send(self, days):
        at = (control.dt.datetime.now(control.dt.timezone.utc) - control.dt.timedelta(days=days)).isoformat(timespec='seconds')
        with control.connect() as c:
            c.execute("UPDATE commercial_attempts SET created_at=? WHERE job_id=? AND source='gmail_api' AND touch=0", (at,self.job))
    def test_followup_day4_and_day10_same_thread(self):
        self.prepare(); self.authorize()
        self.dispatch()
        self.age_first_send(11)
        plan = control.snapshot()['gmail_followups'][self.job]
        self.assertEqual(plan['next_touch'],1)
        self.assertTrue(plan['due'])
        self.assertIn('Empresa Um',plan['message'])
        fake = FakeGmail()
        result = gmail.dispatch(control.gmail_ledger(),self.job,fake,touch=1)
        self.assertEqual(result['status'],'sent')
        self.assertEqual(fake.last_send[-1]['thread_id'],'thread12345678')
        first = next(r for r in control.snapshot()['commercial_attempts'] if r['touch'] == 0)
        self.assertEqual(fake.last_send[-1]['in_reply_to'],first['rfc_message_id'])
        self.assertEqual(control.snapshot()['gmail_followups'][self.job]['next_touch'],2)
        final = gmail.dispatch(control.gmail_ledger(),self.job,FakeGmail(),touch=2)
        self.assertEqual(final['status'],'sent')
        self.assertIsNone(control.snapshot()['gmail_followups'][self.job]['next_touch'])
        self.assertEqual(control.snapshot()['jobs'][0]['contact_status'],'sent')
    def test_followup_not_due_or_after_response_and_no_duplicates(self):
        self.prepare(); self.authorize()
        self.dispatch()
        with self.assertRaisesRegex(ValueError,'not due'):
            gmail.dispatch(control.gmail_ledger(),self.job,FakeGmail(),touch=1)
        self.age_first_send(5)
        control.record_commercial(self.job,'replied','Empresa respondeu')
        with self.assertRaisesRegex(ValueError,'blocked'):
            gmail.dispatch(control.gmail_ledger(),self.job,FakeGmail(),touch=1)
    def test_followup_daily_limit_and_concurrent_reservation(self):
        self.prepare(); self.authorize()
        self.dispatch(); self.age_first_send(5)
        other = self.new_job('Empresa Dois','second@example.org')
        self.prepare(other); self.authorize(jobs=[self.job,other],daily_limit=1)
        self.dispatch(other)
        with self.assertRaisesRegex(ValueError,'daily'):
            gmail.dispatch(control.gmail_ledger(),self.job,FakeGmail(),touch=1)
        self.authorize(jobs=[self.job,other],daily_limit=5)
        results = []
        def worker():
            try: results.append(gmail.dispatch(control.gmail_ledger(),self.job,FakeGmail(),touch=1))
            except ValueError: results.append('blocked')
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(sum(isinstance(r,dict) for r in results),1)
    def test_legacy_initial_send_without_rfc_id_requires_manual_reply(self):
        self.prepare(); self.authorize()
        self.dispatch(); self.age_first_send(5)
        with control.connect() as c:
            c.execute("UPDATE commercial_attempts SET rfc_message_id=NULL WHERE job_id=? AND source='gmail_api' AND touch=0", (self.job,))
        plan = control.snapshot()['gmail_followups'][self.job]
        self.assertIsNone(plan['next_touch'])
        self.assertIn('manualmente',plan['reason'])
    def test_concurrent_reservation_and_history_preserved(self):
        self.prepare(); self.authorize()
        with control.connect() as c:
            c.execute("INSERT INTO commercial_attempts(job_id,channel,status,message,evidence,created_at) VALUES(?,?,?,?,?,?)",
                      (self.job,'form','failed_no_send','historical','old proof',control.now()))
        results = []
        def worker():
            try: results.append(self.dispatch(client=FakeGmail()))
            except ValueError: results.append('blocked')
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(len([r for r in results if isinstance(r,dict)]),1)
        self.assertEqual(len(control.snapshot()['commercial_attempts']),2)
        self.assertEqual(control.snapshot()['jobs'][0]['stage'],'ready')

if __name__ == '__main__': unittest.main()
