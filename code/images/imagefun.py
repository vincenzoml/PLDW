"""Lecture 8, exercise 4: the language of images, with functions and procedures.

The language of imagecontrol.py (Lecture 7), with the declarations of Lecture 8:
`fun f(x, y) = e` and `proc p(x, y) c`. A call looks like a call of a primitive,
mirror(p) or scale(p, 0.5): the evaluator tells them apart by what the name
stands for. A function or a procedure is a closure, and can call itself.

Run with `python3 imagefun.py`: it runs the examples of the slides and saves
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
from imagecontrol import (
    Block,
    Boolean,
    EVal,
    Environment,
    Expression,
    If,
    IfExpr,
    While,
    create_initial_control_env,
    show,
    transform_expression,
)
from imagelang import BinaryExpression, Call, Function, Let, Number, Text, Var, bind, lookup
from imagestate import Assign, Loc, Print, State, VarDecl, access, allocate, empty_state, update

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | assign | print | if | while | block
            | fundecl | procdecl | callcmd
    vardecl: "var" IDENTIFIER "=" expr
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    if: "if" expr "then" command "else" command
    while: "while" expr "do" command
    block: "{" sequence "}"
    fundecl: "fun" IDENTIFIER "(" params ")" "=" expr
    procdecl: "proc" IDENTIFIER "(" params ")" command
    callcmd: IDENTIFIER "(" expr ("," expr)* ")"
    params: IDENTIFIER ("," IDENTIFIER)*

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
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|while|do|true|false|fun|proc)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


@dataclass(frozen=True)
class FunDecl:
    name: str
    params: tuple[str, ...]
    body: Expression


@dataclass(frozen=True)
class ProcDecl:
    name: str
    params: tuple[str, ...]
    body: Command


@dataclass(frozen=True)
class CallCommand:
    name: str
    args: tuple[Expression, ...]


type Command = (
    VarDecl | Assign | Print | If | While | Block | FunDecl | ProcDecl | CallCommand
)


@dataclass(frozen=True)
class Sequence:
    first: Command
    rest: Sequence | None = None


def transform_command(tree: Tree) -> Command:
    match tree:
        case Tree(data="fundecl", children=[Token(value=name), Tree(children=params), body]):
            return FunDecl(name, tuple(map(str, params)), transform_expression(body))
        case Tree(data="procdecl", children=[Token(value=name), Tree(children=params), body]):
            return ProcDecl(name, tuple(map(str, params)), transform_command(body))
        case Tree(data="callcmd", children=[Token(value=name), *args]):
            return CallCommand(name, tuple(transform_expression(a) for a in args))
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


# --- Closures, next to the primitives of imagelang.py ---------------------------


@dataclass(frozen=True)
class Closure:
    """A function declared with fun: its body is an expression."""

    params: tuple[str, ...]
    body: Expression
    env: Environment


@dataclass(frozen=True)
class ProcClosure:
    """A procedure declared with proc: its body is a command."""

    params: tuple[str, ...]
    body: Command
    env: Environment


def check_arity(name: str, params: tuple[str, ...], args: tuple[Expression, ...]) -> None:
    if len(args) != len(params):
        raise ValueError(f"{name} takes {len(params)} argument(s), not {len(args)}")


def evaluate_args(args: tuple[Expression, ...], env: Environment, state: State) -> list[EVal | str]:
    """A file name in double quotes is allowed here, and only here."""
    return [a.value if isinstance(a, Text) else evaluate(a, env, state) for a in args]


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value) | Boolean(value):
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
            callee = lookup(env, name)
            match callee:
                case Function(arity, apply):  # a primitive, as in imagelang.py
                    if len(args) != arity:
                        raise ValueError(f"{name} takes {arity} argument(s)")
                    return apply(evaluate_args(args, env, state))
                case Closure(params, body, closure_env):  # declared with fun
                    check_arity(name, params, args)
                    call_env = closure_env
                    for param, value in zip(params, evaluate_args(args, env, state)):
                        call_env = bind(call_env, param, value)
                    return evaluate(body, call_env, state)
                case _:
                    raise ValueError(f"{name} is not a function")
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
        case FunDecl(name, params, body):

            def env_with_function(n: str) -> object:  # bind(env, name, function)
                return function if n == name else env(n)

            function = Closure(params, body, env_with_function)
            return env_with_function, state
        case ProcDecl(name, params, body):

            def env_with_procedure(n: str) -> object:  # bind(env, name, procedure)
                return procedure if n == name else env(n)

            procedure = ProcClosure(params, body, env_with_procedure)
            return env_with_procedure, state
        case CallCommand(name, args):
            callee = lookup(env, name)
            if not isinstance(callee, ProcClosure):
                raise ValueError(f"{name} is not a procedure")
            check_arity(name, callee.params, args)
            call_env = callee.env
            for param, value in zip(callee.params, evaluate_args(args, env, state)):
                loc, state = allocate(state, value)
                call_env = bind(call_env, param, loc)
            _, state = execute(callee.body, call_env, state, display)
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
    "fun pair(p) = p | mirror(p); print pair(circle) / pair(square)",
    "fun sierpinski(p, size) = if width(p) >= size then p else sierpinski(p / (p | p), size); "
    "print sierpinski(scale(circle, 0.0625), 512)",
    "var gallery = scale(circle, 0.25); proc add(p) gallery <- gallery | scale(p, 0.25); "
    "add(square); add(mirror(circle)); add(square); print gallery",
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
            images.save(picture, out / f"functions-{index}.png")
            print(f"{src}  ->  out/functions-{index}.png  {picture.size}")

    for src in [
        "fun pair(p) = p | mirror(p); print pair(circle, square)",
        "proc show2(p) print p | p; print show2(circle)",
        "fun big(p) = scale(p, 2); var b = big; print b",
    ]:
        print(src)
        try:
            run(src, lambda picture: None)
        except ValueError as e:
            print(e)
