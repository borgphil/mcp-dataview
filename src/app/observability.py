import json
import logging
import os
from time import perf_counter
from typing import Any

LOGGER = logging.getLogger("restricted_sql")


def configure_logging() -> None:
    level = os.getenv("APP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def log_request(source: str, request_id: str, method: str, path: str, inputs: Any) -> None:
    LOGGER.info(
        "request source=%s request_id=%s method=%s path=%s inputs=%s",
        source,
        request_id,
        method,
        path,
        json.dumps(inputs, default=str, sort_keys=True),
    )


def log_response(source: str, request_id: str, status_code: int, started: float) -> None:
    LOGGER.info(
        "response source=%s request_id=%s status_code=%d duration_ms=%.2f",
        source,
        request_id,
        status_code,
        (perf_counter() - started) * 1000,
    )


def log_mcp_tool(tool: str, request_id: str, inputs: dict[str, Any]) -> None:
    log_request("mcp", request_id, "MCP", tool, inputs)


def log_sql(statement: str, parameters: Any) -> None:
    LOGGER.info("sql statement=%s parameters=%s", statement, parameters)
