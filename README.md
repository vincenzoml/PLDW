# Programming Language Design Workshop

A hands-on course exploring programming language design concepts using Python's modern features. This course leverages Python's type system and structural pattern matching to demonstrate key programming language concepts and implementations.

## Course Overview

This workshop consists of 10 lectures (2 hours each) that combine theoretical foundations with practical implementations. Students will learn about programming language design principles while getting hands-on experience with Python's advanced features.

## Course Structure

### Lecture 1: Introduction to Programming Language Design

- What is a programming language?
- The importance of programming language design
- The course structure and expectations
- Python as a language for exploring language design concepts

### Lecture 2: Types and Structural Pattern Matching in Python

- Introduction to Python's type system
- Type hints and type checking
- Structural pattern matching (match/case statements)
- Practical applications and examples

### Lecture 3: Programming Language Implementation: A mini interpreter

- Parsing and lexical analysis
- Abstract Syntax Trees (AST)
- Program semantics
- Implementing lexer, parser, and evaluator components

### Lecture 4: Semantic Domains and Environment-Based Interpreters

- Semantic domains: expressible values, denotable values, and environments
- Environment-based interpreters
- Implementing a simple language with variables, functions, and recursion
- Pure functions vs side effects

### Lecture 5: Binding and Scoping

- Variable binding through let expressions
- Static vs dynamic scoping
- Implementing lexical scope
- Environment manipulation and memory management

### Lecture 6: State and Commands

- Introducing state to our language
- Expressions vs commands
- Variable declaration, assignment, and print commands
- Command sequences

### Lecture 7: Control Flow

- Conditionals (if/else) and loops (while)
- Boolean values and expressions
- Unified operator handling
- Block-local variable scoping

### Lecture 8: TBA

### Lecture 9: TBA

### Lecture 10: TBA

## Prerequisites

- Python 3.10 or higher (for pattern matching support)
- Basic Python programming knowledge
- Understanding of basic programming concepts

## Repository Structure

Each lecture has its own directory containing:

- A detailed README.md with lecture notes and exercises
- Python modules with examples and implementations
- Additional resources and references when applicable

## Building the Course Materials

### Requirements

```
pip install -r requirements.txt
```

### Generating Materials

Use the `build.py` script to generate course materials:

```bash
# Generate slides for all chapters
python build.py --slides

# Generate slides for a specific chapter
python build.py --slides --chapter 01

# Generate the course book (PDF and HTML)
python build.py --book

# Generate both slides and course book
python build.py --slides --book
```

The slides are generated from the README.md files in each lecture directory. Slide separators are indicated by HTML comments (`<!-- slide -->`).

### Output Files

- Slides: `Lecture_XX.pdf` (where XX is the chapter number)
- Course book: `course_book.pdf` and `course_book.html`

## Getting Started

1. Clone this repository
2. Ensure you have Python 3.10+ installed
3. Navigate to the specific lecture directory
4. Follow the instructions in each lecture's README.md

## License

[MIT License](LICENSE)
