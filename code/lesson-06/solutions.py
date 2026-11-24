"""Lecture 6, exercises 2 and 3. A solution.

Exercise 2: `var x` without a value. Reading x before the first assignment
is an error; declaring a name that is already a variable is an error too.

Exercise 3: `alias y = x`. After it, y stands for the same location as x.

Everything else is imported from state.py. Run with `python3 solutions.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from state import (
    Assign,
    BinaryExpression,
    Environment,
    EVal,
    Expression,
    Let,
    Loc,
    Number,
    Print,
    State,
    Var,
    VarDecl,
    access,
    allocate,
    bind,
    create_initial_env,
    empty_state,
    lookup,
    transform_expression,
    update,
)

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | declare | alias | assign | print
    vardecl: "var" IDENTIFIER "=" expr
    declare: "var" IDENTIFIER
    alias: "alias" IDENTIFIER "=" IDENTIFIER
    assign: IDENTIFIER "<-" expr
    print: "print" expr

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
    IDENTIFIER: /(?!(let|in|var|print|alias)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


@dataclass(frozen=True)
class Declare:
    name: str


@dataclass(frozen=True)
class Alias:
    name: str
    target: str


type Command = VarDecl | Declare | Alias | Assign | Print


@dataclass(frozen=True)
class Sequence:
    first: Command
    rest: Sequence | None = None


def transform_command(tree: Tree) -> Command:
    match tree:
        case Tree(data="vardecl", children=[Token(type="IDENTIFIER", value=name), expr]):
            return VarDecl(name=name, expr=transform_expression(expr))
        case Tree(data="declare", children=[Token(type="IDENTIFIER", value=name)]):
            return Declare(name=name)
        case Tree(data="alias", children=[Token(value=name), Token(value=target)]):
            return Alias(name=name, target=target)
        case Tree(data="assign", children=[Token(type="IDENTIFIER", value=name), expr]):
            return Assign(name=name, expr=transform_expression(expr))
        case Tree(data="print", children=[expr]):
            return Print(expr=transform_expression(expr))
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def transform_sequence(tree: Tree) -> Sequence:
    match tree:
        case Tree(data="sequence", children=[command]):
            return Sequence(first=transform_command(command))
        case Tree(data="sequence", children=[command, rest]):
            return Sequence(first=transform_command(command), rest=transform_sequence(rest))
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def parse_program(text: str) -> Sequence:
    try:
        tree = parser.parse(text)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return transform_sequence(tree)


# --- Exercise 2: a location that has not been written yet -----------------------


def reserve(state: State) -> tuple[Loc, State]:
    """A fresh location, with nothing written in it: reading it is an error."""
    loc = Loc(state.next_loc)
    return loc, State(store=state.store, next_loc=loc.address + 1)


def is_variable(env: Environment, name: str) -> bool:
    try:
        return isinstance(lookup(env, name), Loc)
    except ValueError:
        return False


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value):
            return value
        case Var(name):
            match lookup(env, name):
                case Loc() as loc:
                    try:
                        return access(state, loc)
                    except ValueError:
                        raise ValueError(f"{name} has no value yet") from None
                case int() as value:
                    return value
                case _:
                    raise ValueError(f"{name} is an operator, not a value")
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if not callable(operator):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env, state), evaluate(right, env, state))
        case Let(name, definition, body):
            value = evaluate(definition, env, state)
            return evaluate(body, bind(env, name, value), state)


def execute(command: Command, env: Environment, state: State) -> tuple[Environment, State]:
    match command:
        case VarDecl(name, expr):
            if is_variable(env, name):
                raise ValueError(f"{name} is already declared")
            value = evaluate(expr, env, state)
            loc, state = allocate(state, value)
            return bind(env, name, loc), state
        case Declare(name):
            if is_variable(env, name):
                raise ValueError(f"{name} is already declared")
            loc, state = reserve(state)
            return bind(env, name, loc), state
        case Alias(name, target):  # exercise 3
            if is_variable(env, name):
                raise ValueError(f"{name} is already declared")
            loc = lookup(env, target)
            if not isinstance(loc, Loc):
                raise ValueError(f"{target} is not a variable")
            return bind(env, name, loc), state
        case Assign(name, expr):
            loc = lookup(env, name)
            if not isinstance(loc, Loc):
                raise ValueError(f"{name} is not a variable")
            value = evaluate(expr, env, state)
            return env, update(state, loc, value)
        case Print(expr):
            print(evaluate(expr, env, state))
            return env, state


def execute_sequence(
    sequence: Sequence, env: Environment, state: State
) -> tuple[Environment, State]:
    env, state = execute(sequence.first, env, state)
    if sequence.rest is None:
        return env, state
    return execute_sequence(sequence.rest, env, state)


def run(text: str) -> None:
    execute_sequence(parse_program(text), create_initial_env(), empty_state())


if __name__ == "__main__":
    for src in [
        # exercise 2
        "var x; x <- 4; print x * x",
        "var x; print x + 1",
        "var x = 1; var x = 2",
        "var x = 1; print let x = 5 in x; var x = 2",
        # exercise 3
        "var x = 1; alias y = x; y <- 7; print x",
        "var x = 0; alias y = x; x <- x + 1; y <- y + 1; var z = y; x <- x + 1; print y + z",
        "alias y = x",
        "var x = 1; print let k = 2 in k; alias y = k",
    ]:
        print(f"\n{src}")
        try:
            run(src)
        except ValueError as e:
            print(e)
