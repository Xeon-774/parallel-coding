import math
import time

import pytest

from orchestrator.recursive import RecursionValidator


def test_validate_depth_happy_path():
    res = RecursionValidator.validate_depth(0, 3, {1: 5, 2: 3, 3: 1})
    assert res.is_valid is True
    assert res.max_workers == 5
    assert res.adjusted_timeout is not None
    # base 300, factor 1.5 ** 1
    assert res.adjusted_timeout == int(300 * (1.5 ** 1))


def test_validate_depth_negative_current():
    res = RecursionValidator.validate_depth(-1, 3, {1: 5})
    assert res.is_valid is False
    assert "negative" in (res.error_message or "").lower()


def test_validate_depth_negative_max():
    res = RecursionValidator.validate_depth(0, -1, {1: 5})
    assert res.is_valid is False
    assert "max depth" in (res.error_message or "").lower()


def test_validate_depth_reach_max():
    # current == max -> cannot create next level
    res = RecursionValidator.validate_depth(3, 3, {4: 1})
    assert res.is_valid is False
    assert "max recursion depth" in (res.error_message or "").lower()


def test_timeout_growth_increases_monotonically():
    t1 = RecursionValidator.validate_depth(0, 5, {1: 1}).adjusted_timeout
    t2 = RecursionValidator.validate_depth(1, 5, {2: 1}).adjusted_timeout
    t3 = RecursionValidator.validate_depth(2, 5, {3: 1}).adjusted_timeout
    assert t1 < t2 < t3


def test_workers_default_to_one_for_missing_depth():
    res = RecursionValidator.validate_depth(2, 5, {1: 8, 2: 3})
    assert res.is_valid is True
    assert res.max_workers == 1


def test_detect_circular_reference_true():
    assert RecursionValidator.detect_circular_reference(["root", "child"], "child")


def test_detect_circular_reference_false():
    assert not RecursionValidator.detect_circular_reference([
        "root",
        "child",
    ], "leaf")

