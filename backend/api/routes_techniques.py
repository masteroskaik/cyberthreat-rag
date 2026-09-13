from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from api.schemas import TechniqueItem
from api.auth import get_current_user
from db.connection import get_connection

router = APIRouter(prefix="/techniques", tags=["techniques"])


@router.get("", response_model=List[TechniqueItem])
def list_techniques(
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: str = Depends(get_current_user),
):
    query = "SELECT id, name, description, tactics, platforms, external_references FROM attack_techniques"
    params = []

    if search:
        query += " WHERE id ILIKE %s OR name ILIKE %s OR description ILIKE %s"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY id LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        TechniqueItem(
            id=row[0], name=row[1], description=row[2],
            tactics=row[3] or [], platforms=row[4] or [],
            external_references=row[5] or [],
        )
        for row in rows
    ]


@router.get("/{technique_id}", response_model=TechniqueItem)
def get_technique(technique_id: str, current_user: str = Depends(get_current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description, tactics, platforms, external_references "
                "FROM attack_techniques WHERE id = %s",
                (technique_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Technique introuvable")

    return TechniqueItem(
        id=row[0], name=row[1], description=row[2],
        tactics=row[3] or [], platforms=row[4] or [],
        external_references=row[5] or [],
    )
