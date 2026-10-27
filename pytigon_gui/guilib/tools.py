"""Utility functions for the Pytigon GUI library.

Includes color manipulation helpers, desktop shortcut creation,
focus tracking, and plugin import functionality.
"""

import logging
import sys
import weakref
import importlib
import contextlib
from pathlib import Path
import os

import wx

import pytigon

try:
    from pyshortcuts import make_shortcut
    # from pyshortcuts.utils import get_desktop
except ImportError:
    make_shortcut = None

_ = wx.GetTranslation
logger = logging.getLogger(__name__)

SIZE_DEFAULT = -1
SIZE_SMALL = 0
SIZE_MEDIUM = 1
SIZE_LARGE = 2


def norm_colour2(c):
    """Clamp a single color channel value to [0, 255].

    Args:
        c: Color channel value.

    Returns:
        int between 0 and 255.
    """
    x = int(c)
    return 255 if x > 255 else x


def norm_colour(r, g, b, proc):
    """Interpolate an RGB color toward white or black.

    When *proc* > 1, blends toward white (lightening).
    When *proc* < 1, blends toward black (darkening).

    Args:
        r: Red channel (0-255).
        g: Green channel (0-255).
        b: Blue channel (0-255).
        proc: Blend factor. 1.0 = no change, >1 = lighter, <1 = darker.

    Returns:
        [r, g, b] list with each channel clamped to 255.
    """
    if proc > 1:
        y = (255, 255, 255)
        dx = 2 - proc
    else:
        y = (0, 0, 0)
        dx = proc
    dy = 1 - dx
    ret = [
        int(r * dx + y[0] * dy),
        int(g * dx + y[1] * dy),
        int(b * dx + y[2] * dy),
    ]
    for i in range(3):
        if ret[i] > 255:
            ret[i] = 255
    return ret


def colour_to_html(colour):
    """Convert a wx.Colour to an HTML hex string (e.g. '#AABBCC').

    Args:
        colour: wx.Colour instance.

    Returns:
        HTML color string.
    """
    return wx.Colour(colour.Red(), colour.Green(), colour.Blue()).GetAsString(wx.C2S_HTML_SYNTAX)


def get_colour(wx_id, proc=None):
    """Get a system color as an HTML string, optionally blended.

    Args:
        wx_id: wx.SYS_COLOUR_* constant.
        proc: Optional blend factor for norm_colour.

    Returns:
        HTML color string.
    """
    c1 = wx.SystemSettings.GetColour(wx_id)
    if not proc:
        return colour_to_html(c1)
    x = norm_colour(c1.Red(), c1.Green(), c1.Blue(), proc)
    return colour_to_html(wx.Colour(x[0], x[1], x[2]))


def standard_tab_colour():
    """Return a tuple of (name, html_color) pairs for tab styling.

    These colors are derived from the system 3D face color at various
    blend levels, plus highlight, shadow, and info background colors.

    Returns:
        Tuple of (str, str) pairs mapping CSS variable names to HTML colors.
    """
    return (
        ("color_body_0_2", get_colour(wx.SYS_COLOUR_3DFACE, 0.2)),
        ("color_body_0_5", get_colour(wx.SYS_COLOUR_3DFACE, 0.5)),
        ("color_body_0_7", get_colour(wx.SYS_COLOUR_3DFACE, 0.7)),
        ("color_body_0_9", get_colour(wx.SYS_COLOUR_3DFACE, 0.9)),
        ("color_body", get_colour(wx.SYS_COLOUR_3DFACE)),
        ("color_body_1_1", get_colour(wx.SYS_COLOUR_3DFACE, 1.1)),
        ("color_body_1_3", get_colour(wx.SYS_COLOUR_3DFACE, 1.3)),
        ("color_body_1_5", get_colour(wx.SYS_COLOUR_3DFACE, 1.5)),
        ("color_body_1_8", get_colour(wx.SYS_COLOUR_3DFACE, 1.8)),
        ("color_higlight", get_colour(wx.SYS_COLOUR_3DHIGHLIGHT)),
        ("color_shadow", get_colour(wx.SYS_COLOUR_3DSHADOW)),
        ("color_background_0_5", get_colour(wx.SYS_COLOUR_3DFACE, 0.5)),
        ("color_background_0_8", get_colour(wx.SYS_COLOUR_3DFACE, 0.8)),
        ("color_background_0_9", get_colour(wx.SYS_COLOUR_3DFACE, 0.9)),
        ("color_background", get_colour(wx.SYS_COLOUR_3DFACE)),
        ("color_background_1_1", get_colour(wx.SYS_COLOUR_3DFACE, 1.1)),
        ("color_background_1_2", get_colour(wx.SYS_COLOUR_3DFACE, 1.2)),
        ("color_background_1_5", get_colour(wx.SYS_COLOUR_3DFACE, 1.5)),
        ("color_info", get_colour(wx.SYS_COLOUR_INFOBK, 1.5)),
    )


def create_desktop_shortcut(app_name, title=None, parameters="", desktop=True, startmenu=True):
    """Create a desktop shortcut for launching a Pytigon application.

    Args:
        app_name: Application/project name.
        title: Shortcut display name (defaults to app_name).
        parameters: Additional command-line parameters.
    """
    pytigon_init_path = Path(pytigon.__file__).resolve()
    ico_path = str(pytigon_init_path).replace("__init__.py", "pytigon.ico")
    ptig_path = str(pytigon_init_path).replace("__init__.py", "ptig.pyw")
    name = title if title else app_name

    if "python" in sys.executable and make_shortcut:
        make_shortcut(
            ptig_path + " " + app_name,
            executable=sys.executable
            if os.name == "posix"
            else sys.executable.replace("python.exe", "pythonw.exe"),
            name=name,
            icon=ico_path,
            terminal=False,
            desktop=desktop,
            startmenu=startmenu,
        )


# A weakref.ref to the last focused control, or None. A strong reference here
# transitively pinned the whole SchForm (ctrl.parent is the form), including
# its W*H*4 back buffer, whenever the frame exited without going through
# CanClose() - the invalidation below only fires when parent.closing is set,
# which happens solely in SchForm._on_close.
LAST_FOCUS_CTRL_IN_FORM = None


def find_focus_in_form():
    """Find the currently focused control that belongs to a SchForm.

    Walks up the window hierarchy from the current focus to locate a
    SchForm parent. Caches the last known focused control and invalidates
    it if the parent form is closing.

    Returns:
        The focused wx.Window inside a SchForm, or None.
    """
    global LAST_FOCUS_CTRL_IN_FORM

    win_focus = wx.Window.FindFocus()
    win = win_focus
    while win:
        if win.__class__.__name__ == "SchForm":
            LAST_FOCUS_CTRL_IN_FORM = weakref.ref(win_focus)
            return win_focus
        win = win.GetParent()

    ctrl = LAST_FOCUS_CTRL_IN_FORM() if LAST_FOCUS_CTRL_IN_FORM else None
    if ctrl is not None and (
        not hasattr(ctrl, "parent")
        or not ctrl.parent
        or (hasattr(ctrl.parent, "closing") and ctrl.parent.closing)
    ):
        LAST_FOCUS_CTRL_IN_FORM = None
        return None

    return ctrl


@contextlib.contextmanager
def force_base_path(path):
    # Insert the path at the very beginning for the highest priority
    tmp = sys.path
    sys.path = [
        path,
    ]
    try:
        yield
    finally:
        # Remove the path after the 'with' block to keep sys.path clean
        # if path in sys.path:
        #    sys.path.remove(path)
        sys.path = tmp
