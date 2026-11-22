"""Lecture 8: functions and procedures.

The language of Lecture 7, with two new declarations. `fun f(x, y) = e`
declares a function: its body is an expression, and a call f(1, 2) is an
expression. `proc p(x, y) c` declares a procedure: its body is a command, and a
call p(1, 2) is a command. Both are closures: they keep the environment where
they are declared. Run with `python3 functions.py`. The fragments shown in the
slides are taken from this file, in the order they appear here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

# --- Syntax: Lecture 7, with declarations and calls ---------------------------

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
    callcmd: IDENTIFIER "(" args ")"
    params: (IDENTIFIER ("," IDENTIFIER)*)?
    args: (expr ("," expr)*)?

    ?expr: let | ifexpr | test
    let: "let" IDENTIFIER "=" expr "in" expr
    ifexpr: "if" expr "then" expr "else" expr
    ?test: arith | compare
    compare: arith CMP arith
    ?arith: bin | mono
    bin: arith OP mono
    mono: ground | boolean | call | var | paren
    call: IDENTIFIER "(" args ")"
    paren: "(" expr ")"
    ground: NUMBER
    boolean: BOOLEAN
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    BOOLEAN: "true" | "false"
    OP: "+" | "-" | "*" | "/" | "%"
    CMP: "==" | "!=" | "<=" | ">=" | "<" | ">"
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|while|do|true|false|fun|proc)\b)[a-zA-Z_][a-zA-Z0-9_]*/

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


@dataclass(frozen=True)
class Call:
    name: str
    args: tuple[Expression, ...]


type Expression = Number | Boolean | Var | BinaryExpression | Let | IfExpr | Call


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


def transform_names(tree: Tree) -> tuple[str, ...]:
    return tuple(str(token) for token in tree.children)


def transform_args(tree: Tree) -> tuple[Expression, ...]:
    return tuple(transform_expression(child) for child in tree.children)


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
        case Tree(data="call", children=[Token(type="IDENTIFIER", value=name), args]):
            return Call(name=name, args=transform_args(args))
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
        case Tree(data="fundecl", children=[Token(value=name), params, body]):
            return FunDecl(
                name=name, params=transform_names(params), body=transform_expression(body)
            )
        case Tree(data="procdecl", children=[Token(value=name), params, body]):
            return ProcDecl(
                name=name, params=transform_names(params), body=transform_command(body)
            )
        case Tree(data="callcmd", children=[Token(value=name), args]):
            return CallCommand(name=name, args=transform_args(args))
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


# --- Semantic domains: functions and procedures are closures ---------------------


@dataclass(frozen=True)
class Loc:
    address: int


@dataclass(frozen=True)
class Function:
    params: tuple[str, ...]
    body: Expression
    env: Environment  # the environment of the declaration


@dataclass(frozen=True)
class Procedure:
    params: tuple[str, ...]
    body: Command
    env: Environment  # the environment of the declaration


type EVal = int | bool  # what an expression can produce
type MVal = EVal  # what a location can hold
type Operator = Callable[[EVal, EVal], EVal]
type DVal = EVal | Operator | Loc | Function | Procedure  # what a name can stand for

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
    """As in Lecture 7: the new store copies what the old one holds."""
    cells = {address: state.store(address) for address in range(state.next_loc)}
    cells[loc.address] = value

    def new_store(address: int) -> MVal:
        if address in cells:
            return cells[address]
        raise ValueError(f"Location {address} is not allocated")

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


def check_arity(name: str, params: tuple[str, ...], values: list[EVal]) -> None:
    if len(values) != len(params):
        raise ValueError(f"{name} takes {len(params)} argument(s), not {len(values)}")


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
                    raise ValueError(f"{name} is not a value")
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
        case Call(name, args):
            function = lookup(env, name)
            if not isinstance(function, Function):
                raise ValueError(f"{name} is not a function")
            values = [evaluate(arg, env, state) for arg in args]
            check_arity(name, function.params, values)
            call_env = function.env
            for param, value in zip(function.params, values):
                call_env = bind(call_env, param, value)
            return evaluate(function.body, call_env, state)


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
        case FunDecl(name, params, body):

            def env_with_function(n: str) -> DVal:  # bind(env, name, function)
                if n == name:
                    return function
                return env(n)

            function = Function(params, body, env_with_function)
            return env_with_function, state
        case ProcDecl(name, params, body):

            def env_with_procedure(n: str) -> DVal:  # bind(env, name, procedure)
                if n == name:
                    return procedure
                return env(n)

            procedure = Procedure(params, body, env_with_procedure)
            return env_with_procedure, state
        case CallCommand(name, args):
            callee = lookup(env, name)
            if not isinstance(callee, Procedure):
                raise ValueError(f"{name} is not a procedure")
            values = [evaluate(arg, env, state) for arg in args]
            check_arity(name, callee.params, values)
            call_env = callee.env
            for param, value in zip(callee.params, values):
                loc, state = allocate(state, value)
                call_env = bind(call_env, param, loc)
            _, state = execute(callee.body, call_env, state)
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
    print(parse_program("fun square(x) = x * x; print square(3)"))

    for src in [
        "fun square(x) = x * x; print square(3) + square(4)",
        "fun max(a, b) = if a > b then a else b; print max(3, 7)",
        "var k = 1; fun addk(x) = x + k; print let k = 100 in addk(1); k <- 5; print addk(1)",
        "fun fact(n) = if n == 0 then 1 else n * fact(n - 1); print fact(10)",
        "fun fib(n) = if n < 2 then n else fib(n - 1) + fib(n - 2); print fib(15)",
        "var total = 0; proc add(x) total <- total + x; add(3); add(4); print total",
        "proc countdown(n) while n > 0 do { print n; n <- n - 1 }; "
        "var a = 3; countdown(a); print a",
        "proc down(n) if n == 0 then print 0 else { print n; down(n - 1) }; down(2)",
        "fun three() = 3; print three()",
        # errors, on purpose
        "fun square(x) = x * x; print square(1, 2)",
        "fun square(x) = x * x; square(3)",
        "proc p(x) print x; print p(1)",
        "fun square(x) = x * x; var g = square",
        "fun f(x) = y; var y = 1; print f(0)",
        "fun forever(n) = forever(n + 1); print forever(0)",
    ]:
        print(f"\n{src}")
        try:
            run(src)
        except ValueError as e:
            print(e)
        except RecursionError as e:
            print(f"RecursionError: {e}")
