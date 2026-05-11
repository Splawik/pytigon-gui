"""Menu bar toolbar implementation.

Provides a standard wx.MenuBar-based toolbar using the abstract
ToolbarBar/ToolbarPage/ToolbarPanel hierarchy.
"""

import wx

from pytigon_gui.guilib.events import *
from pytigon_gui.toolbar.basetoolbar import (
    ToolbarBar,
    ToolbarPage,
    ToolbarPanel,
    ToolbarButton,
)


class MenuToolbarButton(ToolbarButton, wx.MenuItem):
    """A toolbar button that wraps a wx.MenuItem."""

    def __init__(
        self,
        parent_panel,
        id,
        title,
        bitmap=None,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        """Initialize the menu item button.

        Args:
            parent_panel: Parent wx.Menu (acting as the panel).
            id: Menu item identifier.
            title: Menu item text.
            bitmap: Optional bitmap for the menu item.
            bitmap_disabled: Ignored for menu items.
            kind: Button type (ignored for menu items).
        """
        wx.MenuItem.__init__(self, parentMenu=parent_panel, id=id, text=title)
        if bitmap is not None and bitmap.IsOk():
            self.SetBitmap(bitmap)


class MenuToolbarPanel(ToolbarPanel, wx.Menu):
    """A toolbar panel that wraps a wx.Menu (dropdown or submenu)."""

    def __init__(self, parent_page, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        """Initialize the menu panel.

        Args:
            parent_page: Parent MenuToolbarPage.
            title: Menu title.
            kind: Panel type (defaults to TYPE_PANEL_TOOLBAR).
        """
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
        """Create and append a menu item button to this menu.

        Returns:
            MenuToolbarButton: The newly created menu item.
        """
        b = MenuToolbarButton(self, id, title, bitmap, bitmap_disabled, kind)
        self.Append(b)
        return b


class MenuToolbarPage(ToolbarPage):
    """A toolbar page for the menu bar (essentially a top-level menu)."""

    def __init__(self, parent_bar, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        """Initialize the menu page.

        Args:
            parent_bar: Parent MenuToolbarBar.
            title: Menu title.
            kind: Page type (defaults to TYPE_PAGE_NORMAL).
        """
        ToolbarPage.__init__(self, parent_bar, title, kind)

    def create_panel(self, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        """Create a submenu panel within this menu page.

        Returns:
            MenuToolbarPanel: The newly created menu panel.
        """
        return MenuToolbarPanel(self, title, kind)


class MenuToolbarBar(ToolbarBar, wx.MenuBar):
    """The top-level menu bar, combining ToolbarBar and wx.MenuBar."""

    def __init__(self, parent, gui_style):
        """Initialize the menu bar.

        Args:
            parent: Parent wx.Frame.
            gui_style: GUI style string for standard button creation.
        """
        wx.MenuBar.__init__(self)
        ToolbarBar.__init__(self, parent, gui_style)

    def create_page(self, title, kind):
        """Create a new top-level menu page.

        Returns:
            MenuToolbarPage: The newly created page.
        """
        return MenuToolbarPage(self, title, kind)

    def update_bar(self, obj):
        """Apply this menu bar to the given frame/window.

        Args:
            obj: The wx.Frame to attach the menu bar to.
        """
        obj.SetMenuBar(self)
