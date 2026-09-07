import logging

from fastapi.testclient import TestClient
from app.api.mcp.server import query as mcp_query
from app.main import app


def test_rest_request_input_and_sql_are_logged(caplog):
    caplog.set_level(logging.INFO, logger="restricted_sql")
    response = TestClient(app).post(
        "/api/query",
        headers={"x-request-id": "rest-test-1"},
        json={"sql": "SELECT c.id FROM customers c LIMIT 1"},
    )
    assert response.status_code == 200
    messages = [record.getMessage() for record in caplog.records]
    assert any("source=rest" in message and "rest-test-1" in message for message in messages)
    assert any("sql statement=" in message and "LIMIT" in message for message in messages)


def test_mcp_input_and_sql_are_logged(caplog):
    caplog.set_level(logging.INFO, logger="restricted_sql")
    result = mcp_query("SELECT c.id FROM customers c WHERE c.id = 1")
    assert result["count"] == 1
    messages = [record.getMessage() for record in caplog.records]
    assert any("source=mcp" in message and "SELECT c.id" in message for message in messages)
    assert any("sql statement=" in message and "parameters=" in message for message in messages)

def test_application_logger_can_reuse_uvicorn_terminal_handler(monkeypatch):
    import logging
    from app.observability import configure_logging, LOGGER

    uvicorn_logger = logging.getLogger("uvicorn.error")
    handler = logging.StreamHandler()
    uvicorn_logger.addHandler(handler)
    try:
        configure_logging()
        assert any(getattr(item, "_restricted_sql_uvicorn", False) for item in LOGGER.handlers)
    finally:
        uvicorn_logger.removeHandler(handler)
