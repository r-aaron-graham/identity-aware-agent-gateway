from app.services.policy import evaluate_policy


def test_destructive_prompt_refused():
    decision = evaluate_policy("analyst", "Delete the customer records", "medium", None)
    assert decision.outcome == "refused"


def test_ambiguous_prompt_clarify():
    decision = evaluate_policy("viewer", "handle this", "low", None)
    assert decision.outcome == "clarify"


def test_confidential_request_requires_review():
    decision = evaluate_policy("analyst", "Export quarterly finance data", "medium", "finance_export")
    assert decision.outcome == "review_required"
