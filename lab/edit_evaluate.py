"""Independent edit grading from committed snapshots; no application/driver helpers."""


def evaluate_edit(before, after, identifier_email, changes):
    if not changes or not set(changes) <= {"company", "email"}:
        raise ValueError("Edit expectations require supported fields")
    originals = before["customers"]
    current = after["customers"]
    old = {r["id"]: r for r in originals}
    new = {r["id"]: r for r in current}
    issues = []
    created = set(new) - set(old)
    deleted = set(old) - set(new)
    if created or deleted or len(current) != len(originals):
        issues.append("customer_identity_set_changed")
    if len(old) != len(originals) or len(new) != len(current):
        issues.append("duplicate_customer_identity")
    candidates = [r for r in originals if r["email"] == identifier_email]
    old_events = {e["id"]: e for e in before["events"]}
    after_events = {e["id"]: e for e in after["events"]}
    additions = [e for e in after["events"] if e["id"] not in old_events]
    if (len(after_events) != len(after["events"])
            or len(old_events) != len(before["events"])
            or any(after_events.get(key) != value for key, value in old_events.items())):
        issues.append("existing_audit_history_changed")
    if before["faults"] != after["faults"]:
        issues.append("unexpected_fault_history_change")
    if len(candidates) != 1:
        issues.append("target_identifier_not_unique")
        return {"passed": False, "issues": issues, "total_customers_created": len(created),
                "total_customers_deleted": len(deleted), "new_audit_events": len(additions)}
    target = candidates[0]
    identity = target["id"]
    actual = new.get(identity)
    expected = {**target, **changes}
    changed_fields = sorted(key for key in changes if target[key] != changes[key])
    if actual is None or any(actual.get(key) != value for key, value in changes.items()):
        issues.append("requested_edit_missing_or_incorrect")
    if actual is None or (set(actual) != set(target) or any(
            actual.get(key) != value for key, value in target.items() if key not in changes)):
        issues.append("unrequested_target_field_changed")
    if any(new.get(key) != value for key, value in old.items() if key != identity):
        issues.append("other_customer_changed_or_deleted")
    # One real edit must produce one truthful event; a no-op produces no event.
    if changed_fields:
        accurate = [e for e in additions if e["action"] == "customer.updated"
                    and e["customer_id"] == identity
                    and e["details"] == {"before": target, "after": expected,
                                         "changed_fields": changed_fields}]
        if len(additions) != 1 or len(accurate) != 1:
            issues.append("incorrect_edit_audit")
    elif additions:
        issues.append("unexpected_noop_audit")
    if any(e["id"] <= max(old_events, default=0) for e in additions):
        issues.append("audit_not_appended")
    return {"passed": not issues, "issues": issues, "target_customer_id": identity,
            "expected_changed_fields": changed_fields, "total_customers_created": len(created),
            "total_customers_deleted": len(deleted), "new_audit_events": len(additions)}
