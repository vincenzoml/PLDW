"""Extending the language: comparisons.

The precedence grammar of precedence.py gets one more level, below `+` and
`-`, for `<`, `<=` and `==`. The level is non-associative: `1<2<3` is a syntax
error. A comparison gives 1 or 0, so values stay `int`.

Every stage of the pipeline changes a little: the grammar (one level), the
AST (one node), the transformation (one case), the evaluator (one case).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, assert_never

from lark import Lark, Token, Tree

# --- The grammar: one new level ---------------------------------------------

grammar_cmp = r"""
    ?expr: cmp
    ?cmp: sum CMPOP sum    -> compare
        | sum
    ?sum: sum ADDOP prod   -> bin
        | prod
    ?prod: prod MULOP mono -> bin
         | mono
    ?mono: ground | paren
    paren: "(" expr ")"
    ground: NUMBER

    NUMBER: /[0-9]+/
    ADDOP: "+" | "-"
    MULOP: "*" | "/" | "%"
    CMPOP: "<" | "<=" | "=="

    %import common.WS
    %ignore WS
"""

parser_cmp = Lark(grammar_cmp, start="expr")


# --- The AST: one new node --------------------------------------------------

type Op = Literal["+", "-", "*", "/", "%"]
type CmpOp = Literal["<", "<=", "=="]


@dataclass(frozen=True)
class Number:
    value: int


@dataclass(frozen=True)
class BinaryExpression:
    op: Op
    left: Expression
    right: Expression


@dataclass(frozen=True)
class Comparison:
    op: CmpOp
    left: Expression
    right: Expression


type Expression = Number | BinaryExpression | Comparison


# --- The transformation: one new case ---------------------------------------


def transform_cmp(tree: Tree) -> Expression:
    match tree:
        case Tree(data="paren", children=[subtree]):
            return transform_cmp(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(
            data="bin",
            children=[left, Token(value="+" | "-" | "*" | "/" | "%" as op), right],
        ):
            return BinaryExpression(op, transform_cmp(left), transform_cmp(right))
        case Tree(
            data="compare",
            children=[left, Token(value="<" | "<=" | "==" as op), right],
        ):
            return Comparison(op, transform_cmp(left), transform_cmp(right))
        case _:
            raise ValueError(f"Unexpected parse tree node: {tree}")


# --- The evaluator: one new case --------------------------------------------


def arithmetic(op: Op, a: int, b: int) -> int:
    match op:
        case "+":
            return a + b
        case "-":
            return a - b
        case "*":
            return a * b
        case "/" | "%" if b == 0:
            raise ValueError("Division by zero")
        case "/":
            return a // b
        case "%":
            return a % b
        case _:
            assert_never(op)


def evaluate(ast: Expression) -> int:
    match ast:
        case Number(value):
            return value
        case BinaryExpression(op, left, right):
            return arithmetic(op, evaluate(left), evaluate(right))
        case Comparison(op, left, right):
            a, b = evaluate(left), evaluate(right)
            match op:
                case "<":
                    return int(a < b)
                case "<=":
                    return int(a <= b)
                case "==":
                    return int(a == b)
                case _:
                    assert_never(op)
        case _:
            assert_never(ast)


def evaluate_cmp(expression: str) -> int:
    return evaluate(transform_cmp(parser_cmp.parse(expression)))


if __name__ == "__main__":
    print(transform_cmp(parser_cmp.parse("1+2 <= 3")))
    print(evaluate_cmp("1+2*3 < 10"))       # 1
    print(evaluate_cmp("2*2 == 5"))         # 0
    print(evaluate_cmp("(1<2) + (2<1)"))    # 1
    try:
        evaluate_cmp("1 < 2 < 3")
    except Exception as e:
        print(f"{type(e).__name__}: {str(e).splitlines()[0]}")
