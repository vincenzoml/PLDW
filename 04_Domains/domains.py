from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Literal, TypeAlias, Union


# Define the semantic domains
# Using Python 3.13 simplified syntax for union types
type Num = int  # A type alias for integers
type DenOperator = Callable[[int, int], int]
type DVal = int | DenOperator  # Denotable values: can be stored in environment
type MVal = int  # Memorizable values: can be stored in memory/state
type Location = int  # Memory locations

# Environment and State as functions
type Environment = Callable[[str], DVal]
type State = Callable[[Location], MVal]


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
    try:
        return env(name)
    except ValueError:
        raise ValueError(f"Undefined identifier: {name}")


def env_extend(env: Environment, name: str, value: DVal) -> Environment:
    """Create new environment with an added binding"""

    def new_env(n: str) -> DVal:
        if n == name:
            return value
        return env(n)

    return new_env


# Memory (State) primitives
def empty_memory() -> State:
    """Create an empty memory state function"""

    def state(location: Location) -> MVal:
        raise ValueError(f"Undefined memory location: {location}")

    return state


def state_lookup(state: State, location: Location) -> MVal:
    """Look up a value at a given location in the state"""
    try:
        return state(location)
    except ValueError:
        raise ValueError(f"Undefined memory location: {location}")


def state_update(state: State, location: Location, value: MVal) -> State:
    """Create new state with an updated value at given location"""

    def new_state(loc: Location) -> MVal:
        if loc == location:
            return value
        return state(loc)

    return new_state


# Memory allocation requires a bit more sophistication when using functions
# We'll need to track the next available location
class MemoryAllocator:
    def __init__(self):
        self.next_location = 0

    def allocate(self, state: State, value: MVal) -> tuple[State, Location]:
        """Allocate a new memory location and store value there.
        Returns the updated state and the new location."""
        location = self.next_location
        self.next_location += 1
        new_state = state_update(state, location, value)
        return new_state, location


# Create a global allocator instance
memory_allocator = MemoryAllocator()


def allocate(state: State, value: MVal) -> tuple[State, Location]:
    """Allocate a new memory location and store a value there."""
    return memory_allocator.allocate(state, value)


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


# Evaluate a parse tree with environment
def evaluate(ast: Expression, env: Environment) -> MVal:
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


# Parse function (simplified, would be replaced by actual parser)
def parse_ast(expression: str) -> Expression:
    """Parse a string expression into an AST (simplified example)"""
    # This is a placeholder - in a real implementation,
    # this would use the Lark parser from Chapter 3
    if expression == "1+2":
        return BinaryExpression(op="+", left=Number(value=1), right=Number(value=2))
    elif expression == "3*4":
        return BinaryExpression(op="*", left=Number(value=3), right=Number(value=4))
    else:
        # Very basic fallback
        try:
            return Number(value=int(expression))
        except ValueError:
            raise ValueError(f"Cannot parse expression: {expression}")


def evaluate_string(expression: str) -> MVal:
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


if __name__ == "__main__":
    REPL()
