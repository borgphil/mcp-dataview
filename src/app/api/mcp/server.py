from mcp.server.fastmcp import FastMCP
from app.main import registry, service
from uuid import uuid4

mcp = FastMCP("restricted-sql")

@mcp.tool()
def list_views() -> list[dict]:
    return [{"name": view.name, "description": view.description} for view in registry.list_views()]

@mcp.tool()
def describe_view(view_name: str) -> dict:
    return registry.get_view(view_name).model_dump()

@mcp.tool()
def validate_query(sql: str) -> dict:
    request_id = str(uuid4())
    try:
        plan = service.validate(sql, source="mcp", request_id=request_id)
    except (ValueError, TimeoutError) as exc:
        return {"valid": False, "error": getattr(exc, "code", "QUERY_ERROR"), "message": str(exc)}
    return {"valid": True, "normalized_query": plan.sql, "root_view": plan.root_view}

@mcp.tool()
def query(sql: str) -> dict:
    request_id = str(uuid4())
    try:
        return service.execute(sql, source="mcp", request_id=request_id)
    except (ValueError, TimeoutError) as exc:
        return {"valid": False, "error": getattr(exc, "code", "QUERY_ERROR"), "message": str(exc)}

if __name__ == "__main__":
    mcp.run()
