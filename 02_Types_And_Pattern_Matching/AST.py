# Blind-folded Exercise: Arithmetic Expression Parser
# ------------------------------------------------------
# Write a program that parses arithmetic expressions like "2 + 5 - 3 * 4" and computes the AST.
# Assumptions:
# - Operators and operands are separated by spaces
# - Only binary operators (+, -, *) are used
# - No parentheses are in the expressions
# - Operations should be evaluated ignoring standard precedence rules; just run left to right

# Type definitions

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

@dataclass
class Operator:
    operator: str  # Could be Literal["+", "-", "*"]
    arguments: list[Expr]

@dataclass
class Constant:
    value: int

type Expr = Constant | Operator

# Example: "3 + 2" 
expr = Operator(
    operator="+",
    arguments=[Constant(value=3), Constant(value=2)]
)

# Example: "3" 
expr2 = Constant(value=3)

# %%

# Parser: parse a string into an AST (plain recursive version, left-to-right)
def parse(expression: str) -> Expr:
    """Parse an arithmetic expression into an AST.
    Expression is space-separated like "2 + 5 - 3 * 4"
    Evaluates left-to-right ignoring precedence.
    """
    tokens = expression.split()
    return parse_tokens(tokens)

def parse_tokens(tokens: list[str]) -> Expr:
    """Recursively parse tokens into an AST, left-to-right"""
    match tokens:
        case []:
            raise ValueError("Empty expression")
        case [num]:
            return Constant(value=int(num))
        case [num, op, *rest] if op in ["+", "-", "*"]:
            # Start with first number and build left-to-right
            left = Constant(value=int(num))
            return parse_left_to_right(left, op, rest)
        case _:
            raise ValueError(f"Invalid tokens: {tokens}")

def parse_left_to_right(left: Expr, op: str, tokens: list[str]) -> Expr:
    """Build AST left-to-right with accumulator"""
    match tokens:
        case []:
            raise ValueError("Operator without right operand")
        case [num]:
            # Final operand
            return Operator(operator=op, arguments=[left, Constant(value=int(num))])
        case [num, next_op, *rest] if next_op in ["+", "-", "*"]:
            # Build current operation and continue
            current = Operator(operator=op, arguments=[left, Constant(value=int(num))])
            return parse_left_to_right(current, next_op, rest)
        case _:
            raise ValueError(f"Invalid tokens: {tokens}")

# %%

# Evaluator: evaluate an AST to get the result
def evaluate(expr: Expr) -> int:
    """Evaluate an arithmetic expression AST"""
    match expr:
        case Constant(value=v):
            return v
        case Operator(operator=op, arguments=[left, right]):
            left_val = evaluate(left)
            right_val = evaluate(right)
            match (left_val, op, right_val):
                case (int(l), "+", int(r)):
                    return l + r
                case (int(l), "-", int(r)):
                    return l - r
                case (int(l), "*", int(r)):
                    return l * r
                case _:
                    raise ValueError(f"Invalid operation: {left_val} {op} {right_val}")
        case _:
            raise ValueError(f"Invalid expression: {expr}")

# %%

# Pretty-printer: display AST in a readable tree format
def pretty_print(expr: Expr, indent: int = 0) -> str:
    """Pretty print an AST with tree structure"""
    prefix = "  " * indent
    match expr:
        case Constant(value=v):
            return f"{prefix}{v}"
        case Operator(operator=op, arguments=[left, right]):
            left_str = pretty_print(left, indent + 1)
            right_str = pretty_print(right, indent + 1)
            return f"{prefix}({op})\n{left_str}\n{right_str}"
        case _:
            return f"{prefix}<invalid>"

# %%

# Test examples
test_expr1 = "2 + 5 - 3 * 4"
test_expr2 = "3 + 2"
test_expr3 = "10 - 2 + 3"

ast1 = parse(test_expr1)
ast2 = parse(test_expr2)
ast3 = parse(test_expr3)

print(f"Expression: {test_expr1}")
print("AST (tree view):")
print(pretty_print(ast1))
print(f"Result: {evaluate(ast1)}")
print()

print(f"Expression: {test_expr2}")
print("AST (tree view):")
print(pretty_print(ast2))
print(f"Result: {evaluate(ast2)}")
print()

print(f"Expression: {test_expr3}")
print("AST (tree view):")
print(pretty_print(ast3))
print(f"Result: {evaluate(ast3)}")
print()
