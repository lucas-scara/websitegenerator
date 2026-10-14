import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
import base64
from email import message_from_bytes, policy
from email.utils import parseaddr

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
    def test_oauth_scopes_use_canonical_userinfo_email(self):
        self.assertEqual(gmail.SCOPES, [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/gmail.send',
        ])
        self.assertNotIn('email', gmail.SCOPES)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = control.DB
        self.old_files = (gmail.AUTH_FILE, gmail.SENDER_FILE)
        self.old_email = os.environ.get('BR_COMMERCIAL_EMAIL')
        control.DB = Path(self.tmp.name) / 'ledger.sqlite3'
        gmail.AUTH_FILE = Path(self.tmp.name) / 'gmail-authorization.json'
        gmail.SENDER_FILE = Path(self.tmp.name) / 'gmail-sender.json'
        os.environ['BR_COMMERCIAL_EMAIL'] = 'lucas@example.org'
        self.batch = control.batch('chaveiros', 'Bauru, SP', 3)['id']
        self.job = self.new_job('Empresa Um', 'first@example.org')
    def tearDown(self):
        control.DB = self.old_db
        gmail.AUTH_FILE, gmail.SENDER_FILE = self.old_files
        if self.old_email is None: os.environ.pop('BR_COMMERCIAL_EMAIL',None)
        else: os.environ['BR_COMMERCIAL_EMAIL'] = self.old_email
        self.tmp.cleanup()
    def private(self, path, data):
        path.write_text(json.dumps(data))
        path.chmod(0o600)
    def authorize(self, jobs=None, max_contacts=3, daily_limit=20, sender='scarasoftbauru@gmail.com', **overrides):
        auth = {'mode':'live','approved_by':'Lucas Scaranello',
                     'approved_at':control.now(),'batch_id':self.batch,'job_ids':jobs or [self.job],
                     'sender':sender,'max_contacts':max_contacts,'daily_limit':daily_limit}
        auth.update(overrides)
        self.private(gmail.AUTH_FILE, auth)
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

    def seed_sent_attempts(self, count):
        """Fill today's global Gmail ledger using isolated historical contacts."""
        for index in range(count):
            batch_id = control.batch('chaveiros', f'Cidade anterior {index}', 1)['id']
            jid = control.add(batch_id, f'Contato anterior {index}')['id']
            with control.connect() as c:
                c.execute('''INSERT INTO commercial_attempts
                    (job_id,channel,status,message,evidence,created_at,source,recipient,sender,subject,touch)
                    VALUES(?,?,?,?,?,?,?,?,?,?,0)''',
                    (jid, 'email', 'sent', 'prior', 'confirmed', control.now(), 'gmail_api',
                     f'prior{index}@example.org', 'scarasoftbauru@gmail.com', 'Prior'))

    def test_dry_run_and_missing_authorization(self):
        self.prepare()
        result = gmail.simulate(control.gmail_ledger(),self.job)
        self.assertEqual(result['mode'],'dry_run')
        self.assertTrue(result['commercial_eligibility']['eligible'])
        self.assertFalse(result['live_authorized'])
        self.assertFalse(result['would_send_live'])
        self.assertFalse(result['would_send'])
        self.assertEqual(result['preview_url'], 'https://preview.example')
        self.assertEqual(control.snapshot()['commercial_attempts'],[])
        with self.assertRaisesRegex(ValueError,'disabled'): self.dispatch()
        self.assertEqual(control.snapshot()['commercial_attempts'],[])
    def test_simulation_separates_commercial_eligibility_and_live_approval(self):
        self.prepare(); self.authorize()
        ready = gmail.simulate(control.gmail_ledger(), self.job)
        self.assertTrue(ready['commercial_eligibility']['eligible'])
        self.assertTrue(ready['live_authorized'])
        self.assertTrue(ready['would_send_live'])
        with control.connect() as c:
            data = json.loads(c.execute('SELECT data FROM jobs WHERE id=?', (self.job,)).fetchone()['data'])
            data['contacts']['form'] = {'status':'encontrado','url':'https://example.org/contato',
                                        'purpose':'contato comercial','eligible':True}
            c.execute('UPDATE jobs SET data=? WHERE id=?', (json.dumps(data),self.job))
        blocked = gmail.simulate(control.gmail_ledger(), self.job)
        self.assertFalse(blocked['commercial_eligibility']['eligible'])
        self.assertTrue(blocked['live_authorized'])
        self.assertFalse(blocked['would_send_live'])
        self.assertIsNone(blocked['recipient'])
        self.assertEqual(control.snapshot()['commercial_attempts'], [])
    def test_simulation_reports_daily_capacity_without_reserving(self):
        other = self.new_job('Empresa Dois', 'second@example.org')
        self.prepare(); self.prepare(other)
        self.authorize(jobs=[self.job,other],daily_limit=1)
        self.dispatch()
        before = len(control.snapshot()['commercial_attempts'])
        result = gmail.simulate(control.gmail_ledger(),other)
        self.assertTrue(result['commercial_eligibility']['eligible'])
        self.assertFalse(result['live_authorized'])
        self.assertIn('daily',result['authorization']['reason'])
        self.assertEqual(len(control.snapshot()['commercial_attempts']),before)
    def test_authorization_dates_and_optional_expiration(self):
        self.prepare()
        now = control.dt.datetime.now(control.dt.timezone.utc)
        future = (now + control.dt.timedelta(days=1)).isoformat()
        past = (now - control.dt.timedelta(days=1)).isoformat()
        for invalid in ('yesterday','2026-10-12','2026-10-12T12:00:00',future):
            with self.subTest(approved_at=invalid):
                self.authorize(approved_at=invalid)
                self.assertFalse(gmail.authorization(control.gmail_ledger(),
                    control.snapshot()['jobs'][0])['authorized'])
                with self.assertRaisesRegex(ValueError,'date'): self.dispatch()
        for expiry in ('bad date', past, future.replace('+00:00','')):
            with self.subTest(expires_at=expiry):
                self.authorize(approved_at=past,expires_at=expiry)
                with self.assertRaisesRegex(ValueError,'date'): self.dispatch()
        self.authorize(approved_at=past,expires_at=future)
        self.assertTrue(gmail.simulate(control.gmail_ledger(),self.job)['live_authorized'])
        self.assertEqual(control.snapshot()['commercial_attempts'],[])
    def test_valid_authorization_and_confirmed_send(self):
        self.prepare(); self.authorize()
        fake = FakeGmail()
        result = self.dispatch(client=fake)
        self.assertEqual(result['status'],'sent')
        self.assertEqual(result['gmail_message_id'],'gmail12345678')
        self.assertEqual(result['gmail_thread_id'],'thread12345678')
        self.assertEqual(fake.calls,1)
        self.assertIn('Lucas Scaranello\nscarasoft\nlucas@example.org',fake.last_send[3])
        self.assertNotIn('+5514999999999',fake.last_send[3])
        state = control.snapshot()
        self.assertEqual(state['jobs'][0]['stage'],'ready')
        self.assertEqual(state['jobs'][0]['contact_status'],'sent')
        self.assertEqual(state['commercial_attempts'][0]['source'],'gmail_api')
        with self.assertRaises(ValueError): self.dispatch(client=fake)
    def test_followups_do_not_include_phone(self):
        for touch in (1, 2):
            message = gmail.followup_message('Empresa Um', touch)
            self.assertFalse(control.commercial.message_has_phone(message))
            self.assertNotIn('+5514999999999', message)
    def test_old_prepared_signature_is_blocked_without_changing_history(self):
        prepared = self.prepare(); self.authorize()
        old_message = prepared['message'].replace('lucas@example.org', 'lucas@example.org\n+55 14 90000-0000')
        with control.connect() as c:
            row = c.execute('SELECT data FROM jobs WHERE id=?',(self.job,)).fetchone()
            data = json.loads(row['data'])
            data['commercial_contact']['message'] = old_message
            c.execute('UPDATE jobs SET data=? WHERE id=?',(json.dumps(data),self.job))
        before = control.snapshot()
        self.assertTrue(before['jobs'][0]['commercial_requires_review'])
        self.assertFalse(gmail.simulate(control.gmail_ledger(),self.job)['commercial_eligibility']['eligible'])
        fake = FakeGmail()
        with self.assertRaisesRegex(ValueError,'phone number'):
            self.dispatch(client=fake)
        after = control.snapshot()
        self.assertEqual(fake.calls,0)
        self.assertEqual(after['commercial_attempts'],before['commercial_attempts'])
        self.assertEqual(after['jobs'][0]['data']['commercial_contact']['message'],old_message)
    def test_sent_history_is_not_rewritten_when_old_signature_is_present(self):
        self.prepare(); self.authorize()
        result = self.dispatch()
        with control.connect() as c:
            data = json.loads(c.execute('SELECT data FROM jobs WHERE id=?',(self.job,)).fetchone()['data'])
            data['commercial_contact']['message'] += '\n+55 14 90000-0000'
            c.execute('UPDATE jobs SET data=? WHERE id=?',(json.dumps(data),self.job))
        state = control.snapshot()
        self.assertEqual(state['jobs'][0]['contact_status'],'sent')
        self.assertFalse(state['jobs'][0]['commercial_requires_review'])
        self.assertEqual(state['commercial_attempts'][0]['id'],result['attempt_id'])
        self.assertEqual(state['commercial_attempts'][0]['status'],'sent')
        self.assertEqual(state['commercial_attempts'][0]['gmail_message_id'],'gmail12345678')
    def test_confirmed_gmail_response_and_optout_need_no_new_send_proof(self):
        self.prepare(); self.authorize()
        result = self.dispatch()
        self.assertEqual(result['status'],'sent')
        self.assertEqual(control.record_commercial(self.job,'replied','Empresa respondeu')['contact_status'],'replied')
        self.assertEqual(control.record_commercial(self.job,'opted_out','Solicitou exclusão')['contact_status'],'opted_out')
        state = control.snapshot()
        self.assertEqual(state['jobs'][0]['stage'],'ready')
        self.assertEqual(state['commercial_attempts'][-1]['gmail_message_id'],'gmail12345678')
        with self.assertRaises(ValueError): self.dispatch()
    def test_uncertain_gmail_result_cannot_be_bypassed_by_external_send_record(self):
        self.prepare(); self.authorize()
        self.assertEqual(self.dispatch(client=FakeGmail(error=TimeoutError()))['status'],'uncertain')
        with self.assertRaisesRegex(ValueError,'reconciled'):
            control.record_commercial(self.job,'sent_external','Envio externo','email','id:message-12345678')
        with self.assertRaises(ValueError): self.dispatch()
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

    def test_legacy_daily_limit_five_remains_restrictive(self):
        self.prepare()
        self.authorize(daily_limit=5)
        self.seed_sent_attempts(5)
        with self.assertRaisesRegex(ValueError, 'daily'):
            self.dispatch()

    def test_missing_authorization_daily_limit_defaults_to_twenty(self):
        self.prepare()
        self.authorize(max_contacts=100)
        auth = json.loads(gmail.AUTH_FILE.read_text())
        del auth['daily_limit']
        self.private(gmail.AUTH_FILE, auth)
        self.seed_sent_attempts(19)
        result = self.dispatch()
        self.assertEqual(result['status'], 'sent')

    def test_authorization_above_twenty_cannot_raise_global_cap(self):
        self.prepare()
        self.authorize(max_contacts=100, daily_limit=100)
        self.seed_sent_attempts(20)
        with self.assertRaisesRegex(ValueError, 'daily'):
            self.dispatch()
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
                self_outer.assertEqual(parseaddr(str(msg['From']))[1],'scarasoftbauru@gmail.com')
                self_outer.assertEqual(str(msg['Reply-To']),'contato@scarasoft.com.br')
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
                self_outer.assertEqual(parseaddr(str(msg['From']))[1],'scarasoftbauru@gmail.com')
                self_outer.assertEqual(str(msg['Reply-To']),'contato@scarasoft.com.br')
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
                self_outer.assertEqual(parseaddr(str(msg['From']))[1],'scarasoftbauru@gmail.com')
                self_outer.assertEqual(str(msg['Reply-To']),'contato@scarasoft.com.br')
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
    def test_response_states_changed_during_initial_send_are_preserved(self):
        jobs = [self.job] + [self.new_job('Empresa ' + status, status + '@example.org')
                             for status in ('interested','not_interested','opted_out')]
        self.authorize(jobs=jobs, max_contacts=4, daily_limit=4)
        for jid, state in zip(jobs, ('replied','interested','not_interested','opted_out')):
            with self.subTest(state=state):
                self.prepare(jid)
                class ConcurrentChange(FakeGmail):
                    def send(self, recipient, sender, subject, body, preview_url=None, **kwargs):
                        with control.connect() as c:
                            c.execute('UPDATE jobs SET contact_status=? WHERE id=?', (state,jid))
                        return super().send(recipient,sender,subject,body,preview_url,**kwargs)
                result = self.dispatch(jid,ConcurrentChange())
                self.assertEqual(result['status'],'sent')
                with control.connect() as c:
                    self.assertEqual(c.execute('SELECT contact_status FROM jobs WHERE id=?',(jid,)).fetchone()[0],state)
                    self.assertEqual(c.execute('SELECT status FROM commercial_attempts WHERE id=?',(result['attempt_id'],)).fetchone()[0],'sent')
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
    def test_response_states_changed_during_followup_are_preserved(self):
        states = ('replied','interested','not_interested','opted_out')
        jobs = [self.job] + [self.new_job('Empresa ' + state, state + '@example.org') for state in states[1:]]
        self.authorize(jobs=jobs,max_contacts=4,daily_limit=10)
        for jid, state in zip(jobs,states):
            with self.subTest(state=state):
                self.prepare(jid)
                self.dispatch(jid)
                at = (control.dt.datetime.now(control.dt.timezone.utc) - control.dt.timedelta(days=5)).isoformat(timespec='seconds')
                with control.connect() as c:
                    c.execute("UPDATE commercial_attempts SET created_at=? WHERE job_id=? AND source='gmail_api' AND touch=0", (at,jid))
                class ConcurrentChange(FakeGmail):
                    def send(self, recipient, sender, subject, body, preview_url=None, **kwargs):
                        with control.connect() as c:
                            c.execute('UPDATE jobs SET contact_status=? WHERE id=?', (state,jid))
                        return super().send(recipient,sender,subject,body,preview_url,**kwargs)
                result = gmail.dispatch(control.gmail_ledger(),jid,ConcurrentChange(),touch=1)
                self.assertEqual(result['status'],'sent')
                with control.connect() as c:
                    self.assertEqual(c.execute('SELECT contact_status FROM jobs WHERE id=?',(jid,)).fetchone()[0],state)
                    self.assertEqual(c.execute('SELECT status FROM commercial_attempts WHERE id=?',(result['attempt_id'],)).fetchone()[0],'sent')
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
