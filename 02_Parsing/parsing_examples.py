"""
Examples of parsing using Parsimonious library.
This module demonstrates practical parsing concepts using PEG grammars.
"""

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from dataclasses import dataclass
from typing import Any

# Example 1: Simple Arithmetic Expression Parser
type Expression = int | tuple["Operation", "Expression", "Expression"]
type Operation = str

ARITHMETIC_GRAMMAR = Grammar(
    r"""
    expr      = term (add_op term)*
    term      = factor (mul_op factor)*
    factor    = number / "(" expr ")"
    add_op    = "+" / "-"
    mul_op    = "*" / "/"
    number    = ~r"\d+"
    ws        = ~r"\s*"
    """
)

class ArithmeticVisitor(NodeVisitor):
    def visit_expr(self, _, visited_children) -> Expression:
        term, rest = visited_children
        if not rest:
            return term
        operation, second_term = rest[0]
        return (operation, term, second_term)
    
    def visit_term(self, _, visited_children) -> Expression:
        factor, rest = visited_children
        if not rest:
            return factor
        operation, second_factor = rest[0]
        return (operation, factor, second_factor)
    
    def visit_factor(self, _, visited_children) -> Expression:
        return visited_children[0]
    
    def visit_number(self, node, _) -> int:
        return int(node.text)
    
    def visit_add_op(self, node, _) -> str:
        return node.text
    
    def visit_mul_op(self, node, _) -> str:
        return node.text
    
    def generic_visit(self, node, visited_children: list[Any]) -> Any:
        return visited_children or node

# Example 2: Simple JSON-like Parser
@dataclass
class JsonObject:
    pairs: dict[str, Any]

@dataclass
class JsonArray:
    items: list[Any]

type JsonValue = str | int | float | bool | None | JsonObject | JsonArray

JSON_GRAMMAR = Grammar(
    r"""
    value     = object / array / string / number / boolean / null
    object    = "{" ws (pair (comma pair)*)? ws "}"
    array     = "[" ws (value (comma value)*)? ws "]"
    pair      = string ws ":" ws value
    string    = '"' ~'[^"]*' '"'
    number    = ~r"-?\d+(\.\d+)?"
    boolean   = "true" / "false"
    null      = "null"
    comma     = ws "," ws
    ws        = ~r"\s*"
    """
)

class JsonVisitor(NodeVisitor):
    def visit_object(self, _, visited_children) -> JsonObject:
        if len(visited_children) == 3:  # Empty object
            return JsonObject({})
        _, _, pairs, _, _ = visited_children
        first_pair, rest = pairs
        result = dict([first_pair])
        if rest:
            for comma_pair in rest:
                _, pair = comma_pair
                key, value = pair
                result[key] = value
        return JsonObject(result)
    
    def visit_array(self, _, visited_children) -> JsonArray:
        if len(visited_children) == 3:  # Empty array
            return JsonArray([])
        _, _, items, _, _ = visited_children
        first_item, rest = items
        result = [first_item]
        if rest:
            for comma_item in rest:
                _, item = comma_item
                result.append(item)
        return JsonArray(result)
    
    def visit_pair(self, _, visited_children) -> tuple[str, JsonValue]:
        key, _, _, _, value = visited_children
        return key, value
    
    def visit_string(self, node, _) -> str:
        return node.text[1:-1]  # Remove quotes
    
    def visit_number(self, node, _) -> int | float:
        text = node.text
        return int(text) if text.isdigit() else float(text)
    
    def visit_boolean(self, node, _) -> bool:
        return node.text == "true"
    
    def visit_null(self, _, __) -> None:
        return None
    
    def generic_visit(self, node, visited_children: list[Any]) -> Any:
        return visited_children or node

def main() -> None:
    # Test arithmetic parser
    arithmetic_visitor = ArithmeticVisitor()
    tree = ARITHMETIC_GRAMMAR.parse("2 + 3 * 4")
    result = arithmetic_visitor.visit(tree)
    print(f"Arithmetic AST: {result}")
    
    # Test JSON parser
    json_visitor = JsonVisitor()
    tree = JSON_GRAMMAR.parse('{"name": "Alice", "age": 30, "scores": [95, 87, 92]}')
    result = json_visitor.visit(tree)
    print(f"JSON AST: {result}")

if __name__ == "__main__":
    main()
