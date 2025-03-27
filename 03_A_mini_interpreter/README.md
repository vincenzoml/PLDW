# Chapter 3: Parsing and Mini-Interpreters

## Section 1: Introduction to Context-Free Grammars and Parsing

Lark is a parsing toolkit that works with Context-Free Grammars (CFGs). Context-free grammars are a formal grammar formalism that can express the syntax of most programming languages and many natural language constructs.

### Key Features of Lark's Parsing Approach
- **Multiple Parsing Algorithms**: Lark implements Earley and LALR(1) algorithms for parsing CFGs.
- **Ambiguity Support**: Unlike PEG parsers, Lark's Earley algorithm can handle ambiguous grammars gracefully.
- **Complete Language Coverage**: Lark can parse all context-free languages, making it capable of handling almost any programming language.
- **EBNF Notation**: Lark uses Extended Backus-Naur Form (EBNF) for grammar definition, which provides powerful and concise syntax.

## Section 2: Working with Lark

Lark is a modern parsing library for Python that implements parsers for Context-Free Grammars with additional features. It provides a clean interface for defining grammars and working with parse trees.

### Defining a Grammar in Lark

```python
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
```

### Grammar Components Explained
- **Rules**: Non-terminals like `expr`, `mono`, and `bin` define the structure of the language.
- **Terminals**: Items like `NUMBER` or literals like `"("` match specific patterns in the input.
- **Special Rules**: The `?expr` rule is an anonymous rule that doesn't create a separate node in the parse tree.
- **Directives**: `%import common.WS` and `%ignore WS` handle whitespace elegantly.

### Creating a Parser and Parsing Input

```python
from lark import Lark

# Create the Lark parser
parser = Lark(grammar, start="expr")

# Parse an input string
parse_tree = parser.parse("(1 + 2) - 3")

# Print the parse tree
print(parse_tree.pretty())
```

## Section 3: Understanding Parse Trees

Lark generates parse trees that represent the structure of the input according to the grammar rules. Each node in the tree corresponds to a rule in the grammar or a terminal value.

### Parse Tree Structure
For the expression `(1 + 2) - 3`, the parse tree looks like:

```
bin
├── mono
│   └── paren
│       └── bin
│           ├── mono
│           │   └── ground
│           │       └── 1
│           ├── op
│           │   └── +
│           └── mono
│               └── ground
│                   └── 2
├── op
│   └── -
└── mono
    └── ground
        └── 3
```

### Navigating the Parse Tree
Parse trees can be navigated and inspected programmatically:

```python
def print_tree(tree: ParseTree | Token):
    match tree:
        case Tree(data=data, children=children):
            print("Tree", data)
            for child in children:
                print_tree(child)
        case Token(type=type, value=value):
            print("Token", type, value)
```

## Section 4: Pattern Matching with Parse Trees

Python 3.10's pattern matching feature works exceptionally well with parse trees, allowing for declarative tree traversal:

```python
match parse_tree:
    case Tree(data='bin', children=[left, Tree(data='op', children=[Token(value=op)]), right]):
        print(f"Found binary operation: {op}")
        print(f"Left: {left}")
        print(f"Right: {right}")
    
    case Tree(data='mono', children=[Tree(data='ground', children=[Token(value=number)])]):
        print(f"Found number: {number}")
    
    case _:
        print("Unknown tree structure")
```

## Section 5: Transforming Parse Trees to ASTs

Parse trees often contain more detail than needed for interpretation. We can define custom types and use pattern matching to convert parse trees into a more abstract syntax tree (AST):

```python
from dataclasses import dataclass
from typing import Literal

# Define AST types for the expression language
type Op = Literal["+", "-", "*"]

@dataclass
class Number:
    value: int

@dataclass
class BinaryExpression:
    op: Op
    left: Expression
    right: Expression

type Expression = Number | BinaryExpression
```

This AST representation is cleaner and more suitable for evaluation than the raw parse tree.

## Section 6: Converting Parse Trees to ASTs

With our AST structure defined, we can convert parse trees into ASTs using pattern matching:

```python
def transform_parse_tree(tree: Tree) -> Expression:
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_parse_tree(subtree)

        case Tree(data="ground", children=[Token(type="NUMBER", value=value)]):
            return Number(value=int(value))

        case Tree(data="paren", children=[subtree]):
            return transform_parse_tree(subtree)

        case Tree(
            data="bin",
            children=[
                left,
                Token(type="OP", value=op),
                right,
            ],
        ):
            return BinaryExpression(
                op=op,
                left=transform_parse_tree(left),
                right=transform_parse_tree(right),
            )

        case _:
            raise ValueError(f"Unexpected parse tree structure")
```

This approach provides much better type safety and makes the intent clearer than the Transformer class approach.

## Section 7: Building a Mini-Interpreter

By combining parsing with evaluation, we can create a mini-interpreter:

1. **Parse**: Convert the input string into a parse tree
2. **Transform**: Convert the parse tree into an AST
3. **Evaluate**: Traverse the AST to compute a result

```python
# Function to parse a string and return an AST
def parse_ast(expression: str) -> Expression:
    parse_tree = parser.parse(expression)
    return transform_parse_tree(parse_tree)

# Example
expression = "(1 + 2) - 3"
ast = parse_ast(expression)
print(ast)  # BinaryExpression(op='-', left=BinaryExpression(op='+', left=Number(value=1), right=Number(value=2)), right=Number(value=3))

# Evaluate function (to be implemented)
def evaluate(ast: Expression) -> int:
    match ast:
        case Number(value=value):
            return value
        case BinaryExpression(op="+", left=left, right=right):
            return evaluate(left) + evaluate(right)
        case BinaryExpression(op="-", left=left, right=right):
            return evaluate(left) - evaluate(right)
        case BinaryExpression(op="*", left=left, right=right):
            return evaluate(left) * evaluate(right)
        case _:
            raise ValueError(f"Unknown expression: {ast}")

result = evaluate(ast)
print(f"Result: {result}")  # Output: Result: 0
```

This pattern-matching approach to evaluation is clear, concise, and type-safe.

## Exercises
1. Extend the grammar to support division (`/`) and exponentiation (`^`).
2. Add support for variables in the grammar and evaluator.
3. Implement a transformer that converts the parse tree to a different AST structure.
4. Add error handling to provide meaningful error messages for invalid input.
5. Implement a visualization tool for parse trees and ASTs.

## Additional Resources
- [Lark Documentation](https://lark-parser.readthedocs.io/en/latest/)
- [Context-Free Grammars (Wikipedia)](https://en.wikipedia.org/wiki/Context-free_grammar)
- [Parsing Expression Grammars (Wikipedia)](https://en.wikipedia.org/wiki/Parsing_expression_grammar) - For comparing with other parsing approaches
- [EBNF Syntax (Wikipedia)](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form)
- [Python Pattern Matching Documentation](https://docs.python.org/3/reference/expressions.html#pattern-matching)
