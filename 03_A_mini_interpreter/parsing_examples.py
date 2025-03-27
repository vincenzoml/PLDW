# https://en.wikipedia.org/wiki/Parsing_expression_grammar

# %%

from lark import Lark, ParseTree, Token, Transformer, Tree

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

parse_tree = parser.parse("(1 + 2) - 3")

print(parse_tree.pretty())

# bin
# ├── mono
# │   └── paren
# │       └── bin
# │           ├── mono
# │           │   └── ground
# │           │       └── 1
# │           ├── op
# │           └── mono
# │               └── ground
# │                   └── 2
# ├── op
# └── mono
#     └── ground
#         └── 3


# %%
def print_tree(tree: ParseTree | Token):
    match tree:
        case Tree(data=data, children=children):
            print("Tree", data)
            for child in children:
                print_tree(child)
        case Token(type=type, value=value):
            print("Token", type, value)


print_tree(parse_tree)


# %%

# %%

# %%

# %%

# %%


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
