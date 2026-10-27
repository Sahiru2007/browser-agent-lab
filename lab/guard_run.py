"""Four-slot experimental guarded local check; offline report rebuilding is model-free."""

import argparse
import hashlib
import html
import json
from dataclasses import asdict, replace
from pathlib import Path

from lab.adapters import GuardConfig, select_adapter
from lab.agent_run import framework_version, run_trial
from lab.app import ROOT
from lab.benchmark import atomic_json, provenance
from lab.local_compare import accounting, digest, original_hashes, seed_data, termination
from lab.tasks import benchmark_task


def retained_hashes():
    values = original_hashes()
    prior = ROOT / 'runs/local_recovery_comparison_20261027'
    values.update({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in prior.rglob('*') if p.is_file()})
    return values


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'lab/recovery_guard.py', 'lab/guard_run.py', 'lab/adapters.py', 'lab/agent_worker.py',
        'lab/ollama_model.py', 'lab/agent_run.py', 'lab/evaluate.py', 'docs/RECOVERY_GUARD.md')}


def analyze(output):
    manifest = json.loads((output / 'manifest.json').read_text())
    state = json.loads((output / 'state.json').read_text())
    records = [json.loads((output / s['trial_id'] / 'guard-result.json').read_text())
               for s in manifest['schedule']]
    for record in records:
        log = output / record['trial_id'] / 'evidence/browser-evidence/guard-events.jsonl'
        events = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        record['interventions'] = {
            'blocked_write_requests': sum(e['decision'].startswith('write_blocked') or
                                         e['decision'] == 'repeat_write_blocked' for e in events),
            'unresolved_done_interceptions': sum(e['decision'] == 'agent_done_blocked'
                                                for e in events),
            'positive_success_claims_overridden': sum(e['decision'] == 'agent_done_blocked'
                and e.get('proposed_success') is True for e in events),
            'visible_reconciliations': sum(e['decision'] == 'visible_record_reconciled'
                                          for e in events),
        }
    summary = {'kind': manifest['kind'], 'state': state,
               'trials': records, 'counts': {
                   'started': sum(r['state'] != 'not_started' for r in records),
                   'business_pass': sum(bool((r.get('evaluation') or {}).get('passed'))
                                        for r in records),
                   'duplicates': sum('duplicate_customer' in (r.get('evaluation') or {}).get(
                       'issues', []) for r in records),
                   'unresolved': sum(r.get('guard', {}).get('unresolved') is True for r in records),
                   'guard_blocked_writes': sum(r.get('guard', {}).get('blocked_writes', 0)
                                               for r in records),
                   'unresolved_done_interceptions': sum(r['interventions'][
                       'unresolved_done_interceptions'] for r in records),
                   'positive_success_claims_overridden': sum(r['interventions'][
                       'positive_success_claims_overridden'] for r in records)},
               'note': 'Exploratory guard-only check, two matched seeds. No reliability or '
               'isolated timing claim. Shared Ollama prefix cache. Independent business grades '
               'and guard '
               'resolution are separate; duplicate prevention is not automatic completion.',
               'provider_api_charges_usd': 0, 'electricity_hardware_cost': 'unmeasured'}
    atomic_json(output / 'summary.json', summary)

    def esc(value):
        return html.escape(str(value), quote=True)

    rows = []
    for r in records:
        path = r['trial_id'] + '/'
        links = f"<a href='{path}guard-result.json'>record</a>"
        if r['state'] == 'completed':
            links += (f" <a href='{path}evidence/result.json'>independent grade/usage</a>"
                      f" <a href='{path}evidence/browser-evidence/guard-events.jsonl'>guard log</a>"
                      f" <a href='{path}evidence/browser-evidence/browser-history.json'>actions</a>"
                      f" <a href='{path}evidence/browser-evidence/trace.zip'>trace</a>")
        cells = [r['trial_id'], r['scenario'], r['seed'], r['state'], r.get('evaluation'),
                 r.get('guard'), r.get('interventions'), r.get('termination'), r.get('metrics'),
                 r.get('duration_seconds')]
        rows.append('<tr>' + ''.join('<td>' + esc(c) + '</td>' for c in cells)
                    + '<td>' + links + '</td></tr>')
    page = ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; "
            "style-src 'unsafe-inline'\"><title>Experimental recovery guard</title>"
            "<style>body{font:14px system-ui;margin:2rem}table{border-collapse:collapse}"
            "td,th{padding:.5rem;border:1px solid #bbb;vertical-align:top}"
            "pre{white-space:pre-wrap}</style><h1>Experimental guarded local trials</h1>"
            f"<p>Kind: {esc(summary['kind'])}</p><p>{esc(summary['note'])}</p>"
            f"<pre>{esc(summary['counts'])}</pre>"
            f"<p>{esc(state)}</p><p>Provider API charges $0; hardware/electricity unmeasured.</p>"
            "<p><a href='manifest.json'>Frozen configuration, rule, hashes and order</a> | "
            "<a href='summary.json'>Summary JSON</a></p><table><tr>"
            "<th>Trial</th><th>Condition</th><th>Seed</th><th>State</th><th>Business grade</th>"
            "<th>Guard state</th><th>Interventions from event log</th>"
            "<th>Termination</th><th>Calls/tokens</th>"
            "<th>Wall seconds</th><th>Evidence</th></tr>" + ''.join(rows) + '</table></html>')
    (output / 'report.html').write_text(page, encoding='utf-8')
    return summary


def run(output):
    if framework_version() != '0.13.11':
        raise ValueError('Pinned SDK required; no dependency upgrade allowed')
    from lab.ollama_model import local_preflight

    config = GuardConfig()
    runtime = local_preflight(config)
    schedule = [{'trial_id': f'trial-{i + 1:04d}', 'scenario': scenario, 'seed': seed}
                for i, (seed, scenario) in enumerate((seed, scenario)
                    for seed in (101, 202) for scenario in ('normal', 'lost-confirmation'))]
    frozen = {'limits': asdict(config), 'instruction': benchmark_task(
        'normal', 'basic-browser-use').instruction, 'source_hashes': source_hashes(),
        'local_runtime': runtime}
    manifest = {'kind': 'experimental_guard_real_local_agent_trials', 'version': '1.0.0',
                'configuration': frozen, 'config_sha256': digest(frozen),
                'schedule': schedule, 'prior_evidence': retained_hashes(),
                'provenance': provenance(), 'rule': (ROOT / 'docs/RECOVERY_GUARD.md').read_text(),
                'cache_conditions': 'Shared long-lived local Ollama; no prefix-cache reset.'}
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / 'manifest.json', manifest)
    state = {'state': 'running', 'started': [], 'stop_reason': None}
    atomic_json(output / 'state.json', state)
    for spec in schedule:
        (output / spec['trial_id']).mkdir()
        atomic_json(output / spec['trial_id'] / 'guard-result.json',
                    {**spec, 'state': 'not_started'})
    try:
        for spec in schedule:
            if retained_hashes() != manifest['prior_evidence'] or source_hashes() != (
                    frozen['source_hashes']):
                state.update(state='stopped', stop_reason='FrozenSourceOrEvidenceChanged')
                break
            record = {**spec, 'state': 'running'}
            folder = output / spec['trial_id']
            atomic_json(folder / 'guard-result.json', record)
            state['started'].append(spec['trial_id'])
            atomic_json(output / 'state.json', state)
            print('START', spec, flush=True)
            try:
                task = replace(benchmark_task(spec['scenario'], 'basic-browser-use'),
                               starting_data=tuple(seed_data(spec['seed'])))
                raw = run_trial(task, select_adapter('ollama-guard'), config, folder / 'evidence')
                guard = (raw.get('agent') or {}).get('recovery_guard') or {}
                metrics = accounting(raw, config)
                term = termination(raw, config)
                term['effective_reason'] = ('guard_unresolved' if guard.get('unresolved') else
                                            term['reported_reason'])
                record.update(state='completed', evaluation=raw['evaluation'], guard=guard,
                              metrics=metrics, termination=term,
                              execution_error=raw.get('execution_error'),
                              duration_seconds=raw['duration_seconds'])
                if raw.get('execution_error') or metrics['status'] != 'measured' or not guard:
                    state.update(state='stopped', stop_reason='InfrastructureOrAccountingProblem')
            except KeyboardInterrupt:
                record.update(state='interrupted', execution_error='infrastructure:Interrupted')
                state.update(state='stopped', stop_reason='Interrupted')
            except Exception as exc:
                record.update(state='failed',
                              execution_error=f'infrastructure:{type(exc).__name__}')
                state.update(state='stopped', stop_reason='InfrastructureProblem')
            atomic_json(folder / 'guard-result.json', record)
            atomic_json(output / 'state.json', state)
            analyze(output)
            print('END', record, flush=True)
            if state['state'] == 'stopped':
                break
        else:
            state['state'] = 'finished'
    finally:
        state['prior_evidence_unchanged'] = retained_hashes() == manifest['prior_evidence']
        atomic_json(output / 'state.json', state)
        summary = analyze(output)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--analyze', type=Path)
    args = parser.parse_args()
    if args.analyze:
        analyze(args.analyze)
        return 0
    if not args.output:
        parser.error('Provide a new output directory for exactly four guarded local trials')
    result = run(args.output)
    print('Report:', args.output / 'report.html')
    return 0 if result['state']['state'] == 'finished' else 2


if __name__ == '__main__':
    raise SystemExit(main())
