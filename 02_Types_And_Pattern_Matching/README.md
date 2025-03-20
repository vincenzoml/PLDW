# Lecture 2: Types and Pattern Matching in Python

This lecture explores two powerful features of modern Python: the type system and structural pattern matching. These features enhance code robustness, maintainability, and readability while demonstrating important programming language design concepts.

## Learning Objectives
- Master Python's type system and type hints
- Understand structural pattern matching with match/case statements
- Apply type checking for more reliable code
- Implement algebraic data types (ADTs) in Python
- Combine types and pattern matching in practical applications

## Python's Type System

### Type Annotations
Python's type system allows developers to add optional type hints to variables, function parameters, and return values. These annotations help catch errors early and improve code documentation.

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

### Basic Types
Python provides several built-in types:
- Primitive types: `int`, `float`, `bool`, `str`
- Collection types: `list`, `tuple`, `dict`, `set`

### Union Types
Union types allow a variable to have multiple possible types:

```python
def process_data(data: int | str) -> None:
    # Can handle both integers and strings
    pass
```

### Optional Types
For values that might be `None`:

```python
def find_user(id: int) -> str | None:
    # Returns a username or None if not found
    pass
```

### Generic Types
Generics allow you to create reusable, type-safe components:

```python
class Container[T]:
    def __init__(self, item: T) -> None:
        self.item: T = item
```

### Type Aliases
Type aliases help simplify complex type annotations:

```python
type JsonData = dict[str, int | str | list | dict]
```

### Literal Types
Literal types restrict values to specific constants:

```python
def align_text(alignment: Literal["left", "center", "right"]) -> None:
    # Only accepts these three string values
    pass
```

## Structural Pattern Matching

### Basic Pattern Matching
The `match` statement, introduced in Python 3.10, provides powerful pattern matching capabilities:

```python
def describe(value):
    match value:
        case 0:
            return "Zero"
        case int(x) if x > 0:
            return "Positive integer"
        case str():
            return "String"
        case _:
            return "Something else"
```

### Sequence Patterns
Match against sequences like lists and tuples:

```python
def process_point(point):
    match point:
        case (0, 0):
            return "Origin"
        case (0, y):
            return f"Y-axis at {y}"
        case (x, 0):
            return f"X-axis at {x}"
        case (x, y):
            return f"Point at ({x}, {y})"
```

### Mapping Patterns
Match against dictionaries:

```python
def process_config(config):
    match config:
        case {"debug": True}:
            return "Debug mode enabled"
        case {"output": output, "format": "json"}:
            return f"JSON output to {output}"
        case _:
            return "Default configuration"
```

### Class Patterns
Match against class instances:

```python
match shape:
    case Circle(radius=r):
        return f"Circle with radius {r}"
    case Rectangle(width=w, height=h):
        return f"Rectangle {w}×{h}"
```

## Algebraic Data Types in Python

Python can implement algebraic data types (ADTs) using classes, dataclasses, and union types:

### Sum Types (Tagged Unions)
Represent values that could be one of several alternatives:

```python
@dataclass
class Success:
    value: Any

@dataclass
class Error:
    message: str

type Result = Success | Error
```

### Product Types
Represent combinations of values:

```python
@dataclass
class Point:
    x: float
    y: float
```

### Recursive Types
Types that refer to themselves:

```python
@dataclass
class Node:
    value: int
    next: "Node | None" = None
```

## Combining Types and Pattern Matching

The real power comes from combining type annotations with pattern matching:

```python
def process_result(result: Success | Error) -> str:
    match result:
        case Success(value=val):
            return f"Operation succeeded with value: {val}"
        case Error(message=msg):
            return f"Operation failed: {msg}"
```

## Type Checking

### Static Type Checking
Tools like mypy, pyright, and pylance can analyze your code without running it:

```bash
$ mypy my_program.py
```

### Runtime Type Checking
Python's type hints are not enforced at runtime by default, but libraries like `typeguard` can add runtime checks:

```python
from typeguard import typechecked

@typechecked
def add(a: int, b: int) -> int:
    return a + b
```

## Practical Applications

Type hints and pattern matching are particularly useful for:
- Data validation and processing
- Parsing and interpreting structured data (like JSON)
- Implementing domain-specific languages
- Building robust APIs
- Functional programming patterns

## Exercises
1. Create a generic container class with type hints
2. Implement a recursive data structure with proper type annotations
3. Build a pattern-matching based interpreter for a simple expression language
4. Design a type-safe data processing pipeline

## Additional Resources
- [Python Type Checking Guide](https://mypy.readthedocs.io/en/stable/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [PEP 585 – Type Hinting Generics In Standard Collections](https://peps.python.org/pep-0585/)
- [PEP 634 – Structural Pattern Matching](https://peps.python.org/pep-0634/)
- [PEP 636 – Structural Pattern Matching: Tutorial](https://peps.python.org/pep-0636/)
