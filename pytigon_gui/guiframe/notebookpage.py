"""Notebook page container for Pytigon applications.

SchNotebookPage represents one tab within a SchNotebook. It manages
multiple SchPage windows laid out inside a single tab using a custom
split/stack algorithm and supports mouse-driven divider resizing.
"""

import wx

from pytigon_gui.guiframe import page


class SchNotebookPage(wx.Window):
    """One tab in a SchNotebook, hosting one or more SchPage windows."""

    def __init__(self, parent):
        """Initialize the notebook page.

        Args:
            parent: Parent SchNotebook window.
        """
        wx.Window.__init__(
            self,
            parent,
            style=wx.TAB_TRAVERSAL | wx.WANTS_CHARS,
            name="SchNotebookPage",
        )
        try:
            self.SetBackgroundStyle(wx.BG_STYLE_ERASE)
        except Exception:
            self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        self._start_pos = None
        self._start_pos_x_y_dx_dy = None
        self._last_x_y_dx_dy = None
        self._best_x_y_dx_dy = None
        self._layout_style = 0

        self.child_panels = []
        self.bestx = -1
        self.orient = None
        self.http = None
        self.reverse_style = True

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_move)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)

        self.SetWindowStyleFlag(wx.WANTS_CHARS)

    def on_set_focus(self, evt):
        """Delegate focus to the last child page."""
        if self.get_page_count() > 0:
            self.get_page(-1).SetFocus()

    def get_app_http(self):
        """Return the HTTP client associated with this notebook page."""
        return self.http

    # ------------------------------------------------------------------
    # Drawing and hit-test helpers
    # ------------------------------------------------------------------

    def on_erase_background(self, evt):
        """Draw borders between child pages and resize handles."""
        top = wx.GetApp().GetTopWindow()
        if not top:
            return

        dc = wx.ClientDC(self)
        dc.Clear()
        margin = self.get_margins()

        has_desktop = hasattr(top, "desktop")
        tabs_count = len(top.desktop._mgr.GetAllPanes()) if has_desktop else 0
        page_count = self.get_page_count()

        show_border = (
            (page_count > 0 and tabs_count > 2)
            or page_count > 1
            or (top.count_shown_panels(count_toolbars=False) > 1 and page_count > 0)
        )

        if not show_border:
            # Nothing to draw.
            return

        last_page = self.get_page(-1)
        (dx, dy) = last_page.GetSize()
        (x, y) = last_page.GetPosition()
        x -= margin / 2
        y -= margin / 2
        dx += margin
        dy += margin

        parent = self.GetParent()
        if parent.active and parent.GetCurrentPage() == self:
            col = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        else:
            col = wx.SystemSettings.GetColour(wx.SYS_COLOUR_INACTIVEBORDER)
        dc.SetPen(wx.Pen(col, margin))

        # Border rectangle
        dc.DrawLine(int(x), int(y), int(x + dx), int(y))
        dc.DrawLine(int(x + dx), int(y), int(x + dx), int(y + dy))
        dc.DrawLine(int(x), int(y - margin / 2), int(x), int(y + dy))
        dc.DrawLine(int(x), int(y + dy), int(x + dx), int(y + dy))

        # Resize handle lines
        if self._layout_style > 0:
            col = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DSHADOW)
            dc.SetPen(wx.Pen(col, 1))
            self._draw_resize_handles(dc, x, y, dx, dy, margin)

    def _draw_resize_handles(self, dc, x, y, dx, dy, margin):
        """Draw resize handle decorations for layout styles 1-3.

        Args:
            dc: Device context.
            x, y: Top-left corner of the border.
            dx, dy: Width and height of the border rectangle.
            margin: Margin width.
        """
        if self._layout_style in (1, 3):
            # Vertical divider handles
            dc.DrawLine(int(x - margin), int(y), int(x - margin), int(y + dy))
            dc.DrawLine(
                int(x - 5 * margin), int(y),
                int(x - 5 * margin), int(y + dy),
            )
            for i in range(-4, 5, 2):
                dc.DrawLine(
                    int(x - 5 * margin + 2),
                    int(y + dy / 2 + margin * i),
                    int((x - margin) - 1),
                    int(y + dy / 2 + margin * i),
                )
        if self._layout_style in (2, 3):
            # Horizontal divider handles
            dc.DrawLine(int(x), int(y - margin), int(x + dx), int(y - margin))
            dc.DrawLine(
                int(x), int(y - 5 * margin),
                int(x + dx), int(y - 5 * margin),
            )
            for i in range(-4, 5, 2):
                dc.DrawLine(
                    int(x + dx / 2 + margin * i),
                    int(y - 5 * margin + 2),
                    int(x + dx / 2 + margin * i),
                    int((y - margin) - 1),
                )

    # ------------------------------------------------------------------
    # Mouse interaction for splitter resize
    # ------------------------------------------------------------------

    def on_left_down(self, event):
        """Begin splitter drag."""
        self._start_pos = event.GetPosition()
        self._start_pos_x_y_dx_dy = self._last_x_y_dx_dy
        self.SetCursor(wx.Cursor(wx.CURSOR_SIZING))
        self.CaptureMouse()
        event.Skip()

    def on_left_up(self, event):
        """End splitter drag."""
        if self._start_pos:
            self._start_pos = None
            self._start_pos_x_y_dx_dy = None
            self._best_x_y_dx_dy = None
            self.ReleaseMouse()
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        event.Skip()

    def on_move(self, event):
        """Handle mouse movement during splitter drag."""
        if self._start_pos and self._start_pos_x_y_dx_dy:
            pos = event.GetPosition()
            dx = pos[0] - self._start_pos[0]
            dy = pos[1] - self._start_pos[1]
            if self.reverse_style:
                dy = -dy
            self._best_x_y_dx_dy = (
                self._start_pos_x_y_dx_dy[0] + dx,
                self._start_pos_x_y_dx_dy[1] + dy,
                self._start_pos_x_y_dx_dy[2],
                self._start_pos_x_y_dx_dy[3],
            )
            self._layout()
        event.Skip()

    # ------------------------------------------------------------------
    # Layout calculation
    # ------------------------------------------------------------------

    def get_xy(self, size=None, page=-1):
        """Calculate the divider position for two child pages.

        Args:
            size: Size of the container (uses self.GetSize() if None).
            page: Index of the page to measure (default: last page).

        Returns:
            Tuple (x, y, width, height) for the divider position.
        """
        if size is None:
            size = self.GetSize()
        if self._best_x_y_dx_dy:
            return self._best_x_y_dx_dy

        bestx, besty = self.get_page(page).calculate_best_size()
        self.bestx = bestx

        if bestx > size.GetWidth() - 20:
            x = size.GetWidth() / 10
        else:
            x = (size.GetWidth() - 2) - bestx
        if besty > size.GetHeight() - 20:
            y = size.GetHeight() / 10
        else:
            y = (size.GetHeight() - 2) - besty

        self._last_x_y_dx_dy = (x, y, size.GetWidth(), size.GetHeight())
        return self._last_x_y_dx_dy

    def get_margins(self):
        """Return the margin between child windows, in pixels."""
        return 2

    def _set_dimensions(self, page, x, y, width, height, dx, dy):
        """Set the size and position of a child page.

        Respects the ``vertical_position`` attribute of the last child
        panel and the ``reverse_style`` flag.

        Args:
            page: SchPage to resize.
            x, y: Desired position.
            width, height: Desired size.
            dx, dy: Container dimensions.
        """
        if x > 0 and y > 0 and width >= 0 and height >= 0:
            if self.child_panels[-1].vertical_position:
                if self.child_panels[-1].vertical_position == "top":
                    page.SetSize(int(x), int(dy - height - y), int(width), int(height))
                else:
                    page.SetSize(int(x), int(y), int(width), int(height))
            else:
                if self.reverse_style:
                    page.SetSize(int(x), int(dy - height - y), int(width), int(height))
                else:
                    page.SetSize(int(x), int(y), int(width), int(height))

    def _layout(self, size=None):
        """Arrange child pages according to the current layout style.

        Layout styles:
            0: single page fills the container.
            1: two pages split vertically (left/right).
            2: two pages split horizontally (top/bottom).
            3: three or more pages, left column + stacked right.

        Args:
            size: Container size override.
        """
        count = self.get_page_count()
        if count == 0:
            return

        margin = self.get_margins()
        if not size:
            size = self.GetSize()
        if not size:
            return
        dx = size.GetWidth()
        dy = size.GetHeight()

        if count == 1:
            self._layout_style = 0
            self._set_dimensions(
                self.get_page(0),
                margin, margin,
                dx - 2 * margin, dy - 2 * margin,
                dx, dy,
            )
            return

        # Two or more pages
        (x, y, dx2, dy2) = self.get_xy(size)
        if not self._best_x_y_dx_dy:
            if self.bestx >= 0 and x > self.bestx:
                x = self.bestx
            else:
                self.bestx = x
        else:
            self._last_x_y_dx_dy = self._best_x_y_dx_dy

        if count == 2:
            self._layout_two_pages(x, y, dx, dy, margin, dx2, dy2)
        else:
            self._layout_many_pages(count, x, y, dx, dy, margin, dx2, dy2)

        self.Refresh()

    def _layout_two_pages(self, x, y, dx, dy, margin, dx2, dy2):
        """Arrange two child pages (vertical or horizontal split)."""
        # Determine orientation: prefer the orientation that gives
        # more area to the second page.
        if (dx - x) * dy < 2 * ((dy - y) * dx):
            self._layout_style = 1  # left/right
            self._set_dimensions(
                self.get_page(0), margin, margin,
                x - 2 * margin, dy - 2 * margin,
                dx, dy,
            )
            self._set_dimensions(
                self.get_page(1), x + 5 * margin, margin,
                (dx - x) - 6 * margin, dy - 2 * margin,
                dx, dy,
            )
        else:
            self._layout_style = 2  # top/bottom
            self._set_dimensions(
                self.get_page(0), margin, margin,
                dx - 2 * margin, y - 2 * margin,
                dx, dy,
            )
            self._set_dimensions(
                self.get_page(1), margin, y + 5 * margin,
                dx - 2 * margin, (dy - y) - 6 * margin,
                dx, dy,
            )

    def _layout_many_pages(self, count, x, y, dx, dy, margin, dx2, dy2):
        """Arrange three or more child pages.

        Pages 0..count-3 stack vertically on the left.
        Page count-2 sits top-right.
        Page count-1 fills bottom-right.
        """
        self._layout_style = 3
        for i in range(0, count - 2):
            self._set_dimensions(
                self.get_page(i),
                margin,
                margin + (i * dy) / (count - 2),
                x - 2 * margin,
                dy / (count - 2) - 2 * margin,
                dx, dy,
            )
        self._set_dimensions(
            self.get_page(-2),
            x + margin, margin,
            (dx - x) - 2 * margin, y - 2 * margin,
            dx, dy,
        )
        self._set_dimensions(
            self.get_page(-1),
            x + 5 * margin, y + 5 * margin,
            (dx - x) - 6 * margin, (dy - y) - 6 * margin,
            dx, dy,
        )

    # ------------------------------------------------------------------
    # Page management
    # ------------------------------------------------------------------

    def get_page_count(self):
        """Return number of child SchPage windows."""
        return len(self.child_panels)

    def get_page(self, nr):
        """Return a child SchPage by index.

        Args:
            nr: Index of the page (supports negative indexing).

        Returns:
            SchPage instance.
        """
        return self.child_panels[nr]

    def add_page(self, page):
        """Append a child SchPage to this notebook page.

        If the new page has ``disable_parent`` set and there are
        existing pages, the last existing page's forms are disabled.

        Args:
            page: The SchPage to add.
        """
        if self.get_page_count() > 0:
            if page.disable_parent:
                self.get_page(-1).enable_forms(False)
        self.child_panels.append(page)
        self._layout()

    def on_size(self, event):
        """Re-layout children when the container is resized."""
        size = event.GetSize()
        self.bestx = -1
        if size:
            wx.CallAfter(self._layout, size)
        event.Skip()

    # ------------------------------------------------------------------
    # Close / cancel / ok lifecycle
    # ------------------------------------------------------------------

    def close_no_del(self, close_without_refresh=True):
        """Close the last child page without destroying this container.

        Args:
            close_without_refresh: If True, signal 'child_canceled';
                otherwise signal 'child_closed_with_ok'.

        Returns:
            True if the close was handled (more pages remain or vetoed),
            False if this container itself should be closed.
        """
        count = self.get_page_count()
        if count == 0:
            return False

        win = self.get_page(-1)
        if not win.CanClose():
            return True

        del self.child_panels[-1]
        if count > 1:
            self.get_page(-1).enable_forms(True)
            self._layout()
            self.get_page(-1).set_focus()
            if close_without_refresh:
                self.get_page(-1).signal("child_canceled", win)
            else:
                self.get_page(-1).signal("child_closed_with_ok", win)
            win.Destroy()
            return True

        win.Destroy()
        return False

    def close_child_page(self, close_without_refresh=True):
        """Close the last child page; remove this tab if it was the only page.

        Args:
            close_without_refresh: Forwarded to :meth:`close_no_del`.

        Returns:
            Result of :meth:`close_no_del`.
        """
        parent = self.GetParent()
        pages = parent._tabs._pages
        for i, page_info in enumerate(pages):
            if page_info.window == self:
                ret = self.close_no_del(close_without_refresh)
                if not ret:
                    parent.DeletePage(i)
                return ret
        return False

    def on_child_form_ok(self):
        """Called by child SchForm when OK is pushed.

        Closes the child and refreshes the parent form.
        """
        self.close_child_page(False)

    def on_child_form_cancel(self):
        """Called by child SchForm when Cancel is pushed.

        Closes the child without refreshing the parent.
        """
        self.close_child_page(True)

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------

    def activate_page(self):
        """Activate the last child page."""
        if self.get_page_count() > 0:
            self.get_page(-1).activate_page()
        else:
            self.SetFocus()

    def deactivate_page(self):
        """Deactivate the last child page."""
        if self.get_page_count() > 0:
            self.get_page(-1).deactivate_page()

    # ------------------------------------------------------------------
    # Creating new pages
    # ------------------------------------------------------------------

    def new_child_page(
        self, address_or_parser, title="", parameters=None, callback=None
    ):
        """Append a new SchPage as a child of this notebook page.

        Args:
            address_or_parser: HTTP address (str) or ShtmlParser instance.
            title: Caption for the new page.
            parameters: Dictionary of request parameters.
            callback: Optional callback invoked after init.

        Returns:
            The created SchPage.
        """
        h = page.SchPage(self, address_or_parser, parameters)
        if self.get_page_count() > 0:
            h.parent_page = self.get_page(-1)

        nr = 0
        if h.header is not None:
            nr += 4
        if h.footer is not None:
            nr += 2
        if h.panel is not None:
            nr += 1

        title2 = title if title else h.get_title()
        self.add_page(h)

        def init_page():
            nonlocal h, callback
            h.init_frame(callback)
            h.activate_page()
            top = wx.GetApp().GetTopWindow()
            if top:
                top._mgr.GetPane("desktop").Show()
            h.Update()

        wx.CallAfter(init_page)
        return h

    def new_main_page(self, address_or_parser, title="", parameters=None, view_in=None):
        """Create a new top-level page in a specific pane.

        Delegates to the application frame's ``new_main_page``.

        Args:
            address_or_parser: HTTP address (str) or ShtmlParser instance.
            title: Caption for the new page.
            parameters: Dictionary of request parameters.
            view_in: Pane name ('desktop', 'panel', 'header', 'footer').

        Returns:
            Result of the application frame's new_main_page.
        """
        top = wx.GetApp().GetTopWindow()
        if view_in is None:
            pp = top._mgr.GetPane(self.GetParent())
            return top.new_main_page(
                address_or_parser, title, parameters, pp.name
            )
        return top.new_main_page(
            address_or_parser, title, parameters, view_in
        )
