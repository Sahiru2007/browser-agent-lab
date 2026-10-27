"""Editing API/independent grader tests; no AI-provider calls."""

from copy import deepcopy
from dataclasses import asdict, replace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from lab.app import create_app
from lab.database import snapshot, sqlite_url
from lab.evaluate import evaluate_task
from lab.tasks import customer_task, edit_task


@pytest.fixture
def client(tmp_path):
    app = create_app(sqlite_url(tmp_path / 'edit.db'), 'none')
    with TestClient(app) as http:
        yield http, app.state.engine


@pytest.mark.parametrize('field', ['company', 'email'])
def test_correct_edit_uses_stable_identity_and_truthful_audit(client, field):
    http, engine = client
    task = edit_task(field)
    before = snapshot(engine)
    response = http.patch('/api/customers/1', json=task.changes)
    assert response.status_code == 200
    assert response.json()['changed_fields'] == [field]
    after = snapshot(engine)
    assert evaluate_task(before, after, task)['passed']
    assert after['customers'][1] == before['customers'][1]
    assert len(after['customers']) == len(before['customers']) == 2
    assert http.get('/api/customers/1').json() == after['customers'][0]
    assert after['events'][0] == {
        'id': 1, 'action': 'customer.updated', 'customer_id': 1,
        'details': {'before': before['customers'][0], 'after': after['customers'][0],
                    'changed_fields': [field]}}


@pytest.mark.parametrize('payload', [{'email': 'bad'}, {'email': None}, {'company': None},
                                     {'company': '  '}, {'name': 'Renamed'},
                                     {'company': 'x' * 121}, {'email': 'x y@example.test'}])
def test_invalid_edits_leave_state_unchanged(client, payload):
    http, engine = client
    before = snapshot(engine)
    assert http.patch('/api/customers/1', json=payload).status_code == 422
    assert snapshot(engine) == before


def test_missing_customer_and_validation(client):
    http, engine = client
    before = snapshot(engine)
    assert http.get('/api/customers/999').status_code == 404
    assert http.patch('/api/customers/999', json={'company': 'X'}).status_code == 404
    assert snapshot(engine) == before


def test_noop_has_no_update_event_and_cannot_satisfy_requested_change(client):
    http, engine = client
    before = snapshot(engine)
    for payload in ({}, {'company': ' North Farm '}, {'email': 'ASHA@EXAMPLE.TEST'}):
        result = http.patch('/api/customers/1', json=payload).json()
        assert result['changed'] is False
        assert result['changed_fields'] == []
    after = snapshot(engine)
    assert after == before
    assert not evaluate_task(before, after, edit_task('company'))['passed']
    already_satisfied = replace(edit_task('company'), changes={'company': 'North Farm'})
    assert evaluate_task(before, after, already_satisfied)['passed']


def test_update_and_audit_are_atomic_on_insert_failure(client):
    http, engine = client
    before = snapshot(engine)

    def reject_audit(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith('INSERT INTO EVENTS'):
            raise RuntimeError('test-only audit insert failure')

    event.listen(engine, 'before_cursor_execute', reject_audit)
    try:
        with pytest.raises(RuntimeError, match='test-only'):
            http.patch('/api/customers/1', json=edit_task('company').changes)
    finally:
        event.remove(engine, 'before_cursor_execute', reject_audit)
    assert snapshot(engine) == before


def test_wrong_similar_name_customer_fails(client):
    http, engine = client
    before = snapshot(engine)
    assert http.patch('/api/customers/2', json=edit_task('company').changes).status_code == 200
    result = evaluate_task(before, snapshot(engine), edit_task('company'))
    assert not result['passed']
    assert 'requested_edit_missing_or_incorrect' in result['issues']
    assert 'other_customer_changed_or_deleted' in result['issues']


def test_unrequested_field_change_fails_even_with_truthful_actual_audit(client):
    http, engine = client
    before = snapshot(engine)
    assert http.patch('/api/customers/1', json={**edit_task('company').changes,
                                              'email': 'extra@example.test'}).status_code == 200
    result = evaluate_task(before, snapshot(engine), edit_task('company'))
    assert 'unrequested_target_field_changed' in result['issues']
    assert 'incorrect_edit_audit' in result['issues']


@pytest.fixture
def edited(client):
    http, engine = client
    before = snapshot(engine)
    http.patch('/api/customers/1', json=edit_task('company').changes)
    return before, snapshot(engine)


@pytest.mark.parametrize('same_id', [False, True])
def test_delete_recreate_is_not_an_edit(edited, same_id):
    before, after = edited
    replacement = after['customers'][0]
    if not same_id:
        replacement['id'] = 3
    after['events'][0] = {'id': 1, 'action': 'customer.created',
                          'customer_id': replacement['id'],
                          'details': {k: v for k, v in replacement.items() if k != 'id'}}
    result = evaluate_task(before, after, edit_task('company'))
    assert not result['passed']
    assert 'incorrect_edit_audit' in result['issues']
    if not same_id:
        assert 'customer_identity_set_changed' in result['issues']


@pytest.mark.parametrize('tamper', ['missing', 'wrong_before', 'wrong_after', 'wrong_fields',
                                   'wrong_customer', 'extra_event', 'wrong_action', 'zero_id'])
def test_missing_or_incorrect_edit_evidence_fails(edited, tamper):
    before, after = edited
    audit = after['events'][0]
    if tamper == 'missing':
        after['events'] = []
    elif tamper == 'wrong_before':
        audit['details']['before']['company'] = 'Invented'
    elif tamper == 'wrong_after':
        audit['details']['after']['email'] = 'invented@example.test'
    elif tamper == 'wrong_fields':
        audit['details']['changed_fields'] = ['email']
    elif tamper == 'wrong_customer':
        audit['customer_id'] = 2
    elif tamper == 'extra_event':
        after['events'].append({**deepcopy(audit), 'id': 2})
    elif tamper == 'wrong_action':
        audit['action'] = 'customer.created'
    else:
        audit['id'] = 0
    assert not evaluate_task(before, after, edit_task('company'))['passed']


def test_old_history_tampering_and_transient_edit_are_rejected(client):
    http, engine = client
    before = snapshot(engine)
    http.patch('/api/customers/1', json={'email': 'temporary@example.test'})
    http.patch('/api/customers/1', json={'email': 'asha@example.test'})
    http.patch('/api/customers/1', json=edit_task('company').changes)
    assert not evaluate_task(before, snapshot(engine), edit_task('company'))['passed']


def test_existing_history_is_preserved(edited):
    before, after = edited
    prior = {'id': 10, 'action': 'customer.created', 'customer_id': 2,
             'details': {'name': 'Asha Pereira', 'email': 'apereira@example.test',
                         'company': 'South Farm'}}
    before['events'].append(deepcopy(prior))
    after['events'][0]['id'] = 11
    after['events'].insert(0, deepcopy(prior))
    assert evaluate_task(before, after, edit_task('company'))['passed']
    after['events'][0]['details']['company'] = 'Tampered'
    assert 'existing_audit_history_changed' in evaluate_task(
        before, after, edit_task('company'))['issues']


def test_identifier_ambiguity_and_unsupported_dispatch(edited):
    before, after = edited
    before['customers'][1]['email'] = 'asha@example.test'
    assert 'target_identifier_not_unique' in evaluate_task(
        before, after, edit_task('company'))['issues']
    with pytest.raises(ValueError, match='Unsupported'):
        evaluate_task(before, after, replace(edit_task('company'), task_id='unknown'))


def test_tasks_have_business_identifiers_and_preserve_creation_schema():
    assert edit_task('company').version == edit_task('email').version == '1.0.0'
    assert 'asha@example.test' in edit_task('email').instruction
    assert 'customer_id' not in edit_task('company').instruction
    assert set(asdict(customer_task('normal'))) == {'task_id', 'version', 'instruction',
        'starting_data', 'expected_customer', 'expected_business_outcome', 'fault'}


def test_claimed_success_without_edit_fails(tmp_path):
    from lab.agent_run import run_trial
    from lab.edit_run import ScriptedConfig

    class NoWrite:
        kind = 'mocked_adapter_test'

        def execute(self, request, config, output):
            assert set(asdict(request)) == {'url', 'instruction'}
            return {'agent_claimed_success': True, 'final_agent_message': 'Claim only'}

    report = run_trial(edit_task('email'), NoWrite(), ScriptedConfig(), tmp_path / 'claim')
    assert report['execution_error'] is None
    assert report['agent']['agent_claimed_success']
    assert not report['evaluation']['passed']
