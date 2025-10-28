# Test Task: Simple Function Implementation

**Task ID**: TEST_SIMPLE_TASK
**Duration**: 5 minutes
**Priority**: Test
**Status**: Ready for Testing

---

## 🎯 Objective

Create a simple Python utility function to verify the parallel AI system is working correctly.

## 📦 Deliverables

### 1. Simple Math Utility (20 lines)
**File**: `test_output/math_utils.py`

**Requirements**:
- Function `add(a: int, b: int) -> int`: Returns sum of two integers
- Function `multiply(a: int, b: int) -> int`: Returns product of two integers
- Complete type hints
- Docstrings with examples

**Example Implementation**:
```python
"""Simple math utilities for testing"""

def add(a: int, b: int) -> int:
    """
    Add two integers.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Sum of a and b

    Examples:
        >>> add(2, 3)
        5
    """
    return a + b


def multiply(a: int, b: int) -> int:
    """
    Multiply two integers.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Product of a and b

    Examples:
        >>> multiply(2, 3)
        6
    """
    return a * b
```

### 2. Unit Tests (30 lines)
**File**: `test_output/test_math_utils.py`

**Requirements**:
- Test `add()` function with positive numbers
- Test `add()` with negative numbers
- Test `multiply()` function with positive numbers
- Test `multiply()` with zero
- 100% coverage

**Example Implementation**:
```python
"""Unit tests for math utilities"""

import pytest
from math_utils import add, multiply


def test_add_positive():
    """Test addition with positive numbers"""
    assert add(2, 3) == 5
    assert add(10, 20) == 30


def test_add_negative():
    """Test addition with negative numbers"""
    assert add(-5, 3) == -2
    assert add(-10, -20) == -30


def test_multiply_positive():
    """Test multiplication with positive numbers"""
    assert multiply(2, 3) == 6
    assert multiply(10, 5) == 50


def test_multiply_zero():
    """Test multiplication with zero"""
    assert multiply(5, 0) == 0
    assert multiply(0, 10) == 0
```

---

## ✅ Success Criteria

- [x] File `test_output/math_utils.py` created with 2 functions
- [x] File `test_output/test_math_utils.py` created with 4 tests
- [x] All tests pass when running `pytest test_output/`
- [x] Complete docstrings with examples
- [x] 100% type hints

---

## 📝 Implementation Steps

1. Create directory `test_output/`
2. Write `math_utils.py` with `add()` and `multiply()` functions
3. Write `test_math_utils.py` with 4 test functions
4. Run `pytest test_output/` to verify
5. Report completion

**Estimated Time**: 5 minutes
