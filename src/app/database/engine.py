from pathlib import Path
import re
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import make_url
from app.observability import log_sql

_SQLITE_INTROSPECTION_PATTERNS = (
    r"^\s*SELECT\s+.*\bFROM\s+sqlite_master\b",
    r"^\s*SELECT\s+.*\bFROM\s+pragma_.*\b",
    r"^\s*pragma\b",
    r"^\s*EXPLAIN\b",
    r"^\s*WITH\s+.*\bsqlite_master\b",
)

_ALLOWED_SQL_PREFIXES = (
    "select",
    "insert",
    "update",
    "delete",
    "with",
    "create",
    "alter",
    "drop",
    "begin",
    "commit",
    "rollback",
)


def _should_log_sql(statement: str) -> bool:
    normalized = " ".join(statement.strip().split())
    if not normalized:
        return False
    lowered = normalized.lower()
    if any(re.search(pattern, lowered, re.IGNORECASE) for pattern in _SQLITE_INTROSPECTION_PATTERNS):
        return False
    prefix = lowered.split(None, 1)[0]
    return prefix in _ALLOWED_SQL_PREFIXES


def _attach_sql_logging(engine: Engine) -> Engine:
    @event.listens_for(engine, "before_cursor_execute")
    def log_before_cursor_execute(connection, cursor, statement, parameters, context, executemany):
        if _should_log_sql(statement):
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
