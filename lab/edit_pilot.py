"""Six fixed unguarded local editing trials; no retry or paid dispatch path."""
import argparse
import hashlib
import html
import json
import random
import shutil
import zipfile
from dataclasses import asdict, replace
from importlib.metadata import distribution, version
from pathlib import Path
from urllib.parse import urlsplit

from lab.adapters import OllamaConfig, select_adapter
from lab.agent_run import run_trial
from lab.agent_worker import BROWSER_ACTIONS
from lab.app import ROOT
from lab.benchmark import atomic_json, provenance
from lab.database import make_engine, snapshot, sqlite_url
from lab.evaluate import evaluate_task
from lab.local_compare import accounting, digest, termination
from lab.ollama_model import local_preflight
from lab.tasks import edit_task

SEEDS = (101, 202, 303)


def pilot_task(field, seed):
    if seed not in SEEDS:
        raise ValueError("Unsupported pilot seed")
    task = edit_task(field)
    email = f"asha-{seed}@example.test"
    rows = [dict(r) for r in task.starting_data]
    rows[0].update(email=email, company=f"North Farm {seed}")
    rows[1].update(email=f"apereira-{seed}@example.test", company=f"South Farm {seed}")
    # Vary position while keeping both tasks matched within each data seed.
    if random.Random(seed).getrandbits(1):
        rows[0]['id'], rows[1]['id'] = rows[1]['id'], rows[0]['id']
    rows.sort(key=lambda r: r['id'])
    value = (f"Evergreen Cooperative {seed}" if field == 'company'
             else f"asha.perera-{seed}@example.test")
    instruction = task.instruction.replace(task.identifier_email, email).replace(
        task.changes[field], value)
    return replace(task, instruction=instruction, identifier_email=email,
                   starting_data=tuple(rows), changes={field: value})


def hashes():
    files = list((ROOT / 'lab').glob('*.py')) + list((ROOT / 'frontend/src').glob('*'))
    files += [ROOT / 'uv.lock', ROOT / 'frontend/package-lock.json']
    sdk = Path(distribution('browser-use').locate_file('browser_use/agent'))
    files += [sdk / 'service.py', sdk / 'views.py', *sdk.rglob('*.md')]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}


def prepare():
    config = OllamaConfig()
    runtime = local_preflight(config)
    assert version('browser-use') == '0.13.11'
    slots = []
    for seed in SEEDS:
        fields = ['company', 'email']
        random.Random(seed).shuffle(fields)
        for field in fields:
            task = pilot_task(field, seed)
            slots.append({'trial_id': f'{len(slots)+1:02d}_{field}_{seed}', 'field': field,
                          'seed': seed, 'task': asdict(task), 'task_sha256': digest(asdict(task))})
    common = {'limits': asdict(config), 'tools': sorted(BROWSER_ACTIONS),
              'general_operating_instructions': '', 'recovery_guard': None,
              'runtime': runtime, 'sdk_version': version('browser-use'),
              'model_options': {'think': False, 'temperature': 0, 'seed': 42,
                                'keep_alive': '5m', 'num_ctx': 16384, 'num_predict': 2048},
              'source_hashes': hashes()}
    old = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in (ROOT / 'runs').rglob('*') if p.is_file()}
    return {'kind': 'exploratory_real_local_editing_pilot', 'version': '1.0.0',
            'planned_trials': 6, 'seeds': list(SEEDS), 'schedule': slots,
            'common': common, 'configuration_sha256': digest(common),
            'historical_hashes': old, 'provenance': provenance(),
            'cache_conditions': 'Shared long-lived Ollama/model/prefix cache; no flush or timing '
                                'isolation. Fresh DB/server/browser/context per attempt.',
            'ordering': 'Seeds 101,202,303; per-seed task order shuffled with that seed; '
                        'one attempt per task/seed. No replacement.'}


def cleanup_check(raw, folder):
    import psutil
    evidence = folder / 'browser-evidence'
    if not zipfile.is_zipfile(evidence / 'trace.zip'):
        raise RuntimeError('MissingBrowserTrace')
    history = json.loads((evidence / 'browser-history.json').read_text())
    ports = {urlsplit(h.get('state', {}).get('url', '')).port for h in history['history']
             if h.get('state', {}).get('url', '').startswith('http://127.0.0.1:')}
    listeners = [c for c in psutil.net_connections(kind='tcp')
                 if c.status == 'LISTEN' and c.laddr.port in ports]
    workers = [p.pid for p in psutil.process_iter(['name', 'cmdline'])
               if (p.info['name'] or '').lower() in {'python.exe', 'python'}
               and 'lab.agent_worker' in (p.info['cmdline'] or [])]
    browsers = [p.pid for p in psutil.process_iter(['name', 'cmdline'])
                if (p.info['name'] or '').lower() in {'chrome.exe', 'headless_shell.exe'}
                and any(v.startswith('--user-data-dir=') and 'browser-agent-lab-local-' in v
                        for v in p.info['cmdline'] or [])]
    if listeners or workers or browsers:
        raise RuntimeError('RemainingTrialResources')
    return {'crm_listeners': listeners, 'workers': workers, 'browsers': browsers}


def audit_trial(raw, task, folder):
    engine = make_engine(sqlite_url(folder / 'trial.db'))
    try:
        current = snapshot(engine)
    finally:
        engine.dispose()
    grade = evaluate_task(raw['before'], current, task)
    if current != raw['after'] or grade != raw['evaluation']:
        raise RuntimeError('SavedDatabaseRegradeMismatch')
    before = raw['before']
    after = current
    target = next(r for r in before['customers'] if r['email'] == task.identifier_email)
    actual = next((r for r in after['customers'] if r['id'] == target['id']), None)
    old_events = {e['id'] for e in before['events']}
    events = [e for e in after['events'] if e['id'] not in old_events]
    touched = sorted({e['customer_id'] for e in events})
    return {'regrade': grade, 'saved_database_regrade_matches': True,
            'correct_customer_write_target': touched == [target['id']],
            'write_targets': touched, 'requested_edit_committed': actual is not None and all(
                actual.get(k) == v for k, v in task.changes.items()),
            'unrequested_fields_preserved': actual is not None and all(
                actual.get(k) == v for k, v in target.items() if k not in task.changes),
            'other_records_preserved': all(r in after['customers'] for r in before['customers']
                                           if r['id'] != target['id']),
            'identity_set_preserved': {r['id'] for r in before['customers']} == {
                r['id'] for r in after['customers']},
            'audit_correct': not any('audit' in issue for issue in grade['issues']),
            'selection_measurement': 'Committed write targets from independent audit; '
                                     'browser selection actions retained separately in trace.'}


def analyze(output):
    manifest = json.loads((output / 'manifest.json').read_text())
    rows = []
    for spec in manifest['schedule']:
        p = output / spec['trial_id'] / 'pilot-result.json'
        rows.append(json.loads(p.read_text()) if p.exists() else {**spec, 'state': 'not_started'})
    atomic_json(output / 'summary.json', {'kind': manifest['kind'], 'trials': rows})
    body = []
    for row in rows:
        evidence = row['trial_id'] + '/result.json'
        body.append('<tr><td>' + html.escape(row['trial_id']) + '</td><td><pre>'
                    + html.escape(json.dumps({k: v for k, v in row.items() if k != 'task'},
                                            indent=2)) + '</pre></td><td><a href="'
                    + evidence + '">Raw trial</a> <a href="' + row['trial_id']
                    + '/browser-evidence/browser-history.json">Browser history</a> '
                    + '<a href="' + row['trial_id']
                    + '/browser-evidence/trace.zip">Trace</a></td></tr>')
    (output / 'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
        '<title>Local editing pilot</title><h1>Exploratory local editing pilot</h1>'
        '<p>Six authorized attempts, no replacements. Unguarded baseline; no injected failures. '
        'Shared model/cache, no timing isolation; not evidence of reliability. Provider API '
        'charges $0; hardware/electricity unmeasured. Raw evidence and operator DB regrades '
        'are distinct from agent claims. Only completed rows count as observations.</p>'
        '<p><a href="manifest.json">Frozen configuration, tasks, hashes, ordering</a> '
        '<a href="state.json">Execution state</a> <a href="summary.json">Summary</a></p>'
        '<table><tr><th>Attempt</th><th>Outcome/accounting</th><th>Evidence</th></tr>'
        + ''.join(body) + '</table></html>', encoding='utf-8')
    return rows


def run(output):
    manifest = prepare()  # preflight performs no inference
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / 'manifest.json', manifest)
    frozen = output / 'frozen-source'
    frozen.mkdir()
    for i, source in enumerate(manifest['common']['source_hashes']):
        shutil.copyfile(source, frozen / (f'{i:03d}_' + Path(source).name))
    state = {'state': 'running', 'started': [], 'stop_reason': None}
    try:
        for spec in manifest['schedule']:
            if hashes() != manifest['common']['source_hashes']:
                raise RuntimeError('FrozenSourceChanged')
            task = pilot_task(spec['field'], spec['seed'])
            if digest(asdict(task)) != spec['task_sha256']:
                raise RuntimeError('FrozenTaskChanged')
            state['started'].append(spec['trial_id'])
            atomic_json(output / 'state.json', state)
            folder = output / spec['trial_id']
            print('START', spec['trial_id'], flush=True)
            raw = run_trial(task, select_adapter('ollama'), OllamaConfig(), folder)
            row = {**spec, 'state': 'completed', 'execution_error': raw['execution_error'],
                   'evaluation': raw['evaluation'], 'duration_seconds': raw['duration_seconds'],
                   'driver_duration_seconds': raw.get('driver_duration_seconds'),
                   'metrics': accounting(raw, OllamaConfig()),
                   'termination': termination(raw, OllamaConfig()),
                   'agent_success_claim': (raw['agent'] or {}).get('agent_claimed_success'),
                   'final_agent_message': (raw['agent'] or {}).get('final_agent_message'),
                   'task_failure': (raw['agent'] or {}).get('task_failure')}
            atomic_json(folder / 'pilot-result.json', row)
            try:
                row['database_audit'] = audit_trial(raw, task, folder)
                row['cleanup'] = cleanup_check(raw, folder)
                if (raw['limits'] != manifest['common']['limits']
                        or (raw['agent'] or {}).get('local_runtime', {}).get('model_digest')
                        != manifest['common']['runtime']['model_digest']):
                    raise RuntimeError('FrozenSettingsMismatch')
                if raw['execution_error'] or row['metrics']['status'] != 'measured':
                    raise RuntimeError('InfrastructureOrAccountingProblem')
            except Exception as exc:
                row['pilot_error'] = type(exc).__name__ + ':' + str(exc)
                state.update(state='stopped', stop_reason=row['pilot_error'])
            atomic_json(folder / 'pilot-result.json', row)
            atomic_json(output / 'state.json', state)
            analyze(output)
            print('END', spec['trial_id'], row['evaluation'], row['metrics'], flush=True)
            if state['state'] == 'stopped':
                break
        else:
            state['state'] = 'finished'
    except BaseException as exc:
        state.update(state='stopped', stop_reason=type(exc).__name__)
    finally:
        atomic_json(output / 'state.json', state)
        analyze(output)
        changed = [p for p, sha in manifest['historical_hashes'].items()
                   if not (ROOT / p).is_file()
                   or hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != sha]
        atomic_json(output / 'preservation.json', {
            'files_checked': len(manifest['historical_hashes']), 'changed': changed})
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--execute', type=Path,
                       help='New output directory for six authorized trials')
    group.add_argument('--analyze', type=Path, help='Rebuild offline report without inference')
    args = parser.parse_args()
    if args.analyze:
        analyze(args.analyze)
        return 0
    state = run(args.execute)
    return 0 if state['state'] == 'finished' else 2


if __name__ == '__main__':
    raise SystemExit(main())
