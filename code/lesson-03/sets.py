"""Lecture 3, exercise 5: a language for sets of integers, a solution.

    {1, 2, 3} | {3, 4}       union
    {1, 2, 3} & {2, 3, 4}    intersection
    {1, 2, 3} - {2}          difference

& binds tighter than | and -, which group from left to right.
Values are frozenset[int]; Python's sets do the computing.

Run:    python3 sets.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, assert_never

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

# --- The grammar ------------------------------------------------------------

grammar = r"""
    ?expr: expr UNIONOP inter -> bin
         | inter
    ?inter: inter INTEROP atom -> bin
          | atom
    ?atom: set | paren
    paren: "(" expr ")"
    set: "{" (NUMBER ("," NUMBER)*)? "}"

    NUMBER: /[0-9]+/
    UNIONOP: "|" | "-"
    INTEROP: "&"

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="expr")

# --- The AST ----------------------------------------------------------------

type Op = Literal["|", "&", "-"]


@dataclass(frozen=True)
class SetLiteral:
    elements: frozenset[int]


@dataclass(frozen=True)
class BinaryExpression:
    op: Op
    left: Expression
    right: Expression


type Expression = SetLiteral | BinaryExpression

# --- From the parse tree to the AST -----------------------------------------


def transform(tree: Tree | str) -> Expression:
    match tree:
        case Tree(data="paren", children=[subtree]):
            return transform(subtree)
        case Tree(data="set", children=numbers):
            return SetLiteral(frozenset(int(n) for n in numbers if isinstance(n, Token)))
        case Tree(data="bin", children=[left, Token(value="|" | "&" | "-" as op), right]):
            return BinaryExpression(op, transform(left), transform(right))
        case _:
            raise ValueError(f"Unexpected parse tree node: {tree}")


# --- Evaluation -------------------------------------------------------------


def evaluate(ast: Expression) -> frozenset[int]:
    match ast:
        case SetLiteral(elements):
            return elements
        case BinaryExpression(op, left, right):
            left_value = evaluate(left)
            right_value = evaluate(right)
            match op:
                case "|":
                    return left_value | right_value
                case "&":
                    return left_value & right_value
                case "-":
                    return left_value - right_value
                case _:
                    assert_never(op)
        case _:
            assert_never(ast)


def show(value: frozenset[int]) -> str:
    return "{" + ", ".join(str(n) for n in sorted(value)) + "}"


def run(text: str) -> str:
    try:
        tree = parser.parse(text)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return show(evaluate(transform(tree)))


if __name__ == "__main__":
    assert run("{1, 2, 3} | {3, 4}") == "{1, 2, 3, 4}"
    assert run("{1, 2, 3} & {2, 3, 4}") == "{2, 3}"
    assert run("{1, 2, 3} - {2}") == "{1, 3}"
    assert run("{1, 2} | {3} & {3, 4}") == "{1, 2, 3}"
    assert run("({1, 2} | {3}) & {3, 4}") == "{3}"
    assert run("{1, 2, 3} - {1} - {2}") == "{3}"
    assert run("{} - {1}") == "{}"
    assert run("{3, 1, 1}") == "{1, 3}"
    for bad in ["{1, 2", "{1,, 2}", "{1} + {2}"]:
        try:
            run(bad)
            raise AssertionError(bad)
        except ValueError as e:
            print(f"{bad!r}: {e}")
    print("all examples check")
