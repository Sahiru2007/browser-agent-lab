from fastapi.testclient import TestClient

from lab.app import create_app
from lab.database import snapshot, sqlite_url
from lab.evaluate import evaluate

CUSTOMER = {"name": "Nimal Silva", "email": "nimal@example.test", "company": "Evergreen Farms"}


def test_create_commits_customer_and_audit_together(tmp_path):
    app = create_app(sqlite_url(tmp_path / "test.db"), "none")
    with TestClient(app) as client:
        before = snapshot(app.state.engine)
        response = client.post("/api/customers", json=CUSTOMER)
        assert response.status_code == 201
        assert evaluate(before, snapshot(app.state.engine), CUSTOMER)["passed"]
        assert len(client.get("/api/customers", params={"q": CUSTOMER["email"]}).json()) == 1


def test_invalid_customer_does_not_change_state(tmp_path):
    app = create_app(sqlite_url(tmp_path / "test.db"), "none")
    with TestClient(app) as client:
        before = snapshot(app.state.engine)
        assert client.post("/api/customers", json={**CUSTOMER, "name": "  "}).status_code == 422
        assert snapshot(app.state.engine) == before


def test_control_endpoints_are_not_exposed(tmp_path):
    app = create_app(sqlite_url(tmp_path / "test.db"), "none")
    with TestClient(app) as client:
        for path in ["/api/reset", "/api/faults", "/api/evaluate", "/openapi.json"]:
            assert client.post(path).status_code in {404, 405}
