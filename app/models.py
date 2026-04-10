from typing import List, Optional
from pydantic import BaseModel, Field


class Identity(BaseModel):
    user_id: str
    name: str
    role: str
    exp: int


class QueryRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    requested_tool: Optional[str] = None
    sensitivity: str = Field(default="low", pattern="^(low|medium|high|critical)$")


class SourceRef(BaseModel):
    doc_id: str
    title: str
    classification: str
    score: float


class QueryResponse(BaseModel):
    trace_id: str
    outcome: str
    reasons: List[str]
    response_text: str
    used_tool: Optional[str] = None
    sources: List[SourceRef] = []
    blocked_matches: List[str] = []


class ReviewResolution(BaseModel):
    resolution: str = Field(pattern="^(approved|rejected)$")
    note: Optional[str] = Field(default="", max_length=1000)
