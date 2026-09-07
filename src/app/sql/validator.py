from dataclasses import dataclass
from typing import Any
import sqlglot
from sqlglot import exp
from app.metadata.registry import MetadataRegistry, MetadataError
from app.sql.ast import (
    AggregateExpression, BinaryExpression, FieldRef, InExpression, LikeExpression,
    LiteralValue, LogicalExpression, JoinSpec, NotExpression, OrderSpec,
    RestrictedQueryAst, SelectItem,
)
from app.sql.parser import parse_restricted_sql

class QueryValidationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)

@dataclass(frozen=True)
class QueryPlan:
    sql: str
    root_view: str
    tables: tuple[str, ...]
    aliases: tuple[tuple[str, str], ...]
    selected_fields: tuple[str, ...]
    joins: tuple[tuple[str, str, str], ...]
    distinct: bool
    limit: int | None
    offset: int | None
    ast: RestrictedQueryAst
    complexity: dict[str, int]

class RestrictedSqlValidator:
    def __init__(self, registry: MetadataRegistry, max_joins: int = 4, max_fields: int = 50,
                 max_predicates: int = 50, max_group_fields: int = 20, max_aggregates: int = 20,
                 max_expression_depth: int = 12, max_relationship_depth: int = 4):
        self.registry = registry
        self.max_joins = max_joins
        self.max_fields = max_fields
        self.max_predicates = max_predicates
        self.max_group_fields = max_group_fields
        self.max_aggregates = max_aggregates
        self.max_expression_depth = max_expression_depth
        self.max_relationship_depth = max_relationship_depth

    def validate(self, sql: str) -> QueryPlan:
        if self._has_comment(sql) or ";" in sql.rstrip(" ;"):
            raise QueryValidationError("UNSUPPORTED_SQL", "Multiple statements are not supported")
        try:
            statement = parse_restricted_sql(sql)
        except sqlglot.errors.ParseError as exc:
            raise QueryValidationError("INVALID_SQL", str(exc)) from exc
        except ValueError as exc:
            raise QueryValidationError("UNSUPPORTED_SQL", str(exc)) from exc
        if not isinstance(statement, exp.Select):
            raise QueryValidationError("UNSUPPORTED_SQL", "Only one SELECT statement is supported")
        if any(isinstance(item, exp.Star) for item in statement.expressions):
            raise QueryValidationError("UNSUPPORTED_SQL", "SELECT * is not supported")
        if statement.find(exp.Subquery) or statement.find(exp.CTE) or statement.find(exp.Union):
            raise QueryValidationError("UNSUPPORTED_SQL", "Subqueries, CTEs, and set operations are not supported")
        for function in statement.find_all(exp.Func):
            if not isinstance(function, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)):
                raise QueryValidationError("UNSUPPORTED_SQL", f"Function '{function.key}' is not supported")
            if isinstance(function, exp.Count) and isinstance(function.this, exp.Distinct):
                raise QueryValidationError("UNSUPPORTED_SQL", "COUNT(DISTINCT ...) is not supported")
        if statement.find(exp.Window):
            raise QueryValidationError("UNSUPPORTED_SQL", "Window functions are not supported")
        tables = list(statement.find_all(exp.Table))
        if not tables:
            raise QueryValidationError("INVALID_VIEW", "A configured logical view is required")
        aliases: list[tuple[str, str]] = []
        for table in tables:
            try:
                self.registry.get_view(table.name)
            except MetadataError as exc:
                raise QueryValidationError("INVALID_VIEW", str(exc)) from exc
            aliases.append((table.alias_or_name, table.name))
        if len({alias for alias, _ in aliases}) != len(aliases):
            raise QueryValidationError("INVALID_ALIAS", "Table aliases must be unique")
        joins = list(statement.find_all(exp.Join))
        if len(joins) > self.max_joins:
            raise QueryValidationError("QUERY_TOO_COMPLEX", "Maximum join count exceeded")
        table_names = [table.name for table in tables]
        if len(table_names) - 1 > self.max_relationship_depth:
            raise QueryValidationError("QUERY_TOO_COMPLEX", "Maximum relationship depth exceeded")
        join_specs: list[tuple[str, str, str]] = []
        for join in joins:
            if join.args.get("on") is not None:
                raise QueryValidationError("INVALID_RELATIONSHIP", "JOIN predicates are generated from metadata")
            side = str(join.args.get("side") or "INNER").upper()
            if side not in {"INNER", "LEFT"}:
                raise QueryValidationError("UNSUPPORTED_SQL", "Only INNER JOIN and LEFT JOIN are supported")
        for index, (source, target) in enumerate(zip(table_names, table_names[1:])):
            try:
                self.registry.get_relationship(source, target)
            except MetadataError:
                try:
                    self.registry.get_relationship(target, source)
                except MetadataError as exc:
                    raise QueryValidationError("INVALID_RELATIONSHIP", str(exc)) from exc
            join_specs.append((source, target, str(joins[index].args.get("side") or "INNER").upper()))
        select_aliases = {
            expression.alias for expression in statement.expressions if isinstance(expression, exp.Alias)
        }
        for column in statement.find_all(exp.Column):
            if not column.table and column.name in select_aliases:
                continue
            alias = column.table or aliases[0][0]
            view_name = dict(aliases).get(alias)
            if view_name is None or column.name not in self.registry.get_view(view_name).fields:
                raise QueryValidationError("INVALID_FIELD", f"Field '{column.name}' is not exposed")
        for comparison in statement.find_all((exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE, exp.Like)):
            self._validate_literal_type(comparison.left, comparison.right, aliases)
        for membership in statement.find_all(exp.In):
            for value in membership.expressions:
                self._validate_literal_type(membership.this, value, aliases)
        selected_fields = tuple(column.name for column in statement.find_all(exp.Column))
        if len(statement.expressions) > self.max_fields:
            raise QueryValidationError("QUERY_TOO_COMPLEX", "Maximum selected field count exceeded")
        predicate_count = sum(1 for node in statement.walk() if isinstance(node, (exp.And, exp.Or, exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE, exp.Like, exp.In)))
        if predicate_count > self.max_predicates:
            raise QueryValidationError("QUERY_TOO_COMPLEX", "Maximum predicate count exceeded")
        aggregates = [node for node in statement.walk() if isinstance(node, (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max))]
        if len(aggregates) > self.max_aggregates:
            raise QueryValidationError("QUERY_TOO_COMPLEX", "Maximum aggregate count exceeded")
        group = statement.args.get("group")
        if group and len(group.expressions) > self.max_group_fields:
            raise QueryValidationError("QUERY_TOO_COMPLEX", "Maximum GROUP BY field count exceeded")
        group_columns = {column.sql() for column in (group.expressions if group else [])}
        has_aggregate = bool(aggregates)
        for expression in statement.expressions:
            plain = expression.this if isinstance(expression, exp.Alias) else expression
            if isinstance(plain, exp.Column) and plain.sql() not in group_columns and (group or has_aggregate):
                raise QueryValidationError("INVALID_GROUPING", f"Selected field '{plain.sql()}' must be grouped")
        for aggregate in aggregates:
            if isinstance(aggregate, (exp.Sum, exp.Avg)) and isinstance(aggregate.this, exp.Column):
                alias = aggregate.this.table or aliases[0][0]
                view_name = dict(aliases).get(alias)
                field_type = self.registry.get_view(view_name).fields[aggregate.this.name].type
                if field_type not in {"integer", "decimal"}:
                    raise QueryValidationError("INVALID_AGGREGATE", f"{aggregate.key.upper()} requires a numeric field")
        if any(self._depth(node) > self.max_expression_depth for node in statement.walk()):
            raise QueryValidationError("QUERY_TOO_COMPLEX", "Maximum expression depth exceeded")
        limit = statement.args.get("limit")
        offset = statement.args.get("offset")
        limit_value = int(limit.expression.this) if limit and limit.expression.is_int else None
        offset_value = int(offset.expression.this) if offset and offset.expression.is_int else None
        if limit and limit_value is None or offset and offset_value is None:
            raise QueryValidationError("INVALID_PAGINATION", "LIMIT and OFFSET must be numeric")
        if limit_value is not None and limit_value > 1000 or offset_value is not None and offset_value > 10000:
            raise QueryValidationError("QUERY_TOO_COMPLEX", "Pagination limit exceeded")
        root = tables[0].name
        restricted_ast = RestrictedQueryAst(
            root_view=root,
            aliases=tuple(aliases),
            select=tuple(
                SelectItem(self._to_ast(expression.this if isinstance(expression, exp.Alias) else expression, aliases), expression.alias if isinstance(expression, exp.Alias) else None)
                for expression in statement.expressions
            ),
            joins=tuple(JoinSpec(source, target, side) for source, target, side in join_specs),
            where=self._to_ast(statement.args["where"].this, aliases) if statement.args.get("where") else None,
            group_by=tuple(self._field_ref(item, aliases) for item in (group.expressions if group else [])),
            having=self._to_ast(statement.args["having"].this, aliases) if statement.args.get("having") else None,
            order_by=tuple(
                OrderSpec(
                    item.this.name if not item.this.table and item.this.name in select_aliases else self._to_ast(item.this, aliases),
                    bool(item.args.get("desc")),
                )
                for item in (statement.args["order"].expressions if statement.args.get("order") else [])
            ),
            distinct=bool(statement.args.get("distinct")),
            limit=limit_value,
            offset=offset_value,
        )
        return QueryPlan(
            sql=sql,
            root_view=root,
            tables=tuple(table_names),
            aliases=tuple(aliases),
            selected_fields=selected_fields,
            joins=tuple(join_specs),
            distinct=bool(statement.args.get("distinct")),
            limit=limit_value,
            offset=offset_value,
            ast=restricted_ast,
            complexity={
                "joins": len(join_specs),
                "selected_fields": len(statement.expressions),
                "predicates": predicate_count,
                "aggregates": len(aggregates),
                "group_by_fields": len(group.expressions) if group else 0,
            },
        )

    def _field_ref(self, expression: exp.Expression, aliases: list[tuple[str, str]]) -> FieldRef:
        if not isinstance(expression, exp.Column):
            raise QueryValidationError("UNSUPPORTED_SQL", "GROUP BY accepts fields only")
        alias = expression.table or aliases[0][0]
        return FieldRef(alias, expression.name)

    def _to_ast(self, expression: exp.Expression, aliases: list[tuple[str, str]]):
        if isinstance(expression, exp.Column):
            return self._field_ref(expression, aliases)
        if isinstance(expression, exp.Literal):
            value = expression.this
            if not expression.is_string:
                value = float(value) if "." in value else int(value)
            return LiteralValue(value)
        if isinstance(expression, exp.Paren):
            return self._to_ast(expression.this, aliases)
        if isinstance(expression, exp.Not):
            return NotExpression(self._to_ast(expression.this, aliases))
        if isinstance(expression, exp.In):
            return InExpression(self._to_ast(expression.this, aliases), tuple(self._to_ast(item, aliases) for item in expression.expressions))
        if isinstance(expression, exp.Like):
            return LikeExpression(self._to_ast(expression.this, aliases), self._to_ast(expression.expression, aliases))
        if isinstance(expression, (exp.And, exp.Or)):
            return LogicalExpression(expression.key.upper(), self._to_ast(expression.left, aliases), self._to_ast(expression.right, aliases))
        binary_operators = {exp.EQ: "=", exp.NEQ: "!=", exp.GT: ">", exp.GTE: ">=", exp.LT: "<", exp.LTE: "<="}
        for expression_type, operator in binary_operators.items():
            if isinstance(expression, expression_type):
                return BinaryExpression(operator, self._to_ast(expression.left, aliases), self._to_ast(expression.right, aliases))
        aggregate_types = {exp.Count: "COUNT", exp.Sum: "SUM", exp.Avg: "AVG", exp.Min: "MIN", exp.Max: "MAX"}
        for expression_type, function in aggregate_types.items():
            if isinstance(expression, expression_type):
                field = None if isinstance(expression.this, exp.Star) else self._field_ref(expression.this, aliases)
                return AggregateExpression(function, field)
        raise QueryValidationError("UNSUPPORTED_SQL", f"Unsupported expression: {expression.key}")

    @staticmethod
    def _depth(node: exp.Expression) -> int:
        depth = 0
        current = node.parent
        while current is not None:
            depth += 1
            current = current.parent
        return depth

    def _validate_literal_type(self, left: exp.Expression, right: exp.Expression, aliases: list[tuple[str, str]]) -> None:
        if not isinstance(left, exp.Column) or not isinstance(right, exp.Literal):
            return
        alias = left.table or aliases[0][0]
        view_name = dict(aliases).get(alias)
        if view_name is None:
            return
        field_type = self.registry.get_view(view_name).fields[left.name].type
        if field_type in {"integer", "decimal"} and right.is_string:
            raise QueryValidationError("INVALID_LITERAL", f"Field '{left.name}' requires a numeric literal")
        if field_type in {"string", "date"} and not right.is_string:
            raise QueryValidationError("INVALID_LITERAL", f"Field '{left.name}' requires a string literal")
        if field_type == "boolean" and right.is_string and right.this.lower() not in {"true", "false"}:
            raise QueryValidationError("INVALID_LITERAL", f"Field '{left.name}' requires a boolean literal")
        if field_type == "boolean" and not right.is_string:
            raise QueryValidationError("INVALID_LITERAL", f"Field '{left.name}' requires a boolean literal")

    @staticmethod
    def _has_comment(sql: str) -> bool:
        quote: str | None = None
        index = 0
        while index < len(sql):
            character = sql[index]
            if quote:
                if character == quote:
                    if index + 1 < len(sql) and sql[index + 1] == quote:
                        index += 2
                        continue
                    quote = None
            elif character in "'\"":
                quote = character
            elif sql.startswith("--", index) or sql.startswith("/*", index):
                return True
            index += 1
        return False
