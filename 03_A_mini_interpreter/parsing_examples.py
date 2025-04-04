# %%
from __future__ import annotations

# %%

from lark import Lark, Token, Tree

# Define the grammar in Lark's EBNF format
grammar = r"""
    ?expr: bin | mono
    mono: ground | paren
    paren: "(" expr ")"
    bin: expr OP mono
    ground: NUMBER

    NUMBER: /[0-9]+/
    OP: "+" | "-" | "*" | "/" | "%"

    %import common.WS
    %ignore WS
"""

# Create the Lark parser
parser = Lark(grammar, start="expr")

parse_tree = parser.parse("(1 + 2) - 3")

# print(parse_tree.pretty())

# bin
# ├── mono
# │   └── paren
# │       └── bin
# │           ├── mono
# │           │   └── ground
# │           │       └── 1
# │           ├── op
# │           └── mono
# │               └── ground
# │                   └── 2
# ├── op
# └── mono
#     └── ground
#         └── 3


# %%
def print_tree(tree: Tree | Token):
    match tree:
        case Tree(data=data, children=children):
            print("Tree", data)
            for child in children:
                print_tree(child)
        case Token(type=type, value=value):
            print("Token", type, value)


# print_tree(parse_tree)


# %%

from dataclasses import dataclass
from typing import Literal

# Define AST types for the expression language
type Op = Literal["+", "-", "*"]


@dataclass
class Number:
    value: int


@dataclass
class BinaryExpression:
    op: Op
    left: Expression
    right: Expression


type Expression = Number | BinaryExpression


# %%
def transform_parse_tree(tree: Tree) -> Expression:
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_parse_tree(subtree)

        case Tree(data="ground", children=[Token(type="NUMBER", value=actual_value)]):
            return Number(value=int(actual_value))

        case Tree(data="paren", children=[subtree]):
            return transform_parse_tree(subtree)

        case Tree(
            data="bin",
            children=[
                left,
                Token(type="OP", value=op),
                right,
            ],
        ):
            return BinaryExpression(
                op=op,
                left=transform_parse_tree(left),
                right=transform_parse_tree(right),
            )

        case _:
            raise ValueError(f"Unexpected parse tree structure")


def parse_ast(expression: str) -> Expression:
    parse_tree = parser.parse(expression)
    return transform_parse_tree(parse_tree)


example = "(1+2)-3"

# example = "1+2"
ast = parse_ast(example)

# print(ast)

# %%

# Exercise:
# Add more operators. Implement the interpreter. Print the result. Add "/" and "%" operators.
# Q: How will you handle division by zero?

# %% Interpreter


def evaluate(ast: Expression) -> int:
    match ast:
        case Number(value):
            return value
        case BinaryExpression(op, left, right):
            left_value = evaluate(left)
            right_value = evaluate(right)
            match op:
                case "+":
                    return left_value + right_value
                case "-":
                    return left_value - right_value
                case "*":
                    return left_value * right_value
                case "/":
                    if right_value == 0:
                        raise ValueError("Division by zero")
                    return left_value // right_value
                case "%":
                    if right_value == 0:
                        raise ValueError("Division by zero")
                    return left_value % right_value


def evaluate_string(expression: str) -> int:
    ast = parse_ast(expression)
    return evaluate(ast)


# print(evaluate_string("1+2"))


def REPL():
    exit = False
    while not exit:
        expression = input("Enter an expression (exit to quit): ")
        if expression == "exit":
            exit = True
        else:
            try:
                print(evaluate_string(expression))
            except Exception as e:
                print(e)


REPL()
