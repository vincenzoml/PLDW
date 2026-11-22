"""Lecture 7: control flow.

The language of Lecture 6, with booleans and comparisons, and three new
commands: if-then-else, while, and a block of commands in braces. There is an
if-then-else for expressions too. Run with `python3 control.py`. The fragments
shown in the slides are taken from this file, in the order they appear here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

# --- Syntax: Lecture 6, with conditions, if, while and blocks ----------------

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
    mono: ground | boolean | var | paren
    paren: "(" expr ")"
    ground: NUMBER
    boolean: BOOLEAN
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    BOOLEAN: "true" | "false"
    OP: "+" | "-" | "*" | "/" | "%"
    CMP: "==" | "!=" | "<=" | ">=" | "<" | ">"
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|while|do|true|false)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


@dataclass(frozen=True)
class Number:
    value: int


@dataclass(frozen=True)
class Boolean:
    value: bool


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


@dataclass(frozen=True)
class IfExpr:
    test: Expression
    then_branch: Expression
    else_branch: Expression


type Expression = Number | Boolean | Var | BinaryExpression | Let | IfExpr


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
        case Tree(data="mono", children=[subtree]):
            return transform_expression(subtree)
        case Tree(data="paren", children=[subtree]):
            return transform_expression(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(data="boolean", children=[Token(type="BOOLEAN", value=word)]):
            return Boolean(value=(word == "true"))
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(data="bin" | "compare", children=[left, Token(value=op), right]):
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
        case Tree(data="ifexpr", children=[test, then_branch, else_branch]):
            return IfExpr(
                test=transform_expression(test),
                then_branch=transform_expression(then_branch),
                else_branch=transform_expression(else_branch),
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
        case Tree(data="if", children=[test, then_branch, else_branch]):
            return If(
                test=transform_expression(test),
                then_branch=transform_command(then_branch),
                else_branch=transform_command(else_branch),
            )
        case Tree(data="while", children=[test, body]):
            return While(test=transform_expression(test), body=transform_command(body))
        case Tree(data="block", children=[sequence]):
            return Block(body=transform_sequence(sequence))
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


# --- Semantic domains: integers and booleans --------------------------------------


@dataclass(frozen=True)
class Loc:
    address: int


type EVal = int | bool  # what an expression can produce
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
    """As in Lecture 6, but the new store does not ask the old one: it copies
    what the old one holds. A loop makes thousands of updates, and a chain of
    thousands of stores breaks Python's limit on nested calls."""
    cells = {address: state.store(address) for address in range(state.next_loc)}
    cells[loc.address] = value

    def new_store(address: int) -> MVal:
        if address in cells:
            return cells[address]
        raise ValueError(f"Location {address} is not allocated")

    return State(store=new_store, next_loc=state.next_loc)


def update_chained(state: State, loc: Loc, value: MVal) -> State:
    """The update of Lecture 6, kept to show what goes wrong with loops."""

    def new_store(address: int) -> MVal:
        if address == loc.address:
            return value
        return state.store(address)

    return State(store=new_store, next_loc=state.next_loc)


def allocate(state: State, value: MVal) -> tuple[Loc, State]:
    loc = Loc(state.next_loc)
    state = update(state, loc, value)
    return loc, State(store=state.store, next_loc=loc.address + 1)


def show(value: EVal) -> str:
    """Booleans are printed the way the language writes them."""
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def integer(value: EVal) -> int:
    # bool is a subclass of int in Python: without this check, true + 1 is 2
    if type(value) is not int:
        raise ValueError(f"{show(value)} is not a number")
    return value


def add(x: EVal, y: EVal) -> EVal:
    return integer(x) + integer(y)


def subtract(x: EVal, y: EVal) -> EVal:
    return integer(x) - integer(y)


def multiply(x: EVal, y: EVal) -> EVal:
    return integer(x) * integer(y)


def divide(x: EVal, y: EVal) -> EVal:
    if integer(y) == 0:
        raise ValueError("Division by zero")
    return integer(x) // integer(y)


def modulo(x: EVal, y: EVal) -> EVal:
    if integer(y) == 0:
        raise ValueError("Division by zero")
    return integer(x) % integer(y)


def less(x: EVal, y: EVal) -> EVal:
    return integer(x) < integer(y)


def less_equal(x: EVal, y: EVal) -> EVal:
    return integer(x) <= integer(y)


def greater(x: EVal, y: EVal) -> EVal:
    return integer(x) > integer(y)


def greater_equal(x: EVal, y: EVal) -> EVal:
    return integer(x) >= integer(y)


def equal(x: EVal, y: EVal) -> EVal:
    if type(x) is not type(y):
        raise ValueError(f"Cannot compare {show(x)} and {show(y)}")
    return x == y


def not_equal(x: EVal, y: EVal) -> EVal:
    return not equal(x, y)


def create_initial_env() -> Environment:
    env = empty_environment()
    env = bind(env, "+", add)
    env = bind(env, "-", subtract)
    env = bind(env, "*", multiply)
    env = bind(env, "/", divide)
    env = bind(env, "%", modulo)
    env = bind(env, "<", less)
    env = bind(env, "<=", less_equal)
    env = bind(env, ">", greater)
    env = bind(env, ">=", greater_equal)
    env = bind(env, "==", equal)
    env = bind(env, "!=", not_equal)
    return env


# --- Expressions read the state ------------------------------------------------


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value):
            return value
        case Boolean(value):
            return value
        case Var(name):
            match lookup(env, name):
                case Loc() as loc:
                    return access(state, loc)
                case bool() | int() as value:
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
        case IfExpr(test, then_branch, else_branch):
            if condition(test, env, state):
                return evaluate(then_branch, env, state)
            return evaluate(else_branch, env, state)


def condition(test: Expression, env: Environment, state: State) -> bool:
    value = evaluate(test, env, state)
    if type(value) is not bool:
        raise ValueError(f"The condition is {show(value)}, not true or false")
    return value


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
            print(show(evaluate(expr, env, state)))
            return env, state
        case If(test, then_branch, else_branch):
            if condition(test, env, state):
                _, state = execute(then_branch, env, state)
            else:
                _, state = execute(else_branch, env, state)
            return env, state
        case While(test, body):
            while condition(test, env, state):
                _, state = execute(body, env, state)
            return env, state
        case Block(body):
            _, state = execute_sequence(body, env, state)
            return env, state


def execute_while(test: Expression, body: Command, env: Environment, state: State) -> State:
    """The equation of while, word for word. execute does not use it."""
    if not condition(test, env, state):
        return state
    _, state = execute(body, env, state)
    return execute_while(test, body, env, state)


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
    print(parse_program("while n > 0 do n <- n - 1"))

    for src in [
        "var x = 7; if x % 2 == 0 then print 0 else print 1",
        "var n = 5; var f = 1; while n > 1 do { f <- f * n; n <- n - 1 }; print f",
        "var i = 0; while i < 3 do i <- i + 1; print i",
        "var x = 1; { var x = 2; print x }; print x",
        "var x = 0; print if x != 0 then 10 / x else 0",
        "print 3 < 4; print 2 + 2 == 5; print true == false",
        "var a = 12; var b = 18; while b != 0 do { var t = b; b <- a % b; a <- t }; print a",
        "var i = 0; var limit = 3000; while i < limit do i <- i + 1; print i",
        # errors, on purpose
        "if 1 then print 1 else print 2",
        "print true + 1",
        "print 1 == true",
        "print 1 < 2 < 3",
        "if true then var y = 1 else var y = 2; print y",
        "var x = 0; print 10 / x",
    ]:
        print(f"\n{src}")
        try:
            run(src)
        except ValueError as e:
            print(e)

    # The equation of while, transcribed, and the store of Lecture 6: both fail
    # on a long loop, because each step is one more nested Python call.
    program = parse_program("var i = 0; while i < 3000 do i <- i + 1")
    env, state = execute(program.first, create_initial_env(), empty_state())
    loop = program.rest.first  # type: ignore[union-attr]
    assert isinstance(loop, While)
    try:
        execute_while(loop.test, loop.body, env, state)
    except RecursionError as e:
        print(f"\nexecute_while: RecursionError: {e}")

    update = update_chained  # back to the store of Lecture 6, for the next run
    try:
        run("var i = 0; var limit = 3000; while i < limit do i <- i + 1; print i")
    except RecursionError as e:
        print(f"update_chained: RecursionError: {e}")
