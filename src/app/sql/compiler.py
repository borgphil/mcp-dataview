from sqlalchemy import MetaData, Table, and_, asc, bindparam, desc, func, or_, select
from sqlalchemy.sql.elements import ClauseElement
from app.metadata.registry import MetadataRegistry
from app.sql.validator import QueryPlan, QueryValidationError
from app.sql.ast import AggregateExpression, BinaryExpression, FieldRef, InExpression, LikeExpression, LiteralValue, LogicalExpression, NotExpression

class SqlAlchemyCompiler:
    def __init__(self, registry: MetadataRegistry):
        self.registry = registry

    def compile(self, plan: QueryPlan) -> ClauseElement:
        metadata = MetaData()
        aliases = dict(plan.aliases)
        tables = {}
        projection_labels = {}
        for alias, view_name in plan.aliases:
            view = self.registry.get_view(view_name)
            with self._engine.connect() as connection:
                object_type = connection.exec_driver_sql(
                    "SELECT type FROM sqlite_master WHERE name = ?", (view.sql_view,)
                ).scalar_one_or_none()
            if object_type != "view":
                raise QueryValidationError("INVALID_METADATA", f"Configured object '{view.sql_view}' is not a database view")
            physical = Table(view.sql_view, metadata, autoload_with=self._engine)
            tables[alias] = physical.alias(alias)
        first_alias = plan.aliases[0][0]
        statement = select()
        for projection in plan.ast.select:
            compiled_projection = self._expression(projection.expression, tables, aliases, projection_labels)
            if projection.alias:
                compiled_projection = compiled_projection.label(projection.alias)
                projection_labels[projection.alias] = compiled_projection
            statement = statement.add_columns(compiled_projection)
        statement = statement.select_from(tables[first_alias])
        for join in plan.ast.joins:
            source, target, side = join.source, join.target, join.side
            source_alias = next(alias for alias, view in plan.aliases if view == source)
            target_alias = next(alias for alias, view in plan.aliases if view == target)
            relationship = self._relationship(source, target)
            predicates = []
            for mapping in relationship.column_mappings:
                if relationship.to_view == target:
                    left = self._column(source_alias, source, mapping.from_field, tables, aliases)
                    right = self._column(target_alias, target, mapping.to_field, tables, aliases)
                else:
                    left = self._column(source_alias, source, mapping.to_field, tables, aliases)
                    right = self._column(target_alias, target, mapping.from_field, tables, aliases)
                predicates.append(left == right)
            statement = statement.join(tables[target_alias], and_(*predicates), isouter=side == "LEFT")
        if plan.ast.where:
            statement = statement.where(self._expression(plan.ast.where, tables, aliases))
        if plan.ast.distinct:
            statement = statement.distinct()
        if plan.ast.group_by:
            statement = statement.group_by(*(self._expression(item, tables, aliases) for item in plan.ast.group_by))
        if plan.ast.having:
            statement = statement.having(self._expression(plan.ast.having, tables, aliases))
        if plan.ast.order_by:
            statement = statement.order_by(*(
                desc(self._expression(item.expression, tables, aliases, projection_labels)) if item.descending
                else asc(self._expression(item.expression, tables, aliases, projection_labels))
                for item in plan.ast.order_by
            ))
        if plan.limit is not None:
            statement = statement.limit(plan.limit)
        if plan.offset is not None:
            statement = statement.offset(plan.offset)
        return statement

    def bind_engine(self, engine) -> None:
        self._engine = engine

    def _relationship(self, source: str, target: str):
        try:
            return self.registry.get_relationship(source, target)
        except Exception:
            return self.registry.get_relationship(target, source)

    def _column(self, alias, view_name, field, tables, aliases):
        try:
            definition = self.registry.get_view(view_name).fields[field]
        except KeyError as exc:
            raise QueryValidationError("INVALID_FIELD", f"Field '{field}' is not exposed") from exc
        return tables[alias].c[definition.column]

    def _expression(self, expression, tables, aliases, projection_labels=None):
        projection_labels = projection_labels or {}
        if isinstance(expression, FieldRef):
            if expression.alias not in aliases:
                raise QueryValidationError("INVALID_ALIAS", f"Unknown alias '{expression.alias}'")
            return self._column(expression.alias, aliases[expression.alias], expression.name, tables, aliases)
        if isinstance(expression, LiteralValue):
            return bindparam(None, expression.value)
        if isinstance(expression, BinaryExpression):
            left = self._expression(expression.left, tables, aliases, projection_labels)
            right = self._expression(expression.right, tables, aliases, projection_labels)
            return {"=": left == right, "!=": left != right, ">": left > right, ">=": left >= right, "<": left < right, "<=": left <= right}[expression.operator]
        if isinstance(expression, LogicalExpression):
            left = self._expression(expression.left, tables, aliases, projection_labels)
            right = self._expression(expression.right, tables, aliases, projection_labels)
            return and_(left, right) if expression.operator == "AND" else or_(left, right)
        if isinstance(expression, NotExpression):
            return ~self._expression(expression.expression, tables, aliases, projection_labels)
        if isinstance(expression, InExpression):
            return self._expression(expression.field, tables, aliases, projection_labels).in_([self._expression(item, tables, aliases, projection_labels) for item in expression.values])
        if isinstance(expression, LikeExpression):
            return self._expression(expression.field, tables, aliases, projection_labels).like(self._expression(expression.pattern, tables, aliases, projection_labels))
        if isinstance(expression, AggregateExpression):
            argument = func.count() if expression.field is None else self._expression(expression.field, tables, aliases, projection_labels)
            return getattr(func, expression.function.lower())(argument) if expression.function != "COUNT" else (func.count() if expression.field is None else func.count(argument))
        if isinstance(expression, str) and expression in projection_labels:
            return projection_labels[expression]
        raise QueryValidationError("UNSUPPORTED_SQL", "Unsupported validated expression")
