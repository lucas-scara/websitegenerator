#!/usr/bin/env python3
"""Durable generation and preview deployment for one claimed business.

No real deployment happens unless the explicit deploy subcommand is used.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import control
import quick_site

PROJECT = 'scarasoft-previas'
META_KEY = 'scarasoft_operation'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def job_dir(job_id):
    if not job_id.startswith('site-') or not all(c.isalnum() or c == '-' for c in job_id):
        raise ValueError('Invalid job ID')
    return control.ROOT / 'runs' / job_id


def job_record(job_id):
    with control.connect() as con:
        row = con.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
        if row is None: raise ValueError('Unknown job')
        return dict(row)


def generate(job_id, worker):
    folder = job_dir(job_id)
    input_path = folder / 'quick-site-batch.json'
    control.site_input(job_id, input_path)
    record = json.loads(input_path.read_text())[0]
    key = digest({'job_id': job_id, 'kind': 'generate', 'record': record})
    root = folder / 'generated'
    prior = control.operation_get(job_id, 'generate', key)
    existing = quick_site.find_generated(root, key)
    if prior and prior['status'] == 'complete':
        if not existing: raise ValueError('Completed generation artifact is missing; inspect before continuing')
        return existing
    if prior and prior['status'] in ('running', 'uncertain'):
        if existing:
            control.operation_finish(job_id,worker,'generate',key,artifact=str(root / existing['id'] / 'website.json'),
                                     duration_seconds=existing.get('seconds'),reconciled=True)
            return existing
        if prior['status'] == 'running':
            raise ValueError('Generation is active; recover stopped worker before retry')
        control.operation_finish(job_id,worker,'generate',key,status='failed',
                                 failure='No completed local artifact found after recovery',reconciled=True)
    control.operation_begin(job_id,worker,'generate',key,executor='quick_site.py')
    started = time.monotonic()
    try:
        result = quick_site.create(record, output_root=root, operation_key=key)
        control.operation_finish(job_id,worker,'generate',key,artifact=str(root / result['id'] / 'website.json'),
                                 duration_seconds=time.monotonic()-started)
        return result
    except Exception as exc:
        control.operation_finish(job_id,worker,'generate',key,status='failed',failure=type(exc).__name__)
        raise


def site_digest(site):
    h = hashlib.sha256()
    for path in sorted(site.rglob('*')):
        if path.is_file() and '.vercel' not in path.relative_to(site).parts:
            h.update(str(path.relative_to(site)).encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def generated_site(job_id):
    with control.connect() as con:
        row = con.execute("SELECT artifact FROM operations WHERE job_id=? AND kind='generate' AND status='complete' ORDER BY finished_at DESC LIMIT 1",(job_id,)).fetchone()
    if not row or not row['artifact']: raise ValueError('No completed tracked generation')
    manifest_path = Path(row['artifact']).resolve()
    if not manifest_path.is_relative_to((job_dir(job_id) / 'generated').resolve()):
        raise ValueError('Generation artifact is outside the job directory')
    manifest = json.loads(manifest_path.read_text())
    site = Path(manifest['site']).resolve()
    if site != manifest_path.parent / 'site' or not site.is_dir(): raise ValueError('Generated site is missing')
    return site


class VercelClient:
    def __init__(self, project_link):
        link = json.loads(Path(project_link).read_text())
        if link.get('projectName') != PROJECT or not link.get('projectId') or not link.get('orgId'):
            raise ValueError('Link this site to the approved scarasoft-previas project first')
        self.project_id = link['projectId']
        self.team_id = link['orgId']
        self.token = os.environ.get('VERCEL_TOKEN', '')
        if not self.token: raise ValueError('VERCEL_TOKEN is required for safe deployment reconciliation')
        self.settings = json.loads((control.ROOT / 'settings.json').read_text())

    def link_site(self, site):
        """Use the already linked project for this static site without changing its digest."""
        target = site / '.vercel' / 'project.json'
        if target.exists():
            current = json.loads(target.read_text())
            if current.get('projectId') != self.project_id or current.get('orgId') != self.team_id:
                raise ValueError('Generated site is linked to a different Vercel project')
            return
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps({'projectId': self.project_id, 'orgId': self.team_id,
                                      'projectName': PROJECT}))

    def request(self, path, params):
        url = 'https://api.vercel.com' + path + '?' + urlencode(params)
        request = Request(url, headers={'Authorization': 'Bearer ' + self.token})
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    def find(self, operation_key, started_at):
        since = int((dt.datetime.fromisoformat(started_at).timestamp() - 120) * 1000)
        params = {'projectId': self.project_id, 'teamId': self.team_id, 'since': since, 'limit': 100}
        matches = []
        for _ in range(10):
            result = self.request('/v6/deployments', params)
            deployments = result.get('deployments')
            if not isinstance(deployments, list): raise ValueError('Unexpected Vercel deployment response')
            matches.extend(item for item in deployments if item.get('projectId') == self.project_id
                           and item.get('meta', {}).get(META_KEY) == operation_key)
            next_page = (result.get('pagination') or {}).get('next')
            if not next_page: break
            params['until'] = next_page
        else:
            raise ValueError('Vercel deployment search was truncated; reconcile manually')
        if len(matches) > 1: raise ValueError('Multiple deployments have the same operation key; reconcile manually')
        return matches[0] if matches else None

    def deploy(self, site, operation_key):
        self.link_site(site)
        command = list(self.settings['vercel_cli']) + ['deploy', '--cwd', str(site), '--target', 'preview',
                  '--scope', self.settings['vercel_scope'], '--meta', META_KEY + '=' + operation_key]
        result = subprocess.run(command, capture_output=True, text=True, timeout=600, check=False)
        if result.returncode: raise RuntimeError('Vercel CLI failed; remote result must be reconciled')
        url = result.stdout.strip()
        if not url.startswith('https://') or '\n' in url:
            raise ValueError('Vercel CLI did not return one HTTPS deployment URL')
        return url


def reconcile_deploy(job_id, worker, key, client):
    prior = control.operation_get(job_id,'deploy',key)
    if not prior: raise ValueError('No reserved deployment operation')
    if prior['status'] == 'complete': return {'id':prior['remote_id'],'url':prior['remote_url'],'reused':True}
    found = client.find(key, prior['started_at'])
    if not found:
        raise ValueError('No matching remote deployment found; outcome remains uncertain and no redeploy is allowed')
    if found.get('target') not in (None,'preview'):
        raise ValueError('Matching deployment is not a preview')
    if found.get('readyState') != 'READY' or not found.get('uid') or not found.get('url'):
        raise ValueError('Matching deployment is not ready; recheck later without redeploying')
    url = 'https://' + found['url'].removeprefix('https://')
    control.operation_finish(job_id,worker,'deploy',key,remote_id=found['uid'],remote_url=url,reconciled=True)
    return {'id':found['uid'],'url':url,'reused':True}


def deploy(job_id, worker, client=None, approved_batch=None):
    site = generated_site(job_id)
    if client is None and approved_batch != job_record(job_id)['batch_id']:
        raise ValueError('An explicit approval for this exact batch is required before real deploy')
    client = client or VercelClient(control.ROOT / '.vercel' / 'project.json')
    key = digest({'job_id':job_id,'kind':'deploy','project':PROJECT,'site_digest':site_digest(site)})
    prior = control.operation_get(job_id,'deploy',key)
    if prior:
        return reconcile_deploy(job_id,worker,key,client)
    control.operation_begin(job_id,worker,'deploy',key,executor='vercel-cli')
    started = time.monotonic()
    try:
        url = client.deploy(site,key)
        # Persist the CLI result before querying the API. The remote metadata is
        # still the source for recovery if the process stops before this write.
        result_file = job_dir(job_id) / ('deployment-' + key + '.txt')
        with result_file.open('w') as output:
            output.write(url + '\n'); output.flush(); os.fsync(output.fileno())
        result = reconcile_deploy(job_id,worker,key,client)
        return result
    except Exception as exc:
        row = control.operation_get(job_id,'deploy',key)
        if row and row['status'] == 'running':
            control.operation_finish(job_id,worker,'deploy',key,status='uncertain',failure=type(exc).__name__,
                                     duration_seconds=time.monotonic()-started)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('generate','deploy','reconcile-deploy'):
        item = sub.add_parser(command)
        item.add_argument('--job',required=True)
        item.add_argument('--worker',required=True)
        if command == 'deploy': item.add_argument('--approved-batch',required=True)
    args = parser.parse_args()
    if args.command == 'generate': result = generate(args.job,args.worker)
    elif args.command == 'deploy': result = deploy(args.job,args.worker,approved_batch=args.approved_batch)
    else:
        site = generated_site(args.job)
        client = VercelClient(control.ROOT / '.vercel' / 'project.json')
        key = digest({'job_id':args.job,'kind':'deploy','project':PROJECT,'site_digest':site_digest(site)})
        result = reconcile_deploy(args.job,args.worker,key,client)
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
