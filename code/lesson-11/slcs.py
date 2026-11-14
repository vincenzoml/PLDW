"""Lecture 11: a model checker for the spatial logic SLCS, on images.

Run with `python3 slcs.py`. It reads exercise.png, checks a few formulas on it
and saves each result as a black and white PNG (white: the formula holds).
The fragments shown in the slides are taken from this file; some are shown
without type annotations.
"""

from __future__ import annotations

from dataclasses import dataclass

from lark import Lark, Token, Tree
from PIL import Image

# --- Syntax ------------------------------------------------------------------
#
# Same shape as the calculator of lecture 4: binary operators have no
# precedence and associate to the left, so `a & b S c` means `(a & b) S c`.

grammar = r"""
    ?formula: bin | mono
    ?mono: atom | unary | paren
    bin: formula OP mono
    unary: UOP mono
    paren: "(" formula ")"
    atom: NAME

    OP: "&" | "|" | "S" | "T"
    UOP: "!" | "N"
    NAME: /[a-z]+/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="formula")


@dataclass(frozen=True)
class Atom:
    name: str


@dataclass(frozen=True)
class Not:
    arg: Formula


@dataclass(frozen=True)
class Near:
    arg: Formula


@dataclass(frozen=True)
class And:
    left: Formula
    right: Formula


@dataclass(frozen=True)
class Or:
    left: Formula
    right: Formula


@dataclass(frozen=True)
class Surrounded:
    left: Formula
    right: Formula


@dataclass(frozen=True)
class Touch:
    left: Formula
    right: Formula


type Formula = Atom | Not | Near | And | Or | Surrounded | Touch

UNARY = {"!": Not, "N": Near}
BINARY = {"&": And, "|": Or, "S": Surrounded, "T": Touch}


def transform_parse_tree(tree: Tree) -> Formula:
    match tree:
        case Tree(data="paren", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="atom", children=[Token(type="NAME", value=name)]):
            return Atom(name=name)
        case Tree(data="unary", children=[Token(type="UOP", value=op), arg]):
            return UNARY[op](transform_parse_tree(arg))
        case Tree(data="bin", children=[left, Token(type="OP", value=op), right]):
            return BINARY[op](transform_parse_tree(left), transform_parse_tree(right))
    raise ValueError(f"unexpected parse tree: {tree}")


def parse(text: str) -> Formula:
    return transform_parse_tree(parser.parse(text))


# --- Models --------------------------------------------------------------------
#
# A model is a graph whose nodes carry atomic propositions. For an image the
# nodes are the pixels, each pixel is related to its 8 neighbours, and the
# atomic propositions are the colours.

type Point = tuple[int, int]


@dataclass(frozen=True)
class Model:
    points: frozenset[Point]
    neighbours: dict[Point, frozenset[Point]]
    valuation: dict[str, frozenset[Point]]


COLOURS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
}


def image_model(path: str) -> Model:
    image = Image.open(path).convert("RGB")
    width, height = image.size
    points = frozenset((x, y) for x in range(width) for y in range(height))
    neighbours = {
        (x, y): frozenset(
            (x + dx, y + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if (dx, dy) != (0, 0) and (x + dx, y + dy) in points
        )
        for (x, y) in points
    }
    valuation = {
        name: frozenset(p for p in points if image.getpixel(p) == rgb)
        for name, rgb in COLOURS.items()
    }
    return Model(points, neighbours, valuation)


# --- Semantics: a formula denotes a set of points --------------------------------


def evaluate(phi: Formula, m: Model) -> frozenset[Point]:
    match phi:
        case Atom(name):
            return m.valuation[name]
        case Not(arg):
            return m.points - evaluate(arg, m)
        case And(left, right):
            return evaluate(left, m) & evaluate(right, m)
        case Or(left, right):
            return evaluate(left, m) | evaluate(right, m)
        case Near(arg):
            return near(evaluate(arg, m), m)
        case Surrounded(left, right):
            return surrounded(evaluate(left, m), evaluate(right, m), m)
        case Touch(left, right):
            return touch(evaluate(left, m), evaluate(right, m), m)


def near(a: frozenset[Point], m: Model) -> frozenset[Point]:
    """The closure of a: a, and every point one step away from it."""
    return a | {y for x in a for y in m.neighbours[x]}


def surrounded(a: frozenset[Point], b: frozenset[Point], m: Model) -> frozenset[Point]:
    """The points of a from which every way out of a first crosses b.

    A flood from the outside in: the points next to a that are neither in a
    nor in b are leaks; a point of a next to a leak is lost, and a lost point
    that is not in b is a leak in its turn.
    """
    good = set(a)
    leaks = {y for x in a for y in m.neighbours[x]} - a - b
    while leaks:
        lost = {x for y in leaks for x in m.neighbours[y]} & good
        good -= lost
        leaks = lost - b
    return frozenset(good)


def touch(a: frozenset[Point], b: frozenset[Point], m: Model) -> frozenset[Point]:
    """The points of a from which a path inside a reaches a point near b."""
    reached = set(a & near(b, m))
    frontier = set(reached)
    while frontier:
        frontier = {y for x in frontier for y in m.neighbours[x]} & a - reached
        reached |= frontier
    return frozenset(reached)


# --- Output ----------------------------------------------------------------------


def save_mask(points: frozenset[Point], m: Model, path: str) -> None:
    width = max(x for x, _ in m.points) + 1
    height = max(y for _, y in m.points) + 1
    image = Image.new("L", (width, height), 0)
    for p in points:
        image.putpixel(p, 255)
    image.save(path)


if __name__ == "__main__":
    model = image_model("exercise.png")
    examples = [
        "N blue",
        "blue S green",
        "green T blue",
        "green T (blue T black)",
        "!(N !green)",
    ]
    for i, text in enumerate(examples, start=1):
        result = evaluate(parse(text), model)
        save_mask(result, model, f"result-{i}.png")
        print(f"result-{i}.png  {len(result):5} points  {text}")
