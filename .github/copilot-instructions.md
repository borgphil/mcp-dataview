# Restricted SQL MCP Server Instructions

- Treat all incoming SQL as untrusted input.
- Never execute parser-generated SQL directly; compile only a validated internal QueryPlan with SQLAlchemy Core.
- Resolve logical views, fields, physical views, physical columns, and joins exclusively through `config/views/*.yaml` metadata.
- Reject writes, DDL, comments, multiple statements, subqueries, CTEs, set operations, arbitrary functions, windows, unknown identifiers, arbitrary join predicates, and unrestricted `SELECT *`.
- Bind every literal as a SQLAlchemy parameter. Never concatenate user values into SQL.
- Keep REST and MCP behind the same `QueryService`; do not duplicate validation or authorization logic.
- Preserve the read-only database boundary and enforce query complexity and result-size limits.
- Add focused unit and security tests for every parser or validator change.
- Use type hints, Pydantic v2 models, SQLAlchemy 2.x, and Python 3.12+.
