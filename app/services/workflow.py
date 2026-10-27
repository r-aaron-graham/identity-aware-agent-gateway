import json
import uuid
from typing import Any

from app.db import execute, fetch_all, fetch_one, write_audit
from app.models import Identity, QueryRequest
from app.services.policy import evaluate_policy
from app.services.retrieval import search_documents
from app.services.tools import execute_tool


def _compose_response(outcome: str, prompt: str, reasons: list[str], sources: list[dict], tool_result: str | None) -> str:
    if outcome == "clarify":
        return "I need more detail before I proceed. Please clarify the task, target system, or desired action."
    if outcome == "refused":
        return "I cannot proceed with this request because it crosses a destructive or unauthorized boundary."
    if outcome == "review_required":
        return "This request exceeds current role or sensitivity boundaries and has been routed for human review."
    if outcome == "fallback":
        return "I could not safely produce a supported answer from your authorized context. Returning a limited fallback response."
    citations = " ".join([f"[{s['doc_id']}]" for s in sources[:3]])
    summary = " ".join([s["content"].split(".")[0].strip() + "." for s in sources[:2]]) if sources else "No directly supported content found."
    tool_part = f" Tool: {tool_result}" if tool_result else ""
    return f"{summary} {citations}{tool_part}".strip()


def process_request(identity: Identity, payload: QueryRequest) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    write_audit(trace_id, "request_received", {"user_id": identity.user_id, "role": identity.role})

    decision = evaluate_policy(identity.role, payload.prompt, payload.sensitivity, payload.requested_tool)
    write_audit(trace_id, "policy_evaluated", {
        "outcome": decision.outcome,
        "risk_score": decision.risk_score,
        "reasons": decision.reasons,
        "required_classification": decision.required_classification,
    })

    retrieval = {"results": [], "blocked_matches": []}
    tool_result = None

    if decision.outcome == "approved":
        retrieval = search_documents(payload.prompt, decision.allowed_classifications)
        write_audit(trace_id, "retrieval_completed", {
            "result_count": len(retrieval["results"]),
            "blocked_matches": retrieval["blocked_matches"],
        })

        if not retrieval["results"]:
            decision.outcome = "fallback"
            decision.reasons.append("No authorized supporting documents were found for this request.")
            decision.risk_score = max(decision.risk_score, 0.45)

        elif retrieval["blocked_matches"]:
            decision.reasons.append("Some semantically relevant matches were blocked by classification policy.")
            decision.risk_score = max(decision.risk_score, 0.62)

        if payload.requested_tool and decision.outcome == "approved":
            tool_result = execute_tool(payload.requested_tool, payload.prompt, retrieval["results"])
            write_audit(trace_id, "tool_executed", {"tool_name": payload.requested_tool, "tool_result": tool_result})

    response_text = _compose_response(decision.outcome, payload.prompt, decision.reasons, retrieval["results"], tool_result)

    request_id = execute(
        """
        INSERT INTO requests (
            trace_id, user_id, user_name, role, prompt, requested_tool, sensitivity,
            outcome, risk_score, reason_summary, response_text, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            trace_id,
            identity.user_id,
            identity.name,
            identity.role,
            payload.prompt,
            payload.requested_tool,
            payload.sensitivity,
            decision.outcome,
            decision.risk_score,
            "; ".join(decision.reasons),
            response_text,
        ),
    )

    for src in retrieval["results"]:
        execute(
            """
            INSERT INTO retrieved_sources (request_id, doc_id, title, classification, score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (request_id, src["doc_id"], src["title"], src["classification"], src["score"]),
        )

    if decision.outcome == "review_required":
        execute(
            """
            INSERT INTO review_items (request_id, status, assigned_role, created_at)
            VALUES (?, 'open', 'reviewer', datetime('now'))
            """,
            (request_id,),
        )
        write_audit(trace_id, "review_opened", {"request_id": request_id})

    write_audit(trace_id, "request_finalized", {"request_id": request_id, "outcome": decision.outcome})

    return {
        "trace_id": trace_id,
        "outcome": decision.outcome,
        "reasons": decision.reasons,
        "response_text": response_text,
        "used_tool": payload.requested_tool if tool_result else None,
        "sources": [
            {
                "doc_id": s["doc_id"],
                "title": s["title"],
                "classification": s["classification"],
                "score": s["score"],
            }
            for s in retrieval["results"]
        ],
        "blocked_matches": retrieval["blocked_matches"],
    }


def get_trace(trace_id: str) -> dict[str, Any] | None:
    request_row = fetch_one("SELECT * FROM requests WHERE trace_id = ?", (trace_id,))
    if not request_row:
        return None
    sources = fetch_all(
        "SELECT doc_id, title, classification, score FROM retrieved_sources WHERE request_id = ? ORDER BY score DESC",
        (request_row["id"],),
    )
    audit = fetch_all("SELECT event_type, details_json, created_at FROM audit_events WHERE trace_id = ? ORDER BY id ASC", (trace_id,))
    for row in audit:
        row["details"] = json.loads(row.pop("details_json"))
    return {"request": request_row, "sources": sources, "audit": audit}


def list_reviews() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT r.id, r.status, r.assigned_role, r.created_at, q.trace_id, q.user_name, q.role, q.prompt, q.outcome
        FROM review_items r
        JOIN requests q ON q.id = r.request_id
        ORDER BY r.id DESC
        """
    )
    return rows


def resolve_review(review_id: int, resolver_name: str, resolution: str, note: str) -> dict[str, Any] | None:
    item = fetch_one("SELECT * FROM review_items WHERE id = ?", (review_id,))
    if not item:
        return None
    if item["status"] != "open":
        return {"error": "Review item already resolved."}
    execute(
        """
        UPDATE review_items
        SET status = 'resolved',
            resolved_at = datetime('now'),
            resolution = ?,
            resolution_note = ?,
            resolved_by = ?
        WHERE id = ?
        """,
        (resolution, note, resolver_name, review_id),
    )
    req = fetch_one("SELECT trace_id FROM requests WHERE id = ?", (item["request_id"],))
    if req:
        write_audit(req["trace_id"], "review_resolved", {"review_id": review_id, "resolution": resolution, "resolver": resolver_name})
    return fetch_one("SELECT * FROM review_items WHERE id = ?", (review_id,))


def get_metrics() -> dict[str, Any]:
    rows = fetch_all("SELECT outcome, COUNT(*) as count FROM requests GROUP BY outcome")
    metrics = {r["outcome"]: r["count"] for r in rows}
    open_reviews = fetch_one("SELECT COUNT(*) as c FROM review_items WHERE status = 'open'")
    metrics["open_reviews"] = open_reviews["c"] if open_reviews else 0
    return metrics
