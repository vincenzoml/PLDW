"""Lecture 3, exercise 6: a language for sets of integers written as intervals, a solution.

    [1, 4] | [3, 8]     union
    [1, 4] & [3, 8]     intersection

[a, b] is the set of integers from a to b, both included. & binds tighter than |.

A value is an ordered list of intervals, list[tuple[int, int]], always kept in
normal form: sorted, and with no two intervals that overlap or touch.
[1, 5] | [6, 8] is [(1, 8)]: as sets of integers, 1..5 and 6..8 together are 1..8.

Run:    python3 intervals.py
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
    ?atom: interval | paren
    paren: "(" expr ")"
    interval: "[" NUMBER "," NUMBER "]"

    NUMBER: /[0-9]+/
    UNIONOP: "|"
    INTEROP: "&"

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="expr")

# --- The AST ----------------------------------------------------------------

type Op = Literal["|", "&"]


@dataclass(frozen=True)
class Interval:
    low: int
    high: int


@dataclass(frozen=True)
class BinaryExpression:
    op: Op
    left: Expression
    right: Expression


type Expression = Interval | BinaryExpression

# --- From the parse tree to the AST -----------------------------------------


def transform(tree: Tree | str) -> Expression:
    match tree:
        case Tree(data="paren", children=[subtree]):
            return transform(subtree)
        case Tree(data="interval", children=[Token(value=low), Token(value=high)]):
            if int(low) > int(high):
                raise ValueError(f"empty interval [{low}, {high}]: {low} > {high}")
            return Interval(int(low), int(high))
        case Tree(data="bin", children=[left, Token(value="|" | "&" as op), right]):
            return BinaryExpression(op, transform(left), transform(right))
        case _:
            raise ValueError(f"Unexpected parse tree node: {tree}")


# --- The values: ordered lists of intervals ---------------------------------

type Value = list[tuple[int, int]]


def normalize(intervals: Value) -> Value:
    """Sort, then merge the intervals that overlap or touch."""
    result: Value = []
    for low, high in sorted(intervals):
        if result != [] and low <= result[-1][1] + 1:
            last_low, last_high = result[-1]
            result[-1] = (last_low, max(last_high, high))
        else:
            result.append((low, high))
    return result


def union(a: Value, b: Value) -> Value:
    return normalize(a + b)


def intersection(a: Value, b: Value) -> Value:
    """Every interval of a with every interval of b; simple, not fast."""
    pieces = []
    for low1, high1 in a:
        for low2, high2 in b:
            low, high = max(low1, low2), min(high1, high2)
            if low <= high:
                pieces.append((low, high))
    return normalize(pieces)


# --- Evaluation -------------------------------------------------------------


def evaluate(ast: Expression) -> Value:
    match ast:
        case Interval(low, high):
            return [(low, high)]
        case BinaryExpression(op, left, right):
            left_value = evaluate(left)
            right_value = evaluate(right)
            match op:
                case "|":
                    return union(left_value, right_value)
                case "&":
                    return intersection(left_value, right_value)
                case _:
                    assert_never(op)
        case _:
            assert_never(ast)


def run(text: str) -> Value:
    try:
        tree = parser.parse(text)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return evaluate(transform(tree))


if __name__ == "__main__":
    assert run("[1, 4] | [3, 8]") == [(1, 8)]
    assert run("[1, 4] & [3, 8]") == [(3, 4)]
    assert run("[1, 4] | [3, 8] & [6, 10]") == [(1, 4), (6, 8)]
    assert run("([1, 4] | [3, 8]) & [6, 10]") == [(6, 8)]
    assert run("[1, 5] | [6, 8]") == [(1, 8)]
    assert run("[1, 2] & [5, 6]") == []
    assert run("[7, 9] | [1, 2] | [4, 4]") == [(1, 2), (4, 4), (7, 9)]
    assert run("([1, 3] | [6, 9]) & ([2, 7] | [9, 12])") == [(2, 3), (6, 7), (9, 9)]
    for bad in ["[5, 1]", "[1, 2", "[1, 2] - [3, 4]"]:
        try:
            run(bad)
            raise AssertionError(bad)
        except ValueError as e:
            print(f"{bad!r}: {e}")
    print("all examples check")
