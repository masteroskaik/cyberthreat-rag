from typing import List, Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QueryRequest(BaseModel):
    question: str
    top_k_retrieval: int = 20
    top_n_context: int = 5


class SourceItem(BaseModel):
    type: str
    id: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]


class CVEItem(BaseModel):
    id: str
    description: str
    cvss_score: Optional[float]
    cvss_severity: Optional[str]
    published_at: Optional[str]
    is_kev: bool


class HealthResponse(BaseModel):
    status: str
    database: bool
