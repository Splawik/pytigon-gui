"""Select2-style autocomplete widget classes.

Provides server-backed autocomplete with popup selection list,
inspired by the Select2 JavaScript library (https://select2.github.io/).

Classes:
    ListBoxNoFocus, Select2Popup, Select2Base
"""

import string
import logging
import wx

from pytigon_lib.schtools import schjson
from pytigon_gui.guictrl.basectrl import SchBaseCtrl

logger = logging.getLogger(__name__)

_ = wx.GetTranslation


class ListBoxNoFocus(wx.ListBox):
    """ListBox that never accepts keyboard focus."""

    def CanAcceptFocus(self):
        """Return False always -- this listbox cannot receive focus."""
        return False


class Select2Popup(wx.MiniFrame):
    """Popup window for Select2-style autocomplete search.

    Displays a text entry field above a list of matching results.
    Supports keyboard navigation (arrows, Enter, Escape, Tab).
    """

    def __init__(
        self,
        parent,
        id,
        title,
        pos,
        size,
        style,
        combo,
        field_id,
        url=None,
        minimum_input_length=2,
    ):
        """Initialize the Select2 popup.

        Args:
            parent: Parent window.
            id: Window ID.
            title: Window title.
            pos: Screen position.
            size: Window size.
            style: Window style flags.
            combo: The parent Select2Base control.
            field_id: Django field identifier for the AJAX endpoint.
            url: Optional override URL for the autocomplete endpoint.
            minimum_input_length: Minimum characters before search triggers.
        """
        from pytigon_gui.guiframe.page import SchPage

        self.combo = combo
        self.point = pos
        self.field_id = field_id
        self.url = url
        self.minimum_input_length = minimum_input_length if minimum_input_length else 0

        wx.MiniFrame.__init__(self, parent, id, title, pos, size, wx.RESIZE_BORDER)

        self.edit_ctrl = wx.TextCtrl(
            self, size=(440, -1), style=wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB
        )
        self.list_ctrl = ListBoxNoFocus(self, size=(440, 200), style=wx.LB_SINGLE)

        self.edit_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.edit_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        self.list_ctrl.Bind(wx.EVT_LISTBOX_DCLICK, self.on_enter)
        self.list_ctrl.Bind(wx.EVT_LISTBOX, self.on_enter)

        self.Bind(wx.EVT_ACTIVATE, self.on_activate)
        self.Bind(wx.EVT_TEXT, self.on_text)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.edit_ctrl)
        box.Add(self.list_ctrl, 1, wx.ALL | wx.GROW, 1)
        self.SetSizer(box)
        self.SetAutoLayout(True)
        self.Fit()

    def on_enter(self, event):
        """Handle Enter/DoubleClick on a list item: dismiss and set value.

        Args:
            event: The wx event.
        """
        sel = self.list_ctrl.GetSelection()
        if sel != wx.NOT_FOUND:
            self.Dismiss()
            item_id = self.list_ctrl.GetClientData(sel)
            item_str = self.list_ctrl.GetString(sel)
            self.combo.set_value(item_id, item_str)

    def on_activate(self, event):
        """Hide popup and return focus when deactivated.

        Args:
            event: The wx.ActivateEvent.
        """
        if not event.GetActive():
            self.Hide()
            self.combo.SetFocus()
        event.Skip()

    def on_key_down(self, event):
        """Handle keyboard navigation within the popup.

        Args:
            event: wx.KeyEvent.
        """
        if event.KeyCode == wx.WXK_ESCAPE:
            self.Dismiss()
        elif event.KeyCode == wx.WXK_DOWN or (
            event.AltDown() and event.KeyCode == ord("J")
        ):
            sel = self.list_ctrl.GetSelection()
            if sel != wx.NOT_FOUND and sel < self.list_ctrl.GetCount() - 1:
                self.list_ctrl.SetSelection(sel + 1)
        elif event.KeyCode == wx.WXK_UP or (
            event.AltDown() and event.KeyCode == ord("K")
        ):
            sel = self.list_ctrl.GetSelection()
            if sel != wx.NOT_FOUND and sel > 0:
                self.list_ctrl.SetSelection(sel - 1)
        elif event.KeyCode == wx.WXK_TAB:
            return self.on_enter(event)
        else:
            event.Skip()

    def on_text(self, event):
        """Handle text input: query the server for autocomplete results.

        Args:
            event: wx.CommandEvent with the text string.
        """
        event.Skip()
        s = event.GetString()
        if len(s) < self.minimum_input_length:
            return

        base_url = self.url if self.url else "/select2/fields/auto.json"
        url = f"{base_url}?term={s}&page=1&context=&field_id={self.field_id}"

        try:
            http = wx.GetApp().get_http(self.combo)
            response = http.get(self, url)
            tab = schjson.loads(response.str())
        except Exception:
            logger.warning("Failed to load select2 data from: %s", url, exc_info=True)
            return

        err = tab.get("err")
        if err is None or err == "nil":
            self.list_ctrl.Clear()
            if len(tab["results"]) > 0:
                for pos in tab["results"]:
                    self.list_ctrl.Append(pos["text"], pos["id"])
                if s:
                    self.list_ctrl.SetSelection(0)

    def set_position(self, point):
        """Store the target screen position for the popup.

        Args:
            point: (x, y) tuple in screen coordinates.
        """
        self.point = point

    def clear(self):
        """Clear the search field and results list."""
        self.edit_ctrl.ChangeValue("")
        self.list_ctrl.Clear()

    def Popup(self):
        """Show the popup at the stored position."""
        self.Show()
        self.Move(self.point)

    def Dismiss(self):
        """Hide the popup and return focus to the combo control."""
        self.Hide()
        self.combo.SetFocus()

    def Hide(self):
        """Notify the parent combo and hide the window."""
        self.combo.on_popup_hidden()
        super().Hide()


class Select2Base(wx.ComboCtrl, SchBaseCtrl):
    """Server-backed autocomplete combo using Select2 protocol.

    Provides a wx.ComboCtrl that communicates with a Select2-compatible
    server endpoint for autocomplete search and selection.

    Supports multiple selection mode and action buttons (F2/Insert keys).
    """

    def __init__(self, parent, **kwds):
        """Initialize the Select2 control.

        Args:
            parent: Parent window.
            **kwds: Keyword arguments forwarded to wx.ComboCtrl and
                SchBaseCtrl. Expects 'param' containing 'data' with
                Select2 configuration attrs.
        """
        self.popup = None
        self.button1 = None
        self.button2 = None
        self._popup_shown = False

        SchBaseCtrl.__init__(self, parent, kwds)

        data = self.param["data"][0]["attrs"]
        self.multiple = "multiple" in data

        if "style" in kwds:
            kwds["style"] |= wx.TE_PROCESS_ENTER
        else:
            kwds["style"] = wx.TE_PROCESS_ENTER

        if "item_id" in self.param and self.param["item_id"] != "None":
            self.item_id = [int(self.param["item_id"])]
            self.item_str = [self.param["item_str"]]
        else:
            self.item_id = [-1]
            self.item_str = [""]

        kwds["size"] = (438, -1)

        wx.ComboCtrl.__init__(self, parent, **kwds)

        if self.GetTextCtrl():
            self.GetTextCtrl().SetForegroundColour(wx.Colour(0, 0, 0))

        self.Bind(wx.EVT_CHAR, self.on_char)

        if self.item_str:
            self.SetValue(self.item_str[0])

        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down_base)

        self.GetParent().get_parent_page().register_signal(self, "return_new_row")
        self.GetParent().get_parent_page().register_signal(self, "return_updated_row")

    def return_updated_row(self, **argv):
        """Handle return_updated_row signal by updating the value."""
        self.set_value(argv["id"], argv["title"])

    def return_new_row(self, **argv):
        """Handle return_new_row signal by updating the value."""
        self.set_value(argv["id"], argv["title"])

    def init(self, button1, button2):
        """Register optional action buttons (F2 and Insert shortcuts).

        Args:
            button1: Button triggered by F2.
            button2: Button triggered by Insert.
        """
        self.button1 = button1
        self.button2 = button2

    def on_key_down_base(self, event):
        """Handle global keyboard shortcuts.

        Args:
            event: wx.KeyEvent.
        """
        if event.GetKeyCode() == wx.WXK_TAB:
            if event.ShiftDown():
                self.GetParent().GetParent().Navigate(self.GetParent(), True)
            else:
                self.GetParent().GetParent().Navigate(self.GetParent(), False)
        elif event.GetKeyCode() == wx.WXK_F2:
            self.button1.on_click(event)
        elif event.GetKeyCode() == wx.WXK_INSERT:
            self.button2.on_click(event)
        else:
            event.Skip()

    def set_value(self, item_id, item_str):
        """Set the selected value.

        Args:
            item_id: Table row ID (database key).
            item_str: String representation of the row.
        """
        if self.multiple:
            if item_id not in self.item_id:
                self.item_id.append(item_id)
                self.item_str.append(item_str)
            self.SetValue("; ".join(self.item_str)[2:])
        else:
            self.item_id = [item_id]
            self.item_str = [item_str]
            self.SetValue(item_str)

        def _finish():
            self.SelectNone()
            self.SetInsertionPointEnd()

        wx.CallAfter(_finish)

    def on_char(self, event):
        """Handle character input: forward to the popup search field.

        Args:
            event: wx.KeyEvent.
        """
        try:
            c = chr(event.GetUnicodeKey())
            if c in string.printable:
                if not self._popup_shown:
                    self._on_button_click()
                self.popup.edit_ctrl.AppendText(c)
        except (ValueError, OverflowError):
            pass
        if event.KeyCode in (wx.WXK_DELETE, wx.WXK_BACK):
            self.item_id = [-1]
            self.item_str = [""]
            self.Clear()

    def _on_button_click(self):
        """Show the Select2 popup, creating it if needed."""
        if not self.popup:
            pos = self.GetScreenPosition()
            pos = (pos[0], pos[1] + self.GetSize()[1])
            field_id = None
            minimum_input_length = None
            url = None
            data = self.param["data"][0]["attrs"]
            if "data-field_id" in data:
                field_id = data["data-field_id"]
            if "data-minimum-input-length" in data:
                minimum_input_length = int(data["data-minimum-input-length"])
            if "data-ajax--url" in data:
                url = data["data-ajax--url"]

            parent = self.GetTextCtrl() if self.GetTextCtrl() else self
            self.popup = Select2Popup(
                parent,
                -1,
                _("Select item"),
                pos=pos,
                size=(450, 400),
                style=wx.DEFAULT_DIALOG_STYLE,
                combo=self,
                url=url,
                field_id=field_id,
                minimum_input_length=minimum_input_length,
            )
        self.popup.clear()

        pos = self.GetScreenPosition()
        pos = (pos[0], pos[1] + self.GetSize()[1])
        pos = [pos[0], pos[1]]

        screen_dx = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        screen_dy = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)

        popup_size = self.popup.GetSize()

        if pos[0] + popup_size[0] > screen_dx:
            pos[0] = screen_dx - popup_size[0]
        if pos[1] + popup_size[1] > screen_dy:
            pos[1] = pos[1] - self.GetSize().GetHeight() - popup_size[1]

        self.popup.set_position(pos)
        self.popup.Popup()
        self._popup_shown = True

    def on_popup_hidden(self):
        """Called when the popup is hidden."""
        self._popup_shown = False
        self.SetFocus()

    def GetValue(self):
        """Return the selected value (item_id or list of item_ids).

        Returns:
            int or list of int item IDs.
        """
        if self.multiple:
            return self.item_id
        return self.item_id[0]

    def OnButtonClick(self):
        """Handle the dropdown button click: open popup and clear search."""
        ret = self._on_button_click()
        self.popup.edit_ctrl.SetValue("")
        wx.CallAfter(self.popup.edit_ctrl.SetFocus)
        return ret

    def DoSetPopupControl(self, popup):
        """Placeholder for popup control setup (not used)."""
        pass

    def Dismiss(self):
        """Close the popup and return focus."""
        if self.popup:
            self.popup.Close()
            self.popup = None
        self.SetFocus()
