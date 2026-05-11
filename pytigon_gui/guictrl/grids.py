"""
Grid widget classes for the SchForm GUI framework.

Provides wxPython grid/table controls integrated with SchBaseCtrl:
table grid, data grid, and update-grid-button.

Classes:
    TABLE, GRID, UPDATEGRIDBUTTON
"""

import wx
import logging

logger = logging.getLogger(__name__)

from pytigon_gui.guictrl.basectrl import SchBaseCtrl
from pytigon_gui.guictrl.grid import grid, gridtable_from_proxy, tabproxy
from pytigon_gui.guictrl.grid.gridtable_from_html_table import SimpleDataTable
from pytigon_gui.guictrl.grid.gridpanel import SchGridPanel
from pytigon_lib.schtools import createparm
from pytigon_lib.schhtml.htmlviewer import tdata_from_html


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
            logger.warning("no tdata: href=%s src=%s", self.href, self.src)
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
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self._table = table
        for signal_name in ("update_row_ok", "new_row_ok", "delete_row_ok"):
            self.get_parent_page().register_signal(self, signal_name)

    def get_table_lp(self):
        return self._table_lp

    def set_table_lp(self, table_lp):
        self._table_lp = table_lp

    table_lp = property(get_table_lp, set_table_lp)

    def _on_close(self, event):
        """Unregister signals on close."""
        for signal_name in ("update_row_ok", "new_row_ok", "delete_row_ok"):
            self.get_parent_page().unregister_signal(self, signal_name)
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
        parm = createparm.create_parm(self.src, parent.get_parm_obj())
        if parm:
            self.proxy = tabproxy.DataProxy(wx.GetApp().get_http(parent), str(parm[0]))
            self.proxy.set_address_parm(parm[2])
        else:
            self.proxy = tabproxy.DataProxy(wx.GetApp().get_http(parent), str(self.src))
        table = gridtable_from_proxy.DataSource(self.proxy)

        if self.readonly:
            kwds["typ"] = self.VIEW
            table.set_read_only(True)
        else:
            table.set_read_only(False)

        super().__init__(table, self.src, parent, **kwds)

    def process_refr_data(self, **kwds):
        """Refresh grid with new data source.

        Args:
            **kwds: New keyword arguments.
        """
        self.init_base(kwds)

        parm = createparm.create_parm(self.src, self.GetParent().get_parm_obj())
        if parm:
            self.proxy = tabproxy.DataProxy(wx.GetApp().get_http(self), str(parm[0]))
            self.proxy.SetAddressParm(parm[2])
        else:
            self.proxy = tabproxy.DataProxy(wx.GetApp().get_http(self), str(self.src))
        table = gridtable_from_proxy.DataSource(self.proxy)
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
                self.SetSize((size[0], size[1] - 8))
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
        """Collect form values and update parent grid.

        Args:
            event: Button click event.
        """
        rec = {}
        keys = list(self.GetParent().GetWidgets().keys())
        for k in keys:
            ctrl = self.GetParent().GetItem(k)
            if hasattr(ctrl, "GetValue"):
                rec[k] = ctrl.GetValue()
        self.GetParent().GetPrevWin().ActiveCtrl.OnUpRecFromForm(rec)
        self.GetParent().any_parent_command("OnCancel", None)
