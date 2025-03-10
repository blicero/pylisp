#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-03-10 20:41:17 krylon>
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

from krylisp import data, error, lisp, parser


def default_env() -> data.Environment:
    """Return a fresh default environment."""
    env: data.Environment = data.Environment()

    env["pi"] = 3.141592
    env["peter"] = "Wer das liest, ist doof."
    env["mu"] = data.Symbol(":abobo")

    return env


class TestInterpreter(unittest.TestCase):
    """Test the interpreter."""

    def test_01_atoms(self) -> None:
        """Test evaluating atoms"""
        interpreter = lisp.LispInterpreter(default_env())
        interpreter.debug = True

        test_cases = [
            (data.Symbol("pi"), 3.141592, False),
            (data.Symbol(":hallo"), data.Symbol(":hallo"), False),
        ]

        for c in test_cases:
            try:
                result = interpreter.eval_expr(c[0])
                print(f"(Eval {c[0]} => {result.__class__} {result}")
                self.assertEqual(result, c[1])
            except Exception as err:  # pylint: disable-msg=W0718
                if not c[2]:
                    self.fail(f"{err.__class__}: {err}")

    def test_02_lists(self) -> None:
        """Test evaluating lists."""
        interpreter = lisp.LispInterpreter(default_env())
        interpreter.debug = True

        test_cases = [
            ("(+ 5 7)", 12, False),
            ("(* 8 8)", 64, False),
            ("(/ 32 0)", None, True),
            ("(defun id (x) x)", data.Symbol("id"), False),
        ]

        for c in test_cases:
            ast = parser.parse_string(c[0])
            if c[2]:
                with self.assertRaises(error.LispError):
                    _ = interpreter.eval_expr(ast)
            else:
                try:
                    res = interpreter.eval_expr(ast)
                except Exception as err:  # pylint: disable-msg=W0718
                    self.fail(f"{err.__class__} was caught: {err}")
                else:
                    self.assertEqual(c[1], res)

# Local Variables: #
# python-indent: 4 #
# End: #
