# Lecture 8: Function Abstraction - Design and Semantics

TODO: add a comment about the purpose similarity between Operator and Closure. We leave them distinct for clarity. In particular the similarity augments if closures are saved semantically, by putting in the environment the function of state and env that computes the resulting value and the resulting state. In that case, operators are just closures that do not capture any state.

TODO: explain that in a modern real-world language, function application and operator application are the same thing and one can also define or redefine operators. In our language, we leave them distinct for clarity and ease of explanation.

## Requirements and Goals

- Extend the mini-language to support user-defined functions with a single argument.
- Functions and constants both take one argument for simplicity.
- Functions are declared with the syntax:

  ```
  function f(x) command1; ...; commandN; return expr
  ```

- The `return` statement closes the function body and environment.
- Introduce a new concrete and abstract syntax category for function bodies.
- Functions are denotable (can be stored in environments and sub-blocks), but not memorizable (not stored in the store).
- Lexical (static) scoping: closures are pairs of function code and their declaration environment.
- Functions can be declared in any block (e.g., inside an `if` or `while` block).
- Closures cannot escape their state because they are not memorizable.
- On function application, only the store of the calling point is passed; the calling environment is NOT passed. All functions are closures in their environment.
- Add a test program demonstrating that state variables are passed correctly to closures in blocks.

## Syntax Extensions

- **Function Declaration:**
  ```
  function f(x) command_seq; return expr
  ```
- **Function Application:**
  ```
  f(expr)
  ```
- **Function Body:**
  - A sequence of commands followed by a return expression.

## Abstract Syntax Extensions

- `FunctionDecl(name, param, body)`
- `FunctionBody(commands, return_expr)`
- `FunctionApp(name, arg)`
- `Closure(function, env)`

## Semantics

- **Function Declaration:**
  - Binds the function name to a closure (function + environment) in the current environment.
- **Closure:**
  - A pair of the function declaration and the environment at the point of declaration.
- **Function Application:**
  - Looks up the closure in the environment.
  - Evaluates the argument in the calling environment and state.
  - Binds the parameter to the argument value in the closure's environment.
  - Executes the function body commands in the closure's environment and the current store.
  - Evaluates the return expression in the closure's environment and the updated store.
- **Lexical Scoping:**
  - The closure captures the environment at the point of function declaration, not at the point of call.
- **No Closure Escape:**
  - Since closures are not memorizable, they cannot be stored in the store and thus cannot escape their state.
- **Block-local Functions:**
  - Functions can be declared in any block, and their environment is the block in which they are declared.

## Test Program

A test program is included to demonstrate that closures in blocks capture the correct state variables:

```
var x = 10;
if x > 0 then
    var y = 42; function f(z) print y; return y + z
else
    function f(z) print 0; return z;
print f(5)
```

- If `x > 0`, `f` is defined in the `then` block and captures `y = 42`.
- The call `f(5)` prints `42` and returns `47`.
- If `x <= 0`, `f` is defined in the `else` block and prints `0` and returns `5`.

## Summary

- This design ensures that all functions are closures with lexical scoping, and that closures cannot escape their state.
- The semantics are clear, modular, and support block-local function declarations and correct state passing to closures.
