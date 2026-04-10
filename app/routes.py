from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from app.auth import mint_token, verify_token
from app.config import DEMO_USERS
from app.models import Identity, QueryRequest, QueryResponse, ReviewResolution
from app.services.workflow import process_request, get_trace, list_reviews, resolve_review, get_metrics

router = APIRouter(prefix="/api/v1")
templates = Jinja2Templates(directory="app/templates")


def current_identity(authorization: str | None = Header(default=None)) -> Identity:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    payload = verify_token(token)
    return Identity(
        user_id=payload["sub"],
        name=payload["name"],
        role=payload["role"],
        exp=payload["exp"],
    )


def reviewer_or_admin(identity: Identity = Depends(current_identity)) -> Identity:
    if identity.role not in {"reviewer", "admin"}:
        raise HTTPException(status_code=403, detail="Reviewer or admin role required")
    return identity


@router.get("/auth/demo-tokens")
def demo_tokens():
    tokens = {}
    for key, user in DEMO_USERS.items():
        tokens[key] = {
            "name": user["name"],
            "role": user["role"],
            "token": mint_token(user["user_id"], user["name"], user["role"]),
        }
    return tokens


@router.get("/whoami")
def whoami(identity: Identity = Depends(current_identity)):
    return identity


@router.post("/agent/query", response_model=QueryResponse)
def agent_query(payload: QueryRequest, identity: Identity = Depends(current_identity)):
    result = process_request(identity, payload)
    return QueryResponse(**result)


@router.get("/traces/{trace_id}")
def trace(trace_id: str, identity: Identity = Depends(current_identity)):
    result = get_trace(trace_id)
    if not result:
        raise HTTPException(status_code=404, detail="Trace not found")
    owner_id = result["request"]["user_id"]
    if owner_id != identity.user_id and identity.role not in {"reviewer", "admin"}:
        raise HTTPException(status_code=403, detail="Trace not accessible for current identity")
    return result


@router.get("/reviews")
def reviews(identity: Identity = Depends(reviewer_or_admin)):
    return list_reviews()


@router.post("/reviews/{review_id}/resolve")
def resolve(review_id: int, payload: ReviewResolution, identity: Identity = Depends(reviewer_or_admin)):
    result = resolve_review(review_id, identity.name, payload.resolution, payload.note or "")
    if result is None:
        raise HTTPException(status_code=404, detail="Review item not found")
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    return result


@router.get("/metrics")
def metrics(identity: Identity = Depends(reviewer_or_admin)):
    return get_metrics()
