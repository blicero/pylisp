#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-03-11 20:14:02 krylon>
#
# /data/code/python/krylisp/data.py
# created on 17. 05. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
krylisp.data

(c) 2024 Benjamin Walkenhorst
"""

import copy
import re
from collections import deque
from typing import Any, Final, Generator, Optional, Union

from krylisp import error

whitespace: Final[re.Pattern] = re.compile(r"\s+")
blank: Final[re.Pattern] = re.compile(r"^\s*$")
int_re: Final[re.Pattern] = re.compile(r"^-?\d+$")
float_re: Final[re.Pattern] = re.compile(r"^-?\d+(?:[.]\d+)(?:e-?\d+)?$")


def qw(s: str) -> list[str]:
    """Split a string by whitespace"""
    if blank.match(s) is not None:
        return []
    return whitespace.split(s)


def listp(x: Any) -> bool:
    """Return True if x is a Lisp list"""
    match x:
        case None:
            return True
        case ConsCell(_, _):
            return True
        case Symbol("nil"):
            return True
        case _:
            return False


def is_atomic(x: Any) -> bool:
    """Return True if x is an atomic value."""
    return isinstance(x, (int, str, float, Symbol))


class Function:
    """A Function is a callable code object"""

    def __init__(self, args, body, environment) -> None:
        assert isinstance(environment, (dict, Environment))
        assert isinstance(args, (list, tuple, ConsCell))
        assert isinstance(body, ConsCell)

        self.env = environment
        self.args = args
        self.body = body

    # Eigentlich muss ich noch dingsen...
    def __call__(self, *args):
        """Call the function with the given arguments"""


class Symbol:
    """Symbol symbolizes a symbolic token"""

    __slots__ = ["value"]
    __match_args__ = ("value", )

    value: str

    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:
        return self.value.upper()

    def __str__(self) -> str:
        return self.value.upper()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Symbol):
            return False
        return self.value.upper() == other.value.upper()

    def __hash__(self):
        return hash(f"Symbol({self.value.upper()})")

    def is_keyword(self) -> bool:
        """Return True if self is a keyword symbol (i.e. begins with a colon)"""
        return self.value[0] == ':'


# Ich muss mur noch einmal Gedanken über die Darstellung von nil machen... ;-/
# Eine ConsCell mit den Membern None und None wäre die naheliegende Lösung,
# aber wie stelle ich dann eine Liste mit einer leeren Liste als Element dar?
class ConsCell:
    """ConsCells are the backbone of Lisp, so to speak."""

    __slots__ = ['head', 'tail']

    head: Union[None, Symbol, int, float, str, Function, 'ConsCell']
    tail: Optional['ConsCell']

    __match_args__ = ('car', 'cdr')

    def __init__(self,
                 car: Union[None, Symbol, Function, int, float, str, 'ConsCell'],
                 cdr: Optional['ConsCell']) -> None:
        self.head = car
        self.tail = cdr

    def __len__(self) -> int:
        cnt: int = 1
        node: ConsCell = self
        while node.tail is not None:
            cnt += 1
            if node.tail is not None:
                node = node.tail
            else:
                break

        return cnt

    def __iter__(self) -> Generator:
        x: Optional['ConsCell'] = self
        while x is not None:
            if isinstance(x, ConsCell):
                yield x.head
                x = x.tail
            else:
                yield x
                break

    def __nonzero__(self) -> bool:
        return (self.head is not None) or (self.tail is not None)

    def __str__(self) -> str:
        if bool(self):
            return "(" + " ".join([str(x) for x in self]) + ")"
        return "()"

    def __repr__(self) -> str:
        if bool(self):
            return "(" + " ".join([str(x) for x in self]) + ")"
        return "()"

    def __getitem__(self, key):
        assert isinstance(key, int)
        assert key >= 0
        node = self
        while key > 0 and node.tail is not None:
            node = node.tail
            key -= 1
        # return ConsCell(None, None) if key > 0 else l.head
        if key == 0:
            return node.head
        raise error.LispError(f"Index {key} is out of range (list only has {len(self)} elements!")

    def __reversed__(self):
        rev = deque(self)
        try:
            while True:
                yield rev.pop()
        except IndexError:
            pass

    @staticmethod
    def fromList(lst) -> 'ConsCell':
        """Create a list that is a deep copy of the parameter"""
        assert isinstance(lst, (list, tuple, ConsCell)), \
            f"lst must be a list, not a {lst.__class__}"
        res = None
        for x in reversed(lst):
            item = None
            if isinstance(x, (list, tuple)):
                item = ConsCell.fromList(x)
            else:
                item = x
            res = cons(item, res)
        if res is None:
            return ConsCell(None, None)
        return res

    def car(self) -> Any:
        """Return the head of the list."""
        return self.head

    def cdr(self) -> 'ConsCell':
        """Return the tail of the list"""
        if self.tail is None:
            return ConsCell(None, None)
        return self.tail


# Streng genommen wäre NIL ja die leere Liste und nicht None, aber ... wenn ich
# das mache, verhält sich das ganze Ding auf einmal komisch...
NIL = Symbol("nil")
EMPTY_LIST: Final[ConsCell] = ConsCell(None, None)


def cons(a, b) -> ConsCell:
    """Cons to gether the arguments and return the result"""
    return ConsCell(a, b)


def cadr(x: ConsCell) -> Any:
    """Return the second element of the list."""
    assert listp(x) and isinstance(x.cdr(), ConsCell)
    return x.cdr().car()


def nullp(x: Any) -> bool:
    """Return True if x is nil"""
    match x:
        case None:
            return True
        case Symbol("nil"):
            return True
        case ConsCell(None, None):
            return True
        case _:
            return False


class Environment:
    """An Environment is a set of variable bindings that may reference other Environments."""

    __slots__ = ['data', 'parent', 'level']

    data: dict
    parent: Optional['Environment']
    level: int

    def __init__(self, parent: Optional['Environment'] = None, init: Optional[dict] = None) -> None:  # noqa: E501, pylint: disable-msg=C0301
        if init is None:
            init = {}
        assert (parent is None) or isinstance(parent, (dict, Environment))
        assert isinstance(init, dict)
        self.parent = parent
        self.data = {}
        for sym, val in init.items():
            self.data[sym.value if isinstance(sym, Symbol) else sym] = val
        self.level = 0 if (parent is None) else parent.level + 1

    def __getitem__(self, key: Union[str, Symbol]) -> Any:
        lookup_key = key
        if isinstance(key, Symbol):
            assert isinstance(key.value, str)
            lookup_key = key.value.upper()
        try:
            if lookup_key in self.data:
                return self.data[lookup_key]
            if isinstance(self.parent, dict):
                return self.parent[lookup_key]
            if isinstance(self.parent, Environment):
                return self.parent[lookup_key]
            raise error.BindingError(f"No such variable in environment: {lookup_key}")
        except KeyError as err:
            # Shouldn't I raise NoSuchVariableError?
            raise error.BindingError(f"No such variable in environment: {lookup_key}") from err

    # Dafür müsste ich erst nachsehen, welches das "top-most" environment ist,
    # in dem eine Variable mit dem angegebenen Namen existiert, und die dann
    # darin speichern...
    def __setitem__(self, key: Union[str, Symbol], value) -> None:
        assert isinstance(key, (Symbol, str))

        if isinstance(key, Symbol):
            assert isinstance(key.value, str)
            key = key.value

        key = key.upper()

        env: Environment = self
        while (env.parent is not None) and (key not in env.data):
            env = env.parent

        if key in env.data:
            env.data[key] = value
        else:
            self.data[key] = value

    def __contains__(self, key: str) -> bool:
        if key in self.data:
            return True

        parent: Optional[Environment] = self.parent
        while parent is not None:
            if key in parent:
                return True
            parent = parent.parent
        return False

    def __repr__(self) -> str:
        env = copy.copy(self.data)
        p = self.parent
        while p is not None:
            for key, val in p.data.items():
                if key not in env:
                    env[key] = val
            p = p.parent
        return str(env)

    def get_global(self) -> 'Environment':
        """Get the upmost enclosing Environment (i.e. the global environment)"""
        env = self
        while env.parent is not None:
            env = env.parent
        return env

    def get_depth(self) -> int:
        """Return the depth of nested Environments"""
        return self.level


# Local Variables: #
# python-indent: 4 #
# End: #
