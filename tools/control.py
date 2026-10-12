#!/usr/bin/env python3
"""Local, transactional job ledger and contact-sheet server. Standard library only."""
import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import uuid
import mimetypes
sys.path.insert(0, str(Path(__file__).resolve().parent))
from quick_site import create as create_quick_site, TEMPLATES, profile, validate as validate_quick_site
import commercial

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get('REVAMP_DB', ROOT / 'data' / 'revamp.sqlite3'))
OUTREACH_AUTH_FILE = ROOT / 'data' / 'outreach-authorization.json'
STAGES = ['queued', 'reviewing', 'verified', 'qualified', 'extracting', 'building', 'checking', 'deploying', 'ready', 'contacting', 'complete', 'sent', 'uncertain', 'blocked', 'skipped', 'manual', 'simulated']
NEXT = {'queued': ['reviewing'], 'reviewing': ['verified', 'extracting'], 'verified': ['qualified'], 'qualified': ['extracting'], 'extracting': ['building'], 'building': ['checking'], 'checking': ['building', 'deploying'], 'deploying': ['checking', 'ready'], 'ready': ['contacting'], 'contacting': ['complete', 'sent', 'uncertain', 'blocked']}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

def ident(prefix):
    return prefix + '-' + uuid.uuid4().hex[:12]

def domain(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('A public HTTP(S) business URL without credentials is required')
    value = parsed.hostname.lower().rstrip('.').encode('idna').decode()
    value = value.removeprefix('www.')
    if '.' not in value or value in ('localhost',) or value.endswith(('.local', '.localhost')):
        raise ValueError('Use a public business domain')
    return value

def identity(value):
    kind, sep, raw = value.partition(':')
    if not sep: raise ValueError('Identity must use domain:, phone: or email:')
    kind = kind.lower().strip(); raw = raw.strip()
    if kind == 'domain': return 'domain:' + domain(raw if '://' in raw else 'https://' + raw)
    if kind == 'email':
        raw = raw.lower()
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', raw): raise ValueError('Invalid email identity')
        return 'email:' + raw
    if kind == 'phone':
        raw = re.sub(r'[ ()\-.]', '', raw)
        if not re.fullmatch(r'\+[1-9][0-9]{7,14}', raw): raise ValueError('Use an international phone number with +country code')
        return 'phone:' + raw
    raise ValueError('Identity must use domain:, phone: or email:')

SCHEMA_VERSION = 3


def migrate(con, hook=None):
    """Atomically initialize or migrate the ledger; keep FK checks on for normal work."""
    version = con.execute('PRAGMA user_version').fetchone()[0]
    if version > SCHEMA_VERSION:
        raise ValueError('Ledger schema is newer than this application')
    if version >= 2:
        domain_column = next(row for row in con.execute('PRAGMA table_info(jobs)') if row['name'] == 'domain')
        if domain_column['notnull']:
            raise ValueError('Ledger schema version and jobs.domain disagree')
    if version == SCHEMA_VERSION:
        return
    # SQLite cannot change foreign_keys inside a transaction. Turn it off only
    # for the table rebuild; every exit path closes or restores this connection.
    con.execute('PRAGMA foreign_keys=OFF')
    try:
        con.execute('BEGIN IMMEDIATE')
        version = con.execute('PRAGMA user_version').fetchone()[0]
        if version > SCHEMA_VERSION:
            raise ValueError('Ledger schema is newer than this application')
        if version < 2:
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='jobs_new'").fetchone():
                raise ValueError('Unexpected jobs_new table; inspect ledger before migration')
            con.execute("""CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY, industry TEXT NOT NULL, city TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, requested_count INTEGER NOT NULL DEFAULT 3)""")
            if 'requested_count' not in {row['name'] for row in con.execute('PRAGMA table_info(batches)')}:
                con.execute('ALTER TABLE batches ADD COLUMN requested_count INTEGER NOT NULL DEFAULT 3')
            exists = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='jobs'").fetchone()
            jobs_schema = """(id TEXT PRIMARY KEY,batch_id TEXT NOT NULL REFERENCES batches(id),name TEXT NOT NULL,url TEXT NOT NULL,domain TEXT UNIQUE,stage TEXT NOT NULL,worker TEXT,detail TEXT DEFAULT '',reason TEXT DEFAULT '',preview_url TEXT DEFAULT '',contact_status TEXT DEFAULT 'not_sent',data TEXT NOT NULL DEFAULT '{}',updated_at TEXT NOT NULL)"""
            if not exists:
                con.execute('CREATE TABLE jobs' + jobs_schema)
            else:
                domain_column = next(row for row in con.execute('PRAGMA table_info(jobs)') if row['name'] == 'domain')
                if domain_column['notnull']:
                    before = con.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
                    con.execute('CREATE TABLE jobs_new' + jobs_schema)
                    con.execute('INSERT INTO jobs_new SELECT * FROM jobs')
                    if hook: hook('copied')
                    con.execute('DROP TABLE jobs')
                    if hook: hook('dropped')
                    con.execute('ALTER TABLE jobs_new RENAME TO jobs')
                    if con.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] != before:
                        raise ValueError('Job count changed during migration')
            con.execute("""CREATE TABLE IF NOT EXISTS identities(identity TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id))""")
            con.execute("""CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT,message TEXT NOT NULL,created_at TEXT NOT NULL)""")
            con.execute("""CREATE TABLE IF NOT EXISTS workers(id TEXT PRIMARY KEY,job_id TEXT,status TEXT NOT NULL,updated_at TEXT NOT NULL)""")
            con.execute("""CREATE TABLE IF NOT EXISTS submissions(job_id TEXT PRIMARY KEY REFERENCES jobs(id),message TEXT NOT NULL,message_hash TEXT NOT NULL,form_url TEXT NOT NULL,status TEXT NOT NULL,evidence TEXT,created_at TEXT NOT NULL)""")
            con.execute("""CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT NOT NULL)""")
            con.execute("INSERT OR IGNORE INTO config VALUES ('max_workers','3')")
            if con.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('Ledger foreign key check failed')
            if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Ledger integrity check failed')
            if hook: hook('before_commit')
        con.execute('''CREATE TABLE IF NOT EXISTS commercial_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL REFERENCES jobs(id),
            channel TEXT NOT NULL, status TEXT NOT NULL, message TEXT NOT NULL,
            evidence TEXT NOT NULL, created_at TEXT NOT NULL)''')
        con.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
        con.execute('COMMIT')
    except BaseException:
        if con.in_transaction: con.execute('ROLLBACK')
        raise
    finally:
        con.execute('PRAGMA foreign_keys=ON')
        if con.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
            raise ValueError('Failed to enable SQLite foreign keys')


@contextlib.contextmanager
def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=15, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA foreign_keys=ON')
        migrate(con)
        con.execute('BEGIN IMMEDIATE')
        try:
            yield con
            con.execute('COMMIT')
        except BaseException:
            if con.in_transaction: con.execute('ROLLBACK')
            raise
    finally:
        con.close()

def event(c, job, message):
    c.execute('INSERT INTO events(job_id,message,created_at) VALUES(?,?,?)', (job, message[:4000], now()))

def production_status(job):
    data = json.loads(job['data']) if isinstance(job['data'], str) else job['data']
    if (data.get('preview_verified') is True and data.get('qa_passed') is True
            and (job['stage'] in ('ready','contacting','complete','sent','uncertain','manual','simulated')
                 or (isinstance(data.get('deployment'), dict) and data['deployment'].get('id')
                     and data['deployment'].get('project') == 'scarasoft-previas'))
            and job['preview_url'].startswith('https://')):
        return 'published'
    if job['stage'] in ('blocked', 'skipped') or data.get('commercial_category') == 'descartada':
        return 'pending'
    if job['stage'] in ('building', 'checking', 'deploying', 'ready', 'contacting', 'complete', 'sent', 'manual', 'simulated'):
        return 'generated'
    if job['stage'] in ('qualified','extracting') and data.get('commercial_category') in ('A_prioritaria', 'B_promissora', 'C_potencial'):
        return 'qualified'
    if data.get('presence_status') or data.get('verification'):
        return 'verified'
    return 'discovered'

def batch_progress(c, bid):
    row = c.execute('SELECT requested_count FROM batches WHERE id=?', (bid,)).fetchone()
    if row is None: raise ValueError('Unknown batch')
    jobs = list(c.execute('SELECT * FROM jobs WHERE batch_id=?', (bid,)))
    statuses = [production_status(j) for j in jobs]
    published = statuses.count('published')
    running_jobs = {r[0] for r in c.execute("SELECT workers.job_id FROM workers JOIN jobs ON jobs.id=workers.job_id WHERE jobs.batch_id=? AND workers.status='running'", (bid,))}
    worker_count = len(running_jobs)
    evaluating = sum(j['stage'] in ('queued','reviewing','verified','qualified','extracting') for j in jobs)
    producing = sum(j['stage'] in ('building','checking','deploying','ready') and status != 'published'
                    for j, status in zip(jobs, statuses))
    unfinished = worker_count + producing
    counts = {stage: sum(j['stage'] == stage for j in jobs) for stage in STAGES}
    remaining = max(0, row['requested_count'] - published)
    pending = sum(status in ('pending','discovered') or (json.loads(j['data']).get('identity_review') or {}).get('status') in ('pending','same')
                  or json.loads(j['data']).get('commercial_category') == 'D_pendente'
                  for j, status in zip(jobs, statuses))
    return {'discovered_count': len(jobs), 'candidate_count': len(jobs),
            'evaluating_count': evaluating, 'production_count': producing, 'worker_count': worker_count,
            'unfinished_count': unfinished,
            'verified_count': sum(x in ('verified','qualified','generated','published') for x in statuses),
            'qualified_count': sum(x in ('qualified','generated','published') for x in statuses),
            'generated_count': sum(x in ('generated','published') for x in statuses),
            'published_count': published, 'pending_count': pending,
            'completed_count': published, 'active_count': worker_count, 'remaining_count': remaining,
            'manual_count': counts.get('manual', 0), 'available_count': max(0, remaining - producing)}

def batch_status(bid, status):
    if status not in ('running', 'complete', 'blocked', 'exhausted'): raise ValueError('Invalid batch status')
    with connect() as c:
        progress = batch_progress(c, bid)
        if status in ('complete', 'exhausted') and progress['unfinished_count']:
            raise ValueError('Batch has unfinished jobs')
        if status == 'complete' and progress['remaining_count']:
            raise ValueError(f"Batch needs {progress['remaining_count']} more verified public previews")
        c.execute('UPDATE batches SET status=? WHERE id=?', (status, bid))
        return {'status': status, **progress}

def snapshot():
    with connect() as c:
        out = {table: [dict(r) for r in c.execute('SELECT * FROM ' + table + (' ORDER BY id DESC LIMIT 200' if table == 'events' else ''))] for table in ('batches', 'jobs', 'events', 'workers')}
        for j in out['jobs']: j['data'] = json.loads(j['data'])
        out['commercial_attempts'] = [dict(r) for r in c.execute('SELECT * FROM commercial_attempts ORDER BY id DESC')]
        out['legacy_submissions'] = [dict(r) for r in c.execute('SELECT * FROM submissions')]
        for b in out['batches']: b.update(batch_progress(c, b['id']))
        out['settings'] = {'batch_size': 3, 'max_workers': int(c.execute("SELECT value FROM config WHERE key='max_workers'").fetchone()[0])}
        out['templates'] = [{'id': k, 'name': v['name']} for k,v in TEMPLATES.items()]
        out['server_time'] = now()
        return out

def batch(industry, city, requested_count=3):
    if not isinstance(industry, str) or not isinstance(city, str) or not industry.strip() or not city.strip():
        raise ValueError('Industry and city are required')
    if len(industry)>150 or len(city)>150: raise ValueError('Use an industry and city under 150 characters')
    if industry != 'all' and industry not in TEMPLATES: raise ValueError('Choose an available template or all')
    if isinstance(requested_count, bool) or not isinstance(requested_count, int) or not 1 <= requested_count <= 100:
        raise ValueError('Website count must be a whole number from 1 to 100')
    with connect() as c:
        bid = ident('batch')
        c.execute('INSERT INTO batches(id,industry,city,status,created_at,requested_count) VALUES (?,?,?,?,?,?)', (bid, industry.strip(), city.strip(), 'queued', now(), requested_count))
        event(c, None, f'Batch queued: {requested_count} websites for {industry.strip()} in {city.strip()}. Waiting for Codex coordinator.')
        return {'id': bid, 'status': 'queued', 'requested_count': requested_count}

def cancel_batch(bid, reason):
    """Stop an unsubmitted batch while retaining its audit and dedupe records."""
    if not reason.strip(): raise ValueError('Provide a cancellation reason')
    with connect() as c:
        batch_row = c.execute('SELECT id FROM batches WHERE id=?', (bid,)).fetchone()
        if batch_row is None: raise ValueError('Unknown batch')
        active = c.execute("SELECT id,stage FROM jobs WHERE batch_id=? AND stage NOT IN ('complete','sent','uncertain','blocked','skipped','manual')", (bid,)).fetchall()
        for job in active:
            # A submission attempt must never be silently cancelled or made retryable.
            attempted = c.execute('SELECT 1 FROM submissions WHERE job_id=?', (job['id'],)).fetchone()
            stage = 'uncertain' if attempted else 'skipped'
            detail = f'{reason} No outreach submission was made.' if not attempted else f'{reason} Submission history retained as uncertain; do not retry.'
            c.execute('UPDATE jobs SET stage=?,detail=?,worker=NULL,updated_at=?,contact_status=? WHERE id=?', (stage, detail, now(), 'uncertain' if attempted else 'not_sent', job['id']))
            if attempted:
                c.execute("UPDATE submissions SET status='uncertain',evidence=? WHERE job_id=?", (detail, job['id']))
            c.execute("UPDATE workers SET status='idle',updated_at=? WHERE job_id=?", (now(), job['id']))
            event(c, job['id'], f'Batch cancelled: {detail}')
        c.execute("UPDATE batches SET status='cancelled' WHERE id=?", (bid,))
        event(c, None, f'Batch {bid} cancelled: {reason}')
        return {'id': bid, 'status': 'cancelled', 'stopped_jobs': len(active)}

def clear_all(reason):
    """Clear dashboard work records while retaining operational configuration."""
    if not reason.strip(): raise ValueError('Provide a reset reason')
    if DB.resolve() == (ROOT / 'data' / 'revamp.sqlite3').resolve():
        raise ValueError('clear-all is disabled for the durable MVP ledger; use a disposable REVAMP_DB for tests')
    with connect() as c:
        counts = {table: c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in ('batches','jobs','identities','events','workers','submissions')}
        # Delete children before their referenced parents. `config` intentionally survives.
        for table in ('commercial_attempts','submissions','events','workers','identities','jobs','batches'):
            c.execute(f'DELETE FROM {table}')
        return {'cleared': counts, 'reason': reason}

def business_identity(name, city):
    import unicodedata
    def norm(value):
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
        return re.sub(r'[^a-z0-9]+', '-', value).strip('-')
    return f"business:{norm(name)}:{norm(city.partition(',')[0])}"

def evidence_url(value):
    if not isinstance(value, str) or not value.startswith(('https://','http://')):
        raise ValueError('Evidence source must be an HTTP(S) URL')
    domain(value)

def checked_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Evidence needs checked_at as YYYY-MM-DD')
    dt.date.fromisoformat(value)

def validate_verification(value):
    if not isinstance(value, dict): raise ValueError('Verification must be an object')
    checked_date(value.get('checked_at'))
    sources = value.get('sources')
    if not isinstance(sources, list) or not sources: raise ValueError('Verification needs sources')
    for source in sources: evidence_url(source)
    if 'queries' in value and (not isinstance(value['queries'], list) or any(not isinstance(q,str) or not q.strip() for q in value['queries'])):
        raise ValueError('Invalid presence queries')

def validate_contacts(value):
    if not isinstance(value, dict): raise ValueError('Contacts must be an object')
    phone = value.get('phone')
    if phone is not None:
        if not isinstance(phone, dict) or not phone.get('value'):
            raise ValueError('Phone must include a value')
        identity('phone:' + phone['value'])
        evidence_url(phone.get('source'))
        checked_date(phone.get('checked_at'))
    for channel in ('email','form'):
        record = value.get(channel)
        if not isinstance(record, dict) or record.get('status') not in ('encontrado','nao_encontrado','nao_verificado'):
            raise ValueError(f'{channel} needs encontrado, nao_encontrado or nao_verificado')
        if record['status'] != 'nao_verificado':
            evidence_url(record.get('source'))
            checked_date(record.get('checked_at'))
        if channel == 'email' and record['status'] == 'encontrado':
            identity('email:' + str(record.get('value', '')))
        if channel == 'form' and record['status'] == 'encontrado':
            evidence_url(record.get('url'))
            if not isinstance(record.get('purpose'), str) or not record['purpose'].strip() or type(record.get('eligible')) is not bool or not isinstance(record.get('restrictions'), list):
                raise ValueError('Found form needs URL, purpose, eligibility and restrictions')
    whatsapp = value.get('whatsapp')
    if whatsapp is not None:
        if not isinstance(whatsapp, dict) or whatsapp.get('status') not in ('confirmado','presumido','nao_utiliza','nao_verificado'):
            raise ValueError('Invalid WhatsApp status')
        if whatsapp['status'] == 'presumido' and not phone:
            raise ValueError('Presumed WhatsApp needs a public phone')
        if whatsapp['status'] == 'confirmado':
            identity('phone:' + str(whatsapp.get('value', '')))
            evidence_url(whatsapp.get('source'))
            checked_date(whatsapp.get('checked_at'))
        if whatsapp['status'] == 'nao_utiliza':
            evidence_url(whatsapp.get('source'))
            checked_date(whatsapp.get('checked_at'))

def validate_services(value, template):
    if not isinstance(value, dict): raise ValueError('Services must be an object')
    confirmed, excluded, evidence = value.get('confirmed', []), value.get('excluded', []), value.get('evidence', {})
    if not isinstance(confirmed,list) or not isinstance(excluded,list) or not isinstance(evidence,dict):
        raise ValueError('Invalid services evidence')
    catalog = profile(template)['catalog']
    defaults = profile(template)['segment']['default_services']
    if any(not isinstance(s,str) or s not in catalog for s in confirmed + excluded):
        raise ValueError('Service outside template catalog')
    if len(confirmed) != len(set(confirmed)) or len(excluded) != len(set(excluded)) or set(confirmed) & set(excluded):
        raise ValueError('Conflicting or duplicate services')
    for service in set(excluded) | {s for s in confirmed if s not in defaults}:
        item = evidence.get(service)
        if not isinstance(item,dict) or not isinstance(item.get('observation'),str) or not item['observation'].strip():
            raise ValueError('Service addition or exclusion needs observed evidence')
        evidence_url(item.get('source'))
        if service in excluded and service in defaults and item.get('contradiction') is not True:
            raise ValueError('Default service exclusion needs an explicit documented contradiction')

def add(bid, name, url='', aliases=(), template=None):
    if not name or not name.strip(): raise ValueError('Business name required')
    d = domain(url) if url else None
    with connect() as c:
        row = c.execute('SELECT * FROM batches WHERE id=?', (bid,)).fetchone()
        if row is None: raise ValueError('Unknown batch')
        if row['status'] in ('complete','cancelled'): raise ValueError('Batch is closed')
        chosen = template or row['industry']
        if chosen not in TEMPLATES or (row['industry'] != 'all' and chosen != row['industry']):
            raise ValueError('Choose the batch segment or an available template for all')
        # Name and city are a review signal, never a unique identity. Homonyms
        # can legitimately share both values across different businesses.
        possible = [other['id'] for other in c.execute('''
            SELECT jobs.id, jobs.name, batches.city FROM jobs
            JOIN batches ON batches.id=jobs.batch_id''')
            if business_identity(other['name'], other['city']) == business_identity(name, row['city'])]
        jid = ident('site')
        keys = set(identity(a) for a in aliases)
        if d: keys.add('domain:'+d)
        if not keys and not possible:
            review = {'status': 'pending', 'reason': 'No reliable domain, phone or email identity yet'}
        elif possible:
            review = {'status': 'pending', 'possible_matches': possible}
        else:
            review = {'status': 'clear'}
        c.execute('INSERT INTO jobs(id,batch_id,name,url,domain,stage,data,updated_at) VALUES(?,?,?,?,?,?,?,?)',
                  (jid,bid,name.strip(),url or '',d,'queued',json.dumps({'template': chosen, 'identity_review': review}),now()))
        for key in keys: c.execute('INSERT INTO identities VALUES (?,?)',(key,jid))
        event(c,jid,'Prospect registered; identity review pending.' if review['status'] == 'pending' else 'Prospect registered; reliable identities reserved.')
        return {'id':jid, 'identity_review': review}

def reserve_contact_identities(c, jid, contacts):
    keys = []
    if contacts.get('phone'):
        keys.append(identity('phone:' + contacts['phone']['value']))
    email = contacts.get('email') or {}
    if email.get('status') == 'encontrado':
        keys.append(identity('email:' + email['value']))
    whatsapp = contacts.get('whatsapp') or {}
    if whatsapp.get('status') == 'confirmado':
        keys.append(identity('phone:' + whatsapp['value']))
    for key in set(keys):
        existing = c.execute('SELECT job_id FROM identities WHERE identity=?', (key,)).fetchone()
        if existing and existing['job_id'] != jid:
            raise ValueError(f'Contact identity already belongs to job {existing["job_id"]}; review duplicate')
        if not existing: c.execute('INSERT INTO identities VALUES (?,?)', (key, jid))

def own(c, jid, worker):
    j = c.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
    if j is None: raise ValueError('Unknown job')
    if not worker or j['worker'] != worker: raise ValueError('Worker does not own this job')
    if not c.execute("SELECT 1 FROM workers WHERE id=? AND job_id=? AND status='running'", (worker,jid)).fetchone():
        raise ValueError('Worker assignment is no longer active')
    return j

def claim(bid, worker):
    with connect() as c:
        batch_row = c.execute('SELECT status FROM batches WHERE id=?', (bid,)).fetchone()
        if not batch_row or batch_row['status'] in ('complete','cancelled'):
            raise ValueError('Batch is missing or closed')
        progress = batch_progress(c, bid)
        if progress['worker_count'] >= progress['remaining_count']:
            raise ValueError('Batch worker capacity is covered by the preview target')
        if c.execute("SELECT 1 FROM workers WHERE id=? AND status='running'",(worker,)).fetchone(): raise ValueError('Worker already owns a running job')
        limit = int(c.execute("SELECT value FROM config WHERE key='max_workers'").fetchone()[0])
        if c.execute("SELECT COUNT(*) FROM workers WHERE status='running'").fetchone()[0]>=limit: raise ValueError('Worker capacity reached')
        j = c.execute("SELECT * FROM jobs WHERE batch_id=? AND stage='queued' AND worker IS NULL ORDER BY rowid LIMIT 1",(bid,)).fetchone()
        if j is None: return {'job': None}
        c.execute("UPDATE jobs SET worker=?,stage='reviewing',updated_at=? WHERE id=?",(worker,now(),j['id']))
        c.execute('INSERT INTO workers VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET job_id=excluded.job_id,status=excluded.status,updated_at=excluded.updated_at',(worker,j['id'],'running',now()))
        c.execute("UPDATE batches SET status='running' WHERE id=?",(bid,))
        event(c,j['id'],f'{worker} claimed this business.')
        return {'job':dict(c.execute('SELECT * FROM jobs WHERE id=?',(j['id'],)).fetchone())}

def update(jid, worker, stage=None, detail='', fields=None):
    fields = fields or {}
    if not isinstance(fields,dict): raise ValueError('Fields must be a JSON object')
    allowed = {'reason','preview_url','qa_passed','preview_verified','source_urls','screenshots','browser_id','tab_id','workspace','booking_url','logo_decision','cost','failure','contact_url','qualification','seo_checked','outreach_mode','contact_email','contact_phone','template','presence_status','commercial_category','opportunity_type','verification','contacts','commercial_reason','discard_reason','deployment','services','qualified','qa_evidence','identity_review'}
    if set(fields)-allowed: raise ValueError('Unknown fields: '+str(set(fields)-allowed))
    with connect() as c:
        j=own(c,jid,worker)
        new=stage or j['stage']
        if new not in STAGES: raise ValueError('Unknown stage')
        if new in ('contacting','complete','sent','uncertain','manual','simulated') and new!=j['stage']: raise ValueError('Use contact-begin, contact-finish, contact-simulate or manual-outreach')
        if new!=j['stage'] and new not in NEXT.get(j['stage'],[]) + (['blocked','skipped'] if j['stage'] not in ('complete','sent','uncertain','blocked','skipped','manual','simulated','contacting') else []):
            raise ValueError('Invalid stage transition')
        data=json.loads(j['data']); data.update(fields)
        if 'identity_review' in fields:
            review = fields['identity_review']
            if (not isinstance(review, dict) or review.get('status') not in ('distinct','same')
                    or not isinstance(review.get('reason'), str) or not review['reason'].strip()
                    or not isinstance(review.get('sources'), list) or not review['sources']):
                raise ValueError('Identity review needs distinct/same, reason and sources')
            for source in review['sources']: evidence_url(source)
        if 'template' in fields and (fields['template'] not in TEMPLATES or fields['template'] != data.get('template')):
            raise ValueError('Template is fixed when the prospect is added')
        if 'presence_status' in fields and fields['presence_status'] not in ('site_confirmado','site_inoperante','sem_site_confirmado','sem_site_potencial','presenca_inconclusiva'):
            raise ValueError('Invalid digital presence status')
        if 'commercial_category' in fields and fields['commercial_category'] not in ('A_prioritaria','B_promissora','C_potencial','D_pendente','descartada'):
            raise ValueError('Invalid commercial category')
        if 'opportunity_type' in fields and fields['opportunity_type'] not in ('redesign','primeiro_site'):
            raise ValueError('Invalid opportunity type')
        if data.get('commercial_category') and (not isinstance(data.get('commercial_reason'), str) or not data['commercial_reason'].strip()):
            raise ValueError('Commercial category needs an objective reason')
        if data.get('commercial_category') == 'descartada' and (not isinstance(data.get('discard_reason'), str) or not data['discard_reason'].strip()):
            raise ValueError('Discard needs a reason')
        if 'verification' in fields: validate_verification(fields['verification'])
        if 'contacts' in fields: validate_contacts(fields['contacts'])
        if 'services' in fields: validate_services(fields['services'], data['template'])
        if 'contacts' in fields: reserve_contact_identities(c, jid, fields['contacts'])
        if new == 'qualified' and (data.get('commercial_category') not in ('A_prioritaria','B_promissora','C_potencial')
                                   or data.get('presence_status') not in ('site_confirmado','site_inoperante','sem_site_confirmado')
                                   or not isinstance(data.get('verification'), dict) or not data['verification'].get('sources')):
            raise ValueError('Essential commercial and presence evidence required for qualification')
        if new == 'qualified' and data.get('identity_review', {}).get('status') in ('pending', 'same'):
            raise ValueError('Ambiguous business identity needs documented distinct review')
        if new == 'qualified':
            validate_verification(data['verification'])
            validate_contacts(data.get('contacts'))
            contacts = data['contacts']
            if not (contacts.get('phone') or (contacts.get('email') or {}).get('status') == 'encontrado'
                    or (contacts.get('whatsapp') or {}).get('status') == 'confirmado'):
                raise ValueError('A verified public contact is needed for preview generation')
            if ((data['presence_status'] == 'sem_site_confirmado' and data.get('opportunity_type') != 'primeiro_site')
                    or (data['presence_status'] in ('site_confirmado','site_inoperante') and data.get('opportunity_type') != 'redesign')):
                raise ValueError('Opportunity type conflicts with verified digital presence')
        if new == 'qualified' and data.get('presence_status') == 'site_confirmado' and data.get('opportunity_type') == 'redesign':
            qualification = data.get('qualification')
            findings = qualification.get('findings') if isinstance(qualification, dict) else None
            if not isinstance(findings,list) or not any(isinstance(f,str) and f.strip() for f in findings) or not isinstance(data.get('screenshots'),list) or not data['screenshots']:
                raise ValueError('Redesign needs observed visual findings and screenshots')
        if new == 'qualified' and data.get('presence_status') == 'sem_site_confirmado' and not data['verification'].get('queries'):
            raise ValueError('Confirmed first-site opportunity needs documented presence queries')
        if new in ('building','checking','deploying','ready') and data.get('commercial_category') not in ('A_prioritaria','B_promissora','C_potencial'):
            raise ValueError('Commercial qualification required before generation')
        if new in ('building','checking','deploying','ready') and data.get('presence_status') not in ('site_confirmado','site_inoperante','sem_site_confirmado'):
            raise ValueError('Essential digital presence confirmation required')
        if new == 'building' and j['stage'] != 'building' and batch_progress(c, j['batch_id'])['available_count'] < 1:
            raise ValueError('Preview production slots are full; keep candidate qualified for a later replacement')
        if new != j['stage'] and new in ('building', 'checking'):
            data['qa_passed'] = False
            data['preview_verified'] = False
        if new=='deploying' and data.get('qa_passed') is not True: raise ValueError('Passing QA evidence required')
        if new=='ready' and (data.get('preview_verified') is not True or not data.get('preview_url',j['preview_url']).startswith('https://')): raise ValueError('Verified HTTPS preview required')
        if new=='ready' and (not isinstance(data.get('deployment'),dict) or not data['deployment'].get('id') or data['deployment'].get('project') != 'scarasoft-previas' or not data.get('qa_evidence')):
            raise ValueError('Deployment ID, approved project and QA evidence required')
        c.execute('UPDATE jobs SET stage=?,detail=?,reason=?,preview_url=?,data=?,worker=?,updated_at=? WHERE id=?',
                  (new,detail or j['detail'],fields.get('reason',j['reason']),fields.get('preview_url',j['preview_url']),json.dumps(data),
                   None if new in ('blocked','skipped') else worker,now(),jid))
        c.execute('UPDATE workers SET updated_at=? WHERE id=?',(now(),worker))
        if new in ('blocked','skipped'): c.execute("UPDATE workers SET status='idle',updated_at=? WHERE id=?",(now(),worker))
        event(c,jid,detail or f'Stage: {new}')
        return {'id':jid,'stage':new}

def preview_finish(jid, worker):
    with connect() as c:
        j = own(c, jid, worker)
        if j['stage'] != 'ready' or production_status(j) != 'published':
            raise ValueError('Only a verified public preview can be finished')
        c.execute('UPDATE jobs SET worker=NULL,updated_at=? WHERE id=?', (now(), jid))
        c.execute("UPDATE workers SET status='idle',updated_at=? WHERE id=?", (now(), worker))
        event(c, jid, 'Verified commercial preview completed; no contact performed.')
        return {'id': jid, 'production_status': 'published', 'contact_status': j['contact_status']}

def recover(jid, reason):
    if not reason.strip(): raise ValueError('Recovery reason required')
    with connect() as c:
        j = c.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
        if not j: raise ValueError('Unknown job')
        attempt = c.execute('SELECT 1 FROM submissions WHERE job_id=?', (jid,)).fetchone()
        if j['stage'] in ('complete','sent','manual','simulated'):
            raise ValueError('Terminal outreach jobs cannot be automatically recovered')
        target = 'uncertain' if attempt else ('ready' if production_status(j) == 'published' else 'queued')
        c.execute('UPDATE jobs SET stage=?,worker=NULL,updated_at=?,contact_status=? WHERE id=?',
                  (target,now(),'uncertain' if attempt else j['contact_status'],jid))
        c.execute("UPDATE workers SET status='idle',updated_at=? WHERE job_id=?", (now(),jid))
        if attempt: c.execute("UPDATE submissions SET status='uncertain',evidence=? WHERE job_id=?", (reason,jid))
        event(c,jid,'Coordinator recovery after worker stopped: '+reason)
        return {'stage':target}

def site_input(jid, output):
    """Build a private quick_site batch record from verified ledger facts."""
    with connect() as c:
        job = c.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
        if job is None: raise ValueError('Unknown job')
        data = json.loads(job['data'])
        if data.get('commercial_category') not in ('A_prioritaria','B_promissora','C_potencial') or data.get('presence_status') not in ('site_confirmado','site_inoperante','sem_site_confirmado'):
            raise ValueError('Qualified opportunity and confirmed presence required')
        batch_row = c.execute('SELECT city FROM batches WHERE id=?', (job['batch_id'],)).fetchone()
    template = data['template']
    contacts = data.get('contacts') or {}
    validate_verification(data.get('verification'))
    validate_contacts(contacts)
    phone = contacts.get('phone') or {}
    email = contacts.get('email') or {}
    whatsapp = contacts.get('whatsapp') or {}
    services = data.get('services') or {}
    validate_services(services, template)
    defaults = profile(template)['segment']['default_services']
    excluded = services.get('excluded', [])
    confirmed = services.get('confirmed', [])
    enabled = list(dict.fromkeys([s for s in defaults if s not in excluded] + [s for s in confirmed if s not in excluded]))
    city, _, state = batch_row['city'].rpartition(',')
    record = {'template': template, 'name': job['name'], 'city': city.strip() if city else batch_row['city'],
              'state': state.strip().upper() if city and len(state.strip()) == 2 else '',
              'phone': phone.get('value', '') if isinstance(phone,dict) else '',
              'email': email.get('value', '') if isinstance(email,dict) and email.get('status') == 'encontrado' else '',
              'enabled_services': enabled, 'preview': True}
    address = data.get('verification') or {}
    for key in ('street', 'zip', 'service_area'):
        if isinstance(address.get(key),str): record[key] = address[key]
    if whatsapp.get('status') == 'confirmado': record['whatsapp'] = whatsapp.get('value', '')
    elif whatsapp.get('status') == 'nao_utiliza': record['whatsapp'] = False
    validate_quick_site(record)
    output = Path(output)
    if not output.resolve().is_relative_to((ROOT / 'runs').resolve()):
        raise ValueError('Write private site input under runs/')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([record], ensure_ascii=False, indent=2))
    return {'file': str(output), 'template': template, 'enabled_services': enabled}

def require_outreach_authorization(c, job, message=None):
    """Fail closed until a specific, locally recorded batch is approved for live contact."""
    try:
        auth = json.loads(OUTREACH_AUTH_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        raise ValueError('Live outreach is disabled: local batch authorization is missing')
    batch = c.execute('SELECT * FROM batches WHERE id=?', (job['batch_id'],)).fetchone()
    if (not isinstance(auth, dict) or auth.get('mode') != 'live'
            or auth.get('approved_by') != 'Lucas Scaranello'
            or auth.get('batch_id') != job['batch_id']
            or auth.get('industry') != batch['industry']
            or auth.get('city') != batch['city']
            or type(auth.get('max_contacts')) is not int
            or not 1 <= auth['max_contacts'] <= batch['requested_count']):
        raise ValueError('Live outreach authorization does not match this batch and scope')
    email = os.environ.get('BR_COMMERCIAL_EMAIL', '').strip()
    phone = os.environ.get('BR_COMMERCIAL_PHONE', '').strip()
    if not email or not phone or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        raise ValueError('Approved commercial email and phone must be configured locally')
    if message is not None and ('scarasoft — Lucas Scaranello' not in message or email not in message or phone not in message):
        raise ValueError('Message must contain the approved signature and configured commercial contacts')
    attempts = c.execute('SELECT COUNT(*) FROM submissions JOIN jobs ON jobs.id=submissions.job_id WHERE jobs.batch_id=?',
                         (job['batch_id'],)).fetchone()[0]
    if attempts >= auth['max_contacts']:
        raise ValueError('Authorized contact limit reached')

def contact_begin(jid,worker,message,form_url):
    if not message.strip(): raise ValueError('Message is empty')
    domain(form_url)
    with connect() as c:
        j=own(c,jid,worker); data=json.loads(j['data'])
        if j['contact_status'] in ('opted_out','not_interested','uncertain','sent','replied','interested') or c.execute('SELECT 1 FROM commercial_attempts WHERE job_id=?', (jid,)).fetchone():
            raise ValueError('Commercial history prevents an automatic submission')
        require_outreach_authorization(c, j, message)
        if data.get('outreach_mode') == 'manual':
            raise ValueError('This job is routed to manual outreach; do not submit automatically')
        if j['stage']!='ready' or data.get('qa_passed') is not True or data.get('preview_verified') is not True or not j['reason']:
            raise ValueError('Ready stage, specific reason, verified preview and passing QA required')
        if j['preview_url'] not in message:
            raise ValueError('Message must contain the verified public preview URL')
        qualification=data.get('qualification') or {}
        findings=qualification.get('findings',[]) if isinstance(qualification,dict) else []
        if len([f for f in findings if isinstance(f,str) and f.strip()]) < 2 or not data.get('source_urls') or not data.get('screenshots'):
            raise ValueError('Two qualification findings, source URLs and screenshot evidence required')
        if not c.execute('SELECT 1 FROM identities WHERE identity=? AND job_id=?',('domain:'+domain(form_url),jid)).fetchone():
            raise ValueError('Contact form must be on the original or verified alias domain')
        c.execute('INSERT INTO submissions VALUES(?,?,?,?,?,?,?)',(jid,message,hashlib.sha256(message.encode()).hexdigest(),form_url,'attempting',None,now()))
        c.execute("UPDATE jobs SET stage='contacting',contact_status='attempting',updated_at=? WHERE id=?",(now(),jid))
        event(c,jid,'Submission reserved. One submit attempt permitted; never auto-retry an uncertain result.')
        return {'id':jid,'status':'attempting'}

def contact_simulate(jid, worker, message, form_url):
    if not message.strip(): raise ValueError('Message is empty')
    domain(form_url)
    with connect() as c:
        j=own(c,jid,worker); data=json.loads(j['data'])
        if j['contact_status'] == 'opted_out': raise ValueError('Opt-out prevents contact preparation')
        if j['stage']!='ready' or data.get('qa_passed') is not True or data.get('preview_verified') is not True or not j['reason']:
            raise ValueError('Simulation requires a ready, qualified, verified preview')
        qualification=data.get('qualification') or {}
        findings=qualification.get('findings',[]) if isinstance(qualification,dict) else []
        if len([f for f in findings if isinstance(f,str) and f.strip()])<2 or not data.get('source_urls') or not data.get('screenshots'):
            raise ValueError('Two visual findings, source URLs and screenshots required')
        if j['preview_url'] not in message:
            raise ValueError('Message must contain the verified public preview URL')
        if not c.execute('SELECT 1 FROM identities WHERE identity=? AND job_id=?',('domain:'+domain(form_url),jid)).fetchone():
            raise ValueError('Contact form must be on the original or verified alias domain')
        if c.execute('SELECT 1 FROM submissions WHERE job_id=?',(jid,)).fetchone():
            raise ValueError('A real submission attempt already exists')
        data['contact_simulation']={'message':message,'form_url':form_url,'created_at':now()}
        c.execute("UPDATE jobs SET stage='simulated',contact_status='simulated',detail=?,data=?,worker=NULL,updated_at=? WHERE id=?",
                  ('Mensagem preparada em simulação; nenhum formulário enviado.',json.dumps(data),now(),jid))
        c.execute("UPDATE workers SET status='idle',updated_at=? WHERE id=?",(now(),worker))
        event(c,jid,'Contato simulado; nenhum submit realizado.')
        return {'id':jid,'stage':'simulated','contact_status':'simulated'}

def resume_simulated(jid, worker):
    """Reclaim an unsent simulation only after this exact batch gains live authorization."""
    if not worker: raise ValueError('Worker ID is required')
    with connect() as c:
        j=c.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
        if not j or j['stage']!='simulated': raise ValueError('Only a simulated job can be resumed')
        if c.execute('SELECT 1 FROM submissions WHERE job_id=?',(jid,)).fetchone():
            raise ValueError('A real submission attempt already exists')
        require_outreach_authorization(c,j)
        if c.execute("SELECT 1 FROM workers WHERE id=? AND status='running'",(worker,)).fetchone():
            raise ValueError('Worker already owns a running job')
        limit=int(c.execute("SELECT value FROM config WHERE key='max_workers'").fetchone()[0])
        if c.execute("SELECT COUNT(*) FROM workers WHERE status='running'").fetchone()[0]>=limit:
            raise ValueError('Worker capacity reached')
        c.execute("UPDATE jobs SET stage='ready',worker=?,contact_status='not_sent',updated_at=? WHERE id=?",(worker,now(),jid))
        c.execute('INSERT INTO workers VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET job_id=excluded.job_id,status=excluded.status,updated_at=excluded.updated_at',(worker,jid,'running',now()))
        c.execute("UPDATE batches SET status='running' WHERE id=?",(j['batch_id'],))
        event(c,jid,'Authorized simulation reclaimed; recheck preview, form and message before contact.')
        return {'id':jid,'stage':'ready','worker':worker}

def contact_finish(jid,worker,status,evidence):
    if status not in ('submitted','sent','uncertain','blocked') or not evidence.strip(): raise ValueError('Provide result and observed evidence')
    with connect() as c:
        j=own(c,jid,worker)
        if j['stage']!='contacting': raise ValueError('No submission in progress')
        c.execute('UPDATE submissions SET status=?,evidence=? WHERE job_id=?',(status,evidence,jid))
        c.execute('UPDATE jobs SET stage=?,contact_status=?,detail=?,worker=NULL,updated_at=? WHERE id=?',('complete' if status == 'submitted' else status,status,evidence,now(),jid))
        c.execute("UPDATE workers SET status='idle',updated_at=? WHERE id=?",(now(),worker))
        event(c,jid,f'Contact {status}: {evidence}')
        return {'id':jid,'status':status}

def manual_outreach(jid, worker, reason, message, email='', phone=''):
    if not reason.strip() or not message.strip():
        raise ValueError('Manual outreach needs a reason and prepared message')
    if email: email = identity('email:' + email).removeprefix('email:')
    if phone: phone = identity('phone:' + phone).removeprefix('phone:')
    with connect() as c:
        j = own(c, jid, worker)
        if j['contact_status'] == 'opted_out': raise ValueError('Opt-out prevents contact preparation')
        data = json.loads(j['data'])
        if j['stage'] != 'ready' or data.get('qa_passed') is not True or data.get('preview_verified') is not True or not j['preview_url'].startswith('https://'):
            raise ValueError('Manual outreach requires a ready, QA-passed, verified public website')
        if c.execute('SELECT 1 FROM submissions WHERE job_id=?', (jid,)).fetchone():
            raise ValueError('A reserved/attempted submission cannot become manual outreach automatically')
        if not data.get('source_urls') or j['preview_url'] not in message:
            raise ValueError('Contact sources and the verified preview URL in the message are required')
        qualification = data.get('qualification') or {}
        findings = qualification.get('findings', []) if isinstance(qualification, dict) else []
        if not j['reason'] or not data.get('screenshots') or len([f for f in findings if isinstance(f, str) and f.strip()]) < 2:
            raise ValueError('Manual outreach requires visual qualification and screenshot evidence')
        data['manual_outreach'] = {'reason': reason.strip(), 'message': message, 'email': email,
                                  'phone': phone, 'source_urls': data['source_urls']}
        data['outreach_mode'] = 'manual'
        c.execute("UPDATE jobs SET stage='manual', contact_status='manual_required', detail=?, data=?, worker=NULL, updated_at=? WHERE id=?",
                  (reason.strip(), json.dumps(data), now(), jid))
        c.execute("UPDATE workers SET status='idle',updated_at=? WHERE id=?", (now(), worker))
        event(c, jid, 'Manual outreach required: ' + reason.strip())
        return {'id': jid, 'stage': 'manual', 'contact_status': 'manual_required'}

COMMERCIAL_STATES = {'pending','prepared','sent','replied','interested','not_interested','opted_out','uncertain'}

def prepare_commercial(jid, observation=''):
    """Prepare copy only. No external request or production transition occurs."""
    with connect() as c:
        job = c.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
        if not job: raise ValueError('Unknown job')
        data = json.loads(job['data'])
        if data.get('preview_verified') is not True or not job['preview_url'].startswith('https://'):
            raise ValueError('A verified public preview is required')
        if job['contact_status'] in ('opted_out','not_interested','uncertain','sent','submitted','replied','interested','attempting'):
            raise ValueError('Commercial contact is already resolved or requires review')
        if c.execute('SELECT 1 FROM submissions WHERE job_id=?', (jid,)).fetchone():
            raise ValueError('Legacy submission exists; review before preparing')
        latest = c.execute('SELECT status FROM commercial_attempts WHERE job_id=? ORDER BY id DESC LIMIT 1', (jid,)).fetchone()
        if latest and latest['status'] != 'failed_no_send':
            raise ValueError('Prior attempt prevents preparation')
        failed = [row['channel'] for row in c.execute("SELECT channel FROM commercial_attempts WHERE job_id=? AND status='failed_no_send'", (jid,))]
        channel, destination = commercial.route(data.get('contacts'), failed)
        if channel == 'no_channel':
            data['commercial_contact'] = {'channel': channel, 'next_action': 'Pesquisar contato público adequado'}
            c.execute('UPDATE jobs SET data=?,contact_status=?,updated_at=? WHERE id=?', (json.dumps(data), 'pending', now(), jid))
            return data['commercial_contact']
        presence = data.get('presence_status')
        template = {'sem_site_confirmado': 'primeiro_site', 'site_confirmado': 'redesign', 'site_inoperante': 'site_inoperante'}.get(presence)
        if not template: raise ValueError('Digital presence is not sufficiently verified')
        if template == 'site_inoperante':
            verification = data.get('verification') or {}
            failure = verification.get('technical_failure') or {}
            checked = failure.get('checked_at','')
            try: recent = (dt.datetime.now(dt.timezone.utc).date() - dt.date.fromisoformat(checked)).days in range(0, 15)
            except ValueError: recent = False
            if (not recent or not isinstance(failure.get('source'),str) or not failure['source'].startswith(('https://','http://'))
                    or not isinstance(failure.get('result'),str) or not failure['result'].strip()
                    or type(failure.get('attempts')) is not int or failure['attempts'] < 2
                    or not observation.strip()):
                raise ValueError('Recent technical evidence and a verified observation are required')
            if observation.strip() != failure['result'].strip():
                raise ValueError('Observation must match the recorded technical result')
        batch_row = c.execute('SELECT city FROM batches WHERE id=?', (job['batch_id'],)).fetchone()
        city = batch_row['city'].split(',')[0].strip()
        segment = data.get('template')
        if segment not in commercial.SEARCHES: raise ValueError('Unknown segment')
        noun, search = commercial.SEARCHES[segment]
        values = {'empresa': job['name'], 'cidade': city, 'segmento': noun,
                  'busca_exemplo': search.replace('{cidade}', city), 'preview_url': job['preview_url'],
                  'observacao_verificada': observation.strip(), 'assinatura': 'scarasoft — Lucas Scaranello',
                  'email_comercial': os.environ.get('BR_COMMERCIAL_EMAIL','').strip(),
                  'telefone_comercial': os.environ.get('BR_COMMERCIAL_PHONE','').strip()}
        variant = 'full' if channel == 'email' else 'short'
        message = commercial.render(template, variant, values)
        subject = commercial.render(template, 'subject', values) if channel == 'email' else ''
        if channel != 'email':
            message += '\n\n{assinatura}\n{email_comercial}\n{telefone_comercial}'.format(**values)
        require_commercial_identity(message)
        prepared = {'channel': channel, 'destination': destination, 'template': template,
                    'message': message, 'subject': subject, 'prepared_at': now(),
                    'next_action': 'Revisar e registrar o resultado do contato manual' if channel == 'whatsapp_manual' else 'Revisar antes de qualquer envio'}
        if channel == 'whatsapp_manual': prepared['whatsapp_url'] = commercial.whatsapp_link(destination, message)
        data['commercial_contact'] = prepared
        c.execute('UPDATE jobs SET data=?,contact_status=?,updated_at=? WHERE id=?', (json.dumps(data, ensure_ascii=False), 'prepared', now(), jid))
        event(c, jid, 'Commercial message prepared; no contact sent.')
        return prepared

def require_commercial_identity(message):
    email = os.environ.get('BR_COMMERCIAL_EMAIL','').strip()
    phone = os.environ.get('BR_COMMERCIAL_PHONE','').strip()
    if not email or not phone or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        raise ValueError('Approved commercial email and phone must be configured locally')
    if any(value not in message for value in ('scarasoft — Lucas Scaranello', email, phone)):
        raise ValueError('Message lacks approved commercial identity')

def load_commercial_env():
    """Read only the two approved contact fields for the local dashboard."""
    try: lines = (ROOT / '.env').read_text().splitlines()
    except OSError: return
    for line in lines:
        match = re.fullmatch(r'\s*(BR_COMMERCIAL_EMAIL|BR_COMMERCIAL_PHONE)\s*=\s*(.*?)\s*', line)
        if match:
            value = match.group(2).strip().strip('"\'')
            if value: os.environ.setdefault(match.group(1), value)

def record_commercial(jid, status, evidence):
    """Operator records an observed result; opening a link never calls this."""
    allowed = {'sent','uncertain','failed_no_send','replied','interested','not_interested','opted_out'}
    if status not in allowed or not isinstance(evidence,str) or not evidence.strip():
        raise ValueError('Status and observed evidence are required')
    with connect() as c:
        job = c.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
        if not job: raise ValueError('Unknown job')
        data = json.loads(job['data'])
        prepared = data.get('commercial_contact') or {}
        current = job['contact_status']
        if current == 'opted_out' or c.execute("SELECT 1 FROM commercial_attempts WHERE job_id=? AND status='opted_out'", (jid,)).fetchone():
            raise ValueError('Opt-out prevents further contact')
        if status in ('sent','uncertain','failed_no_send'):
            if current != 'prepared' or not prepared.get('message'):
                raise ValueError('A prepared message is required')
            previous = c.execute('SELECT status FROM commercial_attempts WHERE job_id=? ORDER BY id DESC LIMIT 1', (jid,)).fetchone()
            if previous and previous['status'] != 'failed_no_send':
                raise ValueError('Prior attempt prevents duplicate contact')
        elif status != 'opted_out' and current not in ('sent','submitted','replied','interested','not_interested','prepared','manual_required'):
            raise ValueError('No recorded or prepared contact to update')
        next_status = {'failed_no_send':'pending'}.get(status,status)
        c.execute('INSERT INTO commercial_attempts(job_id,channel,status,message,evidence,created_at) VALUES(?,?,?,?,?,?)',
                  (jid,prepared.get('channel','legacy'),status,prepared.get('message',''),evidence.strip(),now()))
        if status == 'failed_no_send': data.pop('commercial_contact',None)
        c.execute('UPDATE jobs SET contact_status=?,data=?,updated_at=? WHERE id=?',
                  (next_status,json.dumps(data,ensure_ascii=False),now(),jid))
        event(c,jid,'Commercial result recorded: '+status)
        return {'id':jid,'contact_status':next_status}

def serve(port):
    load_commercial_env()
    static=(ROOT/'dashboard').resolve()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def send(self,code,body,kind='application/json'):
            if not isinstance(body,bytes): body=json.dumps(body).encode()
            self.send_response(code); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store'); self.send_header('X-Robots-Tag','noindex, nofollow'); self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(body)
        def valid_host(self):
            return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
        def do_GET(self):
            if not self.valid_host(): return self.send(403,{'error':'Local host required'})
            path=urlsplit(self.path).path
            if path=='/api/sites':
                results=[]
                for manifest in sorted((ROOT/'runs/quick').glob('*/website.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:100]:
                    try:
                        item=json.loads(manifest.read_text())
                        item['preview_url']='/preview/'+item['id']+'/'
                        results.append(item)
                    except (ValueError,OSError): continue
                return self.send(200,results)
            if path=='/api/templates': return self.send(200,[{'id': k, 'name': v['name']} for k,v in TEMPLATES.items()])
            if path.startswith('/preview/'):
                parts=path.split('/')
                if len(parts)<4 or not re.fullmatch(r'[a-z0-9-]+',parts[2]): return self.send(404,{'error':'Not found'})
                site=(ROOT/'runs/quick'/parts[2]/'site').resolve()
                if not site.is_dir(): return self.send(404,{'error':'Not found'})
                target=(site/'/'.join(parts[3:])).resolve()
                if not target.is_relative_to(site): return self.send(404,{'error':'Not found'})
                if not target.is_file():
                    if target.suffix: return self.send(404,{'error':'Not found'})
                    target=site/'index.html'
                body=target.read_bytes()
                if target.name=='index.html':
                    prefix='/preview/'+parts[2]
                    page=body.decode().replace('src="/', 'src="'+prefix+'/').replace('href="/', 'href="'+prefix+'/')
                    body=page.encode()
                elif target.name=='business.js':
                    body=('window.WEBSITE_BASE = '+json.dumps('/preview/'+parts[2])+';\n').encode()+body
                return self.send(200,body,mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
            if path=='/api/state': return self.send(200,snapshot())
            files={'/':('index.html','text/html; charset=utf-8'),'/style.css':('style.css','text/css'),'/app.js':('app.js','text/javascript'),'/styles.css':('styles.css','text/css')}
            if path not in files: return self.send(404,{'error':'Not found'})
            name,kind=files[path]
            try: self.send(200,(static/name).read_bytes(),kind)
            except FileNotFoundError: self.send(404,{'error':'Dashboard asset unavailable'})
        def do_POST(self):
            origin=self.headers.get('Origin')
            if not self.valid_host() or origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
                return self.send(403,{'error':'Same-origin browser request required'})
            if self.path not in ('/api/batches','/api/sites','/api/commercial/prepare','/api/commercial/record'): return self.send(404,{'error':'Not found'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if size<1 or size>8192 or self.headers.get_content_type()!='application/json': raise ValueError('JSON body required (8 KB maximum)')
                data=json.loads(self.rfile.read(size))
                if self.path=='/api/commercial/prepare':
                    self.send(200,prepare_commercial(data.get('job_id'),data.get('observation','')))
                elif self.path=='/api/commercial/record':
                    self.send(200,record_commercial(data.get('job_id'),data.get('status'),data.get('evidence','')))
                elif self.path=='/api/sites':
                    result=create_quick_site(data)
                    result['preview_url']='/preview/'+result['id']+'/'
                    self.send(201,result)
                else: self.send(201,batch(data.get('industry'),data.get('city'),data.get('requested_count',3)))
            except (ValueError,AttributeError) as e: self.send(400,{'error':str(e)})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'Contact sheet: http://127.0.0.1:{server.server_port}',flush=True)
    server.serve_forever()

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('state')
    s=sub.add_parser('serve'); s.add_argument('--port',type=int,default=4310)
    s=sub.add_parser('batch'); s.add_argument('--industry',required=True); s.add_argument('--city',required=True); s.add_argument('--count',type=int,default=3)
    s=sub.add_parser('add'); s.add_argument('--batch',required=True); s.add_argument('--name',required=True); s.add_argument('--url',default=''); s.add_argument('--template'); s.add_argument('--alias',action='append',default=[])
    s=sub.add_parser('claim'); s.add_argument('--batch',required=True); s.add_argument('--worker',required=True)
    s=sub.add_parser('update'); s.add_argument('--job',required=True); s.add_argument('--worker',required=True); s.add_argument('--stage',choices=STAGES); s.add_argument('--detail',default=''); s.add_argument('--fields',type=Path)
    s=sub.add_parser('alias'); s.add_argument('--job',required=True); s.add_argument('--worker',required=True); s.add_argument('--identity',required=True)
    s=sub.add_parser('capacity'); s.add_argument('count',type=int,choices=range(1,6))
    s=sub.add_parser('preview-finish'); s.add_argument('--job',required=True); s.add_argument('--worker',required=True)
    s=sub.add_parser('site-input'); s.add_argument('--job',required=True); s.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('contact-begin'); s.add_argument('--job',required=True); s.add_argument('--worker',required=True); s.add_argument('--message-file',type=Path,required=True); s.add_argument('--form-url',required=True)
    s=sub.add_parser('contact-simulate'); s.add_argument('--job',required=True); s.add_argument('--worker',required=True); s.add_argument('--message-file',type=Path,required=True); s.add_argument('--form-url',required=True)
    s=sub.add_parser('resume-simulated'); s.add_argument('--job',required=True); s.add_argument('--worker',required=True)
    s=sub.add_parser('contact-finish'); s.add_argument('--job',required=True); s.add_argument('--worker',required=True); s.add_argument('--status',choices=['submitted','sent','uncertain','blocked'],required=True); s.add_argument('--evidence',required=True)
    s=sub.add_parser('manual-outreach'); s.add_argument('--job',required=True); s.add_argument('--worker',required=True); s.add_argument('--reason',required=True); s.add_argument('--message-file',type=Path,required=True); s.add_argument('--email',default=''); s.add_argument('--phone',default='')
    s=sub.add_parser('commercial-prepare'); s.add_argument('--job',required=True); s.add_argument('--observation',default='')
    s=sub.add_parser('commercial-record'); s.add_argument('--job',required=True); s.add_argument('--status',choices=['sent','uncertain','failed_no_send','replied','interested','not_interested','opted_out'],required=True); s.add_argument('--evidence',required=True)
    s=sub.add_parser('recover'); s.add_argument('--job',required=True); s.add_argument('--reason',required=True)
    s=sub.add_parser('batch-status'); s.add_argument('--batch',required=True); s.add_argument('--status',choices=['running','complete','blocked','exhausted'],required=True)
    s=sub.add_parser('cancel-batch'); s.add_argument('--batch',required=True); s.add_argument('--reason',required=True)
    s=sub.add_parser('clear-all'); s.add_argument('--reason',required=True)
    a=p.parse_args()
    try:
        if a.cmd=='serve': return serve(a.port)
        if a.cmd=='state': result=snapshot()
        elif a.cmd=='batch': result=batch(a.industry,a.city,a.count)
        elif a.cmd=='add': result=add(a.batch,a.name,a.url,a.alias,a.template)
        elif a.cmd=='claim': result=claim(a.batch,a.worker)
        elif a.cmd=='update': result=update(a.job,a.worker,a.stage,a.detail,json.loads(a.fields.read_text()) if a.fields else None)
        elif a.cmd=='preview-finish': result=preview_finish(a.job,a.worker)
        elif a.cmd=='site-input': result=site_input(a.job,a.output)
        elif a.cmd=='contact-begin': result=contact_begin(a.job,a.worker,a.message_file.read_text(),a.form_url)
        elif a.cmd=='contact-simulate': result=contact_simulate(a.job,a.worker,a.message_file.read_text(),a.form_url)
        elif a.cmd=='resume-simulated': result=resume_simulated(a.job,a.worker)
        elif a.cmd=='contact-finish': result=contact_finish(a.job,a.worker,a.status,a.evidence)
        elif a.cmd=='manual-outreach': result=manual_outreach(a.job,a.worker,a.reason,a.message_file.read_text(),a.email,a.phone)
        elif a.cmd=='commercial-prepare': result=prepare_commercial(a.job,a.observation)
        elif a.cmd=='commercial-record': result=record_commercial(a.job,a.status,a.evidence)
        elif a.cmd=='capacity':
            with connect() as c: c.execute("UPDATE config SET value=? WHERE key='max_workers'",(str(a.count),))
            result={'max_workers':a.count}
        elif a.cmd=='alias':
            with connect() as c:
                own(c,a.job,a.worker); c.execute('INSERT INTO identities VALUES(?,?)',(identity(a.identity),a.job)); event(c,a.job,'Verified identity added: '+identity(a.identity))
            result={'ok':True}
        elif a.cmd=='batch-status': result=batch_status(a.batch,a.status)
        elif a.cmd=='cancel-batch': result=cancel_batch(a.batch,a.reason)
        elif a.cmd=='clear-all': result=clear_all(a.reason)
        elif a.cmd=='recover': result=recover(a.job,a.reason)
        print(json.dumps(result,indent=2))
    except (ValueError,sqlite3.IntegrityError) as e:
        print(json.dumps({'error':str(e)}),file=sys.stderr); sys.exit(1)

if __name__=='__main__': main()
