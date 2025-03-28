# %%
from __future__ import annotations

# %%

from lark import Lark, ParseTree, Token, Transformer, Tree

# Define the grammar in Lark's EBNF format
grammar = r"""
    ?expr: bin | mono
    mono: ground | paren
    paren: "(" expr ")"
    bin: mono OP expr
    ground: NUMBER

    NUMBER: /[0-9]+/
    OP: "+" | "-" | "*"

    %import common.WS
    %ignore WS
"""

# Create the Lark parser
parser = Lark(grammar, start="expr")

parse_tree = parser.parse("(1 + 2) - 3")

print(parse_tree.pretty())

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
def print_tree(tree: ParseTree | Token):
    match tree:
        case Tree(data=data, children=children):
            print("Tree", data)
            for child in children:
                print_tree(child)
        case Token(type=type, value=value):
            print("Token", type, value)


print_tree(parse_tree)


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

        case Tree(data="ground", children=[Token(type="NUMBER", value=value)]):
            return Number(value=int(value))

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

print(ast)

# %%

# Exercise:
# Add more operators. Implement the interpreter. Print the result. Add "/" and "%" operators.
# Q: How will you handle division by zero?

# Exercise:
# Add a ternary conditional operator (like the COND ? THEN : ELSE operator in C)
