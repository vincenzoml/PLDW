"""Lecture 6: state and commands.

The language of Lecture 5, with three commands: var, <- and print, separated
by semicolons. A name declared with var stands for a location; the store says
what each location holds. Run with `python3 state.py`. The fragments shown in
the slides are taken from this file, in the order they appear here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

# --- Syntax: the expressions of Lecture 5, and commands above them ----------

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
    mono: ground | var | paren
    paren: "(" expr ")"
    ground: NUMBER
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    OP: "+" | "-" | "*" | "/" | "%"
    IDENTIFIER: /(?!(let|in|var|print)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


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


def transform_expression(tree: Tree | str) -> Expression:
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_expression(subtree)
        case Tree(data="paren", children=[subtree]):
            return transform_expression(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(data="bin", children=[left, Token(type="OP", value=op), right]):
            return BinaryExpression(
                op=op,
                left=transform_expression(left),
                right=transform_expression(right),
            )
        case Tree(
            data="let",
            children=[Token(type="IDENTIFIER", value=name), definition, body],
        ):
            return Let(
                name=name,
                definition=transform_expression(definition),
                body=transform_expression(body),
            )
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def transform_command(tree: Tree) -> Command:
    match tree:
        case Tree(data="vardecl", children=[Token(type="IDENTIFIER", value=name), expr]):
            return VarDecl(name=name, expr=transform_expression(expr))
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
            return Sequence(
                first=transform_command(command),
                rest=transform_sequence(rest),
            )
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def parse_program(text: str) -> Sequence:
    try:
        tree = parser.parse(text)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return transform_sequence(tree)


# --- Semantic domains: environment and store ---------------------------------


@dataclass(frozen=True)
class Loc:
    address: int


type EVal = int  # what an expression can produce
type MVal = EVal  # what a location can hold
type Operator = Callable[[EVal, EVal], EVal]
type DVal = EVal | Operator | Loc  # what a name can stand for

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


type Store = Callable[[int], MVal]


@dataclass(frozen=True)
class State:
    store: Store
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


# --- Expressions read the state ------------------------------------------------


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value):
            return value
        case Var(name):
            match lookup(env, name):
                case Loc() as loc:
                    return access(state, loc)
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


# --- Commands change the state ---------------------------------------------------


def execute(command: Command, env: Environment, state: State) -> tuple[Environment, State]:
    match command:
        case VarDecl(name, expr):
            value = evaluate(expr, env, state)
            loc, state = allocate(state, value)
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


# --- A REPL that keeps the environment and the state ----------------------------


def run_session(lines: list[str]) -> None:
    """What the REPL does, with a list of lines instead of the keyboard."""
    env, state = create_initial_env(), empty_state()
    for line in lines:
        print(f"> {line}")
        try:
            env, state = execute_sequence(parse_program(line), env, state)
        except ValueError as e:
            print(e)


def REPL() -> None:
    env, state = create_initial_env(), empty_state()
    while True:
        line = input("> ")
        if line == "exit":
            break
        try:
            env, state = execute_sequence(parse_program(line), env, state)
        except ValueError as e:
            print(e)


if __name__ == "__main__":
    print(parser.parse("var x = 1; print x").pretty())
    print(parse_program("var x = 1; print x"))

    for src in [
        "var x = 10; print x; x <- 20; print x",
        "var x = 10; x <- x + 1; print x",
        "var x = 10; var y = 20; var z = x + y; print z; x <- 30; print x + y; print z",
        "var x = 1; print let x = 5 in x; print x",
        "var x = 1; var x = 2; print x",
        # errors, on purpose
        "x <- 1",
        "print y",
        "var x = 1; x <- 1 / 0",
        "print 1; print (x <- 3)",
        "var x = 1; let y = 2 in y",
        "var let = 3",
    ]:
        print(f"\n{src}")
        try:
            run(src)
        except ValueError as e:
            print(e)

    print()
    run_session(["var x = 1", "x <- x + 1; print x", "var y = x * 10; print y"])

    # Uncomment to try it interactively.
    # REPL()
