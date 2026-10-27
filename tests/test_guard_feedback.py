"""Mocked feedback-presentation tests; never invoke a real provider."""

import asyncio
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from lab.adapters import GuardConfig, GuardFeedbackConfig
from lab.guard_feedback import CLARIFICATION, feedback_tools


@pytest.mark.parametrize('variant', ['A', 'B'])
@pytest.mark.parametrize('state', ['idle', 'unknown', 'confirmed_visible'])
def test_feedback_only_changes_unknown_text(tmp_path, variant, state):
    config = asdict(GuardFeedbackConfig(feedback_variant=variant))
    assert config.pop('feedback_variant') == variant
    assert config == asdict(GuardConfig())
    base = 'Original exact feedback'
    guard = SimpleNamespace(state=state, message=lambda: base)
    result = SimpleNamespace(extracted_content=base, is_done=False, success=None)

    async def original(*args, **kwargs):
        return result

    tools = feedback_tools(SimpleNamespace(act=original), guard, variant, tmp_path / 'log')
    returned = asyncio.run(tools.act(None, None))
    assert returned is result
    assert result.extracted_content == base + (
        '\n' + CLARIFICATION if state == 'unknown' and variant == 'B' else '')
    assert (tmp_path / 'log').exists() == (state == 'unknown')


def test_terminal_feedback_is_unchanged(tmp_path):
    guard = SimpleNamespace(state='unknown', message=lambda: 'Original UNKNOWN feedback')
    result = SimpleNamespace(extracted_content='UNRESOLVED terminal result', is_done=True)

    async def original(*args, **kwargs):
        return result

    tools = feedback_tools(SimpleNamespace(act=original), guard, 'B', tmp_path / 'log')
    assert asyncio.run(tools.act(None, None)).extracted_content == 'UNRESOLVED terminal result'
    assert not (tmp_path / 'log').exists()


def test_feedback_variant_validation():
    with pytest.raises(ValueError):
        GuardFeedbackConfig(feedback_variant='other')


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    import lab.feedback_run as module

    monkeypatch.setattr(module, 'framework_version', lambda: '0.13.11')
    monkeypatch.setattr(module, 'base_feedback', lambda: 'Exact A feedback')
    monkeypatch.setattr(module, 'local_preflight', lambda config: {'model_digest': 'mocked'})
    monkeypatch.setattr(module, 'sources', lambda: {'source': 'frozen'})
    monkeypatch.setattr(module, 'preserved', lambda: {'prior': 'unchanged'})
    monkeypatch.setattr(module, 'provenance', lambda: {'kind': 'mocked_adapter_test'})
    monkeypatch.setattr(module, 'SOURCES', ())
    output = tmp_path / 'ablation'
    manifest = module.prepare(output)
    # All synthetic test reports are explicitly labeled, never real-agent outcomes.
    from lab.benchmark import atomic_json
    from lab.local_compare import digest
    manifest['kind'] = 'mocked_adapter_test'
    atomic_json(output / 'manifest.json', manifest)
    atomic_json(output / 'state.json', {'state': 'planned', 'started': [], 'stop_reason': None,
                                      'manifest_sha256': digest(manifest)})
    return module, output, manifest


def test_frozen_pairing_and_feedback(prepared):
    module, output, manifest = prepared
    assert [(s['variant'], s['seed']) for s in manifest['schedule']] == [
        ('B', 101), ('A', 101), ('A', 202), ('B', 202)]
    a, b = manifest['variants']['A'], manifest['variants']['B']
    assert a['common'] == b['common']
    assert a['uncertain_feedback'] == 'Exact A feedback'
    assert b['uncertain_feedback'] == 'Exact A feedback\n' + CLARIFICATION
    assert a['sha256'] != b['sha256']
    summary = module.analyze(output)
    assert all(t['state'] == 'not_started' for t in summary['trials'])
    assert 'mocked_adapter_test' in (output / 'report.html').read_text()


def test_infrastructure_failure_stops_without_replacement(prepared, monkeypatch):
    module, output, _ = prepared
    calls = []

    def broken(*args):
        calls.append(1)
        raise RuntimeError('Do not persist raw error')

    monkeypatch.setattr(module, 'run_trial', broken)
    result = module.execute(output)
    assert len(calls) == 1
    assert result['state']['state'] == 'stopped'
    assert sum(t['state'] == 'not_started' for t in result['trials']) == 3
    with pytest.raises(ValueError, match='No resume'):
        module.execute(output)
    assert 'Do not persist raw error' not in (output / 'summary.json').read_text()


def test_changed_source_stops_before_dispatch(prepared, monkeypatch):
    module, output, _ = prepared
    monkeypatch.setattr(module, 'sources', lambda: {'source': 'changed'})
    result = module.execute(output)
    assert not result['state']['started']
    assert result['state']['stop_reason'] == 'FrozenSourceOrEvidenceChanged'


def test_fresh_get_does_not_imply_visible_reconciliation(tmp_path, monkeypatch):
    import json
    import sys
    import zipfile
    from types import SimpleNamespace

    from lab.feedback_run import inspect_trial

    # Process checks are mocked; the base test suite must not require the agent extra.
    monkeypatch.setitem(sys.modules, 'psutil', SimpleNamespace(
        net_connections=lambda *args, **kwargs: [],
        process_iter=lambda *args, **kwargs: []))
    evidence = tmp_path / 'evidence/browser-evidence'
    evidence.mkdir(parents=True)
    (evidence / 'guard-events.jsonl').write_text(json.dumps({
        'decision': 'post_write_read_observed'}) + '\n')
    (evidence / 'browser-history.json').write_text(json.dumps({
        'history': [{'state': {'url': 'http://127.0.0.1:1234'}}]}))
    rows = [{'snapshot': {'startedDateTime': time, 'time': 1,
                         'request': {'method': method, 'url': 'http://127.0.0.1:1234/api/customers'},
                         'response': {'status': status}}}
            for time, method, status in [('2026-01-01T00:00:00Z', 'POST', -1),
                                        ('2026-01-01T00:00:01Z', 'GET', 200)]]
    with zipfile.ZipFile(evidence / 'trace.zip', 'w') as archive:
        archive.writestr('trace.network', '\n'.join(json.dumps(r) for r in rows))
    result = inspect_trial(tmp_path, {'agent': {'recovery_guard': {
        'state': 'unknown', 'blocked_writes': 0}}, 'task': {'expected_customer': {}}})
    assert result['mechanism']['fresh_application_read_attempts'] == 1
    assert result['mechanism']['matching_record_visible'] is None
    assert result['mechanism']['reconciliation_succeeded'] is False
