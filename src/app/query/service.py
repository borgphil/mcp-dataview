import logging
from time import monotonic, perf_counter
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from app.metadata.registry import MetadataRegistry
from app.sql.compiler import SqlAlchemyCompiler
from app.sql.validator import QueryPlan, RestrictedSqlValidator

logger = logging.getLogger(__name__)


class QueryService:
    def __init__(self, registry: MetadataRegistry, engine: Engine, max_result_size: int = 1000,
                 query_timeout_ms: int = 5000):
        self.registry = registry
        self.validator = RestrictedSqlValidator(registry)
        self.compiler = SqlAlchemyCompiler(registry)
        self.compiler.bind_engine(engine)
        self.engine = engine
        self.max_result_size = max_result_size
        self.query_timeout_ms = query_timeout_ms

    def validate(self, sql: str, source: str = "unknown", request_id: str | None = None) -> QueryPlan:
        try:
            plan = self.validator.validate(sql)
        except ValueError as exc:
            logger.warning(
                "query rejected source=%s request_id=%s error_code=%s",
                source, request_id, getattr(exc, "code", "INVALID_SQL"),
            )
            raise
        logger.info(
            "query validated source=%s request_id=%s root_view=%s complexity=%s",
            source, request_id, plan.root_view, plan.complexity,
        )
        return plan

    def execute(self, sql: str, source: str = "unknown", request_id: str | None = None) -> dict:
        started = perf_counter()
        logger.info("executing query sql=%s", sql)
        plan = self.validate(sql, source=source, request_id=request_id)
        statement = self.compiler.compile(plan)
        normalized_query = str(statement.compile(dialect=self.engine.dialect))
        if plan.limit is None:
            statement = statement.limit(self.max_result_size)
        with self.engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA query_only = ON")
            raw_connection = connection.connection
            deadline = monotonic() + self.query_timeout_ms / 1000
            if hasattr(raw_connection, "set_progress_handler"):
                raw_connection.set_progress_handler(lambda: int(monotonic() >= deadline), 1000)
            try:
                rows = [dict(row) for row in connection.execute(statement).mappings()]
            except OperationalError as exc:
                if monotonic() >= deadline:
                    raise TimeoutError("Database query timeout exceeded") from exc
                raise
            finally:
                if hasattr(raw_connection, "set_progress_handler"):
                    raw_connection.set_progress_handler(None, 0)
        logger.info(
            "query executed result_count=%d duration_ms=%.2f",
            len(rows), (perf_counter() - started) * 1000,
        )
        return {"columns": list(rows[0]) if rows else [], "rows": rows, "count": len(rows)}
