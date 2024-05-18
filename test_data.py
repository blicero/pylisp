#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-05-18 15:46:14 krylon>
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
from typing import Final

from krylisp import data


class TestBasics(unittest.TestCase):
    """Test the basic stuff."""

    def test_01_qw(self) -> None:
        """Test the function qw"""
        test_cases: Final[list[tuple[str, list[str]]]] = [
            ("a b c", ["a", "b", "c"]),
        ]

        for c in test_cases:
            result = data.qw(c[0])
            self.assertEqual(result, c[1])

# Local Variables: #
# python-indent: 4 #
# End: #
