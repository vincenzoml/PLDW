"""Lecture 8, exercises 1, 3 and 4. A solution, all in one interpreter.

Exercise 1: mutual recursion. `function f(..) = .. and g(..) = ..` declares a
group of functions; at each call, every name of the group is bound again, as
functions.py does for the one name of a function.

Exercise 3: call by name. A parameter is bound to its argument, not computed,
together with the caller's environment: a Thunk. It is computed each time the
body uses it, in the store of that moment.

Exercise 4: the host's stack. A recursion too deep for Python is reported as
an error of our language, not as a Python RecursionError.

The AST and the domains are imported from functions.py. Run with
`python3 solutions.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from functions import (
    Apply,
    Assign,
    Bool,
    Environment,
    EVal,
    Expression,
    FunctionApp,
    FunctionDecl,
    IfElse,
    IfExpr,
    Let,
    Loc,
    Number,
    Operator,
    Print,
    State,
    Var,
    VarDecl,
    While,
    access,
    allocate,
    bind,
    check_arguments,
    create_initial_env,
    empty_state,
    lookup,
    show,
    transform_expression,
    update,
)

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | assign | print | ifelse | while | fundecl
    vardecl: "var" IDENTIFIER "=" expr
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    ifelse: "if" expr "then" sequence "else" sequence "endif"
    while: "while" expr "do" sequence "done"
    fundecl: "function" fundef ("and" fundef)*
    fundef: IDENTIFIER "(" params ")" "=" expr
    params: (IDENTIFIER ("," IDENTIFIER)*)?

    ?expr: let | arith
    let: "let" IDENTIFIER "=" expr "in" expr
    ?arith: bin | mono
    bin: arith OP mono
    mono: ground | var | paren | unary | funapp | ifexpr
    funapp: IDENTIFIER "(" args ")"
    args: (expr ("," expr)*)?
    ifexpr: "if" expr "then" expr "else" expr "endif"
    unary: UNOP mono
    paren: "(" expr ")"
    ground: NUMBER | BOOL
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    BOOL: "true" | "false"
    OP: "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<=" | ">=" | "<" | ">" | "and" | "or"
    UNOP: "not"
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|endif|while|do|done|true|false|and|or|not|function)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


# --- Exercise 1: a group of functions, declared together ----------------------------


@dataclass(frozen=True)
class FunctionGroup:
    functions: list[FunctionDecl]


type Command = VarDecl | Assign | Print | IfElse | While | FunctionGroup


@dataclass(frozen=True)
class Sequence:
    first: Command
    rest: Sequence | None = None


@dataclass(frozen=True)
class Closure:
    function: FunctionDecl
    env: Environment
    group: list[FunctionDecl]  # the functions declared together with it


def transform_command(tree: Tree) -> Command:
    match tree:
        case Tree(data="fundecl", children=definitions):
            functions = []
            for definition in definitions:
                name, params, body = definition.children
                functions.append(
                    FunctionDecl(str(name), [str(p) for p in params.children], transform_expression(body))
                )
            return FunctionGroup(functions)
        case Tree(data="vardecl", children=[Token(value=name), expr]):
            return VarDecl(name, transform_expression(expr))
        case Tree(data="assign", children=[Token(value=name), expr]):
            return Assign(name, transform_expression(expr))
        case Tree(data="print", children=[expr]):
            return Print(transform_expression(expr))
        case Tree(data="ifelse", children=[cond, then_branch, else_branch]):
            return IfElse(
                transform_expression(cond),
                transform_sequence(then_branch),
                transform_sequence(else_branch),
            )
        case Tree(data="while", children=[cond, body]):
            return While(transform_expression(cond), transform_sequence(body))
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def transform_sequence(tree: Tree) -> Sequence:
    match tree:
        case Tree(data="sequence", children=[command]):
            return Sequence(transform_command(command))
        case Tree(data="sequence", children=[command, rest]):
            return Sequence(transform_command(command), transform_sequence(rest))
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def parse_program(text: str) -> Sequence:
    try:
        tree = parser.parse(text)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return transform_sequence(tree)


# --- Exercise 3: a parameter stands for an expression not computed yet --------------


@dataclass(frozen=True)
class Thunk:
    expr: Expression
    env: Environment  # the caller's: the argument was written there


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value) | Bool(value):
            return value
        case Var(name):
            match lookup(env, name):
                case Loc() as loc:
                    return access(state, loc)
                case int() | bool() as value:
                    return value
                case Thunk(expr, thunk_env):  # exercise 3: computed now, at each use
                    return evaluate(expr, thunk_env, state)
                case _:
                    raise ValueError(f"{name} is not a value")
        case Apply(op, args):
            values = [evaluate(arg, env, state) for arg in args]
            match lookup(env, op):
                case Operator(type=(expected_types, _), fn=fn):
                    check_arguments(op, expected_types, values)
                    return fn(values)
                case _:
                    raise ValueError(f"{op} is not an operator")
        case Let(name, definition, body):
            value = evaluate(definition, env, state)
            return evaluate(body, bind(env, name, value), state)
        case IfExpr(cond, then_branch, else_branch):
            if evaluate_condition(cond, env, state):
                return evaluate(then_branch, env, state)
            return evaluate(else_branch, env, state)
        case FunctionApp(name, args):
            closure = lookup(env, name)
            if not isinstance(closure, Closure):
                raise ValueError(f"{name} is not a function")
            function = closure.function
            if len(args) != len(function.params):
                raise ValueError(
                    f"Function {name} expects {len(function.params)} arguments, got {len(args)}"
                )
            call_env = closure.env
            for other in closure.group:  # exercise 1: the whole group, not only name
                call_env = bind(call_env, other.name, Closure(other, closure.env, closure.group))
            for param, arg in zip(function.params, args):
                call_env = bind(call_env, param, Thunk(arg, env))  # exercise 3
            return evaluate(function.body, call_env, state)


def evaluate_condition(cond: Expression, env: Environment, state: State) -> bool:
    value = evaluate(cond, env, state)
    if type(value) is not bool:
        raise ValueError(f"Condition must be a boolean, got {show(value)}")
    return value


def execute_block(block: Sequence, env: Environment, state: State) -> State:
    _, new_state = execute_sequence(block, env, state)
    return State(store=new_state.store, next_loc=state.next_loc)


def execute(command: Command, env: Environment, state: State) -> tuple[Environment, State]:
    match command:
        case VarDecl(name, expr):
            loc, state = allocate(state, evaluate(expr, env, state))
            return bind(env, name, loc), state
        case Assign(name, expr):
            loc = lookup(env, name)
            if not isinstance(loc, Loc):
                raise ValueError(f"{name} is not a variable")
            return env, update(state, loc, evaluate(expr, env, state))
        case Print(expr):
            print(show(evaluate(expr, env, state)))
            return env, state
        case IfElse(cond, then_branch, else_branch):
            if evaluate_condition(cond, env, state):
                return env, execute_block(then_branch, env, state)
            return env, execute_block(else_branch, env, state)
        case While(cond, body):
            while evaluate_condition(cond, env, state):
                state = execute_block(body, env, state)
            return env, state
        case FunctionGroup(functions):
            new_env = env
            for function in functions:
                new_env = bind(new_env, function.name, Closure(function, env, functions))
            return new_env, state


def execute_sequence(
    sequence: Sequence, env: Environment, state: State
) -> tuple[Environment, State]:
    env, state = execute(sequence.first, env, state)
    if sequence.rest is None:
        return env, state
    return execute_sequence(sequence.rest, env, state)


# --- Exercise 4: Python's limit, reported in our language -----------------------------


def run(text: str) -> None:
    program = parse_program(text)
    try:
        execute_sequence(program, create_initial_env(), empty_state())
    except RecursionError:
        raise ValueError("Recursion too deep: the interpreter ran out of stack") from None


if __name__ == "__main__":
    for src in [
        # exercise 1
        "function even(n) = if n == 0 then true else odd(n - 1) endif "
        "and odd(n) = if n == 0 then false else even(n - 1) endif; print even(10); print odd(7)",
        "function fact(n) = if n == 0 then 1 else n * fact(n - 1) endif; print fact(5)",
        # exercise 3
        "function f(x) = 0; print f(1 / 0)",
        "function twice(x) = x + x; var n = 1; print twice(n * 10)",
        "var k = 1; function f(x) = let k = 100 in x; print f(k)",
        # exercise 4
        "function count(n) = if n == 0 then 0 else 1 + count(n - 1) endif; print count(1000)",
    ]:
        print(f"\n{src}")
        try:
            run(src)
        except ValueError as e:
            print(e)
