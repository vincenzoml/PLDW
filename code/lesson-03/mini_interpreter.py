"""A mini interpreter for arithmetic expressions.

Pipeline: text -> tokens -> parse tree (Lark) -> AST (our dataclasses) -> value.

Run with `python3 mini_interpreter.py`: it prints the examples used in the
chapter, then starts the REPL if standard input is a terminal.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Literal, assert_never

from lark import Lark, Token, Tree

# --- The grammar ------------------------------------------------------------

grammar = r"""
    expr: bin | mono
    mono: ground | paren
    paren: "(" expr ")"
    bin: expr OP mono
    ground: NUMBER

    NUMBER: /[0-9]+/
    OP: "+" | "-" | "*" | "/" | "%"

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="expr")


# --- The AST ----------------------------------------------------------------

type Op = Literal["+", "-", "*", "/", "%"]


@dataclass(frozen=True)
class Number:
    value: int


@dataclass(frozen=True)
class BinaryExpression:
    op: Op
    left: Expression
    right: Expression


type Expression = Number | BinaryExpression


# --- From the parse tree to the AST -----------------------------------------


def transform_parse_tree(tree: Tree) -> Expression:
    match tree:
        case Tree(data="expr", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="mono", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="paren", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(
            data="bin",
            children=[
                left,
                Token(type="OP", value="+" | "-" | "*" | "/" | "%" as op),
                right,
            ],
        ):
            return BinaryExpression(
                op=op,
                left=transform_parse_tree(left),
                right=transform_parse_tree(right),
            )
        case _:
            raise ValueError(f"Unexpected parse tree node: {tree}")


def parse_ast(expression: str) -> Expression:
    parse_tree = parser.parse(expression)
    return transform_parse_tree(parse_tree)


# --- Evaluation -------------------------------------------------------------


def evaluate(ast: Expression) -> int:
    match ast:
        case Number(value):
            return value
        case BinaryExpression(op, left, right):
            left_value = evaluate(left)
            right_value = evaluate(right)
            match op:
                case "+":
                    return left_value + right_value
                case "-":
                    return left_value - right_value
                case "*":
                    return left_value * right_value
                case "/":
                    if right_value == 0:
                        raise ValueError("Division by zero")
                    return left_value // right_value
                case "%":
                    if right_value == 0:
                        raise ValueError("Division by zero")
                    return left_value % right_value
                case _:
                    assert_never(op)
        case _:
            assert_never(ast)


def evaluate_string(expression: str) -> int:
    return evaluate(parse_ast(expression))


# --- The REPL ---------------------------------------------------------------


def REPL() -> None:
    while True:
        try:
            expression = input("> ")
        except EOFError:
            print()
            return
        if expression == "exit":
            return
        try:
            print(evaluate_string(expression))
        except Exception as e:
            print(f"Error: {e}")


# --- Examples used in the chapter -------------------------------------------


def main() -> None:
    parse_tree = parser.parse("(1 + 2) - 3")
    print(parse_tree.pretty())
    print(repr(parse_tree))
    print(list(parser.lex("(1 + 2) - 3")))

    for bad in ["1 +", "1 ++ 2", "-1"]:
        try:
            parser.parse(bad)
        except Exception as e:
            print(f"{bad!r}: {type(e).__name__}: {str(e).splitlines()[0]}")

    print(parse_ast("(1+2)-3"))
    print(parse_ast("1"))

    print(evaluate(parse_ast("(1+2)-3")))
    print(evaluate_string("(1+2)*3"))
    print(evaluate_string("7/2"), evaluate_string("(0-7)/2"), evaluate_string("(0-7)%2"))
    try:
        evaluate_string("1/(2-2)")
    except ValueError as e:
        print(f"ValueError: {e}")

    print(parser.parse("1+2*3").pretty())
    print(parse_ast("1+2*3"))
    print(evaluate_string("1+2*3"))
    print(evaluate_string("10-4-3"))


if __name__ == "__main__":
    main()
    if sys.stdin.isatty():
        REPL()
