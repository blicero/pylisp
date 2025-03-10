#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-03-10 19:33:46 krylon>
#
# /data/code/python/krylisp/lisp.py
# created on 20. 05. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
krylisp.lisp

(c) 2024 Benjamin Walkenhorst
"""

import logging
import math
import operator
import sys
import time
import traceback
from functools import reduce
from typing import Any, Final, Optional, Union

from krylib import even

from krylisp import common, data, error, parser

# Donnerstag, 07. 10. 2010, 22:03
# Damit ich richtige Makros schreiben kann, brauche ich gensym, und damit DAS
# funktioniert, muss ich irgendwie State haben, der über das normale
# Environment hinaus geht.
# DAS wiederum heißt, ich werde wohl - nach einem missglückten Anlauf - zu
# einem objektorientierten Ansatz zurück kehren.


def get_num(v: Any) -> Union[int, float]:
    """Atempt to get the numeric value of its argument."""
    if isinstance(v, (int, float)):
        return v
    raise error.LispError(f"{v} is not a numerical value!")


class LispInterpreter:
    """LispInterpreter interprets Lisp code."""

    __slots__ = ['debug', 'gensym_counter', 'env', 'log']

    debug: bool
    gensym_counter: int
    env: data.Environment
    log: logging.Logger

    def __init__(self, env=None, counter=0) -> None:
        assert env is None or isinstance(env, data.Environment)
        self.debug = False
        self.env = data.Environment() if env is None else env
        self.gensym_counter = counter
        self.log = common.get_logger(f"{self.__class__}")

    def dbg(self, *args):
        """Print a debug message if the debug flag is set."""
        self.log.debug(args[0], *args[1:])

    def warn(self, *args):
        """Print a warning."""
        self.log.warning(args[0], *args[1:])

    def eval_atom(self, atom, env=None) -> Optional[Union[data.Symbol, str, int, float, data.ConsCell]]:
        """Evaluate an Atom."""
        assert atom is not None, "Atom must not be None."

        if env is None:
            env = self.env

        self.dbg("Evaluating %s %s", atom.__class__, atom)

        match atom:
            case None:
                return data.Symbol("nil")
            case data.Symbol(value):
                if atom.is_keyword():
                    return atom
                if atom.value.upper() == "nil":
                    return data.EMPTY_LIST
                if atom.value.upper() == "T":
                    return data.Symbol("t")
                return env[value.upper()]
            case x if isinstance(x, (str, int, float)):
                return x
            case _:
                raise TypeError(f"Did not expect {atom.__class__}")

    # Ich muss mir noch überlegen, wie viel von der Sprache ich fest in den
    # Interpreter einbauen bzw. auf der reinen Lisp-Ebene implementieren will.
    # Aus Performance-Gründen wäre es wohl sinnvoller, so viel wie möglich in Python
    # zu machen.
    #
    # Freitag, 01. 10. 2010, 18:54
    # Ich würde als nächstes gern loops implementieren, aber damit das funktioniert,
    # müsste ich erst ein return-Statement implementieren. WENN mir das gelingt,
    # kann ich auch z.B. eine Common Lisp-style do-Schleife als Makro
    # implementieren, aber ... äh, return wird kompliziert.
    # return müsste dann ja auch bei Funktionen funktionieren... ;-? Das wird
    # haarig...
    #
    # Freitag, 01. 10. 2010, 19:43
    # Bevor ich mich um iteratives Gedöns kümmern kann, muss ich noch mal über
    # Makros nachdenken.
    #
    # Freitag, 08. 10. 2010, 01:36
    # Ich glaube, ich muss progn als special form implementieren!!!
    def eval_list(self, lst, env=None) -> Union[data.Symbol, data.ConsCell, data.Function, int, float, str]:  # pylint: disable-msg=R0911,R0912 # noqa: E501
        """Evaluate a list."""
        assert env is None or isinstance(env, data.Environment)
        self.dbg("Evaluating list %s", lst)

        if env is None:
            env = self.env

        if data.nullp(lst):
            return data.EMPTY_LIST

        if isinstance(lst, data.ConsCell):
            if lst.car() == '+':
                return sum(self.eval_expr(x, env) for x in lst.cdr())
            if lst.car() == '-':
                lst = lst.cdr()
                res = self.eval_expr(lst.car(), env)
                for val in lst.cdr():
                    res -= self.eval_expr(val, env)
                return res
            if lst.car() == '*':
                return reduce(operator.mul, [self.eval_expr(x, env) for x in lst.cdr()])
            if lst.car() == '**':
                return self.eval_expr(lst[1], env) ** self.eval_expr(lst[2], env)
            if lst.car() == '/':
                return reduce(operator.truediv, [self.eval_expr(x, env) for x in lst.cdr()])
            if lst.car() == 'mod':
                return self.eval_expr(lst[1], env) % self.eval_expr(lst[2], env)
            if lst.car() == 'sqrt':
                num_value = get_num(self.eval_expr(lst[1], env))
                return math.sqrt(num_value)
            if lst.car() == '<':
                lst = lst.cdr()
                while not data.nullp(lst.cdr()):
                    if self.eval_expr(lst.car(), env) >= self.eval_expr(data.cadr(lst), env):
                        return data.ConsCell(None, None)
                    lst = lst.cdr()
                return data.Symbol('t')
            if lst.car() == '>':
                lst = lst.cdr()
                while not data.nullp(lst.cdr()):
                    if self.eval_expr(lst.car(), env) <= self.eval_expr(data.cadr(lst), env):
                        return data.ConsCell(None, None)
                    lst = lst.cdr()
                return data.Symbol('t')
            if lst.car() == '=':
                lst = lst.cdr()
                while not data.nullp(lst.cdr()):
                    if self.eval_expr(lst.car(), env) != self.eval_expr(data.cadr(lst), env):
                        return data.ConsCell(None, None)
                    lst = lst.cdr()
                return data.Symbol('t')
            if lst.car() == 'eq':
                if self.eval_expr(lst[1], env) == self.eval_expr(lst[2], env):
                    return data.Symbol('t')
                return data.Symbol('nil')
            if lst.car() == 'if':
                if len(lst) != 4:
                    raise error.LispError(
                        "'if' needs exactly three parameters: condition, then-part, else-part!")

                self.dbg("Evaluating condition of if-expression.")
                cond = not data.nullp(self.eval_expr(lst[1], env))
                self.dbg("--> %s", cond)
                if cond:
                    self.dbg("if-condition is true.")
                    return self.eval_expr(lst[2], env)
                self.dbg("if-condition is false.")
                return self.eval_expr(lst[3], env)
            if lst.car() == 'return':
                assert len(lst) == 2
                return self.eval_expr(lst[1], env)
            if lst.car() == 'print':
                assert len(lst) == 2
                val = self.eval_expr(lst[1], env)
                print(val)
                return val
            # and und or sollte ich vielleicht besser mit einer for-Schleife implementieren...
            if lst.car() == 'and':
                val = data.EMPTY_LIST
                for expr in lst.cdr():
                    val = self.eval_expr(expr, env)
                    if data.nullp(val):
                        return data.EMPTY_LIST
                return val
            if lst.car() == 'or':
                val = data.EMPTY_LIST
                for expr in lst.cdr():
                    val = self.eval_expr(expr, env)
                    if not data.nullp(val):
                        return val
                return data.EMPTY_LIST
            if lst.car() == 'not':
                return data.Symbol('nil') \
                    if not data.nullp(self.eval_expr(lst[1], env)) \
                    else data.Symbol('t')
            if lst.car() == 'quote':
                return lst[1]
            if lst.car() in ('quit', 'exit'):
                sys.exit(0)
            if lst.car() == 'cons':
                # (cons 1 ()) ergibt im Moment (1 None)!!!
                arg1 = self.eval_expr(lst[1], env)
                arg2 = self.eval_expr(lst[2], env)
                if not data.nullp(arg2):
                    return data.cons(arg1, arg2)
                return data.ConsCell(arg1, None)
            if lst.car() == 'car':
                arg = self.eval_expr(lst[1], env)
                if not data.listp(arg):
                    raise error.LispError("Argument to car must be a list!")
                if data.nullp(arg):
                    return data.ConsCell(None, None)
                return arg[0]
            if lst.car() == 'cdr':
                arg = self.eval_expr(lst[1], env)
                if not data.listp(arg):
                    raise error.LispError("Argument to cdr must be a list!")
                if data.nullp(arg):
                    return data.ConsCell(None, None)
                return arg.cdr()
            if lst.car() == 'listp':
                return data.Symbol('t') if data.listp(self.eval_expr(lst[1], env)) \
                    else data.Symbol('nil')
            if lst.car() == 'null':
                return data.Symbol('t') if data.nullp(self.eval_expr(lst[1], env)) \
                    else data.Symbol('nil')
            if lst.car() == 'list':
                return data.ConsCell.fromList([self.eval_expr(x, env) for x in lst.cdr()])
            if lst.car() == 'atom':
                arg = self.eval_expr(lst[1], env)
                if isinstance(arg, (data.Symbol, int, float)) or data.nullp(arg):
                    return data.Symbol('t')
                return data.Symbol('nil')
            if lst.car() == 'lambda':
                return lst
            if lst.car() == 'defun':
                assert len(lst.cdr()) >= 3, \
                    "A Function definition needs at least three arguments (name, arglist, body)"
                lst = lst.cdr()
                env.get_global()[lst[0]] = data.ConsCell(data.Symbol("lambda"), lst.cdr())
                return lst[0]
            if lst.car() == 'defmacro':
                assert len(lst.cdr()) >= 3, \
                    "A Macro definition needs at least three arguments (name, arglist, body)"
                macro = lst.cdr()
                env.get_global()[macro[0]] = data.ConsCell(data.Symbol('macro'), macro.cdr())
                # warn("Macros are not implemented yet!")
                return macro[0]
            if lst.car() == 'backquote':
                return self.eval_backquote(lst, env)
            if lst.car() == 'gensym':
                self.gensym_counter += 1
                return f"#:{self.gensym_counter:-012d}"
            if lst.car() == 'let':
                let_env = {}
                for symbol, value in lst[1]:
                    assert isinstance(symbol, (data.Symbol, str)), \
                        "A let-variable must be a symbol!"
                    let_env[symbol] = self.eval_expr(value, env)
                lenv = data.Environment(env, let_env)
                res = data.NIL
                for expr in lst.cdr().cdr():
                    res = self.eval_expr(expr, lenv)
                return res
            if lst.car() == 'setq':
                assert even(len(lst.cdr())), \
                    "The parameters to setq must be a list of symbols and values."
                lst = lst.cdr()
                val = None
                while not data.nullp(lst):
                    sym = lst.car()
                    lst = lst.cdr()
                    val = lst.car()
                    lst = lst.cdr()
                    if not isinstance(sym, data.Symbol):
                        raise error.LispError(f"{sym} is not a symbol!")
                    env[sym] = self.eval_expr(val, env)
                return val
            if lst.car() == 'apply':
                assert len(lst) == 3, "Apply takes exactly two arguments (function and arglist)!"
                # Wenn lst[2] eine Liste ist, darf ich lst[1] nicht einfach davor consen... ;-/
                return self.eval_expr(data.cons(lst[1], self.eval_expr(lst[2], env)), env)
            if lst.car() == 'do':
                if len(lst) < 3:
                    raise error.LispError(
                        "do needs at least two arguments (init-list and end-list)!")
                var_dict = {}
                update_forms = {}
                body = lst.cdr().cdr().cdr()

                self.dbg("Evaluating do-loop: %s", lst)

                end_expr = lst[2][0]
                result_expr = lst[2][1]

                if not data.nullp(lst[1]):
                    for var_def in lst[1]:
                        sym = var_def[0]
                        init_val = var_def[1]
                        update = var_def[2]

                        if isinstance(sym, data.Symbol):
                            sym = sym.value

                        var_dict[sym] = self.eval_expr(init_val, env)
                        update_forms[sym] = update

                loop_env = data.Environment(env, var_dict)

                while data.nullp(self.eval_expr(end_expr, loop_env)):
                    for expr in body:
                        self.eval_expr(expr, loop_env)
                    for sym, expr in update_forms.items():
                        loop_env[sym] = self.eval_expr(expr, loop_env)

                return self.eval_expr(result_expr, loop_env)
            if lst.car() == 'eval':
                return self.eval_expr(lst[2], env)
            if lst.car() == 'time':
                before: Final[float] = time.time()
                res = self.eval_expr(lst[1], env)
                after: Final[float] = time.time()
                delta: Final[float] = after - before
                print(f"Evaluating {lst[1]} took {delta} seconds.")
                return res
            if lst.car() == 'load':
                path = lst[1]
                return load_file(path, env)
            if lst.car() == 'dbg':
                arg = self.eval_expr(lst[1], env)
                self.dbg("Setting debug flag to %s", arg)
                self.debug = not data.nullp(arg)
                return data.Symbol('t') if self.debug else data.Symbol('nil')

            # Ich habe so die Idee, dass ich eine Kombination aus den
            # Konventionen für Common Lisp und Scheme verwende:
            # Das erste Element wird genau so interpretiert wie alle anderen
            # Elemente in der Liste, ABER alle Parameter werden von links
            # nach rechts ausgewertet.
            # Dafür brauche ich eigentlich so etwas wie map, nur dass eine
            # verkettete Liste anstelle einer normalen Python-Liste zurück
            # kommen muss.
            # Das könnte ich natürlich erstmal faken...
            # Mmmh, damit Makros richtig funktionieren, darf ich nicht alle
            # Argumente evaluieren, bevor dingsen...
            op = self.eval_expr(lst[0], env)
            if not (isinstance(op, data.ConsCell) and isinstance(op[0], data.Symbol)):
                return lst
            if op[0] == 'lambda':
                arg_list = data.ConsCell.fromList(
                    [self.eval_expr(x, env) for x in lst.cdr()]) \
                    if not data.nullp(lst.cdr()) \
                    else data.ConsCell(None, None)
                # Okay, arg_list ist also die Liste der formalen Parameter.
                formal_args = op[1]
                arg_dict = {}
                # Ich müsste hier irgendwie mit &rest-Argumenten zurecht kommen...
                # Dafür müsste ich aber meine Schleife anders gestalten...
                # for arg_name, arg_val in map(lambda x,y: (x,y), formal_args, arg_list):
                #     #if arg_name == '&rest':
                #     arg_dict[arg_name] = eval_expr(arg_val, env)
                while not (data.nullp(formal_args) or data.nullp(arg_list)):
                    arg_name = formal_args.car()
                    if arg_name == '&rest':
                        arg_dict[formal_args[1]] = arg_list
                        formal_args = None
                        break
                    arg_dict[arg_name] = arg_list.car()
                    arg_list = arg_list.cdr()
                    formal_args = formal_args.cdr()

                # Dann muss ich jetzt das neue Environment aus den Parametern
                # erzeugen und dann den Funktionskörper auswerten...
                funcall_env = data.Environment(env, arg_dict)
                if not data.nullp(formal_args):
                    raise error.LispError(
                        "arg list is shorter than the list of formal arguments!")
                self.dbg("Function call environment is %s", funcall_env)
                self.dbg("Local environment for function call: %s", funcall_env.data)
                res = None
                for expr in op.cdr().cdr():
                    res = self.eval_expr(expr, funcall_env)
                    self.dbg("Sub-expression %s evaluates to %s", expr, res)
                    if isinstance(expr, data.ConsCell) and expr[0] == 'return':
                        break
                return res
            if op[0] == 'macro':
                # Hier muss ich zwei Mal evaluieren, einmal, um das Macro zu
                # expandieren, und einmal, um den resultierenden Code zu
                # evaluieren. Mmmmh...
                expand_dict = {}
                formal_args = op[1]
                arg_list = lst.cdr()
                while not data.nullp(formal_args):
                    arg_name = formal_args.car()
                    if arg_name in ('&rest', '&body'):
                        expand_dict[formal_args[1]] = arg_list
                        break
                    expand_dict[arg_name] = arg_list.car()
                    arg_list = arg_list.cdr()
                    formal_args = formal_args.cdr()
                macro_env = data.Environment(env, expand_dict)
                res = []

                # Jaaaa, hier muss ich wieder darauf auchten, dass die
                # evaluierten Ausdrücke vermutlich Listen sind, und dass ich
                # die nicht ohne weiteres an einander consen kann...
                # for stmt in reversed(op.cdr().cdr()):
                #     res = data.ConsCell(eval_macro_expr(stmt, macro_env), res)
                for subexpr in op.cdr().cdr():
                    res.append(self.eval_macro_expr(subexpr, macro_env))

                res = data.ConsCell.fromList(res) if len(res) != 1 else res[0]

                self.dbg("MMM Macro\n\t%s\nexpands to\n\t--> %s", op, res)

                # Wenn alles läuft, wie ich mir das vorstelle, ist res an
                # dieser Stelle das expandierte Makro. Dann müsste ich den
                # makro-expandierten Code jetzt evaluieren. God damn, das sollte
                # wirklich im Parser statt finden, oder ich müsste Reader und
                # Evaluator eleganter verknüpfen.
                # raise error.LispError, "Macros are not implemented, yet."
                return self.eval_expr(res, env)
            return lst

        raise error.LispError(f"List is neither nil nor a Lisp List: {lst}")

    def eval_expr(self, expr, env=None):
        """Evaluate an expression of arbitrary kind or complexity."""
        assert env is None or isinstance(env, data.Environment)

        if env is None:
            env = self.env

        match expr:
            case None:
                return data.EMPTY_LIST
            case data.Symbol(_):
                return self.eval_atom(expr)
            case data.ConsCell(_, _):
                return self.eval_list(expr)
            case _:
                if isinstance(expr, (int, float, str)):
                    return expr
                raise TypeError(f"Unexpected type {expr.__class__}")

    def eval_macro_expr(self, expr, env=None):
        """Evaluate a macro expression."""
        assert env is None or isinstance(env, data.Environment)

        if env is None:
            env = self.env

        self.dbg("Evaluating macro: %s", expr)
        res = None
        if isinstance(expr, data.ConsCell):
            # Hier muss ich eine Reihe von Spezialfällen berücksichtigen, die im
            # Moment der Parser für mich erkennen und kenntlich machen sollte:
            # Wenn das erste Atom der Liste back-quote, comma-at oder comma ist, muss ich
            # das entsprechend behandeln.
            if expr.car() == 'backquote':
                res = self.eval_backquote(expr[1], env)
            elif expr.car() == 'quote':
                res = expr[1]
            else:
                res = self.eval_expr(expr, env)
        else:
            res = self.eval_expr(expr, env)

        self.dbg("Evaluated macro %s --> %s", expr, res)
        return res

    def eval_backquote(self, expr, env=None):
        """Evaluate a backquote expression."""
        assert env is None or isinstance(env, data.Environment)

        if env is None:
            env = self.env

        self.dbg("Evaluating back-quoted expression %s", expr)

        if isinstance(expr, data.ConsCell):  # pylint: disable-msg=R1702
            exlst = []
            for subexpr in expr:
                self.dbg("Evaluating back-quoted sub-expression: %s", subexpr)
                # Hier muss ich jetzt anhand des Typs und der Gestalt dispatchen...
                if isinstance(subexpr, data.ConsCell):
                    if subexpr.car() == 'backquote':
                        exlst.append(self.eval_backquote(subexpr, env))
                    elif subexpr.car() == 'comma-at':
                        # Hier muss ich besonders vorsichtig sein:
                        # Wenn das zweite Argument ein Atom ist, muss ich das aus
                        # dem Environment auflösen. Wenn das eine Liste ist, wird
                        # das offenbar in Common Lisp - zumindest in CLisp  -
                        # normal aufgelöst.
                        res = None
                        if isinstance(subexpr[1], data.Symbol):
                            res = self.eval_atom(subexpr[1], env)
                        elif isinstance(subexpr[1], data.ConsCell):
                            res = self.eval_list(subexpr[1], env)

                        if data.is_atomic(res):
                            exlst.append(self.eval_atom(res, env) if res in env else res)
                        elif isinstance(res, data.ConsCell):
                            for item in res:
                                exlst.append(item)
                    elif subexpr.car() == 'comma':
                        assert len(subexpr) == 2, "A comma un-quotes a single item"
                        exlst.append(self.eval_expr(subexpr[1], env))
                    else:
                        exlst.append(self.eval_backquote(subexpr, env))
                else:
                    exlst.append(subexpr)

            # if len(exlst) == 1 and isinstance(exlst[0], data.ConsCell):
            #     return exlst[0]
            # else:
            #     return data.ConsCell.fromList(exlst)
            return data.ConsCell.fromList(exlst)
        if data.is_atomic(expr):
            return expr
        raise error.LispError(
            f"Invalid type for backquote expression: {expr.__class__} - {expr}")


def load_file(self, path, env=None) -> Any:
    """Load a source file."""
    assert env is None or isinstance(env, data.Environment)

    if env is None:
        env = self.env

    res = None
    try:
        with open(path, 'r', encoding="utf-8") as fh:
            expr = ""
            complete = False
            for line in fh:
                if complete:
                    complete = False
                    expr = line
                else:
                    expr += line
                try:
                    form = parser.parse_string(expr)
                except parser.IncompleteException:
                    pass
                else:
                    complete = True
                    res = self.eval_expr(form, env)
    except IOError as ioerror:
        msg: Final[str] = "\n".join(traceback.format_exception(ioerror))
        print(f"Error reading {path}: {msg}")
    return res


# Local Variables: #
# python-indent: 4 #
# End: #
