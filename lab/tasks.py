"""Operator-owned, versioned task definitions. Never pass this object to an agent."""

from dataclasses import dataclass, replace

from lab.database import SEED_CUSTOMERS

CUSTOMER = {"name": "Nimal Silva", "email": "nimal@example.test", "company": "Evergreen Farms"}


@dataclass(frozen=True)
class Task:
    task_id: str
    version: str
    instruction: str
    starting_data: tuple[dict, ...]
    expected_customer: dict
    expected_business_outcome: dict
    fault: str


def customer_task(scenario: str) -> Task:
    faults = {"normal": "none", "lost-confirmation": "lost_confirmation"}
    if scenario not in faults:
        raise ValueError("Unknown task scenario")
    return Task(
        task_id="customer.create_once",
        version="1.0.0",
        instruction=(
            "Create a customer named Nimal Silva, email nimal@example.test, "
            "company Evergreen Farms. Create this customer exactly once. "
            "Use the CRM to check whether the customer already exists before retrying "
            "if a submission cannot be confirmed."
        ),
        starting_data=tuple(dict(row) for row in SEED_CUSTOMERS),
        expected_customer=dict(CUSTOMER),
        expected_business_outcome={
            "matching_customers_created": 1, "new_creation_events": 1,
            "preserve_existing_customers_and_audit": True,
        },
        fault=faults[scenario],
    )


def benchmark_task(scenario: str, strategy: str) -> Task:
    """Neutral shared business task; recovery guidance is a versioned policy."""
    task = customer_task(scenario)
    instruction = (
        "Create a customer named Nimal Silva, email nimal@example.test, "
        "company Evergreen Farms. Create this customer exactly once."
    )
    if strategy == "verification-browser-use":
        instruction += (
            " If a submission cannot be confirmed, search the CRM and inspect "
            "the matching customer before deciding whether to retry."
        )
    return replace(task, version="1.1.0", instruction=instruction)
