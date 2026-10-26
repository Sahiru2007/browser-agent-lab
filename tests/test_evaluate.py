from copy import deepcopy

import pytest

from lab.database import SEED_CUSTOMERS
from lab.evaluate import evaluate

EXPECTED = {"name": "Nimal Silva", "email": "nimal@example.test", "company": "Evergreen Farms"}


@pytest.fixture
def states():
    before = {"customers": deepcopy(SEED_CUSTOMERS), "events": [], "faults": []}
    after = deepcopy(before)
    after["customers"].append({"id": 3, **EXPECTED})
    after["events"].append(
        {"id": 1, "action": "customer.created", "customer_id": 3, "details": deepcopy(EXPECTED)}
    )
    return before, after


def test_correct_creation_passes(states):
    before, after = states
    assert evaluate(before, after, EXPECTED)["passed"]


def test_no_creation_fails(states):
    before, _ = states
    assert "missing_or_incorrect_customer" in evaluate(before, before, EXPECTED)["issues"]


def test_duplicate_creation_fails(states):
    before, after = states
    after["customers"].append({"id": 4, **EXPECTED})
    after["events"].append(
        {"id": 2, "action": "customer.created", "customer_id": 4, "details": deepcopy(EXPECTED)}
    )
    assert "duplicate_customer" in evaluate(before, after, EXPECTED)["issues"]


@pytest.mark.parametrize("change", ["edit", "delete"])
def test_old_record_tampering_fails(states, change):
    before, after = states
    if change == "edit":
        after["customers"][0]["company"] = "Incorrect company"
    else:
        after["customers"].pop(0)
    assert "existing_customer_changed_or_deleted" in evaluate(before, after, EXPECTED)["issues"]


def test_wrong_fields_fail(states):
    before, after = states
    after["customers"][-1]["email"] = "wrong@example.test"
    assert not evaluate(before, after, EXPECTED)["passed"]


def test_extra_customer_fails(states):
    before, after = states
    after["customers"].append({"id": 4, "name": "Other", "email": "x@example.test", "company": "X"})
    assert "unexpected_customer_created" in evaluate(before, after, EXPECTED)["issues"]


def test_missing_audit_event_fails(states):
    before, after = states
    after["events"] = []
    assert "unexpected_audit_history" in evaluate(before, after, EXPECTED)["issues"]


def test_duplicate_audit_event_fails(states):
    before, after = states
    after["events"].append({**after["events"][0], "id": 2})
    assert "unexpected_audit_history" in evaluate(before, after, EXPECTED)["issues"]


def test_old_audit_history_cannot_be_removed(states):
    before, after = states
    old_event = {
        "id": 20,
        "action": "customer.created",
        "customer_id": 1,
        "details": {"name": "Asha Perera"},
    }
    before["events"].append(old_event)
    assert "existing_audit_history_changed" in evaluate(before, after, EXPECTED)["issues"]
