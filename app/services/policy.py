import re
from dataclasses import dataclass
from typing import List, Optional
from app.services.identity import permissions_for, SENSITIVITY_RANK

DESTRUCTIVE_PATTERNS = [
    r"\bdelete\b",
    r"\bwipe\b",
    r"\berase\b",
    r"\bdestroy\b",
    r"\bdrop\s+database\b",
]

AMBIGUOUS_PATTERNS = [
    r"\bhandle this\b",
    r"\bdo it\b",
    r"\bfix it\b",
    r"\btake care of this\b",
]

CONFIDENTIAL_TERMS = [r"\bfinance\b", r"\bpayroll\b", r"\bmargin\b", r"\bconfidential\b"]
RESTRICTED_TERMS = [r"\barchitecture\b", r"\brestricted\b", r"\bsecret\b", r"\bkey\b"]
INTERNAL_TERMS = [r"\boncall\b", r"\brunbook\b", r"\bincident\b", r"\binternal\b"]


@dataclass
class PolicyDecision:
    outcome: str
    reasons: List[str]
    risk_score: float
    required_classification: str
    allowed_classifications: List[str]
    allowed_tools: List[str]


def _matches_any(prompt: str, patterns: List[str]) -> bool:
    return any(re.search(p, prompt, re.IGNORECASE) for p in patterns)


def infer_required_classification(prompt: str) -> str:
    if _matches_any(prompt, CONFIDENTIAL_TERMS):
        return "confidential"
    if _matches_any(prompt, RESTRICTED_TERMS):
        return "restricted"
    if _matches_any(prompt, INTERNAL_TERMS):
        return "internal"
    return "public"


def evaluate_policy(role: str, prompt: str, sensitivity: str, requested_tool: Optional[str]) -> PolicyDecision:
    perms = permissions_for(role)
    allowed_classifications = perms["classifications"]
    allowed_tools = perms["tools"]
    reasons: List[str] = []
    risk_score = 0.10
    required_classification = infer_required_classification(prompt)

    if len(prompt.strip()) < 8 or _matches_any(prompt, AMBIGUOUS_PATTERNS):
        reasons.append("Prompt is too ambiguous to execute safely without clarification.")
        return PolicyDecision(
            outcome="clarify",
            reasons=reasons,
            risk_score=0.35,
            required_classification=required_classification,
            allowed_classifications=allowed_classifications,
            allowed_tools=allowed_tools,
        )

    if _matches_any(prompt, DESTRUCTIVE_PATTERNS):
        reasons.append("Destructive or irreversible action language detected.")
        return PolicyDecision(
            outcome="refused",
            reasons=reasons,
            risk_score=0.98,
            required_classification=required_classification,
            allowed_classifications=allowed_classifications,
            allowed_tools=allowed_tools,
        )

    if SENSITIVITY_RANK[sensitivity] > SENSITIVITY_RANK[perms["max_sensitivity"]]:
        reasons.append(f"Declared sensitivity '{sensitivity}' exceeds role limit '{perms['max_sensitivity']}'.")
        return PolicyDecision(
            outcome="review_required",
            reasons=reasons,
            risk_score=0.82,
            required_classification=required_classification,
            allowed_classifications=allowed_classifications,
            allowed_tools=allowed_tools,
        )

    if required_classification not in allowed_classifications:
        reasons.append(
            f"Prompt appears to require '{required_classification}' data, which exceeds role '{role}' scope."
        )
        return PolicyDecision(
            outcome="review_required",
            reasons=reasons,
            risk_score=0.88,
            required_classification=required_classification,
            allowed_classifications=allowed_classifications,
            allowed_tools=allowed_tools,
        )

    if requested_tool == "finance_export" and role != "admin":
        reasons.append("Finance export is privileged and must be reviewed or approved by admin.")
        return PolicyDecision(
            outcome="review_required",
            reasons=reasons,
            risk_score=0.90,
            required_classification=required_classification,
            allowed_classifications=allowed_classifications,
            allowed_tools=allowed_tools,
        )

    if requested_tool and requested_tool not in allowed_tools:
        reasons.append(f"Tool '{requested_tool}' is not allowed for role '{role}'.")
        return PolicyDecision(
            outcome="review_required",
            reasons=reasons,
            risk_score=0.86,
            required_classification=required_classification,
            allowed_classifications=allowed_classifications,
            allowed_tools=allowed_tools,
        )

    if requested_tool:
        reasons.append(f"Tool '{requested_tool}' is permitted for role '{role}'.")
        risk_score += 0.05

    reasons.append(f"Role '{role}' is allowed to access '{required_classification}' data.")
    return PolicyDecision(
        outcome="approved",
        reasons=reasons,
        risk_score=risk_score,
        required_classification=required_classification,
        allowed_classifications=allowed_classifications,
        allowed_tools=allowed_tools,
    )
