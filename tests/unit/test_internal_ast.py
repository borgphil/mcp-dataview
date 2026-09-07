from app.main import service
from app.sql.ast import AggregateExpression, BinaryExpression, FieldRef, JoinSpec, LiteralValue


def test_validation_produces_internal_ast_without_parser_nodes():
    plan = service.validate("SELECT c.id, COUNT(*) AS total FROM customers c GROUP BY c.id HAVING COUNT(*) > 0")
    assert isinstance(plan.ast.select[0].expression, FieldRef)
    assert isinstance(plan.ast.select[1].expression, AggregateExpression)
    assert isinstance(plan.ast.having, BinaryExpression)
    assert isinstance(plan.ast.having.right, LiteralValue)


def test_relationships_are_represented_as_trusted_join_specs():
    plan = service.validate("SELECT c.id FROM customers c LEFT JOIN investments i")
    assert plan.ast.joins == (JoinSpec("customers", "investments", "LEFT"),)
