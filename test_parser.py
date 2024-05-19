#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-05-19 21:15:14 krylon>
#
# /data/code/python/krylisp/test_parser.py
# created on 19. 05. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
krylisp.test_parser

(c) 2024 Benjamin Walkenhorst
"""

import traceback
import unittest
from typing import Final, Optional, Union

from krylisp import data, parser


class TestParser(unittest.TestCase):
    """Test the parser"""

    def test_01_atoms(self) -> None:
        """Test parsing atoms"""
        test_cases: Final[list[tuple[str, Optional[Union[data.ConsCell, data.Atom]], bool]]] = [
            ("31", data.Atom(31), False),
            ("+", data.Atom("+"), False),
            ("", data.Atom("nil"), False),
        ]

        for c in test_cases:
            if c[2]:
                with self.assertRaises(parser.ParseError):
                    _ = parser.parse_string(c[0], True)
            else:
                try:
                    res = parser.parse_string(c[0], True)
                except Exception as err:  # pylint: disable-msg=W0718
                    msg: str = "\n".join(traceback.format_exception(err))
                    self.fail(f"Failed to parse '{c[0]}': {msg}")
                else:
                    if c[1] is None:
                        self.assertIsNone(res)
                    else:
                        self.assertEqual(res, c[1])


# Local Variables: #
# python-indent: 4 #
# End: #
