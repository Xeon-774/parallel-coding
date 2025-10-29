"""Simple calculator module providing basic arithmetic operations.

This module defines four functions: `add`, `subtract`, `multiply`, and
`divide`, each operating on two numeric values. All functions include type
annotations and docstrings. Division by zero is explicitly handled by raising
`ZeroDivisionError` with a clear message.
"""

from typing import Union

# Define a simple numeric type alias for clarity
Number = Union[int, float]


def add(a: Number, b: Number) -> Number:
    """Return the sum of two numbers.

    Parameters:
        a: The first addend.
        b: The second addend.

    Returns:
        The arithmetic sum of `a` and `b`.
    """

    return a + b


def subtract(a: Number, b: Number) -> Number:
    """Return the difference of two numbers (a - b).

    Parameters:
        a: The minuend.
        b: The subtrahend.

    Returns:
        The arithmetic difference of `a` and `b`.
    """

    return a - b


def multiply(a: Number, b: Number) -> Number:
    """Return the product of two numbers.

    Parameters:
        a: The first factor.
        b: The second factor.

    Returns:
        The arithmetic product of `a` and `b`.
    """

    return a * b


def divide(a: Number, b: Number) -> float:
    """Return the quotient of two numbers (a / b).

    Parameters:
        a: The dividend.
        b: The divisor.

    Returns:
        The result of dividing `a` by `b` as a float.

    Raises:
        ZeroDivisionError: If `b` is zero.
    """

    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
