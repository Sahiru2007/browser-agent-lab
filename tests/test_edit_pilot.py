import copy
import json
from dataclasses import asdict

import pytest
from fastapi.testclient import TestClient

from lab.app import create_app
from lab.database import customers, make_engine, metadata, snapshot, sqlite_url
from lab.edit_pilot import analyze, audit_trial, pilot_task
from lab.evaluate import evaluate_task


def test_matched_seeds_and_business_only_instructions():
    for seed in (101, 202, 303):
        company, email = (pilot_task(field, seed) for field in ('company', 'email'))
        assert company.starting_data == email.starting_data
        assert company.fault == email.fault == 'none'
        assert company.version == email.version == '1.0.0'
        assert company.identifier_email in company.instruction
        assert company.identifier_email in email.instruction
        assert all(word not in company.instruction.lower() for word in
                   ('database', 'assertion', 'customer_id', 'seed', 'fault'))
        assert len({r['name'] for r in company.starting_data}) == 2
    assert pilot_task('email', 101) != pilot_task('email', 202)
    with pytest.raises(ValueError):
        pilot_task('email', 404)


@pytest.mark.parametrize('field', ['company', 'email'])
def test_saved_database_audit_and_claim_independence(tmp_path, field):
    task = pilot_task(field, 202)
    engine = make_engine(sqlite_url(tmp_path / 'trial.db'))
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(customers.insert(), list(task.starting_data))
    before = snapshot(engine)
    raw = {'before': before, 'after': before, 'evaluation': evaluate_task(before, before, task),
           'agent': {'agent_claimed_success': True}}
    audit = audit_trial(raw, task, tmp_path)
    assert not audit['regrade']['passed']
    assert not audit['requested_edit_committed']
    target = next(r for r in before['customers'] if r['email'] == task.identifier_email)
    with TestClient(create_app(sqlite_url(tmp_path / 'trial.db'))) as client:
        response = client.patch('/api/customers/' + str(target['id']), json=task.changes)
        assert response.status_code == 200
    raw['after'] = snapshot(engine)
    raw['evaluation'] = evaluate_task(before, raw['after'], task)
    audit = audit_trial(raw, task, tmp_path)
    assert audit['regrade']['passed'] and audit['audit_correct']
    assert audit['correct_customer_write_target'] and audit['other_records_preserved']
    altered = copy.deepcopy(raw)
    altered['evaluation']['passed'] = False
    with pytest.raises(RuntimeError, match='RegradeMismatch'):
        audit_trial(altered, task, tmp_path)
    engine.dispose()


def test_report_retains_unstarted_slots_without_calls(tmp_path):
    spec = {'trial_id': 'company_101', 'task': asdict(pilot_task('company', 101))}
    (tmp_path / 'manifest.json').write_text(json.dumps({'kind': 'mocked_adapter_test',
                                                      'schedule': [spec]}))
    rows = analyze(tmp_path)
    assert rows[0]['state'] == 'not_started'
    text = (tmp_path / 'report.html').read_text()
    assert 'not_started' in text and 'Provider API' in text
    assert '<script' not in text and 'https://' not in text


@pytest.mark.parametrize('field', ['company', 'email'])
def test_real_runner_cli_dispatch_without_inference(monkeypatch, field):
    import sys

    from lab import agent_run
    observed = []
    monkeypatch.setattr(sys, 'argv', ['agent_run', '--adapter', 'ollama', '--task', field])
    monkeypatch.setattr(agent_run, 'framework_version', lambda: '0.13.11')
    monkeypatch.setattr(agent_run, 'select_adapter', lambda name: object())
    def mocked_run(task, adapter, config, output):
        observed.append(task)
        return {'trial_status': 'business_pass', 'execution_error': None,
                'evaluation': {'passed': True}}
    monkeypatch.setattr(agent_run, 'run_trial', mocked_run)
    assert agent_run.main() == 0
    assert observed[0].task_id == 'customer.change_' + field
    assert observed[0].version == '1.0.0' and observed[0].fault == 'none'


def test_edit_cli_rejects_fault_before_dispatch(monkeypatch):
    import sys

    from lab import agent_run
    monkeypatch.setattr(sys, 'argv', ['agent_run', '--adapter', 'ollama', '--task',
                                     'company', '--scenario', 'lost-confirmation'])
    monkeypatch.setattr(agent_run, 'select_adapter', lambda name: pytest.fail('dispatch'))
    with pytest.raises(SystemExit) as exc:
        agent_run.main()
    assert exc.value.code == 2
