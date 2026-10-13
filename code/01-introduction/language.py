"""Chapter 1 — a language in forty lines.

Syntax: a tree of dataclasses.  Semantics: one recursive function.
Run:    python3 language.py
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Syntax ---------------------------------------------------------------
# An expression is a number, a variable, or an operator applied to two expressions.
# The grammar, in the notation of Chapter 3:
#
#     expr ::= NUMBER | NAME | expr OP expr        OP ::= "+" | "-" | "*" | "/"


@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class Variable:
    name: str


@dataclass(frozen=True)
class BinaryOp:
    left: Expr
    operator: str
    right: Expr


type Expr = Number | Variable | BinaryOp

# The tree for  2 + (x * 3).  Parentheses are not in the tree: the shape *is* the grouping.
example = BinaryOp(
    left=Number(2.0),
    operator="+",
    right=BinaryOp(left=Variable("x"), operator="*", right=Number(3.0)),
)

# --- Semantics ------------------------------------------------------------
# The meaning of an expression is a number, once we know the value of every variable.

type Env = dict[str, float]


def evaluate(expr: Expr, env: Env) -> float:
    match expr:
        case Number(value):
            return value
        case Variable(name):
            if name not in env:
                raise NameError(f"variable '{name}' is not defined")
            return env[name]
        case BinaryOp(left, operator, right):
            lv = evaluate(left, env)
            rv = evaluate(right, env)
            match operator:
                case "+":
                    return lv + rv
                case "-":
                    return lv - rv
                case "*":
                    return lv * rv
                case "/":
                    return lv / rv
                case _:
                    raise ValueError(f"unknown operator '{operator}'")


if __name__ == "__main__":
    print(example)
    print(evaluate(example, {"x": 4.0}))  # 14.0

    # Two trees for the same characters "2 * 3 + 4": the tree decides the answer.
    left_first = BinaryOp(BinaryOp(Number(2), "*", Number(3)), "+", Number(4))
    right_first = BinaryOp(Number(2), "*", BinaryOp(Number(3), "+", Number(4)))
    print(evaluate(left_first, {}), evaluate(right_first, {}))  # 10.0 14.0

    try:
        evaluate(Variable("y"), {"x": 4.0})
    except NameError as e:
        print("error:", e)
