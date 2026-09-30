"""
Grid widget classes for the SchForm GUI framework.

Provides wxPython grid/table controls integrated with SchBaseCtrl:
table grid, data grid, and update-grid-button.

Classes:
    TABLE, GRID, UPDATEGRIDBUTTON
"""

import logging

import wx

logger = logging.getLogger(__name__)

from pytigon_gui.guictrl.basectrl import SchBaseCtrl
from pytigon_gui.guictrl.grid import grid, gridtable_from_proxy, tabproxy
from pytigon_gui.guictrl.grid.gridpanel import SchGridPanel
from pytigon_gui.guictrl.grid.gridtable_from_html_table import SimpleDataTable
from pytigon_gui.guilib.threads import block_http_pumping
from pytigon_lib.schhtml.htmlviewer import tdata_from_html
from pytigon_lib.schtools import createparm


class TABLE(SchGridPanel, SchBaseCtrl):
    """Table grid panel for viewing/editing HTML table data.

    Handles ctrltable tag. Renders data from tdata as a grid
    with toolbar actions. Supports row insert/update/delete
    signals and server-side data refresh.

    Tag arguments:
        value: Not directly used.
        table_lp: Table layout parameter (from param).
        no_actions: If in param, hides action toolbar buttons.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)

        if self.param and "table_lp" in self.param:
            self._table_lp = int(self.param["table_lp"])
        else:
            self._table_lp = 0

        name = kwds.get("name", "LIST")

        if "size" in kwds:
            SchGridPanel.__init__(self, parent, size=kwds["size"], name=name)
        else:
            SchGridPanel.__init__(self, parent, name=name)

        tdata = self.get_tdata()
        if not tdata:
            logger.debug(
                "no tdata for table: href=%s src=%s (empty table)",
                self.href,
                self.src,
            )
        if tdata:
            table = SimpleDataTable(self, tdata)
            if self.param and "no_actions" in self.param:
                table.set_no_actions(True)
        else:
            table = None

        self.grid = grid.SchTableGrid(
            table,
            "",
            self,
            typ=grid.SchTableGrid.VIEW,
            style=wx.TAB_TRAVERSAL | wx.FULL_REPAINT_ON_RESIZE,
        )
        self.create_toolbar(self.grid)
        # A wx.Panel never receives EVT_CLOSE; it is only destroyed.
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_close)
        self._table = table
        for signal_name in ("update_row_ok", "new_row_ok", "delete_row_ok"):
            self.get_parent_page().register_signal(self, signal_name)

    def get_table_lp(self):
        return self._table_lp

    def set_table_lp(self, table_lp):
        self._table_lp = table_lp

    table_lp = property(get_table_lp, set_table_lp)

    def _on_close(self, event):
        """Unregister signals when the panel is destroyed.

        Args:
            event: wx.WindowDestroyEvent.
        """
        page = self.get_parent_page()
        if page:
            for signal_name in ("update_row_ok", "new_row_ok", "delete_row_ok"):
                page.unregister_signal(self, signal_name)
        event.Skip()

    def delete_row_ok(self, data):
        """Handle delete_row_ok signal.

        Hides the current row and moves cursor appropriately.

        Args:
            data: Delete signal data (unused).

        Returns:
            True.
        """
        row_id = self.grid.GetGridCursorRow()
        self.grid.HideRow(row_id)
        row_id += 1
        if row_id >= self.grid.GetNumberRows():
            self.grid.goto_last_row()
        else:
            self.grid.SetGridCursor(row_id, 0)
            self.grid.MakeCellVisible(row_id, 0)
        return True

    def update_row_ok(self, data):
        """Handle update_row_ok signal."""
        return self._row_ok(data, insert=False)

    def new_row_ok(self, data):
        """Handle new_row_ok signal."""
        return self._row_ok(data, insert=True)

    def _row_ok(self, data, insert=False):
        """Fetch updated row data from server and refresh grid.

        Args:
            data: Signal data with 'id' or 'pk' key.
            insert: If True, appends a new row; else updates existing.

        Returns:
            True if successful, None otherwise.
        """
        url = self.GetParent().address
        if not url:
            return None
        pk = data.get("id", data.get("pk"))
        if "?" in url:
            url += "&pk=" + str(pk)
        else:
            url += "?pk=" + str(pk)
        http = wx.GetApp().get_http(self)
        with block_http_pumping():
            response = http.get(self, url)
        if response.ret_code == 404:
            return None
        data = response.str()
        tdatabuf = tdata_from_html(data, wx.GetApp().http)
        if len(tdatabuf) == 2:
            row = tdatabuf[1]
            if insert:
                count = self.grid.GetNumberRows()
                self.grid.GetTable().append_row(row)
                self.grid.GetTable().refr_count(count + 1, False)
                self.grid.GetTable().GetView().ForceRefresh()
                self.grid.goto_last_row()
            else:
                row_id = self.grid.GetGridCursorRow()
                self.grid.GetTable().set_rec(row_id, row)
                self.grid.GetTable().GetView().ForceRefresh()
                self.grid.MakeCellVisible(self.grid.GetGridCursorRow(), 0)
            return True
        return None

    def GetMinSize(self):
        return SchGridPanel.GetMinSize(self)

    def process_refr_data(self, **kwds):
        """Refresh the table with new data.

        Args:
            **kwds: New keyword arguments.

        Returns:
            Result from do_refresh.
        """
        self.grid.last_action = ""
        self.init_base(kwds)
        tdata = self.get_tdata()
        return self.do_refresh(tdata)

    def do_refresh(self, tdata):
        """Replace table data and restore cursor position.

        Args:
            tdata: New table data to display.
        """
        oldRow = self.grid.GetGridCursorRow()
        self._table.replace_tab(tdata)
        if self.grid.last_action == "insert":
            newRow = self.grid.GetGridCursorRow() + 1
            if newRow < self.grid.GetTable().GetNumberRows():
                self.grid.SetGridCursor(newRow, 0)
                self.grid.MakeCellVisible(newRow, 0)
        else:
            if oldRow < self.grid.GetTable().GetNumberRows():
                if oldRow < 0:
                    oldRow = 0
                self.grid.SetGridCursor(oldRow, 0)
                self.grid.MakeCellVisible(oldRow, 0)
            else:
                self.grid.goto_last_row()

    def refresh_from_source(self, html_src):
        """Refresh table from raw HTML source.

        Args:
            html_src: Raw HTML containing table data.

        Returns:
            Result from do_refresh.
        """
        self.refresh_tdata(html_src)
        tdata = self.get_tdata()
        return self.do_refresh(tdata)


class GRID(grid.SchTableGrid, SchBaseCtrl):
    """Data-bound grid connected to a server data proxy.

    Handles ctrlgrid tag. Uses a DataProxy to fetch and display
    paginated server data. Supports readonly mode and auto-refresh
    on parent parameter changes.

    Tag arguments:
        value: Not directly used.
        src: Data source URL.
        readonly: If True, grid is read-only.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        table = gridtable_from_proxy.DataSource(self._create_proxy(parent, self.src))

        if self.readonly:
            kwds["typ"] = self.VIEW
            table.set_read_only(True)
        else:
            table.set_read_only(False)

        super().__init__(table, self.src, parent, **kwds)

    @staticmethod
    def _create_proxy(parent, src):
        """Build a DataProxy for *src*, degrading to an empty one on failure.

        The proxy performs an HTTP request in its constructor.  A failure
        there would otherwise propagate out of the widget constructor and
        abort the surrounding HTML parse, so it is logged and an empty proxy
        is returned instead.

        Args:
            parent: Window used to look up the application's http client.
            src: Data source URL, possibly with ``createparm`` placeholders.

        Returns:
            A :class:`~pytigon_gui.guictrl.grid.tabproxy.DataProxy`, or a
            :class:`~pytigon_gui.guictrl.grid.tabproxy.NullProxy` on failure.
        """
        try:
            parm = createparm.create_parm(src, parent.get_parm_obj())
            if parm:
                proxy = tabproxy.DataProxy(wx.GetApp().get_http(parent), str(parm[0]))
                proxy.set_address_parm(parm[2])
            else:
                proxy = tabproxy.DataProxy(wx.GetApp().get_http(parent), str(src))
        except Exception:
            logger.exception("Failed to create grid data proxy for %s", src)
            return tabproxy.NullProxy(str(src))
        return proxy

    def process_refr_data(self, **kwds):
        """Refresh grid with new data source.

        Args:
            **kwds: New keyword arguments.
        """
        self.init_base(kwds)

        proxy = self._create_proxy(self.GetParent(), self.src)
        self.proxy = proxy
        table = gridtable_from_proxy.DataSource(proxy)
        self.SetTable(table)

    def refr_obj(self):
        """Refresh grid if parent is visible and parameters changed."""
        if self.GetParent().IsShown():
            parm = createparm.create_parm(self.src, self.GetParent().get_parm_obj())
            if parm:
                if self.proxy.set_address_parm(parm[2]):
                    self.GetTable().refresh(False)

    def OnSize(self, event=None):
        """Handle resize event, adjusting height for toolbar.

        Args:
            event: wx.SizeEvent or None.
        """
        if event is not None:
            size = event.GetSize()
            old = self.GetSize()
            if old[1] != size[1] - 8:
                self.SetSize((size[0], max(0, size[1] - 8)))
                self.GetParent().RefrPage()
            event.Skip()


class UPDATEGRIDBUTTON(wx.Button, SchBaseCtrl):
    """Button that submits form data to update a parent grid.

    Handles ctrlupdategridbutton tag. Collects values from all
    sibling controls and sends them to the parent grid's
    OnUpRecFromForm method.

    Tag arguments:
        value: Not directly used.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.Button.__init__(self, parent, **kwds)
        self.Bind(wx.EVT_BUTTON, self._on_click)

    def _on_click(self, event):
        """Collect form values and push them into the parent grid.

        Args:
            event: Button click event.
        """
        grid_ctrl = self.get_parent_grid()
        if grid_ctrl is None:
            logger.warning("no parent grid found for %s", self.get_unique_name())
            return

        table = grid_ctrl.GetTable()
        # on_update_rec_from_form is written for the +1 primary-key offset used
        # by gridtable_from_proxy.DataSource. SimpleDataTable (ctrl-table) is
        # 0-based and its SetValue would overwrite the Td cell objects.
        if not isinstance(table, gridtable_from_proxy.DataSource):
            logger.warning(
                "on_update_rec_from_form is not supported for %s",
                type(table).__name__,
            )
            return

        page = self.get_parent_form().get_parent_page()
        row = grid_ctrl.GetGridCursorRow()
        rec = {}
        for i, name in enumerate(table.GetColNames()[1:], start=1):
            ctrl = page.get_item(name)
            if ctrl is not None:
                rec[name] = ctrl.get_form_value()
            else:
                # keep the grid's current value for columns the form omits
                rec[name] = table.GetValue(row, i)
        grid_ctrl.on_update_rec_from_form(rec)
        table.commit()
        self.GetParent().any_parent_command("on_child_form_cancel")

    def get_parent_grid(self):
        """Return the SchTableGrid on the page above this button's form.

        Returns:
            The parent grid widget, or None if the button is not on a child
            page or no grid exists on the parent page.
        """
        form = self.get_parent_form()
        page = form.get_gparent_page() if form is not None else None
        if page is None:
            return None
        for ctrl in page.get_widgets().values():
            if isinstance(ctrl, grid.SchTableGrid):
                return ctrl
            inner = getattr(ctrl, "grid", None)
            if isinstance(inner, grid.SchTableGrid):
                return inner
        return None
