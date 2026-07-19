"""
Choice/selection widget classes for the SchForm GUI framework.

Provides wxPython selection controls integrated with SchBaseCtrl:
checkbox, checklistbox, listbox, list control, radiobox, radio button.

Classes:
    CHECKBOX, CHECKLISTBOX, LISTBOX, LIST, CHECKLIST, RADIOBOX, RADIOBUTTON
"""

import wx

from pytigon_gui.guictrl.basectrl import SchBaseCtrl, handle_best_size


class CHECKBOX(wx.CheckBox, SchBaseCtrl):
    """Checkbox control with optional custom value.

    Handles ctrlcheckbox tag. When the checkbox is checked,
    GetValue returns either the configured custom value or True.
    When unchecked, returns None.

    Tag arguments:
        checked: If present, initializes the checkbox as checked.
        value: Custom value returned when checked (instead of True).
        label: Checkbox label text.
    """

    def __init__(self, parent, **kwds):
        """Initialize the checkbox control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.CheckBox. If 'checked' is
                present, the checkbox starts checked. If no label
                is provided, adds ALIGN_RIGHT style.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if "checked" in kwds:
            del kwds["checked"]
            checked = True
        else:
            checked = False

        if self.label:
            kwds["label"] = self.label

        if "value" in kwds:
            self.value = kwds["value"]
            del kwds["value"]
        else:
            self.value = None

        if not self.label:
            if "style" in kwds:
                kwds["style"] |= wx.ALIGN_RIGHT
            else:
                kwds["style"] = wx.ALIGN_RIGHT

        wx.CheckBox.__init__(self, parent, **kwds)
        if checked:
            self.SetValue(True)

    def process_refr_data(self, **kwds):
        """Refresh the checkbox with new data.

        Args:
            **kwds: New keyword arguments. Supports 'checked'
                and 'value' keys.
        """
        self.init_base(kwds)
        if "checked" in kwds:
            del kwds["checked"]
            checked = True
        else:
            checked = False
        if "value" in kwds:
            self.value = kwds["value"]
            del kwds["value"]
        else:
            self.value = None

        if checked:
            self.SetValue(True)

    def GetValue(self):
        """Get the current checkbox value.

        Returns:
            If checked and a custom value is set, returns str(value).
            If checked and no custom value, returns True.
            If unchecked, returns None.
        """
        checked = wx.CheckBox.GetValue(self)
        if checked:
            if self.value:
                return str(self.value)
            else:
                return True
        else:
            return None

    def SetValue(self, value):
        """Set the checkbox state.

        Args:
            value: If bool, sets the check state directly.
                Otherwise stores as the custom value.
        """
        if isinstance(value, bool):
            return wx.CheckBox.SetValue(self, value)
        else:
            self.value = value


@handle_best_size
class CHECKLISTBOX(wx.CheckListBox, SchBaseCtrl):
    """Check list box allowing multiple selections with checkboxes.

    Handles ctrlchecklistbox tag. Provides a list where each item
    has an associated checkbox. GetValue returns a list of values
    for checked items.

    Tag arguments:
        checked: Pre-checked items.
        value: Custom values for items.
        label: Control label.
    """

    def __init__(self, parent, **kwds):
        """Initialize the check list box.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.CheckListBox with WANTS_CHARS style.
        """
        SchBaseCtrl.__init__(self, parent, kwds)

        if "style" in kwds:
            kwds["style"] |= wx.WANTS_CHARS
        else:
            kwds["style"] = wx.WANTS_CHARS
        wx.CheckListBox.__init__(self, parent, **kwds)
        self._init_data(self.get_tdata())

    def _init_data(self, data):
        """Populate the list from tdata.

        Items with 'selected' in their attrs are pre-checked.

        Args:
            data: List of rows from tdata, each row[0] being a Td object.
        """
        checked_items = []
        if data:
            for row in data:
                item_id = self.Append(row[0].data)
                if "selected" in row[0].attrs:
                    checked_items.append(item_id)
        if checked_items:
            self.SetCheckedItems(checked_items)

    def process_refr_data(self, **kwds):
        """Refresh the list with new data.

        Args:
            **kwds: New keyword arguments.
        """
        self.init_base(kwds)
        self.Clear()
        self._init_data(self.get_tdata())

    def GetBestSize(self):
        """Return the best size for the control.

        Returns:
            Tuple of (300, 68).
        """
        return (300, 68)

    def GetMinSize(self):
        """Return the minimum size (same as best size).

        Returns:
            Tuple of (300, 68).
        """
        return self.GetBestSize()

    def GetValue(self):
        """Get values of all checked items.

        Returns:
            List of values for checked items. Uses the 'value'
            attribute from item attrs if present, otherwise the
            item's display text.
        """
        ret = []
        data = self.get_tdata()
        items = self.GetCheckedItems()
        for item in items:
            if hasattr(data[item][0], "attrs") and "value" in data[item][0].attrs:
                ret.append(data[item][0].attrs["value"])
            else:
                ret.append(data[item][0].data)
        return ret


class LISTBOX(wx.ListBox, SchBaseCtrl):
    """Standard list box for single or multiple selection.

    Handles ctrllistbox tag. Supports multiple selection mode
    via the 'multiple' parameter. Tracks selected items and
    their associated values.

    Tag arguments:
        value: Initial selection value.
        multiple: If set in param, enables LB_MULTIPLE style.
    """

    def __init__(self, parent, **kwds):
        """Initialize the list box.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.ListBox. Enables LB_MULTIPLE
                if 'multiple' is in the param dict.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        self._norefresh = False

        if self.param and "multiple" in self.param:
            style = 0
            if "style" in kwds:
                style = kwds["style"]
            style = style | wx.LB_MULTIPLE
            kwds["style"] = style

        wx.ListBox.__init__(self, parent, **kwds)

        self._init_choices(self.get_tdata())

    def block_refresh(self):
        """Prevent automatic refresh on process_refr_data calls."""
        self._norefresh = True

    def find_and_select(self, item):
        """Find the first occurrence of item and select it.

        Matches items that start with the given string.

        Args:
            item: String prefix to search for.
        """
        strings = self.GetStrings()
        for i, s in enumerate(strings):
            if s.startswith(item):
                self.SetSelection(i)
                return

    def process_refr_data(self, **kwds):
        """Refresh the list with new data.

        Args:
            **kwds: New keyword arguments. Skips refresh if
                _norefresh is True.
        """
        self.init_base(kwds)
        if not self._norefresh:
            self.Clear()
            self.refresh_tdata()
            self._init_choices(self.get_tdata())

    def _init_choices(self, data):
        """Populate the list from tdata.

        Args:
            data: List of rows from tdata. Each row[0] is a Td
                object with data (display text) and optional
                attrs dict with 'value' and 'selected' keys.
        """
        self.choices = []
        self.selected_rows = []
        if data:
            for i, row in enumerate(data):
                value = row[0].data
                self.Append(value)
                if "value" in row[0].attrs:
                    self.choices.append(row[0].attrs["value"])
                else:
                    self.choices.append(value)
                if "selected" in row[0].attrs:
                    self.selected_rows.append(i)
        if self.selected_rows:
            for j in self.selected_rows:
                self.SetSelection(j)

    def GetValue(self):
        """Get values of all selected items.

        Returns:
            List of values corresponding to selected items.
        """
        ret = []
        sel = self.GetSelections()
        for s in sel:
            ret.append(self.choices[s])
        return ret


class LIST(wx.ListCtrl, SchBaseCtrl):
    """List control with multiple columns (report view).

    Handles ctrllist tag. Displays tabular data in report mode
    with auto-sized columns. First row of tdata provides column
    headers.

    Tag arguments:
        value: Not directly used; data comes from tdata.
    """

    def __init__(self, parent, **kwds):
        """Initialize the list control in report mode.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.ListCtrl with LC_REPORT style.
        """
        SchBaseCtrl.__init__(self, parent, kwds)

        if "style" in kwds:
            kwds["style"] = kwds["style"] | wx.LC_REPORT
        else:
            kwds["style"] = wx.LC_REPORT
        kwds["size"] = wx.Size(-1, -1)

        wx.ListCtrl.__init__(self, parent, **kwds)

        tdata = self.get_tdata()
        if tdata:
            first_row = True
            num_cols = 0
            for row in tdata:
                if first_row:
                    first_row = False
                    num_cols = len(row)
                    for i in range(num_cols):
                        self.InsertColumn(i, row[i].data)
                else:
                    index = self.InsertItem(0, row[0].data)
                    for i in range(1, num_cols):
                        self.SetItem(index, i, row[i].data)

            for i in range(num_cols):
                self.SetColumnWidth(i, -1)

    def process_refr_data(self, **kwds):
        """Refresh the list with new data.

        Args:
            **kwds: New keyword arguments.
        """
        self.init_base(kwds)
        self.ClearAll()
        tdata = self.get_tdata()
        if tdata:
            first_row = True
            num_cols = 0
            for row in tdata:
                if first_row:
                    first_row = False
                    num_cols = len(row)
                    for i in range(num_cols):
                        self.InsertColumn(i, row[i].data)
                else:
                    index = self.InsertItem(0, row[0].data)
                    for i in range(1, num_cols):
                        self.SetItem(index, i, row[i].data)


class CHECKLIST(LIST):
    """List control with checkboxes for each item.

    Extends LIST to enable item checkboxes. Items can be toggled
    by activating them (Enter or double-click).

    Tag arguments:
        value: Same as LIST.
    """

    def __init__(self, parent, **kwds):
        """Initialize the checklist control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to LIST. Enables checkboxes and
                binds item activation for toggling.
        """
        super().__init__(parent, **kwds)
        self.EnableCheckBoxes()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_item_activated)

    def ToggleItem(self, index):
        """Toggle the checked state of an item.

        Args:
            index: Zero-based item index.
        """
        toggle = not self.IsItemChecked(index)
        self.CheckItem(index, toggle)

    def _on_item_activated(self, evt):
        """Handle item activation by toggling its checkbox.

        Args:
            evt: The list item activation event.
        """
        self.ToggleItem(evt.Index)

    def GetBestSize(self):
        """Return the best size for the control.

        Returns:
            Tuple of (400, 48).
        """
        return (400, 48)


class RADIOBOX(wx.RadioBox, SchBaseCtrl):
    """Radio box with a group of mutually exclusive choices.

    Handles ctrlradiobox tag. Choices are populated from tdata.

    Tag arguments:
        value: Initial selection value.
    """

    def __init__(self, parent, **kwds):
        """Initialize the radio box.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.RadioBox with 'choices'
                populated from tdata.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        tdata = self.get_tdata()
        if tdata:
            choices = []
            for row in tdata:
                choices.append(row[0].data)
            kwds["choices"] = choices
        wx.RadioBox.__init__(self, parent, **kwds)

    def process_refr_data(self, **kwds):
        """Refresh the radio box with new choices.

        Args:
            **kwds: New keyword arguments.
        """
        self.init_base(kwds)
        self.Clear()
        self.refresh_tdata()
        tdata = self.get_tdata()
        if tdata:
            for row in tdata:
                self.Append(row[0].data)


class RADIOBUTTON(wx.RadioButton, SchBaseCtrl):
    """Individual radio button for use in radio groups.

    Handles ctrlradiobutton tag. The first button with a given
    name prefix automatically gets the RB_GROUP style to start
    a new radio group.

    Tag arguments:
        checked: If present, initializes as selected.
        value: Custom value returned when selected.
    """

    def __init__(self, parent, **kwds):
        """Initialize the radio button.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.RadioButton. Adds RB_GROUP
                style if this is the first button with this name
                prefix (before '__').
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if "name" in kwds:
            name = kwds["name"]
            # If no sibling with same name group exists, make this the group start
            if not hasattr(parent, name.split("__")[0]):
                if "style" in kwds:
                    kwds["style"] |= wx.RB_GROUP
                else:
                    kwds["style"] = wx.RB_GROUP

        if "checked" in kwds:
            del kwds["checked"]
            checked = True
        else:
            checked = False
        if "value" in kwds:
            self.value = kwds["value"]
            del kwds["value"]
        else:
            self.value = None

        wx.RadioButton.__init__(self, parent, **kwds)
        if checked:
            self.SetValue(True)

    def GetValue(self):
        """Get the radio button value.

        Returns:
            If selected and custom value is set, returns str(value).
            If selected without custom value, returns None.
            If not selected, returns None.
        """
        selected = wx.RadioButton.GetValue(self)
        if selected:
            if self.value:
                return str(self.value)
            else:
                return None
        else:
            return None

    def SetValue(self, value):
        """Set the radio button state.

        Args:
            value: If bool, sets the selection state directly.
                Otherwise stores as the custom value.
        """
        if isinstance(value, bool):
            return wx.RadioButton.SetValue(self, value)
        else:
            self.value = value
