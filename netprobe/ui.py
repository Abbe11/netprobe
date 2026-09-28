"""Tiny terminal-colour helpers, shared by every command.

Older Windows consoles print raw escape codes (like the ←[36m you saw)
instead of colours. On Windows 10+ we switch on "virtual terminal" mode;
if that fails, or output isn't a real terminal, we silently drop colours
so the text always stays clean.
"""
from __future__ import annotations

import os
import sys


def _enable_windows_ansi() -> bool:
    if os.name != "nt":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)          # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        return bool(
            kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        )
    except Exception:
        return False


_COLOR_OK = None


def color_enabled() -> bool:
    global _COLOR_OK
    if _COLOR_OK is None:
        if os.environ.get("NO_COLOR") is not None or not sys.stdout.isatty():
            _COLOR_OK = False
        else:
            _COLOR_OK = _enable_windows_ansi()
    return _COLOR_OK


def _c(text, code):
    return f"\033[{code}m{text}\033[0m" if color_enabled() else text


def bold(t):
    return _c(t, "1")


def cyan(t):
    return _c(t, "36")


def yellow(t):
    return _c(t, "33")


def green(t):
    return _c(t, "32")


def red(t):
    return _c(t, "31")


def rule():
    print(cyan("─" * 60))
