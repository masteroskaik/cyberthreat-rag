import sys
import os
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.schemas import HealthResponse
from api.routes_auth import router as auth_router
from api.routes_query import router as query_router
from api.routes_cves import router as cves_router
from api.routes_techniques import router as techniques_router
from api.routes_reports import router as reports_router
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
app.include_router(techniques_router)
app.include_router(reports_router)


class SeverityBreakdown(BaseModel):
    critical: int
    high: int
    medium: int
    low: int


class TopKevItem(BaseModel):
    id: str
    cvss_score: Optional[float]
    cvss_severity: Optional[str]
    description: str


class TacticCount(BaseModel):
    tactic: str
    count: int


class StatsResponse(BaseModel):
    total_cves: int
    total_kev: int
    total_techniques: int
    severity_breakdown: SeverityBreakdown
    kev_critical: int
    kev_high: int
    critical_and_kev: int
    high_and_kev: int
    top_kev: List[TopKevItem]
    top_tactics: List[TacticCount]


@app.get("/stats", response_model=StatsResponse)
def stats():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM cves")
            total_cves = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM kev_entries")
            total_kev = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM attack_techniques")
            total_techniques = cur.fetchone()[0]

            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE cvss_severity = 'CRITICAL'),
                    COUNT(*) FILTER (WHERE cvss_severity = 'HIGH'),
                    COUNT(*) FILTER (WHERE cvss_severity = 'MEDIUM'),
                    COUNT(*) FILTER (WHERE cvss_severity = 'LOW')
                FROM cves
            """)
            crit, high, med, low = cur.fetchone()

            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE c.cvss_severity = 'CRITICAL'),
                    COUNT(*) FILTER (WHERE c.cvss_severity = 'HIGH')
                FROM kev_entries k
                JOIN cves c ON c.id = k.cve_id
            """)
            kev_critical, kev_high = cur.fetchone()

            cur.execute("""
                SELECT c.id, c.cvss_score, c.cvss_severity, c.description
                FROM kev_entries k
                JOIN cves c ON c.id = k.cve_id
                ORDER BY c.cvss_score DESC NULLS LAST
                LIMIT 5
            """)
            top_kev_rows = cur.fetchall()

            cur.execute("SELECT tactics FROM attack_techniques")
            all_tactics = {}
            for (tactics,) in cur.fetchall():
                for t in (tactics or []):
                    all_tactics[t] = all_tactics.get(t, 0) + 1
            top_tactics = sorted(all_tactics.items(), key=lambda x: x[1], reverse=True)[:5]

    return StatsResponse(
        total_cves=total_cves,
        total_kev=total_kev,
        total_techniques=total_techniques,
        severity_breakdown=SeverityBreakdown(critical=crit, high=high, medium=med, low=low),
        kev_critical=kev_critical or 0,
        kev_high=kev_high or 0,
        critical_and_kev=kev_critical or 0,
        high_and_kev=kev_high or 0,
        top_kev=[
            TopKevItem(id=r[0], cvss_score=r[1], cvss_severity=r[2], description=r[3])
            for r in top_kev_rows
        ],
        top_tactics=[TacticCount(tactic=t, count=c) for t, c in top_tactics],
    )


class DataSourceStatus(BaseModel):
    source: str
    last_run_at: Optional[str]
    records_count: Optional[int]


@app.get("/data-sources", response_model=List[DataSourceStatus])
def data_sources():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT source, last_run_at, records_count FROM ingestion_log")
            rows = cur.fetchall()

    return [
        DataSourceStatus(
            source=r[0],
            last_run_at=r[1].isoformat() if r[1] else None,
            records_count=r[2],
        )
        for r in rows
    ]


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
