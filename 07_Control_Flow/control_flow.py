"""
Lecture 7: Control flow
Extends the mini-language with control flow constructs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, cast
from lark import Lark, Token, Tree


# Define the semantic domains
@dataclass
class Loc:
    address: int


type EVal = int | bool  # Expressible value type (for expressions)
type MVal = EVal  # Main value type for store and evaluation (expressible)
type DVal = EVal | Loc | Operator  # Denotable values: can be associated with names

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


# Operator dataclass for arity and function
@dataclass
class Operator:
    arity: int
    fn: Callable[[list[EVal]], EVal]


# Update all operator functions to take a list of arguments
def add(args):
    return args[0] + args[1]


def subtract(args):
    return args[0] - args[1]


def multiply(args):
    return args[0] * args[1]


def divide(args):
    if args[1] == 0:
        raise ValueError("Division by zero")
    return args[0] // args[1]


def modulo(args):
    if args[1] == 0:
        raise ValueError("Division by zero")
    return args[0] % args[1]


def eq(args):
    return args[0] == args[1]


def ne(args):
    return args[0] != args[1]


def lt(args):
    return args[0] < args[1]


def gt(args):
    return args[0] > args[1]


def le(args):
    return args[0] <= args[1]


def ge(args):
    return args[0] >= args[1]


def land(args):
    if not (isinstance(args[0], bool) and isinstance(args[1], bool)):
        raise ValueError("and expects booleans")
    return args[0] and args[1]


def lor(args):
    if not (isinstance(args[0], bool) and isinstance(args[1], bool)):
        raise ValueError("or expects booleans")
    return args[0] or args[1]


def lnot(args):
    if not isinstance(args[0], bool):
        raise ValueError("not expects a boolean")
    return not args[0]


# Create initial environment with operators and initial state
def create_initial_env_state() -> tuple[Environment, State]:
    """Create an environment populated with standard operators and an empty state"""
    env = empty_environment()
    state = empty_state()

    # Arithmetic operators
    env = bind(env, "+", Operator(2, add))
    env = bind(env, "-", Operator(2, subtract))
    env = bind(env, "*", Operator(2, multiply))
    env = bind(env, "/", Operator(2, divide))
    env = bind(env, "%", Operator(2, modulo))
    # Relational operators
    env = bind(env, "==", Operator(2, eq))
    env = bind(env, "!=", Operator(2, ne))
    env = bind(env, "<", Operator(2, lt))
    env = bind(env, ">", Operator(2, gt))
    env = bind(env, "<=", Operator(2, le))
    env = bind(env, ">=", Operator(2, ge))
    # Boolean operators
    env = bind(env, "and", Operator(2, land))
    env = bind(env, "or", Operator(2, lor))
    env = bind(env, "not", Operator(1, lnot))

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
            | ifelse
            | while
            
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    vardecl: "var" IDENTIFIER "=" expr
    ifelse: "if" expr "then" command_seq "else" command_seq
    while: "while" expr "do" command_seq
            
    ?expr: bin | mono | let
    mono: ground | paren | var | unary
    paren: "(" expr ")"
    bin: expr OP mono
    unary: UNOP mono
    ground: NUMBER | BOOL
    var: IDENTIFIER
    let: "let" IDENTIFIER "=" expr "in" expr

    NUMBER: /[0-9]+/
    BOOL: "true" | "false"
    OP: "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<" | ">" | "<=" | ">=" | "and" | "or"
    UNOP: "not"

    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

# Create the Lark parser
parser = Lark(grammar, start="program")


# AST Definitions for Expressions (based on Lecture 5)
@dataclass
class Number:
    value: int


@dataclass
class Var:
    name: str


@dataclass
class Apply:
    op: str
    args: list[Expression]


@dataclass
class Let:
    name: str
    expr: Expression
    body: Expression


# Define Expression as a union type
type Expression = Number | Var | Let | Apply


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


@dataclass
class IfElse:
    cond: Expression
    then_branch: CommandSequence
    else_branch: CommandSequence


@dataclass
class While:
    cond: Expression
    body: CommandSequence


# Update Command type comment
type Command = Assign | Print | VarDecl | IfElse | While


# Parse tree transformation for expressions
def transform_expr_tree(tree: Tree) -> Expression:
    # NOTE: The distinction between unary and binary operator parse tree nodes is necessary here
    # because the grammar and parse tree structure are different for prefix (unary) and infix (binary) ops.
    # However, both are unified as Apply nodes in the AST for evaluation and further processing.
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_expr_tree(cast(Tree, subtree))
        case Tree(data="ground", children=[Token(type="NUMBER", value=actual_value)]):
            return Number(value=int(actual_value))
        case Tree(data="ground", children=[Token(type="BOOL", value=actual_value)]):
            return Number(value=True if actual_value == "true" else False)
        case Tree(data="paren", children=[subtree]):
            return transform_expr_tree(cast(Tree, subtree))
        case Tree(data="bin", children=[left, Token(type="OP", value=op), right]):
            return Apply(
                op=op,
                args=[
                    transform_expr_tree(cast(Tree, left)),
                    transform_expr_tree(cast(Tree, right)),
                ],
            )
        case Tree(data="unary", children=[Token(type="UNOP", value=op), expr]):
            return Apply(op=op, args=[transform_expr_tree(cast(Tree, expr))])
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(
            data="let", children=[Token(type="IDENTIFIER", value=name), expr, body]
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

        case Tree(
            data="ifelse",
            children=[cond_tree, then_tree, else_tree],
        ):
            return IfElse(
                cond=transform_expr_tree(cast(Tree, cond_tree)),
                then_branch=transform_command_seq_tree(cast(Tree, then_tree)),
                else_branch=transform_command_seq_tree(cast(Tree, else_tree)),
            )

        case Tree(
            data="while",
            children=[cond_tree, body_tree],
        ):
            return While(
                cond=transform_expr_tree(cast(Tree, cond_tree)),
                body=transform_command_seq_tree(cast(Tree, body_tree)),
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
        case Apply(op, args):
            arg_vals = [
                evaluate_expr(a, env, state) for a in args
            ]  # python idiom for list comprehension
            op_val = lookup(env, op)
            if isinstance(op_val, Operator):
                if op_val.arity != len(arg_vals):
                    raise ValueError(
                        f"Operator '{op}' expects {op_val.arity} arguments, got {len(arg_vals)}"
                    )
                return op_val.fn(arg_vals)
            raise ValueError(f"{op} is not an operator")
        case Var(name):
            try:
                dval = lookup(env, name)
                match dval:
                    case int() | bool():
                        return dval
                    case Loc(address=addr):
                        return access(state, addr)
                    case _:
                        raise ValueError(f"Variable '{name}' does not refer to a value")
            except ValueError as e:
                raise ValueError(f"Variable error: {e}")
        case Let(name, expr, body):
            value = evaluate_expr(expr, env, state)
            extended_env = bind(env, name, value)
            return evaluate_expr(body, extended_env, state)
        case _:
            raise ValueError(f"Unexpected expression type: {expr}")


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
        case IfElse(cond, then_branch, else_branch):
            cond_val = evaluate_expr(cond, env, state)
            if not isinstance(cond_val, bool):
                raise ValueError("If condition must be boolean")
            if cond_val:
                return execute_command_seq(then_branch, env, state)
            else:
                return execute_command_seq(else_branch, env, state)
        case While(cond, body):
            cond_val = evaluate_expr(cond, env, state)
            if not isinstance(cond_val, bool):
                raise ValueError("While condition must be boolean")
            if cond_val:
                env1, state1 = execute_command_seq(body, env, state)
                return execute_command(While(cond, body), env1, state1)
            else:
                return env, state
        case _:
            raise ValueError(f"Unknown command type: {cmd}")


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
        # 1. If-then-else on a variable
        "var x = 1; if x == 1 then print 42 else print 0",
        # 1b. If-then-else on a boolean
        "if true then print 1 else print 0",
        # 2. Print N times by decrementing a variable
        "var n = 3; while n > 0 do (print n; n <- n - 1)",
        # 3. Euclid's algorithm using subtraction
        "var a = 48; var b = 18; while b != 0 do (if a > b then a <- a - b else b <- b - a); print a",
    ]

    print("Running tests:")
    for program in test_programs:
        print(f"\nProgram: {program}")
        try:
            execute_program(program)
            print("Execution successful")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    # Uncomment to run the interactive REPL
    # REPL()

    # Run the tests
    run_tests()
