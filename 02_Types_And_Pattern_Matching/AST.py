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

@dataclass
class Operator:
    operator: str
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
