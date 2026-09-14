from fastapi import APIRouter, Depends, HTTPException
import json

from api.schemas import QueryRequest, QueryResponse, SourceItem
from api.auth import get_current_user
from generation.generate_report import generate_cti_report
from db.connection import get_connection

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query(request: QueryRequest, current_user: str = Depends(get_current_user)):
    try:
        result = generate_cti_report(
            request.question,
            top_k_retrieval=request.top_k_retrieval,
            top_n_context=request.top_n_context,
            target_type=request.target_type,
            target_id=request.target_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    report_id = None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO reports (question, answer, sources) VALUES (%s, %s, %s) RETURNING id",
                (request.question, result["answer"], json.dumps(result["sources"])),
            )
            report_id = cur.fetchone()[0]

    return QueryResponse(
        id=report_id,
        answer=result["answer"],
        sources=[SourceItem(**s) for s in result["sources"]],
    )
