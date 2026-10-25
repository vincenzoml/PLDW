"""Lecture 4: semantic domains and an environment-based evaluator.

Run with `python3 domains.py`. The fragments shown in the slides are taken
from this file, in the order they appear here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree

# --- Syntax: same language as chapter 3 ------------------------------------

grammar = r"""
    ?expr: bin | mono
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


@dataclass(frozen=True)
class Number:
    value: int


@dataclass(frozen=True)
class BinaryExpression:
    op: str
    left: Expression
    right: Expression


type Expression = Number | BinaryExpression


def transform_parse_tree(tree: Tree | str) -> Expression:
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="paren", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(data="bin", children=[left, Token(type="OP", value=op), right]):
            return BinaryExpression(
                op=op,
                left=transform_parse_tree(left),
                right=transform_parse_tree(right),
            )
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def parse_ast(expression: str) -> Expression:
    return transform_parse_tree(parser.parse(expression))


# --- Semantic domains -------------------------------------------------------

type EVal = int  # expressible values: what an expression can evaluate to
type Operator = Callable[[EVal, EVal], EVal]
type DVal = EVal | Operator  # denotable values: what a name can stand for

type Environment = Callable[[str], DVal]


# --- The environment as a function -----------------------------------------


def empty_environment() -> Environment:
    def env(name: str) -> DVal:
        raise ValueError(f"Undefined identifier: {name}")

    return env


def lookup(env: Environment, name: str) -> DVal:
    return env(name)


def bind(env: Environment, name: str, value: DVal) -> Environment:
    def new_env(n: str) -> DVal:
        if n == name:
            return value
        return env(n)

    return new_env


# --- Operators, and the initial environment --------------------------------


def add(x: int, y: int) -> int:
    return x + y


def subtract(x: int, y: int) -> int:
    return x - y


def multiply(x: int, y: int) -> int:
    return x * y


def divide(x: int, y: int) -> int:
    if y == 0:
        raise ValueError("Division by zero")
    return x // y


def modulo(x: int, y: int) -> int:
    if y == 0:
        raise ValueError("Division by zero")
    return x % y


def create_initial_env() -> Environment:
    env = empty_environment()
    env = bind(env, "+", add)
    env = bind(env, "-", subtract)
    env = bind(env, "*", multiply)
    env = bind(env, "/", divide)
    env = bind(env, "%", modulo)
    return env


# --- The evaluator ----------------------------------------------------------


def evaluate(ast: Expression, env: Environment) -> EVal:
    match ast:
        case Number(value):
            return value
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if not callable(operator):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env), evaluate(right, env))


def evaluate_string(expression: str) -> EVal:
    return evaluate(parse_ast(expression), create_initial_env())


# --- Trying it out ----------------------------------------------------------


def power(x: int, y: int) -> int:
    return x**y


def REPL() -> None:
    env = create_initial_env()
    while True:
        expression = input("Enter an expression (exit to quit): ")
        if expression == "exit":
            break
        try:
            print(evaluate(parse_ast(expression), env))
        except Exception as e:
            print(e)


if __name__ == "__main__":
    env = create_initial_env()
    print(lookup(env, "+"))
    times = lookup(env, "*")
    if callable(times):
        print(times(6, 7))
    try:
        lookup(env, "x")
    except ValueError as e:
        print(e)

    for src in ["1+2", "(1+2)*3", "10/(2+3)", "10%(2+3)"]:
        print(f"{src} = {evaluate_string(src)}")

    try:
        evaluate_string("10/0")
    except ValueError as e:
        print(e)

    # The same syntax tree, evaluated in two different environments.
    ast = parse_ast("2*3")
    print(evaluate(ast, env))
    print(evaluate(ast, bind(env, "*", power)))

    # An operator the grammar accepts but the environment does not know.
    try:
        evaluate(parse_ast("2-3"), bind(empty_environment(), "+", add))
    except ValueError as e:
        print(e)

    # Uncomment to try it interactively.
    # REPL()
