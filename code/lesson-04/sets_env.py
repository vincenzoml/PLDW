"""Lecture 4: exercise 5 of lecture 3 (sets of integers) with an environment.

Grammar, AST and transform are those of code/lesson-03/sets.py. The operators
are no longer in evaluate: they are values in the environment.

Run:    python3 sets_env.py
"""

import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lesson-03"))

from sets import BinaryExpression, Expression, SetLiteral, parser, show, transform  # noqa: E402

type EVal = frozenset[int]
type Operator = Callable[[EVal, EVal], EVal]
type DVal = EVal | Operator
type Environment = Callable[[str], DVal]


# The three functions of domains.py, with sets in place of integers.


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


def set_env() -> Environment:
    env = empty_environment()
    env = bind(env, "|", lambda a, b: a | b)
    env = bind(env, "&", lambda a, b: a & b)
    env = bind(env, "-", lambda a, b: a - b)
    return env


def evaluate(ast: Expression, env: Environment) -> EVal:
    match ast:
        case SetLiteral(elements):
            return elements
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if not callable(operator):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env), evaluate(right, env))


def run(text: str, env: Environment) -> str:
    return show(evaluate(transform(parser.parse(text)), env))


if __name__ == "__main__":
    env = set_env()
    assert run("{1, 2} | {3} & {3, 4}", env) == "{1, 2, 3}"
    assert run("{1, 2, 3} - {2}", env) == "{1, 3}"
    # the same program, with | meaning "in one of the two, not in both"
    other = bind(env, "|", lambda a, b: a ^ b)
    assert run("{1, 2} | {2, 3}", env) == "{1, 2, 3}"
    assert run("{1, 2} | {2, 3}", other) == "{1, 3}"
    print("all examples check")
