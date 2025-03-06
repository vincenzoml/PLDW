# https://en.wikipedia.org/wiki/Parsing_expression_grammar

# %%

from lark import Lark, Transformer

# Define the grammar in Lark's EBNF format
grammar = r"""
    ?expr: bin | mono
    mono: ground | paren
    paren: "(" expr ")"
    bin: mono op expr
    ground: NUMBER

    NUMBER: /[0-9]+/
    op: "+" | "-" | "*"

    %import common.WS
    %ignore WS
"""

# Create the Lark parser
parser = Lark(grammar, start="expr")


# Define the transformer to convert parse tree to AST
class ExpressionTransformer(Transformer):
    def expr(self, items):
        return items[0]

    def mono(self, items):
        return items[0]

    def paren(self, items):
        return items[0]

    def bin(self, items):
        return (items[1], items[0], items[2])

    def ground(self, items):
        return int(items[0])

    def op(self, items):
        return items[0]

    def NUMBER(self, token):
        return int(token)


# Example usage
example = "    (   1  +   2  ) -    3   "
parse_tree = parser.parse(example)
transformer = ExpressionTransformer()
ast = transformer.transform(parse_tree)

print(ast)

# %%
