import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select

from lab.database import customers, events, faults, initialize, make_engine

ROOT = Path(__file__).resolve().parents[1]
FAULT_MODES = {"none", "lost_confirmation"}


class CustomerInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    company: str = Field(min_length=1, max_length=120)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if value.count("@") != 1 or any(c.isspace() for c in value):
            raise ValueError("Enter a valid email address")
        local, domain = value.split("@")
        if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("Enter a valid email address")
        return value.lower()


def create_app(database_url: str | None = None, fault_mode: str | None = None) -> FastAPI:
    mode = fault_mode or os.environ.get("LAB_FAULT", "none")
    if mode not in FAULT_MODES:
        raise ValueError(f"Unknown fault mode: {mode}")
    engine = make_engine(database_url or os.environ.get("DATABASE_URL", "sqlite:///lab.db"))

    @asynccontextmanager
    async def lifespan(app):
        initialize(engine)
        yield
        engine.dispose()

    app = FastAPI(
        title="Fieldwork CRM", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None
    )
    app.state.engine = engine

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/customers")
    def list_customers(q: str = Query(default="", max_length=254)):
        with engine.connect() as conn:
            # Literal contains search; '%' and '_' in user input are not wildcards.
            condition = customers.c.name.icontains(
                q, autoescape=True
            ) | customers.c.email.icontains(q, autoescape=True)
            return [
                dict(row)
                for row in conn.execute(
                    select(customers).where(condition).order_by(customers.c.id)
                ).mappings()
            ]

    @app.post("/api/customers", status_code=201)
    async def create_customer(payload: CustomerInput):
        values = payload.model_dump()
        with engine.begin() as conn:
            result = conn.execute(customers.insert().values(**values))
            customer_id = result.inserted_primary_key[0]
            conn.execute(
                events.insert().values(
                    action="customer.created", customer_id=customer_id, details=values
                )
            )
            should_delay = (
                mode == "lost_confirmation"
                and conn.execute(select(faults.c.id).limit(1)).first() is None
            )
            if should_delay:
                conn.execute(
                    faults.insert().values(kind="lost_confirmation", customer_id=customer_id)
                )
        # The transaction has COMMITTED. The UI cancels its request after 700 ms,
        # so the successful response cannot be delivered to that browser request.
        # A fresh GET can still discover the committed record.
        if should_delay:
            await asyncio.sleep(2)
        return {"id": customer_id, **values}

    dist = ROOT / "frontend" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app
