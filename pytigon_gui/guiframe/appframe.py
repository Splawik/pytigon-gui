"""
This module contains SchAppFrame class. When pytigon application starts, new top frame window (class SchAppFrame) is created.
During the initialisation process all defined for application plugins are started.
"""

import os
import sys
import platform
import subprocess
import base64
from pydispatch import dispatcher
from pathlib import Path

import wx

# import wx.html2
import datetime
from wx.lib.agw import aui

from django.conf import settings

from pytigon_lib.schfs.vfstools import get_temp_filename
from pytigon_lib.schdjangoext.tools import gettempdir
from pytigon_lib.schhttptools.httpclient import HttpResponse
from pytigon_lib import schfs

from pytigon_lib.schtools.tools import split2

# from pytigon_lib.schtasks.task import get_process_manager

from pytigon_gui.guilib.image import ArtProviderFromIcon
from pytigon_gui.guilib.events import *  # @UnusedWildImport
from pytigon_gui.guiframe.notebook import SchNotebook
from pytigon_gui.guiframe.notebookpage import SchNotebookPage
from pytigon_gui.guiframe.manager import SChAuiManager
from pytigon_gui.guilib.image import bitmap_from_href

from pytigon_gui.guiframe.baseframe import SchBaseFrame

_ = wx.GetTranslation

_RECORD_VIDEO = 0
_RECORD_VIDEO_STRUCT = None
_RECORD_VIDEO_OUT = None
_RECORD_VIDEO_MONITOR = None


def save_video_frame(win):
    global _RECORD_VIDEO_STRUCT, _RECORD_VIDEO_OUT, _RECORD_VIDEO_MONITOR
    if _RECORD_VIDEO_STRUCT:
        mss = _RECORD_VIDEO_STRUCT[0]
        cv2 = _RECORD_VIDEO_STRUCT[1]
        numpy = _RECORD_VIDEO_STRUCT[2]
        if not _RECORD_VIDEO_OUT:
            pos = win.GetScreenPosition()
            size = win.GetSize()

            # fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            _RECORD_VIDEO_OUT = cv2.VideoWriter(
                win._video, fourcc, 4, (size.width, size.height)
            )
            _RECORD_VIDEO_MONITOR = {
                "top": pos.y,
                "left": pos.x,
                "width": size.width,
                "height": size.height,
            }

        with mss() as sct:
            pos = win.GetScreenPosition()
            size = win.GetSize()
            frame = numpy.array(sct.grab(_RECORD_VIDEO_MONITOR))
            frame = numpy.flip(frame[:, :, :3], 2)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            _RECORD_VIDEO_OUT.write(frame)


def finish_video():
    if _RECORD_VIDEO_OUT:
        _RECORD_VIDEO_OUT.release()
        _RECORD_VIDEO_STRUCT = None


class _SChMainPanel(wx.Window):
    def __init__(self, app_frame, *argi, **argv):
        argv["name"] = "schmainpanel"
        if "style" in argv:
            argv["style"] |= wx.WANTS_CHARS
        self.app_frame = app_frame
        wx.Window.__init__(self, *argi, **argv)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND))

    def GetFrameManager(self):
        return self.GetParent().GetFrameManager()

    def GetMenuBar(self):
        return self.GetParent().GetMenuBar()

    def Freeze(self):
        pass

    def Thaw(self):
        pass


class SchAppFrame(SchBaseFrame):
    """
    This is main window of pytigon application
    """

    def __init__(
        self,
        gui_style="tree(toolbar,statusbar)",
        title="",
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.WANTS_CHARS,
        video_name="",
    ):
        """Constructor

        Args:
            gui_style - there is string with some key words. If specyfied key word exist some functionality of
            SChAppFrame are turned on.

            List of key words:

                dialog - application with one form

                one_form - some as dialog

                tray - application have system tray icon with some actions

                statusbar - show the status bar

                tree - menu in tree form

                standard - standard for platform interface

                modern - replace standard toolbar with ribbon bar

                toolbar - show the tool bar

            title - the window title

            pos - the window position

            size - the window size

            style - see wx.Frame constructor
        """

        SchBaseFrame.__init__(
            self, None, gui_style, wx.ID_ANY, title, pos, size, style, "MainWindow"
        )
        # self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND))

        self._id = wx.ID_HIGHEST
        self._perspectives = []
        self._menu_bar_lp = 0
        self._toolbar_bar_lp = 1
        self._proc_mannager = None
        self._video = video_name
        self.gui_style = gui_style
        self.idle_objects = []
        self.gui_style = gui_style
        self.command = {}
        # self.command_enabled_always = []
        self.last_pane = None
        self.active_pane = None
        self.active_page = None
        self.active_child_ctrl = None

        self.toolbar_interface = None
        self.menubar_interface = None
        self.statusbar_interface = None

        self.destroy_fun_tab = []
        self.after_init = False

        self.sys_command = dict({"EXIT": self.on_exit, "ABOUT": self.on_about})

        if "dialog" in self.gui_style or "one_form" in self.gui_style:
            hide_on_single_page = True
        else:
            hide_on_single_page = False

        self._panel = _SChMainPanel(self, self)
        self._mgr = SChAuiManager()
        self._mgr.SetManagedWindow(self._panel)

        if not hasattr(self._mgr, "SetAGWFlags"):
            self._mgr.SetAGWFlags = self._mgr.SetFlags
            self._mgr.GetAGWFlags = self._mgr.GetFlags

        self._mgr.SetAGWFlags(self._mgr.GetAGWFlags() ^ aui.AUI_MGR_ALLOW_ACTIVE_PANE)

        self.desktop = self._create_notebook_ctrl(hide_on_single_page)
        self.get_dock_art().SetMetric(aui.AUI_DOCKART_PANE_BORDER_SIZE, 0)

        wx.ArtProvider.Push(ArtProviderFromIcon())

        icon = wx.Icon()
        b = wx.Bitmap(wx.Image(wx.GetApp().src_path + "/static/icons/schweb.png"))
        icon.CopyFromBitmap(b)
        self.SetIcon(icon)

        if "tray" in gui_style:
            parent = self

            class _TaskBarIcon(wx.adv.TaskBarIcon):
                def CreatePopupMenu(self):
                    nonlocal parent
                    parent.PopupMenu(parent.menu_tray)
                    return None

            self.tbIcon = _TaskBarIcon()
            self.tbIcon.SetIcon(icon, "Pytigon")
        else:
            self.tbIcon = None

        if "statusbar" in gui_style:
            self.statusbar = self._create_status_bar()
        else:
            self.statusbar = None

        wx.GetApp().SetTopWindow(self)

        self.setup_frame()

        if "tree" in gui_style:
            self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        else:
            self._sizer = wx.BoxSizer(wx.VERTICAL)

        if "standard" in gui_style:
            if len(wx.GetApp().get_tab(self._toolbar_bar_lp)) > 1:
                from pytigon_gui.toolbar import standardtoolbar

                self.toolbar_interface = standardtoolbar.StandardToolbarBar(
                    self, gui_style
                )
                self._create_tool_bar()
                self.toolbar_interface.create()
            self._sizer.Add(self._panel, 1, wx.EXPAND)
            self._mgr.Update()
        elif "generic" in gui_style:
            if len(wx.GetApp().get_tab(self._toolbar_bar_lp)) > 1:
                from pytigon_gui.toolbar import generictoolbar

                self.toolbar_interface = generictoolbar.GenericToolbarBar(
                    self, gui_style
                )
                self._create_tool_bar()
                self.toolbar_interface.create()
            self._sizer.Add(self._panel, 1, wx.EXPAND)
            self._mgr.Update()
        elif "modern" in gui_style:
            from pytigon_gui.toolbar.moderntoolbar import ModernToolbarBar

            self.toolbar_interface = ModernToolbarBar(self, gui_style)
            self._create_tool_bar()
            # self.toolbar_interface.realize_bar()
            self.toolbar_interface.create()
            self._sizer.Add(self.toolbar_interface, 0, wx.EXPAND)
            self._sizer.Add(self._panel, 1, wx.EXPAND)
        elif "tree" in gui_style:
            from pytigon_gui.toolbar.treetoolbar import TreeToolbarBar

            self.toolbar_interface = TreeToolbarBar(self._panel, gui_style)
            self._create_tool_bar()
            self.toolbar_interface.create()
            self._mgr.AddPane(
                self.toolbar_interface,
                self._create_pane_info("menu", _("Menu"))
                .CaptionVisible(True)
                .MinimizeButton(True)
                .CloseButton(False)
                .Left()
                .BestSize((250, 40))
                .MinSize((250, 40))
                .Show(),
            )
            self._sizer.Add(self._panel, 1, wx.EXPAND)
        else:
            self._sizer.Add(self._panel, 1, wx.EXPAND)

        self.SetSizer(self._sizer)

        if wx.GetApp().get_tab(2) and len(wx.GetApp().get_tab(2)) > 1:
            self._menu_bar_lp = 2
        else:
            if wx.GetApp().menu_always:
                self._menu_bar_lp = 1

        if self._menu_bar_lp > 0:
            from pytigon_gui.toolbar import menubar

            self.menubar_interface = menubar.MenuToolbarBar(self, gui_style)
            self._create_menu_bar()

        s_dx = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        s_dy = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)

        self._mgr.AddPane(
            self._create_notebook_ctrl(),
            self._create_pane_info("panel", _("Tools"))
            .CaptionVisible(True)
            .Left()
            .MinSize((400, int(s_dy / 2)))
            .BestSize((int(s_dx / 2) - 50, s_dy - 100))
            .Show(),
        )
        self._mgr.AddPane(
            self._create_notebook_ctrl(),
            self._create_pane_info("header", _("Header"))
            .CaptionVisible(False)
            .Top()
            .MinSize((int(s_dx), int(s_dy / 10)))
            .BestSize((int(s_dx), int(s_dy / 5)))
            .Show(),
        )
        self._mgr.AddPane(
            self._create_notebook_ctrl(),
            self._create_pane_info("footer", _("Footer"))
            .CaptionVisible(False)
            .Bottom()
            .MinSize((int(s_dx), int(s_dy / 10)))
            .BestSize((int(s_dx), int(s_dy / 5)))
            .Show(),
        )
        self._mgr.AddPane(
            self.desktop,
            self._create_pane_info("desktop", _("Desktop")).CenterPane().Show(),
        )
        perspective_notoolbar = self._mgr.SavePerspective()

        if "toolbar" in gui_style and "standard" in gui_style:
            i = 1
            while True:
                name = "tb" + str(i)
                tbpanel = self._mgr.GetPane(name)
                if tbpanel.IsOk():
                    tbpanel.Show()
                else:
                    break
                i += 1

        perspective_all = self._mgr.SavePerspective()
        all_panes = self._mgr.GetAllPanes()

        for ii in range(len(all_panes)):
            if not all_panes[ii].IsToolbar():
                if all_panes[ii].name != "menu":
                    all_panes[ii].Hide()

        self._mgr.GetPane("desktop").Show()

        perspective_default = self._mgr.SavePerspective()

        size = self.desktop.GetPageCount()
        for i in range(size):  # @UnusedVariable
            self.desktop.DeletePage(0)

        self._perspectives.append(perspective_default)
        self._perspectives.append(perspective_all)
        self._perspectives.append(perspective_notoolbar)

        self.init_acc_keys()
        self.init_plugins()
        self.SetAcceleratorTable(wx.AcceleratorTable(self.aTable))

        self._mgr.Update()

        self.t1 = wx.Timer(self)
        self.t1.Start(250)

        self.Bind(wx.EVT_TIMER, self.on_timer, self.t1)
        self.Bind(aui.EVT_AUI_PANE_ACTIVATED, self.on_pane_activated)
        self.Bind(
            wx.EVT_MENU_RANGE, self.on_show_elem, id=ID_SHOWHEADER, id2=ID_SHOWTOOLBAR2
        )

        if "tray" in gui_style:
            self.Bind(wx.EVT_CLOSE, self.on_taskbar_hide)
        else:
            self.Bind(wx.EVT_CLOSE, self.on_close)

        self._panel.Bind(wx.EVT_CHILD_FOCUS, self.on_child_focus)

        self.bind_command(self.on_open, id=wx.ID_OPEN)
        self.bind_command(self.on_exit, id=wx.ID_EXIT)

        # if self.toolbar_interface:
        # self.toolbar_interface.bind_ui(self.on_update_ui_command, wx.ID_ANY)

        # for pos in [wx.ID_EXIT, ID_WEB_NEW_WINDOW, wx.ID_OPEN]:
        #    self.command_enabled_always.append(pos)

        self.bind_command(self.on_next_tab, id=ID_NEXTTAB)
        self.bind_command(self.on_prev_tab, id=ID_PREVTAB)
        self.bind_command(self.on_next_page, id=ID_NEXTPAGE)
        self.bind_command(self.on_prev_page, id=ID_PREVPAGE)
        self.bind_command(self.on_close_tab, id=ID_CLOSETAB)
        self.bind_command(self.on_refresh_tab, id=ID_REFRESHTAB)

        self.bind_command(self.on_goto_desktop, id=ID_GOTODESKTOP)
        self.bind_command(self.on_goto_head, id=ID_GOTOHEADER)
        self.bind_command(self.on_goto_panel, id=ID_GOTOPANEL)
        self.bind_command(self.on_goto_footer, id=ID_GOTOFOOTER)

        self.bind_command(self.on_command, id=ID_WEB_NEW_WINDOW)

        self.bind_command(self.on_show_status_bar, id=ID_SHOWSTATUSBAR)

        if self.menubar_interface:
            self.SetMenuBar(self.menubar_interface)

        if self.tbIcon:
            # self.tbIcon.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.on_taskbar_toogle)
            # self.tbIcon.Bind(wx.adv.EVT_TASKBAR_RIGHT_UP, self.on_taskbar_show_menu)

            self.menu_tray = wx.Menu()
            self.menu_tray.Append(ID_TASKBAR_SHOW, _("Show It"))
            self.Bind(wx.EVT_MENU, self.on_taskbar_show, id=ID_TASKBAR_SHOW)
            self.menu_tray.Append(ID_TASKBAR_HIDE, _("Minimize It"))
            self.Bind(wx.EVT_MENU, self.on_taskbar_hide, id=ID_TASKBAR_HIDE)
            self.menu_tray.AppendSeparator()
            self.menu_tray.Append(ID_TASKBAR_CLOSE, _("Close It"))
            self.Bind(wx.EVT_MENU, self.on_close, id=ID_TASKBAR_CLOSE)

        self.SetExtraStyle(wx.WS_EX_PROCESS_UI_UPDATES)
        wx.UpdateUIEvent.SetUpdateInterval(50)
        wx.UpdateUIEvent.SetMode(wx.UPDATE_UI_PROCESS_SPECIFIED)
        wx.CallAfter(self.UpdateWindowUI)
        self.Layout()
        wx.CallAfter(self.Bind, wx.EVT_IDLE, self.on_idle)
        wx.CallAfter(self.Show)

    def setup_frame(self):
        self.SetMinSize(wx.Size(800, 600))

    def init_acc_keys(self):
        self.aTable = [
            (wx.ACCEL_ALT, wx.WXK_PAGEUP, ID_PREVTAB),
            (wx.ACCEL_ALT, wx.WXK_PAGEDOWN, ID_NEXTTAB),
            (wx.ACCEL_ALT, wx.WXK_LEFT, ID_GOTOPANEL),
            (wx.ACCEL_ALT, ord("t"), ID_GOTOPANEL),
            (wx.ACCEL_ALT, wx.WXK_RIGHT, ID_GOTODESKTOP),
            (wx.ACCEL_ALT, ord("d"), ID_GOTODESKTOP),
            (wx.ACCEL_ALT, wx.WXK_UP, ID_GOTOHEADER),
            (wx.ACCEL_CTRL, ord("w"), ID_CLOSETAB),
            (wx.ACCEL_CTRL, ord("n"), ID_WEB_NEW_WINDOW),
            (wx.ACCEL_CTRL, wx.WXK_TAB, ID_NEXTTAB),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_TAB, ID_PREVTAB),
            (wx.ACCEL_CTRL, wx.WXK_F6, ID_NEXTTAB),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_F6, ID_PREVTAB),
            (wx.ACCEL_ALT, ord("h"), ID_PREVTAB),
            (wx.ACCEL_ALT, ord("l"), ID_NEXTTAB),
            (wx.ACCEL_ALT, ord("k"), ID_PREVPAGE),
            (wx.ACCEL_ALT, ord("j"), ID_NEXTPAGE),
            (wx.ACCEL_ALT, wx.WXK_BACK, ID_WEB_BACK),
            (0, wx.WXK_F5, ID_REFRESHTAB),
        ]

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
                                _(url_page[0]) + "," + app.base_path + "/" + url_page[1]
                            )
                        elif len(url_page) == 1:
                            self._on_html("," + app.base_path + "/" + url_page[0])

                wx.CallAfter(start_pages)

        event.Skip()

    def on_pane_activated(self, event):
        active_pane = event.GetPane()

        if self.active_pane != active_pane:
            if self.active_pane and hasattr(self.active_pane, "set_active"):
                self.active_pane.set_active(False)
                if self.active_pane.GetCurrentPage():
                    self.active_pane.GetCurrentPage().Refresh()

            self.active_pane = active_pane

            if active_pane and hasattr(active_pane, "set_active"):
                active_pane.set_active(True)
                if active_pane.GetCurrentPage():
                    active_pane.GetCurrentPage().Refresh()

        event.Skip()

    def get_frame_manager(self):
        """returns frame manager - aui.framemanager.AuiManager derived object"""
        return self._mgr

    def get_dock_art(self):
        """return art provider related to the asociated frame manager"""
        return self._mgr.GetArtProvider()

    def SetActive(self, notebook, tab):
        if tab:
            tab.SetFocus()

    def _create_notebook_ctrl(self, hideSingleTab=True):
        style = (
            aui.AUI_NB_WINDOWLIST_BUTTON
            | aui.AUI_NB_CLOSE_ON_ALL_TABS
            | aui.AUI_NB_TAB_MOVE
            | aui.AUI_NB_TAB_EXTERNAL_MOVE
            | aui.AUI_NB_TAB_SPLIT
            | aui.AUI_NB_WINDOWLIST_BUTTON
        )
        n = SchNotebook(self._panel, wx.Point(0, 0), wx.Size(0, 0), style=style)
        n.SetAGWWindowStyleFlag(style)
        n.SetArtProvider(aui.VC71TabArt())
        return n

    def _create_pane_info(self, name, caption):
        return aui.AuiPaneInfo().Name(name).Caption(caption)

    def _on_page_event(self, direction):
        """scroll active form"""
        w = wx.Window.FindFocus()
        parent = w
        while parent:
            if parent.__class__.__name__ == "SchForm":
                if hasattr(parent, "on_page_event"):
                    parent.on_page_event(direction)
                    return
                else:
                    y = parent.GetViewStart()[1] * parent.GetScrollPixelsPerUnit()[1]
                    dy = (
                        parent.GetScrollPageSize(wx.VERTICAL)
                        * parent.GetScrollPixelsPerUnit()[1]
                    )
                    y = y + direction * dy
                    if y < 0:
                        y = 0
                    if parent.GetScrollPixelsPerUnit()[1] != 0:
                        parent.Scroll(-1, y / parent.GetScrollPixelsPerUnit()[1])
                    else:
                        parent.Scroll(-1, y)
                    return
            else:
                parent = parent.GetParent()

    def on_next_page(self, evt):
        """scroll active form one page down"""
        self._on_page_event(1)

    def on_prev_page(self, evt):
        """scroll active form one page up"""
        self._on_page_event(-1)

    def on_next_tab(self, evt):
        """select a next tab in desktop notebook"""
        desktop = wx.GetApp().GetTopWindow().desktop
        id = desktop.GetPageIndex(desktop.GetCurrentPage())
        idn = 0
        if id != None and id >= 0:
            idn = id + 1
        if idn >= desktop.GetPageCount():
            idn = 0
        desktop.SetSelection(idn)
        return

    def on_prev_tab(self, evt):
        """select a previous tab in desktop notebook"""
        desktop = wx.GetApp().GetTopWindow().desktop
        id = desktop.GetSelection()
        idn = 0
        if id >= 0:
            idn = id - 1
        if idn < 0:
            idn = desktop.GetPageCount() - 1
        desktop.SetSelection(idn)
        return

    def on_close_tab(self, evt):
        """close active tab in active notebook"""
        win = wx.Window.FindFocus()
        while win:
            if win.__class__.__name__ == "SchNotebook":
                id = win.GetSelection()
                if id >= 0:
                    panel = win.GetPage(id)
                    panel.close_child_page(True)
                return
            win = win.GetParent()

    def after_close(self, win):
        count = win.GetPageCount()
        if count < 1:
            apppanel = win.GetPanel()
            if apppanel:
                apppanel.Hide()
                self._mgr.Update()

    def on_refresh_tab(self, evt):
        """Refresh content of active form"""
        desktop = wx.GetApp().GetTopWindow().desktop
        idn = desktop.GetSelection()
        if idn >= 0:
            panel = desktop.GetPage(idn)
            panel.refresh_html()

    def get_active_ctrl(self):
        """Get active widget"""
        ctrl = None
        idn = self.desktop.GetSelection()
        if idn >= 0:
            panel = self.desktop.GetPage(idn)
            if panel:
                count = panel.get_page_count()
                if count > 0:
                    htmlwin = panel.get_page(count - 1)
                    if htmlwin:
                        ctrl = htmlwin.get_last_control_with_focus()
                return ctrl
        return None

    def get_active_panel(self):
        """get active form"""
        idn = self.desktop.GetSelection()
        if idn >= 0:
            panel = self.desktop.GetPage(idn)
            if panel:
                count = panel.GetPageCount()
                if count > 0:
                    htmlwin = panel.GetPage(count - 1)
                    return htmlwin
        return None

    def _open_page(
        self,
        response,
        title="",
        parameters=None,
        view_in=None,
    ):
        address = response.url
        # html: text/html
        # js: text/javascript
        # jsnon: application/json
        if "text/" in response.ret_content_type:
            return self.new_main_page(response, title, parameters, view_in)

        # html: text/python
        if "text/python" in response.ret_content_type:
            exec(http.str())
            return

        # pdf: "application/pdf"
        if "application/pdf" in response.ret_content_type:
            return self.show_pdf(response, title, parameters)

        # spdf: "application/spdf"
        if "application/spdf" in response.ret_content_type:
            if "?print=" in address:
                return self.print_spdf(response, title, parameters)
            else:
                return self.show_spdf(response, title, parameters)
            # return self.show_spdf(response, title, parameters)

        # ods: "application/vnd.oasis.opendocument.spreadsheet"
        # odp: "application/vnd.oasis.opendocument.text"
        # xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        # docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document

        if "application/vnd" in response.ret_content_type:
            return self.show_document(response, title, parameters)

        if "application/" in response.ret_content_type:
            return self.download_data(response, title, parameters)

        if (
            "video/" in response.ret_content_type
            or "audio/" in response.ret_content_type
        ):
            return self.show_document(response, title, parameters)

        # "image/"
        if "image/" in response.ret_content_type:
            return self.show_image(response, title, parameters)

        # zip: application/zip
        if "application/zip" in response.ret_content_type:
            return self.download_data(response, title, parameters)

        if "application/json" in response.ret_content_type:
            return self.download_data(response, title, parameters, view_in)

        return self.download_data(response, title, parameters)

    def open_page(
        self,
        address,
        title="",
        parameters=None,
        view_in=None,
    ):
        http = wx.GetApp().get_http_for_adr(address)
        if parameters:
            response = http.post(self, address, parameters)
        else:
            response = http.get(self, address)

        return self._open_page(response, title, parameters, view_in)

    def new_main_page(
        self, address_or_parser, title="", parameters=None, view_in="desktop", http=None
    ):
        """Open a new page in main

        Args:
            address_or_parser: can be: address of http page (str type) or
            :class:'~pytigon_lib.schparser.html_parsers.ShtmlParser'
            title - new tab title
            parameters - parameters of http request
            view_in - options are: 'desktop', 'panel', 'header', 'footer'
        Returns:
            created form :class:'~pytigon_gui.guiframe.htmlsash.SchPage'
        """

        if type(address_or_parser) == str:
            address = address_or_parser
            if (
                not address.startswith("^")
                and not address.startswith("file://")
                and view_in == "desktop"
            ):
                return self.open_page(address_or_parser, title, parameters, view_in)

        elif type(address_or_parser) == HttpResponse:
            address = address_or_parser.url
        else:
            address = address_or_parser.address

        ext = address.split("?")[0].split(".")[-1]
        if (
            (not view_in or not "browser" in view_in)
            and ext
            and ext
            in (
                "pdf",
                "spdf",
                "ods",
                "odp",
                "odt",
                "docx",
                "xlsx",
                "pptx",
                "zip",
                "avi",
                "mpeg",
                "mp3",
                "mp4",
            )
        ):
            return self.open_page(address, title, parameters, view_in)

        if view_in:
            panel = view_in
        else:
            parm = split2(address, "?")
            if len(parm) == 2:
                panel = "desktop"
                parm2 = parm[1].split(",")
                parm3 = [pos.split("=") for pos in parm2]
                for pos in parm3:
                    if len(pos) == 2:
                        if pos[0] == "show_in":
                            panel = pos[1]
                            break

        if panel == "pscript":
            if not http:
                http = wx.GetApp().get_http(self)
            response = http.get(self, address)
            ptr = response.str()
            exec(ptr)
            return

        if not address.startswith("^"):
            if (not view_in or view_in.startswith("browser")) or (
                address.startswith("http")
                and not address.startswith(wx.GetApp().base_address)
            ):
                if view_in and "_" in view_in:
                    panel = view_in.split("_")[1]
                else:
                    panel = "desktop"
                ret = self.new_main_page(
                    "^standard/webview/widget_web.html", "Empty page", view_in=panel
                )
                if (
                    address.startswith("http://")
                    or address.startswith("https://")
                    or address.startswith("file://")
                ):

                    def _ret_fun():
                        if type(address_or_parser) == str:
                            ret.body.WEB.go(address)
                        else:
                            ret.body.WEB.load_str(address_or_parser.ptr())

                    wx.CallAfter(_ret_fun)
                else:

                    def _ret_fun():
                        if type(address_or_parser) == str:
                            ret.body.WEB.go(wx.GetApp().base_path + address)
                        else:
                            ret.body.WEB.load_str(address_or_parser.ptr())

                    wx.CallAfter(_ret_fun)
                return ret

        if len(title) < 32:
            title2 = title
        else:
            title2 = title[:30] + "..."

        if panel.startswith("toolbar"):
            name = panel[7:]
            if name[0:1] == "_":
                return self.toolbar_interface.create_html_win(
                    name[1:], address_or_parser, parameters
                )
            else:
                return self.toolbar_interface.create_html_win(
                    None, address_or_parser, parameters
                )
        if panel == "desktop2":
            n = self._mgr.GetPane("desktop").window
        else:
            n = self._mgr.GetPane(panel).window

        if not self._mgr.GetPane(panel).IsShown():
            refr = True
        else:
            refr = False

        if title2 in [pos.caption for pos in n._tabs._pages]:
            for id, pos in enumerate(n._tabs._pages):
                if pos.caption == title2:
                    n.SetSelection(id)
                    n.activate_page(pos.window)
            if refr:
                self._mgr.GetPane(panel).Show()
                self._mgr.Update()
            return None

        page = SchNotebookPage(n)
        if panel == "desktop2":
            if title is None:
                if type(address_or_parser) == str:
                    n.add_and_split(page, "", wx.RIGHT)
                else:
                    n.add_and_split(page, address_or_parser.title, wx.RIGHT)
            else:
                n.add_and_split(page, title2, wx.RIGHT)
        else:
            if title is None:
                if type(address_or_parser) == str:
                    n.AddPage(page, "", True)
                else:
                    n.AddPage(page, address_or_parser.title, True)
            else:
                n.AddPage(page, title2, True)

        if type(address_or_parser) == str:
            address = address_or_parser
        elif type(address_or_parser) == HttpResponse:
            address = address_or_parser.url

        else:
            address = address_or_parser.address

        if http:
            page.http = http
        else:
            page.http = wx.GetApp().get_http_for_adr(address)

        if refr:
            self._mgr.GetPane(panel).Show()
        self._mgr.Update()

        return page.new_child_page(address_or_parser, None, parameters)

    def on_taskbar_hide(self, event):
        self.Hide()

    def on_taskbar_toogle(self, event):
        if self.IsShown():
            self.Hide()
        else:
            self.Show()

    def on_taskbar_show(self, event):
        self.Show()

    def bind_command(self, fun, id=wx.ID_ANY):
        """bind command event, unlike wxPython Bind this function bind command to menu and toolbar interface"""
        self.Bind(wx.EVT_MENU, fun, id=id)
        if self.toolbar_interface:
            self.toolbar_interface.bind(fun, id)

    def get_menu_bar(self):
        """return toolbar interface"""
        return self.menubar_interface

    def get_tool_bar(self):
        """return toolbar interface"""
        return self.toolbar_interface

    def on_child_focus(self, event):
        pane = self._mgr.GetPane(event.GetWindow())
        if pane.IsOk():
            if self.active_pane:
                name = self.active_pane.Name
            else:
                name = ""
            if name != pane.Name:
                self.last_pane = self.active_pane
                self.active_pane = pane

        self.active_child_ctrl = event.GetWindow()
        event.Skip()

    def on_timer(self, evt):
        # if platform.system() == "Windows":
        #    wx.html2.WebView.New("messageloop")
        global _RECORD_VIDEO, _RECORD_VIDEO_STRUCT
        if self._video:
            if _RECORD_VIDEO == 0:
                try:
                    from mss import mss
                    import cv2
                    import numpy

                    _RECORD_VIDEO_STRUCT = (mss, cv2, numpy)
                    _RECORD_VIDEO = 1
                except:
                    _RECORD_VIDEO = 2
            if _RECORD_VIDEO == 1:
                save_video_frame(self)

        x = dispatcher.getReceivers(signal="PROCESS_INFO")
        if len(x) > 0:
            if not self._proc_mannager:
                self._proc_mannager = get_process_manager()
            x = self._proc_mannager.list_threads(all=False)
            dispatcher.send("PROCESS_INFO", self, x)

    def _append_command(self, typ, command):
        id = wx.NewId()
        self.command[id] = (typ, command)
        return id

    def _create_bars(self, bar, tab):
        for row in tab:
            if len(row[0].data) > 0:
                pos = 1
            else:
                if len(row[1].data) > 0:
                    pos = 2
                else:
                    if len(row[2].data) > 0:
                        pos = 3
                    else:
                        pos = -1
            if pos >= 0:
                if pos == 1:
                    page = bar.append(row[0].data)
                if pos == 2:
                    panel = page.append(row[1].data)
                if pos == 3:
                    try:
                        bitmap = (wx.GetApp().images)[int(row[4].data)]
                    except:
                        if row[4].data and row[4].data != "" and row[4].data != "None":
                            try:
                                bitmap = bitmap_from_href(row[4].data.split("<=")[0])
                            except:
                                bitmap = (wx.GetApp().images)[0]
                        else:
                            bitmap = (wx.GetApp().images)[0]
                    if not bitmap:
                        bitmap = (wx.GetApp().images)[0]
                    idn = self._append_command(row[5].data, row[6].data)
                    panel.append(idn, row[2].data, bitmap)
            bar.bind(self.on_command)

    def _create_menu_bar(self):
        tab = wx.GetApp().get_tab(self._menu_bar_lp)[1:]
        bar = self.menubar_interface
        return self._create_bars(bar, tab)

    def _create_tool_bar(self):
        tab = wx.GetApp().get_tab(self._toolbar_bar_lp)[1:]
        bar = self.toolbar_interface
        return self._create_bars(bar, tab)

    def bind_to_toolbar(self, funct, id):
        """bind function to toolbar button

        Args:
            funct - function (event handler) to bind
            id - toolbar button id
        """
        if "toolbar" in self.gui_style:
            self.toolbar_interface.bind(funct, id)

    def _create_status_bar(self):
        statusbar = self.CreateStatusBar(2)
        statusbar.SetStatusWidths([-2, -3])
        statusbar.SetStatusText("Ready", 0)
        return statusbar

    def _exit(self, event=None):
        finish_video()
        self.t1.Stop()
        wx.GetApp().on_exit()
        self._mgr.UnInit()
        if self.tbIcon:
            self.tbIcon.RemoveIcon()
            self.tbIcon = None
        self.Destroy()

    def on_open(self, event):
        if wx.GetApp().base_app:
            base_path = wx.GetApp().base_address + "/" + wx.GetApp().base_app
        else:
            base_path = wx.GetApp().base_address
        self.new_main_page(
            base_path + "/schcommander/form/FileManager/", "Commander", None, "panel"
        )

    def on_exit(self, event=None):
        self._exit()

    def on_close(self, event):
        super().on_close(event)
        self._exit()
        event.Skip()

    def on_show_elem(self, event):
        name = ["header", "panel", "footer", "tb1", "tb2"][
            event.GetId() - ID_SHOWHEADER
        ]
        panel = self._mgr.GetPane(name)
        panel.Show(not panel.IsShown())
        self._mgr.Update()

    def count_shown_panels(self, count_toolbars=True):
        """count visible panels"""
        count = 0
        for panel in self._mgr.GetAllPanes():
            if panel.IsShown():
                if (not "Toolbar" in panel.caption) or count_toolbars:
                    count += 1
        return count

    def on_show_status_bar(self, event):
        if not self.statusbar:
            self._create_status_bar()

    def _on_html(self, command):
        l = command.split(",")
        if len(l) > 2:
            parm = l[2]
            if parm == "":
                parm = None
        else:
            parm = None

        if l[1] != None and l[1][0] == " ":
            l[1] = (l[1])[1:]
        if parm != None and parm[0] == " ":
            parm = parm[1:]

        if l[0]:
            return self.new_main_page(l[1], l[0], parm)
        else:
            return self.new_main_page(l[1], l[0], parm, panel="pscript")

    def _on_python(self, command):
        exec(command)

    def _on_sys(self, command):
        (self.sys_command)[command]()

    def on_command(self, event):
        id = event.GetId()
        if id in self.command:
            cmd = self.command[id]
            if cmd[0] == "html":
                return self._on_html(cmd[1])
            if cmd[0] == "python":
                return self._on_python(cmd[1])
            if cmd[0] == "sys":
                return self._on_sys(cmd[1])
        else:
            if id == ID_RESET:
                from pytigon_gui.toolbar.moderntoolbar import RibbonInterface

                old_toolbar = self.toolbar_interface
                sizer = self.GetSizer()
                self.toolbar_interface = RibbonInterface(self, self.gui_style)
                self._create_tool_bar()
                self.toolbar_interface.realize_bar()
                sizer.Replace(old_toolbar.get_bar(), self.toolbar_interface.get_bar())
                self.toolbar_interface.get_bar().SetSize(
                    old_toolbar.get_bar().GetSize()
                )
                wx.CallAfter(old_toolbar.get_bar().Destroy)
                return
            elif id == ID_WEB_NEW_WINDOW:
                win = (
                    wx.GetApp()
                    .GetTopWindow()
                    .new_main_page("^standard/webview/widget_web.html", "Empty page")
                )
                win.body.new_child_page("^standard/webview/gotopanel.html", title="Go")
                return
        event.Skip()

    def on_about(self):
        msg = (
            "Pytigon runtime\nSławomir Chołaj\nslawomir.cholaj@gmail.com\n\n"
            + "The program uses wxpython library version:"
            + wx.VERSION_STRING
        )
        dlg = (
            wx.MessageDialog(self, msg, "Pytigon", wx.OK | wx.ICON_INFORMATION)
            % wx.GetApp().title
        )
        dlg.ShowModal()
        dlg.Destroy()

    def on_acc_key_down(self, event):
        for a in self.aTable:
            if event.KeyCode == a[1]:
                if event.AltDown() and (a[0] & wx.ACCEL_ALT == 0):
                    continue
                if event.ControlDown() and (a[0] & wx.ACCEL_CTRL == 0):
                    continue
                if event.ShiftDown() and (a[0] & wx.ACCEL_SHIFT == 0):
                    continue
                self.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_MENU_SELECTED, a[2]))
                return
        event.Skip()

    # def get_start_position(self):
    #    self.x = self.x + 20
    #    x = self.x
    #    pt = self.ClientToScreen(wx.Point(0, 0))
    #    return wx.Point(pt.x + x, pt.y + x)

    def goto_panel(self, panel_name):
        """Activate panel

        Args:
            panel_name: name of panel to activate
        """
        panel = self._mgr.GetPane(panel_name)
        if panel.window.GetPageCount() > 0:
            if not panel.IsShown():
                panel.Show(True)
                self._mgr.Update()
            panel.window.SetFocus()

    def on_goto_panel(self, event):
        panel = self._mgr.GetPane("panel")
        if panel.IsShown():
            self.goto_panel("panel")
        else:
            panel = self._mgr.GetPane("menu")
            if panel and panel.IsShown():
                panel.window.SetFocus()

    def on_goto_head(self, event):
        self.goto_panel("header")

    def on_goto_footer(self, event):
        self.goto_panel("footer")

    def on_goto_desktop(self, event):
        self.desktop.SetFocus()

    def show_pdf(self, response, title="", parameters=None):
        """show pdf downloaded from web server

        Args:
            page: web page address
        """

        temp_filename = schfs.get_temp_filename(ext="pdf")
        with schfs.open_file(temp_filename, "wb") as f:
            f.write(response.ptr())

        form_frame = self.new_main_page(
            "file://" + temp_filename, temp_filename, view_in="browser"
        )

        def _after_init():
            form_frame.body.WEB.execute_javascript("document.title = '%s';" % title)

        wx.CallAfter(_after_init)

        return form_frame

    def show_spdf(self, response, title="", parameters=None):
        temp_filename = schfs.get_temp_filename(ext="spdf", for_vfs=False)
        with schfs.open_file(temp_filename, "wb", for_vfs=False) as f:
            f.write(response.ptr())

        return self.new_main_page(
            "^standard/html_print/html_print.html",
            "file://" + temp_filename,
            parameters=temp_filename,
        )

    def print_spdf(self, response, title="", parameters=None):
        if hasattr(wx.GetApp(), "get_printout"):
            temp_filename = schfs.get_temp_filename(ext="spdf", for_vfs=False)
            with schfs.open_file(temp_filename, "wb", for_vfs=False) as f:
                f.write(response.ptr())

            printer = wx.Printer()
            printout = wx.GetApp().get_printout(temp_filename)
            printer.Print(self, printout, True)

            os.unlink(temp_filename)
        return

    def show_document(self, response, title="", parameters=None):
        cd = response.response.headers.get("content-disposition")
        if cd:
            name = cd.split("filename=")[1].replace('"', "")
        else:
            name = "data.dat"

        p = response.ptr()
        path = gettempdir()

        file_path = os.path.join(path, name)

        with open(file_path, "wb") as f:
            f.write(p)

        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])

    def show_image(self, response, title="", parameters=None):
        temp_filename = schfs.get_temp_filename(ext="spdf", for_vfs=False)
        with schfs.open_file(temp_filename, "wb", for_vfs=False) as f:
            f.write(response.ptr())

        return self.new_main_page(
            "^standard/image_viewer/viewer.html", temp_filename, view_in="desktop"
        )

    def download_data(self, response, title="", parameters=None):
        cd = response.response.headers.get("content-disposition")
        if cd:
            name = cd.split("filename=")[1].replace('"', "")
        else:
            name = "data.dat"

        p = response.ptr()

        path = str(Path.home() / "Downloads")

        with open(os.path.join(path, name), "wb") as f:
            f.write(p)

        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

        return True

    def get_main_panel(self):
        return self._panel
