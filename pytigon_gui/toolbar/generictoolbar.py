"""Generic (AUI) toolbar implementation.

Provides a toolbar based on wx.lib.agw.aui that supports dockable
toolbar panes with standard button types.
"""

import wx

import wx.lib.agw
import wx.lib.agw.aui as aui
import wx.lib.agw.aui.aui_utilities

from pytigon_gui.guilib.events import *
from pytigon_gui.toolbar.basetoolbar import (
    ToolbarBar,
    ToolbarPage,
    ToolbarPanel,
    ToolbarButton,
)


_ = wx.GetTranslation


class SchAuiToolBarArt(aui.AuiDefaultToolBarArt):
    """Custom AUI toolbar art provider that draws a flat background.

    Uses the system background colour and draws a subtle reflex line
    at the bottom (horizontal) or right edge (vertical).
    """

    def __init__(self):
        super().__init__()
        self._base_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND)

    def draw_background(self, dc, wnd, _rect, horizontal=True):
        """Draw the toolbar background with a reflex border line.

        Args:
            dc: wx.DC to draw on.
            wnd: The toolbar window.
            _rect: Rectangle to fill.
            horizontal: True for horizontal toolbar, False for vertical.
        """
        rect = wx.Rect(*_rect)
        start_colour = self._base_colour
        end_colour = self._base_colour
        reflex_colour = aui.StepColour(self._base_colour, 95)
        dc.GradientFillLinear(
            rect, start_colour, end_colour, (horizontal and [wx.SOUTH] or [wx.EAST])[0]
        )
        left = rect.GetLeft()
        right = rect.GetRight()
        top = rect.GetTop()
        bottom = rect.GetBottom()
        dc.SetPen(wx.Pen(reflex_colour))
        if horizontal:
            dc.DrawLine(left, bottom, right + 1, bottom)
        else:
            dc.DrawLine(right, top, right, bottom + 1)


class GenericToolbarButton(ToolbarButton):
    """AUI-specific toolbar button (thin wrapper around ToolbarButton)."""

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


class GenericToolbarPanel(ToolbarPanel):
    """A panel within an AUI toolbar page that holds a group of buttons."""

    def __init__(self, parent_page, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        ToolbarPanel.__init__(self, parent_page, title, kind)

        if len(parent_page.panels) > 0:
            parent_page.AddStretchSpacer()

    def _append(self, b):
        """Add a ToolbarButton to the underlying AUI toolbar.

        Args:
            b: A GenericToolbarButton to add.

        Returns:
            The AUI tool item or None.
        """
        item = None
        if self.kind in (
            ToolbarPanel.TYPE_PANEL_TOOLBAR,
            ToolbarPanel.TYPE_PANEL_BUTTONBAR,
        ):
            if b.kind == ToolbarButton.TYPE_SIMPLE:
                item = self.parent_page.AddSimpleTool(b.id, b.title, b.bitmap, b.title)
            elif b.kind == ToolbarButton.TYPE_DROPDOWN:
                item = self.parent_page.AddSimpleTool(b.id, b.title, b.bitmap, b.title)
            elif b.kind == ToolbarButton.TYPE_HYBRID:
                item = self.parent_page.AddSimpleTool(b.id, b.title, b.bitmap, b.title)
            elif b.kind == ToolbarButton.TYPE_TOOGLE:
                item = self.parent_page.AddToggleTool(b.id, b.title, b.bitmap)
            elif b.kind == ToolbarButton.TYPE_PANEL:
                pass
            elif b.kind == ToolbarButton.TYPE_SEPARATOR:
                self.parent_page.AddSeparator()
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
            GenericToolbarButton: The newly created button.
        """
        b = GenericToolbarButton(self, id, title, bitmap, bitmap_disabled, kind)
        self._append(b)
        return b

    def add_separator(self):
        """Append a visual separator to this panel.

        Returns:
            GenericToolbarButton: The separator button object.
        """
        b = GenericToolbarButton(
            self, 0, "", None, None, kind=ToolbarButton.TYPE_SEPARATOR
        )
        self._append(b)
        return b


class GenericToolbarPage(ToolbarPage, aui.AuiToolBar):
    """A toolbar page that wraps an AUI AuiToolBar pane."""

    def __init__(self, parent_bar, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        ToolbarPage.__init__(self, parent_bar, title, kind)
        agwStyle = aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_HORZ_LAYOUT
        aui.AuiToolBar.__init__(
            self,
            parent_bar.parent,
            -1,
            wx.DefaultPosition,
            wx.DefaultSize,
            agwStyle=agwStyle,
        )

        self.SetToolBitmapSize(wx.Size(24, 24))
        if wx.Platform != "__WXMSW__":
            self.SetArtProvider(SchAuiToolBarArt())
        nr = len(parent_bar.pages) + 1

        pinfo = (
            parent_bar.parent._create_pane_info("tb" + str(nr), "Toolbar " + str(nr))
            .ToolbarPane()
            .Top()
            .LeftDockable(False)
            .RightDockable(False)
            .Row(1)
        )
        parent_bar.parent._mgr.AddPane(self, pinfo)

    def create_panel(self, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        """Create a panel within this AUI toolbar page.

        Returns:
            GenericToolbarPanel: The newly created panel.
        """
        return GenericToolbarPanel(self, title, kind)


class GenericToolbarBar(ToolbarBar):
    """The top-level AUI toolbar bar managing multiple AUI toolbar pages."""

    def __init__(self, parent, gui_style):
        super().__init__(parent, gui_style)

    def create_page(self, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        """Create a new AUI toolbar page.

        Returns:
            GenericToolbarPage: The newly created page.
        """
        return GenericToolbarPage(self, title, kind)

    def create(self):
        """Realize all toolbar pages and set their best sizes."""
        for bar in self.pages:
            bar.Realize()
            bar.SetSize(bar.GetBestSize())

    def update(self):
        """Update the toolbar layout (no-op for generic toolbar)."""
        pass

    def bind_ui(self, fun, id=wx.ID_ANY):
        """Bind a UI update event handler.

        Args:
            fun: Handler function.
            id: Event identifier.
        """
        self.parent.Bind(wx.EVT_UPDATE_UI, fun, id=id)

    def bind(self, fun, id=wx.ID_ANY, e=None):
        """Bind an event handler to the toolbar's parent window.

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
        """Unbind an event handler from the toolbar's parent window.

        Args:
            id: Event identifier.
            e: Event type; defaults to wx.EVT_MENU.
        """
        if e:
            self.parent.Unbind(e, id=id)
        else:
            self.parent.Unbind(wx.EVT_MENU, id=id)
