"""Lecture 8: functions and closures.

The language of Lecture 7 (control.py), with:

    function f(x, y) = e            a command: binds f to a closure
    f(e1, e2)                       an expression: calls f
    if e then e1 else e2 endif      an expression: needed for recursion

Run with `python3 functions.py`. The fragments shown in the slides are taken
from this file, in the order they appear here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

# --- Syntax: the language of Lecture 7, with functions --------------------------

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | assign | print | ifelse | while | fundecl
    vardecl: "var" IDENTIFIER "=" expr
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    ifelse: "if" expr "then" sequence "else" sequence "endif"
    while: "while" expr "do" sequence "done"
    fundecl: "function" IDENTIFIER "(" params ")" "=" expr
    params: (IDENTIFIER ("," IDENTIFIER)*)?

    ?expr: let | arith
    let: "let" IDENTIFIER "=" expr "in" expr
    ?arith: bin | mono
    bin: arith OP mono
    mono: ground | var | paren | unary | funapp | ifexpr
    funapp: IDENTIFIER "(" args ")"
    args: (expr ("," expr)*)?
    ifexpr: "if" expr "then" expr "else" expr "endif"
    unary: UNOP mono
    paren: "(" expr ")"
    ground: NUMBER | BOOL
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    BOOL: "true" | "false"
    OP: "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<=" | ">=" | "<" | ">" | "and" | "or"
    UNOP: "not"
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|endif|while|do|done|true|false|and|or|not|function)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


@dataclass(frozen=True)
class Number:
    value: int


@dataclass(frozen=True)
class Bool:
    value: bool


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Apply:
    op: str
    args: list[Expression]


@dataclass(frozen=True)
class Let:
    name: str
    definition: Expression
    body: Expression


@dataclass(frozen=True)
class FunctionApp:
    name: str
    args: list[Expression]


@dataclass(frozen=True)
class IfExpr:
    cond: Expression
    then_branch: Expression
    else_branch: Expression


type Expression = Number | Bool | Var | Apply | Let | FunctionApp | IfExpr


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
class IfElse:
    cond: Expression
    then_branch: Sequence
    else_branch: Sequence


@dataclass(frozen=True)
class While:
    cond: Expression
    body: Sequence


@dataclass(frozen=True)
class FunctionDecl:
    name: str
    params: list[str]
    body: Expression


type Command = VarDecl | Assign | Print | IfElse | While | FunctionDecl


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
        case Tree(data="ground", children=[Token(type="BOOL", value=word)]):
            return Bool(value=(word == "true"))
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(data="bin", children=[left, Token(type="OP", value=op), right]):
            return Apply(op=op, args=[transform_expression(left), transform_expression(right)])
        case Tree(data="unary", children=[Token(type="UNOP", value=op), operand]):
            return Apply(op=op, args=[transform_expression(operand)])
        case Tree(
            data="let",
            children=[Token(type="IDENTIFIER", value=name), definition, body],
        ):
            return Let(
                name=name,
                definition=transform_expression(definition),
                body=transform_expression(body),
            )
        case Tree(data="funapp", children=[Token(type="IDENTIFIER", value=name), args]):
            return FunctionApp(name=name, args=[transform_expression(a) for a in args.children])
        case Tree(data="ifexpr", children=[cond, then_branch, else_branch]):
            return IfExpr(
                cond=transform_expression(cond),
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
        case Tree(data="ifelse", children=[cond, then_branch, else_branch]):
            return IfElse(
                cond=transform_expression(cond),
                then_branch=transform_sequence(then_branch),
                else_branch=transform_sequence(else_branch),
            )
        case Tree(data="while", children=[cond, body]):
            return While(cond=transform_expression(cond), body=transform_sequence(body))
        case Tree(data="fundecl", children=[Token(type="IDENTIFIER", value=name), params, body]):
            return FunctionDecl(
                name=name,
                params=[str(p) for p in params.children],
                body=transform_expression(body),
            )
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


# --- Semantic domains: as in Lecture 7, and a name can stand for a closure ---------


@dataclass(frozen=True)
class Loc:
    address: int


type EVal = int | bool  # what an expression can produce
type MVal = EVal  # what a location can hold


@dataclass(frozen=True)
class Operator:
    type: tuple[list[type], type]  # (argument types, result type)
    fn: Callable[[list[EVal]], EVal]


@dataclass(frozen=True)
class Closure:
    function: FunctionDecl
    env: Environment  # the environment of the declaration


type DVal = EVal | Operator | Loc | Closure  # what a name can stand for

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


# --- Operators: a function and its type --------------------------------------------


def add(args: list[EVal]) -> EVal:
    return args[0] + args[1]


def subtract(args: list[EVal]) -> EVal:
    return args[0] - args[1]


def multiply(args: list[EVal]) -> EVal:
    return args[0] * args[1]


def divide(args: list[EVal]) -> EVal:
    if args[1] == 0:
        raise ValueError("Division by zero")
    return args[0] // args[1]


def modulo(args: list[EVal]) -> EVal:
    if args[1] == 0:
        raise ValueError("Division by zero")
    return args[0] % args[1]


def equal(args: list[EVal]) -> EVal:
    return args[0] == args[1]


def not_equal(args: list[EVal]) -> EVal:
    return args[0] != args[1]


def less(args: list[EVal]) -> EVal:
    return args[0] < args[1]


def greater(args: list[EVal]) -> EVal:
    return args[0] > args[1]


def less_equal(args: list[EVal]) -> EVal:
    return args[0] <= args[1]


def greater_equal(args: list[EVal]) -> EVal:
    return args[0] >= args[1]


def logical_and(args: list[EVal]) -> EVal:
    return args[0] and args[1]


def logical_or(args: list[EVal]) -> EVal:
    return args[0] or args[1]


def logical_not(args: list[EVal]) -> EVal:
    return not args[0]


def create_initial_env() -> Environment:
    env = empty_environment()
    # arithmetic: int × int → int
    env = bind(env, "+", Operator(([int, int], int), add))
    env = bind(env, "-", Operator(([int, int], int), subtract))
    env = bind(env, "*", Operator(([int, int], int), multiply))
    env = bind(env, "/", Operator(([int, int], int), divide))
    env = bind(env, "%", Operator(([int, int], int), modulo))
    # comparisons: int × int → bool
    env = bind(env, "==", Operator(([int, int], bool), equal))
    env = bind(env, "!=", Operator(([int, int], bool), not_equal))
    env = bind(env, "<", Operator(([int, int], bool), less))
    env = bind(env, ">", Operator(([int, int], bool), greater))
    env = bind(env, "<=", Operator(([int, int], bool), less_equal))
    env = bind(env, ">=", Operator(([int, int], bool), greater_equal))
    # connectives: bool × bool → bool, and bool → bool
    env = bind(env, "and", Operator(([bool, bool], bool), logical_and))
    env = bind(env, "or", Operator(([bool, bool], bool), logical_or))
    env = bind(env, "not", Operator(([bool], bool), logical_not))
    return env


def check_arguments(op: str, expected_types: list[type], values: list[EVal]) -> None:
    if len(expected_types) != len(values):
        raise ValueError(
            f"Operator '{op}' expects {len(expected_types)} arguments, got {len(values)}"
        )
    for i, (expected, actual) in enumerate(zip(expected_types, values)):
        # not isinstance: in Python, bool is a subclass of int, and we do not want true + 1
        if type(actual) is not expected:
            raise ValueError(
                f"Operator '{op}': argument {i + 1} must be {expected.__name__}, "
                f"got {type(actual).__name__}"
            )


def show(value: EVal) -> str:
    """Print booleans the way the language writes them."""
    if type(value) is bool:
        return "true" if value else "false"
    return str(value)


# --- Expressions read the state ------------------------------------------------


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value):
            return value
        case Bool(value):
            return value
        case Var(name):
            match lookup(env, name):
                case Loc() as loc:
                    return access(state, loc)
                case int() | bool() as value:
                    return value
                case _:
                    raise ValueError(f"{name} is not a value")
        case Apply(op, args):
            values = [evaluate(arg, env, state) for arg in args]
            match lookup(env, op):
                case Operator(type=(expected_types, _), fn=fn):
                    check_arguments(op, expected_types, values)
                    return fn(values)
                case _:
                    raise ValueError(f"{op} is not an operator")
        case Let(name, definition, body):
            value = evaluate(definition, env, state)
            return evaluate(body, bind(env, name, value), state)
        case IfExpr(cond, then_branch, else_branch):
            if evaluate_condition(cond, env, state):
                return evaluate(then_branch, env, state)
            return evaluate(else_branch, env, state)
        case FunctionApp(name, args):
            closure = lookup(env, name)
            if not isinstance(closure, Closure):
                raise ValueError(f"{name} is not a function")
            function = closure.function
            if len(args) != len(function.params):
                raise ValueError(
                    f"Function {name} expects {len(function.params)} arguments, got {len(args)}"
                )
            values = [evaluate(arg, env, state) for arg in args]
            call_env = bind(closure.env, function.name, closure)
            for param, value in zip(function.params, values):
                call_env = bind(call_env, param, value)
            return evaluate(function.body, call_env, state)


def evaluate_condition(cond: Expression, env: Environment, state: State) -> bool:
    value = evaluate(cond, env, state)
    if type(value) is not bool:
        raise ValueError(f"Condition must be a boolean, got {show(value)}")
    return value


# --- Commands change the state ---------------------------------------------------


def execute_block(block: Sequence, env: Environment, state: State) -> State:
    """Run a block: its declarations do not survive it, and its locations are reused."""
    _, new_state = execute_sequence(block, env, state)
    return State(store=new_state.store, next_loc=state.next_loc)


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
        case IfElse(cond, then_branch, else_branch):
            if evaluate_condition(cond, env, state):
                return env, execute_block(then_branch, env, state)
            return env, execute_block(else_branch, env, state)
        case While(cond, body):
            while evaluate_condition(cond, env, state):
                state = execute_block(body, env, state)
            return env, state
        case FunctionDecl(name):
            return bind(env, name, Closure(command, env)), state


def execute_sequence(
    sequence: Sequence, env: Environment, state: State
) -> tuple[Environment, State]:
    env, state = execute(sequence.first, env, state)
    if sequence.rest is None:
        return env, state
    return execute_sequence(sequence.rest, env, state)


def run(text: str) -> None:
    execute_sequence(parse_program(text), create_initial_env(), empty_state())


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


EXAMPLES: dict[str, str] = {
    "first call": """
        var x = 10;
        function f(y) = x + y;
        print f(1);
        print 2 + f(1)
    """,
    "not a value": """
        function f(y) = y + 1;
        print f
    """,
    "not storable": """
        function f(y) = y + 1;
        var g = f
    """,
    "not a function": """
        var x = 1;
        print x(1)
    """,
    "store is current": """
        var x = 10;
        function f(y) = x + y;
        x <- 100;
        print f(1)
    """,
    "environment is captured": """
        var x = 10;
        function f(y) = x + y;
        var x = 100;
        print f(1)
    """,
    "static scoping": """
        var x = 1;
        function f() = x;
        if true then var x = 2; print f() else print 0 endif
    """,
    "block-local function": """
        var x = 10;
        if x > 0 then
            var y = 42;
            function f(a) = y + a;
            print f(3)
        else
            print 0
        endif;
        print f(3)
    """,
    "arguments are evaluated first": """
        function f(x) = 0;
        print f(1 / 0)
    """,
    "arity": """
        function f(x, y) = x + y;
        print f(1)
    """,
    "factorial": """
        function fact(n) = if n == 0 then 1 else n * fact(n - 1) endif;
        print fact(5)
    """,
    "gcd": """
        function gcd(a, b) = if b == 0 then a else gcd(b, a % b) endif;
        print gcd(48, 18)
    """,
    "mutual recursion": """
        function even(n) = if n == 0 then true else odd(n - 1) endif;
        function odd(n) = if n == 0 then false else even(n - 1) endif;
        print even(10)
    """,
    "deep recursion": """
        function count(n) = if n == 0 then 0 else 1 + count(n - 1) endif;
        print count(1000)
    """,
}


if __name__ == "__main__":
    print(parse_program("function f(y) = x + y; print f(1)"))

    for title, src in EXAMPLES.items():
        print(f"\n--- {title}")
        try:
            run(src)
        except ValueError as e:
            print(e)
        except RecursionError as e:
            print(f"RecursionError: {e}")
