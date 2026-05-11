"""
SchNotebook object used as a top-level container in panels:
'desktop', 'panel', 'header' and 'footer'.

Extends aui.AuiNotebook with custom page activation, closing,
splitting, and wiki-based help lookup.
"""

import wx
import wx.lib.agw.aui as aui
from wx.lib.agw.aui import framemanager
from pytigon_lib.schtools.wiki import wiki_from_str
from pytigon_gui.guiframe.manager import SChAuiBaseManager
from wx.lib.agw.aui.aui_constants import *


class SchNotebook(aui.AuiNotebook):
    """Custom AUI notebook for Pytigon applications.

    Manages tab pages within desktop, panel, header, and footer
    containers.  Supports page splitting, custom close behaviour,
    and wiki-based help on double-click of a tab.
    """

    def __init__(
        self,
        parent,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.BORDER_NONE | wx.TAB_TRAVERSAL | wx.WANTS_CHARS,
    ):
        """Construct a SchNotebook.

        Args:
            parent: Parent window.
            pos: Window position (default: wx.DefaultPosition).
            size: Window size (default: wx.DefaultSize).
            style: Window style flags.
        """
        self._curpage = -1
        self._tab_id_counter = AuiBaseTabCtrlId
        self._dummy_wnd = None
        self._hide_tabs = False
        self._sash_dclick_unsplit = False
        self._tab_ctrl_height = 20
        self._requested_bmp_size = wx.Size(-1, -1)
        self._requested_tabctrl_height = -1
        self._textCtrl = None
        self._tabBounds = (-1, -1)

        self.panel = None
        self.active = False
        self.closing = False
        self.last_active = None

        # Deliberately call wx.Panel.__init__ instead of AuiNotebook's
        # to keep control over the initialization sequence.
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos, size, style, name="SchNotebook")
        self._mgr = SChAuiBaseManager()

        self._tabs = aui.AuiTabContainer(self)
        self.InitNotebook(AUI_NB_DEFAULT_STYLE)

        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_closing)
        self.Bind(aui.EVT_AUINOTEBOOK_TAB_DCLICK, self.on_dclick)
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_changed)
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGING, self.on_changing)
        self.Bind(wx.EVT_NAVIGATION_KEY, self.on_navigate)

        self.SetWindowStyleFlag(wx.WANTS_CHARS)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND))

    def on_closing(self, event):
        """Handle page close request.

        Vetoes the close if the page's ``close_no_del`` method
        indicates there are still child pages to close first.
        """
        idn = event.GetSelection()
        if idn >= 0:
            page = self.GetPage(idn)
            self.closing = True
            if page.close_no_del(True):
                self.GetParent().GetParent().after_close(self)
                event.Veto()

    def on_changed(self, event):
        """Handle page selection change.

        Refreshes the previously selected and newly selected pages,
        then activates the new page.
        """
        sel = event.GetSelection()
        old_sel = event.GetOldSelection()
        if old_sel >= 0:
            self.GetPage(old_sel).Refresh()
        if sel >= 0:
            self.GetPage(sel).Refresh()
            self.activate_page(self.GetPage(sel))
        event.Skip()

    def on_changing(self, event):
        """Handle page selection about to change.

        When closing a tab, ensures the selection moves to a sensible
        neighbouring page.
        """
        if self.closing:
            self.closing = False
            sel = event.GetSelection()
            oldsel = event.GetOldSelection()
            if oldsel == -1:
                new_page = self.GetPage(sel)
                tab = self.FindTab(new_page)[0]
                if tab:
                    count = tab.GetPageCount()
                    if count > 0:
                        new_sel = count - 1
                        if new_sel > sel:
                            self.SetSelection(new_sel)
                            event.Veto()
                            return
        event.Skip()

    def DeletePage(self, sel):
        """Delete the page at index *sel*.

        When the last page is removed, hides the parent panel and
        restores focus to a visible pane.
        """
        page = self.GetPage(sel)
        if page == self.last_active:
            self.last_active = None

        def _close():
            self.panel.Hide()
            top = wx.GetApp().GetTopWindow()
            if top:
                top._mgr.Update()
            for pane_name in ("desktop", "panel", "menu", "header", "footer"):
                pane_info = top._mgr.GetPane(pane_name) if top else None
                if pane_info and pane_info.IsOk() and pane_info.IsShown():
                    pane_info.window.SetFocus()

        if len(self._tabs._pages) == 1:
            wx.CallAfter(_close)

        return aui.AuiNotebook.DeletePage(self, sel)

    def on_dclick(self, event):
        """Handle tab double-click.

        Opens the associated wiki help page in a new split pane.
        """
        try:
            txt = self.GetPageText(event.GetSelection())
            mp, adr = wx.GetApp().read_html(
                self, "/schwiki/help/" + wiki_from_str(txt) + "/view/", None
            )
            if not txt.startswith("?"):
                wiki = wiki_from_str(txt)
                wx.GetApp().GetTopWindow().new_main_page(
                    mp, "?: " + wiki, panel="desktop2"
                )
        except Exception:
            pass

    def SetPanel(self, panel):
        """Store a reference to the owning panel.

        Args:
            panel: The parent panel object.
        """
        self.panel = panel

    def GetPanel(self):
        """Return the owning panel reference."""
        return self.panel

    def set_active(self, active):
        """Set the active state and refresh the current page.

        Args:
            active: True to activate, False to deactivate.
        """
        self.active = active
        if active:
            w = self.GetCurrentPage()
            self.activate_page(w)
            self.GetParent().GetParent().SetActive(self, w)

    def activate_page(self, page):
        """Activate *page* and deactivate the previously active one.

        Args:
            page: The SchNotebookPage to activate, or None.
        """
        if self.last_active:
            self.last_active.deactivate_page()
        self.last_active = page
        if page:
            page.activate_page()

    def add_and_split(self, page, title, direction):
        """Add a page and split the notebook window.

        Args:
            page: SchNotebookPage to add.
            title: Caption for the new tab.
            direction: wx.LEFT, wx.TOP, wx.RIGHT, or wx.BOTTOM.
        """
        self.closing = False
        if self.GetPageCount() < 1:
            return

        cli_size = self.GetClientSize()
        if self.GetPageCount() > 2:
            split_size = self.CalculateNewSplitSize()
        else:
            split_size = self.GetClientSize()
            split_size.x = int(split_size.x / 2)
            split_size.y = int(split_size.y / 2)

        new_tabs = aui.TabFrame(self)
        new_tabs.SetTabCtrlHeight(self._tab_ctrl_height)
        self._tab_id_counter += 1
        new_tabs._tabs = aui.AuiTabCtrl(self, self._tab_id_counter)
        new_tabs._tabs.SetArtProvider(self._tabs.GetArtProvider().Clone())
        new_tabs._tabs.SetAGWFlags(self._agwFlags)
        dest_tabs = new_tabs._tabs

        pane_info = (
            framemanager.AuiPaneInfo()
            .CaptionVisible(False)
            .BestSize(split_size.GetWidth(), split_size.GetHeight())
        )

        if direction == wx.LEFT:
            pane_info.Left()
            mouse_pt = wx.Point(0, int(cli_size.y / 2))
        elif direction == wx.RIGHT:
            pane_info.Right()
            mouse_pt = wx.Point(cli_size.x, int(cli_size.y / 2))
        elif direction == wx.TOP:
            pane_info.Top()
            mouse_pt = wx.Point(int(cli_size.x / 2), 0)
        elif direction == wx.BOTTOM:
            pane_info.Bottom()
            mouse_pt = wx.Point(int(cli_size.x / 2), cli_size.y)
        else:
            pane_info.Right()
            mouse_pt = wx.Point(cli_size.x, int(cli_size.y / 2))

        page_info = aui.AuiNotebookPage()
        page_info.window = page
        page_info.caption = title
        page_info.active = False
        page_info.control = None

        idn = self.GetPageCount()
        self._tabs.InsertPage(page, page_info, idn)
        dest_tabs.AddPage(page, page_info)
        self.SetPageTextColour(idn, wx.Colour(0, 96, 0))
        page.Reparent(self)
        self.DoSizing()
        dest_tabs.Refresh()
        self.UpdateHintWindowSize()

        self._mgr.AddPane(new_tabs, pane_info, mouse_pt)
        self._mgr.Update()

    def on_navigate(self, evt):
        """Handle navigation key events.

        Activates the current page and passes the event on.
        """
        forward = evt.GetDirection()
        self.activate_page(self.GetCurrentPage())
        evt.Skip()

    def Freeze(self):
        """Prevent visual updates (no-op for this control)."""
        pass

    def Thaw(self):
        """Allow visual updates (no-op for this control)."""
        pass
