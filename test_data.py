#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-05-19 18:53:57 krylon>
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
            (data.ConsCell(data.Atom("3"), None), True),
            ("Abobo", False)
        ]

        for c in test_cases:
            self.assertEqual(data.listp(c[0]), c[1])


class TestAtom(unittest.TestCase):
    """Test Atoms"""

    def test_01_eq(self) -> None:
        """Test checking for equality"""
        test_cases: Final[list[tuple[data.Atom, Any, bool]]] = [
            (data.Atom("peter"), "peter", True),
            (data.Atom("PETER"), data.Atom("peter"), True),
            (data.Atom("32"), data.Atom("32.0"), True),
            (data.Atom("PETER"), data.Atom("3"), False),
            (data.Atom("31"), data.Atom(31), True),
        ]

        for c in test_cases:
            self.assertEqual(c[0] == c[1], c[2])

# Local Variables: #
# python-indent: 4 #
# End: #
