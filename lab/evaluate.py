from collections import Counter


def evaluate(before: dict, after: dict, expected: dict) -> dict:
    """Grade committed business effects, independently of browser messages."""
    before_by_id = {r["id"]: r for r in before["customers"]}
    after_by_id = {r["id"]: r for r in after["customers"]}
    new_records = [r for r in after["customers"] if r["id"] not in before_by_id]
    matches = [r for r in new_records if all(r.get(k) == v for k, v in expected.items())]
    old_event_ids = {r["id"] for r in before["events"]}
    new_events = [r for r in after["events"] if r["id"] not in old_event_ids]
    matching_ids = {r["id"] for r in matches}
    matching_events = [
        e
        for e in new_events
        if e["action"] == "customer.created"
        and e["customer_id"] in matching_ids
        and e["details"] == expected
    ]
    issues = []
    if len(matches) == 0:
        issues.append("missing_or_incorrect_customer")
    if len(matches) > 1:
        issues.append("duplicate_customer")
    if len(new_records) != len(matches):
        issues.append("unexpected_customer_created")
    if any(after_by_id.get(key) != value for key, value in before_by_id.items()):
        issues.append("existing_customer_changed_or_deleted")
    expected_event_counts = Counter(r["id"] for r in matches)
    actual_event_counts = Counter(e["customer_id"] for e in matching_events)
    if actual_event_counts != expected_event_counts or len(new_events) != len(matches):
        issues.append("unexpected_audit_history")
    # Audit evidence must remain present and unchanged, including old events.
    after_event_by_id = {r["id"]: r for r in after["events"]}
    if any(after_event_by_id.get(e["id"]) != e for e in before["events"]):
        issues.append("existing_audit_history_changed")
    return {
        "passed": not issues,
        "issues": issues,
        "matching_customers_created": len(matches),
        "total_customers_created": len(new_records),
        "new_audit_events": len(new_events),
    }



def evaluate_task(before, after, task):
    """Operator-owned task dispatch; legacy creation evaluation stays unchanged."""
    if task.task_id == "customer.create_once":
        return evaluate(before, after, task.expected_customer)
    if (getattr(task, "task_type", None) == "customer.edit"
            and task.task_id in {"customer.change_company", "customer.change_email"}):
        from lab.edit_evaluate import evaluate_edit
        return evaluate_edit(before, after, task.identifier_email, task.changes)
    raise ValueError("Unsupported task type")
