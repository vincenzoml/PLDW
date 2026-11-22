"""Lecture 7, exercise 4: the language of images, with control flow. A solution.

The language of imagestate.py (Lecture 6), with if-then-else (as a command and
as an expression), while and blocks in braces. A condition needs something to compare: width(e) and height(e) give
the size of an image in pixels, and the comparisons < <= > >= == != give true
or false. So a value is now an image, a number or a boolean.

Run with `python3 imagecontrol.py`: it runs the examples of the slides and saves
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
    BinaryExpression,
    Call,
    Function,
    Let,
    Number,
    Text,
    Var,
    bind,
    create_initial_env,
    image_arg,
    lookup,
)
from imagestate import Assign, Loc, Print, State, VarDecl, access, allocate, empty_state, update

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | assign | print | if | while | block
    vardecl: "var" IDENTIFIER "=" expr
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    if: "if" expr "then" command "else" command
    while: "while" expr "do" command
    block: "{" sequence "}"

    ?expr: let | ifexpr | test
    let: "let" IDENTIFIER "=" expr "in" expr
    ifexpr: "if" expr "then" expr "else" expr
    ?test: arith | compare
    compare: arith CMP arith
    ?arith: bin | mono
    bin: arith OP mono
    mono: var | paren | call | ground | text | boolean
    paren: "(" expr ")"
    call: IDENTIFIER "(" expr ("," expr)* ")"
    ground: NUMBER
    text: STRING
    boolean: BOOLEAN
    var: IDENTIFIER

    NUMBER: /[0-9]+(\.[0-9]+)?/
    STRING: /"[^"]*"/
    BOOLEAN: "true" | "false"
    OP: "&" | "|" | "/"
    CMP: "==" | "!=" | "<=" | ">=" | "<" | ">"
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|while|do|true|false)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


@dataclass(frozen=True)
class Boolean:
    value: bool


@dataclass(frozen=True)
class IfExpr:
    test: Expression
    then_branch: Expression
    else_branch: Expression


type Expression = Number | Text | Boolean | Var | BinaryExpression | Call | Let | IfExpr


@dataclass(frozen=True)
class If:
    test: Expression
    then_branch: Command
    else_branch: Command


@dataclass(frozen=True)
class While:
    test: Expression
    body: Command


@dataclass(frozen=True)
class Block:
    body: Sequence


type Command = VarDecl | Assign | Print | If | While | Block


@dataclass(frozen=True)
class Sequence:
    first: Command
    rest: Sequence | None = None


def transform_expression(tree: Tree | str) -> Expression:
    match tree:
        case Tree(data="mono" | "paren", children=[subtree]):
            return transform_expression(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=float(digits))
        case Tree(data="text", children=[Token(type="STRING", value=quoted)]):
            return Text(value=quoted[1:-1])
        case Tree(data="boolean", children=[Token(type="BOOLEAN", value=word)]):
            return Boolean(value=(word == "true"))
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(data="bin" | "compare", children=[left, Token(value=op), right]):
            return BinaryExpression(op, transform_expression(left), transform_expression(right))
        case Tree(data="call", children=[Token(type="IDENTIFIER", value=name), *args]):
            return Call(name=name, args=tuple(transform_expression(a) for a in args))
        case Tree(data="let", children=[Token(value=name), definition, body]):
            return Let(name, transform_expression(definition), transform_expression(body))
        case Tree(data="ifexpr", children=[test, then_branch, else_branch]):
            return IfExpr(
                transform_expression(test),
                transform_expression(then_branch),
                transform_expression(else_branch),
            )
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def transform_command(tree: Tree) -> Command:
    match tree:
        case Tree(data="vardecl", children=[Token(value=name), expr]):
            return VarDecl(name, transform_expression(expr))
        case Tree(data="assign", children=[Token(value=name), expr]):
            return Assign(name, transform_expression(expr))
        case Tree(data="print", children=[expr]):
            return Print(transform_expression(expr))
        case Tree(data="if", children=[test, then_branch, else_branch]):
            return If(
                transform_expression(test),
                transform_command(then_branch),
                transform_command(else_branch),
            )
        case Tree(data="while", children=[test, body]):
            return While(transform_expression(test), transform_command(body))
        case Tree(data="block", children=[sequence]):
            return Block(transform_sequence(sequence))
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def transform_sequence(tree: Tree) -> Sequence:
    match tree:
        case Tree(data="sequence", children=[command]):
            return Sequence(transform_command(command))
        case Tree(data="sequence", children=[command, rest]):
            return Sequence(transform_command(command), transform_sequence(rest))
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def parse_program(text: str) -> Sequence:
    try:
        tree = parser.parse(text)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return transform_sequence(tree)


# --- Values: images, numbers and booleans --------------------------------------

type EVal = Image.Image | float | bool
type Environment = Callable[[str], object]


def show(value: EVal) -> str:
    if isinstance(value, Image.Image):
        return f"an image of {value.width} x {value.height}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return f"{value:g}"


def number(value: EVal) -> float:
    if type(value) is not float:
        raise ValueError(f"{show(value)} is not a number")
    return value


def image(value: EVal) -> Image.Image:
    if not isinstance(value, Image.Image):
        raise ValueError(f"{show(value)} is not an image")
    return value


def equal(x: EVal, y: EVal) -> bool:
    if type(x) is not type(y) or isinstance(x, Image.Image):
        raise ValueError(f"Cannot compare {show(x)} and {show(y)}")
    return x == y


def create_initial_control_env(display: Callable[[Image.Image], None]) -> Environment:
    env: Environment = create_initial_env(display)
    # the three operators of images, now checking that they get two images
    env = bind(env, "&", lambda x, y: images.over(image(x), image(y)))
    env = bind(env, "|", lambda x, y: images.beside(image(x), image(y)))
    env = bind(env, "/", lambda x, y: images.above(image(x), image(y)))
    # two functions that give a number, and the comparisons
    width = Function(1, lambda args: float(image_arg(args[0], "width").width))
    height = Function(1, lambda args: float(image_arg(args[0], "height").height))
    env = bind(env, "width", width)
    env = bind(env, "height", height)
    env = bind(env, "<", lambda x, y: number(x) < number(y))
    env = bind(env, "<=", lambda x, y: number(x) <= number(y))
    env = bind(env, ">", lambda x, y: number(x) > number(y))
    env = bind(env, ">=", lambda x, y: number(x) >= number(y))
    env = bind(env, "==", equal)
    env = bind(env, "!=", lambda x, y: not equal(x, y))
    return env


# --- Expressions: a number or a boolean is now a value too -------------------------


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value):
            return value
        case Boolean(value):
            return value
        case Text(value):
            raise ValueError(f'"{value}" is a file name, not an image: use load')
        case Var(name):
            meaning = lookup(env, name)
            if isinstance(meaning, Loc):
                return access(state, meaning)
            if not isinstance(meaning, Image.Image | float | bool):
                raise ValueError(f"{name} is not a value")
            return meaning
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if not callable(operator) or isinstance(operator, Function):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env, state), evaluate(right, env, state))
        case Call(name, args):
            function = lookup(env, name)
            if not isinstance(function, Function):
                raise ValueError(f"{name} is not a function")
            if len(args) != function.arity:
                raise ValueError(f"{name} takes {function.arity} argument(s)")
            values = [a.value if isinstance(a, Text) else evaluate(a, env, state) for a in args]
            return function.apply(values)
        case Let(name, definition, body):
            value = evaluate(definition, env, state)
            return evaluate(body, bind(env, name, value), state)
        case IfExpr(test, then_branch, else_branch):
            branch = then_branch if condition(test, env, state) else else_branch
            return evaluate(branch, env, state)


def condition(test: Expression, env: Environment, state: State) -> bool:
    value = evaluate(test, env, state)
    if not isinstance(value, bool):
        raise ValueError(f"The condition is {show(value)}, not true or false")
    return value


# --- Commands: those of imagestate.py, and if, while, blocks -------------------------


def execute(
    command: Command, env: Environment, state: State, display: Callable[[Image.Image], None]
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
            value = evaluate(expr, env, state)
            if isinstance(value, Image.Image):
                display(value)
            else:
                print(show(value))
            return env, state
        case If(test, then_branch, else_branch):
            branch = then_branch if condition(test, env, state) else else_branch
            _, state = execute(branch, env, state, display)
            return env, state
        case While(test, body):
            while condition(test, env, state):
                _, state = execute(body, env, state, display)
            return env, state
        case Block(body):
            _, state = execute_sequence(body, env, state, display)
            return env, state


def execute_sequence(
    sequence: Sequence, env: Environment, state: State, display: Callable[[Image.Image], None]
) -> tuple[Environment, State]:
    env, state = execute(sequence.first, env, state, display)
    if sequence.rest is None:
        return env, state
    return execute_sequence(sequence.rest, env, state, display)


def run(text: str, display: Callable[[Image.Image], None]) -> None:
    program = parse_program(text)
    execute_sequence(program, create_initial_control_env(display), empty_state(), display)


EXAMPLES = [
    "var row = scale(circle, 0.25); while width(row) < 512 do row <- row | row; print row",
    "var step = scale(square, 0.25); var stairs = step; "
    "while height(stairs) < 512 do { step <- step | scale(square, 0.25); stairs <- stairs / step }; "
    "print stairs",
    'var p = circle & load("sky.png"); '
    "if width(p) > height(p) then print p / mirror(p) else print p | mirror(p)",
]

if __name__ == "__main__":
    show_windows = "--show" in sys.argv
    out = images.HERE / "out"
    out.mkdir(exist_ok=True)
    for index, src in enumerate(EXAMPLES, start=1):
        shown: list[Image.Image] = []

        def display(picture: Image.Image) -> None:
            shown.append(picture)
            if show_windows:
                images.show(picture)

        run(src, display)
        for picture in shown:
            images.save(picture, out / f"control-{index}.png")
            print(f"{src}  ->  out/control-{index}.png  {picture.size}")

    for src in [
        "print width(circle); print width(circle) < 600",
        "if circle then print circle else print square",
        "print circle < square",
        "print width(circle) | circle",
    ]:
        print(src)
        try:
            run(src, lambda picture: None)
        except ValueError as e:
            print(e)
