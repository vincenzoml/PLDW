# 1. What a language is made of

*Lecture 1, part B. From here on, everything is in the exam programme.*

Chapter 0 argued that a language is worth building. This chapter says what one is made
of, in enough detail that by the end of it you have built one — forty lines of Python,
which you can run — and can see the two halves that the rest of the course will grow:
the **syntax**, which says what programs exist, and the **semantics**, which says what
they mean.

We start with the most familiar language there is, arithmetic, because you already know
what its programs mean. That lets us concentrate on the shape of the thing.

## The characters are not the program

Take the string `2 + (x * 3)`. Whatever a program *is*, it is not this sequence of
eleven characters. Remove the spaces and it is the same program. Write `2+(x*3)` on one
line and `2 +\n(x * 3)` on two, and it is still the same program. Replace the
parentheses with square brackets and you would probably still accept it, and would
certainly mean the same thing.

What stays fixed under all these changes is a **tree**: an addition whose left operand
is the number two and whose right operand is a multiplication of the variable `x` by the
number three. The parentheses are not in the tree. They were only there to tell the
reader which tree we meant: `2 + x * 3` could have been a multiplication of `2 + x` by
three, and in ordinary arithmetic it is not, because of a convention about precedence.

That tree is the program. In this course we call it the **abstract syntax tree**, or AST:
"abstract" because it has forgotten everything about the characters — spaces, brackets,
line breaks — that does not affect meaning. The characters are the **concrete syntax**,
one of many ways of writing the tree down, and turning characters into a tree is the job
of a **parser**, which Chapter 3 will build for us. Until then we will write the trees
directly, by hand.

## Syntax: which trees exist

Here is the syntax of our arithmetic language in Python. Each kind of node is a class
with a field for each child, and a type alias lists the kinds:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class Variable:
    name: str


@dataclass(frozen=True)
class BinaryOp:
    left: Expr
    operator: str
    right: Expr


type Expr = Number | Variable | BinaryOp
```

Read `type Expr = Number | Variable | BinaryOp` as a definition: *an expression is a
number, or a variable, or a binary operation, and nothing else*. A `BinaryOp` contains
two further expressions, so the definition is recursive, and trees of any depth exist.
The word `frozen` says a tree never changes after it is built; we will see in Chapter 2
why that is a good idea. The tree for `2 + (x * 3)` is then:

```python
example = BinaryOp(
    left=Number(2.0),
    operator="+",
    right=BinaryOp(left=Variable("x"), operator="*", right=Number(3.0)),
)
```

Compare this with how a mathematician would write the same definition:

$$e ::= n \;\mid\; x \;\mid\; e \; \mathit{op} \; e$$

"An expression $e$ is a numeral $n$, or a name $x$, or an expression, an operator and an
expression." This is a **grammar**, in the notation Chomsky's work led to and that the
ALGOL report made standard. The Python and the grammar say the same thing. The grammar
is shorter; the Python runs. We will use both, and the ability to move between them is
one of the skills this course teaches.

Notice what the syntax does *not* say. It does not say that `x` has a value, or that
division by zero is forbidden, or that `+` adds. `BinaryOp(Number(1), "?", Number(2))`
is a perfectly good tree. Syntax says which trees exist; it is deliberately silent about
what they mean.

## Semantics: what a tree means

The meaning of an arithmetic expression is a number — once we know the value of every
variable in it. So the meaning of a tree is a function from an **environment**, a table
from names to values, to a number. In Python:

```python
type Env = dict[str, float]


def evaluate(expr: Expr, env: Env) -> float:
    match expr:
        case Number(value):
            return value
        case Variable(name):
            if name not in env:
                raise NameError(f"variable '{name}' is not defined")
            return env[name]
        case BinaryOp(left, operator, right):
            lv = evaluate(left, env)
            rv = evaluate(right, env)
            match operator:
                case "+":
                    return lv + rv
                case "-":
                    return lv - rv
                case "*":
                    return lv * rv
                case "/":
                    return lv / rv
                case _:
                    raise ValueError(f"unknown operator '{operator}'")
```

```python
>>> evaluate(example, {"x": 4.0})
14.0
```

Three things are worth staring at, because the whole course is in them.

First, the function has **one case per kind of node**, and nothing else. The `match`
statement takes the tree apart — `case BinaryOp(left, operator, right)` names the three
children — and the shape of the function mirrors the shape of the syntax. When you add a
kind of node to `Expr`, you add a case to `evaluate`. This is not a coincidence of
Python; it is what a definition of meaning looks like, and Chapter 2 is about the
Python features that make it comfortable.

Second, the function is **recursive** exactly where the syntax is. The meaning of an
addition is computed from the meanings of its two operands. A mathematician writes this
as an equation, with $\rho$ for the environment:

$$⟦e_1 + e_2⟧\rho = ⟦e_1⟧\rho + ⟦e_2⟧\rho$$

"The meaning of the tree `e₁ + e₂`, in environment ρ, is the sum of the meanings of the
two subtrees in the same environment." The `+` on the left is a piece of syntax; the `+`
on the right is addition of numbers. The equation and the `case "+"` line say the same
thing.

Third, the **decisions are visible**. What happens when a variable is missing? We chose
to raise an error; we could have chosen to return zero, as some spreadsheet formulas do,
or to leave the variable in the answer, as a computer algebra system would. What is `1 /
0`? Right now, whatever Python does — an exception. None of these choices is forced by
the syntax. Each of them is a decision about what the language *means*, and a designer
who has not made them has not finished designing.

## Same characters, different trees

The tree is the program, and the following experiment shows it. The string `2 * 3 + 4`
can be read as two trees:

```python
left_first = BinaryOp(BinaryOp(Number(2), "*", Number(3)), "+", Number(4))
right_first = BinaryOp(Number(2), "*", BinaryOp(Number(3), "+", Number(4)))
```

```python
>>> evaluate(left_first, {}), evaluate(right_first, {})
(10.0, 14.0)
```

`evaluate` does not know about precedence and does not need to. Precedence is a rule
about which tree a *string* stands for, and belongs to the parser. Meaning is a rule
about trees. Keeping the two apart is what lets you change the surface of a language —
its keywords, its punctuation, its precedence table — without touching what it means,
and the other way round.

## What we have, and what we do not

In forty lines we have a language: a syntax that says which trees exist, and a semantics
that gives each tree a number. Everything the course adds is an extension of one half or
the other.

- **Chapter 2** looks at the Python we just used — dataclasses, type aliases, `match` —
  and at why these features, and not others, make interpreters pleasant to write.
- **Chapter 3** builds the parser, so that we can write `2 + (x * 3)` instead of the tree.
- **Chapter 4** asks what kinds of values a program can denote, and makes the environment
  a first-class object of study.
- **Chapters 5 to 8** add, one at a time, the constructs that turn arithmetic into a
  programming language: `let`, state and commands, `if` and `while`, functions.

What we do not have is a reason for this particular language to exist. Nobody needs a
new calculator. The language you will build in this course is for a **domain of your
choice** — images, music, geometry, graphs, sound, text, three-dimensional models — and
its numbers will be replaced by the values of that domain, and its `+` and `*` by the
operations that people in that domain actually perform. The forty lines are the frame.
The decisions are the content.

## How this course works

**What you build.** You pick an application domain and design a domain-specific language
for it. You analyse the domain and choose its primitives; you decide what each primitive
means; you build an interpreter; you make the results visible; and you write examples
that show the language is good for something.

**How you are assessed.** A midway submission, required and graded, counts for one third:
your domain, your primitives and why, and a first interpreter that runs. A final
presentation in front of the class, with slides and a live demo followed by questions on
your code and on the theory, counts for two thirds. In it you say why your language is
right, and where it is wrong. That last part is the exam. The full rules are in the
course repository, under `exam/`.

**Tools.** Python 3.12 or later; the `lark` parsing library from Chapter 3 onwards. AI
assistants are allowed and expected. What you must own is every primitive, every example
and every design decision: a language you cannot explain is not your language, whoever
typed it.

**Prerequisites.** Basic Python: functions, lists, dictionaries, recursion. No previous
experience with compilers or interpreters. If your Python is rusty, the file
`code/01-introduction/python_crash_course.py` is a twenty-minute refresher.

## Exercises

1. Add a `Negate` node to `Expr`, for unary minus, and the corresponding case to
   `evaluate`. Build the tree for `-(x * 3)` and evaluate it.
2. `evaluate(Variable("y"), {"x": 4.0})` raises `NameError`. Change the language so that
   an undefined variable evaluates to `0.0` instead. Then write one sentence on why a
   spreadsheet might want this and a bank might not.
3. Write a function `variables(expr: Expr) -> set[str]` that returns the names occurring
   in a tree. It has the same shape as `evaluate`. Why?
4. Write a function `show(expr: Expr) -> str` that turns a tree back into a string, with
   parentheses around every `BinaryOp`. Check that `evaluate` gives the same answer on
   `left_first` and on the tree you get by reading `show(left_first)` by eye.
5. *Blindfolded parsing.* Without reading Chapter 3, write a function that takes a
   string such as `"2 + 5 - 3 * 4"` — operators and integers separated by spaces, no
   parentheses, evaluated left to right with no precedence — and returns its value. Then
   write the version that builds the tree first and calls `evaluate`. The file
   `code/01-introduction/exercises.py` has the statement; `exercises_solved.py` has
   several solutions, to be read only afterwards.
6. Pick a domain you might choose for your project. Write down five operations people in
   that domain perform, as a vocabulary of the form `name(arguments)`. Do not implement
   anything.

## Where we are

We have a syntax, a semantics, and a forty-line interpreter that runs; every later
chapter extends one of the two halves. What we cannot do yet is write a program as text
(Chapter 3), let a program name its own values (Chapters 4 and 5), or change anything
(Chapter 6). And the language has no domain: choosing one is your job, not the book's.
