from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import make_url
from app.observability import log_sql

def _attach_sql_logging(engine: Engine) -> Engine:
    @event.listens_for(engine, "before_cursor_execute")
    def log_before_cursor_execute(connection, cursor, statement, parameters, context, executemany):
        log_sql(statement, parameters)
    return engine

def create_database_engine(path: Path | None = None, read_only: bool = False) -> Engine:
    if path is not None and read_only:
        url = f"sqlite:///file:{path}?mode=ro&uri=true"
        return _attach_sql_logging(create_engine(url, future=True, connect_args={"uri": True}))
    url = f"sqlite:///{path}" if path else "sqlite://"
    if path is None:
        return _attach_sql_logging(create_engine(url, future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool))
    return _attach_sql_logging(create_engine(url, future=True))

def create_url_engine(url: str, read_only: bool = True) -> Engine:
    if not read_only:
        raise ValueError("Application database engines must be read-only")
    return _attach_sql_logging(create_engine(make_url(url), future=True, pool_pre_ping=True))
