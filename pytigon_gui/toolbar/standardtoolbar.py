"""Standard (classic) toolbar implementation.

Provides a simple wx.ToolBar-based toolbar.
"""

import wx

from pytigon_gui.guilib.events import *
from pytigon_gui.toolbar.basetoolbar import (
    ToolbarBar,
    ToolbarPage,
    ToolbarPanel,
    ToolbarButton,
)


_ = wx.GetTranslation


class StandardToolbarButton(ToolbarButton):
    """Standard toolbar button (thin wrapper around ToolbarButton)."""

    def __init__(
        self,
        parent_panel,
        id,
        title,
        bitmap,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        ToolbarButton.__init__(
            self, parent_panel, id, title, bitmap, bitmap_disabled, kind
        )


class StandardToolbarPanel(ToolbarPanel):
    """A panel within a standard toolbar page that holds a group of buttons."""

    def __init__(self, parent_page, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        """Initialize the panel, adding a separator if not the first.

        Args:
            parent_page: Parent StandardToolbarPage.
            title: Panel title.
            kind: Panel type.
        """
        ToolbarPanel.__init__(self, parent_page, title, kind)
        if len(parent_page.panels) > 0:
            parent_page.parent_bar.standard_tool_bar.AddSeparator()

    def _append(self, b):
        """Add a ToolbarButton to the underlying wx.ToolBar.

        Args:
            b: A StandardToolbarButton to add.

        Returns:
            The wx.ToolBar tool item or None.
        """
        item = None
        if self.kind in (
            ToolbarPanel.TYPE_PANEL_TOOLBAR,
            ToolbarPanel.TYPE_PANEL_BUTTONBAR,
        ):
            if b.kind == ToolbarButton.TYPE_SIMPLE:
                item = self.parent_page.parent_bar.standard_tool_bar.AddTool(
                    b.id, b.title, b.bitmap, b.title, kind=wx.ITEM_NORMAL
                )
            elif b.kind == ToolbarButton.TYPE_DROPDOWN:
                item = self.parent_page.parent_bar.standard_tool_bar.AddTool(
                    b.id, b.title, b.bitmap, b.title
                )
            elif b.kind == ToolbarButton.TYPE_HYBRID:
                item = self.parent_page.parent_bar.standard_tool_bar.AddTool(
                    b.id, b.title, b.bitmap, b.title
                )
            elif b.kind == ToolbarButton.TYPE_TOOGLE:
                item = self.parent_page.parent_bar.standard_tool_bar.AddToggleTool(
                    b.id, b.title, b.bitmap
                )
            elif b.kind == ToolbarButton.TYPE_PANEL:
                pass
            elif b.kind == ToolbarButton.TYPE_SEPARATOR:
                self.parent_page.parent_bar.standard_tool_bar.AddSeparator()
        return item

    def create_button(
        self,
        id,
        title,
        bitmap=None,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        """Create and append a button to this panel.

        Returns:
            StandardToolbarButton: The newly created button.
        """
        b = StandardToolbarButton(self, id, title, bitmap, bitmap_disabled, kind)
        self._append(b)
        return b

    def add_separator(self):
        """Append a visual separator to this panel.

        Returns:
            StandardToolbarButton: The separator button object.
        """
        b = StandardToolbarButton(
            self, 0, "", None, None, kind=ToolbarButton.TYPE_SEPARATOR
        )
        self._append(b)
        return b


class StandardToolbarPage(ToolbarPage):
    """A toolbar page in the standard toolbar."""

    def __init__(self, parent_bar, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        """Initialize the page, adding a separator if not the first.

        Args:
            parent_bar: Parent StandardToolbarBar.
            title: Page title.
            kind: Page type.
        """
        ToolbarPage.__init__(self, parent_bar, title, kind)
        if len(parent_bar.pages) > 0:
            parent_bar.standard_tool_bar.AddSeparator()

    def create_panel(self, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        """Create a panel within this page.

        Returns:
            StandardToolbarPanel: The newly created panel.
        """
        return StandardToolbarPanel(self, title, kind)


class StandardToolbarBar(ToolbarBar):
    """The top-level standard toolbar bar wrapping a wx.ToolBar."""

    def __init__(self, parent, gui_style):
        """Initialize the standard toolbar.

        Args:
            parent: Parent wx.Frame.
            gui_style: GUI style string.
        """
        self.standard_tool_bar = parent.CreateToolBar()
        ToolbarBar.__init__(self, parent, gui_style)

    def create_page(self, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        """Create a new standard toolbar page.

        Returns:
            StandardToolbarPage: The newly created page.
        """
        return StandardToolbarPage(self, title, kind)

    def bind_ui(self, fun, id=wx.ID_ANY):
        """Bind a UI update event handler.

        Args:
            fun: Handler function.
            id: Event identifier.
        """
        self.parent.Bind(wx.EVT_UPDATE_UI, fun, id=id)

    def bind(self, fun, id=wx.ID_ANY, e=None):
        """Bind an event handler to the parent window.

        Args:
            fun: Handler function.
            id: Event identifier.
            e: Event type; defaults to wx.EVT_MENU.
        """
        if e:
            self.parent.Bind(e, fun, id=id)
        else:
            self.parent.Bind(wx.EVT_MENU, fun, id=id)

    def bind_dropdown(self, fun, id):
        """Bind a dropdown menu event handler.

        Args:
            fun: Handler function.
            id: Event identifier.
        """
        self.parent.Bind(wx.EVT_MENU, fun, id=id)

    def un_bind(self, id, e=None):
        """Unbind an event handler from the parent window.

        Args:
            id: Event identifier.
            e: Event type; defaults to wx.EVT_MENU.
        """
        if e:
            self.parent.Unbind(e, id=id)
        else:
            self.parent.Unbind(wx.EVT_MENU, id=id)
