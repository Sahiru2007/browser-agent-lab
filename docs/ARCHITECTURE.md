# Architecture

The synthetic FastAPI/SQLite CRM exposes browser-visible customer search,
creation and details/editing. React renders the interface. Operator-owned task
objects supply initial state and expected effects to the runner, not to agents.
Every trial starts its own server/database; browser adapters create fresh contexts.
Only the CRM URL and ordinary instruction cross the AgentRequest boundary.

## Editing

GET /api/customers/{id} loads details. PATCH on the same resource accepts only
company and/or email; names and extra fields are rejected. Validation trims fields,
normalizes email case and rejects empty values, invalid email and excessive length.
IDs in internal API navigation are not task identifiers. Users select records by
visible email; similarly named seeded customers make selection consequential.

A single transaction updates the existing row and appends customer.updated with
full before/after rows and sorted changed_fields. Audit insertion failure rolls
back the update. Creation's customer.created payload and transaction are unchanged.
A normalized no-op returns changed=false and creates no audit event.

The operator's evaluate_task dispatches creation to the original checker and edits
to a separate snapshot-only checker. Edit grading resolves the target from its
original email, requires stable identity, requested values, all unrequested fields
and other records unchanged, no creation/deletion, unchanged prior audit history,
and exactly one truthful update event for a nontrivial edit. Additional edits,
even reverted ones, fail the single-edit audit contract. A requested value already
present is satisfied by unchanged state with no new event; merely saving unchanged
state cannot satisfy a task requesting a different value. Agent claims never grade.

lab.edit_run is a distinct scripted-browser control suite, not AI evidence. It
searches, opens details, saves, performs a no-op, reopens and checks visible values.
The operator independently reopens and regrades each saved database afterward.

## Scope

No authentication, new faults, concurrency conflict handling, uniqueness rule,
application idempotency or edit-specific recovery policy was added. The experimental
write guard remains creation-specific: edits are not a supported guarded workflow.
Existing frozen recovery configurations/evidence are preserved. No live editing
agent trial has been executed. Snapshot/audit grading assumes the tested agent
cannot directly forge database history; the existing browser-only boundary remains.
