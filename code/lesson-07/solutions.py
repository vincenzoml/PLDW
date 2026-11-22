"""Lecture 7, exercises 1, 2, 3 and 5. A solution, all in one interpreter.

Exercise 1: a grammar with precedence levels. From the loosest: or, and, not,
comparisons, + -, * / %. The AST does not change: still Apply.

Exercise 2: short-circuit and, or. They get their own AST nodes, And and Or,
which evaluate the right operand only when it is needed, as if does.

Exercise 3: equality on booleans. == and != accept two arguments of the same
type; true == 1 is still an error.

Exercise 5: a store that does not recurse. A dictionary, copied by update and
allocate, so that old states are never changed.

Everything else is imported from control.py. Run with `python3 solutions.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from control import (
    Apply,
    Assign,
    Bool,
    Environment,
    EVal,
    IfElse,
    Let,
    Loc,
    MVal,
    Number,
    Operator,
    Print,
    Var,
    VarDecl,
    While,
    bind,
    create_initial_env,
    equal,
    lookup,
    not_equal,
    show,
)

# --- Exercise 1: precedence levels ----------------------------------------------

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | assign | print | ifelse | while
    vardecl: "var" IDENTIFIER "=" expr
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    ifelse: "if" expr "then" sequence "else" sequence "endif"
    while: "while" expr "do" sequence "done"

    ?expr: let | disj
    let: "let" IDENTIFIER "=" expr "in" expr
    ?disj: conj | or
    or: disj "or" conj
    ?conj: neg | and
    and: conj "and" neg
    ?neg: comparison | not
    not: "not" neg
    ?comparison: sum | compare
    compare: sum CMP sum
    ?sum: product | bin_sum
    bin_sum: sum ADDOP product
    ?product: mono | bin_product
    bin_product: product MULOP mono
    mono: ground | var | paren
    paren: "(" expr ")"
    ground: NUMBER | BOOL
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    BOOL: "true" | "false"
    CMP: "==" | "!=" | "<=" | ">=" | "<" | ">"
    ADDOP: "+" | "-"
    MULOP: "*" | "/" | "%"
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|endif|while|do|done|true|false|and|or|not)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


# --- Exercise 2: and, or are not operators ----------------------------------------


@dataclass(frozen=True)
class And:
    left: Expression
    right: Expression


@dataclass(frozen=True)
class Or:
    left: Expression
    right: Expression


type Expression = Number | Bool | Var | Apply | Let | And | Or
type Command = VarDecl | Assign | Print | IfElse | While


@dataclass(frozen=True)
class Sequence:
    first: Command
    rest: Sequence | None = None


def transform_expression(tree: Tree | str) -> Expression:
    match tree:
        case Tree(data="mono" | "paren", children=[subtree]):
            return transform_expression(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(int(digits))
        case Tree(data="ground", children=[Token(type="BOOL", value=word)]):
            return Bool(word == "true")
        case Tree(data="var", children=[Token(value=name)]):
            return Var(name)
        case Tree(data="compare" | "bin_sum" | "bin_product", children=[left, Token(value=op), right]):
            return Apply(op, [transform_expression(left), transform_expression(right)])
        case Tree(data="not", children=[operand]):
            return Apply("not", [transform_expression(operand)])
        case Tree(data="and", children=[left, right]):
            return And(transform_expression(left), transform_expression(right))
        case Tree(data="or", children=[left, right]):
            return Or(transform_expression(left), transform_expression(right))
        case Tree(data="let", children=[Token(value=name), definition, body]):
            return Let(name, transform_expression(definition), transform_expression(body))
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
        case Tree(data="ifelse", children=[cond, then_branch, else_branch]):
            return IfElse(
                transform_expression(cond),
                transform_sequence(then_branch),
                transform_sequence(else_branch),
            )
        case Tree(data="while", children=[cond, body]):
            return While(transform_expression(cond), transform_sequence(body))
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


# --- Exercise 3: "two arguments of the same type" ---------------------------------


class Same:
    """In an operator's type: an int or a bool, the same as the first argument."""


def create_env() -> Environment:
    env = create_initial_env()
    env = bind(env, "==", Operator(([Same, Same], bool), equal))
    env = bind(env, "!=", Operator(([Same, Same], bool), not_equal))
    return env


def check_arguments(op: str, expected_types: list[type], values: list[EVal]) -> None:
    if len(expected_types) != len(values):
        raise ValueError(
            f"Operator '{op}' expects {len(expected_types)} arguments, got {len(values)}"
        )
    for i, (expected, actual) in enumerate(zip(expected_types, values)):
        if expected is Same:
            expected = type(values[0])
        if type(actual) is not expected:
            raise ValueError(
                f"Operator '{op}': argument {i + 1} must be {expected.__name__}, "
                f"got {type(actual).__name__}"
            )


# --- Exercise 5: a store that does not recurse -------------------------------------


@dataclass(frozen=True)
class State:
    cells: dict[int, MVal]  # never changed after it is made: update copies it
    next_loc: int


def empty_state() -> State:
    return State(cells={}, next_loc=0)


def access(state: State, loc: Loc) -> MVal:
    if loc.address not in state.cells:
        raise ValueError(f"Location {loc.address} is not allocated")
    return state.cells[loc.address]


def update(state: State, loc: Loc, value: MVal) -> State:
    return State(cells={**state.cells, loc.address: value}, next_loc=state.next_loc)


def allocate(state: State, value: MVal) -> tuple[Loc, State]:
    loc = Loc(state.next_loc)
    state = update(state, loc, value)
    return loc, State(cells=state.cells, next_loc=loc.address + 1)


# --- The interpreter of control.py, with the cases of exercise 2 -------------------


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value) | Bool(value):
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
        case And(left, right):  # if left then right else false
            if evaluate_condition(left, env, state):
                return evaluate_condition(right, env, state)
            return False
        case Or(left, right):  # if left then true else right
            if evaluate_condition(left, env, state):
                return True
            return evaluate_condition(right, env, state)
        case Let(name, definition, body):
            value = evaluate(definition, env, state)
            return evaluate(body, bind(env, name, value), state)


def evaluate_condition(cond: Expression, env: Environment, state: State) -> bool:
    value = evaluate(cond, env, state)
    if type(value) is not bool:
        raise ValueError(f"Condition must be a boolean, got {show(value)}")
    return value


def execute_block(block: Sequence, env: Environment, state: State) -> State:
    _, new_state = execute_sequence(block, env, state)
    return State(cells=new_state.cells, next_loc=state.next_loc)


def execute(command: Command, env: Environment, state: State) -> tuple[Environment, State]:
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
    execute_sequence(parse_program(text), create_env(), empty_state())


if __name__ == "__main__":
    for src in [
        # exercise 1
        "print 1 + 2 * 3",
        "print 1 < 2 and 2 < 3",
        "print not 1 > 2 or false",
        "print 10 - 2 - 3",
        # exercise 2
        "print false and (1 / 0 == 0)",
        "print true or 1 / 0 == 0",
        "print true and 1",
        # exercise 3
        "print true == false",
        "print 3 != 3",
        "print true == 1",
        # exercise 5: the last program of the slides
        "var a = 0; var n = 3000; while n > 0 do n <- n - 1 done; print a",
    ]:
        print(f"\n{src}")
        try:
            run(src)
        except ValueError as e:
            print(e)
