# Architecture

Both MCP and REST call the same `QueryService`. It validates restricted SQL against the startup-loaded YAML registry and returns a validated `QueryPlan`. The future compiler will construct SQLAlchemy Core expressions from that plan; parser ASTs and physical identifiers are never executed or trusted directly.

The parser output is converted into immutable internal AST nodes before compilation. The compiler cannot receive the parser tree or user-supplied physical identifiers.

The database boundary is read-only. Metadata owns the logical-to-physical mapping and the permitted relationship graph.

## Observability

REST middleware logs method, path, request ID, input body, status, and duration. MCP tools log tool name, request ID, and inputs. SQLAlchemy engine hooks log every executed statement and its bound parameters. Query-service logs add validation result, safe normalized SQL, complexity, result count, and duration without logging database credentials.
