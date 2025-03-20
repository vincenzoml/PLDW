# %%
"""
Examples of Python's type system and pattern matching features.
This module demonstrates various use cases of type hints and structural pattern matching.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

# First of all, a familiar example: imperative stacks (Last In, First Out)
# NOTE:
# we will NOT work like this, we will manipulate data in a functional style, but
# this is a good starting point.


class Stack[T]:  # Python 3.12+ syntax for generic types
    """A generic stack implementation demonstrating type variables."""

    def __init__(self) -> None:
        self.items: list[T] = []  # Use list[T] instead of List[T]

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T | None:  # Use | for union types
        return self.items.pop() if self.items else None

    def peek(self) -> T | None:  # Use | for union types
        return self.items[-1] if self.items else None

    def __str__(self) -> str:
        """Return a string representation of the stack contents."""
        return str(self.items)


# Example: a stack of integers

stack_1 = Stack[int]()  # Stack of integers
stack_1.push(1)
stack_1.push(2)
stack_1.push(3)

print("Stack contents:", stack_1)

print("Popped item:", stack_1.pop())  # Output: 3
print("Peeked item:", stack_1.peek())  # Output: 2

print("Stack contents:", stack_1)

# %%


# Now let's create a function that pushes a string
def f():
    print("Pushing 'hello' to the stack...")
    stack_1.push("hello")  # This is an error!


# "hello" is underlined, because it's an error to push a string to an integer
# stack. We will not use this function

# EXERCISE 1: what happens if I actually call the function? Find this out! Why? What happens?

# EXERCISE 2: create a function that pushes an integer to the stack and see what happens

# EXERCISE 3: now define a stack of strings and use it

# Exercise 4: what if you wanted a stack of mixed strings and int?

# %%

## Now let's examine the base types first, union types, records, tuples and sequences.

# Base types
# boolean
# integer
# float
# string

# Union types
# int | float | string


# Records
@dataclass
class Person:
    name: str
    age: int


# Tuples
my_tuple: tuple[int, str, float] = (1, "hello", 1.0)

# Sequences
my_list: list[int] = [1, 2, 3, 4, 5]

print("My tuple:", my_tuple)
print("My list:", my_list)

# %%


# Pattern matching example
def greet(person: Person | str) -> None:
    match person:
        case Person(name="Alice", age=25):
            print("Hello Alice!")
        case Person(name="Bob", age=30):
            print("Hi Bob!")
        case Person(name=x, age=y):
            print(f"Hello {x} of age {y}!")
        case "Alice":
            print("Hello Alice!")
        case "Bob":
            print("Hi Bob!")
        case name:
            print(f"Hello {name}!")


def greet_people(people: tuple[Person, Person]) -> None:
    match people:
        case (Person(name="Alice", age=25), Person(name="Bob", age=30)):
            print("Hello Alice and Bob!")
        case (Person(name=x, age=y), Person(name=z, age=w)):
            print(f"Hello {x} of age {y} and {z} of age {w}!")
        case _:  # Q: this code is unreachable, why?
            print("Hello people!")


greet_people((Person(name="Alice", age=25), Person(name="Bob", age=30)))
greet("Alice")
greet(25)  # Q: WHY does this work? (Hint: type checking)

# %%


def process_lst(lst: list[int]) -> None:
    match lst:
        case []:
            print("List: empty")
        case [head, *tail]:
            print(f"List: head {head}, tail {tail}")


def sum_list(lst: list[int]) -> int:
    match lst:
        case []:
            return 0
        case [head, *tail]:
            return head + sum_list(tail)


@dataclass
class MyList[T]:
    head: T
    tail: MyBaseList[T]


type MyBaseList[T] = None | MyList[T]

my_list_3: MyBaseList[int] = MyList(
    head=1, tail=MyList(head=2, tail=MyList(head=3, tail=None))
)


def sum_list_2(lst: MyBaseList[int]) -> int:
    match lst:
        case None:
            return 0
        case MyList(head=x, tail=y):
            return x + sum_list_2(y)


print(sum_list_2(my_list_3))  # 6


@dataclass
class Sum:
    left: Expr
    right: Expr


type Expr = int | Sum


def eval_expr(expr: Expr) -> int:
    match expr:
        case int(x):
            return x
        case Sum(left=x, right=y):
            return eval_expr(x) + eval_expr(y)


# %%


# JSON as intermediate representation for our expression ADT
def parse_expr(json_expr: dict | int) -> Expr:
    match json_expr:
        case int(x):
            return x
        case {"sum": {"left": left, "right": right}}:
            return Sum(left=parse_expr(left), right=parse_expr(right))
        case _:
            raise ValueError(f"Invalid expression: {json_expr}")


# Example usage
json_expr = {"sum": {"left": 3, "right": {"sum": {"left": 4, "right": 5}}}}

expr = parse_expr(json_expr)
print(f"Evaluated expression: {eval_expr(expr)}")  # Should print 12 (3 + (4 + 5))

# %%

# Direct JSON expression type without intermediate classes
type JsonExpr = int | dict[str, "JsonExpr"]


def eval_json_expr(expr: JsonExpr) -> int:
    match expr:
        case int(x):
            return x
        case {"sum": {"left": left, "right": right}}:
            return eval_json_expr(left) + eval_json_expr(right)
        case _:
            raise ValueError(f"Invalid expression: {expr}")


# Example usage
json_expr_2: JsonExpr = {"sum": {"left": 3, "right": {"sum": {"left": 4, "right": 5}}}}
print(
    f"Evaluated JSON expression: {eval_json_expr(json_expr_2)}"
)  # Should print 12 (3 + (4 + 5))

# %%


@dataclass
class Human:
    name: str
    drivingLicense: bool


type DogKind = Literal["bulldog", "poodle", "labrador"]


@dataclass
class Dog:
    name: str
    kind: DogKind
    colour: Literal["brown", "black", "white"]


type Record = Human | Dog

# %%


def describe_person(person: Human | Dog) -> str:
    match person:
        case Human(name=name, drivingLicense=True):
            return f"Person {name} has a driving license"
        case Human(name=name, drivingLicense=False):
            return f"Person {name} does not have a driving license"
        case Dog(name=name, kind=kind, colour=colour):
            return f"Dog {name} is a {kind} and has a {colour} colour"


def describe_person_2(person: Record) -> str:
    if isinstance(person, Human):
        return person.name + person.colour  # why is this wrong?
    else:
        return person.name + person.kind


# %%
@dataclass
class Car:
    make: str
    model: str
    year: int | None = None  # Year is optional


# Example usage
car1 = Car(make="Toyota", model="Corolla", year=2020)
car2 = Car(make="Honda", model="Civic")  # year is None

print(car1)  # Car(make='Toyota', model='Corolla', year=2020)
print(car2)  # Car(make='Honda', model='Civic', year=None)

# %%

from typing import Generic, TypeVar


@dataclass
class Box[T]:
    content: T
    label: str


# Example usage
box1 = Box(content=42, label="Numbers")
box2 = Box(content="Hello", label="Strings")

boxes = [Box(content=42, label="Numbers"), Box(content="Hello", label="Strings")]

# %%


def process_box[T](box: Box[T]) -> None:
    match box:
        case Box(content=x, label=y):
            print(f"Box contains {x} and is labeled {y}")


# %% So far so good... now let's define an AST for arithmetic expressions.


@dataclass
class BinOp:
    op: Literal["+", "-", "*"]
    left: ArithExpr
    right: ArithExpr


type ArithExpr = int | BinOp


def eval_arith_expr(expr: ArithExpr) -> int:
    match expr:
        case int(x):
            return x
        case BinOp(left=x, right=y, op=op):
            match op:
                case "+":
                    return eval_arith_expr(x) + eval_arith_expr(y)
                case "-":
                    return eval_arith_expr(x) - eval_arith_expr(y)
                case "*":
                    return eval_arith_expr(x) * eval_arith_expr(y)


# example: 5 + (3 * 2)

expr = BinOp(op="+", left=5, right=BinOp(op="*", left=3, right=2))

eval_arith_expr(expr)

# %%

# Amazing! Now the big question is how to switch from "5 + (3 * 2)" to the AST?

# %%
