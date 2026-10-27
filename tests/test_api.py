from fastapi.testclient import TestClient

from app.auth import mint_token
from app.main import app
from scripts.seed import main as seed_main

seed_main()
client = TestClient(app)


def make_token(role: str):
    return mint_token(f"{role}_id", f"{role.title()} User", role)


def test_approved_query():
    token = make_token("analyst")
    res = client.post(
        "/api/v1/agent/query",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prompt": "Summarize the oncall incident runbook",
            "requested_tool": "search_docs",
            "sensitivity": "medium",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["outcome"] == "approved"
    assert body["sources"]


def test_fallback_query():
    token = make_token("architect")
    res = client.post(
        "/api/v1/agent/query",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prompt": "Summarize the lotus cluster migration status",
            "sensitivity": "medium",
        },
    )
    assert res.status_code == 200
    assert res.json()["outcome"] == "fallback"


def test_review_resolution_flow():
    analyst = make_token("analyst")
    reviewer = make_token("reviewer")
    create = client.post(
        "/api/v1/agent/query",
        headers={"Authorization": f"Bearer {analyst}"},
        json={
            "prompt": "Export the quarterly finance data",
            "requested_tool": "finance_export",
            "sensitivity": "medium",
        },
    )
    assert create.status_code == 200
    reviews = client.get("/api/v1/reviews", headers={"Authorization": f"Bearer {reviewer}"})
    assert reviews.status_code == 200
    review_id = reviews.json()[0]["id"]
    resolve = client.post(
        f"/api/v1/reviews/{review_id}/resolve",
        headers={"Authorization": f"Bearer {reviewer}"},
        json={"resolution": "approved", "note": "Escalated export approved for test case."},
    )
    assert resolve.status_code == 200
