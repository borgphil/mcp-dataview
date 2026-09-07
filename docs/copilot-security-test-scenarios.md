# Copilot Security Test Scenarios

Each attempt must be rejected by the server, regardless of whether Copilot generated it:

- Arbitrary SQL execution, base-table access, unregistered views, and sensitive fields.
- Invented relationships, arbitrary join predicates, and incomplete composite joins.
- SQL injection values, comments, multiple statements, and unrestricted `SELECT *`.
- `DROP`, `INSERT`, `UPDATE`, `DELETE`, `MERGE`, DDL, `UNION`, subqueries, and CTEs.
- Arbitrary functions, nested aggregates, window functions, invalid grouping, excessive joins, and excessive pagination.

Values containing SQL syntax must remain bound data and must never change query structure.
