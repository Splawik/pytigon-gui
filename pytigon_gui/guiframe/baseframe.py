"""
Base frame class for Pytigon application windows.

Provides the core SchBaseFrame from which both SchAppFrame (desktop)
and SchBrowserFrame (webview) inherit.
"""

import os
import sys
import traceback
import logging

import wx

import pytigon_gui.guictrl.ctrl

logger = logging.getLogger(__name__)

from pytigon_gui.guilib.tools import import_plugin


class SchBaseFrame(wx.Frame):
    """
    Base main window for Pytigon applications.

    Handles plugin initialization and close event management.
    """

    def __init__(
        self,
        parent,
        gui_style="tree(toolbar,statusbar)",
        id=-1,
        title="",
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.WANTS_CHARS,
        name="MainWindow",
    ):
        """Initialize the base frame.

        Args:
            parent: Parent window (usually None for top-level).
            gui_style: Style string describing UI layout (e.g. "tree(toolbar,statusbar)").
            id: Window identifier.
            title: Window title.
            pos: Window position.
            size: Window size.
            style: wx.Frame style flags.
            name: Widget name.
        """
        wx.Frame.__init__(self, None, wx.ID_ANY, title, pos, size, style, "MainWindow")
        self.run_on_close = []
        self.destroy_fun_tab = []
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def init_plugins(self):
        """Discover and initialize application plugins.

        Searches for plugins in:
        1. Built-in pytigon appdata/plugins directory
        2. User data plugins directory
        3. Application-specific plugins directory

        Plugins in the 'auto' directory or listed in auto_plugins config
        are loaded automatically. Each plugin module may expose an
        ``init_plugin`` function that receives the application, frame,
        desktop notebook, frame manager, menu bar, toolbar interface,
        and accelerator table.
        """
        home_dir = wx.GetApp().get_working_dir()
        app_plugins = os.path.join(wx.GetApp().cwd, "plugins")
        dirnames = [
            os.path.join(wx.GetApp().pytigon_path, "appdata", "plugins"),
            os.path.join(wx.GetApp().data_path, "plugins"),
            app_plugins,
        ]

        auto_plugins = []
        try:
            auto_plugins = (
                wx.GetApp().config["Global settings"].get("auto_plugins", "").split(";")
            )
        except (KeyError, AttributeError):
            pass

        for dirname in dirnames:
            if not os.path.exists(dirname):
                continue

            for ff in sorted(os.listdir(dirname)):
                dirname2 = os.path.join(dirname, ff)
                if not os.path.isdir(dirname2):
                    continue

                files = sorted(os.listdir(dirname2))

                for f in files:
                    if not os.path.isdir(os.path.join(dirname2, f)):
                        continue

                    mod_name = ff + "." + f
                    # Skip internal modules
                    if ".__" in mod_name:
                        break

                    x = mod_name.replace(".", "/")
                    if not (
                        ff == "auto"
                        or (wx.GetApp().plugins and x in wx.GetApp().plugins)
                        or x in auto_plugins
                    ):
                        continue

                    try:
                        mod = import_plugin(mod_name)
                    except Exception:
                        logger.exception("Error importing plugin: %s", mod_name)
                        continue

                    if not hasattr(mod, "init_plugin"):
                        continue

                    try:
                        destroy = mod.init_plugin(
                            wx.GetApp(),
                            self,
                            getattr(self, "desktop", None),
                            getattr(self, "_mgr", None),
                            self.get_menu_bar(),
                            getattr(self, "toolbar_interface", None),
                            getattr(self, "aTable", None),
                        )
                    except Exception:
                        logger.exception("Error initializing plugin: %s", mod_name)
                        continue

                    if destroy is not None:
                        self.destroy_fun_tab.append(destroy)

    def on_close(self, event):
        """Handle the window close event.

        Calls all registered close handlers in order, then allows
        the event to propagate.
        """
        for fun in self.run_on_close:
            try:
                fun(self)
            except Exception:
                traceback.print_exc()
        event.Skip()
