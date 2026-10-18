"""Lecture 1B, exercise 4: the calculator written by hand, a solution.

Integers, + and - only, no parentheses, computed from left to right.
First version: numbers and operators separated by spaces (text.split()).
Second version: spaces optional; tokenize() cuts the text into pieces.

Then the complications, as in last year's lecture:
- adding * : left to right gives 2 + 5 * 3 = 21, not 17; a first pass for *
- parentheses: even checking that they are balanced needs a stack

Run:    python3 calculator.py
"""

DIGITS = "0123456789"


def number(piece: str) -> int:
    # int() alone accepts "+3", "-3", "1_000" and " 7": we check the digits first
    if piece == "" or any(c not in DIGITS for c in piece):
        raise ValueError(f"expected a number, found {piece!r}")
    return int(piece)


def compute(pieces: list[str]) -> int:
    """number, operator, number, operator, ..., number"""
    if pieces == []:
        raise ValueError("empty expression")
    total = number(pieces[0])
    for i in range(1, len(pieces), 2):
        op = pieces[i]
        if op not in ("+", "-"):
            raise ValueError(f"expected + or -, found {op!r}")
        if i + 1 == len(pieces):
            raise ValueError(f"missing number after {op!r}")
        n = number(pieces[i + 1])
        if op == "+":
            total = total + n
        else:
            total = total - n
    return total


def calc_with_spaces(text: str) -> int:
    return compute(text.split())


def tokenize(text: str) -> list[str]:
    """Cut the text into numbers, operators and parentheses; spaces are skipped."""
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == " ":
            i += 1
        elif c in "+-*()":
            tokens.append(c)
            i += 1
        elif c in DIGITS:
            j = i
            while j < len(text) and text[j] in DIGITS:
                j += 1
            tokens.append(text[i:j])
            i = j
        else:
            raise ValueError(f"unexpected character {c!r} at position {i}")
    return tokens


def calc(text: str) -> int:
    return compute(tokenize(text))


# ================================================================ adding *

def compute_left_to_right(pieces: list[str]) -> int:
    """compute() with one more branch for *: no precedence."""
    total = number(pieces[0])
    for i in range(1, len(pieces), 2):
        op, n = pieces[i], number(pieces[i + 1])
        if op == "+":
            total = total + n
        elif op == "-":
            total = total - n
        elif op == "*":
            total = total * n
        else:
            raise ValueError(f"expected an operator, found {op!r}")
    return total


def compute_with_precedence(pieces: list[str]) -> int:
    """First pass: replace each  a * b  by its value. Second pass: compute()."""
    pieces = list(pieces)  # a copy: the caller's list is not changed
    i = 1
    while i < len(pieces):
        if pieces[i] == "*":
            if i + 1 == len(pieces):
                raise ValueError("missing number after '*'")
            product = number(pieces[i - 1]) * number(pieces[i + 1])
            pieces[i - 1 : i + 2] = [str(product)]
        else:
            i += 2
    return compute(pieces)


# ================================================================ parentheses

def balanced(text: str) -> bool:
    """Every ( has its ), and they close in the right order."""
    stack = []
    for c in text:
        if c == "(":
            stack.append(c)
        elif c == ")":
            if stack == []:
                return False
            stack.pop()
    return stack == []


def fails(f, text: str) -> str:
    try:
        f(text)
    except ValueError as e:
        return str(e)
    raise AssertionError(f"{text!r} should be an error")


if __name__ == "__main__":
    for f in (calc_with_spaces, calc):
        assert f("2 + 5 - 3") == 4
        assert f("10 - 4 - 3") == 3
        assert f("7") == 7
        print(fails(f, "2 + + 3"))
        print(fails(f, "2 + x"))
        print(fails(f, "2 +"))
        print(fails(f, "2 3"))
        print(fails(f, ""))
    assert calc_with_spaces("2 + 5") == 7
    print(fails(calc_with_spaces, "2+5-3"))
    assert tokenize("12+5 - 3") == ["12", "+", "5", "-", "3"]
    assert calc("2+5-3") == 4
    assert calc("10-4-3") == 3
    print(fails(calc, "2 * 3"))
    assert compute_left_to_right(tokenize("2 + 5 * 3")) == 21
    assert compute_with_precedence(tokenize("2 + 5 * 3")) == 17
    assert compute_with_precedence(tokenize("2 * 3 * 4 - 1")) == 23
    assert balanced("(1 + (2 - 3)) + 4")
    assert not balanced("(1 + 2))(")
    assert not balanced("(1 + 2")
    print("all examples check")
