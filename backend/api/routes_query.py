from fastapi import APIRouter, Depends, HTTPException

from api.schemas import QueryRequest, QueryResponse, SourceItem
from api.auth import get_current_user
from generation.generate_report import generate_cti_report

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query(request: QueryRequest, current_user: str = Depends(get_current_user)):
    try:
        result = generate_cti_report(
            request.question,
            top_k_retrieval=request.top_k_retrieval,
            top_n_context=request.top_n_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QueryResponse(
        answer=result["answer"],
        sources=[SourceItem(**s) for s in result["sources"]],
    )
