import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import HealthResponse
from api.routes_auth import router as auth_router
from api.routes_query import router as query_router
from api.routes_cves import router as cves_router
from db.connection import get_connection

app = FastAPI(
    title="CyberThreat RAG API",
    description="API de Cyber Threat Intelligence basée sur un pipeline RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(query_router)
app.include_router(cves_router)


@app.get("/health", response_model=HealthResponse)
def health():
    db_ok = True
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception:
        db_ok = False

    return HealthResponse(status="ok" if db_ok else "degraded", database=db_ok)
