from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/views")

@router.get("")
def list_views(request: Request):
    return [{"name": view.name, "description": view.description} for view in request.app.state.registry.list_views()]

@router.get("/{view_name}")
def describe_view(view_name: str, request: Request):
    try:
        return request.app.state.registry.get_view(view_name).model_dump()
    except Exception as exc:
        raise HTTPException(404, detail={"error": "INVALID_VIEW", "message": str(exc)}) from exc
