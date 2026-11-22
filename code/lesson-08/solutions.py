"""Lecture 8, exercises 2 and 3. A solution.

Exercise 2: parameters passed by reference. In `proc swap(ref a, ref b) c` the
parameters marked `ref` are not new variables: each one is bound to the
location of the variable passed as argument.

Exercise 3: functions as values. A name bound to a function can be passed as
an argument, held by a variable, and returned by another function.

The AST of expressions, the domains and the operators are imported from
functions.py. Run with `python3 solutions.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from functions import (
    Assign,
    BinaryExpression,
    Block,
    Boolean,
    Call,
    Environment,
    Expression,
    FunDecl,
    If,
    IfExpr,
    Let,
    Loc,
    Number,
    Print,
    State,
    Var,
    VarDecl,
    While,
    access,
    allocate,
    bind,
    create_initial_env,
    empty_state,
    lookup,
    transform_args,
    transform_expression,
    transform_names,
    update,
)
from functions import Function
from functions import show as show_value

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | assign | print | if | while | block
            | fundecl | procdecl | callcmd
    vardecl: "var" IDENTIFIER "=" expr
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    if: "if" expr "then" command "else" command
    while: "while" expr "do" command
    block: "{" sequence "}"
    fundecl: "fun" IDENTIFIER "(" params ")" "=" expr
    procdecl: "proc" IDENTIFIER "(" procparams ")" command
    callcmd: IDENTIFIER "(" args ")"
    params: (IDENTIFIER ("," IDENTIFIER)*)?
    procparams: (param ("," param)*)?
    ?param: IDENTIFIER | ref
    ref: "ref" IDENTIFIER
    args: (expr ("," expr)*)?

    ?expr: let | ifexpr | test
    let: "let" IDENTIFIER "=" expr "in" expr
    ifexpr: "if" expr "then" expr "else" expr
    ?test: arith | compare
    compare: arith CMP arith
    ?arith: bin | mono
    bin: arith OP mono
    mono: ground | boolean | call | var | paren
    call: IDENTIFIER "(" args ")"
    paren: "(" expr ")"
    ground: NUMBER
    boolean: BOOLEAN
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    BOOLEAN: "true" | "false"
    OP: "+" | "-" | "*" | "/" | "%"
    CMP: "==" | "!=" | "<=" | ">=" | "<" | ">"
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|while|do|true|false|fun|proc|ref)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")


# --- Exercise 2: a procedure knows which parameters are by reference -----------


@dataclass(frozen=True)
class ProcDecl:
    name: str
    params: tuple[str, ...]
    refs: frozenset[str]  # the parameters marked ref
    body: Command


@dataclass(frozen=True)
class CallCommand:
    name: str
    args: tuple[Expression, ...]


type Command = (
    VarDecl | Assign | Print | If | While | Block | FunDecl | ProcDecl | CallCommand
)


@dataclass(frozen=True)
class Sequence:
    first: Command
    rest: Sequence | None = None


@dataclass(frozen=True)
class Procedure:
    params: tuple[str, ...]
    refs: frozenset[str]
    body: Command
    env: Environment


def transform_command(tree: Tree) -> Command:
    match tree:
        case Tree(data="procdecl", children=[Token(value=name), Tree(children=params), body]):
            names = tuple(p.children[0] if isinstance(p, Tree) else p for p in params)
            refs = frozenset(p.children[0] for p in params if isinstance(p, Tree))
            return ProcDecl(str(name), tuple(map(str, names)), frozenset(map(str, refs)),
                            transform_command(body))
        case Tree(data="callcmd", children=[Token(value=name), args]):
            return CallCommand(name, transform_args(args))
        case Tree(data="fundecl", children=[Token(value=name), params, body]):
            return FunDecl(name, transform_names(params), transform_expression(body))
        case Tree(data="vardecl", children=[Token(value=name), expr]):
            return VarDecl(name, transform_expression(expr))
        case Tree(data="assign", children=[Token(value=name), expr]):
            return Assign(name, transform_expression(expr))
        case Tree(data="print", children=[expr]):
            return Print(transform_expression(expr))
        case Tree(data="if", children=[test, then_branch, else_branch]):
            return If(
                transform_expression(test),
                transform_command(then_branch),
                transform_command(else_branch),
            )
        case Tree(data="while", children=[test, body]):
            return While(transform_expression(test), transform_command(body))
        case Tree(data="block", children=[sequence]):
            return Block(transform_sequence(sequence))
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


# --- Exercise 3: a function is a value -------------------------------------------

type EVal = int | bool | Function


def show(value: EVal) -> str:
    if isinstance(value, Function):
        return f"a function of {len(value.params)} argument(s)"
    return show_value(value)


def check_arity(name: str, params: tuple[str, ...], values: list[EVal]) -> None:
    if len(values) != len(params):
        raise ValueError(f"{name} takes {len(params)} argument(s), not {len(values)}")


def evaluate(ast: Expression, env: Environment, state: State) -> EVal:
    match ast:
        case Number(value) | Boolean(value):
            return value
        case Var(name):
            match lookup(env, name):
                case Loc() as loc:
                    return access(state, loc)
                case bool() | int() | Function() as value:  # exercise 3: a function too
                    return value
                case _:
                    raise ValueError(f"{name} is not a value")
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if not callable(operator):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env, state), evaluate(right, env, state))
        case Let(name, definition, body):
            value = evaluate(definition, env, state)
            return evaluate(body, bind(env, name, value), state)
        case IfExpr(test, then_branch, else_branch):
            if condition(test, env, state):
                return evaluate(then_branch, env, state)
            return evaluate(else_branch, env, state)
        case Call(name, args):
            function = lookup(env, name)
            if isinstance(function, Loc):  # exercise 3: a variable that holds a function
                function = access(state, function)
            if not isinstance(function, Function):
                raise ValueError(f"{name} is not a function")
            values = [evaluate(arg, env, state) for arg in args]
            check_arity(name, function.params, values)
            call_env = function.env
            for param, value in zip(function.params, values):
                call_env = bind(call_env, param, value)
            return evaluate(function.body, call_env, state)


def condition(test: Expression, env: Environment, state: State) -> bool:
    value = evaluate(test, env, state)
    if type(value) is not bool:
        raise ValueError(f"The condition is {show(value)}, not true or false")
    return value


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
        case If(test, then_branch, else_branch):
            branch = then_branch if condition(test, env, state) else else_branch
            _, state = execute(branch, env, state)
            return env, state
        case While(test, body):
            while condition(test, env, state):
                _, state = execute(body, env, state)
            return env, state
        case Block(body):
            _, state = execute_sequence(body, env, state)
            return env, state
        case FunDecl(name, params, body):

            def env_with_function(n: str) -> object:
                return function if n == name else env(n)

            function = Function(params, body, env_with_function)
            return env_with_function, state
        case ProcDecl(name, params, refs, body):

            def env_with_procedure(n: str) -> object:
                return procedure if n == name else env(n)

            procedure = Procedure(params, refs, body, env_with_procedure)
            return env_with_procedure, state
        case CallCommand(name, args):
            callee = lookup(env, name)
            if not isinstance(callee, Procedure):
                raise ValueError(f"{name} is not a procedure")
            if len(args) != len(callee.params):
                raise ValueError(f"{name} takes {len(callee.params)} argument(s), not {len(args)}")
            call_env = callee.env
            for param, arg in zip(callee.params, args):
                if param in callee.refs:  # exercise 2: the location of the argument
                    loc = lookup(env, arg.name) if isinstance(arg, Var) else None
                    if not isinstance(loc, Loc):
                        raise ValueError(f"The argument for ref {param} must be a variable")
                else:
                    loc, state = allocate(state, evaluate(arg, env, state))
                call_env = bind(call_env, param, loc)
            _, state = execute(callee.body, call_env, state)
            return env, state


def execute_sequence(
    sequence: Sequence, env: Environment, state: State
) -> tuple[Environment, State]:
    env, state = execute(sequence.first, env, state)
    if sequence.rest is None:
        return env, state
    return execute_sequence(sequence.rest, env, state)


def run(text: str) -> None:
    execute_sequence(parse_program(text), create_initial_env(), empty_state())


if __name__ == "__main__":
    for src in [
        # exercise 2
        "proc swap(ref a, ref b) { var t = a; a <- b; b <- t }; "
        "var x = 1; var y = 2; swap(x, y); print x; print y",
        "proc inc(ref n) n <- n + 1; var a = 5; inc(a); inc(a); print a",
        "proc inc(n) n <- n + 1; var a = 5; inc(a); inc(a); print a",
        "proc inc(ref n) n <- n + 1; inc(3)",
        "proc twice(ref a, ref b) { a <- a + 1; b <- b + 1 }; var x = 0; twice(x, x); print x",
        # exercise 3
        "fun twice(f, x) = f(f(x)); fun inc(x) = x + 1; print twice(inc, 5)",
        "fun inc(x) = x + 1; fun dec(x) = x - 1; "
        "fun pick(b) = if b then inc else dec; var g = pick(false); print g(5)",
        "fun inc(x) = x + 1; print inc",
        "var k = 10; fun addk(x) = x + k; fun apply(f, k) = f(1); print apply(addk, 100)",
        "fun twice(f, x) = f(f(x)); print twice(3, 5)",
    ]:
        print(f"\n{src}")
        try:
            run(src)
        except ValueError as e:
            print(e)
