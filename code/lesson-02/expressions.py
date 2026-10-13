"""Lecture 2: types and pattern matching.

Arithmetic expressions as a tree of dataclasses, an evaluator and a simplifier
written with match. There is no parser yet: the trees are built by hand.

Run:    python3 expressions.py
Check:  python3 -m mypy expressions.py   (pip install mypy)
Python 3.12 or later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, assert_never

# ---------------------------------------------------------------- the types
# One dataclass per kind of node. frozen=True: a node cannot be changed after
# it is built, and the checker reports any assignment to one of its fields.

# The operators: a union of four constants. A wrong operator, such as "^",
# is reported by the checker where the tree is built.
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


# An expression is one of these three kinds of node: a closed list, so the
# checker can tell when a match forgets one of them.
type Expr = Number | Variable | BinaryOp

# The environment gives a value to each variable.
type Env = dict[str, float]

# ---------------------------------------------------------------- evaluate
# One case per kind of node. For BinaryOp, the children are evaluated first,
# then a nested match on the operator.
# assert_never: its parameter has type Never, the type with no values, so the
# call type-checks only if the cases above cover every alternative. If a case
# is missing, mypy reports it and names it. At run time it raises an error.


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
        case _:
            assert_never(expr)


# ---------------------------------------------------------------- simplify
# A second function on the same tree, to show nested patterns.
# The first three cases are the rules 0 + e = e, 1 * e = e, 0 * e = 0;
# "|" is an or-pattern: either alternative, binding the same names.
# The fourth case computes an operation between two numbers. Its guard,
# after "if", leaves 1 / 0 unchanged.
# Cases are tried from top to bottom: the general BinaryOp case must come
# after the specific ones. One pass only: a rule that becomes applicable after
# the children are simplified is not tried again.


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
        case Number() | Variable():
            return expr
        case _:
            assert_never(expr)


# ---------------------------------------------------------------- examples

if __name__ == "__main__":
    # 2 + (x * 3)
    e = BinaryOp(Number(2.0), "+", BinaryOp(Variable("x"), "*", Number(3.0)))

    print(e)
    # BinaryOp(left=Number(value=2.0), operator='+', right=BinaryOp(...))

    print(Number(2.0) == Number(2.0))  # True: equality compares the fields

    print(evaluate(e, {"x": 4.0}))  # 14.0

    try:
        evaluate(e, {})
    except NameError as err:
        print("NameError:", err)  # variable 'x' is not defined

    # 10 - 4 - 3, read left to right: (10 - 4) - 3
    left_first = BinaryOp(BinaryOp(Number(10.0), "-", Number(4.0)), "-", Number(3.0))
    print(evaluate(left_first, {}))  # 3.0

    # frozen=True: a node cannot be changed after it is built
    try:
        e.operator = "-"  # type: ignore[misc]  # mypy would report this line
    except AttributeError as err:
        print("AttributeError:", err)

    # simplify, the two examples of the slides
    print(simplify(BinaryOp(Number(0.0), "+", BinaryOp(Variable("x"), "*", Number(1.0)))))
    # Variable(name='x')
    print(simplify(BinaryOp(BinaryOp(Number(2.0), "+", Number(3.0)), "*", Variable("y"))))
    # BinaryOp(left=Number(value=5.0), operator='*', right=Variable(name='y'))
