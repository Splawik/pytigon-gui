"""
Browser-based main frame for Pytigon.

SchBrowserFrame embeds an HTML2 webview control as the main content
area instead of the standard AUI-managed desktop. It is used when the
application runs in a webview-embedded mode.
"""

import os
import sys
import time
import logging

import wx

import pytigon_gui.guictrl.ctrl

from pytigon_gui.guiframe.baseframe import SchBaseFrame

from django.conf import settings

from pytigon.pytigon_request import init, request
from pytigon_lib.schtools.env import get_environ

logger = logging.getLogger(__name__)

_ = wx.GetTranslation


class SchBrowserFrame(SchBaseFrame):
    """Main window for browser-embedded Pytigon applications.

    Uses an HTML2 webview control as the primary content area,
    loading the initial page directly from the embedded HTTP client.
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
        """Construct the browser frame.

        Args:
            parent: Parent window (usually None).
            gui_style: UI layout style string.
            id: Window identifier.
            title: Window title.
            pos: Initial position.
            size: Initial size.
            style: wx.Frame style flags.
            name: Widget name.
        """
        self.gui_style = gui_style
        self.destroy_fun_tab = []
        self.idle_objects = []
        self.after_init = False
        self.desktop = None
        self._mgr = None
        self.toolbar_interface = None
        self.aTable = None
        self.ctrl = None

        SchBaseFrame.__init__(
            self, parent, id, gui_style, title, pos, size, style | wx.WANTS_CHARS, name
        )
        wx.GetApp().SetTopWindow(self)

        self.init_plugins()
        self.Bind(wx.EVT_IDLE, self.on_idle)
        self.Bind(wx.EVT_SIZE, self.on_size)

        env = get_environ()
        username = env("AUTOUSERNAME")
        password = env("AUTOPASSWORD")

        init(os.environ["PRJ_NAME"], username, password, user_agent="webviewembeded")
        start_request = request("/", None, user_agent="webviewembeded")

        size = self.GetClientSize()
        if size.width < 0 or size.height < 0:
            size = wx.Size(1024, 768)
        self.ctrl = pytigon_gui.guictrl.ctrl.HTML2(self, name="schbrowser", size=size)
        self.ctrl.load_str(start_request.str(), "http://127.0.0.5/")

        if sys.platform != "win32":
            start = time.time()
            while not self.ctrl.page_loaded:
                if time.time() - start > 10:
                    logger.warning("Page load timed out")
                    break
                wx.Yield()

        size = wx.GetApp().app_size
        wx.CallAfter(self.SetSize, (size[0], size[1]))
        wx.CallAfter(self.Show)

    def on_size(self, event):
        if self.ctrl:
            if event:
                sz = event.GetSize()
                if sz.width > 0 and sz.height > 0:
                    self.ctrl.SetSize(sz)
                event.Skip()
            else:
                sz = self.GetSize()
                if sz.width > 0 and sz.height > 0:
                    self.ctrl.SetSize(sz)

    def get_menu_bar(self):
        """Return None; browser frames have no menu bar."""
        return None

    def on_idle(self, event):
        """Idle handler: process idle objects and load start pages.

        On the first idle event, any configured ``start_pages`` are
        opened via ``_on_html``.

        Args:
            event: wx.IdleEvent.
        """
        for obj in self.idle_objects:
            try:
                obj.on_idle()
            except Exception:
                logger.debug("Error in idle object %s", type(obj).__name__, exc_info=True)

        if not self.after_init:
            self.after_init = True
            app = wx.GetApp()
            if len(app.start_pages) > 0:

                def start_pages():
                    for page in app.start_pages:
                        url_page = page.split(";")
                        if len(url_page) == 2:
                            self._on_html(_(url_page[0]) + "," + app.base_address + url_page[1])

                wx.CallAfter(start_pages)

        event.Skip()

    def set_acc_key_tab(self, win, tab):
        """No-op: keyboard accelerators not supported in browser mode.

        Args:
            win: Target window.
            tab: Accelerator table entries.
        """
        pass
