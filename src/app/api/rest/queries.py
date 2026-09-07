from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi import Request
from uuid import uuid4
from app.main import service

router = APIRouter(prefix="/api/query")

class QueryRequest(BaseModel):
    sql: str

@router.post("")
def query(request: QueryRequest, http_request: Request):
    request_id = http_request.headers.get("x-request-id", str(uuid4()))
    try:
        return service.execute(request.sql, source="rest", request_id=request_id)
    except (ValueError, TimeoutError) as exc:
        raise HTTPException(400, detail={"error": getattr(exc, "code", "INVALID_SQL"), "message": str(exc)}) from exc

@router.post("/validate")
def validate(request: QueryRequest, http_request: Request):
    request_id = http_request.headers.get("x-request-id", str(uuid4()))
    try:
        plan = service.validate(request.sql, source="rest", request_id=request_id)
    except (ValueError, TimeoutError) as exc:
        return {"valid": False, "error": getattr(exc, "code", "INVALID_SQL"), "message": str(exc)}
    return {"valid": True, "normalized_query": plan.sql, "root_view": plan.root_view}
