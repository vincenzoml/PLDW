# Blind-folded Exercise: Arithmetic Expression Parser
# ------------------------------------------------------
# Write a program that parses arithmetic expressions like "2 + 5 - 3 * 4" and returns the result.
# Assumptions:
# - Operators and operands are separated by spaces
# - Only binary operators (+, -, *) are used
# - No parentheses are in the expressions
# - Operations should be evaluated with standard precedence rules (* and / before + and -)
# - Operands are integers
# - Expression is well-formed (no syntax errors)

# %%
from typing import List, Tuple, Union


# Solution 1: Naive recursive solution using string splitting
def parse_expression_naive(expression: str) -> int:
    # Split by + and -
    tokens: List[str] = expression.split()
    if len(tokens) == 1:  # Just a number
        return int(tokens[0])

    result: int = int(tokens[0])
    i: int = 1
    while i < len(tokens):
        op: str = tokens[i]
        i += 1
        if op == "+":
            result += int(tokens[i])
        elif op == "-":
            result -= int(tokens[i])
        elif op == "*":
            result *= int(tokens[i])
        i += 1

    return result


# %%

parse_expression_naive("2 + 5 * 3")


# %%


def parse_expression(expression: str) -> int:
    """
    Parses an arithmetic expression respecting operator precedence.
    This solution handles * and / before + and - by processing in two passes.
    """
    tokens: List[str] = expression.split()

    # First pass: handle multiplication and division
    i = 1
    while i < len(tokens) - 1:
        op = tokens[i]
        if op in ("*"):
            left = int(tokens[i - 1])
            right = int(tokens[i + 1])
            result = left * right

            # Replace the three tokens with the result
            tokens[i - 1 : i + 2] = [str(result)]

            # Note that this uses a comfortable Python feature:
            # the list comprehension syntax.
            # tokens[i - 1 : i + 2] = [str(result)] is equivalent to
            # tokens[i - 1] = str(result)
            # remove tokens[i] and tokens[i + 1]
        else:
            i += 2

    # Second pass: handle addition and subtraction
    result = int(tokens[0])
    i = 1
    while i < len(tokens) - 1:
        op = tokens[i]
        right = int(tokens[i + 1])
        if op == "+":
            result += right
        elif op == "-":
            result -= right
        i += 2

    return result


# %%

parse_expression("2 + 5 * 3")


# %%

# We have used quite a few Python features here. What if we only had memory and pointers?


def parse_int(
    expression: str, i: int
) -> Tuple[int, int]:  # returns an integer and the next index
    """
    Parses an integer from the expression starting at index i.
    """
    result: int = 0
    while i < len(expression) and expression[i] == " ":
        i += 1
    while i < len(expression) and expression[i].isdigit():
        result = result * 10 + int(expression[i])
        i += 1
    return (result, i)


# Q: Why is this function returning int | None?
def parse_expression_naive_classic(expression: str) -> int | None:
    """
    Parses an arithmetic expression using a naive iteration approach.
    """
    next_token = parse_int(expression, 0)
    accumulator = next_token[0]
    i = next_token[1]
    state = ""
    while i < len(expression):
        print(
            f"accumulator: {accumulator}, state: {state}, i: {i}, expression[i]: {expression[i:]}"
        )
        if state == "":
            if expression[i] == " ":
                i += 1
                continue
            else:
                state = expression[i]
                i += 1
                continue
        if state == "+":
            next_token = parse_int(expression, i)
            accumulator += next_token[0]
            i = next_token[1]
            state = ""
            continue
        if state == "-":
            next_token = parse_int(expression, i)
            accumulator -= next_token[0]
            i = next_token[1]
            state = ""
            continue
        if state == "*":
            next_token = parse_int(expression, i)
            accumulator *= next_token[0]
            i = next_token[1]
            state = ""
            continue
        else:
            print(f"Error: Invalid state: {state}")
            return None
    return accumulator


parse_expression_naive_classic("2 + 5 * 3")

# %%

# Bonus Exercise (balanced parentheses problem)
#-------------------------------------------------------------------------------------------------------------------------------------------
# Write a program that parses an expression composed of pantheses and returns true if they are balanced 
# (i.e, every open parenthesis has a correspondent closed parenthesis and the order of opening and closing is correct) and false otherwise.

#Solution 1

def balanced_parentheses(expression: str) -> bool:
    stack = []
    couples = {')': '(', ']': '[', '}': '{'} 
    
    for c in expression:
        if c in "([{":
            stack.append(c)
        elif c in ")]}":
            if not stack or stack[-1] != couples[c]:
                return False
            stack.pop()
    
    return len(stack) == 0


