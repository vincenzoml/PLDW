"""Lecture 5: static and dynamic scoping.

The language of binding.py, with one change: `let` does not compute the value
of its definition. It binds the name to the definition itself, and the
definition is computed each time the name is used. Then it matters in which
environment it is computed: the one where the `let` was (static scoping) or
the one where the name is used (dynamic scoping).

Run with `python3 scoping.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from binding import (
    BinaryExpression,
    Expression,
    Let,
    Number,
    Var,
    add,
    divide,
    evaluate_string,
    modulo,
    multiply,
    parse_ast,
    subtract,
)

type EVal = int
type Operator = Callable[[EVal, EVal], EVal]


@dataclass(frozen=True)
class Delayed:
    """A definition that has not been computed yet, with the environment of
    the `let` where it was written. Dynamic scoping does not use `env`."""

    definition: Expression
    env: Environment


type DVal = EVal | Operator | Delayed
type Environment = Callable[[str], DVal]


def empty_environment() -> Environment:
    def env(name: str) -> DVal:
        raise ValueError(f"Undefined identifier: {name}")

    return env


def bind(env: Environment, name: str, value: DVal) -> Environment:
    def new_env(n: str) -> DVal:
        if n == name:
            return value
        return env(n)

    return new_env


def create_initial_env() -> Environment:
    env = empty_environment()
    env = bind(env, "+", add)
    env = bind(env, "-", subtract)
    env = bind(env, "*", multiply)
    env = bind(env, "/", divide)
    env = bind(env, "%", modulo)
    return env


def evaluate_static(ast: Expression, env: Environment) -> EVal:
    match ast:
        case Number(value):
            return value
        case Var(name):
            match env(name):
                case Delayed(definition, saved_env):
                    return evaluate_static(definition, saved_env)
                case int() as value:
                    return value
                case _:
                    raise ValueError(f"{name} is an operator, not a value")
        case BinaryExpression(op, left, right):
            operator = env(op)
            if not callable(operator):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate_static(left, env), evaluate_static(right, env))
        case Let(name, definition, body):
            return evaluate_static(body, bind(env, name, Delayed(definition, env)))


def evaluate_dynamic(ast: Expression, env: Environment) -> EVal:
    match ast:
        case Number(value):
            return value
        case Var(name):
            match env(name):
                case Delayed(definition, _):
                    return evaluate_dynamic(definition, env)
                case int() as value:
                    return value
                case _:
                    raise ValueError(f"{name} is an operator, not a value")
        case BinaryExpression(op, left, right):
            operator = env(op)
            if not callable(operator):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate_dynamic(left, env), evaluate_dynamic(right, env))
        case Let(name, definition, body):
            return evaluate_dynamic(body, bind(env, name, Delayed(definition, env)))


def compare(src: str) -> None:
    print(src)
    ast = parse_ast(src)
    runs: list[tuple[str, Callable[[], EVal]]] = [
        ("eager  ", lambda: evaluate_string(src)),
        ("static ", lambda: evaluate_static(ast, create_initial_env())),
        ("dynamic", lambda: evaluate_dynamic(ast, create_initial_env())),
    ]
    for label, run in runs:
        try:
            print(f"  {label} {run()}")
        except RecursionError:
            print(f"  {label} RecursionError")
        except ValueError as e:
            print(f"  {label} {e}")


if __name__ == "__main__":
    compare("let x = 5 in let f = x + 10 in let x = 42 in f")
    compare("let a = 1 in let f = a + 10 in let a = 100 in f")
    compare("let x = 1 in let y = x * 2 in y + y")
    compare("let z = 1 / 0 in 7")
    compare("let f = x + 1 in let x = 2 in f")
    compare("let x = 1 in let x = x + 1 in x")
