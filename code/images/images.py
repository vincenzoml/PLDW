"""Lecture 5, exercise 7: images in Python.

Only Python here, no language. Pillow is the library (`pip install pillow`);
everything else is the standard library.

Run with `python3 images.py`: it draws the two example images, if they are
missing, and writes the results of the operations next to them.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).parent
SIZE = 512


# --- Load and save ------------------------------------------------------------


def load(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGBA")


def save(image: Image.Image, path: Path) -> None:
    image.save(path)


# --- The two example images -------------------------------------------------


def red_circle() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((56, 56, 356, 356), fill=(220, 40, 40, 200))
    return image


def blue_square() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((176, 176, 456, 456), fill=(40, 80, 220, 160))
    return image


# --- Operations: each returns a new image ------------------------------------


def over(front: Image.Image, back: Image.Image, x: int = 0, y: int = 0) -> Image.Image:
    """`front` on top of `back`, with its top-left corner at (x, y) of `back`.
    The parts of `front` that fall outside `back` are cut away. Pillow does not
    accept a negative position."""
    result = back.copy()
    result.alpha_composite(front, dest=(x, y))
    return result


def scale(image: Image.Image, factor: float) -> Image.Image:
    width = max(1, round(image.width * factor))
    height = max(1, round(image.height * factor))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def beside(left: Image.Image, right: Image.Image) -> Image.Image:
    result = Image.new(
        "RGBA", (left.width + right.width, max(left.height, right.height)), (0, 0, 0, 0)
    )
    result.paste(left, (0, 0))
    result.paste(right, (left.width, 0))
    return result


def above(top: Image.Image, bottom: Image.Image) -> Image.Image:
    result = Image.new(
        "RGBA", (max(top.width, bottom.width), top.height + bottom.height), (0, 0, 0, 0)
    )
    result.paste(top, (0, 0))
    result.paste(bottom, (0, top.height))
    return result


def mirror(image: Image.Image) -> Image.Image:
    return ImageOps.mirror(image)


def fade(image: Image.Image, factor: float) -> Image.Image:
    r, g, b, a = image.split()
    a = a.point(lambda v: round(v * factor))
    return Image.merge("RGBA", (r, g, b, a))


def on_white(image: Image.Image) -> Image.Image:
    return over(image, Image.new("RGBA", image.size, (255, 255, 255, 255)))


if __name__ == "__main__":
    for name, make in [("red_circle.png", red_circle), ("blue_square.png", blue_square)]:
        if not (HERE / name).exists():
            save(make(), HERE / name)

    circle = load(HERE / "red_circle.png")
    square = load(HERE / "blue_square.png")
    print(circle.size, circle.mode)  # (512, 512) RGBA
    print(circle.getpixel((206, 206)))  # (220, 40, 40, 200): inside the circle
    print(circle.getpixel((10, 10)))  # (0, 0, 0, 0): transparent

    out = HERE / "out"
    out.mkdir(exist_ok=True)
    save(over(circle, square), out / "circle_over_square.png")
    save(over(square, circle), out / "square_over_circle.png")
    save(beside(circle, square), out / "beside.png")
    save(mirror(circle), out / "mirror.png")
    save(over(fade(circle, 0.4), square), out / "faded_over.png")
    small = scale(circle, 0.5)
    print(small.size)  # (256, 256)
    save(over(small, square, 256, 256), out / "small_circle_at.png")
    print(over(circle, square).getpixel((300, 300)))  # where the two overlap
