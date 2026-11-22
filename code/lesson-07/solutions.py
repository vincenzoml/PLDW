"""Lecture 7, exercises 2 and 3. A solution.

Exercise 2: `and`, `or` and `not`. The second operand of `and` and `or` is
computed only when it is needed, so they are not operators: the parser turns
them into the if-then-else of expressions.

Exercise 3: `for i = e1 to e2 do c`. The parser turns it into a block with a
declaration and a while loop. The bound e2 is computed once, before the loop.

Neither exercise adds a case to evaluate or execute: the interpreter is the one
of control.py, imported unchanged. Run with `python3 solutions.py`.
"""

from __future__ import annotations

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from control import (
    Assign,
    BinaryExpression,
    Block,
    Boolean,
    Command,
    Expression,
    If,
    IfExpr,
    Let,
    Number,
    Print,
    Sequence,
    Var,
    VarDecl,
    While,
    create_initial_env,
    empty_state,
    execute_sequence,
)

grammar = r"""
    sequence: command | command ";" sequence

    ?command: vardecl | assign | print | if | while | for | block
    vardecl: "var" IDENTIFIER "=" expr
    assign: IDENTIFIER "<-" expr
    print: "print" expr
    if: "if" expr "then" command "else" command
    while: "while" expr "do" command
    for: "for" IDENTIFIER "=" expr "to" expr "do" command
    block: "{" sequence "}"

    ?expr: let | ifexpr | disj
    let: "let" IDENTIFIER "=" expr "in" expr
    ifexpr: "if" expr "then" expr "else" expr
    ?disj: conj | or
    or: disj "or" conj
    ?conj: neg | and
    and: conj "and" neg
    ?neg: test | not
    not: "not" neg
    ?test: arith | compare
    compare: arith CMP arith
    ?arith: bin | mono
    bin: arith OP mono
    mono: ground | boolean | var | paren
    paren: "(" expr ")"
    ground: NUMBER
    boolean: BOOLEAN
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    BOOLEAN: "true" | "false"
    OP: "+" | "-" | "*" | "/" | "%"
    CMP: "==" | "!=" | "<=" | ">=" | "<" | ">"
    IDENTIFIER: /(?!(let|in|var|print|if|then|else|while|do|true|false|and|or|not|for|to)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="sequence")

TRUE, FALSE = Boolean(True), Boolean(False)


def transform_expression(tree: Tree | str) -> Expression:
    match tree:
        # exercise 2: three new cases, and no new node
        case Tree(data="and", children=[left, right]):
            return IfExpr(transform_expression(left), transform_expression(right), FALSE)
        case Tree(data="or", children=[left, right]):
            return IfExpr(transform_expression(left), TRUE, transform_expression(right))
        case Tree(data="not", children=[operand]):
            return IfExpr(transform_expression(operand), FALSE, TRUE)
        # the rest is as in control.py
        case Tree(data="mono" | "paren", children=[subtree]):
            return transform_expression(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(data="boolean", children=[Token(type="BOOLEAN", value=word)]):
            return Boolean(value=(word == "true"))
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(data="bin" | "compare", children=[left, Token(value=op), right]):
            return BinaryExpression(op, transform_expression(left), transform_expression(right))
        case Tree(data="let", children=[Token(value=name), definition, body]):
            return Let(name, transform_expression(definition), transform_expression(body))
        case Tree(data="ifexpr", children=[test, then_branch, else_branch]):
            return IfExpr(
                transform_expression(test),
                transform_expression(then_branch),
                transform_expression(else_branch),
            )
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


# The bound of a for loop is kept in a variable with a space in its name: no
# program can write that name, so no program can see it or change it.
LIMIT = "for limit"


def transform_command(tree: Tree) -> Command:
    match tree:
        # exercise 3:  { var i = e1; var limit = e2; while i <= limit do { { c }; i <- i + 1 } }
        case Tree(data="for", children=[Token(value=name), start, stop, body]):
            i = Var(name)
            step = Sequence(
                Block(Sequence(transform_command(body))),
                Sequence(Assign(name, BinaryExpression("+", i, Number(1)))),
            )
            loop = While(BinaryExpression("<=", i, Var(LIMIT)), Block(step))
            return Block(
                Sequence(
                    VarDecl(name, transform_expression(start)),
                    Sequence(VarDecl(LIMIT, transform_expression(stop)), Sequence(loop)),
                )
            )
        # the rest is as in control.py
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


def run(text: str) -> None:
    execute_sequence(parse_program(text), create_initial_env(), empty_state())


if __name__ == "__main__":
    for src in [
        # exercise 2
        "var x = 0; if x != 0 and 10 / x > 1 then print 1 else print 2",
        "var x = 0; if x == 0 or 10 / x > 1 then print 1 else print 2",
        "print not 1 < 2; print not not true",
        "print true or false and false",
        "print 1 < 2 and 2 < 3",
        "print 1 and true",
        "print true and 5",
        # exercise 3
        "for i = 1 to 5 do print i * i",
        "var n = 3; for i = 1 to n do n <- n + 1; print n",
        "for i = 1 to 3 do i <- i + 1",
        "for i = 1 to 2 do print i; print i",
        "var s = 0; for i = 1 to 10 do if i % 2 == 0 then s <- s + i else s <- s; print s",
    ]:
        print(f"\n{src}")
        try:
            run(src)
        except ValueError as e:
            print(e)
