"""Lecture 5, exercise 4: a language for composing text.

A solution. The values are strings and integers; `let` and the environment
are those of binding.py, and the primitives on text are names in the initial
environment, like the operators.

Run with `python3 text.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

grammar = r"""
    ?expr: let | arith
    let: "let" IDENTIFIER "=" expr "in" expr
    ?arith: bin | post
    bin: arith OP post
    ?post: slice | mono
    slice: post "[" expr ":" expr "]"
    mono: text | ground | var | paren | call
    paren: "(" expr ")"
    call: IDENTIFIER "(" expr ")"
    text: STRING
    ground: NUMBER
    var: IDENTIFIER

    STRING: /"[^"]*"/
    NUMBER: /[0-9]+/
    OP: "+" | "*"
    IDENTIFIER: /(?!(let|in)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="expr")


@dataclass(frozen=True)
class Text:
    value: str


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
class Call:
    name: str
    argument: Expression


@dataclass(frozen=True)
class Slice:
    text: Expression
    start: Expression
    stop: Expression


@dataclass(frozen=True)
class Let:
    name: str
    definition: Expression
    body: Expression


type Expression = Text | Number | Var | BinaryExpression | Call | Slice | Let


def transform_parse_tree(tree: Tree | str) -> Expression:
    match tree:
        case Tree(data="mono" | "paren", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="text", children=[Token(type="STRING", value=quoted)]):
            return Text(value=quoted[1:-1])
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(data="bin", children=[left, Token(type="OP", value=op), right]):
            return BinaryExpression(
                op, transform_parse_tree(left), transform_parse_tree(right)
            )
        case Tree(data="call", children=[Token(type="IDENTIFIER", value=name), arg]):
            return Call(name, transform_parse_tree(arg))
        case Tree(data="slice", children=[text, start, stop]):
            return Slice(
                transform_parse_tree(text),
                transform_parse_tree(start),
                transform_parse_tree(stop),
            )
        case Tree(
            data="let",
            children=[Token(type="IDENTIFIER", value=name), definition, body],
        ):
            return Let(name, transform_parse_tree(definition), transform_parse_tree(body))
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def parse_ast(expression: str) -> Expression:
    try:
        tree = parser.parse(expression)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return transform_parse_tree(tree)


# --- Semantic domains ---------------------------------------------------------

type EVal = str | int
type Operator = Callable[[EVal, EVal], EVal]
type Primitive = Callable[[EVal], EVal]


@dataclass(frozen=True)
class Unary:
    """A primitive of one argument. Wrapped, so that it can be told apart from
    an operator of two arguments: both are callable."""

    apply: Primitive


type DVal = EVal | Operator | Unary
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


# --- Primitives -----------------------------------------------------------------


def as_text(v: EVal, where: str) -> str:
    if not isinstance(v, str):
        raise ValueError(f"{where}: expected a text, got the number {v}")
    return v


def as_number(v: EVal, where: str) -> int:
    if not isinstance(v, int):
        raise ValueError(f"{where}: expected a number, got the text {v!r}")
    return v


def concat(x: EVal, y: EVal) -> EVal:
    if isinstance(x, int) and isinstance(y, int):
        return x + y
    return as_text(x, "+") + as_text(y, "+")


def repeat(x: EVal, y: EVal) -> EVal:
    if isinstance(x, int) and isinstance(y, int):
        return x * y
    return as_text(x, "*") * as_number(y, "*")


def reverse(x: EVal) -> EVal:
    return as_text(x, "reverse")[::-1]


def upper(x: EVal) -> EVal:
    return as_text(x, "upper").upper()


def lower(x: EVal) -> EVal:
    return as_text(x, "lower").lower()


def length(x: EVal) -> EVal:
    return len(as_text(x, "length"))


def create_initial_env() -> Environment:
    env = empty_environment()
    env = bind(env, "+", concat)
    env = bind(env, "*", repeat)
    env = bind(env, "reverse", Unary(reverse))
    env = bind(env, "upper", Unary(upper))
    env = bind(env, "lower", Unary(lower))
    env = bind(env, "length", Unary(length))
    env = bind(env, "nl", "\n")
    return env


# --- The evaluator ------------------------------------------------------------


def evaluate(ast: Expression, env: Environment) -> EVal:
    match ast:
        case Text(value):
            return value
        case Number(value):
            return value
        case Var(name):
            meaning = lookup(env, name)
            if callable(meaning) or isinstance(meaning, Unary):
                raise ValueError(f"{name} is an operation, not a value")
            return meaning
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if not callable(operator):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env), evaluate(right, env))
        case Call(name, argument):
            primitive = lookup(env, name)
            if not isinstance(primitive, Unary):
                raise ValueError(f"{name} is not a primitive of one argument")
            return primitive.apply(evaluate(argument, env))
        case Slice(text, start, stop):
            s = as_text(evaluate(text, env), "[:]")
            return s[as_number(evaluate(start, env), "[:]") : as_number(
                evaluate(stop, env), "[:]"
            )]
        case Let(name, definition, body):
            return evaluate(body, bind(env, name, evaluate(definition, env)))


def run(text: str) -> EVal:
    return evaluate(parse_ast(text), create_initial_env())


if __name__ == "__main__":
    for src in [
        '"ciao" + " " + "mondo"',
        '"ab" * 3',
        'upper("ciao") + nl + reverse("ciao")',
        '"programming"[0:7]',
        'let w = "na" in (w * 8 + nl) * 2 + upper("batman")',
        'let s = "Pisa" in s + nl + ("-" * length(s))',
        'let s = "Hello" in upper(s[0:1]) + lower(s[1:length(s)])',
        'let p = "level" in reverse(p) + " " + p',
    ]:
        print(f"{src}\n{run(src)}\n")

    for src in ['"a" * "b"', '"a" + 3', 'upper(3)', '"abc"["a":2]', 'reverse', 'nl(1)']:
        try:
            print(f"{src} = {run(src)!r}")
        except ValueError as e:
            print(f"{src}: {e}")
