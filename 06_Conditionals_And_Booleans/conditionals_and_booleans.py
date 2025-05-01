"""
Lecture 6: Conditionals and Booleans
Extends the mini-language with boolean expressions and conditional (if-then-else) expressions.
Follows the style and naming conventions of previous lectures.
"""

from dataclasses import dataclass
from typing import Callable, Union


# --- AST Nodes ---
@dataclass
class Number:
    value: int


@dataclass
class Boolean:
    value: bool


@dataclass
class Var:
    name: str


@dataclass
class Let:
    name: str
    expr: "Expression"
    body: "Expression"


@dataclass
class BinOp:
    op: str  # '+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=' , 'and', 'or'
    left: "Expression"
    right: "Expression"


@dataclass
class If:
    cond: "Expression"
    then_branch: "Expression"
    else_branch: "Expression"


Expression = Union[Number, Boolean, Var, Let, BinOp, If]


# --- Parser (very simple, for demonstration) ---
def parse(expr):
    """
    Dummy parser for demonstration. In a real scenario, use a proper parser.
    Accepts nested tuples representing the AST.
    """
    if isinstance(expr, int):
        return Number(expr)
    if isinstance(expr, bool):
        return Boolean(expr)
    if isinstance(expr, str):
        return Var(expr)
    if isinstance(expr, tuple):
        tag = expr[0]
        if tag == "let":
            _, name, value_expr, body_expr = expr
            return Let(name, parse(value_expr), parse(body_expr))
        if tag == "if":
            _, cond, then_branch, else_branch = expr
            return If(parse(cond), parse(then_branch), parse(else_branch))
        if tag in {"+", "-", "*", "/", "==", "!=", "<", ">", "<=", ">=", "and", "or"}:
            _, left, right = expr
            return BinOp(tag, parse(left), parse(right))
    raise ValueError(f"Cannot parse: {expr}")


# --- Environment and Binding ---
DVal = Union[int, bool]
Environment = Callable[[str], DVal]


def empty_env(name: str) -> DVal:
    raise NameError(f"Unbound variable: {name}")


def bind(env: Environment, name: str, value: DVal) -> Environment:
    return lambda n: value if n == name else env(n)


# --- Evaluation ---
def eval_expr(expr: Expression, env: Environment) -> DVal:
    if isinstance(expr, Number):
        return expr.value
    if isinstance(expr, Boolean):
        return expr.value
    if isinstance(expr, Var):
        return env(expr.name)
    if isinstance(expr, Let):
        value = eval_expr(expr.expr, env)
        extended_env = bind(env, expr.name, value)
        return eval_expr(expr.body, extended_env)
    if isinstance(expr, BinOp):
        # Short-circuit for 'and' and 'or'
        if expr.op == "and":
            left = eval_expr(expr.left, env)
            if not left:
                return False  # short-circuit
            return bool(eval_expr(expr.right, env))
        if expr.op == "or":
            left = eval_expr(expr.left, env)
            if left:
                return True  # short-circuit
            return bool(eval_expr(expr.right, env))
        left = eval_expr(expr.left, env)
        right = eval_expr(expr.right, env)
        if expr.op == "+":
            return left + right
        if expr.op == "-":
            return left - right
        if expr.op == "*":
            return left * right
        if expr.op == "/":
            return left // right  # integer division
        if expr.op == "==":
            return left == right
        if expr.op == "!=":
            return left != right
        if expr.op == "<":
            return left < right
        if expr.op == ">":
            return left > right
        if expr.op == "<=":
            return left <= right
        if expr.op == ">=":
            return left >= right
        raise ValueError(f"Unknown operator: {expr.op}")
    if isinstance(expr, If):
        cond = eval_expr(expr.cond, env)
        if cond:
            return eval_expr(expr.then_branch, env)
        else:
            return eval_expr(expr.else_branch, env)
    raise ValueError(f"Unknown expression: {expr}")


# --- Examples ---
if __name__ == "__main__":
    # Example 1: let x = 10 in if x > 5 then x else 0
    ast1 = parse(("let", "x", 10, ("if", (">", "x", 5), "x", 0)))
    print("Example 1 result:", eval_expr(ast1, empty_env))

    # Example 2: let x = 3 in let y = 4 in if (x < y) and (y < 10) then x + y else 0
    ast2 = parse(
        (
            "let",
            "x",
            3,
            (
                "let",
                "y",
                4,
                ("if", ("and", ("<", "x", "y"), ("<", "y", 10)), ("+", "x", "y"), 0),
            ),
        )
    )
    print("Example 2 result:", eval_expr(ast2, empty_env))

    # Example 3: let x = 0 in if (x != 0) and (10 // x > 1) then 1 else 2 (should short-circuit and not error)
    ast3 = parse(
        ("let", "x", 0, ("if", ("and", ("!=", "x", 0), (">", ("/", 10, "x"), 1)), 1, 2))
    )
    print("Example 3 result:", eval_expr(ast3, empty_env))
