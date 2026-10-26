from pathlib import Path

from sqlalchemy import JSON, Column, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.engine import Engine

metadata = MetaData()
customers = Table(
    "customers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(120), nullable=False),
    Column("email", String(254), nullable=False),
    Column("company", String(120), nullable=False),
)
events = Table(
    "events",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("action", String(40), nullable=False),
    Column("customer_id", Integer, nullable=False),
    Column("details", JSON, nullable=False),
)
faults = Table(
    "faults",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("kind", String(40), nullable=False),
    Column("customer_id", Integer, nullable=False),
)

SEED_CUSTOMERS = [
    {"id": 1, "name": "Asha Perera", "email": "asha@example.test", "company": "North Farm"},
    {"id": 2, "name": "Asha Pereira", "email": "apereira@example.test", "company": "South Farm"},
]


def make_engine(url: str) -> Engine:
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    return create_engine(url, **kwargs)


def initialize(engine: Engine) -> None:
    metadata.create_all(engine)
    with engine.begin() as conn:
        if conn.execute(select(customers.c.id).limit(1)).first() is None:
            conn.execute(customers.insert(), SEED_CUSTOMERS)


def snapshot(engine: Engine) -> dict:
    """Operator-only state access; never exposed as an application endpoint."""
    with engine.connect() as conn:
        return {
            table.name: [
                dict(row) for row in conn.execute(select(table).order_by(table.c.id)).mappings()
            ]
            for table in [customers, events, faults]
        }


def sqlite_url(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()
