import wx

from pytigon_gui.guilib.events import *
from pytigon_gui.toolbar.basetoolbar import (
    ToolbarBar,
    ToolbarPage,
    ToolbarPanel,
    ToolbarButton,
)


class MenuToolbarButton(ToolbarButton, wx.MenuItem):
    def __init__(
        self,
        parent_panel,
        id,
        title,
        bitmap=None,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        wx.MenuItem.__init__(self, parentMenu=parent_panel, id=id, text=title)
        if bitmap and bitmap.IsOk():
            self.SetBitmap(bitmap)


class MenuToolbarPanel(ToolbarPanel, wx.Menu):
    def __init__(self, parent_page, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        wx.Menu.__init__(self)
        ToolbarPanel.__init__(self, parent_page, title, kind)
        self.parent_page.parent_bar.Append(self, title)

    def create_button(
        self,
        id,
        title,
        bitmap=None,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        b = MenuToolbarButton(self, id, title, bitmap, bitmap_disabled, kind)
        self.Append(b)
        return b


class MenuToolbarPage(ToolbarPage):
    def __init__(self, parent_bar, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        ToolbarPage.__init__(self, parent_bar, title, kind)

    def create_panel(self, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        m = MenuToolbarPanel(self, title, kind)
        return m


class MenuToolbarBar(ToolbarBar, wx.MenuBar):
    def __init__(self, parent, gui_style):
        wx.MenuBar.__init__(self)
        ToolbarBar.__init__(self, parent, gui_style)

    def create_page(self, title, kind):
        return MenuToolbarPage(self, title, kind)

    def update_bar(self, obj):
        obj.SetMenuBar(self.bar)
