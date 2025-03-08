#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-03-08 22:45:24 krylon>
#
# /data/code/python/krylisp/parser.py
# created on 19. 05. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
krylisp.parser

(c) 2024 Benjamin Walkenhorst
"""

from typing import Final, Optional, Union

from pyparsing import (Forward, Literal, ParseException, ParseResults,
                       QuotedString, Regex, Suppress, Word, ZeroOrMore, alphas,
                       nums)

from krylisp import data
from krylisp.error import CantHappenError

DEBUG_GRAMMAR: Final[bool] = False

open_paren = Suppress(Literal("("))
close_paren = Suppress(Literal(")"))

expr = Forward()
string = QuotedString('"')
integer = Regex(r"-?\d+").setParseAction(lambda string, loc, tok: int(tok[0]))
floating_point_number = Regex(r"-?\d+[.]\d+(?:e-?\d+)?").setParseAction(
    lambda string, loc, tok: float(tok[0]))
word_chars = alphas + nums + "-!$:%&/=+-_*<>|"
symbol = Word(word_chars).setParseAction(lambda string, loc, tok: data.Atom(tok[0]))
comment = Suppress(Regex(";[^\n]*"))
token = Forward()

lisp_list = open_paren + ZeroOrMore(expr) + close_paren
lisp_list.setParseAction(
    lambda st, loc, tok: result_to_list(tok) if len(tok) > 0 else data.ConsCell(None, None))
quote_expr = (Suppress(Literal("'")) + expr).setParseAction(
    lambda st, loc, tok: quote_body(data.Atom("quote"), result_to_list(tok)))

# Eigentlich brauche ich hier eine Regel für Backquoted-Listen, damit
# der Parser da auch rekursiv durchsteigen kann.  Und ich muss dafür
# sorgen, dass aus `(peter horst karl) (backquote (peter horst karl))
# wird, und nicht (backquote peter horst karl)!!!
splice_expr = (Suppress(Literal(",@")) + expr).setParseAction(
    lambda st, loc, tok: data.ConsCell(data.Atom("comma-at"), result_to_list(tok)))
unquote_expr = (Suppress(Literal(",")) + expr).setParseAction(
    lambda st, loc, tok: data.ConsCell(data.Atom("comma"), result_to_list(tok)))
# backquote = Forward
backquote_content = Forward()
backquote_list = open_paren + ZeroOrMore(backquote_content) + close_paren
backquote_list.setParseAction(lambda st, loc, tok: result_to_list(tok))
backquote_content << (expr |    # pylint: disable-msg=W0104
                      splice_expr |
                      unquote_expr |
                      backquote_list)
backquote_expr = (Suppress(Literal("`")) + backquote_content).setParseAction(
    lambda st, loc, tok: quote_body(data.Atom("backquote"), result_to_list(tok)))
token << (floating_point_number |  # pylint: disable-msg=W0104
          integer |
          string |
          symbol |
          comment |
          quote_expr |
          backquote_expr)

# for x in (backquote_content, backquote_list, backquote_expr):
#     x.setDebug(True)

expr << (token | lisp_list)  # pylint: disable-msg=W0104

program = ZeroOrMore(expr)

if DEBUG_GRAMMAR:
    for xpr in (open_paren,
                close_paren,
                string,
                # number,
                symbol,
                token,
                lisp_list,
                expr,
                program):
        xpr.setDebug(True)


class ParseError(Exception):
    """Base class for errors that occur in the parser"""


class SyntaxException(ParseError):
    """A SyntaxException is raised when the parsers encounters a malformed program"""


class IncompleteException(ParseError):
    """
    IncompleteException indicates that the parsed code is incomplete.

    An example would be an unmatched open parenthesis.
    """


def result_to_list(r: ParseResults) -> data.ConsCell:
    """
    Return the argument r as a Lisp list.

    Atoms and numbers are returned verbatim.
    """
    # print "result_to_list({0.__class__}({0}))".format(r)
    lst = []
    if isinstance(r, (list, tuple)):
        return data.ConsCell.fromList(r)
    if isinstance(r, data.ConsCell):
        return r
    if isinstance(r, data.Atom):
        return data.ConsCell(r, None)
    if isinstance(r, (int, float, str)):
        a = data.Atom(r)
        return data.ConsCell(a, None)

    for x in r:
        if isinstance(x, ParseResults):
            lst.append(result_to_list(x))
        elif isinstance(x, (list, tuple)):
            lst.append(data.ConsCell.fromList(x))
        else:
            lst.append(x)
    return data.ConsCell.fromList(lst)


def quote_body(head, body) -> data.ConsCell:
    """Return a list consisting of the head verbatim and the body quoted"""
    return data.ConsCell(head,
                         data.ConsCell(body, None)
                         if not isinstance(body, data.ConsCell)
                         else body)


# Als nächstes möchte ich gern auch Makros schreiben und einsetzen können,
# damit ich nicht so viele Special Forms schreiben kann.
# Dafür bräuchte ich im Parser ein Environment mit Makros und müsste beim
# Parsen prüfen, ob irgendwo ein Makro auftaucht, DAS wiederum durch den
# Lisp-Interpreter heizen - der ganze State liegt ja zum Glück im Environment -
# und dann die entstehende Liste an den regulären Interpreter durchreichen...
# Mooooment - ich KÖNNTE Makros auch im Interpreter selbst expandieren... wenn
# ich Makros als Liste speichere, die anstelle von lambda z.B. ein macro am
# Anfang stehen haben... ;-) Aber ... ...
#
# Ja, die Idee, Makros direkt im Interpreter unterzubringen ist gar nicht
# schlecht, aber wenn ich keine Backquotes/Kommata unterstütze, wird das
# Schreiben von Makros unerträglich eklig.
# Aaaaber Backquotes, Komma und Komma-At funktionieren in Common Lisp auch
# außerhalb von Makrodefinitionen. Aber Moment ... ,@ ... dafür müsste ich
# noch eine Special Form im Interpreter implementieren.
# Für das Komma würde es reichen, wenn der Parser wüsste, ob wir im Moment
# innerhalb eines Backquote-Ausdrucks sind, aber ,@ kann erfordern, erst ein
# Symbol auszuwerten oder so, und das dann in den übergebordneten Ausdruck
# zu splicen, das muss ich zwangsläufig im Interpreter tun.
def parse_string(s: str, dbg: bool = False) -> Optional[Union[data.Atom, data.ConsCell, data.Function]]:
    """Attempt to parse a string and return the result"""
    assert isinstance(s, str)
    res = None
    try:
        res = program.parseString(s)
    except ParseException as err:
        print(err.line)
        print(" "*(err.column-1) + "^")
        print(err)
        raise SyntaxException() from err

    if dbg:
        print(f"Got {type(res)}: {res}")

    if res is None or len(res) == 0:
        return data.Atom("nil")

    if len(res) == 1:
        if data.is_atomic(res[0]):
            match res[0]:
                case data.Atom(value):
                    return res[0]
                case x if isinstance(x, (int, str, float)):
                    return data.Atom(x)
                case _:
                    raise CantHappenError(f"Unexpected type: {res[0].__class__}")
        else:
            return result_to_list(res[0])

        match res[0]:
            case None:
                return None
            case data.Atom(value):
                return data.Atom(value)
            case data.ConsCell(head, tail):
                if tail is None:
                    if head is None:
                        return data.Atom("nil")
                    if dbg:
                        print(f"XXX Got {type(head)}: {head}")
                    return head
                return res[0]
            case _:
                return result_to_list(res)

    return result_to_list(res)

    # if data.listp(res):
    #     return result_to_list(res)

    # if len(res) == 1:
    #     if dbg:
    #         print(f"{res[0].__class__}: {res[0]}")
    #     return data.Atom(res[0])

    # if isinstance(res, (str, data.ConsCell, data.Atom)):
    #     if dbg:
    #         print(f"Return a single value: {res}")
    #     return res
    # if len(res) == 0:
    #     # raise IncompleteException("Incomplete expression!")
    #     return data.Atom('nil')

    # if dbg:
    #     print(res.__class__, "(", len(res), ") ->", res)

    # try:
    #     # return result_to_list(res if len(res) > 1 else res[0])
    #     if len(res) <= 1:
    #         return data.Atom(res[0])
    #     return result_to_list(res)
    # except TypeError as terr:
    #     print("TypeError:", terr)
    #     return result_to_list(res) if len(res) > 1 else res[0]


# Local Variables: #
# python-indent: 4 #
# End: #
