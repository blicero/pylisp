#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2025-03-08 16:00:14 krylon>
#
# /data/code/python/krylisp/common.py
# created on 17. 05. 2024
# (c) 2024 Benjamin Walkenhorst
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY BENJAMIN WALKENHORST ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

"""
Common

(c) 2024 Benjamin Walkenhorst
"""

import logging
import logging.handlers
import os
import queue
import sys

from threading import Lock
from typing import Final

APP_NAME: Final[str] = "kryLisp"
APP_VERSION: Final[str] = "0.0.1"
DEBUG: Final[bool] = True
TIME_FMT: Final[str] = "%Y-%m-%d %H:%M:%S"

log_format: Final[str] = "%(asctime)s (%(name)-16s / line %(lineno)-4d) " + \
    "- %(levelname)-8s %(message)s"


class Path:
    """Holds the paths of folders and files used by the application"""

    __base: str

    def __init__(self, root: str = os.path.expanduser(f"~/.{APP_NAME.lower()}.d")) -> None:  # noqa
        self.__base = root

    def base(self, folder: str = "") -> str:
        """
        Return the base directory for application specific files.

        If path is a non-empty string, set the base directory to its value.
        """
        if folder != "":
            self.__base = folder
        return self.__base

    def db(self) -> str:  # pylint: disable-msg=C0103
        """Return the path to the database"""
        return os.path.join(self.__base, f"{APP_NAME.lower()}.db")

    def log(self) -> str:
        """Return the path to the log file"""
        return os.path.join(self.__base, f"{APP_NAME.lower()}.log")

    def config(self) -> str:
        """Return the path of the configuration file"""
        return os.path.join(self.__base, f"{APP_NAME.lower()}.conf")

    def histfile(self) -> str:
        """Return the path of the history file for the REPL"""
        return os.path.join(self.__base, "repl.history")


path: Path = Path(os.path.expanduser(f"~/.{APP_NAME.lower()}.d"))

_lock: Final[Lock] = Lock()  # pylint: disable-msg=C0103
_cache: Final[dict[str, logging.Logger]] = {}  # pylint: disable-msg=C0103
log_queue: queue.SimpleQueue = queue.SimpleQueue()


def set_basedir(folder: str) -> None:
    """Set the base dir to the speficied path."""
    path.base(folder)
    init_app()


def init_app() -> None:
    """Initialize the application environment"""
    if not os.path.isdir(path.base()):
        print(f"Create base directory {path.base()}")
        os.mkdir(path.base())


def get_logger(name: str, terminal: bool = True) -> logging.Logger:
    """Create and return a logger with the given name"""
    with _lock:
        init_app()

        if name in _cache:
            return _cache[name]

        max_log_size = 100 * 2**10  # 100 KiB
        max_log_count = 4

        log_obj = logging.getLogger(name)
        log_obj.setLevel(logging.DEBUG)
        log_file_handler = logging.handlers.RotatingFileHandler(path.log(),
                                                                'a',
                                                                max_log_size,
                                                                max_log_count)

        log_fmt = logging.Formatter(log_format)
        log_file_handler.setFormatter(log_fmt)
        log_obj.addHandler(log_file_handler)

        # queue_handler = logging.handlers.QueueHandler(log_queue)
        # # queue_handler.setFormatter(log_fmt)
        # queue_handler.setLevel(logging.DEBUG)
        # log_obj.addHandler(queue_handler)

        if terminal:
            log_console_handler = logging.StreamHandler(sys.stdout)
            log_console_handler.setFormatter(log_fmt)
            log_console_handler.setLevel(logging.DEBUG)
            log_obj.addHandler(log_console_handler)

        _cache[name] = log_obj
        return log_obj


# Local Variables: #
# python-indent: 4 #
# End: #
