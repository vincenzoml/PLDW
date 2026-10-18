"""Roads not taken, run so that the claims about them are checked.

1. An ambiguous grammar: Lark accepts it and picks one reading.
2. Earley (Lark's default) against LALR on the same grammar.
3. Lark's own Transformer class instead of a `match` function.
"""

from __future__ import annotations

import time

from lark import Lark, Transformer

from mini_interpreter import (
    BinaryExpression,
    Number,
    evaluate,
    grammar,
    transform_parse_tree,
)

# --- 1. An ambiguous grammar ------------------------------------------------

grammar_ambiguous = r"""
    expr: bin | mono
    mono: ground | paren
    paren: "(" expr ")"
    bin: expr OP expr
    ground: NUMBER

    NUMBER: /[0-9]+/
    OP: "+" | "-" | "*" | "/" | "%"

    %import common.WS
    %ignore WS
"""


def ambiguity() -> None:
    # Earley picks one of the two trees by Python's string hashing, which
    # changes from run to run: try PYTHONHASHSEED=1 and PYTHONHASHSEED=2.
    for algorithm in ["earley", "lalr"]:
        p = Lark(grammar_ambiguous, start="expr", parser=algorithm)
        tree = p.parse("10-4-3")
        print(algorithm, evaluate(transform_parse_tree(tree)))  # 3 or 9
    explicit = Lark(grammar_ambiguous, start="expr", ambiguity="explicit")
    print(explicit.parse("10-4-3").children[0].data)  # _ambig: two trees


# --- 2. Earley against LALR -------------------------------------------------


def speed() -> None:
    earley = Lark(grammar, start="expr")  # the default
    lalr = Lark(grammar, start="expr", parser="lalr")
    text = "+".join(["1"] * 3000)
    for name, p in [("earley", earley), ("lalr", lalr)]:
        start = time.perf_counter()
        p.parse(text)
        print(f"{name}: {time.perf_counter() - start:.3f} s")
    try:
        Lark('start: a | b\na: "x"\nb: "x"', parser="lalr")
    except Exception as e:
        print(f"{type(e).__name__}: {str(e).splitlines()[0]}")


# --- 3. A Transformer class, with one method forgotten ----------------------


class ToAST(Transformer):
    def ground(self, children):
        return Number(int(children[0]))

    def bin(self, children):
        left, op, right = children
        return BinaryExpression(str(op), left, right)

    def mono(self, children):
        return children[0]

    def expr(self, children):
        return children[0]

    # no method for `paren`


def transformer() -> None:
    parser = Lark(grammar, start="expr")
    print(ToAST().transform(parser.parse("(1+2)-3")))


if __name__ == "__main__":
    ambiguity()
    speed()
    transformer()
