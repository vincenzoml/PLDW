"""Lecture 4: functions as values in Python, the examples of the slides.

Run:    python3 functions.py
"""

from collections.abc import Callable

# --- A function is a value ---------------------------------------------------


def double(x: int) -> int:
    return 2 * x


f = double                      # no parentheses: the function itself
assert f(21) == 42
operations: list[Callable[[int], object]] = [double, abs, str]
assert [op(-3) for op in operations] == [-6, 3, "-3"]

# --- Functions that take functions -------------------------------------------


def twice(g: Callable[[int], int], x: int) -> int:
    return g(g(x))


assert twice(double, 5) == 20
assert list(map(double, [1, 2, 3])) == [2, 4, 6]
assert sorted(["pear", "fig", "banana"], key=len) == ["fig", "pear", "banana"]

# --- Functions that return functions -----------------------------------------


def make_adder(n: int) -> Callable[[int], int]:
    def add_n(x: int) -> int:
        return x + n

    return add_n


add3 = make_adder(3)
add10 = make_adder(10)
assert add3(4) == 7
assert add10(4) == 14
assert add3(add10(0)) == 13

# --- lambda ------------------------------------------------------------------

add3_again = lambda x: x + 3  # noqa: E731
assert add3_again(4) == 7
assert sorted(["pear", "fig", "banana"], key=lambda w: w[-1]) == ["banana", "fig", "pear"]

# --- Pure and impure ---------------------------------------------------------


def area(width: int, height: int) -> int:
    return width * height


calls = 0


def counted_area(width: int, height: int) -> int:
    global calls
    calls += 1
    return width * height


log: list[str] = []


def logged_area(width: int, height: int) -> int:
    log.append(f"area({width}, {height})")
    return width * height


assert area(2, 3) == area(2, 3) == 6
counted_area(2, 3)
counted_area(2, 3)
assert calls == 2
logged_area(2, 3)
assert log == ["area(2, 3)"]

print("all examples check")
