"""Lecture 5: binding and scoping, with let expressions.

Run with `python3 binding.py`. The fragments shown in the slides are taken
from this file, in the order they appear here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

# --- Syntax: the language of Lecture 4, plus names and let -----------------

grammar = r"""
    ?expr: let | arith
    let: "let" IDENTIFIER "=" expr "in" expr
    ?arith: bin | mono
    bin: arith OP mono
    mono: ground | var | paren
    paren: "(" expr ")"
    ground: NUMBER
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    OP: "+" | "-" | "*" | "/" | "%"
    IDENTIFIER: /(?!(let|in)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="expr")


@dataclass(frozen=True)
class Number:
    value: int


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class BinaryExpression:
    op: str
    left: Expression
    right: Expression


@dataclass(frozen=True)
class Let:
    name: str
    definition: Expression
    body: Expression


type Expression = Number | Var | BinaryExpression | Let


def transform_parse_tree(tree: Tree | str) -> Expression:
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="paren", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(data="bin", children=[left, Token(type="OP", value=op), right]):
            return BinaryExpression(
                op=op,
                left=transform_parse_tree(left),
                right=transform_parse_tree(right),
            )
        case Tree(
            data="let",
            children=[Token(type="IDENTIFIER", value=name), definition, body],
        ):
            return Let(
                name=name,
                definition=transform_parse_tree(definition),
                body=transform_parse_tree(body),
            )
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def parse_ast(expression: str) -> Expression:
    try:
        tree = parser.parse(expression)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return transform_parse_tree(tree)


# --- Semantic domains: as in Lecture 4 ---------------------------------------

type EVal = int
type Operator = Callable[[EVal, EVal], EVal]
type DVal = EVal | Operator

type Environment = Callable[[str], DVal]


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


# --- The evaluator: two new cases -------------------------------------------


def evaluate(ast: Expression, env: Environment) -> EVal:
    match ast:
        case Number(value):
            return value
        case Var(name):
            meaning = lookup(env, name)
            if callable(meaning):
                raise ValueError(f"{name} is an operator, not a value")
            return meaning
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if not callable(operator):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env), evaluate(right, env))
        case Let(name, definition, body):
            value = evaluate(definition, env)
            return evaluate(body, bind(env, name, value))


def evaluate_string(expression: str) -> EVal:
    return evaluate(parse_ast(expression), create_initial_env())


# --- Free variables -----------------------------------------------------------


def free_variables(ast: Expression) -> frozenset[str]:
    match ast:
        case Number(_):
            return frozenset()
        case Var(name):
            return frozenset({name})
        case BinaryExpression(_, left, right):
            return free_variables(left) | free_variables(right)
        case Let(name, definition, body):
            return free_variables(definition) | (free_variables(body) - {name})


# --- Trying it out ----------------------------------------------------------


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
    print(parse_ast("let x = 3 in x + 1"))

    for src in [
        "let x = 3 in x + 1",
        "let x = 1 in let y = 2 in x + y",
        "let x = 1 in let y = x + 1 in x * y",
        "let x = 1 in let x = x + 10 in x * 2",
        "(let x = 2 in x * x) + (let x = 3 in x * x)",
        "let x = 5 in (let x = 1 in x) + x",
        "let let1 = 2 in let inside = 3 in let1 * inside",
    ]:
        print(f"{src} = {evaluate_string(src)}")

    for src in [
        "(let x = 1 in x) + x",
        "let x = x + 1 in x",
        "let x = 1 in 2 + let y = 3 in y",
        "let in = 3 in in",
    ]:
        try:
            print(f"{src} = {evaluate_string(src)}")
        except ValueError as e:
            print(f"{src}: {e}")

    # Which names does an expression need from its environment?
    for src in ["x + y", "let x = 1 in x + y", "let x = x in x", "let y = 2 in 3"]:
        print(f"{src}: {sorted(free_variables(parse_ast(src)))}")

    # Uncomment to try it interactively.
    # REPL()
