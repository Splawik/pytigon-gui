"""Thread-safety helpers for marshalling GUI calls to the wx main thread.

wxPython widgets must only be created, modified or destroyed from the
thread that runs the main event loop. Callbacks delivered by background
threads (Twisted reactor, HTTP workers, external plugins) have to be
forwarded to the main thread with :func:`wx.CallAfter`.

The helpers below centralise the "is this still safe to touch" logic so
that deferred callbacks do not operate on windows that have already been
destroyed.
"""

import logging
from contextlib import contextmanager

import wx

logger = logging.getLogger(__name__)


def is_main_thread():
    """Return True when called from the wx GUI thread."""
    return wx.IsMainThread()


def is_alive(win):
    """Return True if *win* is a live wx object.

    ``None`` and C++ objects that have already been deleted evaluate to
    False. wxPython defines ``__bool__`` on wx.Window for exactly this
    check. Accessing a deleted object raises ``RuntimeError`` on some
    platforms, so it is converted to False as well.
    """
    if win is None:
        return False
    try:
        return bool(win)
    except RuntimeError:
        return False


def run_in_main_thread(fun, *args, **kwargs):
    """Run *fun* on the main thread.

    When already on the main thread, *fun* is called immediately and its
    return value is propagated. Otherwise it is deferred with
    :func:`wx.CallAfter` and ``None`` is returned (the call becomes
    asynchronous).
    """
    if wx.IsMainThread():
        return fun(*args, **kwargs)
    wx.CallAfter(fun, *args, **kwargs)
    return None


def call_after_if_alive(win, fun, *args, **kwargs):
    """Defer *fun* to the main thread, skipping it if *win* is gone.

    The liveness of *win* is checked when the deferred callback actually
    runs, not when it is scheduled, so a window destroyed in the
    meantime cannot be touched.
    """

    def _runner():
        if is_alive(win):
            try:
                fun(*args, **kwargs)
            except RuntimeError:
                logger.debug(
                    "Skipped deferred call %s: target window destroyed",
                    getattr(fun, "__name__", fun),
                )

    wx.CallAfter(_runner)


@contextmanager
def block_http_pumping():
    """Stop :class:`HttpClient` from pumping the wx event loop.

    While active, synchronous HTTP requests made on the GUI thread block
    with ``join()`` instead of calling ``app.Yield()``. This must be used
    around code that runs during painting or while structural GUI changes
    are in progress, where re-entering the event loop can destroy objects
    that are still on the stack.

    The underlying flag lives in ``pytigon_lib``; it is a plain counter
    and is only ever modified from the GUI thread here.
    """
    from pytigon_lib.schhttptools import httpclient

    httpclient.IN_PAINT += 1
    try:
        yield
    finally:
        httpclient.IN_PAINT -= 1
