# Restricted SQL MCP and REST Query Server

A secure Python 3.12+ service that exposes only configured logical database views to GitHub Copilot and REST clients. The security boundary is:

`restricted SQL -> parser -> validated plan -> SQLAlchemy Core -> read-only database`

## Run

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Metadata is loaded from `config/views` at startup.

Application logging records REST and MCP request inputs, request IDs, validation outcomes, execution timing, and every SQLAlchemy statement with its bound parameters. Logs are explicitly sent to the console (`stderr`), including the terminal, VS Code Debug Console, and integrated terminal. Set `APP_LOG_LEVEL=DEBUG` or `APP_LOG_LEVEL=WARNING` to adjust verbosity. Database credentials are never included in application logs.

## SQLite and VS Code debugging

Create or repair the local sample database explicitly with:

```bash
PYTHONPATH=src .venv/bin/python -m app.database.sample_db
```

To recreate all sample tables, views, and data from scratch, add `--reset`. In VS Code, use the `Initialize SQLite Database` launch configuration or task. Use `REST API` to debug FastAPI and `MCP Server` to debug the stdio MCP process. The `Run tests` task runs the complete suite.

For a production database, install the optional PostgreSQL driver with `python -m pip install -e '.[postgres]'`, set `DATABASE_URL`, and keep `DATABASE_READ_ONLY=true`. The database account must be provisioned with `SELECT` permission only on the configured physical views; the application refuses a non-read-only external configuration.

Run the test suite with `PYTHONPATH=src pytest`. The development database is created at `data/sample.db`; production deployments should point the application at a read-only database account containing only the configured views.

## VS Code and Copilot

The MCP configuration is in `.vscode/mcp.json`. Start the server, open this folder in VS Code, enable Copilot Agent mode, and inspect the `list_views`, `describe_view`, `validate_query`, and `query` tools. Ask Copilot to produce restricted SQL, then use `validate_query` before execution.

For MCP directly, use `PYTHONPATH=src python -m app.main --mcp`.

## Security model

Only logical views and fields in YAML metadata are trusted. Physical identifiers are never accepted from the query text. Joins must match configured relationships, literals are bound parameters, the default result cap is 1,000 rows, queries have a five-second SQLite progress timeout, and the parser AST is never executed directly.

The sample database is for development only. Do not grant the service account access to base tables, unrelated views, writes, DDL, or administrative operations.
