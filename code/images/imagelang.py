"""Lecture 5, exercise 5: a language for images.

A solution. The values are images; `let` and the environment are those of
binding.py, and the primitives are the functions of images.py, as names in
the initial environment. Numbers and strings appear only as arguments of
`scale` and `load`.

Run with `python3 imagelang.py`: it runs the examples of the slides and saves
what each `print` shows in out/. Add `--show` to open a window for each one.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass

from lark import Lark, Token, Tree
from lark.exceptions import LarkError
from PIL import Image

import images

grammar = r"""
    ?expr: let | arith
    let: "let" IDENTIFIER "=" expr "in" expr
    ?arith: bin | mono
    bin: arith OP mono
    mono: var | paren | call | ground | text
    paren: "(" expr ")"
    call: IDENTIFIER "(" expr ("," expr)* ")"
    ground: NUMBER
    text: STRING
    var: IDENTIFIER

    NUMBER: /[0-9]+(\.[0-9]+)?/
    STRING: /"[^"]*"/
    OP: "&" | "|" | "/"
    IDENTIFIER: /(?!(let|in)\b)[a-zA-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="expr")


@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class Text:
    value: str


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class BinaryExpression:
    op: str
    left: Expression
    right: Expression


@dataclass(frozen=True)
class Call:
    name: str
    args: tuple[Expression, ...]


@dataclass(frozen=True)
class Let:
    name: str
    definition: Expression
    body: Expression


type Expression = Number | Text | Var | BinaryExpression | Call | Let


def transform_parse_tree(tree: Tree | str) -> Expression:
    match tree:
        case Tree(data="mono", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="paren", children=[subtree]):
            return transform_parse_tree(subtree)
        case Tree(data="ground", children=[Token(type="NUMBER", value=digits)]):
            return Number(value=float(digits))
        case Tree(data="text", children=[Token(type="STRING", value=quoted)]):
            return Text(value=quoted[1:-1])
        case Tree(data="var", children=[Token(type="IDENTIFIER", value=name)]):
            return Var(name=name)
        case Tree(data="bin", children=[left, Token(type="OP", value=op), right]):
            return BinaryExpression(
                op=op,
                left=transform_parse_tree(left),
                right=transform_parse_tree(right),
            )
        case Tree(data="call", children=[Token(type="IDENTIFIER", value=name), *args]):
            return Call(name=name, args=tuple(transform_parse_tree(a) for a in args))
        case Tree(
            data="let",
            children=[Token(type="IDENTIFIER", value=name), definition, body],
        ):
            return Let(
                name=name,
                definition=transform_parse_tree(definition),
                body=transform_parse_tree(body),
            )
        case _:
            raise ValueError(f"Unexpected parse tree: {tree}")


def parse_ast(expression: str) -> Expression:
    try:
        tree = parser.parse(expression)
    except LarkError as e:
        raise ValueError(f"syntax error: {str(e).splitlines()[0]}") from e
    return transform_parse_tree(tree)


# --- Semantic domains ---------------------------------------------------------

type EVal = Image.Image
type Argument = EVal | float | str
type Operator = Callable[[EVal, EVal], EVal]
type Primitive = Callable[[list[Argument]], EVal]


@dataclass(frozen=True)
class Function:
    """A primitive called with parentheses, such as mirror(e)."""

    arity: int
    apply: Primitive


type DVal = EVal | Operator | Function

type Environment = Callable[[str], DVal]


def empty_environment() -> Environment:
    def env(name: str) -> DVal:
        raise ValueError(f"Undefined identifier: {name}")

    return env


def lookup(env: Environment, name: str) -> DVal:
    return env(name)


def bind(env: Environment, name: str, value: DVal) -> Environment:
    def new_env(n: str) -> DVal:
        if n == name:
            return value
        return env(n)

    return new_env


def image_arg(arg: Argument, name: str) -> EVal:
    if not isinstance(arg, Image.Image):
        raise ValueError(f"{name} needs an image, not {arg!r}")
    return arg


def number_arg(arg: Argument, name: str) -> float:
    if not isinstance(arg, float):
        raise ValueError(f"{name} needs a number, not an image")
    return arg


def text_arg(arg: Argument, name: str) -> str:
    if not isinstance(arg, str):
        raise ValueError(f"{name} needs a file name in double quotes")
    return arg


def create_initial_env(display: Callable[[EVal], None]) -> Environment:
    def mirror(args: list[Argument]) -> EVal:
        return images.mirror(image_arg(args[0], "mirror"))

    def scale(args: list[Argument]) -> EVal:
        return images.scale(image_arg(args[0], "scale"), number_arg(args[1], "scale"))

    def load(args: list[Argument]) -> EVal:
        return images.load(images.HERE / text_arg(args[0], "load"))

    def print_(args: list[Argument]) -> EVal:
        image = image_arg(args[0], "print")
        display(image)
        return image

    env = empty_environment()
    env = bind(env, "circle", images.load(images.HERE / "red_circle.png"))
    env = bind(env, "square", images.load(images.HERE / "blue_square.png"))
    env = bind(env, "&", images.over)
    env = bind(env, "|", images.beside)
    env = bind(env, "/", images.above)
    env = bind(env, "mirror", Function(1, mirror))
    env = bind(env, "scale", Function(2, scale))
    env = bind(env, "load", Function(1, load))
    env = bind(env, "print", Function(1, print_))
    return env


# --- The evaluator ------------------------------------------------------------


def evaluate(ast: Expression, env: Environment) -> EVal:
    match ast:
        case Number(value):
            raise ValueError(f"{value:g} is a number, not an image")
        case Text(value):
            raise ValueError(f'"{value}" is a file name, not an image: use load')
        case Var(name):
            meaning = lookup(env, name)
            if not isinstance(meaning, Image.Image):
                raise ValueError(f"{name} is not an image")
            return meaning
        case BinaryExpression(op, left, right):
            operator = lookup(env, op)
            if isinstance(operator, Image.Image | Function):
                raise ValueError(f"{op} is not an operator")
            return operator(evaluate(left, env), evaluate(right, env))
        case Call(name, args):
            function = lookup(env, name)
            if not isinstance(function, Function):
                raise ValueError(f"{name} is not a function")
            if len(args) != function.arity:
                raise ValueError(f"{name} takes {function.arity} argument(s)")
            return function.apply([evaluate_argument(a, env) for a in args])
        case Let(name, definition, body):
            image = evaluate(definition, env)
            return evaluate(body, bind(env, name, image))


def evaluate_argument(ast: Expression, env: Environment) -> Argument:
    """Numbers and file names are allowed here, and only here."""
    match ast:
        case Number(value):
            return value
        case Text(value):
            return value
        case _:
            return evaluate(ast, env)


def sky() -> EVal:
    """A 512 x 512 background, light blue at the top, white at the bottom."""
    image = Image.new("RGBA", (images.SIZE, images.SIZE))
    for y in range(images.SIZE):
        t = y / (images.SIZE - 1)
        colour = (round(120 + 135 * t), round(180 + 75 * t), 255, 255)
        image.paste(colour, (0, y, images.SIZE, y + 1))
    return image


EXAMPLES = [
    "print(circle & square)",
    "print(circle | mirror(circle))",
    "let c = scale(circle, 0.5) in print((c | c) / (c | c))",
    'let bg = load("sky.png") in print(circle & bg)',
]

if __name__ == "__main__":
    if not (images.HERE / "sky.png").exists():
        images.save(sky(), images.HERE / "sky.png")

    show = "--show" in sys.argv
    out = images.HERE / "out"
    out.mkdir(exist_ok=True)
    for number, src in enumerate(EXAMPLES, start=1):
        shown: list[EVal] = []

        def display(image: EVal) -> None:
            shown.append(image)
            if show:
                images.show(image)

        evaluate(parse_ast(src), create_initial_env(display))
        for image in shown:
            images.save(image, out / f"lang-{number}.png")
        print(f"{src}  ->  out/lang-{number}.png")

    for src in ["circle & 3", "scale(circle, circle)", "mirror(circle, square)", "print"]:
        try:
            evaluate(parse_ast(src), create_initial_env(lambda image: None))
        except ValueError as e:
            print(f"{src}: {e}")
