# Programming Languages Lab

An open textbook, with slides and code, on **writing interpreters for small
languages** — the laboratory module of *Linguaggi di Programmazione* at the University of
Pisa (3 credits, one lecture a week). Taught by Vincenzo Ciancia (CNR-ISTI).

**Read it here:** <https://vincenzoml.github.io/PLDW/>

## What the course is about

You already know how to write a program. This course asks why anyone would build a
*language* instead, and answers by making you build one: a domain-specific language for a
domain of your choice — images, music, geometry, graphs, sound, text, 3D models — with a
parser, an interpreter, and examples that show it is good for something.

The thesis is that a language is how a person keeps control of an automatic system. AI
assistants are allowed and expected while you build; what you must own is every
primitive, every example and every design decision, because the exam is you explaining
your language in front of the class and saying where it is wrong.

## Programme

Lectures appear here as they are taught. The full sequence:

| # | Lecture | Exam |
|---|---------|------|
| 1 | **Why build a language** (part A) — Chomsky, symbolic AI, one real case: VoxLogicA | no |
| 1 | **What a language is made of** (part B) — syntax, semantics, forty lines of Python | yes |
| 2 | Types and pattern matching in Python | yes |
| 3 | AI-assisted coding and GitHub — how to work | no |
| 4 | A mini interpreter — parsing with Lark, ASTs, evaluation | yes |
| 5 | Semantic domains and environments | yes |
| 6 | Binding and scoping | yes |
| 7 | State and commands | yes |
| 8 | Control flow | yes |
| 9 | Functions and closures | yes |
| 10 | A language in the wild: spatial logic and VoxLogicA | no |

Each lecture is a chapter of the book (`book/`), a deck of slides (`slides/`) and a folder
of code that runs (`code/`). The book chapters are numbered by topic, so chapter numbers
and lecture numbers differ slightly.

## Exam

A midway submission, required and graded (one third): your domain, your primitives and
why, a first interpreter that runs. A final presentation with slides and a live demo in
front of the class, followed by questions on your code and on the theory (two thirds).
Texts and rules, in Italian: [`exam/`](exam/).

## Running the code

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
python3 code/01-introduction/language.py
```

Python 3.12 or later. The only library the interpreters need is `lark`.

## Building the site

```bash
python3 tools/build.py          # -> site/  (needs pandoc)
python3 tools/build.py --serve  # then open http://localhost:8000
python3 tools/build.py --pdf    # also site/book.pdf (needs xelatex and IBM Plex fonts)
```

The slides are plain HTML files that open in any browser, with or without a build.

## Layout

```
book/       one Markdown file per chapter, figures in book/figures/, STYLE.md for authors
slides/     one HTML5 deck per lecture (reveal.js), shared theme in slides/assets/
code/       the code shown in each chapter, one folder per chapter
exam/       exam rules and the texts of the two assignments (Italian)
docs/       the teacher's programme and notes (Italian)
tools/      the build script and the book stylesheet
```

## Licence

Text and figures: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Code: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0). Figures from published
papers are reproduced with the authors' permission and cited in the chapters.

The previous edition of the course (2025, PDF slides generated from the same sources) is
on the branch `edizione-2025`.
