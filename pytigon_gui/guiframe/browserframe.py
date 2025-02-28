import os
import sys
import wx

from pytigon_lib.schhttptools.httpclient import COOKIES

import pytigon_gui.guictrl.ctrl

from pytigon_gui.guiframe.baseframe import SchBaseFrame

from django.conf import settings

from pytigon.pytigon_request import init, request

_ = wx.GetTranslation


class SchBrowserFrame(SchBaseFrame):
    """
    This is main window of pytigon application
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

        init(os.environ["PRJ_NAME"], "auto", "anawa", user_agent="webviewembeded")
        start_request = request("/", None, user_agent="webviewembeded")

        self.ctrl = pytigon_gui.guictrl.ctrl.HTML2(
            self, name="schbrowser", size=self.GetClientSize()
        )
        self.ctrl.load_str(start_request.str(), "http://127.0.0.5/")

        if sys.platform != "win32":
            while not self.ctrl.page_loaded:
                wx.Yield()

        size = wx.GetApp().app_size
        wx.CallAfter(self.SetSize, (size[0], size[1]))
        wx.CallAfter(self.Show)

    def on_size(self, event):
        if event:
            if self.ctrl:
                self.ctrl.SetSize(event.GetSize())
            event.Skip()
        else:
            if self.ctrl:
                self.ctrl.SetSize(self.GetSize())

    def get_menu_bar(self):
        return None

    def on_idle(self, event):
        for obj in self.idle_objects:
            obj.on_idle()

        if not self.after_init:
            self.after_init = True
            app = wx.GetApp()
            if len(app.start_pages) > 0:

                def start_pages():
                    for page in app.start_pages:
                        url_page = page.split(";")
                        if len(url_page) == 2:
                            self._on_html(
                                _(url_page[0]) + "," + app.base_address + url_page[1]
                            )

                wx.CallAfter(start_pages)

        event.Skip()

    def set_acc_key_tab(self, win, tab):
        pass
