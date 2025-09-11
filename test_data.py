#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-09-11 18:27:45 krylon>
#
# /data/code/python/krylisp/test_data.py
# created on 18. 05. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
krylisp.test_data

(c) 2024 Benjamin Walkenhorst
"""

import unittest
from typing import Any, Final

from krylisp import data


class TestBasics(unittest.TestCase):
    """Test the basic stuff."""

    def test_01_qw(self) -> None:
        """Test the function qw"""
        test_cases: Final[list[tuple[str, list[str]]]] = [
            ("a b c", ["a", "b", "c"]),
            ("", []),
            ("abobo macht kinder froh", ["abobo", "macht", "kinder", "froh"]),
        ]

        for c in test_cases:
            result = data.qw(c[0])
            self.assertEqual(result, c[1])

    def test_02_listp(self) -> None:
        """Test listp"""
        test_cases: Final[list[tuple[Any, bool]]] = [
            (None, True),
            (data.ConsCell(3, None), True),
            ("Abobo", False)
        ]

        for c in test_cases:
            self.assertEqual(data.listp(c[0]), c[1])

    def test_03_is_atomic(self) -> None:
        """Test is_atomic"""
        test_cases: Final[list[tuple[Any, bool]]] = [
            (None, False),
            (42, True),
            (3.141592, True),
            ("Wer das liest, ist doof.", True),
            (data.Symbol("LAMBDA"), True),
            (data.ConsCell(data.Symbol("LAMBDA"), None), False),
        ]

        for c in test_cases:
            self.assertEqual(data.is_atomic(c[0]), c[1])


class TestAtom(unittest.TestCase):
    """Test Atoms"""

    def test_01_eq(self) -> None:
        """Test checking for equality"""
        test_cases: Final[list[tuple[data.Symbol, Any, bool]]] = [
            (data.Symbol("peter"), data.Symbol("peter"), True),
            (data.Symbol("PETER"), data.Symbol("peter"), True),
            (data.Symbol("PETER"), 3, False),
            (data.Symbol("LAMBDA"), data.Symbol("ABOBO"), False),
            (data.NIL, data.EMPTY_LIST, True),
            (data.NIL, None, True),
        ]

        for c in test_cases:
            self.assertEqual(c[0] == c[1], c[2], f"(eq {c[0]} {c[1]})? Expected {c[2]}")


class TestCons(unittest.TestCase):
    """Test cons cells"""

    def test_01_basics(self) -> None:
        """Test some really basic assumptions."""
        lst = data.ConsCell.fromList([1, 2, 3, 4, 5])
        self.assertEqual(len(lst), 5)
        self.assertEqual(str(lst), "(1 2 3 4 5)")
        self.assertNotEqual(lst, data.NIL)

        empty = data.ConsCell(None, None)
        self.assertEqual(len(empty), 0)
        self.assertEqual(empty, data.NIL)
        self.assertEqual(empty, data.EMPTY_LIST)

        l1 = data.ConsCell.fromList([1, 2, 3, 4, 5])
        l2 = data.ConsCell.fromList([1, 2, 3, 4, 5])
        l3 = data.ConsCell.fromList([data.Symbol(x) for x in data.qw("lambda sigma delta")])

        self.assertEqual(l1, l2)
        self.assertEqual(l2, l1)
        self.assertNotEqual(l1, l3)

# Local Variables: #
# python-indent: 4 #
# End: #
