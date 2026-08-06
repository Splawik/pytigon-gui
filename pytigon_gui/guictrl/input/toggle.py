"""
Toggle button widget classes for the SchForm GUI framework.

Provides wxPython toggle (switchable) controls integrated with SchBaseCtrl:
a plain toggle button and a bitmap toggle button.

Classes:
    TOGGLEBUTTON, BITMAPTOGGLEBUTTON
"""

import wx

from pytigon_gui.guictrl.basectrl import SchBaseCtrl
from pytigon_gui.guilib.image import bitmap_from_href


class TOGGLEBUTTON(wx.ToggleButton, SchBaseCtrl):
    """Toggle button that keeps its pressed state.

    Handles ctrltogglebutton tag. A push button that stays in the
    pressed/released state until clicked again.

    Tag arguments:
        label: Button label text.
        checked: If set, the button starts pressed.
        value: Optional value returned when pressed.
    """

    def __init__(self, parent, **kwds):
        """Initialize the toggle button.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.ToggleButton. Removes 'checked'
                and 'value' handling before constructing.
        """
        SchBaseCtrl.__init__(self, parent, kwds)

        checked = False
        if "checked" in kwds:
            del kwds["checked"]
            checked = True

        value = kwds.pop("value", None)
        self.custom_value = value

        if self.label:
            kwds["label"] = self.label.replace("&", "")

        wx.ToggleButton.__init__(self, parent, **kwds)
        if checked:
            self.SetValue(True)

        self.Bind(wx.EVT_TOGGLEBUTTON, self._on_toggle)

    def _on_toggle(self, event):
        """Notify the parent form about the state change."""
        parent = self.GetParent()
        if hasattr(parent, "on_togglebutton"):
            parent.on_togglebutton(self)
        event.Skip()

    def GetValue(self):
        """Get the toggle state.

        Returns:
            If pressed and a custom value is set, returns str(value).
            If pressed without a custom value, returns True.
            If released, returns None.
        """
        if wx.ToggleButton.GetValue(self):
            if self.custom_value:
                return str(self.custom_value)
            return True
        return None

    def SetValue(self, value):
        """Set the toggle state.

        Args:
            value: If bool, sets the pressed state directly.
                Otherwise stores it as the custom value.
        """
        if isinstance(value, bool):
            return wx.ToggleButton.SetValue(self, value)
        self.custom_value = value


class BITMAPTOGGLEBUTTON(wx.ToggleButton, SchBaseCtrl):
    """Toggle button with a bitmap label.

    Handles ctrlbitmaptogglebutton tag. Uses an image (from the 'src'
    attribute) as the button label while keeping toggle behaviour.

    Tag arguments:
        src: Resource identifier for the bitmap (see bitmap_from_href).
        checked: If set, the button starts pressed.
    """

    def __init__(self, parent, **kwds):
        """Initialize the bitmap toggle button.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.ToggleButton. The 'src' attribute
                is used to load the bitmap label.
        """
        SchBaseCtrl.__init__(self, parent, kwds)

        checked = False
        if "checked" in kwds:
            del kwds["checked"]
            checked = True

        if self.src:
            bmp = bitmap_from_href(self.src, 1)
            kwds["label"] = bmp

        wx.ToggleButton.__init__(self, parent, **kwds)
        if checked:
            self.SetValue(True)

    def GetValue(self):
        """Return whether the button is currently pressed."""
        return bool(wx.ToggleButton.GetValue(self))
