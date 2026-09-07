from pathlib import Path
from fastapi import FastAPI
from .metadata.registry import MetadataRegistry
from .query.service import QueryService
from .database.engine import create_database_engine
from .database.sample_db import initialize_sample_database
from .config import DatabaseSettings
from .database.engine import create_url_engine

ROOT = Path(__file__).resolve().parents[2]
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
from .api.rest import query_router, views_router

app.include_router(views_router)
app.include_router(query_router)

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
