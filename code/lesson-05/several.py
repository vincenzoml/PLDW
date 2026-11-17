"""Lecture 5, exercise 3: several names in one let. A solution.

    let x = 1, y = 2 in x + y

The AST and the evaluator are those of binding.py: a let with several names
is transformed into nested Lets, so evaluate does not change. Two meanings,
two transformations:

- sequential: each definition sees the names before it (let* in Scheme);
- simultaneous: no definition sees any of them (let ... and ... in OCaml),
  and no name can appear twice.

Run with `python3 several.py`.
"""

from __future__ import annotations

from collections.abc import Callable

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from binding import (
    BinaryExpression,
    Expression,
    Let,
    Number,
    Var,
    create_initial_env,
    evaluate,
)

grammar = r"""
    ?expr: let | arith
    let: "let" binding ("," binding)* "in" expr
    binding: IDENTIFIER "=" expr
    ?arith: bin | mono
    bin: arith OP mono
    mono: ground | var | paren
    paren: "(" expr ")"
    ground: NUMBER
    var: IDENTIFIER

    NUMBER: /[0-9]+/
    OP: "+" | "-" | "*" | "/" | "%"
    IDENTIFIER: /(?!(let|in)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="expr")

type Bindings = list[tuple[str, Expression]]


def sequential(bindings: Bindings, body: Expression) -> Expression:
    """let x = 1, y = x + 1 in b   becomes   let x = 1 in let y = x + 1 in b"""
    for name, definition in reversed(bindings):
        body = Let(name, definition, body)
    return body


def simultaneous(bindings: Bindings, body: Expression) -> Expression:
    """let x = e1, y = e2 in b   becomes
    let #0 = e1 in let #1 = e2 in let x = #0 in let y = #1 in b

    #0 and #1 are names that no program can write, as + is: so e2 cannot
    see them, and it sees the x of the environment outside, if there is one.

    The names are bound together, so the same name cannot appear twice:
    let x = 1, x = 2 in x is an error, as in Scheme and OCaml.
    """
    names = [name for name, _ in bindings]
    for name in names:
        if names.count(name) > 1:
            raise ValueError(f"{name} is bound twice")
    hidden = [(f"#{i}", definition) for i, (_, definition) in enumerate(bindings)]
    renamed = [(name, Var(f"#{i}")) for i, (name, _) in enumerate(bindings)]
    return sequential(hidden + renamed, body)


type Meaning = Callable[[Bindings, Expression], Expression]


def transform_parse_tree(tree: Tree | str, meaning: Meaning) -> Expression:
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_parse_tree(subtree, meaning)
        case Tree(data="paren", children=[subtree]):
            return transform_parse_tree(subtree, meaning)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=int(digits))
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(data="bin", children=[left, Token(type="OP", value=op), right]):
            return BinaryExpression(
                op=op,
                left=transform_parse_tree(left, meaning),
                right=transform_parse_tree(right, meaning),
            )
        case Tree(data="let", children=[*bindings, body]):
            pairs = [transform_binding(b, meaning) for b in bindings]
            return meaning(pairs, transform_parse_tree(body, meaning))
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def transform_binding(tree: Tree, meaning: Meaning) -> tuple[str, Expression]:
    match tree:
        case Tree(
            data="binding",
            children=[Token(type="IDENTIFIER", value=name), definition],
        ):
            return name, transform_parse_tree(definition, meaning)
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def parse_ast(expression: str, meaning: Meaning = sequential) -> Expression:
    try:
        tree = parser.parse(expression)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return transform_parse_tree(tree, meaning)


if __name__ == "__main__":
    print(parse_ast("let x = 1, y = 2 in x + y"))
    for meaning in [sequential, simultaneous]:
        print(f"\n{meaning.__name__}")
        for src in [
            "let x = 1, y = 2 in x + y",
            "let x = 1, y = x + 1 in x * y",
            "let x = 10 in let x = 1, y = x + 1 in x * y",
            "let x = 1, x = x + 1 in x",
        ]:
            try:
                print(f"{src} = {evaluate(parse_ast(src, meaning), create_initial_env())}")
            except ValueError as e:
                print(f"{src}: {e}")
