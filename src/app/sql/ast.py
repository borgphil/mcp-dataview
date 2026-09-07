from dataclasses import dataclass
from typing import Any, Literal

@dataclass(frozen=True)
class FieldRef:
    alias: str
    name: str

@dataclass(frozen=True)
class LiteralValue:
    value: Any

@dataclass(frozen=True)
class BinaryExpression:
    operator: str
    left: Any
    right: Any

@dataclass(frozen=True)
class LogicalExpression:
    operator: Literal["AND", "OR"]
    left: Any
    right: Any

@dataclass(frozen=True)
class NotExpression:
    expression: Any

@dataclass(frozen=True)
class InExpression:
    field: Any
    values: tuple[Any, ...]

@dataclass(frozen=True)
class LikeExpression:
    field: Any
    pattern: Any

@dataclass(frozen=True)
class AggregateExpression:
    function: Literal["COUNT", "SUM", "AVG", "MIN", "MAX"]
    field: FieldRef | None

@dataclass(frozen=True)
class SelectItem:
    expression: Any
    alias: str | None = None

@dataclass(frozen=True)
class JoinSpec:
    source: str
    target: str
    side: Literal["INNER", "LEFT"]

@dataclass(frozen=True)
class OrderSpec:
    expression: Any
    descending: bool

@dataclass(frozen=True)
class RestrictedQueryAst:
    root_view: str
    aliases: tuple[tuple[str, str], ...]
    select: tuple[SelectItem, ...]
    joins: tuple[JoinSpec, ...]
    where: Any | None
    group_by: tuple[FieldRef, ...]
    having: Any | None
    order_by: tuple[OrderSpec, ...]
    distinct: bool
    limit: int | None
    offset: int | None
