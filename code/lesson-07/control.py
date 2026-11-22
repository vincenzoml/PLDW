"""Lecture 7: control flow.

The language of Lecture 6 (state.py), with three changes:

1. Booleans are values: EVal = int | bool.
2. Every operator is an Operator(type, fn) bound in the environment, and the
   evaluator checks the number and the types of the arguments before applying
   it. One AST node, Apply, for every operator application, binary or unary.
3. Two new commands, if-then-else-endif and while-do-done. Their branches and
   body are blocks: what is declared inside is not visible after, and its
   locations are reused.

Run with `python3 control.py`. The fragments shown in the slides are taken
from this file, in the order they appear here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

# --- Syntax: the language of Lecture 6, with booleans, if and while ------------

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | assign | print | ifelse | while
    vardecl: "var" IDENTIFIER "=" expr
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    ifelse: "if" expr "then" sequence "else" sequence "endif"
    while: "while" expr "do" sequence "done"

    ?expr: let | arith
    let: "let" IDENTIFIER "=" expr "in" expr
    ?arith: bin | mono
    bin: arith OP mono
    mono: ground | var | paren | unary
    unary: UNOP mono
    paren: "(" expr ")"
    ground: NUMBER | BOOL
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    BOOL: "true" | "false"
    OP: "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<=" | ">=" | "<" | ">" | "and" | "or"
    UNOP: "not"
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|endif|while|do|done|true|false|and|or|not)\b)[a-zA-Z_][a-zA-Z0-9_]*/

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


type Expression = Number | Bool | Var | Apply | Let


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


type Command = VarDecl | Assign | Print | IfElse | While


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


# --- Semantic domains: as in Lecture 6, and EVal gains bool ------------------------


@dataclass(frozen=True)
class Loc:
    address: int


type EVal = int | bool  # what an expression can produce
type MVal = EVal  # what a location can hold


@dataclass(frozen=True)
class Operator:
    type: tuple[list[type], type]  # (argument types, result type)
    fn: Callable[[list[EVal]], EVal]


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
                    raise ValueError(f"{name} is an operator, not a value")
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


def execute_while_by_recursion(
    cond: Expression, body: Sequence, env: Environment, state: State
) -> State:
    """The equation of while, transcribed literally. execute does not use it."""
    if evaluate_condition(cond, env, state):
        return execute_while_by_recursion(cond, body, env, execute_block(body, env, state))
    return state


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


if __name__ == "__main__":
    print(parse_program("while n > 0 do n <- n - 1 done"))

    for src in [
        # booleans, and what the typed operators refuse
        "print 3 < 4",
        "var b = true; print b; b <- 3 == 4; print b",
        "print true + 1",
        "print 1 < 2 and 2 < 3",
        "print (1 < 2) and (2 < 3)",
        "print true == false",
        "print false and (1 / 0 == 0)",
        # if
        "var x = 1; if x == 1 then print 42 else print 0 endif",
        "if 1 then print 1 else print 0 endif",
        # while
        "var n = 3; while n > 0 do print n; n <- n - 1 done",
        "var a = 48; var b = 18; "
        "while b != 0 do if a > b then a <- a - b else b <- b - a endif done; print a",
        "while false do print 1 done; print 0",
        "var n = 5000; while n > 0 do n <- n - 1 done; print n",
        # blocks
        "var x = 0; if true then var y = 1; x <- x + y else print 0 endif; print x; print y",
        "var i = 0; while i < 3 do var sq = i * i; print sq; i <- i + 1 done",
    ]:
        print(f"\n{src}")
        try:
            run(src)
        except ValueError as e:
            print(e)

    # The equation of while, transcribed literally: one Python call per iteration
    print("\nwhile by recursion, 5000 iterations")
    env, state = execute(VarDecl("n", Number(5000)), create_initial_env(), empty_state())
    loop = parse_program("while n > 0 do n <- n - 1 done").first
    assert isinstance(loop, While)
    try:
        execute_while_by_recursion(loop.cond, loop.body, env, state)
    except RecursionError as e:
        print(f"RecursionError: {e}")

    # The store as a chain of functions: a limit inherited from Lecture 6
    src = "var a = 0; var n = 3000; while n > 0 do n <- n - 1 done; print a"
    print(f"\n{src}")
    try:
        run(src)
    except RecursionError as e:
        print(f"RecursionError: {e}")

    # Uncomment to try it interactively.
    # REPL()
