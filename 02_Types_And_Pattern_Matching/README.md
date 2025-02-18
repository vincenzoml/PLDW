# Lecture 1: Types and Pattern Matching in Python

This lecture introduces two powerful features of modern Python: the type system and structural pattern matching. These features not only make Python code more robust and maintainable but also serve as excellent examples of programming language design concepts.

## Learning Objectives
- Understand Python's type system and type hints
- Master structural pattern matching with match/case statements
- Learn about type checking and its benefits
- Apply these concepts in practical examples

## Type System
### Static Type Hints
- Introduction to type annotations
- Built-in types: `int`, `str`, `list`, `dict`, etc.
- Complex types: `Union`, `Optional`, `Any`
- Generic types and type variables
- Custom types and `TypeVar`

### Type Checking
- Using `mypy` for static type checking
- Runtime type checking considerations
- Type checking best practices
- Common type-related errors and how to fix them

## Structural Pattern Matching
### Basic Pattern Matching
- Introduction to `match` statement
- Simple patterns with literals
- Variable patterns
- Wildcard patterns (`_`)

### Advanced Patterns
- Sequence patterns
- Mapping patterns
- OR patterns (`|`)
- Guard clauses (`if`)
- Class patterns

## Practical Examples
The accompanying Python module `types_and_matching.py` contains practical examples demonstrating:
1. Type hints in function definitions
2. Generic type usage
3. Pattern matching for data processing
4. Combining types and pattern matching

## Exercises
1. Implement a function that uses type hints and processes different data structures
2. Create a pattern-matching based calculator
3. Design a small type-safe data processing pipeline

## Additional Resources
- [Python Type Checking Guide](https://mypy.readthedocs.io/en/stable/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [PEP 634 – Structural Pattern Matching](https://peps.python.org/pep-0634/)
