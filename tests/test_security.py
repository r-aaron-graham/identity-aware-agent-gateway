"""Identity boundary tests: the gateway must fail closed."""

import base64
import json

import pytest
from fastapi.testclient import TestClient

import app.routes as routes
from app.auth import mint_token, verify_token
from app.main import app
from scripts.seed import main as seed_main

seed_main()
client = TestClient(app)


def bearer(role: str, user_id: str | None = None) -> dict[str, str]:
    token = mint_token(user_id or f"{role}_id", f"{role.title()} User", role)
    return {"Authorization": f"Bearer {token}"}


def query(headers: dict[str, str], prompt: str, **extra: str):
    return client.post("/api/v1/agent/query", headers=headers, json={"prompt": prompt, **extra})


def test_health_is_public():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Basic dXNlcjpwYXNz"},
        {"Authorization": "Bearer not-a-jwt"},
        {"Authorization": "Bearer a.b.c"},
    ],
)
def test_missing_or_malformed_tokens_are_rejected(headers):
    assert client.get("/api/v1/whoami", headers=headers).status_code == 401


def test_tampered_role_claim_is_rejected():
    header, payload, sig = mint_token("u1", "Viewer", "viewer").split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["role"] = "admin"
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    res = client.get("/api/v1/whoami", headers={"Authorization": f"Bearer {header}.{forged}.{sig}"})
    assert res.status_code == 401


def test_expired_token_is_rejected():
    token = mint_token("u1", "Old", "admin", ttl_seconds=-10)
    with pytest.raises(Exception) as info:
        verify_token(token)
    assert getattr(info.value, "status_code", None) == 401
    assert client.get("/api/v1/whoami", headers={"Authorization": f"Bearer {token}"}).status_code == 401


@pytest.mark.parametrize("path", ["/api/v1/reviews", "/api/v1/metrics"])
@pytest.mark.parametrize("role", ["viewer", "analyst", "architect"])
def test_review_endpoints_require_reviewer_or_admin(path, role):
    assert client.get(path, headers=bearer(role)).status_code == 403


def test_users_cannot_read_each_others_traces():
    owner = bearer("analyst", user_id="owner-1")
    trace_id = query(owner, "Summarize the oncall incident runbook", sensitivity="medium").json()[
        "trace_id"
    ]
    assert client.get(f"/api/v1/traces/{trace_id}", headers=owner).status_code == 200
    stranger = bearer("analyst", user_id="stranger-2")
    assert client.get(f"/api/v1/traces/{trace_id}", headers=stranger).status_code == 403
    assert client.get(f"/api/v1/traces/{trace_id}", headers=bearer("reviewer")).status_code == 200


def test_unknown_trace_is_404():
    assert client.get("/api/v1/traces/does-not-exist", headers=bearer("admin")).status_code == 404


def test_viewer_cannot_reach_restricted_data():
    body = query(bearer("viewer"), "Explain the architecture exception standard").json()
    assert body["outcome"] == "review_required"
    assert all(src["classification"] == "public" for src in body["sources"])


def test_unknown_role_falls_back_to_least_privilege():
    body = query(bearer("superuser"), "Show me the payroll margin report").json()
    assert body["outcome"] == "review_required"


def test_invalid_sensitivity_is_rejected_before_policy():
    res = query(bearer("admin"), "Summarize the onboarding checklist", sensitivity="extreme")
    assert res.status_code == 422


def test_review_cannot_be_resolved_twice():
    query(
        bearer("analyst"),
        "Export the quarterly finance data",
        requested_tool="finance_export",
        sensitivity="medium",
    )
    reviewer = bearer("reviewer")
    open_items = [r for r in client.get("/api/v1/reviews", headers=reviewer).json() if r["status"] == "open"]
    review_id = open_items[0]["id"]
    body = {"resolution": "rejected", "note": "no"}
    first = client.post(f"/api/v1/reviews/{review_id}/resolve", headers=reviewer, json=body)
    second = client.post(f"/api/v1/reviews/{review_id}/resolve", headers=reviewer, json=body)
    assert first.status_code == 200
    assert second.status_code == 409
    missing = client.post("/api/v1/reviews/999999/resolve", headers=reviewer, json=body)
    assert missing.status_code == 404


def test_demo_tokens_can_be_disabled(monkeypatch):
    assert client.get("/api/v1/auth/demo-tokens").status_code == 200
    monkeypatch.setattr(routes, "ENABLE_DEMO_TOKENS", False)
    assert client.get("/api/v1/auth/demo-tokens").status_code == 404


def test_ui_and_static_assets_render():
    page = client.get("/")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert client.get("/static/app.js").status_code == 200
