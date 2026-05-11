"""Utility functions for the Pytigon GUI library.

Includes color manipulation helpers, desktop shortcut creation,
focus tracking, and plugin import functionality.
"""

import os
import sys
import logging

import importlib
import wx
import pytigon

from pytigon_lib.schtools.main_paths import get_main_paths

try:
    from pyshortcuts import make_shortcut
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
    return wx.Colour(colour.Red(), colour.Green(), colour.Blue()).GetAsString(
        wx.C2S_HTML_SYNTAX
    )


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


def create_desktop_shortcut(app_name, title=None, parameters=""):
    """Create a desktop shortcut for launching a Pytigon application.

    Args:
        app_name: Application/project name.
        title: Shortcut display name (defaults to app_name).
        parameters: Additional command-line parameters.
    """
    pytigon_init_path = os.path.abspath(pytigon.__file__)
    ico_path = pytigon_init_path.replace("__init__.py", "pytigon.ico")
    ptig_path = pytigon_init_path.replace("__init__.py", "ptig.py")

    if "python" in sys.executable and make_shortcut:
        make_shortcut(
            ptig_path + " " + app_name,
            name=title if title else app_name,
            icon=ico_path,
        )


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
            LAST_FOCUS_CTRL_IN_FORM = win_focus
            return win_focus
        win = win.GetParent()

    if LAST_FOCUS_CTRL_IN_FORM and (
        not hasattr(LAST_FOCUS_CTRL_IN_FORM, "parent")
        or not LAST_FOCUS_CTRL_IN_FORM.parent
        or (
            hasattr(LAST_FOCUS_CTRL_IN_FORM.parent, "closing")
            and LAST_FOCUS_CTRL_IN_FORM.parent.closing
        )
    ):
        LAST_FOCUS_CTRL_IN_FORM = None
        return None

    return LAST_FOCUS_CTRL_IN_FORM


def import_plugin(plugin_name, prj_name=None):
    """Import a plugin module by name, searching standard plugin paths.

    Lookup order depends on whether *prj_name* is given:
      - With project: prj_cfg, then prj_cfg_alt.
      - Without project: pytigon_cfg, then data_cfg.

    Args:
        plugin_name: Dotted module name (e.g. 'plugins.myplugin').
        prj_name: Optional project name for project-specific plugins.

    Returns:
        The imported module, or None if not found or import failed.
    """
    cfg = get_main_paths()
    pytigon_cfg = [cfg["PYTIGON_PATH"], "appdata", "plugins"]
    data_cfg = [cfg["DATA_PATH"], "plugins"]
    prj_cfg = [cfg["PRJ_PATH"], prj_name, "applib"]
    prj_cfg_alt = [cfg["PRJ_PATH_ALT"], prj_name, "applib"]

    if prj_name:
        folders = [prj_cfg, prj_cfg_alt]
    else:
        folders = [pytigon_cfg, data_cfg]

    path = None
    for folder in folders:
        plugins_path = os.path.join(folder[0], *folder[1:])
        if prj_name:
            plugin_path = os.path.join(plugins_path, *plugin_name.split(".")[:-1])
        else:
            plugin_path = os.path.join(plugins_path, *plugin_name.split("."))
        if os.path.exists(plugin_path):
            path = plugins_path
            break

    if not path:
        logger.warning("Plugin path not found: %s", plugin_name)
        return None

    try:
        return importlib.import_module(plugin_name, package=None)
    except ImportError as e:
        logger.error("Failed to import plugin '%s': %s", plugin_name, e)
        return None
