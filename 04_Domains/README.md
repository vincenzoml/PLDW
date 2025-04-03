# Chapter 4: Semantic domains and expressions with identifiers and environment

# Syntactic domains

- Files

- Strings

- Tokens

- Parse tree

- Syntax tree

# Semantic domains

Numbers

Identifiers (names of constants, variables, functions, etc.)

Environment (maps identifiers to a semantic domain called "denotable values")

State (maps memory locations to a semantic domain called "memorizable values")

Expressible values: the semantic domain to which expressions evaluate.

# Implementation of environment and state

We adopt a purely mathematical standpoint. These domains are implemented using functions, and update is a map from functions to functions. 

Indeed, in practice, one uses hashtables (also nested ones) for the environment, which can also be eliminated in some cases by the compilation process, and pointers for memory. 

