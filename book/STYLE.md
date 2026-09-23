# How this book is written

This is an open textbook on **writing interpreters for small languages**, used in the
Programming Languages Lab at the University of Pisa. Every chapter is a lecture. The
order of topics is fixed; the text is not.

## Who reads it

Second- and third-year students who can write Python, know lists, dictionaries and
recursion, and have never built an interpreter. They read on a screen, often the night
before a lecture, and they have an AI assistant open in another window. The book has to
be worth more than that window: it has to say *why*, not just *how*.

## The voice

- Write like a person explaining to one student across a table. First person plural is
  fine ("we now add…"), second person is fine ("you will notice…").
- Every chapter opens with a **concrete problem** the previous chapter could not solve,
  and closes with what is still missing. No chapter opens with a definition.
- **Say why before how.** Each design decision (a grammar rule, a data structure, an
  environment representation) gets: the alternative we did not take, and what it would
  have cost.
- One idea per paragraph. Short paragraphs. Prose, not bullet lists, for anything that
  is an argument. Bullet lists only for genuinely parallel items.
- **No filler.** Delete: "In this chapter we will explore…", "is a powerful tool",
  "plays a crucial role", "Let's dive in", "Key takeaways", "Conclusion" sections that
  restate the chapter, generic history of programming languages, lists of "advantages".
- No marketing adjectives (powerful, elegant, seamless, robust, modern). If something is
  good, show the case where it pays.
- Technical terms are defined once, in the sentence where they are first needed, in
  bold, and then used consistently.
- Italian readers: keep sentences short and words plain. British or American spelling is
  fine; be consistent within a chapter.

## Code

- Every code block in a chapter is **taken from the chapter's file under `code/`**, and
  that file **runs** with `python3 file.py` (Python 3.12+, `lark` installed). If the text
  needs a fragment that is not in the file, add it to the file first.
- Show code in the order a reader would write it, and run it: after a block that defines
  something, show a call and its output.
- Type annotations everywhere; `match` for anything that dispatches on an AST node;
  `@dataclass(frozen=True)` for AST nodes; `type X = …` aliases (Python 3.12).
- Errors are part of the language: show what happens on bad input, and decide it on
  purpose.

## Structure of a chapter

```
# N. Title                      (one line, no "Chapter N:" prefix — the build adds it)
Opening: the problem              (2–4 paragraphs, no heading)
## Sections                       (as many as needed; "##" only, "###" sparingly)
## Exercises                      (3–6, graded; the last one is open-ended)
## Where we are                   (one paragraph: what we can now express, what we cannot)
```

Sections are named after what they do ("Turning the parse tree into an AST"), not after a
category ("Implementation").

## Mathematics

Use it when it is shorter than prose: the syntax of a language as a grammar, the meaning
of an expression as an equation `⟦e₁ + e₂⟧ρ = ⟦e₁⟧ρ + ⟦e₂⟧ρ`. Inline LaTeX with `$…$`
is fine. Never a formula without a sentence saying what it says.

## What to check when revising

1. Every factual claim about Python, Lark or a language is true for Python 3.12+ and Lark
   1.x. When unsure, run it.
2. The code in the chapter and the code in `code/` agree, and the code runs.
3. The chapter refers only to things introduced in earlier chapters.
4. The exercises can actually be done with what the chapter teaches.
