from pathlib import Path
from fastapi import FastAPI, Request
from time import perf_counter
from uuid import uuid4
from .metadata.registry import MetadataRegistry
from .query.service import QueryService
from .database.engine import create_database_engine
from .database.sample_db import initialize_sample_database
from .config import DatabaseSettings
from .database.engine import create_url_engine
from .observability import configure_logging, log_request, log_response

ROOT = Path(__file__).resolve().parents[2]
configure_logging()
registry = MetadataRegistry(ROOT / "config" / "views")
database_settings = DatabaseSettings.from_environment()
if database_settings.sample:
    engine = create_database_engine(ROOT / "data" / "sample.db")
    initialize_sample_database(engine)
    engine.dispose()
    engine = create_database_engine(ROOT / "data" / "sample.db", read_only=True)
else:
    engine = create_url_engine(database_settings.url, read_only=database_settings.read_only)
service = QueryService(registry, engine)
app = FastAPI(title="Restricted SQL Query Server")
app.state.registry = registry
app.state.service = service
from .api.rest import query_router, views_router

app.include_router(views_router)
app.include_router(query_router)

@app.middleware("http")
async def log_rest_requests(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    body = await request.body()
    inputs = body.decode("utf-8", errors="replace") if body else {}
    started = perf_counter()
    log_request("rest", request_id, request.method, request.url.path, inputs)
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    log_response("rest", request_id, response.status_code, started)
    return response

def main() -> None:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    import sys
    if "--mcp" in sys.argv:
        from .api.mcp.server import mcp
        mcp.run()
    else:
        main()
