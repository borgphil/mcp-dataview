# Restricted SQL

The initial slice accepts one `SELECT` over configured logical views and rejects writes, DDL, comments, multiple statements, `SELECT *`, subqueries, CTEs, set operations, and arbitrary `JOIN ... ON` predicates. Relationship-derived join predicates and SQLAlchemy parameter binding are implementation requirements for the next slice.
