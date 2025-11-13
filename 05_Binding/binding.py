from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from lark import Lark, Token, Tree


# Define the semantic domains
type DenOperator = Callable[[int, int], int]
type DVal = DenOperator | int  # Denotable values: can be stored in environment

# Environment as a function
type Environment = Callable[[str], DVal]


# Environment primitives
def empty_environment() -> Environment:
    """Create an empty environment function"""

    def env(name: str) -> DVal:
        raise ValueError(f"Undefined identifier: {name}")

    return env


# Create initial environment with operators
def create_initial_env() -> Environment:
    """Create an environment populated with standard operators"""
    env = empty_environment()
    env = bind(env, "+", add)
    env = bind(env, "-", subtract)
    env = bind(env, "*", multiply)
    env = bind(env, "/", divide)
    env = bind(env, "%", modulo)
    return env


def lookup(env: Environment, name: str) -> DVal:
    """Look up an identifier in the environment"""
    return env(name)


def bind(env: Environment, name: str, value: DVal) -> Environment:
    """Create new environment with an added binding"""

    def new_env(n: str) -> DVal:
        if n == name:
            return value
        return env(n)

    return new_env


# Define grammar for parsing

# (let x = 3 in x + 1) + x
grammar = r"""
    ?expr: bin | mono | let 
    mono: ground | paren | var
    paren: "(" expr ")"
    bin: expr OP mono        
    ground: NUMBER 
    ident: IDENTIFIER
    let: "let" IDENTIFIER "=" expr "in" expr
    var: IDENTIFIER

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


# AST Definitions (based on the mini-interpreter from Lecture 3)
@dataclass
class Number:
    value: int


@dataclass
class Var:
    name: str


@dataclass
class Let:
    name: str
    expr: Expression
    body: Expression


@dataclass
class BinaryExpression:
    op: str
    left: Expression
    right: Expression


# Define Expression as a union type using the simplified Python 3.13 syntax
type Expression = Number | BinaryExpression | Let | Var


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

        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)

        case Tree(
            data="let",
            children=[
                Token(type="IDENTIFIER", value=name),
                expr,
                body,
            ],
        ):
            return Let(
                name=name,
                expr=transform_parse_tree(expr),
                body=transform_parse_tree(body),
            )

        case x:
            print("******")
            print(x.pretty())
            print("******")
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
                operator = lookup(env, op)

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
        # case Let(name, expr, body):
        #     value = evaluate(expr, env)
        #     extended_env = bind(env, name, value)
        #     return evaluate(body, extended_env)
        # case Var(name):
        #     return lookup(env, name)
        case Let(name, expr, body):
            value = evaluate(expr, env)
            extended_env = bind(env, name, value)
            return evaluate(body, extended_env)
        case Var(name):
            x = lookup(env, name)
            match x:
                case int():
                    return x
                case _:
                    raise ValueError(f"Unexpected value type: {type(x)}")


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
        "let x = 10 in x+1",
        "let x = 10 in let y = 20 in (x*(y+2))",
        "let x = 1 in let y = 2 in y + 1",
        "let x = 1 in let y = 2 in 1 + y",
        "let x = 1 in let y = 2 in (x + y)",
        "let x = 1 in let y = 2 in x + y",
        "let x = 1 in let y = 2 in y + x",
        "let x = 1 in let y = 2 in x + 1",
        "let x = 1 in let y = x+2 in 1 + x",
    ]

    env = create_initial_env()

    print("Running tests:")
    for expr in test_expressions:
        try:
            ast = parse_ast(expr)
            result = evaluate(ast, env)
            print(f"{expr} --> {result}")
        except Exception as e:
            print(f"{expr} -> Error: {e}")


if __name__ == "__main__":
    # Uncomment to run the interactive REPL
    # REPL()

    # Run the tests
    run_tests()
