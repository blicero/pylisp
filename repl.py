#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-03-08 15:56:50 krylon>
#
# /data/code/python/krylisp/repl.py
# created on 08. 03. 2025
# (c) 2025 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
krylisp.repl

(c) 2025 Benjamin Walkenhorst
"""


import atexit
import logging
import readline
from typing import Final

from krylisp import common, lisp, parser

HIST_LENGTH: Final[int] = 20000


class Repl:
    """
    Repl provides a prompt that reads code, evaluates it, and prints the result.

    Hence the name.
    """

    __slots__ = [
        'log',
        'interpreter',
    ]

    log: logging.Logger
    interpreter: lisp.LispInterpreter

    intro: Final[str] = f"""Welcome to {common.APP_NAME} {common.APP_VERSION}
(c) 2025 Benjamin Walkenhorst <krylon@posteo.de>
Type 'help' or '?' for a list of commands.
    """
    prompt: Final[str] = f"({common.APP_NAME})  "

    def __init__(self):
        try:
            readline.read_history_file(common.path.histfile())
            readline.set_history_length(HIST_LENGTH)
        except FileNotFoundError:
            pass
        else:
            atexit.register(readline.write_history_file, common.path.histfile())

        self.log = common.get_logger("REPL")
        self.interpreter = lisp.LispInterpreter()

    def run(self) -> None:
        """Run the read-eval-print-loop"""
        print(self.intro)

        while True:
            try:
                txt: str = input(self.prompt)

                if txt.lower() == '#quit':
                    break

                ast = parser.parse_string(txt)
                result = self.interpreter.eval_expr(ast)

                print(result)
            except Exception as err:  # pylint: disable-msg=W0718
                self.log.error("%s was raised: %s",
                               type(err),
                               err)


if __name__ == '__main__':
    r = Repl()
    r.run()


# Local Variables: #
# python-indent: 4 #
# End: #
