"""Lecture 7, exercise 4: counting loops. A solution.

    for x = e1 to e2 do s done

e1 and e2 are computed once, before the loop. Two versions of the loop variable:

1. bound as in let: at each iteration x stands for a value. The body cannot
   assign it ("x is not a variable").
2. a variable in the store: x is a location, initialised to e1 and incremented
   after each iteration. The body can assign it, and changes the iterations.

The loop variable and what the body declares are local to the loop.
Everything else comes from control.py. Run with `python3 for_loop.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

import control
from control import (
    Environment,
    Expression,
    IfElse,
    Loc,
    Sequence,
    State,
    While,
    access,
    allocate,
    bind,
    create_initial_env,
    empty_state,
    evaluate,
    evaluate_condition,
    transform_expression,
    update,
)

# --- Syntax: one more command, and two more keywords --------------------------------

grammar = (
    control.grammar.replace(
        "?command: vardecl | assign | print | ifelse | while",
        '?command: vardecl | assign | print | ifelse | while | for\n'
        '    for: "for" IDENTIFIER "=" expr "to" expr "do" sequence "done"',
    ).replace("|do|done|", "|do|done|for|to|")
)
assert "| for" in grammar and "|for|to|" in grammar

parser = Lark(grammar, start="sequence")


@dataclass(frozen=True)
class For:
    name: str
    start: Expression
    end: Expression
    body: Sequence


def transform_command(tree: Tree):
    match tree:
        case Tree(data="for", children=[Token(type="IDENTIFIER", value=name), start, end, body]):
            return For(name, transform_expression(start), transform_expression(end), transform_sequence(body))
        case Tree(data="ifelse", children=[cond, then_branch, else_branch]):
            return IfElse(transform_expression(cond), transform_sequence(then_branch), transform_sequence(else_branch))
        case Tree(data="while", children=[cond, body]):
            return While(transform_expression(cond), transform_sequence(body))
        case _:
            return control.transform_command(tree)


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


# --- Semantics ----------------------------------------------------------------------


def evaluate_int(expr: Expression, env: Environment, state: State) -> int:
    value = evaluate(expr, env, state)
    if type(value) is not int:
        raise ValueError(f"The bounds of for must be integers, got {control.show(value)}")
    return value


def for_as_let(name: str, i: int, end: int, body: Sequence, env: Environment, state: State) -> State:
    """Version 1: at each iteration, name is bound to the value i, as in let."""
    if i > end:
        return state
    state = execute_block(body, bind(env, name, i), state)
    return for_as_let(name, i + 1, end, body, env, state)


def for_as_var(loc: Loc, end: int, body: Sequence, env: Environment, state: State) -> State:
    """Version 2: name is a location; the body may assign it."""
    i = access(state, loc)
    if i > end:
        return state
    state = execute_block(body, env, state)
    state = update(state, loc, access(state, loc) + 1)
    return for_as_var(loc, end, body, env, state)


VERSION = "let"  # or "var"


def execute(command, env: Environment, state: State) -> tuple[Environment, State]:
    match command:
        case For(name, start, end, body):
            first, last = evaluate_int(start, env, state), evaluate_int(end, env, state)
            if VERSION == "let":
                after = for_as_let(name, first, last, body, env, state)
            else:
                loc, inner = allocate(state, first)
                after = for_as_var(loc, last, body, bind(env, name, loc), inner)
            return env, State(store=after.store, next_loc=state.next_loc)
        case IfElse(cond, then_branch, else_branch):
            if evaluate_condition(cond, env, state):
                return env, execute_block(then_branch, env, state)
            return env, execute_block(else_branch, env, state)
        case While(cond, body):
            if evaluate_condition(cond, env, state):
                return execute(command, env, execute_block(body, env, state))
            return env, state
        case _:
            return control.execute(command, env, state)


def execute_sequence(sequence: Sequence, env: Environment, state: State) -> tuple[Environment, State]:
    env, state = execute(sequence.first, env, state)
    if sequence.rest is None:
        return env, state
    return execute_sequence(sequence.rest, env, state)


def execute_block(block: Sequence, env: Environment, state: State) -> State:
    _, new_state = execute_sequence(block, env, state)
    return State(store=new_state.store, next_loc=state.next_loc)


def run(text: str) -> None:
    try:
        execute_sequence(parse_program(text), create_initial_env(), empty_state())
    except ValueError as e:
        print(e)


if __name__ == "__main__":
    programs = [
        "for i = 1 to 3 do print i * i done",
        # the program whose output differs: the body assigns the loop variable
        "for i = 1 to 5 do print i; i <- i + 1 done",
    ]
    for version in ["let", "var"]:
        VERSION = version
        print(f"--- loop variable as {version}")
        for p in programs:
            print(p)
            run(p)
