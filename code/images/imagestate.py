"""Lecture 6, exercise 4: the language of images, with variables. A solution.

The expressions are those of imagelang.py (Lecture 5, exercise 5), without
print(...). Above them, the commands of Lecture 6: var, <- and print, with ;
between them. A variable holds an image, and an assignment replaces it.

Run with `python3 imagestate.py`: it runs the examples of the slides and saves
what each print shows in out/. Add `--show` to open a window for each one.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError
from PIL import Image

import images
from imagelang import (
    Argument,
    BinaryExpression,
    Call,
    DVal,
    EVal,
    Expression,
    Function,
    Let,
    Number,
    Text,
    Var,
    bind,
    create_initial_env,
    lookup,
    transform_parse_tree,
)

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | assign | print
    vardecl: "var" IDENTIFIER "=" expr
    assign: IDENTIFIER "<-" expr
    print: "print" expr

    ?expr: let | arith
    let: "let" IDENTIFIER "=" expr "in" expr
    ?arith: bin | mono
    bin: arith OP mono
    mono: var | paren | call | ground | text
    paren: "(" expr ")"
    call: IDENTIFIER "(" expr ("," expr)* ")"
    ground: NUMBER
    text: STRING
    var: IDENTIFIER

    NUMBER: /[0-9]+(\.[0-9]+)?/
    STRING: /"[^"]*"/
    OP: "&" | "|" | "/"
    IDENTIFIER: /(?!(let|in|var|print)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


@dataclass(frozen=True)
class VarDecl:
    name: str
    expr: Expression


@dataclass(frozen=True)
class Assign:
    name: str
    expr: Expression


@dataclass(frozen=True)
class Print:
    expr: Expression


type Command = VarDecl | Assign | Print


@dataclass(frozen=True)
class Sequence:
    first: Command
    rest: Sequence | None = None


def transform_command(tree: Tree) -> Command:
    match tree:
        case Tree(data="vardecl", children=[Token(type="IDENTIFIER", value=name), expr]):
            return VarDecl(name=name, expr=transform_parse_tree(expr))
        case Tree(data="assign", children=[Token(type="IDENTIFIER", value=name), expr]):
            return Assign(name=name, expr=transform_parse_tree(expr))
        case Tree(data="print", children=[expr]):
            return Print(expr=transform_parse_tree(expr))
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


# --- The store, as in state.py: a location holds an image ----------------------


@dataclass(frozen=True)
class Loc:
    address: int


type MVal = EVal
type Environment = Callable[[str], DVal | Loc]


@dataclass(frozen=True)
class State:
    store: Callable[[int], MVal]
    next_loc: int


def empty_state() -> State:
    def store(address: int) -> MVal:
        raise ValueError(f"Location {address} is not allocated")

    return State(store=store, next_loc=0)


def access(state: State, loc: Loc) -> MVal:
    return state.store(loc.address)


def update(state: State, loc: Loc, value: MVal) -> State:
    def new_store(address: int) -> MVal:
        if address == loc.address:
            return value
        return state.store(address)

    return State(store=new_store, next_loc=state.next_loc)


def allocate(state: State, value: MVal) -> tuple[Loc, State]:
    loc = Loc(state.next_loc)
    state = update(state, loc, value)
    return loc, State(store=state.store, next_loc=loc.address + 1)


# --- Expressions: as in imagelang.py, plus the case of a variable ---------------


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value):
            raise ValueError(f"{value:g} is a number, not an image")
        case Text(value):
            raise ValueError(f'"{value}" is a file name, not an image: use load')
        case Var(name):
            meaning = lookup(env, name)
            if isinstance(meaning, Loc):
                return access(state, meaning)
            if not isinstance(meaning, Image.Image):
                raise ValueError(f"{name} is not an image")
            return meaning
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if isinstance(operator, Image.Image | Function | Loc):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env, state), evaluate(right, env, state))
        case Call(name, args):
            function = lookup(env, name)
            if not isinstance(function, Function):
                raise ValueError(f"{name} is not a function")
            if len(args) != function.arity:
                raise ValueError(f"{name} takes {function.arity} argument(s)")
            return function.apply([evaluate_argument(a, env, state) for a in args])
        case Let(name, definition, body):
            image = evaluate(definition, env, state)
            return evaluate(body, bind(env, name, image), state)


def evaluate_argument(ast: Expression, env: Environment, state: State) -> Argument:
    match ast:
        case Number(value):
            return value
        case Text(value):
            return value
        case _:
            return evaluate(ast, env, state)


# --- Commands -------------------------------------------------------------------


def execute(
    command: Command, env: Environment, state: State, display: Callable[[EVal], None]
) -> tuple[Environment, State]:
    match command:
        case VarDecl(name, expr):
            loc, state = allocate(state, evaluate(expr, env, state))
            return bind(env, name, loc), state
        case Assign(name, expr):
            loc = lookup(env, name)
            if not isinstance(loc, Loc):
                raise ValueError(f"{name} is not a variable")
            return env, update(state, loc, evaluate(expr, env, state))
        case Print(expr):
            display(evaluate(expr, env, state))
            return env, state


def execute_sequence(
    sequence: Sequence, env: Environment, state: State, display: Callable[[EVal], None]
) -> tuple[Environment, State]:
    env, state = execute(sequence.first, env, state, display)
    if sequence.rest is None:
        return env, state
    return execute_sequence(sequence.rest, env, state, display)


def run(text: str, display: Callable[[EVal], None]) -> None:
    # the "print" in the environment of imagelang.py cannot be named any more
    execute_sequence(parse_program(text), create_initial_env(display), empty_state(), display)


EXAMPLES = [
    "var row = scale(circle, 0.5); row <- row | row; row <- row | row; print row",
    'var p = load("sky.png"); p <- circle & p; print p; p <- mirror(p); print p',
    "var a = circle; var b = square; var t = a; a <- b; b <- t; print a | b",
]

if __name__ == "__main__":
    show = "--show" in sys.argv
    out = images.HERE / "out"
    out.mkdir(exist_ok=True)
    for number, src in enumerate(EXAMPLES, start=1):
        shown: list[EVal] = []

        def display(image: EVal) -> None:
            shown.append(image)
            if show:
                images.show(image)

        run(src, display)
        for k, image in enumerate(shown, start=1):
            name = f"state-{number}.png" if len(shown) == 1 else f"state-{number}-{k}.png"
            images.save(image, out / name)
            print(f"{src}  ->  out/{name}  {image.size}")

    for src in ["circle <- square", "var c = circle; c <- 2"]:
        try:
            run(src, lambda image: None)
        except ValueError as e:
            print(f"{src}: {e}")
