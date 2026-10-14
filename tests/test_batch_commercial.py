"""Batch commercial approval and dispatch tests using a temporary SQLite ledger."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('control', ROOT / 'tools/control.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)
batch_spec = importlib.util.spec_from_file_location('batch_commercial', ROOT / 'tools/batch_commercial.py')
batch_commercial = importlib.util.module_from_spec(batch_spec)
batch_spec.loader.exec_module(batch_commercial)
gmail = control.gmail_outreach


class FakeGmail:
    """Small stand-in for Gmail; tests must never contact the live API."""
    def __init__(self, *, error=None, account='scarasoftbauru@gmail.com'):
        self.error = error
        self.account = account
        self.calls = []
        self.active = 0
        self.max_active = 0

    def verify_identity(self, expected, sender):
        if self.account != expected:
            raise gmail.PreSendError('Authenticated Google account does not match authorized mailbox')

    def send(self, recipient, sender, subject, body, preview_url=None, **kwargs):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.calls.append((recipient, sender, subject, body, preview_url, kwargs))
        try:
            if self.error:
                raise self.error
            return {'id': f'message-{len(self.calls)}', 'threadId': f'thread-{len(self.calls)}'}
        finally:
            self.active -= 1


class BatchCommercialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = control.DB
        self.old_auth = gmail.AUTH_FILE
        self.old_sender = gmail.SENDER_FILE
        self.old_email = os.environ.get('BR_COMMERCIAL_EMAIL')
        control.DB = Path(self.tmp.name) / 'ledger.sqlite3'
        gmail.AUTH_FILE = Path(self.tmp.name) / 'gmail-authorization.json'
        gmail.SENDER_FILE = Path(self.tmp.name) / 'gmail-sender.json'
        os.environ['BR_COMMERCIAL_EMAIL'] = 'contato@scarasoft.com.br'
        self.ledger = control.gmail_ledger()
        self.batch_id = control.batch('chaveiros', 'Bauru, SP', 4)['id']
        self.jobs = [self.add_ready_job(f'Empresa {i}', f'empresa{i}@example.org') for i in range(1, 5)]
        self.private(gmail.SENDER_FILE, {'oauth_email': 'scarasoftbauru@gmail.com',
                                         'sender': 'scarasoftbauru@gmail.com'})

    def tearDown(self):
        control.DB = self.old_db
        gmail.AUTH_FILE = self.old_auth
        gmail.SENDER_FILE = self.old_sender
        if self.old_email is None:
            os.environ.pop('BR_COMMERCIAL_EMAIL', None)
        else:
            os.environ['BR_COMMERCIAL_EMAIL'] = self.old_email
        self.tmp.cleanup()

    @staticmethod
    def private(path, value):
        path.write_text(json.dumps(value))
        path.chmod(0o600)

    def add_ready_job(self, name, email):
        jid = control.add(self.batch_id, name)['id']
        contacts = {'email': {'status': 'encontrado', 'value': email,
                              'source': 'https://example.org/contact',
                              'checked_at': control.now()[:10]},
                    'form': {'status': 'nao_encontrado'}}
        data = {'template': 'chaveiros', 'preview_verified': True, 'qa_passed': True,
                'presence_status': 'sem_site_confirmado', 'contacts': contacts,
                'verification': {'checked_at': control.now()[:10],
                                 'sources': ['https://example.org/contact']}}
        with control.connect() as c:
            c.execute('UPDATE jobs SET stage=?,preview_url=?,data=? WHERE id=?',
                      ('ready', f'https://preview.example/{jid}', json.dumps(data), jid))
        control.prepare_commercial(jid)
        return jid

    def approve(self, batch_id, job_ids):
        """Approve the exact digests that the operator saw in the review response."""
        reviewed = batch_commercial.review(self.ledger, batch_id)
        digests = {row['job_id']: row['approval_digest'] for row in reviewed['rows']
                   if row['job_id'] in job_ids}
        return batch_commercial.approve(self.ledger, batch_id, job_ids, reviewed=digests)

    def test_review_and_approval_are_scoped_to_selected_jobs(self):
        before = batch_commercial.review(self.ledger, self.batch_id)
        self.assertEqual(len(before['rows']), 4)
        self.assertIn('capacity', before)
        approval = self.approve(self.batch_id, [self.jobs[0], self.jobs[2]])
        self.assertTrue(approval)
        fake = FakeGmail()
        result = batch_commercial.dispatch_batch(self.ledger, self.batch_id,
                                                 client_factory=lambda: fake)
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual({call[0] for call in fake.calls},
                         {'empresa1@example.org', 'empresa3@example.org'})
        self.assertEqual(sum(item['status'] == 'sent' for item in result['results']), 2)

    def test_digest_invalidates_when_reviewed_content_changes(self):
        original_auth = gmail.AUTH_FILE
        for index, mutation in enumerate(('recipient', 'message', 'preview', 'channel')):
            with self.subTest(mutation=mutation):
                gmail.AUTH_FILE = Path(self.tmp.name) / f'gmail-authorization-{mutation}.json'
                isolated_batch = control.batch('chaveiros', 'Bauru, SP', 1)['id']
                jid = self.add_job_in_batch(isolated_batch, f'Isolada {index}', f'isolada{index}@example.org')
                self.approve(isolated_batch, [jid])
                with control.connect() as c:
                    row = c.execute('SELECT data,preview_url FROM jobs WHERE id=?', (jid,)).fetchone()
                    data = json.loads(row['data'])
                    if mutation == 'recipient':
                        data['commercial_contact']['destination'] = 'changed@example.org'
                    elif mutation == 'message':
                        data['commercial_contact']['message'] += '\nAlteração após aprovação'
                    elif mutation == 'channel':
                        data['commercial_contact']['channel'] = 'whatsapp_manual'
                    c.execute('UPDATE jobs SET data=?,preview_url=? WHERE id=?',
                              (json.dumps(data), f'https://changed.example/{jid}' if mutation == 'preview' else row['preview_url'], jid))
                fake = FakeGmail()
                dispatch = batch_commercial.dispatch_batch(self.ledger, isolated_batch,
                                                           client_factory=lambda: fake)
                self.assertEqual(fake.calls, [])
                self.assertTrue(any(row['status'] == 'blocked' for row in dispatch['results']))
                # Restore the reviewed state so the next mutation can be approved independently.
                with control.connect() as c:
                    row = c.execute('SELECT data,preview_url FROM jobs WHERE id=?', (jid,)).fetchone()
                    data = json.loads(row['data'])
                    data['commercial_contact']['destination'] = f'isolada{index}@example.org'
                    data['commercial_contact']['channel'] = 'email'
                    data['commercial_contact']['message'] = data['commercial_contact']['message'].split('\nAlteração após aprovação')[0]
                    c.execute('UPDATE jobs SET data=?,preview_url=? WHERE id=?',
                              (json.dumps(data), 'https://preview.example/other', jid))
        gmail.AUTH_FILE = original_auth

    def test_stale_review_is_rejected_before_authorization_is_written(self):
        jid = self.jobs[0]
        displayed = batch_commercial.review(self.ledger, self.batch_id)
        digest = next(row['approval_digest'] for row in displayed['rows'] if row['job_id'] == jid)
        with control.connect() as c:
            c.execute('UPDATE jobs SET preview_url=? WHERE id=?',
                      ('https://preview.example/changed-after-review', jid))
        with self.assertRaisesRegex(ValueError, 'reviewed|Review'):
            batch_commercial.approve(self.ledger, self.batch_id, [jid], reviewed={jid: digest})
        self.assertFalse(Path(gmail.AUTH_FILE).exists())

    def test_cumulative_batch_capacity_and_global_daily_limit(self):
        self.approve(self.batch_id, self.jobs)
        first = FakeGmail()
        first_report = batch_commercial.dispatch_batch(self.ledger, self.batch_id,
                                                       client_factory=lambda: first)
        self.assertEqual(sum(x['status'] == 'sent' for x in first_report['results']), 4)
        # A later approval in the same batch gets only the still-available cumulative capacity.
        extra = self.add_job_in_batch(self.batch_id, 'Empresa Cinco', 'empresa5@example.org')
        self.assertEqual(batch_commercial.review(self.ledger, self.batch_id)['capacity']['prior_attempts'], 4)
        self.approve(self.batch_id, [extra])
        extra_report = batch_commercial.dispatch_batch(self.ledger, self.batch_id,
                                                       client_factory=lambda: FakeGmail())
        self.assertTrue(any(x['job_id'] == extra and x['status'] == 'sent' for x in extra_report['results']))
        review = batch_commercial.review(self.ledger, self.batch_id)
        self.assertEqual(review['capacity']['prior_attempts'], 5)
        # A different batch still shares the daily limit.
        other_batch = control.batch('chaveiros', 'Campinas, SP', 1)['id']
        other = self.add_job_in_batch(other_batch, 'Outra Empresa', 'outra@example.org')
        with self.assertRaisesRegex(ValueError, 'limits'):
            self.approve(other_batch, [other])
        self.assertEqual(batch_commercial.review(self.ledger, other_batch)['capacity']['remaining_daily'], 0)
        # No authorization is written after a denied approval.
        auth = json.loads(Path(gmail.AUTH_FILE).read_text())
        self.assertEqual(auth['batch_id'], self.batch_id)

    def test_approval_returns_nested_capacity_consistent_with_review(self):
        selected = self.jobs[:2]
        result = self.approve(self.batch_id, selected)
        self.assertIn('capacity', result)
        self.assertEqual(result['capacity']['remaining_daily'], batch_commercial.DAILY_LIMIT - len(selected))
        self.assertEqual(result['capacity']['approved_new'], len(selected))
        self.assertEqual(result['capacity']['prior_attempts'], 0)

    def test_concurrent_approvals_cannot_replace_pending_authorization(self):
        other_batch = control.batch('chaveiros', 'Campinas, SP', 1)['id']
        other = self.add_job_in_batch(other_batch, 'Outra empresa', 'concorrente@example.org')
        barrier = threading.Barrier(2)
        outcomes = []

        def attempt(batch_id, job_id):
            barrier.wait(timeout=5)
            try:
                outcomes.append(('approved', self.approve(batch_id, [job_id])))
            except ValueError as exc:
                outcomes.append(('rejected', str(exc)))

        threads = [threading.Thread(target=attempt, args=(self.batch_id, self.jobs[0])),
                   threading.Thread(target=attempt, args=(other_batch, other))]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=10)
        self.assertTrue(all(not thread.is_alive() for thread in threads), 'approval threads did not finish')
        self.assertEqual(sum(kind == 'approved' for kind, _ in outcomes), 1, outcomes)
        auth = json.loads(Path(gmail.AUTH_FILE).read_text())
        winner = next(job for job in (self.jobs[0], other) if job in auth['job_ids'])
        self.assertEqual(auth['job_ids'], [winner])
        # The surviving authorization must stay pending after a process restart.
        restarted = FakeGmail()
        batch_commercial.resume(self.ledger, client_factory=lambda: restarted)
        self.assertEqual(len(restarted.calls), 1)
        self.assertEqual(restarted.calls[0][0], 'empresa1@example.org' if winner == self.jobs[0] else 'concorrente@example.org')

    def test_restart_skips_attempting_and_uncertain_and_sends_unattempted_approved_contact(self):
        selected = self.jobs[:3]
        self.approve(self.batch_id, selected)
        for jid, status in ((selected[0], 'attempting'), (selected[1], 'uncertain')):
            with control.connect() as c:
                c.execute('''INSERT INTO commercial_attempts
                    (job_id,channel,status,message,evidence,created_at,source,recipient,sender,subject,touch)
                    VALUES(?,?,?,?,?,?,?,?,?,?,0)''',
                    (jid,'email',status,'interrupted','unknown',control.now(),'gmail_api',
                     f'{jid}@example.org','scarasoftbauru@gmail.com','Interrupted'))
        restarted = FakeGmail()
        batch_commercial.resume(self.ledger, client_factory=lambda: restarted)
        self.assertEqual(len(restarted.calls), 1)
        self.assertEqual(restarted.calls[0][0], 'empresa3@example.org')
        again = FakeGmail()
        batch_commercial.resume(self.ledger, client_factory=lambda: again)
        self.assertEqual(again.calls, [])
        other_batch = control.batch('chaveiros', 'Campinas, SP', 1)['id']
        other = self.add_job_in_batch(other_batch, 'Outra empresa', 'outra@example.org')
        with self.assertRaisesRegex(ValueError, 'uncertain outcome'):
            self.approve(other_batch, [other])

    def test_completed_dispatch_closes_its_authorization(self):
        self.approve(self.batch_id, self.jobs[:2])
        sent = FakeGmail()
        report = batch_commercial.dispatch_batch(self.ledger, self.batch_id,
                                                 client_factory=lambda: sent)
        self.assertEqual(report['report']['counts']['sent'], 2)
        auth = json.loads(Path(gmail.AUTH_FILE).read_text())
        self.assertNotEqual(auth.get('mode'), 'live', 'completed approval remains available for sending')
        restarted = FakeGmail()
        result = batch_commercial.resume(self.ledger, client_factory=lambda: restarted)
        self.assertEqual(restarted.calls, [])
        self.assertIn(result.get('status'), ('no_authorization', 'complete'))

    def test_unexpected_dispatch_failure_is_recorded_and_never_retried(self):
        self.approve(self.batch_id, self.jobs[:2])
        with patch.object(batch_commercial.gmail, 'dispatch', side_effect=RuntimeError('unexpected transport crash')):
            result = batch_commercial.dispatch_batch(self.ledger, self.batch_id,
                                                     client_factory=lambda: FakeGmail())
        self.assertEqual(result.get('status'), 'operational_failure', result)
        self.assertIn('RuntimeError', result.get('operational_failure', ''))
        self.assertEqual(result.get('report', {}).get('dispatch_status'), 'operational_failure')
        auth = json.loads(Path(gmail.AUTH_FILE).read_text())
        self.assertEqual(auth.get('mode'), 'paused')
        self.assertIn('RuntimeError', auth.get('operational_failure', ''))
        with control.connect() as c:
            events = list(c.execute("SELECT message FROM events WHERE message LIKE '%operational_failure%'"))
        self.assertTrue(events, 'unexpected failure was not recorded in the audit event log')
        restarted = FakeGmail()
        resumed = batch_commercial.resume(self.ledger, client_factory=lambda: restarted)
        self.assertEqual(resumed.get('status'), 'paused')
        self.assertEqual(restarted.calls, [])

    def test_daily_limit_is_enforced_during_dispatch_when_capacity_changes(self):
        # Concurrent or earlier jobs may consume capacity after approval; dispatch still checks.
        selected = self.jobs[:2]
        self.approve(self.batch_id, selected)
        # Seed four already-recorded Gmail attempts from separate jobs using the normal ledger schema.
        extra_batch = control.batch('chaveiros', 'Ribeirão Preto, SP', 4)['id']
        existing = [self.add_job_in_batch(extra_batch, f'Anterior {i}', f'anterior{i}@example.org')
                    for i in range(1, 5)]
        for jid in existing:
            with control.connect() as c:
                c.execute('''INSERT INTO commercial_attempts
                    (job_id,channel,status,message,evidence,created_at,source,recipient,sender,subject,touch)
                    VALUES(?,?,?,?,?,?,?,?,?,?,0)''',
                    (jid,'email','sent','prior','confirmed',control.now(),'gmail_api',
                     f'{jid}@example.org','scarasoftbauru@gmail.com','Prior'))
        second = FakeGmail()
        result = batch_commercial.dispatch_batch(self.ledger, self.batch_id,
                                                 client_factory=lambda: second)
        self.assertEqual(len(second.calls), 1, result)
        self.assertTrue(any(x['status'] == 'blocked' for x in result['results']), result)

    def add_job_in_batch(self, batch_id, name, email):
        jid = control.add(batch_id, name)['id']
        data = {'template': 'chaveiros', 'preview_verified': True, 'qa_passed': True,
                'presence_status': 'sem_site_confirmado',
                'contacts': {'email': {'status': 'encontrado', 'value': email,
                                       'source': 'https://example.org/contact',
                                       'checked_at': control.now()[:10]},
                             'form': {'status': 'nao_encontrado'}},
                'verification': {'checked_at': control.now()[:10]}}
        with control.connect() as c:
            c.execute('UPDATE jobs SET stage=?,preview_url=?,data=? WHERE id=?',
                      ('ready', 'https://preview.example/other', json.dumps(data), jid))
        control.prepare_commercial(jid)
        return jid

    def test_dispatch_is_sequential_and_report_contains_job_results(self):
        selected = self.jobs[:3]
        self.approve(self.batch_id, selected)
        fake = FakeGmail()
        report = batch_commercial.dispatch_batch(self.ledger, self.batch_id,
                                                 client_factory=lambda: fake)
        self.assertEqual(fake.max_active, 1)
        self.assertEqual(report['report']['counts']['sent'], 3)
        self.assertEqual(len(report['results']), 3)
        self.assertTrue(all(item['status'] == 'sent' for item in report['results']))

    def test_optout_uncertain_and_restart_never_retry_contact(self):
        self.approve(self.batch_id, self.jobs[:2])
        control.record_commercial(self.jobs[0], 'opted_out', 'Solicitou exclusão')
        fake = FakeGmail(error=TimeoutError())
        report = batch_commercial.dispatch_batch(self.ledger, self.batch_id,
                                                 client_factory=lambda: fake)
        self.assertEqual(len(fake.calls), 1)
        self.assertTrue(any(row['status'] == 'uncertain' for row in report['results']))
        restarted = FakeGmail()
        batch_commercial.resume(self.ledger, client_factory=lambda: restarted)
        self.assertEqual(restarted.calls, [])
        attempts = control.snapshot()['commercial_attempts']
        self.assertEqual(sum(a['status'] == 'uncertain' for a in attempts), 1)
        self.assertFalse(any(a['job_id'] == self.jobs[0] and a['status'] == 'sent' for a in attempts))


if __name__ == '__main__':
    unittest.main()
