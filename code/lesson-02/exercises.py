"""Lecture 2: the exercises.

Write your solutions in place of `raise NotImplementedError`. Running the file
tells you which exercises give the results shown on the slides.

Run:    python3 exercises.py
Check:  python3 -m mypy exercises.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import assert_never

from expressions import BinaryOp, Expr, Number, Variable, evaluate

# ================================================================ exercise 1
# Print a tree: show(expr) returns the expression as a string, with
# parentheses around every operation.
# One case per kind of node; an f-string for BinaryOp. End with
# case _: assert_never(expr), and run mypy: no errors.


def show(expr: Expr) -> str:
    raise NotImplementedError


# ================================================================ exercise 2
# Adding a node: Negate, the negation -e. This one is done in expressions.py
# itself (work in a copy):
#
#   @dataclass(frozen=True)
#   class Negate:
#       operand: Expr
#
#   type Expr = Number | Variable | BinaryOp | Negate
#
# Run mypy before touching any function, and write down what it reports.
# Fix each function it names, starting with evaluate and your show.
# In Python, -v is the negation of v. Expected:
#   evaluate(Negate(Variable("x")), {"x": 4.0})  ->  -4.0
#   evaluate(Negate(Negate(Number(3.0))), {})    ->  3.0

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
# For BinaryOp, a nested match on the operator. For "/", raise a ValueError:
# division is not supported. End with assert_never and run mypy.


def derive(expr: Expr, x: str) -> Expr:
    raise NotImplementedError


# ================================================================ checks
# The examples of the slides. Each exercise is "ok" when all its examples
# give the expected result.

e = BinaryOp(Number(2.0), "+", BinaryOp(Variable("x"), "*", Number(3.0)))
left_first = BinaryOp(BinaryOp(Number(10.0), "-", Number(4.0)), "-", Number(3.0))
X = Variable("x")


def check(name: str, test: object) -> None:
    try:
        assert callable(test)
        test()
        print(f"{name}: ok")
    except NotImplementedError:
        print(f"{name}: not written yet")
    except AssertionError:
        print(f"{name}: a result is not the expected one")


def exercise_1() -> None:
    assert show(e) == "(2.0 + (x * 3.0))"
    assert show(Number(7.0)) == "7.0"
    assert show(left_first) == "((10.0 - 4.0) - 3.0)"


def exercise_3() -> None:
    assert show(derive(BinaryOp(X, "+", Number(5.0)), "x")) == "(1.0 + 0.0)"
    assert show(derive(BinaryOp(Number(3.0), "*", X), "x")) == "((0.0 * x) + (3.0 * 1.0))"
    sq = BinaryOp(X, "*", X)
    assert show(derive(sq, "x")) == "((1.0 * x) + (x * 1.0))"
    assert evaluate(derive(sq, "x"), {"x": 3.0}) == 6.0



if __name__ == "__main__":
    check("exercise 1", exercise_1)
    check("exercise 3", exercise_3)
