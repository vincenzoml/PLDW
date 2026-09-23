#!/usr/bin/env python3
"""Build the course site: the book as HTML (one page per chapter), the slides, the
index. Sources are never touched.

    python3 tools/build.py            # -> site/
    python3 tools/build.py --pdf      # also site/book.pdf (needs xelatex)
    python3 tools/build.py --serve    # build, then serve site/ on :8000

Layout of the sources:
    book/NN-slug.md        one chapter per file, sorted by NN
    book/figures/          figures, referenced from the chapters as figures/...
    slides/NN-slug.html    one self-contained HTML5 deck per lecture
    slides/assets/         theme shared by the decks
    code/NN-slug/          the code shown in chapter NN
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book"
SLIDES = ROOT / "slides"
CODE = ROOT / "code"
TOOLS = ROOT / "tools"
SITE = ROOT / "site"

TITLE = "Programming Languages Lab"
SUBTITLE = "An open textbook on writing interpreters — University of Pisa"

CHAPTER_RE = re.compile(r"^(\d\d)-([a-z0-9-]+)\.md$")


def chapters() -> list[tuple[str, str, Path]]:
    """(number, slug, path) for every chapter, in order."""
    out = []
    for p in sorted(BOOK.iterdir()):
        m = CHAPTER_RE.match(p.name)
        if m:
            out.append((m.group(1), m.group(2), p))
    return out


def chapter_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return re.sub(r"^#\s*(\d+\.\s*)?", "", line).strip()
    return path.stem


def pandoc(args: list[str]) -> None:
    subprocess.run(["pandoc", *args], check=True)


def body_without_h1(path: Path) -> Path:
    """The chapter with its first H1 removed: pandoc renders the title from metadata."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("# "):
            del lines[i]
            break
    tmp = SITE / "_body.md"
    tmp.write_text("".join(lines), encoding="utf-8")
    return tmp


def build_chapter(num: str, slug: str, path: Path, nav: str) -> None:
    out = SITE / "book" / f"{num}-{slug}.html"
    title = chapter_title(path)
    pandoc(
        [
            str(body_without_h1(path)),
            "-o", str(out),
            "--standalone",
            "--from=markdown+smart",
            "--to=html5",
            "--mathjax",
            "--toc", "--toc-depth=2",
            "--section-divs",
            "--highlight-style=tango",
            f"--css=../assets/book.css",
            f"--metadata=title:{num}. {title}" if num != "00" else f"--metadata=title:{title}",
            f"--metadata=pagetitle:{title} — {TITLE}",
            f"--include-before-body={nav}",
            f"--include-after-body={TOOLS / 'book_footer.html'}",
            "--resource-path", str(BOOK),
        ]
    )


def write_nav(num: str, chs: list[tuple[str, str, Path]]) -> Path:
    """A small top bar with previous/next chapter links, written to a temp file."""
    idx = [c[0] for c in chs].index(num)
    prev_ = chs[idx - 1] if idx > 0 else None
    next_ = chs[idx + 1] if idx + 1 < len(chs) else None
    parts = ['<nav class="top">', '<a href="../index.html">Contents</a>']
    if prev_:
        parts.append(f'<a href="{prev_[0]}-{prev_[1]}.html">← {html.escape(chapter_title(prev_[2]))}</a>')
    if next_:
        parts.append(f'<a href="{next_[0]}-{next_[1]}.html">{html.escape(chapter_title(next_[2]))} →</a>')
    parts.append("</nav>")
    tmp = SITE / "_nav.html"
    tmp.write_text("\n".join(parts), encoding="utf-8")
    return tmp


def decks() -> list[tuple[str, str, Path]]:
    out = []
    for p in sorted(SLIDES.glob("*.html")):
        m = re.match(r"^(\d\d)-([a-z0-9-]+)\.html$", p.name)
        if m:
            out.append((m.group(1), m.group(2), p))
    return out


def deck_title(path: Path) -> str:
    m = re.search(r"<title>(.*?)</title>", path.read_text(encoding="utf-8"), re.S)
    return html.unescape(m.group(1).strip()) if m else path.stem


def build_index(chs, dks) -> None:
    by_num = {n: (s, p) for n, s, p in dks}
    rows = []
    for num, slug, path in chs:
        t = html.escape(chapter_title(path))
        label = f"Chapter {int(num)}"
        deck = ""
        if num in by_num:
            deck = f'<a class="deck" href="slides/{num}-{by_num[num][0]}.html">slides</a>'
        code = ""
        if (CODE / f"{num}-{slug}").is_dir():
            code = f'<a class="deck" href="code/{num}-{slug}/">code</a>'
        rows.append(
            f'<li><span class="num">{label}</span> '
            f'<a href="book/{num}-{slug}.html">{t}</a> {deck} {code}</li>'
        )
    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(TITLE)}</title>
<link rel="stylesheet" href="assets/book.css">
</head><body class="index">
<header class="title-block-header">
<h1 class="title">{html.escape(TITLE)}</h1>
<p class="subtitle">{html.escape(SUBTITLE)}</p>
</header>
<main>
<p>A chapter per lecture: a text to read, the slides shown in class, and a folder of code
that runs. Chapters appear here as they are taught. Chapter 0 and chapter 1 are the two
halves of the first lecture.</p>
<ol class="chapters">
{chr(10).join(rows)}
</ol>
<p><a href="exam/">How you are assessed</a> · <a href="https://github.com/vincenzoml/PLDW">Source repository</a></p>
</main>
{(TOOLS / 'book_footer.html').read_text(encoding='utf-8')}
</body></html>"""
    (SITE / "index.html").write_text(body, encoding="utf-8")


def build_exam() -> None:
    src = ROOT / "exam"
    if not src.is_dir():
        return
    out = SITE / "exam"
    out.mkdir(parents=True, exist_ok=True)
    pages = sorted(src.glob("*.md"))
    for p in pages:
        pandoc(
            [
                str(p), "-o", str(out / (p.stem + ".html")),
                "--standalone", "--from=markdown+smart", "--to=html5",
                "--css=../assets/book.css",
                f"--metadata=pagetitle:{p.stem} — {TITLE}",
                f"--include-after-body={TOOLS / 'book_footer.html'}",
            ]
        )
    links = "\n".join(
        f'<li><a href="{p.stem}.html">{html.escape(chapter_title(p))}</a></li>' for p in pages
    )
    (out / "index.html").write_text(
        f'<!doctype html><html lang="it"><head><meta charset="utf-8">'
        f'<title>Esame — {TITLE}</title><link rel="stylesheet" href="../assets/book.css">'
        f'</head><body class="index"><main><h1>Esame</h1><ul>{links}</ul>'
        f'<p><a href="../index.html">Contents</a></p></main></body></html>',
        encoding="utf-8",
    )


def build_pdf(chs) -> None:
    """The whole book as one PDF, chapters in order."""
    pandoc(
        [
            *[str(p) for _, _, p in chs],
            "-o", str(SITE / "book.pdf"),
            "--from=markdown+smart",
            "--pdf-engine=xelatex",
            "--toc", "--toc-depth=1",
            "--top-level-division=chapter",
            "--highlight-style=tango",
            "--resource-path", str(BOOK),
            "-V", "documentclass=book",
            "-V", "mainfont=IBM Plex Serif",
            "-V", "sansfont=IBM Plex Sans",
            "-V", "monofont=IBM Plex Mono",
            "-V", "fontsize=11pt",
            "-V", "geometry:margin=2.6cm",
            "-V", "colorlinks=true",
            f"--metadata=title:{TITLE}",
            f"--metadata=subtitle:{SUBTITLE}",
        ]
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", action="store_true", help="also build site/book.pdf")
    ap.add_argument("--serve", action="store_true", help="serve site/ after building")
    args = ap.parse_args()

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "book").mkdir(parents=True)
    (SITE / "assets").mkdir()
    shutil.copy(TOOLS / "book.css", SITE / "assets" / "book.css")
    if (BOOK / "figures").is_dir():
        shutil.copytree(BOOK / "figures", SITE / "book" / "figures")
    if SLIDES.is_dir():
        shutil.copytree(SLIDES, SITE / "slides", ignore=shutil.ignore_patterns("*.md"))
    if CODE.is_dir():
        shutil.copytree(CODE, SITE / "code", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    chs = chapters()
    for num, slug, path in chs:
        nav = write_nav(num, chs)
        build_chapter(num, slug, path, str(nav))
        print(f"  book/{num}-{slug}.html")
    (SITE / "_nav.html").unlink(missing_ok=True)
    (SITE / "_body.md").unlink(missing_ok=True)
    build_exam()
    build_index(chs, decks())
    if args.pdf:
        build_pdf(chs)
        print("  book.pdf")
    print(f"Built {len(chs)} chapters and {len(decks())} decks into {SITE.relative_to(ROOT)}/")

    if args.serve:
        os.chdir(SITE)
        subprocess.run([sys.executable, "-m", "http.server", "8000"])


if __name__ == "__main__":
    main()
