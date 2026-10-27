"""Frozen four-trial local feedback ablation; no historical-trial substitution."""

import argparse
import hashlib
import html
import json
import subprocess
import zipfile
from dataclasses import asdict, replace
from pathlib import Path
from urllib.parse import urlsplit

from lab.adapters import GuardConfig, GuardFeedbackConfig, select_adapter
from lab.agent_run import framework_version, run_trial
from lab.agent_worker import BROWSER_ACTIONS
from lab.app import ROOT
from lab.benchmark import atomic_json, make_manifest, provenance
from lab.benchmark_metrics import valid_evaluation
from lab.guard_feedback import CLARIFICATION
from lab.guard_run import retained_hashes
from lab.local_compare import accounting, digest, seed_data, termination
from lab.ollama_model import local_preflight
from lab.recovery_guard import RecoveryGuard
from lab.tasks import benchmark_task

BASE = 'aeba563'
SOURCES = ('lab/feedback_run.py', 'lab/guard_feedback.py', 'lab/adapters.py',
           'lab/agent_worker.py', 'lab/agent_run.py', 'lab/ollama_model.py',
           'lab/recovery_guard.py', 'lab/evaluate.py', 'lab/tasks.py', 'lab/database.py',
           'lab/local_compare.py', 'lab/guard_run.py', 'lab/benchmark.py',
           'lab/benchmark_metrics.py')


def sources():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def preserved():
    result = retained_hashes()
    for name in ('recovery_guard_20261027', 'guard_diagnosis_20261027'):
        result.update({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (ROOT / 'runs' / name).rglob('*') if p.is_file()})
    return result


def base_feedback():
    # Compare the unchanged guard and grader to the approved commit, allowing only
    # Git/Windows line-ending normalization. No model call or DB read occurs here.
    for name in ('lab/recovery_guard.py', 'lab/evaluate.py'):
        baseline = subprocess.check_output(['git', 'show', f'{BASE}:{name}'], cwd=ROOT).decode()
        if (ROOT / name).read_text() != baseline.replace('\r\n', '\n'):
            raise ValueError('Guard/grader differs from aeba563; experiment cannot dispatch')
    guard = RecoveryGuard('http://127.0.0.1:1', None, Path('unused'))
    guard.state = 'unknown'
    return guard.message()


def prepare(output):
    if framework_version() != '0.13.11':
        raise ValueError('Pinned SDK required')
    feedback = base_feedback()
    runtime = local_preflight(GuardConfig())
    common = {'base_commit': BASE, 'model_runtime': runtime, 'guard_limits': asdict(GuardConfig()),
              'tools': sorted(BROWSER_ACTIONS), 'task_instruction': benchmark_task(
                  'lost-confirmation', 'basic-browser-use').instruction,
              'model_options': {'think': False, 'temperature': 0, 'seed': 42,
                                'num_ctx': 16384, 'num_predict': 2048, 'keep_alive': '5m'},
              'source_hashes': sources(), 'framework_version': framework_version()}
    variants = {}
    for variant in ('A', 'B'):
        value = {'settings': asdict(GuardFeedbackConfig(feedback_variant=variant)),
                 'uncertain_feedback': feedback + ('\n' + CLARIFICATION if variant == 'B' else ''),
                 'common': common}
        variants[variant] = {**value, 'sha256': digest(value)}
    slots = make_manifest(scenarios=('lost-confirmation',), trials=2, seed=4)['schedule']
    schedule = [{'trial_id': r['trial_id'],
                 'variant': 'A' if r['strategy'] == 'blind-retry' else 'B',
                 'seed': (101, 202)[r['repetition'] - 1], 'scenario': 'lost-confirmation'}
                for r in slots]
    assert [s['variant'] for s in schedule[::2]] == ['B', 'A']
    manifest = {'kind': 'real_local_feedback_ablation', 'version': '1.0.0',
                'variants': variants, 'common': common, 'schedule': schedule,
                'ordering_seed': 4, 'preserved_evidence': preserved(), 'provenance': provenance(),
                'clarification': CLARIFICATION,
                'cache_conditions': 'Shared Ollama prefix cache, no flush. Routing disables '
                'browser HTTP cache in both arms. Fresh isolated state per trial. '
                'No timing isolation or deterministic-model claim.',
                'scope': 'User-authorized lost-only ablation replaces earlier proposed normal/lost '
                'design; no normal or historical result substitutes for any of these four slots.'}
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / 'manifest.json', manifest)
    atomic_json(output / 'state.json', {'state': 'planned', 'started': [], 'stop_reason': None,
                                      'manifest_sha256': digest(manifest)})
    for spec in schedule:
        (output / spec['trial_id']).mkdir()
        atomic_json(output / spec['trial_id'] / 'ablation.json', {**spec, 'state': 'not_started'})
    capsule = output / 'frozen-source'
    for name in SOURCES:
        target = capsule / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    analyze(output)
    return manifest


def inspect_trial(folder, raw):
    evidence = folder / 'evidence/browser-evidence'
    events = [json.loads(line) for line in
              (evidence / 'guard-events.jsonl').read_text().splitlines()]
    feedback_path = evidence / 'feedback-events.jsonl'
    feedback = [json.loads(line) for line in feedback_path.read_text().splitlines()] if (
        feedback_path.exists()) else []
    with zipfile.ZipFile(evidence / 'trace.zip') as trace:
        if trace.testzip() is not None:
            raise RuntimeError('Invalid trace')
        network = [json.loads(line)['snapshot'] for line in trace.read('trace.network').decode(
            ).splitlines()]
    posts = [r for r in network if r['request']['method'] == 'POST']
    first = min((r['startedDateTime'] for r in posts), default=None)
    reads = [r for r in network if first and r['startedDateTime'] > first
             and r['request']['method'] == 'GET'
             and urlsplit(r['request']['url']).path == '/api/customers']
    visible = [e['visible_record'] for e in events if e['decision'] == 'visible_record_reconciled']
    guard = raw['agent']['recovery_guard']
    history = json.loads((evidence / 'browser-history.json').read_text())
    port = urlsplit(history['history'][0]['state']['url']).port
    import psutil

    if any(c.status == 'LISTEN' and c.laddr.port == port for c in psutil.net_connections('tcp')):
        raise RuntimeError('CRM listener remains')
    if any('lab.agent_worker' in (p.info['cmdline'] or [])
           for p in psutil.process_iter(['cmdline'])):
        raise RuntimeError('Agent worker remains')
    if any(p.info['name'].lower() in {'chrome.exe', 'headless_shell.exe'}
           and any(a.startswith('--user-data-dir=') and 'browser-agent-lab-local-' in a
                   for a in p.info['cmdline'] or [])
           for p in psutil.process_iter(['name', 'cmdline'])):
        raise RuntimeError('Trial browser remains')
    return {'mechanism': {
                'fresh_application_read_attempts': len(reads),
                'fresh_read_results': [{'url': r['request']['url'],
                    'status': r['response']['status'],
                    'duration_ms': r['time']} for r in reads],
                'guard_fresh_read_observations': sum(e['decision'] == 'post_write_read_observed'
                                                     for e in events),
                'matching_record_visible': (any(v == raw['task']['expected_customer']
                    for v in visible) if visible else None),
                'submitted_record_visible': bool(visible),
                'visible_evidence': visible,
                'visibility_status': 'observed_by_DOM' if visible else 'not_established',
                'reconciliation_succeeded': guard['state'] == 'confirmed_visible'},
            'interventions': {
                'blocked_write_requests': guard['blocked_writes'],
                'unresolved_done_interceptions': sum(e['decision'] == 'agent_done_blocked'
                                                    for e in events),
                'positive_claims_overridden': sum(e['decision'] == 'agent_done_blocked'
                    and e.get('proposed_success') is True for e in events)},
            'proposed_completion_claims': [e['action']['done'] for e in events
                if e['decision'] == 'agent_action' and 'done' in e.get('action', {})],
            'feedback_events': feedback,
            'post_results': [{'status': r['response']['status'], 'duration_ms': r['time']}
                             for r in posts], 'crm_port': port}


def execute(output):
    manifest = json.loads((output / 'manifest.json').read_text())
    state = json.loads((output / 'state.json').read_text())
    if state['state'] != 'planned':
        raise ValueError('No resume/retry: this experiment has already started')
    state['state'] = 'running'
    atomic_json(output / 'state.json', state)
    try:
        for spec in manifest['schedule']:
            if (sources() != manifest['common']['source_hashes'] or preserved() != (
                    manifest['preserved_evidence'])
                    or digest(json.loads((output / 'manifest.json').read_text()))
                    != state['manifest_sha256']):
                state.update(state='stopped', stop_reason='FrozenSourceOrEvidenceChanged')
                break
            base_feedback()
            folder = output / spec['trial_id']
            record = {**spec, 'state': 'running'}
            atomic_json(folder / 'ablation.json', record)
            state['started'].append(spec['trial_id'])
            atomic_json(output / 'state.json', state)
            print('START', spec, flush=True)
            try:
                frozen = manifest['variants'][spec['variant']]
                config = GuardFeedbackConfig(**frozen['settings'])
                task = replace(benchmark_task('lost-confirmation', 'basic-browser-use'),
                               instruction=manifest['common']['task_instruction'],
                               starting_data=tuple(seed_data(spec['seed'])))
                raw = run_trial(task, select_adapter('ollama-guard'), config, folder / 'evidence')
                record.update(state='completed', evaluation=raw['evaluation'],
                    execution_error=raw.get('execution_error'), metrics=accounting(raw, config),
                    duration_seconds=raw['duration_seconds'], termination=termination(raw, config),
                    guard=(raw.get('agent') or {}).get('recovery_guard'),
                    final_agent_message=(raw.get('agent') or {}).get('final_agent_message'),
                    agent_completion_success=(raw.get('agent') or {}).get('agent_claimed_success'))
                if (raw.get('execution_error') or not valid_evaluation(raw)
                        or record['metrics']['status'] != 'measured' or not record['guard']):
                    state.update(state='stopped', stop_reason='InfrastructureOrAccountingProblem')
                else:
                    record.update(inspect_trial(folder, raw))
                    if any(e['feedback'] != frozen['uncertain_feedback'] for e in (
                            record['feedback_events'])):
                        raise RuntimeError('Feedback text differs from frozen manifest')
                    if raw['limits'] != frozen['settings'] or raw['agent']['local_runtime'][
                            'model_digest'] != manifest['common']['model_runtime']['model_digest']:
                        raise RuntimeError('Frozen settings mismatch')
                record['workflow'] = ('unresolved' if (record['guard'] or {}).get('unresolved') else
                    'confirmed' if (record['guard'] or {}).get('state') == 'confirmed_visible'
                    and raw['evaluation']['passed'] and record['agent_completion_success']
                    and not record['execution_error'] else 'failed')
            except KeyboardInterrupt:
                record.update(state='interrupted', execution_error='infrastructure:Interrupted')
                state.update(state='stopped', stop_reason='Interrupted')
            except Exception as exc:
                record.update(state='failed',
                              execution_error=f'infrastructure:{type(exc).__name__}')
                state.update(state='stopped', stop_reason='InfrastructureProblem')
            atomic_json(folder / 'ablation.json', record)
            atomic_json(output / 'state.json', state)
            analyze(output)
            print('END', {k: record.get(k) for k in ['trial_id', 'variant', 'seed', 'workflow',
                'mechanism', 'evaluation', 'metrics', 'execution_error']}, flush=True)
            if state['state'] == 'stopped':
                break
        else:
            state['state'] = 'finished'
    finally:
        state['prior_evidence_unchanged'] = preserved() == manifest['preserved_evidence']
        atomic_json(output / 'state.json', state)
        result = analyze(output)
    return result


def analyze(output):
    manifest = json.loads((output / 'manifest.json').read_text())
    state = json.loads((output / 'state.json').read_text())
    records = [json.loads((output / s['trial_id'] / 'ablation.json').read_text())
               for s in manifest['schedule']]
    summary = {'kind': manifest['kind'], 'state': state, 'trials': records,
               'cache_conditions': manifest['cache_conditions'],
               'note': 'Four new local trials, two seeds, lost condition only. Fresh GET alone is '
               'not visible-record reconciliation. No deterministic behavior, causal reliability '
               'or isolated timing claim. Prior trials are excluded.',
               'provider_api_charges_usd': 0, 'electricity_hardware_cost': 'unmeasured'}
    atomic_json(output / 'summary.json', summary)

    def esc(value):
        return html.escape(str(value), quote=True)

    rows = []
    for r in records:
        links = f"<a href='{r['trial_id']}/ablation.json'>trial</a>"
        if r['state'] == 'completed' and 'mechanism' in r:
            base = r['trial_id'] + '/evidence/'
            links += (f" <a href='{base}result.json'>DB grade/claims/usage</a>"
                      f" <a href='{base}browser-evidence/trace.zip'>trace</a>"
                      f" <a href='{base}browser-evidence/browser-history.json'>actions</a>"
                      f" <a href='{base}browser-evidence/guard-events.jsonl'>guard events</a>")
        cells = [r['trial_id'], r['variant'], r['seed'], r['state'], r.get('workflow'),
                 r.get('mechanism'), r.get('evaluation'), r.get('interventions'),
                 r.get('proposed_completion_claims'), r.get('termination'), r.get('metrics'),
                 r.get('duration_seconds')]
        rows.append('<tr>' + ''.join('<td>' + esc(v) + '</td>' for v in cells)
                    + '<td>' + links + '</td></tr>')
    feedback = {k: {'sha256': v['sha256'], 'feedback': v['uncertain_feedback']}
                for k, v in manifest['variants'].items()}
    page = ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; "
            "style-src 'unsafe-inline'\"><title>Local feedback ablation</title>"
            "<style>body{font:14px system-ui;margin:2rem}td,th{border:1px solid #aaa;"
            "padding:.5rem;vertical-align:top}table{border-collapse:collapse}"
            "pre{white-space:pre-wrap}</style><h1>Local feedback ablation</h1>"
            f"<p>{esc(summary['kind'])}; {esc(state)}</p><p>{esc(summary['note'])}</p>"
            f"<p>{esc(summary['cache_conditions'])}</p><p>Provider API charges $0; energy/hardware "
            "unmeasured.</p><p><a href='manifest.json'>Frozen manifest</a> | "
            "<a href='summary.json'>Summary</a></p><h2>Exact feedback and hashes</h2>"
            f"<pre>{esc(json.dumps(feedback, indent=2))}</pre><h2>Trial evidence</h2><table><tr>"
            '<th>Trial</th><th>Variant</th><th>Seed</th><th>State</th><th>Workflow</th>'
            '<th>Reads/visible details/reconciliation</th><th>Independent grade</th>'
            '<th>Interventions</th><th>Claims</th><th>Termination</th><th>Calls/tokens</th>'
            '<th>Seconds</th><th>Evidence</th></tr>' + ''.join(rows) + '</table></html>')
    (output / 'report.html').write_text(page, encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--execute', type=Path)
    parser.add_argument('--analyze', type=Path)
    args = parser.parse_args()
    if sum(bool(v) for v in (args.prepare, args.execute, args.analyze)) != 1:
        parser.error('Choose exactly one prepare/execute/analyze operation')
    if args.prepare:
        manifest = prepare(args.prepare)
        print('Frozen hashes:', {k: v['sha256'] for k, v in manifest['variants'].items()})
        return 0
    if args.analyze:
        analyze(args.analyze)
        return 0
    result = execute(args.execute)
    print('Report:', args.execute / 'report.html')
    return 0 if result['state']['state'] == 'finished' else 2


if __name__ == '__main__':
    raise SystemExit(main())
