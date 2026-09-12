from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from api.schemas import CVEItem
from api.auth import get_current_user
from db.connection import get_connection

router = APIRouter(prefix="/cves", tags=["cves"])


@router.get("", response_model=List[CVEItem])
def list_cves(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    severity: str = Query(default=None),
    current_user: str = Depends(get_current_user),
):
    query = """
        SELECT c.id, c.description, c.cvss_score, c.cvss_severity,
               c.published_at, k.cve_id IS NOT NULL AS is_kev
        FROM cves c
        LEFT JOIN kev_entries k ON k.cve_id = c.id
    """
    params = []

    if severity:
        query += " WHERE c.cvss_severity = %s"
        params.append(severity)

    query += " ORDER BY c.published_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        CVEItem(
            id=row[0],
            description=row[1],
            cvss_score=float(row[2]) if row[2] is not None else None,
            cvss_severity=row[3],
            published_at=str(row[4]) if row[4] else None,
            is_kev=row[5],
        )
        for row in rows
    ]


@router.get("/{cve_id}", response_model=CVEItem)
def get_cve(cve_id: str, current_user: str = Depends(get_current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.description, c.cvss_score, c.cvss_severity,
                       c.published_at, k.cve_id IS NOT NULL AS is_kev
                FROM cves c
                LEFT JOIN kev_entries k ON k.cve_id = c.id
                WHERE c.id = %s
                """,
                (cve_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="CVE introuvable")

    return CVEItem(
        id=row[0],
        description=row[1],
        cvss_score=float(row[2]) if row[2] is not None else None,
        cvss_severity=row[3],
        published_at=str(row[4]) if row[4] else None,
        is_kev=row[5],
    )
