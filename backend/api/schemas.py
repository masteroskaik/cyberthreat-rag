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
    target_type: Optional[str] = None
    target_id: Optional[str] = None


class SourceItem(BaseModel):
    type: str
    id: str
    score: float


class QueryResponse(BaseModel):
    id: Optional[int] = None
    answer: str
    sources: List[SourceItem]


class ReportItem(BaseModel):
    id: int
    question: str
    answer: str
    sources: List[dict]
    created_at: str


class CVEItem(BaseModel):
    id: str
    description: str
    cvss_score: Optional[float]
    cvss_severity: Optional[str]
    published_at: Optional[str]
    is_kev: bool


class TechniqueItem(BaseModel):
    id: str
    name: str
    description: str
    tactics: List[str]
    platforms: List[str]
    external_references: List[dict]


class HealthResponse(BaseModel):
    status: str
    database: bool
