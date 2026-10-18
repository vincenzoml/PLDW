"""The same language with the usual precedence: `*`, `/`, `%` bind tighter
than `+` and `-`. Reuses the AST and evaluator of mini_interpreter.py; only
the grammar and the tree-to-AST function change.
"""

from __future__ import annotations

from lark import Lark, Token, Tree

from mini_interpreter import BinaryExpression, Expression, Number, evaluate

grammar_prec = r"""
    ?expr: sum
    ?sum: sum ADDOP prod   -> bin
        | prod
    ?prod: prod MULOP mono -> bin
         | mono
    ?mono: ground | paren
    paren: "(" expr ")"
    ground: NUMBER

    NUMBER: /[0-9]+/
    ADDOP: "+" | "-"
    MULOP: "*" | "/" | "%"

    %import common.WS
    %ignore WS
"""

parser_prec = Lark(grammar_prec, start="expr")


def transform_prec(tree: Tree) -> Expression:
    match tree:
        case Tree(data="paren", children=[subtree]):
            return transform_prec(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(
            data="bin",
            children=[left, Token(value="+" | "-" | "*" | "/" | "%" as op), right],
        ):
            return BinaryExpression(
                op=op, left=transform_prec(left), right=transform_prec(right)
            )
        case _:
            raise ValueError(f"Unexpected parse tree node: {tree}")


def parse_ast_prec(expression: str) -> Expression:
    return transform_prec(parser_prec.parse(expression))


if __name__ == "__main__":
    print(parser_prec.parse("1+2*3").pretty())
    print(parse_ast_prec("1+2*3"))
    print(evaluate(parse_ast_prec("1+2*3")))
    print(evaluate(parse_ast_prec("(1+2)*3")))
    print(evaluate(parse_ast_prec("10-4-3")))
