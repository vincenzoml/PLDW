"""
Lecture 7: Control Flow
Extends the mini-language with boolean expressions and conditional (if-then-else) expressions.
Follows the style and naming conventions of previous lectures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Any, cast
from lark import Lark, Token, Tree


# Define the semantic domains
type DenOperator = Callable[[int, int], int]
type DVal = DenOperator | int | bool  # Denotable values now include booleans

# Environment maps to locations (store addresses)
type Environment = Callable[[str], int]


# State (store) maps locations to values
class State:
    def __init__(self):
        self.store: Dict[int, Any] = {}
        self.next_loc: int = 0

    def alloc(self, value: Any) -> int:
        """Allocate a new location in the store for the value."""
        loc = self.next_loc
        self.store[loc] = value
        self.next_loc += 1
        return loc

    def update(self, loc: int, value: Any) -> None:
        """Update the value at a location."""
        if loc not in self.store:
            raise ValueError(f"Location {loc} not allocated")
        self.store[loc] = value

    def lookup(self, loc: int) -> Any:
        """Look up the value at a location."""
        if loc not in self.store:
            raise ValueError(f"Location {loc} not allocated")
        return self.store[loc]


# Environment primitives
def empty_environment() -> Environment:
    """Create an empty environment function"""

    def env(name: str) -> int:
        raise ValueError(f"Undefined identifier: {name}")

    return env


# Create initial environment with operators and initial state
def create_initial_env() -> tuple[Environment, State]:
    """Create an environment populated with standard operators and an empty state"""
    env = empty_environment()
    state = State()

    # Allocate operators in the state
    plus_loc = state.alloc(add)
    minus_loc = state.alloc(subtract)
    mult_loc = state.alloc(multiply)
    div_loc = state.alloc(divide)
    mod_loc = state.alloc(modulo)

    # Allocate comparison operators in the state
    eq_loc = state.alloc(equals)
    neq_loc = state.alloc(not_equals)
    lt_loc = state.alloc(less_than)
    gt_loc = state.alloc(greater_than)
    lte_loc = state.alloc(less_than_equals)
    gte_loc = state.alloc(greater_than_equals)

    # Allocate logical operators in the state
    and_loc = state.alloc(logical_and)
    or_loc = state.alloc(logical_or)

    # Allocate boolean constants
    true_loc = state.alloc(True)
    false_loc = state.alloc(False)

    # Bind operator names to their locations
    env = bind(env, "+", plus_loc)
    env = bind(env, "-", minus_loc)
    env = bind(env, "*", mult_loc)
    env = bind(env, "/", div_loc)
    env = bind(env, "%", mod_loc)

    # Bind comparison operators
    env = bind(env, "==", eq_loc)
    env = bind(env, "!=", neq_loc)
    env = bind(env, "<", lt_loc)
    env = bind(env, ">", gt_loc)
    env = bind(env, "<=", lte_loc)
    env = bind(env, ">=", gte_loc)

    # Bind logical operators
    env = bind(env, "and", and_loc)
    env = bind(env, "or", or_loc)

    # Bind boolean constants
    env = bind(env, "true", true_loc)
    env = bind(env, "false", false_loc)

    return env, state


def lookup_env(env: Environment, name: str) -> int:
    """Look up an identifier's location in the environment"""
    return env(name)


def bind(env: Environment, name: str, loc: int) -> Environment:
    """Create new environment with an added binding to a location"""

    def new_env(n: str) -> int:
        if n == name:
            return loc
        return env(n)

    return new_env


# Define grammar for parsing
grammar = r"""
    ?program: command_seq

    ?command_seq: command
               | command ";" command_seq
               
    ?command: assign
            | print
            
    assign: IDENTIFIER "<-" expr
    print: "print" expr
            
    ?expr: bin | mono | let | if
    mono: ground | paren | var | boolean
    paren: "(" expr ")"
    bin: expr OP mono        
    ground: NUMBER 
    boolean: "true" | "false"
    ident: IDENTIFIER
    let: "let" IDENTIFIER "=" expr "in" expr
    if: "if" expr "then" expr "else" expr
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    OP: "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<" | ">" | "<=" | ">=" | "and" | "or"

    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

# Create the Lark parser
parser = Lark(grammar, start="program")


# Define arithmetic operators
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


# Define comparison operators
def equals(x: Any, y: Any) -> bool:
    return x == y


def not_equals(x: Any, y: Any) -> bool:
    return x != y


def less_than(x: int, y: int) -> bool:
    return x < y


def greater_than(x: int, y: int) -> bool:
    return x > y


def less_than_equals(x: int, y: int) -> bool:
    return x <= y


def greater_than_equals(x: int, y: int) -> bool:
    return x >= y


# Define logical operators with short-circuit evaluation
def logical_and(x: bool, y: bool) -> bool:
    return x and y  # Python's 'and' already short-circuits


def logical_or(x: bool, y: bool) -> bool:
    return x or y  # Python's 'or' already short-circuits


# AST Definitions for Expressions
@dataclass
class Number:
    value: int


@dataclass
class Boolean:
    value: bool


@dataclass
class Var:
    name: str


@dataclass
class Let:
    name: str
    expr: Expression
    body: Expression


@dataclass
class If:
    condition: Expression
    then_branch: Expression
    else_branch: Expression


@dataclass
class BinaryExpression:
    op: str
    left: Expression
    right: Expression


# Define Expression as a union type
type Expression = Number | Boolean | Var | Let | If | BinaryExpression


# AST Definitions for Commands
@dataclass
class Assign:
    name: str
    expr: Expression


@dataclass
class Print:
    expr: Expression


@dataclass
class CommandSequence:
    first: Command
    rest: Optional[CommandSequence] = None


# Define Command as a union type
type Command = Assign | Print


# Parse tree transformation for expressions
def transform_expr_tree(tree: Tree) -> Expression:
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_expr_tree(cast(Tree, subtree))

        case Tree(data="ground", children=[Token(type="NUMBER", value=actual_value)]):
            return Number(value=int(actual_value))

        case Tree(data="boolean", children=[Token(value="true")]):
            return Boolean(value=True)

        case Tree(data="boolean", children=[Token(value="false")]):
            return Boolean(value=False)

        case Tree(data="paren", children=[subtree]):
            return transform_expr_tree(cast(Tree, subtree))

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
                left=transform_expr_tree(cast(Tree, left)),
                right=transform_expr_tree(cast(Tree, right)),
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
                expr=transform_expr_tree(cast(Tree, expr)),
                body=transform_expr_tree(cast(Tree, body)),
            )

        case Tree(
            data="if",
            children=[
                condition,
                then_branch,
                else_branch,
            ],
        ):
            return If(
                condition=transform_expr_tree(cast(Tree, condition)),
                then_branch=transform_expr_tree(cast(Tree, then_branch)),
                else_branch=transform_expr_tree(cast(Tree, else_branch)),
            )

        case x:
            print("******")
            print(x.pretty())
            print("******")
            raise ValueError(f"Unexpected parse tree structure for expression")


# Parse tree transformation for commands
def transform_command_tree(tree: Tree) -> Command:
    match tree:
        case Tree(
            data="assign",
            children=[
                Token(type="IDENTIFIER", value=name),
                expr_tree,
            ],
        ):
            return Assign(
                name=name,
                expr=transform_expr_tree(cast(Tree, expr_tree)),
            )

        case Tree(
            data="print",
            children=[expr_tree],
        ):
            return Print(
                expr=transform_expr_tree(cast(Tree, expr_tree)),
            )

        case x:
            print("******")
            print(x.pretty())
            print("******")
            raise ValueError(f"Unexpected parse tree structure for command")


# Parse tree transformation for command sequences
def transform_command_seq_tree(tree: Tree) -> CommandSequence:
    match tree:
        case Tree(
            data="command_seq",
            children=[first_command, rest_seq],
        ):
            return CommandSequence(
                first=transform_command_tree(cast(Tree, first_command)),
                rest=transform_command_seq_tree(cast(Tree, rest_seq)),
            )

        case Tree(
            data="command_seq",
            children=[single_command],
        ):
            return CommandSequence(
                first=transform_command_tree(cast(Tree, single_command)),
            )

        case x:
            print("******")
            print(x.pretty())
            print("******")
            raise ValueError(f"Unexpected parse tree structure for command sequence")


def parse_program(program_text: str) -> CommandSequence:
    """Parse a program string into a CommandSequence"""
    parse_tree = parser.parse(program_text)
    return transform_command_seq_tree(parse_tree)


# Evaluate expressions with environment and state
def evaluate_expr(expr: Expression, env: Environment, state: State) -> Any:
    """Evaluate an expression with given environment and state"""
    match expr:
        case Number(value):
            return value

        case Boolean(value):
            return value

        case BinaryExpression(op, left, right):
            try:
                # Handle short-circuit evaluation for logical operators
                if op == "and":
                    left_value = evaluate_expr(left, env, state)
                    if not left_value:  # Short-circuit if left is false
                        return False
                    right_value = evaluate_expr(right, env, state)
                    return bool(left_value and right_value)

                elif op == "or":
                    left_value = evaluate_expr(left, env, state)
                    if left_value:  # Short-circuit if left is true
                        return True
                    right_value = evaluate_expr(right, env, state)
                    return bool(left_value or right_value)

                # For other operators, evaluate both operands
                else:
                    # Get operator from environment and state
                    op_loc = lookup_env(env, op)
                    operator = state.lookup(op_loc)

                    # Ensure it's a function (DenOperator)
                    if not isinstance(operator, Callable):
                        raise ValueError(f"{op} is not a function")

                    # Evaluate operands
                    left_value = evaluate_expr(left, env, state)
                    right_value = evaluate_expr(right, env, state)

                    # Apply the operator to the evaluated operands
                    return operator(left_value, right_value)
            except ValueError as e:
                raise ValueError(f"Evaluation error: {e}")

        case Let(name, expr, body):
            # Evaluate the expression and bind it in a new location
            value = evaluate_expr(expr, env, state)
            loc = state.alloc(value)
            extended_env = bind(env, name, loc)
            return evaluate_expr(body, extended_env, state)

        case Var(name):
            # Look up variable's location and then its value in the state
            try:
                loc = lookup_env(env, name)
                return state.lookup(loc)
            except ValueError as e:
                raise ValueError(f"Variable error: {e}")

        case If(condition, then_branch, else_branch):
            # Evaluate the condition
            cond_value = evaluate_expr(condition, env, state)

            # Convert to boolean if needed
            if not isinstance(cond_value, bool):
                cond_value = bool(cond_value)

            # Evaluate the appropriate branch based on the condition
            if cond_value:
                return evaluate_expr(then_branch, env, state)
            else:
                return evaluate_expr(else_branch, env, state)


# Execute commands with environment and state
def execute_command(
    cmd: Command, env: Environment, state: State
) -> tuple[Environment, State]:
    """Execute a command, returning the updated environment and state"""
    match cmd:
        case Assign(name, expr):
            # Evaluate the expression
            value = evaluate_expr(expr, env, state)

            try:
                # If variable exists, update its value in the state
                loc = lookup_env(env, name)
                state.update(loc, value)
                return env, state
            except ValueError:
                # If variable doesn't exist, allocate a new location
                loc = state.alloc(value)
                # Create an extended environment with the new binding
                new_env = bind(env, name, loc)
                return new_env, state

        case Print(expr):
            # Evaluate the expression and print the result
            value = evaluate_expr(expr, env, state)
            print(value)
            return env, state


# Execute command sequences
def execute_command_seq(
    seq: CommandSequence, env: Environment, state: State
) -> tuple[Environment, State]:
    """Execute a command sequence, returning the final environment and state"""
    # Execute the first command
    env, state = execute_command(seq.first, env, state)

    # If there are more commands, execute them with the updated environment and state
    if seq.rest:
        return execute_command_seq(seq.rest, env, state)

    return env, state


def execute_program(program_text: str) -> tuple[Environment, State]:
    """Parse and execute a program, returning the final environment and state"""
    command_seq = parse_program(program_text)
    env, state = create_initial_env()
    return execute_command_seq(command_seq, env, state)


# Example usage
def REPL():
    """Read-Evaluate-Print Loop with stateful commands and control flow"""
    env, state = create_initial_env()
    exit = False

    print("Mini-language with control flow (type 'exit' to quit)")
    print("Commands: assign (x <- expr), print (print expr)")
    print("Expressions: arithmetic, booleans, conditionals (if-then-else)")
    print("Available operators: +, -, *, /, %, ==, !=, <, >, <=, >=, and, or")

    while not exit:
        program = input("Enter a command or program (exit to quit): ")
        if program.lower() == "exit":
            exit = True
        else:
            try:
                command_seq = parse_program(program)
                env, state = execute_command_seq(command_seq, env, state)
            except Exception as e:
                print(f"Error: {e}")


def run_tests():
    """Run some test expressions to verify the parser and evaluator"""
    test_programs = [
        # Simple boolean and conditional tests
        "x <- true; print x",
        "x <- false; print x",
        "x <- 10; y <- 20; print x < y",
        "x <- 5; print if x > 3 then x * 2 else 0",
        # Short-circuit evaluation demonstration
        "x <- false; print x and (10 / 0 > 5)",  # Should not error - short circuits
        "x <- true; print x or (10 / 0 > 5)",  # Should not error - short circuits
        # Nested conditionals
        "x <- 10; print if x < 5 then 'small' else if x < 15 then 'medium' else 'large'",
        # Conditionals with bindings
        "x <- 0; x <- if x == 0 then 42 else 0; print x",
    ]

    print("Running tests:")
    for program in test_programs:
        print(f"\nProgram: {program}")
        try:
            # Execute the program and discard the environment and state
            execute_program(program)
            print("Execution successful")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    # Uncomment to run the interactive REPL
    # REPL()

    # Run the tests
    run_tests()
