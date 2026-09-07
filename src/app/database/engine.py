from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import make_url

def create_database_engine(path: Path | None = None, read_only: bool = False) -> Engine:
    if path is not None and read_only:
        url = f"sqlite:///file:{path}?mode=ro&uri=true"
        return create_engine(url, future=True, connect_args={"uri": True})
    url = f"sqlite:///{path}" if path else "sqlite://"
    if path is None:
        return create_engine(url, future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(url, future=True)

def create_url_engine(url: str, read_only: bool = True) -> Engine:
    if not read_only:
        raise ValueError("Application database engines must be read-only")
    return create_engine(make_url(url), future=True, pool_pre_ping=True)
