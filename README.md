# Programming Languages Lab

**Slides online: <https://vincenzoml.github.io/PLDW/>**

Slides and code on **writing interpreters for small languages** — the laboratory module of *Linguaggi di Programmazione* at the University of
Pisa (3 credits, one lecture a week). Taught by Vincenzo Ciancia (CNR-ISTI).

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

Lectures appear here as they are taught.

1. Introduction to programming language design
2. Types and structural pattern matching in Python
3. Programming language implementation: a mini interpreter
4. Semantic domains and environment-based interpreters
5. Binding and scoping
6. State and commands
7. Control flow
8. Functions

## Slides

Online at **<https://vincenzoml.github.io/PLDW/>**. They are plain HTML files: a downloaded copy of the repository opens in any browser too.

- `slides/lesson-00.html` — Lecture 0: why build a language?
- `slides/lesson-01a.html` — Lecture 1, part A: what a language is made of
- `slides/lesson-01b.html` — Lecture 1, part B: Python, with VS Code

## Exam

The exam rules will be published here during the course.

## Running the code

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
python3 code/01-introduction/language.py
```

Python 3.12 or later. The only library the interpreters need is `lark`.

## Layout

```
slides/     one HTML deck per lecture (reveal.js), shared theme in slides/assets/
book/       figures used by the slides
code/       the code shown in the lectures
```

## Licence

Text and figures: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Code: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0). Figures from published
papers are reproduced with the authors' permission and cited in the slides.
