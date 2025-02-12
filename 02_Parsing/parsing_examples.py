# https://en.wikipedia.org/wiki/Parsing_expression_grammar

# %%

from typing import Tuple
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

grammar = rf"""
    expr        = ws ( bin / mono )
    mono        = ground / paren
    paren       = lparen expr rparen
    bin         = mono op expr
    ground      = number

    ws          = ~" *"
    lparen      = "(" ws
    rparen      = ")" ws
    number      = ~"[0-9]+" ws
    op          = ( "+" / "-" / "*" ) ws
"""

expr = Grammar(grammar)

example = "    (   1  +   2  ) -    3   "

parse_tree = expr.parse(example)

print(parse_tree)

# %%
# Type definition using union type
type Expr = int | Tuple[str, Expr, Expr]


class ExpressionVisitor(NodeVisitor):
    def visit_expr(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            return (children[1], children[0], children[2])

    def visit_ground(self, node, children):
        return children[0]

    def visit_paren(self, node, children):
        return children[1]

    def visit_op(self, node, children):
        return node.text

    def visit_bin(self, node, children):
        return children[1], children[0], children[2]

    def visit_number(self, node, children):
        return int(node.text)

    def generic_visit(self, node, visited_children):
        return


visitor = ExpressionVisitor()

ast: Expr = visitor.visit(parse_tree)

print(ast)
