"""Popup cell editor classes for grid cells.

Provides wx.Grid cell editors that use server-backed DataPopupControl
for data selection within grid cells: generic popup, date picker,
list picker, and a base popup data editor.
"""

import string
import datetime

import wx
from wx.grid import GridCellEditor

from pytigon_gui.guictrl.popup import popuphtml
from pytigon_lib.schtools import schjson


class PopupDataCellControl(popuphtml.DataPopupControl):
    """Thin wrapper around DataPopupControl for use as a grid cell control."""

    def __init__(self, href, *args, **kwds):
        """Initialize with a server URL.

        Args:
            href: Server URL for the popup endpoint.
            *args: Positional arguments for DataPopupControl.
            **kwds: Keyword arguments for DataPopupControl.
        """
        self.href = href
        self.defaultvalue = None
        popuphtml.DataPopupControl.__init__(self, *args, **kwds)


class PopupDataCellEditor(GridCellEditor):
    """Grid cell editor using a server-backed DataPopupControl.

    Provides inline editing for grid cells that need data lookup
    via server endpoints. The address can be set via property or
    parameters.
    """

    def __init__(self):
        """Initialize the editor with no address or params."""
        GridCellEditor.__init__(self)
        self.address = None
        self.param = None

    def get_address(self):
        """Return the server address for data lookup."""
        return self._address

    def set_address(self, address):
        """Set the server address.

        Args:
            address: URL string for the data endpoint.
        """
        self._address = address

    address = property(get_address, set_address)

    def Create(self, parent, id, evt_handler):
        """Create the cell editor control.

        Args:
            parent: Parent window.
            id: Window ID.
            evt_handler: Event handler for focus events.
        """
        self.Parent = parent
        self._tc = PopupDataCellControl(self.address, parent, id)
        self._tc.DismissObject = self
        self.SetControl(self._tc)
        self.evtHandler = evt_handler

        if evt_handler:
            self._tc.PushEventHandler(self.evtHandler)
            evt_handler.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

    def on_kill_focus(self, event):
        """Handle kill-focus event (no-op)."""

    def SetSize(self, rect):
        """Set the size of the editor control.

        Args:
            rect: wx.Rect defining position and size.
        """
        self._tc.SetSize(
            rect.x, rect.y, rect.width + 2, rect.height + 2, wx.SIZE_ALLOW_MINUS_ONE
        )

    def Show(self, show, attr):
        """Show or hide the editor.

        Args:
            show: Boolean visibility flag.
            attr: Cell attributes.
        """
        GridCellEditor.Show(self, show, attr)

    def PaintBackground(self, rect, attr):
        """No-op background paint for the editor."""

    def BeginEdit(self, row, col, grid):
        """Begin editing a cell.

        Args:
            row: Grid row index.
            col: Grid column index.
            grid: The parent wx.Grid.
        """
        self.grid = grid
        self.start_value = None
        value = grid.GetTable().GetValue(row, col)

        if isinstance(value, datetime.date):
            self.start_value = value.isoformat()
        elif isinstance(value, str):
            self.start_value = value
        else:
            self.start_value = str(value)

        self._tc.focus_in(self.start_value)
        if self.start_value:
            self._tc.set_rec(self.start_value, (self.start_value,))
        self._tc.SetInsertionPointEnd()
        self._tc.GetTextCtrl().SetSelection(0, -1)
        self._tc.GetTextCtrl().SetFocus()

    def EndEdit(self, row, col, grid, old_value):
        """End editing and commit changes if value changed.

        Args:
            row: Grid row index.
            col: Grid column index.
            grid: The parent wx.Grid.
            old_value: The previous cell value.

        Returns:
            True if the value changed, False otherwise.
        """
        self._tc.focus_out(self._tc.GetValue())
        changed = False
        value = self._tc.GetValue()
        if str(value) != str(self.start_value):
            changed = True
            grid.GetTable().SetValue(row, col, value)
        grid.SetFocus()
        return changed

    def ApplyEdit(self, row, col, grid):
        """Apply the edit value to the table.

        Args:
            row: Grid row index.
            col: Grid column index.
            grid: The parent wx.Grid.
        """
        val = self._tc.GetValue()
        grid.GetTable().SetValue(row, col, val)
        self.start_value = ""
        self._tc.SetValue("")

    def Reset(self):
        """Reset the editor to the initial value."""
        self._tc.SetValue(self.start_value)

    def IsAcceptedKey(self, evt):
        """Check if a key event should start cell editing.

        Args:
            evt: wx.KeyEvent.

        Returns:
            True if the key is accepted for starting edit.
        """
        return (
            not (evt.ControlDown() or evt.AltDown())
            and evt.GetKeyCode() != wx.WXK_SHIFT
        )

    def StartingKey(self, evt):
        """Handle the initiating keystroke for cell editing.

        Args:
            evt: wx.KeyEvent.
        """
        key = evt.GetKeyCode()
        ch = None
        if 0 <= key < 256 and chr(key) in string.printable:
            ch = chr(key)
        if ch is not None:
            self._tc.start_value = ""
            self._tc.SetValue(ch)
            if self._tc.popup:
                self._tc.popup.set_string_value(ch)
            self._tc.rec_value = (ch,)
            if self._tc.popup:
                self._tc.popup.Dismiss()
            self._tc.SetInsertionPointEnd()
        else:
            evt.Skip()

    def StartingClick(self):
        """Handle click to start editing (no-op)."""

    def Clone(self):
        """Return a copy of this editor.

        Returns:
            A new PopupDataCellEditor instance.
        """
        ret = PopupDataCellEditor()
        ret.SetParameters(self.param)
        return ret

    def set_parameters(self, params):
        """Set editor parameters.

        Args:
            params: Parameter dict or value.
        """
        self.param = params


class DatePopupDataCellEditor(PopupDataCellEditor):
    """Date picker cell editor with masked input format.

    Uses the server's datedialog endpoint with a masked text control
    for YYYY-MM-DD date entry.
    """

    def __init__(self):
        """Initialize with the datedialog server endpoint."""
        PopupDataCellEditor.__init__(self)
        self.address = wx.GetApp().make_href("/schsys/datedialog/")

    def Create(self, parent, id, evt_handler):
        """Create the editor and set masked date format.

        Args:
            parent: Parent window.
            id: Window ID.
            evt_handler: Event handler.
        """
        PopupDataCellEditor.Create(self, parent, id, evt_handler)
        self._tc.to_masked(autoformat="EUDATEYYYYMMDD.")

    def Clone(self):
        """Return a copy of this date editor.

        Returns:
            A new DatePopupDataCellEditor instance.
        """
        ret = DatePopupDataCellEditor()
        ret.address = self.address
        ret.SetParameters(self.param)
        return ret


class ListPopupCellEditor(PopupDataCellEditor):
    """List picker cell editor that loads choices from the cell type.

    Parses a JSON-encoded choice list from the cell's type name
    and presents it in the popup dialog for selection.
    """

    def __init__(self):
        """Initialize with the listdialog server endpoint."""
        PopupDataCellEditor.__init__(self)
        self.address = wx.GetApp().make_href("/schsys/listdialog/")

    def Create(self, parent, id, evt_handler):
        """Create the editor and set the event object.

        Args:
            parent: Parent window.
            id: Window ID.
            evt_handler: Event handler.
        """
        PopupDataCellEditor.Create(self, parent, id, evt_handler)
        self._tc.SetEventObject(self)

    def Clone(self):
        """Return a copy of this list editor.

        Returns:
            A new ListPopupCellEditor instance.
        """
        ret = ListPopupCellEditor()
        ret.address = self.address
        ret.SetParameters(self.param)
        return ret

    def BeginEdit(self, row, col, grid):
        """Begin editing: parse choice list from cell type name.

        Args:
            row: Grid row index.
            col: Grid column index.
            grid: The parent wx.Grid.
        """
        typ = grid.GetTable().GetTypeName(row, col)
        sep = typ.find(":")
        self.choices = schjson.loads(typ[sep + 1 :])
        PopupDataCellEditor.BeginEdit(self, row, col, grid)

    def OnButtonClick(self):
        """Populate the popup dialog with parsed choices."""
        if self._tc.simpleDialog:
            self._tc.popup.html.choices = self.choices
            self._tc.popup.html.refr()
        else:
            self._tc.page.body.choices = self.choices
            self._tc.page.body.refr()

    def set_rec(self, value, value_rec, dismiss=True):
        """Match typed value against choice list.

        Args:
            value: Typed value to match.
            value_rec: Record object.
            dismiss: Dismiss popup after setting.

        Returns:
            Matched 'id:name' string, or empty string.
        """
        if len(value) > 2 and value[1] == ":":
            return value
        for choice in self.choices:
            if choice[1].lower().startswith(value.lower()):
                return choice[0] + ":" + choice[1]
        return ""


class GenericPopupCellEditor(PopupDataCellEditor):
    """Generic popup cell editor with configurable server endpoint.

    The address is set via set_parameters, allowing reuse across
    different data types.
    """

    def __init__(self):
        """Initialize with a default datedialog endpoint."""
        PopupDataCellEditor.__init__(self)
        self.address = wx.GetApp().make_href("/schsys/datedialog/")

    def Clone(self):
        """Return a copy of this editor.

        Returns:
            A new GenericPopupCellEditor instance.
        """
        ret = GenericPopupCellEditor()
        ret.SetParameters(self.address)
        return ret

    def set_parameters(self, params):
        """Set the server address from parameters.

        Args:
            params: URL string for the data endpoint.
        """
        self.address = params
