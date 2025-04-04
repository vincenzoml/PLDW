from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, TypeAlias, Union
from lark import Lark, Token, Tree


# Define the semantic domains
# Using Python 3.13 simplified syntax for union types
type DenOperator = Callable[[int, int], int]
type DVal = DenOperator  # Denotable values: can be stored in environment

# Environment as a function
type Environment = Callable[[str], DVal]

# Define grammar for parsing
grammar = r"""
    ?expr: bin | mono
    mono: ground | paren
    paren: "(" expr ")"
    bin: expr OP mono        
    ground: NUMBER 
    ident: IDENTIFIER


    NUMBER: /[0-9]+/
    OP: "+" | "-" | "*" | "/" | "%"

    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""
# Note: bin rule is left-associative, implementing left recursive parsing
# The IDENTIFIER rule is used to match variable names, but it's unused now. As an exercise, you will use it to extend the language with numeric constants.
# Create the Lark parser

parser = Lark(grammar, start="expr")


# Define operators
def add(x: int, y: int) -> int:
    return x + y


def subtract(x: int, y: int) -> int:
    return x - y


def multiply(x: int, y: int) -> int:
    return x * y


def divide(x: int, y: int) -> int:
    if y == 0:
        raise ValueError("Division by zero")
    return x // y


def modulo(x: int, y: int) -> int:
    if y == 0:
        raise ValueError("Division by zero")
    return x % y


# Environment primitives
def empty_environment() -> Environment:
    """Create an empty environment function"""

    def env(name: str) -> DVal:
        raise ValueError(f"Undefined identifier: {name}")

    return env


def env_lookup(env: Environment, name: str) -> DVal:
    """Look up an identifier in the environment"""
    return env(name)


def env_extend(env: Environment, name: str, value: DVal) -> Environment:
    """Create new environment with an added binding"""

    def new_env(n: str) -> DVal:
        if n == name:
            return value
        return env(n)

    return new_env


# Create initial environment with operators
def create_initial_env() -> Environment:
    """Create an environment populated with standard operators"""
    env = empty_environment()
    env = env_extend(env, "+", add)
    env = env_extend(env, "-", subtract)
    env = env_extend(env, "*", multiply)
    env = env_extend(env, "/", divide)
    env = env_extend(env, "%", modulo)
    return env


# AST Definitions (based on the mini-interpreter from Lecture 3)
@dataclass
class Number:
    value: int


@dataclass
class BinaryExpression:
    op: str
    left: Expression
    right: Expression


# Define Expression as a union type using the simplified Python 3.13 syntax
type Expression = Number | BinaryExpression


# Parse tree transformation function
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
    """Parse a string expression into an AST"""
    parse_tree = parser.parse(expression)
    return transform_parse_tree(parse_tree)


# Evaluate a parse tree with environment
def evaluate(ast: Expression, env: Environment) -> int:
    """Evaluate an expression with given environment"""
    match ast:
        case Number(value):
            return value
        case BinaryExpression(op, left, right):
            try:
                # Get operator from environment
                operator = env_lookup(env, op)

                # Ensure it's a DenOperator
                if not isinstance(operator, Callable):
                    raise ValueError(f"{op} is not a function")

                # Evaluate operands and apply operator
                left_value = evaluate(left, env)
                right_value = evaluate(right, env)

                # Apply the operator to the evaluated operands
                return operator(left_value, right_value)
            except ValueError as e:
                raise ValueError(f"Evaluation error: {e}")


def evaluate_string(expression: str) -> int:
    """Evaluate a string expression using the initial environment"""
    ast = parse_ast(expression)
    env = create_initial_env()
    return evaluate(ast, env)


# Example usage
def REPL():
    """Read-Evaluate-Print Loop with environment"""
    env = create_initial_env()
    exit = False

    print("Mini-interpreter with environment (type 'exit' to quit)")
    print("Available operators: +, -, *, /, %")
    print("Example inputs: 1+2, 3*4, 5-3, 10/2, 10%3")

    while not exit:
        expression = input("Enter an expression (exit to quit): ")
        if expression == "exit":
            exit = True
        else:
            try:
                # In a real implementation, this would use a proper parser
                # For now, we use our simplified parse_ast
                ast = parse_ast(expression)
                result = evaluate(ast, env)
                print(result)
            except Exception as e:
                print(e)


def run_tests():
    """Run some test expressions to verify the parser and evaluator"""
    test_expressions = [
        "1+2",
        "3*4",
        "5-3",
        "10/2",
        "10%3",
        "(1+2)*3",
        "1+(2*3)",
        "10/(2+3)",
        "10%(2+3)",
    ]

    env = create_initial_env()

    print("Running tests:")
    for expr in test_expressions:
        try:
            ast = parse_ast(expr)
            result = evaluate(ast, env)
            print(f"{expr} = {result}")
        except Exception as e:
            print(f"{expr} -> Error: {e}")


if __name__ == "__main__":
    # Uncomment to run the interactive REPL
    # REPL()

    # Run the tests
    run_tests()
