"""Lecture 4: the same syntax, a different semantic domain.

Values are pictures (tuples of equal-length strings) instead of integers.
Run with `python3 pictures.py` from this directory.
"""

from collections.abc import Callable

from domains import BinaryExpression, Expression, Number, parse_ast

type Picture = tuple[str, ...]  # rows, all of the same length
type Operator = Callable[[Picture, Picture], Picture]
type DVal = Picture | Operator
type Environment = Callable[[str], DVal]


# The three functions of domains.py, with pictures in place of integers.


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


def width(p: Picture) -> int:
    return len(p[0]) if p else 0


def block(n: int) -> Picture:
    return tuple("#" * n for _ in range(n))


def beside(p: Picture, q: Picture) -> Picture:
    height = max(len(p), len(q))
    rows_p = p + (" " * width(p),) * (height - len(p))
    rows_q = q + (" " * width(q),) * (height - len(q))
    return tuple(a + b for a, b in zip(rows_p, rows_q))


def above(p: Picture, q: Picture) -> Picture:
    w = max(width(p), width(q))
    return tuple(row.ljust(w) for row in p + q)


def picture_env() -> Environment:
    env = empty_environment()
    env = bind(env, "+", beside)
    env = bind(env, "*", above)
    return env


def evaluate(ast: Expression, env: Environment) -> Picture:
    match ast:
        case Number(value):
            return block(value)
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if not callable(operator):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env), evaluate(right, env))


def show(p: Picture) -> None:
    print("\n".join(p))


if __name__ == "__main__":
    env = picture_env()
    show(evaluate(parse_ast("(1+2)*3"), env))
    try:
        evaluate(parse_ast("3-1"), env)
    except ValueError as e:
        print(e)
