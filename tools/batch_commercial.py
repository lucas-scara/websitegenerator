"""Review, approve and resume one Gmail batch over the existing ledger."""
import datetime as dt
import json
import os
import tempfile
import threading
import uuid

import gmail_outreach as gmail

DAILY_LIMIT = gmail.DAILY_LIMIT
COMMERCIAL_EMAIL = 'contato@scarasoft.com.br'
_dispatch_lock = threading.Lock()


def _authorization_path(ledger):
    return gmail.private_path(ledger, gmail.AUTH_FILE, 'gmail-authorization.json')


def _write_authorization(path, auth):
    """Replace the single private authorization without exposing a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.gmail-authorization-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as file:
            json.dump(auth, file, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def _authorization_valid(auth):
    if auth.get('mode') != 'live' or auth.get('approval_version') != 2:
        return False
    try:
        approved = gmail.authorization_time(auth.get('approved_at'))
        expires = gmail.authorization_time(auth.get('expires_at'))
        current = dt.datetime.now(dt.timezone.utc)
        return approved <= current < expires and approved < expires
    except ValueError:
        return False


def _pending(c, auth):
    """An approved contact is unresolved until a certain first-attempt result exists."""
    for jid in auth.get('job_ids', []):
        attempt = c.execute("SELECT status FROM commercial_attempts WHERE job_id=? AND source='gmail_api' AND touch=0", (jid,)).fetchone()
        if attempt is None or attempt['status'] in ('attempting', 'uncertain'):
            return True
    return False


def _uncertain(c, auth):
    return any(c.execute("SELECT 1 FROM commercial_attempts WHERE job_id=? AND source='gmail_api' AND touch=0 AND status IN ('attempting','uncertain')", (jid,)).fetchone()
               for jid in auth.get('job_ids', []))


def _set_dispatch_state(ledger, approval_id, mode, status, reason=''):
    """Change only the authorization this dispatcher started with."""
    with ledger.connect() as c:
        path = _authorization_path(ledger)
        current = gmail.private_json(path)
        if current.get('approval_id') != approval_id or current.get('mode') != 'live':
            return False
        updated = {**current, 'mode': mode, 'dispatch_status': status,
                   'dispatch_updated_at': ledger.now()}
        if reason:
            updated['operational_failure' if status == 'operational_failure' else 'dispatch_reason'] = reason[:300]
        _write_authorization(path, updated)
        ledger.event(c, None, f'Gmail batch {current["batch_id"]} dispatch {status}.')
        return True


def _counts(c, batch_id, current_time):
    prior = c.execute('''SELECT COUNT(*) FROM commercial_attempts a JOIN jobs j ON j.id=a.job_id
        WHERE j.batch_id=? AND a.source='gmail_api' AND a.touch=0''', (batch_id,)).fetchone()[0]
    daily = c.execute("SELECT COUNT(*) FROM commercial_attempts WHERE source='gmail_api' AND substr(created_at,1,10)=?",
                      (current_time[:10],)).fetchone()[0]
    return {'prior_attempts': prior, 'remaining_batch': max(0, 100-prior),
            'daily_limit': DAILY_LIMIT,
            'remaining_daily': max(0, DAILY_LIMIT-daily),
            'approvable_now': max(0, min(100-prior, DAILY_LIMIT-daily))}


def review(ledger, batch_id):
    with ledger.connect() as c:
        if not c.execute('SELECT 1 FROM batches WHERE id=?', (batch_id,)).fetchone():
            raise ValueError('Unknown batch')
        rows = []
        jobs = list(c.execute('SELECT * FROM jobs WHERE batch_id=? ORDER BY id', (batch_id,)))
        sender_ready = os.environ.get('BR_COMMERCIAL_EMAIL', '').strip() == COMMERCIAL_EMAIL
        try:
            gmail.sender_config(ledger, gmail.APPROVED_SENDER)
        except (ValueError, gmail.PreSendError):
            sender_ready = False
        for job in jobs:
            data = json.loads(job['data'])
            prepared = data.get('commercial_contact') or {}
            blockers = []
            if prepared.get('channel') != 'email':
                blockers.append('Canal selecionado não é e-mail')
            else:
                try:
                    gmail.validate(ledger, c, job)
                except ValueError as exc:
                    blockers.append(str(exc))
                if not sender_ready:
                    blockers.append('Identidade comercial ou remetente Gmail não configurado corretamente')
                if c.execute("SELECT 1 FROM commercial_attempts WHERE job_id=? AND source='gmail_api' AND touch=0", (job['id'],)).fetchone():
                    blockers.append('Tentativa Gmail anterior exige revisão; sem repetição automática')
            rows.append({'job_id': job['id'], 'name': job['name'],
                         'segment': data.get('template') or '',
                         'opportunity_type': data.get('opportunity_type') or '',
                         'preview_url': job['preview_url'],
                         'recipient': prepared.get('destination') or '',
                         'subject': prepared.get('subject') or '',
                         'message': prepared.get('message') or '',
                         'channel': prepared.get('channel') or '',
                         'approval_digest': gmail.approval_digest(job),
                         'eligible': not blockers, 'blockers': blockers,
                         'status': job['contact_status']})
        attempts = list(c.execute('''SELECT a.status FROM commercial_attempts a JOIN jobs j ON j.id=a.job_id
            WHERE j.batch_id=? AND a.source='gmail_api' AND a.touch=0''', (batch_id,)))
        statuses = [row['status'] for row in attempts]
        counts = {
            'prospected': len(jobs),
            'in_production': sum(j['stage'] in ('extracting','building','checking','deploying') for j in jobs),
            'previews_verified': sum(json.loads(j['data']).get('preview_verified') is True for j in jobs),
            'messages_prepared': sum(bool((json.loads(j['data']).get('commercial_contact') or {}).get('message')) for j in jobs),
            'awaiting_approval': sum(row['eligible'] for row in rows),
            'sending': statuses.count('attempting'),
            'sent': statuses.count('sent'),
            'blocked': sum(bool(row['blockers']) and row['status'] not in ('not_sent', 'sent')
                           for row in rows),
            'uncertain': statuses.count('uncertain') + statuses.count('attempting'),
        }
        durations = {row['stage']: row['seconds'] for row in c.execute('''SELECT s.stage,SUM(s.duration_seconds) seconds
            FROM stage_runs s JOIN jobs j ON j.id=s.job_id WHERE j.batch_id=? AND s.duration_seconds IS NOT NULL
            GROUP BY s.stage''', (batch_id,))}
        try:
            auth = gmail.private_json(_authorization_path(ledger))
        except ValueError:
            auth = {}
        dispatch_state = auth if auth.get('batch_id') == batch_id else {}
        return {'rows': rows, 'counts': counts, 'duration_seconds': durations,
                'capacity': _counts(c, batch_id, ledger.now()),
                'dispatch_status': dispatch_state.get('dispatch_status', ''),
                'operational_failure': dispatch_state.get('operational_failure', '')}


def approve(ledger, batch_id, job_ids, reviewed=None, *, start_dispatch=False):
    if (not isinstance(job_ids, list) or not job_ids or len(job_ids) != len(set(job_ids))
            or any(not isinstance(jid, str) for jid in job_ids)):
        raise ValueError('Select distinct job IDs for approval')
    if not isinstance(reviewed, dict) or set(reviewed) != set(job_ids):
        raise ValueError('Exact reviewed contacts are required for approval')
    with ledger.connect() as c:
        if not c.execute('SELECT 1 FROM batches WHERE id=?', (batch_id,)).fetchone():
            raise ValueError('Unknown batch')
        path = _authorization_path(ledger)
        if path.exists():
            previous = gmail.private_json(path)
            if previous.get('approval_version') == 2 and _uncertain(c, previous):
                raise ValueError('An earlier Gmail attempt has an uncertain outcome; reconcile it before another approval')
            if _authorization_valid(previous) and _pending(c, previous):
                raise ValueError('An active Gmail authorization still has pending contacts; finish or reconcile it before another approval')
        capacity = _counts(c, batch_id, ledger.now())
        if len(job_ids) > capacity['approvable_now']:
            raise ValueError(f"Only {capacity['approvable_now']} new Gmail sends fit the batch and daily limits")
        if os.environ.get('BR_COMMERCIAL_EMAIL', '').strip() != COMMERCIAL_EMAIL:
            raise ValueError('Approved commercial email must be contato@scarasoft.com.br')
        gmail.sender_config(ledger, gmail.APPROVED_SENDER)
        for jid in job_ids:
            job = c.execute('SELECT * FROM jobs WHERE id=? AND batch_id=?', (jid, batch_id)).fetchone()
            if job is None:
                raise ValueError('Selected job is outside the batch')
            gmail.validate(ledger, c, job)
            if c.execute("SELECT 1 FROM commercial_attempts WHERE job_id=? AND source='gmail_api' AND touch=0", (jid,)).fetchone():
                raise ValueError('Prior Gmail attempt requires review; no automatic retry')
            if reviewed[jid] != gmail.approval_digest(job):
                raise ValueError('Reviewed contact or preview changed; refresh and approve again')
        approved_at = dt.datetime.now(dt.timezone.utc)
        auth = {'mode': 'live', 'approval_version': 2, 'approved_by': 'Lucas Scaranello',
                'approval_id': uuid.uuid4().hex, 'dispatch_status': 'pending',
                'approved_at': approved_at.isoformat(timespec='seconds'),
                'expires_at': (approved_at+dt.timedelta(hours=24)).isoformat(timespec='seconds'),
                'batch_id': batch_id, 'job_ids': job_ids, 'reviewed': reviewed,
                'sender': gmail.APPROVED_SENDER,
                'max_contacts': capacity['prior_attempts']+len(job_ids),
                'daily_limit': DAILY_LIMIT}
        _write_authorization(path, auth)
        ledger.event(c, None, f'Gmail batch approved: {batch_id}; limit {auth["max_contacts"]}; job_ids={json.dumps(job_ids)}.')
    result = {'batch_id': batch_id, 'job_ids': job_ids, 'new_sends': len(job_ids),
              'prior_attempts': capacity['prior_attempts'], 'max_contacts': auth['max_contacts'],
              'capacity': {'prior_attempts': capacity['prior_attempts'], 'approved_new': len(job_ids),
                           'remaining_batch': capacity['remaining_batch']-len(job_ids),
                           'remaining_daily': capacity['remaining_daily']-len(job_ids),
                           'approvable_now': capacity['approvable_now']-len(job_ids)}}
    if start_dispatch:
        threading.Thread(target=dispatch_batch, args=(ledger, batch_id), daemon=True).start()
    return result


def dispatch_batch(ledger, batch_id, client_factory=None):
    if not _dispatch_lock.acquire(blocking=False):
        return {'batch_id': batch_id, 'status': 'already_running', 'results': []}
    approval_id = None
    results = []
    try:
        auth = gmail.private_json(_authorization_path(ledger))
        if auth.get('mode') != 'live' or auth.get('approval_version') != 2 or auth.get('batch_id') != batch_id:
            raise ValueError('No live authorization for this batch')
        approval_id = auth.get('approval_id')
        if not _authorization_valid(auth):
            _set_dispatch_state(ledger, approval_id, 'closed', 'expired')
            return {'batch_id': batch_id, 'status': 'expired', 'results': [], 'report': review(ledger, batch_id)}
        unresolved = False
        blocked = False
        for jid in auth['job_ids']:
            with ledger.connect() as c:
                job = c.execute('SELECT * FROM jobs WHERE id=? AND batch_id=?', (jid, batch_id)).fetchone()
                if job is None:
                    results.append({'job_id': jid, 'status': 'blocked', 'reason': 'Job outside batch'})
                    blocked = True
                    continue
                prior = c.execute("SELECT status FROM commercial_attempts WHERE job_id=? AND source='gmail_api' AND touch=0", (jid,)).fetchone()
                if prior:
                    results.append({'job_id': jid, 'status': prior['status'], 'reason': 'Existing attempt; no automatic retry'})
                    if prior['status'] in ('attempting', 'uncertain'): unresolved = True
                    continue
            try:
                result = gmail.dispatch(ledger, jid, client_factory() if client_factory else None)
                results.append({'job_id': jid, **result})
                if result['status'] in ('attempting', 'uncertain'): unresolved = True
            except ValueError as exc:
                results.append({'job_id': jid, 'status': 'blocked', 'reason': str(exc)})
                blocked = True
                if 'limit' in str(exc).lower() or 'authorization' in str(exc).lower(): break
        if unresolved:
            _set_dispatch_state(ledger, approval_id, 'paused', 'needs_reconciliation')
            status = 'needs_reconciliation'
        elif blocked:
            _set_dispatch_state(ledger, approval_id, 'paused', 'blocked')
            status = 'blocked'
        else:
            _set_dispatch_state(ledger, approval_id, 'closed', 'complete')
            status = 'complete'
        return {'batch_id': batch_id, 'status': status, 'results': results, 'report': review(ledger, batch_id)}
    except Exception as exc:
        reason = f'Unexpected dispatcher failure ({type(exc).__name__}); inspect the ledger before retrying'
        if approval_id is not None:
            _set_dispatch_state(ledger, approval_id, 'paused', 'operational_failure', reason)
        return {'batch_id': batch_id, 'status': 'operational_failure', 'results': results,
                'operational_failure': reason, 'report': review(ledger, batch_id)}
    finally:
        _dispatch_lock.release()


def resume(ledger, client_factory=None):
    try:
        auth = gmail.private_json(_authorization_path(ledger))
    except ValueError:
        return {'status': 'no_authorization'}
    if (auth.get('mode') != 'live' or auth.get('approval_version') != 2
            or not isinstance(auth.get('batch_id'), str)):
        return {'status': 'paused' if auth.get('mode') == 'paused' else 'no_authorization'}
    return dispatch_batch(ledger, auth['batch_id'], client_factory)
