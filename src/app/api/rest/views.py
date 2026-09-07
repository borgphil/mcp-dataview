from fastapi import APIRouter, HTTPException
from app.main import registry

router = APIRouter(prefix="/api/views")

@router.get("")
def list_views():
    return [{"name": view.name, "description": view.description} for view in registry.list_views()]

@router.get("/{view_name}")
def describe_view(view_name: str):
    try:
        return registry.get_view(view_name).model_dump()
    except Exception as exc:
        raise HTTPException(404, detail={"error": "INVALID_VIEW", "message": str(exc)}) from exc
