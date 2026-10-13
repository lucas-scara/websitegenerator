#!/usr/bin/env python3
"""Run a bounded read-only Codex role with explicit routing and verify the session metadata."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ROLES = {'discovery': ('gpt-6-luna','low'),
         'verification': ('gpt-6-luna','low'),
         'qualification': ('gpt-6-luna','medium'),
         'quality_review': ('gpt-6-sol','medium')}


def route(role, effort=None, reason=''):
    if role not in ROLES: raise ValueError('Unknown Codex role')
    path = ROOT / '.codex' / 'agents' / (role.replace('_','-') + '.toml')
    source = path.read_text()
    values = {}
    for name in ('model','model_reasoning_effort'):
        found = re.search(r'^' + name + r'\s*=\s*"([a-z0-9-]+)"\s*$',source,re.M)
        if not found: raise ValueError('Role routing is missing ' + name)
        values[name] = found.group(1)
    configured = (values['model'],values['model_reasoning_effort'])
    if configured != ROLES[role]: raise ValueError('Role TOML disagrees with approved routing')
    selected = effort or configured[1]
    if selected != configured[1] and not (role == 'quality_review' and selected == 'high' and reason.strip()):
        raise ValueError('Non-default effort needs a justified quality review exception')
    return configured[0], selected


def observed_route(thread_id, codex_home=None):
    home = Path(codex_home or os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    paths = list((home / 'sessions').glob('**/*' + thread_id + '*.jsonl'))
    if len(paths) != 1: raise ValueError('Cannot identify one Codex rollout for route verification')
    contexts = []
    for line in paths[0].open():
        try: item = json.loads(line)
        except json.JSONDecodeError: continue
        if item.get('type') == 'turn_context':
            contexts.append(item.get('payload', {}))
    if not contexts: raise ValueError('Codex rollout has no turn context')
    latest = contexts[-1]
    return latest.get('model'), latest.get('effort')


def execute(role, prompt, *, effort=None, reason='', job=None, worker=None,
            run=subprocess.run, observe=observed_route, record=None):
    if bool(job) != bool(worker): raise ValueError('Job and worker must be supplied together')
    model, selected = route(role,effort,reason)
    command = ['codex','exec','--strict-config','--json','--sandbox','read-only',
               '-C',str(ROOT),'-m',model,'-c','model_reasoning_effort="' + selected + '"','-']
    result = run(command,input=prompt,text=True,capture_output=True,check=False)
    if result.returncode: raise RuntimeError('Codex role execution failed; inspect the private session')
    thread_id = None
    answer = None
    usage = None
    for line in result.stdout.splitlines():
        try: item = json.loads(line)
        except json.JSONDecodeError: continue
        if item.get('type') == 'thread.started': thread_id = item.get('thread_id')
        if item.get('type') == 'item.completed' and (item.get('item') or {}).get('type') == 'agent_message':
            answer = item['item'].get('text')
        if item.get('type') == 'turn.completed': usage = item.get('usage')
    if not thread_id: raise ValueError('Codex did not return a thread ID for route verification')
    actual = observe(thread_id)
    if actual != (model,selected):
        raise ValueError('Actual Codex model/effort differs from the approved route')
    if job:
        if record is None:
            from control import record_agent_execution
            record = record_agent_execution
        record(job,worker,thread_id,actual[0],actual[1],usage)
    return {'thread_id':thread_id,'model':actual[0],'effort':actual[1],
            'usage':usage if isinstance(usage,dict) else None,'answer':answer}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('role',choices=ROLES)
    parser.add_argument('--prompt-file',type=Path,required=True)
    parser.add_argument('--effort',choices=['low','medium','high'])
    parser.add_argument('--reason',default='')
    parser.add_argument('--job',help='Attach verified route to an active job stage')
    parser.add_argument('--worker',help='Current owner of --job')
    args = parser.parse_args()
    prompt = args.prompt_file.read_text()
    print(json.dumps(execute(args.role,prompt,effort=args.effort,reason=args.reason,
                             job=args.job,worker=args.worker),ensure_ascii=False))


if __name__ == '__main__': main()
