"""Popup control classes for server-backed data selection.

Provides a ComboCtrl-based popup control (DataPopupControl) that interacts
with server endpoints for data lookup, selection, and dialog display.

Server API:
    test(value):
        Return element matching value, or empty string if no match.
        Response format: (element id, string representation of element).

    dialog(value):
        Return an HTML form to choose an element.
        Response format: (element id, string representation of element).
"""

import logging

import wx
from wx import ComboCtrl
from wx.lib import masked

from pytigon_lib.schtools import schjson
from pytigon_lib.schtools.tools import bencode, bdecode

logger = logging.getLogger(__name__)


class DataPopup(wx.ComboPopup):
    """Popup window that embeds an HTML page for data selection.

    Used by DataPopupControl to display a SchPage inside a combo
    dropdown. Handles ESC dismissal and size negotiation.
    """

    def __init__(self, size, combo, href):
        """Initialize the popup.

        Args:
            size: Preferred size (width, height).
            combo: The parent DataPopupControl.
            href: Server URL for the popup content.
        """
        self.href = href
        self.combo = combo
        self.html = None
        self.size = size
        wx.ComboPopup.__init__(self)

    def Create(self, parent):
        """Create the popup content (SchPage) and layout.

        Args:
            parent: The popup parent window.

        Returns:
            True on success.
        """
        self.html = self.combo.on_create(parent)
        parent.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.html, 1, wx.ALL | wx.GROW, 1)
        parent.SetSizer(box)
        parent.SetAutoLayout(True)
        parent.Fit()
        return True

    def GetControl(self):
        """Return the embedded HTML control."""
        return self.html

    def GetStringValue(self):
        """Return the combo's start value as the string representation."""
        return self.combo.start_value

    def on_key_down(self, event):
        """Handle ESC key to dismiss the popup.

        Args:
            event: wx.KeyEvent.
        """
        if event.KeyCode == wx.WXK_ESCAPE:
            self.Dismiss()
        else:
            event.Skip()

    def set_new_href(self, href):
        """Update the popup's server URL and propagate to the HTML page.

        Args:
            href: New server URL.
        """
        self.href = href
        if self.html:
            self.html.set_new_href(href)

    def OnPopup(self):
        """Called when the popup is shown."""
        self.combo.on_popoup()
        return wx.ComboPopup.OnPopup(self)

    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        """Return the popup's adjusted size.

        Args:
            minWidth: Minimum width.
            prefHeight: Preferred height.
            maxHeight: Maximum height.

        Returns:
            Adjusted (width, height) tuple.
        """
        width = self.size[0]
        height = self.size[1]
        return wx.ComboPopup.GetAdjustedSize(self, width, height, maxHeight)


class DataPopupControl(ComboCtrl):
    """Server-backed combo control with popup data selection.

    Provides a ComboCtrl that uses server endpoints for:
    - /size/  : fetching popup dimensions
    - /test/  : validating/looking up typed values
    - /dialog/: opening an extended selection dialog

    Supports an optional secondary href (separated by ';') for
    the extended dialog endpoint.
    """

    def __init__(self, *args, **kwds):
        """Initialize the popup control.

        Args:
            *args: Positional arguments passed to ComboCtrl.
            **kwds: Keyword arguments. Accepts 'dialog_with_value'
                (bool, default True) and 'style'.
        """
        if "style" in kwds:
            kwds["style"] |= wx.TE_PROCESS_ENTER
        else:
            kwds["style"] = wx.TE_PROCESS_ENTER

        if "dialog_with_value" in kwds:
            self.dialog_with_value = kwds["dialog_with_value"]
            del kwds["dialog_with_value"]
        else:
            self.dialog_with_value = True
        ComboCtrl.__init__(self, *args, **kwds)

        self.win = None
        self.html = None
        self.rec_value = []
        self.event_object = None
        self.page = None
        self.popup = None
        self.start_value = ""

        if self.defaultvalue:
            self.clear_str = self.defaultvalue
        else:
            self.clear_str = ""

        # Support dual-href: primary href for list/size/test,
        # secondary (after ';') for extended dialog
        href_parts = self.href.split(";")
        self.href = href_parts[0]
        self.href2 = href_parts[1] if len(href_parts) > 1 else None

        self.http = wx.GetApp().get_http(self)
        response = self.http.get(self, str(self.href) + "size/")
        self.size = schjson.loads(response.str())

        self.simpleDialog = True
        if self.GetTextCtrl():
            self.GetTextCtrl().SetForegroundColour(wx.Colour(0, 0, 0))

        self.UseAltPopupWindow(enable=True)

        popup_ctrl = self._create_popoup()
        self.SetPopupControl(popup_ctrl)

    def _create_popoup(self):
        """Create or return the cached DataPopup instance.

        Returns:
            DataPopup instance.
        """
        if not self.popup:
            self.popup = DataPopup(size=self.size, combo=self, href=self.href)
        return self.popup

    def to_masked(self, **kwds):
        """Convert the internal text control to a masked.TextCtrl.

        Args:
            **kwds: Parameters forwarded to SetCtrlParameters.
        """
        self.win = ComboCtrl.GetTextCtrl(self)
        self.win.__class__ = masked.TextCtrl
        self.win._PostInit(setupEventHandling=True, name="maskedTextCtrl", value="")
        self.win.SetCtrlParameters(**kwds)

    def GetTextCtrl(self):
        """Return the text control, preferring the masked override if set.

        Returns:
            wx.TextCtrl or masked.TextCtrl instance.
        """
        if self.win:
            return self.win
        return ComboCtrl.GetTextCtrl(self)

    def KillFocus(self):
        """Handle focus loss: trigger focus_out validation if readonly."""
        value = ComboCtrl.GetValue(self)
        if self.readonly:
            self.focus_out(value)

    def any_parent_command(self, command, *args, **kwds):
        """Walk up the widget tree to find and call a named command.

        Args:
            command: Method name to search for.
            *args: Positional arguments.
            **kwds: Keyword arguments.

        Returns:
            Result of the command, or None if not found.
        """
        parent = self
        while parent is not None:
            if hasattr(parent, command):
                return getattr(parent, command)(*args, **kwds)
            parent = parent.GetParent()
        return None

    def alternate_button_click(self):
        """Handle alternative button (e.g. F2) to open extended dialog."""
        if self.event_object and hasattr(self.event_object, "on_before_button_click"):
            self.event_object.on_before_button_click()

        self.run_ext_dialog()

        if self.event_object and hasattr(self.event_object, "OnButtonClick"):
            self.event_object.OnButtonClick()

    def run_ext_dialog(self):
        """Open the extended selection dialog as a child page."""
        self.GetTextCtrl().SetFocus()

        parm = {"value": self.get_parm("value")}

        href = self.href2 if self.href2 else self.href

        _href = href + "dialog/|value" if self.dialog_with_value else href + "dialog/"
        self.page = self.GetParent().new_child_page(str(_href), "Select", parm)
        self.page.body.old_any_parent_command = self.page.body.any_parent_command
        self.page.body.any_parent_command = self.any_parent_command
        self.page.body.parent_combo = self

    def get_last_control_with_focus(self):
        """Return self as the last focused control."""
        return self

    def focus_in(self, value):
        """Handle focus-in event (no-op by default).

        Args:
            value: Current field value.
        """

    def focus_out(self, value):
        """Validate typed value against the server when focus leaves.

        Compares current value with start_value. If changed and non-empty,
        posts the value to the server's /test/ endpoint.

        Args:
            value: The current field value.
        """
        if str(value) != self.start_value and str(value) != "":
            self.http = wx.GetApp().get_http(self)
            x = bencode(value)
            response = self.http.post(self, str(self.href) + "test/", {"value": x})
            tab = schjson.loads(response.str())
            ret = tab[0]

            if ret != 1:
                if ret == 2:
                    self.OnButtonClick()
                else:
                    self.clear_rec()
            else:
                self.set_rec(tab[1], tab[2], False)

    def has_parm(self, parm):
        """Check if a parameter is supported.

        Args:
            parm: Parameter name.

        Returns:
            True if parm is 'value', False otherwise.
        """
        return parm == "value"

    def get_parm(self, parm):
        """Get a parameter value for URL encoding.

        Args:
            parm: Parameter name ('value' supported).

        Returns:
            Bencoded field value, or None.
        """
        return bencode(ComboCtrl.GetValue(self)) if parm == "value" else None

    def set_rec(self, value, value_rec, dismiss=False):
        """Set the field value from a server response record.

        Args:
            value: Element id.
            value_rec: Element data (Td object or similar).
            dismiss: If True, dismisses the popup after setting.
        """
        value2 = value_rec.data

        if self.event_object and hasattr(self.event_object, "set_rec"):
            value2 = self.event_object.set_rec(value, value_rec, dismiss)

        self.start_value = value2
        self.SetValue(value2)
        self.rec_value = value_rec

        if dismiss:
            self.Dismiss()

        parent = self.GetParent()
        if hasattr(parent, "on_popup_control_change_value"):
            parent.on_popup_control_change_value(self)

    def get_rec(self):
        """Return the currently selected record."""
        return self.rec_value

    def clear_rec(self):
        """Clear the current selection and reset to the default string."""
        self.start_value = ""
        self.SetValue(self.clear_str)
        self.rec_value = []

    def on_create(self, parent):
        """Create the embedded SchPage for popup content.

        Args:
            parent: Parent window for the SchPage.

        Returns:
            The created SchPage instance.
        """
        from pytigon_gui.guiframe.page import SchPage

        href = (
            self.href + "dialog/|value"
            if self.dialog_with_value
            else self.href + "dialog/"
        )
        self.html = SchPage(parent, href, self)
        self.html.body.parent_combo = self
        return self.html

    def on_popoup(self):
        """Called when the dropdown popup is shown.

        Refreshes the embedded HTML page and positions it.
        """
        if self.html:
            wx.BeginBusyCursor()
            self.html.body.Hide()

            def _after():
                try:
                    self.html.refresh_html()
                    self.html.SetFocus()
                    self.html.on_size(None)
                    self.html.body.init()

                    def _after2():
                        self.html.body.refr(self.start_value)
                        self.html.body.Show()

                    wx.CallAfter(_after2)
                except Exception:
                    logger.exception("Error in popup on_popoup")
                finally:
                    wx.EndBusyCursor()

            wx.CallAfter(_after)

    def Dismiss(self):
        """Dismiss the popup or extended dialog page."""
        if self.page:
            self.page.body.old_any_parent_command("on_cancel", None)
            self.page = None
        else:
            super().Dismiss()
        self.SetFocus()

    def set_new_href(self, href):
        """Update the server endpoint URL.

        Args:
            href: New base URL. May contain ';' to separate primary
                and secondary (dialog) endpoints.
        """
        self.href = href

        href_parts = self.href.split(";")
        if len(href_parts) > 1:
            self.href = href_parts[0]
            self.href2 = href_parts[1]
        else:
            self.href2 = None

        href3 = self.href2 if self.href2 else self.href

        if self.dialog_with_value:
            href3 += "dialog/|value"
        else:
            href3 += "dialog/"

        if self.popup:
            self.popup.set_new_href(href3)
