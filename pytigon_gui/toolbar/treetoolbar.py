"""Tree-based toolbar implementation.

Provides a vertical tree navigation toolbar using CustomTreeCtrl
from wx.lib.agw.
"""

import wx
from wx.lib.agw import customtreectrl as CT
from wx.lib.agw.ribbon import art

from pytigon_gui.guilib.events import *
from pytigon_gui.toolbar.basetoolbar import (
    BaseHtmlPanel,
    ToolbarBar,
    ToolbarPage,
    ToolbarPanel,
    ToolbarButton,
)
from pytigon_gui.guictrl.basectrl import SchBaseCtrl


_ = wx.GetTranslation


def _tree_list(tree, parent_item, result_list=None):
    """Recursively collect all child items of a tree node into a flat list.

    Args:
        tree: The CustomTreeCtrl instance.
        parent_item: The parent tree item to start from.
        result_list: Optional existing list to append to. If None, a new
            list is created.

    Returns:
        list: Flat list of all child tree items.
    """
    if result_list is None:
        result_list = []

    item, cookie = tree.GetFirstChild(parent_item)
    while item and item.IsOk():
        result_list.append(item)
        if tree.ItemHasChildren(item):
            _tree_list(tree, item, result_list)
        item, cookie = tree.GetNextChild(parent_item, cookie)

    return result_list


class TreeHtmlPanel(BaseHtmlPanel):
    """HTML panel wrapper for the tree toolbar."""

    def get_width(self):
        """Return panel width from the parent tree bar."""
        return self.page.parent_bar.get_bar_width()

    def get_height(self):
        """Return panel height from the parent tree bar."""
        return self.page.parent_bar.get_bar_height()

    def set_page(self, html_page):
        """Set the HTML page within this panel.

        Args:
            html_page: The SchPage to display.
        """
        super().set_page(html_page)


class TreeToolbarButton(ToolbarButton):
    """Tree-specific toolbar button (thin wrapper around ToolbarButton)."""

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


class TreeToolbarPanel(ToolbarPanel):
    """A panel within the tree toolbar that holds a group of tree items."""

    def __init__(self, parent_page, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        """Initialize the tree panel as a child of a tree item.

        Args:
            parent_page: Parent TreeToolbarPage.
            title: Panel title.
            kind: Panel type.
        """
        ToolbarPanel.__init__(self, parent_page, title, kind)
        bar = self.parent_page.parent_bar
        self.tree_item = bar.append_to_tree(parent_page.tree_item, title)

    def _append(self, b):
        """Add a ToolbarButton as a tree item.

        Args:
            b: A TreeToolbarButton to add.

        Returns:
            The tree item or None.
        """
        item = None
        if self.kind in (
            ToolbarPanel.TYPE_PANEL_TOOLBAR,
            ToolbarPanel.TYPE_PANEL_BUTTONBAR,
        ):
            if b.kind == ToolbarButton.TYPE_SIMPLE:
                item = self.parent_page.parent_bar.append_to_tree(
                    self.tree_item, b.title, b.bitmap, ct_type=0
                )
            elif b.kind == ToolbarButton.TYPE_DROPDOWN:
                item = self.parent_page.parent_bar.append_to_tree(
                    self.tree_item, b.title, b.bitmap, ct_type=0
                )
            elif b.kind == ToolbarButton.TYPE_HYBRID:
                item = self.parent_page.parent_bar.append_to_tree(
                    self.tree_item, b.title, b.bitmap, ct_type=0
                )
            elif b.kind == ToolbarButton.TYPE_TOOGLE:
                item = self.parent_page.parent_bar.append_to_tree(
                    self.tree_item, b.title, b.bitmap, ct_type=1
                )
            elif b.kind == ToolbarButton.TYPE_PANEL:
                pass
            elif b.kind == ToolbarButton.TYPE_SEPARATOR:
                item = self.parent_page.parent_bar.AppendSeparator(self.tree_item)

        if item:
            self.parent_page.parent_bar.SetItemHyperText(item, True)
            self.parent_page.parent_bar.SetPyData(item, b.id)

    def create_button(
        self,
        id,
        title,
        bitmap=None,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        """Create and append a button to this tree panel.

        Returns:
            TreeToolbarButton: The newly created button.
        """
        b = TreeToolbarButton(self, id, title, bitmap, bitmap_disabled, kind)
        self._append(b)
        return b

    def add_separator(self):
        """Append a visual separator to this tree panel.

        Returns:
            TreeToolbarButton: The separator button object.
        """
        b = TreeToolbarButton(
            self, 0, "", None, None, kind=ToolbarButton.TYPE_SEPARATOR
        )
        self._append(b)
        return b


class TreeToolbarPage(ToolbarPage):
    """A toolbar page (top-level tree node) in the tree toolbar."""

    def __init__(self, parent_bar, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        """Initialize the tree page.

        Args:
            parent_bar: Parent TreeToolbarBar.
            title: Page title.
            kind: Page type.
        """
        ToolbarPage.__init__(self, parent_bar, title, kind)
        self.tree_item = parent_bar.append_to_tree(parent_bar.tree_main_page, title)

    def create_panel(self, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        """Create a panel within this tree page.

        Returns:
            TreeToolbarPanel: The newly created panel.
        """
        return TreeToolbarPanel(self, title, kind)

    def create_html_panel(self, title):
        """Create an HTML-capable panel within this tree page.

        Args:
            title: Panel title.

        Returns:
            TreeHtmlPanel: The HTML panel wrapper.
        """
        p = wx.Panel(self.parent_bar, size=wx.Size(200, 200))
        self.parent_bar.AppendItem(self.tree_item, title, 0, p)
        self.parent_bar.Expand(self.tree_item)
        return TreeHtmlPanel(self, p)


class TreeToolbarBar(ToolbarBar, CT.CustomTreeCtrl):
    """The top-level tree toolbar bar, displayed as a vertical navigation tree."""

    def __init__(self, parent, gui_style):
        """Initialize the tree toolbar bar.

        Args:
            parent: Parent wx.Frame.
            gui_style: GUI style string.
        """
        agwStyle = (
            CT.TR_HIDE_ROOT
            | CT.TR_HAS_BUTTONS
            | CT.TR_HAS_VARIABLE_ROW_HEIGHT
            | CT.TR_NO_LINES
        )
        CT.CustomTreeCtrl.__init__(self, parent, agwStyle=agwStyle)

        self._indent = 8
        self.tree_main_page = self.AddRoot("The Root Item")
        self.images = wx.ImageList(32, 32)
        self.image_id = 0
        self.show_titles = True

        # Calculate a blended background colour from the system menu colour
        c2 = wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU)
        m = 1.0
        x1 = int((int(c2.Red() * m) + 255) / 2)
        x2 = int((int(c2.Green() * m) + 255) / 2)
        x3 = int((int(c2.Blue() * m) + 255) / 2)
        c = wx.Colour(x1, x2, x3)
        self.bg = c
        self.SetBackgroundColour(c)
        c3 = wx.Colour(0, 0, 0)
        self._hypertextnewcolour = c3
        self._hypertextvisitedcolour = c3

        super().__init__(parent, gui_style)
        self.EnableSelectionVista(True)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(CT.EVT_TREE_ITEM_HYPERLINK, self.on_hyper_link)

        wx.GetApp().GetTopWindow().idle_objects.append(self)

    def append_to_tree(self, parent_elem, title, bitmap=None, ct_type=0):
        """Append a child item to the tree.

        Args:
            parent_elem: Parent tree item.
            title: Display title.
            bitmap: Optional wx.Bitmap; will be rescaled to 32x32 if smaller.
            ct_type: Custom tree item type (0 = normal, 1 = toggle).

        Returns:
            The new tree item.
        """
        if bitmap is not None and bitmap.IsOk():
            if bitmap.GetWidth() < 32 or bitmap.GetHeight() < 32:
                b = wx.Bitmap(bitmap.ConvertToImage().Rescale(32, 32))
            else:
                b = bitmap
            self.images.Add(b)
            item = self.AppendItem(
                parent_elem,
                title if self.show_titles else "",
                image=self.image_id,
                ct_type=ct_type,
            )
            self.image_id += 1
        else:
            item = self.AppendItem(
                parent_elem, title if self.show_titles else "", ct_type=ct_type
            )
        return item

    def create_page(self, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        """Create a new tree toolbar page.

        Returns:
            TreeToolbarPage: The newly created page.
        """
        return TreeToolbarPage(self, title, kind)

    def CanAcceptFocus(self):
        """Return True to indicate this control can accept focus."""
        return True

    def CanAcceptFocusFromKeyboard(self):
        """Return True to indicate this control accepts keyboard focus."""
        return self.CanAcceptFocus()

    def on_close(self, event):
        """Handle the close event by removing from idle objects.

        Args:
            event: wx.CloseEvent.
        """
        if self in wx.GetApp().GetTopWindow().idle_objects:
            wx.GetApp().GetTopWindow().idle_objects.remove(self)
        event.Skip()

    def get_max_width(self, respect_expansion_state=True):
        """Return the maximum width of the tree.

        Args:
            respect_expansion_state: If True, consider expanded items.

        Returns:
            int: Maximum width in pixels.
        """
        return 400

    def realize(self):
        """Realize the tree: assign images, expand, set size."""
        self.AssignImageList(self.images)
        self.ExpandAll()
        self.SetSize((300, 400))

    def on_hyper_link(self, event):
        """Handle a hyperlink click on a tree item.

        Args:
            event: Tree item hyperlink event.
        """
        item = event.GetItem()
        if item:
            wx.CallAfter(self.send_menu_event, item)

    def send_menu_event(self, item):
        """Send a menu event for the given tree item.

        Tries to process the event on this tree first, then falls back
        to the active SchBaseCtrl control.

        Args:
            item: The tree item that was clicked.
        """
        e = wx.CommandEvent(wx.EVT_MENU.typeId, self.GetPyData(item))
        ret = self.ProcessEvent(e)
        if not ret:
            win = wx.GetApp().GetTopWindow().get_active_ctrl()
            if win and isinstance(win, SchBaseCtrl):
                win.ProcessEvent(e)

    def on_idle(self):
        """Handle idle event: update enabled/disabled state of tree items.

        Iterates all tree items and dispatches wx.UpdateUIEvent to determine
        whether each item should be enabled or disabled.
        """
        refresh = False
        for item in _tree_list(self, self.tree_main_page):
            item_id = self.GetPyData(item)
            if item_id:
                if (item_id >= ID_START and item_id < ID_END) or (
                    item_id >= wx.ID_LOWEST and item_id < wx.ID_HIGHEST
                ):
                    event = wx.UpdateUIEvent(item_id)
                    event.Enable(False)
                    event.SetEventObject(self.GetParent())

                    if self.ProcessWindowEvent(event):
                        if item.IsEnabled() != event.GetEnabled():
                            refresh = True
                        item.Enable(event.GetEnabled())
                    else:
                        enable = False
                        win = wx.Window.FindFocus()
                        if win and isinstance(win, SchBaseCtrl):
                            if win.ProcessEvent(event):
                                if event.GetEnabled():
                                    enable = True
                        if enable:
                            if not item.IsEnabled():
                                refresh = True
                            item.Enable(True)
                        else:
                            if item.IsEnabled():
                                refresh = True
                            item.Enable(False)
        if refresh:
            self.Refresh()

    def set_active_page(self, page):
        """Set the active page (no-op for tree toolbar).

        Args:
            page: The page to activate.
        """
        pass

    def get_bar_height(self):
        """Return the preferred height of the tree bar.

        Returns:
            int: Height in pixels.
        """
        return 600

    def get_bar_width(self):
        """Return the preferred width of the tree bar.

        Returns:
            int: Width in pixels.
        """
        return 150

    def remove_page(self, title):
        """Remove a page from the tree toolbar.

        Args:
            title: Title of the page to remove.
        """
        for p in self.pages:
            if p.title == title:
                self.Delete(p.tree_item)
                break
        super().remove_page(title)

    def create(self):
        """Create/realize the tree toolbar."""
        self.AssignImageList(self.images)
        self.ExpandAll()
        self.SetSize((300, 400))

    def close(self):
        """Close/destroy the tree toolbar."""
        self.Close()

    def update(self):
        """Force a layout refresh by briefly resizing the bar."""
        size = self.GetSize()
        width = size.GetWidth()
        if width > 0:
            self.SetSize(wx.Size(width - 1, size.GetHeight()))
        self.SetSize(wx.Size(width, size.GetHeight()))

    def bind_ui(self, fun, id=wx.ID_ANY):
        """Bind a UI update event handler to the parent window.

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
        """Bind a dropdown menu event handler to the parent window.

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
