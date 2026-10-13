"""Lecture 2: the exercises, with solutions.

Self-contained: it repeats the types, evaluate and simplify of expressions.py,
already extended with Negate (exercise 2). Every example on the exercise slides
is checked with assert.

Run:    python3 solutions.py
Check:  python3 -m mypy solutions.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, assert_never

# ================================================================ the types
# The types, evaluate and simplify of expressions.py, already with the
# changes of exercise 2 (marked "exercise 2").

type Op = Literal["+", "-", "*", "/"]


@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class Variable:
    name: str


@dataclass(frozen=True)
class BinaryOp:
    left: Expr
    operator: Op
    right: Expr


@dataclass(frozen=True)
class Negate:
    operand: Expr


type Expr = Number | Variable | BinaryOp | Negate
type Env = dict[str, float]


def evaluate(expr: Expr, env: Env) -> float:
    match expr:
        case Number(value):
            return value
        case Variable(name):
            if name not in env:
                raise NameError(f"variable '{name}' is not defined")
            return env[name]
        case BinaryOp(left, operator, right):
            lv = evaluate(left, env)
            rv = evaluate(right, env)
            match operator:
                case "+":
                    return lv + rv
                case "-":
                    return lv - rv
                case "*":
                    return lv * rv
                case "/":
                    return lv / rv
                case _:
                    assert_never(operator)
        case Negate(operand):  # exercise 2
            return -evaluate(operand, env)
        case _:
            assert_never(expr)


def simplify(expr: Expr) -> Expr:
    match expr:
        case BinaryOp(Number(0), "+", other) | BinaryOp(other, "+", Number(0)):
            return simplify(other)
        case BinaryOp(Number(1), "*", other) | BinaryOp(other, "*", Number(1)):
            return simplify(other)
        case BinaryOp(Number(0), "*", _) | BinaryOp(_, "*", Number(0)):
            return Number(0.0)
        case BinaryOp(Number(a), operator, Number(b)) if operator != "/" or b != 0:
            return Number(evaluate(expr, {}))
        case BinaryOp(left, operator, right):
            return BinaryOp(simplify(left), operator, simplify(right))
        case Negate(operand):  # exercise 2: mypy asks for this case
            return Negate(simplify(operand))
        case Number() | Variable():
            return expr
        case _:
            assert_never(expr)


e = BinaryOp(Number(2.0), "+", BinaryOp(Variable("x"), "*", Number(3.0)))
left_first = BinaryOp(BinaryOp(Number(10.0), "-", Number(4.0)), "-", Number(3.0))

# ================================================================ exercise 1
# Print a tree: show(expr) returns the expression as a string, with
# parentheses around every operation.
# One case per kind of node, as in evaluate. For BinaryOp, show calls itself
# on the two children and joins the results with an f-string.


def show(expr: Expr) -> str:
    match expr:
        case Number(value):
            return str(value)
        case Variable(name):
            return name
        case BinaryOp(left, operator, right):
            return f"({show(left)} {operator} {show(right)})"
        case Negate(operand):  # exercise 2
            return f"(-{show(operand)})"
        case _:
            assert_never(expr)


assert show(e) == "(2.0 + (x * 3.0))"
assert show(Number(7.0)) == "7.0"
assert show(left_first) == "((10.0 - 4.0) - 3.0)"

# ================================================================ exercise 2
# Adding a node: Negate, the negation -e.
# Add the dataclass and add it to the union Expr. Before changing any
# function, run mypy: every function that ends with assert_never(expr) is
# reported, because Negate can now reach it. Here: evaluate, simplify, show,
# and derive below. Each one gets a case for Negate.

assert evaluate(Negate(Variable("x")), {"x": 4.0}) == -4.0
assert evaluate(Negate(Negate(Number(3.0))), {}) == 3.0
assert show(Negate(Variable("x"))) == "(-x)"

# ================================================================ exercise 3
# Derivatives. derive(expr, x) builds the tree of the derivative with respect
# to the variable x. It computes no number: it applies one rule per kind of
# node, and the result is not simplified.
#   d/dx c     = 0                 a number
#   d/dx x     = 1
#   d/dx y     = 0                 another variable
#   d/dx f + g = f' + g'
#   d/dx f - g = f' - g'
#   d/dx f * g = f' * g + f * g'
# f' and g' are the derivatives of the children: recursive calls, as in
# evaluate. Division is not supported: ValueError.


def derive(expr: Expr, x: str) -> Expr:
    match expr:
        case Number():
            return Number(0.0)
        case Variable(name):
            return Number(1.0) if name == x else Number(0.0)
        case BinaryOp(f, operator, g):
            match operator:
                case "+" | "-":
                    return BinaryOp(derive(f, x), operator, derive(g, x))
                case "*":
                    return BinaryOp(
                        BinaryOp(derive(f, x), "*", g), "+", BinaryOp(f, "*", derive(g, x))
                    )
                case "/":
                    raise ValueError("division is not supported")
                case _:
                    assert_never(operator)
        case Negate(f):  # exercise 2 reaches here too: d/dx -f = -f'
            return Negate(derive(f, x))
        case _:
            assert_never(expr)


X = Variable("x")
assert show(derive(BinaryOp(X, "+", Number(5.0)), "x")) == "(1.0 + 0.0)"
assert show(derive(BinaryOp(Number(3.0), "*", X), "x")) == "((0.0 * x) + (3.0 * 1.0))"
sq = BinaryOp(X, "*", X)
assert show(derive(sq, "x")) == "((1.0 * x) + (x * 1.0))"
assert evaluate(derive(sq, "x"), {"x": 3.0}) == 6.0
try:
    derive(BinaryOp(X, "/", Number(2.0)), "x")
    raise AssertionError("expected ValueError")
except ValueError:
    pass

if __name__ == "__main__":
    print(show(e))
    print(show(derive(sq, "x")))
    print("all checks passed")
