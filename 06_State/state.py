"""
Lecture 6: State
Extends the mini-language with state manipulation through commands and command sequences.
Introduces a new syntax level beyond expressions: commands and command sequences.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, cast
from lark import Lark, Token, Tree


# Define the semantic domains
@dataclass
class Loc:
    address: int


type DenOperator = Callable[[int, int], int]
type EVal = int  # Expressible value type (for expressions)
type MVal = EVal  # Main value type for store and evaluation (expressible)
type DVal = EVal | DenOperator | Loc  # Denotable values: can be associated with names

type Environment = Callable[[str], DVal]


# State (store) maps locations to memorizable values (MVal)
@dataclass
class State:
    store: Callable[[int], MVal]
    next_loc: int


def empty_store() -> Callable[[int], MVal]:
    def store_fn(loc: int) -> MVal:
        raise ValueError(f"Location {loc} not allocated")

    return store_fn


def empty_state() -> State:
    return State(store=empty_store(), next_loc=0)


def allocate(state: State, value: MVal) -> tuple[Loc, State]:
    loc = Loc(state.next_loc)
    prev_store = state.store

    def new_store(l: int) -> MVal:
        if l == loc.address:
            return value
        return prev_store(l)

    return loc, State(store=new_store, next_loc=loc.address + 1)


def update(state: State, addr: int, value: MVal) -> State:
    prev_store = state.store

    def new_store(l: int) -> MVal:
        if l == addr:
            return value
        return prev_store(l)

    return State(store=new_store, next_loc=state.next_loc)


def access(state: State, addr: int) -> MVal:
    return state.store(addr)


# Environment primitives
def empty_environment() -> Environment:
    """Create an empty environment function"""

    def env(name: str) -> int:
        raise ValueError(f"Undefined identifier: {name}")

    return env


# Create initial environment with operators and initial state
def create_initial_env_state() -> tuple[Environment, State]:
    """Create an environment populated with standard operators and an empty state"""
    env = empty_environment()
    state = empty_state()

    # Bind operator names directly to their functions (DenOperator)
    env = bind(env, "+", add)
    env = bind(env, "-", subtract)
    env = bind(env, "*", multiply)
    env = bind(env, "/", divide)
    env = bind(env, "%", modulo)

    return env, state


def lookup(env: Environment, name: str) -> DVal:
    """Look up an identifier's denotable value in the environment"""
    return env(name)


def bind(env: Environment, name: str, value: DVal) -> Environment:
    """Create new environment with an added binding to a denotable value (location or operator)"""

    def new_env(n: str) -> DVal:
        if n == name:
            return value
        return env(n)

    return new_env


# Define grammar for parsing
grammar = r"""
    ?program: command_seq

    ?command_seq: command
               | command ";" command_seq
               
    ?command: assign
            | print
            | vardecl
            
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    vardecl: "var" IDENTIFIER "=" expr
            
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

# Create the Lark parser
parser = Lark(grammar, start="program")


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


# AST Definitions for Expressions (based on Lecture 5)
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


# Define Expression as a union type
type Expression = Number | BinaryExpression | Let | Var


# AST Definitions for Commands
@dataclass
class Assign:
    name: str
    expr: Expression


@dataclass
class Print:
    expr: Expression


@dataclass
class VarDecl:
    name: str
    expr: Expression


@dataclass
class CommandSequence:
    first: Command
    rest: Optional[CommandSequence] = None


# Define Command as a union type
type Command = Assign | Print | VarDecl


# Parse tree transformation for expressions
def transform_expr_tree(tree: Tree) -> Expression:
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_expr_tree(cast(Tree, subtree))

        case Tree(data="ground", children=[Token(type="NUMBER", value=actual_value)]):
            return Number(value=int(actual_value))

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

        case Tree(
            data="vardecl",
            children=[Token(type="IDENTIFIER", value=name), expr_tree],
        ):
            return VarDecl(
                name=name,
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

        # Handle the case where the root is a single command node
        case _ if tree.data in {"vardecl", "assign", "print"}:
            return CommandSequence(
                first=transform_command_tree(tree),
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
def evaluate_expr(expr: Expression, env: Environment, state: State) -> EVal:
    """Evaluate an expression with given environment and state"""
    match expr:
        case Number(value):
            return value

        case BinaryExpression(op, left, right):
            try:
                op_val = lookup(env, op)
                match op_val:
                    case fn if callable(fn):
                        left_value = evaluate_expr(left, env, state)
                        right_value = evaluate_expr(right, env, state)
                        return fn(left_value, right_value)
                    case _:
                        raise ValueError(f"{op} is not a function")
            except ValueError as e:
                raise ValueError(f"Evaluation error: {e}")

        case Let(name, expr, body):
            value = evaluate_expr(expr, env, state)
            extended_env = bind(env, name, value)
            return evaluate_expr(body, extended_env, state)

        case Var(name):
            try:
                dval = lookup(env, name)
                match dval:
                    case int():
                        return dval
                    case Loc(address=addr):
                        return access(state, addr)
                    case _:
                        raise ValueError(f"Variable '{name}' does not refer to a value")
            except ValueError as e:
                raise ValueError(f"Variable error: {e}")


# Execute commands with environment and state
def execute_command(
    cmd: Command, env: Environment, state: State
) -> tuple[Environment, State]:
    """Execute a command, returning the updated environment and state"""
    match cmd:
        case VarDecl(name, expr):
            value = evaluate_expr(expr, env, state)
            loc, state1 = allocate(state, value)
            new_env = bind(env, name, loc)
            return new_env, state1
        case Assign(name, expr):
            try:
                dval = lookup(env, name)
                match dval:
                    case Loc(address=addr) as loc:
                        value = evaluate_expr(expr, env, state)
                        state1 = update(state, addr, value)
                        return env, state1
                    case _:
                        raise ValueError(
                            f"Assignment target '{name}' is not a variable"
                        )
            except ValueError:
                raise ValueError(f"Assignment to undeclared variable '{name}'")

        case Print(expr):
            # MORALLY THIS IS THE IDENTITY FUNCTION
            value = evaluate_expr(expr, env, state)
            print(value)
            return env, state


# Execute command sequences
def execute_command_seq(
    seq: CommandSequence, env: Environment, state: State
) -> tuple[Environment, State]:
    """Execute a command sequence, returning the final environment and state"""
    # Execute the first command
    env1, state1 = execute_command(seq.first, env, state)

    # If there are more commands, execute them with the updated environment and state
    if seq.rest:
        return execute_command_seq(seq.rest, env1, state1)

    return env1, state1


def execute_program(program_text: str) -> tuple[Environment, State]:
    """Parse and execute a program, returning the final environment and state"""
    command_seq = parse_program(program_text)
    env, state = create_initial_env_state()
    return execute_command_seq(command_seq, env, state)


# Example usage
def REPL():
    """Read-Evaluate-Print Loop with stateful commands"""
    env, state = create_initial_env_state()
    exit = False

    print("Mini-language with state (type 'exit' to quit)")
    print("Commands: declare (var x = expr), assign (x <- expr), print (print expr)")
    print("Available operators: +, -, *, /, %")

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
        # Simple declaration, assignment, and printing
        "var x = 42; print x",
        # Multiple declarations and assignments
        "var x = 10; var y = x + 5; print y",
        # Updating variables
        "var x = 10; print x; x <- 20; print x",
        # Using let expressions in commands
        "var x = let y = 5 in y * 2; print x",
        # Longer program with multiple operations
        "var x = 10; var y = 20; var z = x + y; print z; x <- 30; print x + y",
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
