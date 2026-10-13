"""Fail-closed, locally authorized Gmail dispatch over the existing commercial ledger."""
import base64
import datetime as dt
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
import json
import os
from pathlib import Path
import re
import commercial

SCOPES = ['openid', 'email', 'https://www.googleapis.com/auth/gmail.send']
APPROVED_SENDER = 'scarasoftbauru@gmail.com'
AUTH_FILE = None  # resolved against the ledger root, or overridden in tests
SENDER_FILE = None
TOKEN_FILE = None
CLIENT_FILE = None

class PreSendError(Exception):
    """The Gmail send request was definitely not accepted."""

class UncertainError(Exception):
    """The send request may have reached Gmail."""

def private_path(ledger, override, name):
    return Path(override) if override is not None else ledger.ROOT / 'data' / name

def private_json(path):
    try:
        if path.stat().st_mode & 0o077:
            raise ValueError(f'Private Gmail file has unsafe permissions: {path.name} (use chmod 600)')
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'Private Gmail file unavailable or invalid: {path.name}') from exc
    if not isinstance(value, dict):
        raise ValueError(f'Invalid private Gmail file: {path.name}')
    return value

def email_address(value):
    return (isinstance(value, str) and len(value) <= 254 and
            bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value)))

def authorization(ledger, job, *, live=False):
    path = private_path(ledger, AUTH_FILE, 'gmail-authorization.json')
    try:
        auth = private_json(path)
    except ValueError:
        if live: raise ValueError('Gmail live sending is disabled: private batch authorization is missing')
        return {'mode': 'dry_run', 'authorized': False, 'reason': 'Autorização local ausente'}
    if auth.get('mode') != 'live':
        if live: raise ValueError('Gmail live sending is disabled: authorization is dry_run')
        return {'mode': 'dry_run', 'authorized': False, 'reason': 'Autorização em dry_run'}
    valid = (auth.get('approved_by') == 'Lucas Scaranello'
             and isinstance(auth.get('approved_at'), str) and bool(auth['approved_at'].strip())
             and auth.get('batch_id') == job['batch_id']
             and isinstance(auth.get('job_ids'), list) and job['id'] in auth['job_ids']
             and all(isinstance(x, str) for x in auth['job_ids'])
             and len(auth['job_ids']) == len(set(auth['job_ids']))
             and auth.get('sender') == APPROVED_SENDER
             and type(auth.get('max_contacts')) is int and 1 <= auth['max_contacts'] <= 100
             and type(auth.get('daily_limit', 5)) is int and 1 <= auth.get('daily_limit', 5) <= 100)
    if not valid:
        if live: raise ValueError('Gmail live authorization does not include this company and scope')
        return {'mode': 'live', 'authorized': False, 'reason': 'Empresa fora do escopo aprovado'}
    sender = auth['sender'].lower()
    try: sender_config(ledger, sender)
    except (ValueError, PreSendError) as exc:
        if live: raise ValueError(str(exc)) from exc
        return {'mode': 'live', 'authorized': False, 'reason': 'Remetente Gmail não configurado ou não verificado'}
    return {'mode': 'live', 'authorized': True, 'sender': sender,
            'max_contacts': auth['max_contacts'], 'daily_limit': auth.get('daily_limit', 5),
            'reason': 'Autorizado localmente'}

def sender_config(ledger, sender):
    cfg = private_json(private_path(ledger, SENDER_FILE, 'gmail-sender.json'))
    if (not email_address(cfg.get('oauth_email')) or not email_address(cfg.get('sender'))
            or cfg['sender'].lower() != sender or cfg['oauth_email'].lower() != sender):
        raise PreSendError('Authenticated Gmail account must be the approved sender')
    return cfg['oauth_email'].lower()

def validate(ledger, c, job):
    data = json.loads(job['data'])
    prepared = data.get('commercial_contact') or {}
    if (data.get('preview_verified') is not True or not job['preview_url'].startswith('https://')
            or job['contact_status'] != 'prepared' or prepared.get('channel') != 'email'):
        raise ValueError('Verified preview and prepared email contact are required')
    if c.execute('SELECT 1 FROM submissions WHERE job_id=?', (job['id'],)).fetchone():
        raise ValueError('Legacy submission prevents Gmail sending')
    prior = c.execute("SELECT 1 FROM commercial_attempts WHERE job_id=? AND status!='failed_no_send'", (job['id'],)).fetchone()
    if prior or job['contact_status'] in ('opted_out', 'not_interested', 'uncertain', 'sent'):
        raise ValueError('Prior contact, opt-out or uncertain attempt prevents Gmail sending')
    excluded = [row['channel'] for row in c.execute("SELECT channel FROM commercial_attempts WHERE job_id=? AND status='failed_no_send'", (job['id'],))]
    route, destination = ledger.commercial.route(data.get('contacts'), excluded)
    if route != 'email' or destination != prepared.get('destination') or not email_address(destination):
        raise ValueError('Email is no longer the eligible priority channel or recipient changed')
    subject, message = prepared.get('subject'), prepared.get('message')
    if not isinstance(subject, str) or not subject.strip() or any(x in subject for x in '\r\n'):
        raise ValueError('Prepared email subject is invalid')
    if (not isinstance(message, str) or not message.strip()
            or ('Ver a prévia do site' not in message and job['preview_url'] not in message)):
        raise ValueError('Prepared email message or preview URL is invalid')
    ledger.require_commercial_identity(message)
    if 'não receber novos contatos' not in message.lower():
        raise ValueError('Prepared email lacks a simple opt-out instruction')
    return prepared

def simulate(ledger, jid):
    with ledger.connect() as c:
        job = c.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
        if job is None: raise ValueError('Unknown job')
        prepared = validate(ledger, c, job)
        auth = authorization(ledger, job)
        return {'job_id': jid, 'mode': 'dry_run', 'would_send': True,
                'authorization': auth, 'recipient': prepared['destination'],
                'subject': prepared['subject'], 'message': prepared['message'],
                'preview_url': job['preview_url'],
                'note': 'Simulation only; no Gmail call or attempt reserved'}

def followup_message(name, touch):
    if touch == 1:
        return (f'Olá!\n\nPassando apenas para saber se conseguiu ver a prévia que preparei para a {name}.\n\n'
                'Se fizer sentido para vocês, posso explicar os próximos passos e o investimento para colocar o site no ar.\n\n'
                'Abraço,\nLucas\n\nSe preferir não receber novos contatos comerciais, responda solicitando a exclusão.')
    if touch == 2:
        return (f'Olá!\n\nEste é meu último contato sobre a prévia que preparei para a {name}.\n\n'
                'Se não for uma prioridade agora, tudo bem; não voltarei a escrever sobre esta proposta. '
                'Se quiser conversar sobre os próximos passos em outro momento, é só responder.\n\n'
                'Abraço,\nLucas\n\nSe preferir não receber novos contatos comerciais, responda solicitando a exclusão.')
    raise ValueError('Follow-up must be day 4 or day 10')

def followup_status(c, job):
    rows = list(c.execute("SELECT * FROM commercial_attempts WHERE job_id=? AND source='gmail_api' ORDER BY touch", (job['id'],)))
    first = next((row for row in rows if row['touch'] == 0 and row['status'] == 'sent'), None)
    if not first: return {'available': False, 'reason': 'Primeiro e-mail Gmail ainda não confirmado'}
    base = dt.datetime.fromisoformat(first['created_at'])
    day4 = (base + dt.timedelta(days=4)).isoformat(timespec='seconds')
    day10 = (base + dt.timedelta(days=10)).isoformat(timespec='seconds')
    result = {'available': True, 'first_sent_at': first['created_at'],
              'day4_due_at': day4, 'day10_due_at': day10,
              'day4_status': next((r['status'] for r in rows if r['touch'] == 1), 'pending'),
              'day10_status': next((r['status'] for r in rows if r['touch'] == 2), 'pending')}
    if job['contact_status'] in ('replied', 'interested', 'not_interested', 'opted_out'):
        return {**result, 'next_touch': None, 'reason': 'Acompanhamento encerrado após resposta ou recusa'}
    if job['contact_status'] != 'sent' or any(r['status'] in ('attempting','uncertain') for r in rows):
        return {**result, 'next_touch': None, 'reason': 'Resultado pendente de reconciliação'}
    if not first['gmail_thread_id'] or not first['rfc_message_id']:
        return {**result, 'next_touch': None, 'reason': 'Conversa anterior sem identificadores suficientes; responder manualmente no Gmail'}
    for touch, due in ((1, day4), (2, day10)):
        prior = next((r for r in rows if r['touch'] == touch), None)
        if prior:
            if prior['status'] != 'sent':
                return {**result, 'next_touch': None, 'reason': 'Tentativa anterior requer revisão manual'}
            if prior['gmail_thread_id'] != first['gmail_thread_id']:
                return {**result, 'next_touch': None, 'reason': 'Gmail confirmou outra conversa; revisar manualmente'}
            continue
        if touch == 2 and result['day4_status'] != 'sent':
            return {**result, 'next_touch': None, 'reason': 'Aguardar confirmação do dia 4'}
        return {**result, 'next_touch': touch, 'due_at': due,
                'due': dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(due),
                'message': followup_message(job['name'], touch),
                'subject': first['subject'], 'recipient': first['recipient']}
    return {**result, 'next_touch': None, 'reason': 'Sequência concluída'}

def limits(c, job, auth, now, touch=0):
    batch_count = c.execute('''SELECT COUNT(*) FROM commercial_attempts a JOIN jobs j ON j.id=a.job_id
        WHERE j.batch_id=? AND a.source='gmail_api' AND a.touch=0''', (job['batch_id'],)).fetchone()[0]
    if touch == 0 and batch_count >= auth['max_contacts']:
        raise ValueError('Authorized Gmail batch contact limit reached')
    today = now[:10]
    daily_count = c.execute("SELECT COUNT(*) FROM commercial_attempts WHERE source='gmail_api' AND substr(created_at,1,10)=?", (today,)).fetchone()[0]
    if daily_count >= auth['daily_limit']:
        raise ValueError('Gmail daily authorization limit reached')

def dispatch(ledger, jid, client=None, touch=0):
    # All eligibility and capacity checks, and the reservation, happen under BEGIN IMMEDIATE.
    with ledger.connect() as c:
        job = c.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
        if job is None: raise ValueError('Unknown job')
        if touch == 0:
            prepared = validate(ledger, c, job)
            parent = None
            references = None
            target_thread_id = None
        elif touch in (1, 2):
            plan = followup_status(c, job)
            if plan.get('next_touch') != touch or not plan.get('due'):
                raise ValueError('Follow-up is not due or is blocked by contact history')
            first = c.execute("SELECT * FROM commercial_attempts WHERE job_id=? AND source='gmail_api' AND touch=0 AND status='sent'", (jid,)).fetchone()
            previous = c.execute("SELECT * FROM commercial_attempts WHERE job_id=? AND source='gmail_api' AND touch=? AND status='sent'", (jid, touch-1)).fetchone()
            if not first or not previous or not previous['rfc_message_id']:
                raise ValueError('Confirmed prior Gmail message headers are required')
            data = json.loads(job['data'])
            route, current_recipient = ledger.commercial.route(data.get('contacts'))
            if route != 'email' or current_recipient != first['recipient']:
                raise ValueError('Current email contact or channel priority changed; review manually')
            parent = previous['rfc_message_id']
            references = first['rfc_message_id'] if touch == 1 else first['rfc_message_id'] + ' ' + previous['rfc_message_id']
            target_thread_id = first['gmail_thread_id']
            prepared = {'destination': first['recipient'], 'subject': first['subject'],
                        'message': followup_message(job['name'], touch)}
        else:
            raise ValueError('Invalid Gmail contact step')
        auth = authorization(ledger, job, live=True)
        sender = auth['sender']
        expected_account = sender_config(ledger, sender)
        if touch and first['sender'] != sender:
            raise ValueError('Follow-up sender must match the original Gmail sender')
        at = ledger.now()
        limits(c, job, auth, at, touch)
        rfc_id = make_msgid(domain='scarasoft.com.br')
        c.execute('''INSERT INTO commercial_attempts
            (job_id,channel,status,message,evidence,created_at,source,recipient,sender,subject,touch,rfc_message_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (jid, 'email', 'attempting', prepared['message'], 'Gmail send reserved', at,
             'gmail_api', prepared['destination'], sender, prepared['subject'], touch, rfc_id))
        attempt = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("UPDATE jobs SET contact_status='attempting',updated_at=? WHERE id=?", (at, jid))
        ledger.event(c, jid, 'Gmail send attempt reserved.')
    status, remote_id, thread_id, reason = 'uncertain', None, None, 'Gmail outcome unknown'
    try:
        client = client or GmailClient(ledger)
        client.verify_identity(expected_account, sender)
        response = client.send(prepared['destination'], sender, prepared['subject'], prepared['message'],
                               job['preview_url'] if touch == 0 else None,
                               message_id=rfc_id, thread_id=target_thread_id, in_reply_to=parent, references=references)
        if not isinstance(response, dict) or not isinstance(response.get('id'), str) or not response['id'].strip():
            raise UncertainError('Gmail returned no message id after send')
        status, remote_id, thread_id, reason = 'sent', response['id'], response.get('threadId'), 'Gmail confirmed send'
        if touch and thread_id != first['gmail_thread_id']:
            reason = 'Gmail confirmed send outside original conversation; review manually'
    except PreSendError as exc:
        status, reason = 'failed_no_send', str(exc)
    except Exception as exc:
        # Never retry a transport error or an unexpected exception after reservation.
        status, reason = 'uncertain', str(exc) if isinstance(exc, UncertainError) else 'Gmail request outcome unknown; reconcile manually'
    with ledger.connect() as c:
        c.execute('''UPDATE commercial_attempts SET status=?,evidence=?,gmail_message_id=?,gmail_thread_id=?
            WHERE id=? AND status='attempting' ''', (status, reason[:500], remote_id, thread_id, attempt))
        if c.execute('SELECT changes()').fetchone()[0] != 1:
            raise ValueError('Gmail attempt changed during dispatch; inspect ledger')
        next_status = ('pending' if touch == 0 else 'sent') if status == 'failed_no_send' else status
        c.execute("UPDATE jobs SET contact_status=CASE WHEN contact_status='opted_out' THEN 'opted_out' ELSE ? END,updated_at=? WHERE id=?",
                  (next_status, ledger.now(), jid))
        ledger.event(c, jid, 'Gmail attempt result: ' + status)
    return {'attempt_id': attempt, 'touch': touch, 'status': status, 'gmail_message_id': remote_id,
            'gmail_thread_id': thread_id, 'reason': reason}

def reconcile(ledger, attempt_id, status, evidence, message_id='', thread_id=''):
    if status not in ('sent', 'failed_no_send') or not isinstance(evidence, str) or not evidence.strip():
        raise ValueError('Explicit reconciliation status and evidence required')
    if status == 'sent' and not re.fullmatch(r'[A-Za-z0-9_-]{8,}', message_id):
        raise ValueError('A confirmed Gmail message id is required')
    if thread_id and not re.fullmatch(r'[A-Za-z0-9_-]{8,}', thread_id):
        raise ValueError('Invalid Gmail thread id')
    with ledger.connect() as c:
        row = c.execute("SELECT * FROM commercial_attempts WHERE id=? AND source='gmail_api'", (attempt_id,)).fetchone()
        if not row or row['status'] not in ('attempting', 'uncertain'):
            raise ValueError('Only pending or uncertain Gmail attempts can be reconciled')
        c.execute('UPDATE commercial_attempts SET status=?,evidence=?,gmail_message_id=?,gmail_thread_id=COALESCE(?,gmail_thread_id) WHERE id=?',
                  (status, evidence.strip()[:500], message_id or None, thread_id or None, attempt_id))
        c.execute("UPDATE jobs SET contact_status=CASE WHEN contact_status='opted_out' THEN 'opted_out' ELSE ? END,updated_at=? WHERE id=?",
                  ('sent' if status == 'sent' or row['touch'] > 0 else 'pending', ledger.now(), row['job_id']))
        ledger.event(c, row['job_id'], 'Gmail attempt explicitly reconciled: ' + status)
        return {'attempt_id': attempt_id, 'status': status}

class GmailClient:
    def __init__(self, ledger):
        self.ledger = ledger
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request, AuthorizedSession
        except ImportError as exc:
            raise PreSendError('Install Gmail OAuth dependencies from requirements-gmail.txt') from exc
        token_path = private_path(ledger, TOKEN_FILE, 'gmail-token.json')
        try:
            private_json(token_path)
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if not creds.valid:
                if not creds.refresh_token: raise PreSendError('Gmail OAuth token is invalid or expired; authenticate again')
                try: creds.refresh(Request())
                except Exception as exc: raise PreSendError('Gmail OAuth token refresh failed; authenticate again') from exc
                token_path.write_text(creds.to_json())
                os.chmod(token_path, 0o600)
            self.session = AuthorizedSession(creds)
        except ValueError as exc:
            raise PreSendError(str(exc)) from exc
    def verify_identity(self, expected_account, sender):
        try:
            r = self.session.get('https://openidconnect.googleapis.com/v1/userinfo', timeout=15)
            if r.status_code != 200: raise PreSendError('Cannot verify authenticated Google account')
            profile = r.json()
        except PreSendError: raise
        except Exception as exc: raise PreSendError('Cannot verify authenticated Google account') from exc
        if (not email_address(profile.get('email')) or profile['email'].lower() != expected_account
                or profile.get('email_verified') is not True):
            raise PreSendError('Authenticated Google account does not match authorized mailbox')
        # Alias validation is an explicit local prerequisite, since gmail.send cannot read send-as settings.
    def send(self, recipient, sender, subject, body, preview_url=None, *, message_id=None,
             thread_id=None, in_reply_to=None, references=None):
        mail = EmailMessage()
        mail['From'] = formataddr(('scarasoft — Lucas Scaranello', sender))
        mail['To'] = recipient
        mail['Subject'] = subject
        if message_id: mail['Message-ID'] = message_id
        if in_reply_to: mail['In-Reply-To'] = in_reply_to
        if references: mail['References'] = references
        if 'Ver a prévia do site' in body:
            if not preview_url: raise PreSendError('Verified preview link is required')
            try: html = commercial.email_html(body, preview_url)
            except ValueError as exc: raise PreSendError(str(exc)) from exc
            mail.set_content(body.replace('Ver a prévia do site', 'Ver a prévia do site: ' + preview_url, 1), charset='utf-8')
            mail.add_alternative(html, subtype='html', charset='utf-8')
        else:
            mail.set_content(body, charset='utf-8')
        raw = base64.urlsafe_b64encode(mail.as_bytes()).decode().rstrip('=')
        try:
            payload = {'raw': raw}
            if thread_id: payload['threadId'] = thread_id
            r = self.session.post('https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
                                  json=payload, timeout=30)
        except Exception as exc:
            raise UncertainError('Gmail request timed out or connection was lost') from exc
        if r.status_code in (400, 401, 403, 404, 429):
            raise PreSendError(f'Gmail rejected request before send (HTTP {r.status_code}); inspect quota or credentials')
        if r.status_code >= 500 or r.status_code != 200:
            raise UncertainError(f'Gmail outcome unknown (HTTP {r.status_code})')
        try: return r.json()
        except ValueError as exc: raise UncertainError('Gmail returned invalid send response') from exc

def authenticate(ledger):
    """Explicit operator command only; never called by dashboard startup or tests."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise ValueError('Install Gmail OAuth dependencies from requirements-gmail.txt') from exc
    client_path = private_path(ledger, CLIENT_FILE, 'gmail-oauth-client.json')
    private_json(client_path)
    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
    creds = flow.run_local_server(host='127.0.0.1', port=0, open_browser=True)
    path = private_path(ledger, TOKEN_FILE, 'gmail-token.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json())
    os.chmod(path, 0o600)
    return {'authenticated': True, 'token_file': str(path)}
