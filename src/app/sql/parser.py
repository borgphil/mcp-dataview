import sqlglot
from sqlglot import exp

def parse_restricted_sql(sql: str) -> exp.Expression:
    statements = sqlglot.parse(sql, read="sqlite")
    if len(statements) != 1:
        raise ValueError("Exactly one statement is required")
    return statements[0]
