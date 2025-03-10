#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-03-10 18:25:02 krylon>
#
# /data/code/python/krylisp/test_interpreter.py
# created on 10. 03. 2025
# (c) 2025 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
krylisp.test_interpreter

(c) 2025 Benjamin Walkenhorst
"""

import unittest

from krylisp import data, lisp


def default_env() -> data.Environment:
    """Return a fresh default environment."""
    env: data.Environment = data.Environment()

    env["pi"] = 3.141592
    env["peter"] = "Wer das liest, ist doof."
    env["mu"] = data.Atom(":abobo")

    return env


class TestParser(unittest.TestCase):
    """Test the interpreter."""

    def test_01_atoms(self) -> None:
        """Test evaluating atoms"""
        interpreter = lisp.LispInterpreter(default_env())

        test_cases = [
            (data.Atom("pi"), 3.141592, False),
            (data.Atom(":hallo"), data.Atom(":hallo"), False),
        ]

        for c in test_cases:
            try:
                result = interpreter.eval_expr(c[0])
                self.assertEqual(result, c[1])
            except Exception as err:  # pylint: disable-msg=W0718
                self.assertTrue(c[2], f"Unexpected {err.__class__}: {err}")

# Local Variables: #
# python-indent: 4 #
# End: #
