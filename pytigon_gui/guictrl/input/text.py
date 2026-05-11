"""
Text input widget classes for the SchForm GUI framework.

Provides wxPython text entry controls integrated with SchBaseCtrl:
single-line text, password, search, styled (multi-line) text,
and masked input widgets.

Classes:
    TEXT, PASSWORD, SEARCH, STYLEDTEXT, MASKTEXT
Aliases:
    AUTOCOMPLETE, STANDARDSTYLEDTEXT
"""

import wx
from wx.lib import masked

from pytigon_gui.guictrl.basectrl import SchBaseCtrl


class TEXT(SchBaseCtrl, wx.TextCtrl):
    """Single-line text input control.

    Handles ctrltext tag. Supports process_enter style for
    Enter key handling, hidden state, and maxlength constraint.

    Tag arguments:
        value: Initial text value.
        process_enter: If set in param, enables TE_PROCESS_ENTER.
        hidden: If True, disables the control.
        maxlength: Maximum number of characters allowed.
    """

    def __init__(self, parent, **kwds):
        """Initialize the text control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.TextCtrl after processing
                'param' for process_enter flag.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param and "process_enter" in self.param:
            kwds["style"] = wx.TE_PROCESS_ENTER
        wx.TextCtrl.__init__(self, parent, **kwds)
        if self.hidden:
            self.Enable(False)
        if self.maxlength:
            self.SetMaxLength(int(self.maxlength))

    def SetValue(self, value):
        """Set the text value, converting bytes to str if needed.

        Args:
            value: String or bytes value to set.
        """
        if isinstance(value, str):
            return wx.TextCtrl.SetValue(self, value)
        else:
            return wx.TextCtrl.SetValue(self, value.decode("utf-8"))

    def GetValue(self):
        """Get the current text value.

        Returns:
            The text content as a string.
        """
        return super().GetValue()

    def GetBestSize(self):
        """Return a wider best size than the default.

        The width is multiplied by 4 to give text fields more
        horizontal space.

        Returns:
            Tuple of (width * 4, height).
        """
        size = super().GetBestSize()
        return (4 * size[0], size[1])


class PASSWORD(TEXT, SchBaseCtrl):
    """Password entry control with masked input.

    Handles ctrlpassword tag. Inherits from TEXT but adds
    the wx.TE_PASSWORD style for masked character display.

    Tag arguments:
        value: Initial password value.
    """

    def __init__(self, parent, **kwds):
        """Initialize the password control with masked style.

        Args:
            parent: Parent window.
            **kwds: Forwarded to TEXT after adding TE_PASSWORD style.
        """
        if "style" in kwds:
            kwds["style"] = kwds["style"] | wx.TE_PASSWORD
        else:
            kwds["style"] = wx.TE_PASSWORD

        TEXT.__init__(self, parent, **kwds)


class SEARCH(wx.SearchCtrl, SchBaseCtrl):
    """Search text control with platform-specific sizing.

    Handles ctrlsearch tag. Wraps wx.SearchCtrl with
    adjusted default sizes for GTK and other platforms.
    Binds key-down events on the internal text control
    for GTK and MSW platforms.

    Tag arguments:
        value: Initial search text.
        process_enter: If set in param, enables TE_PROCESS_ENTER.
    """

    def __init__(self, parent, **kwds):
        """Initialize the search control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.SearchCtrl with platform-adjusted
                size and optional TE_PROCESS_ENTER style.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if wx.Platform in ("__WXGTK__",):
            kwds["size"] = (200, 28)
        else:
            kwds["size"] = (200, -1)
        if self.param and "process_enter" in self.param:
            kwds["style"] = wx.TE_PROCESS_ENTER

        wx.SearchCtrl.__init__(self, parent, **kwds)

        # Bind key-down on the internal TextCtrl child for GTK/MSW
        if wx.Platform in ("__WXGTK__", "__WXMSW__"):
            for child in list(self.GetChildren()):
                if isinstance(child, wx.TextCtrl):
                    child.Bind(wx.EVT_KEY_DOWN, self.on_key_down_base)
                    break


class STYLEDTEXT(wx.TextCtrl, SchBaseCtrl):
    """Multi-line styled text control.

    Handles ctrlstyledtext tag. Always uses wx.TE_MULTILINE style.
    Supports initial data from the 'data' parameter.

    Tag arguments:
        value: Initial text value.
        data: Alternative initial text from param['data'].
    """

    def __init__(self, parent, **kwds):
        """Initialize the styled (multi-line) text control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.TextCtrl with TE_MULTILINE style.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if "style" in kwds:
            style = kwds["style"]
            style = style | wx.TE_MULTILINE
            kwds["style"] = style
        else:
            kwds["style"] = wx.TE_MULTILINE
        wx.TextCtrl.__init__(self, parent, **kwds)
        if self.param and "data" in self.param:
            self.SetValue(self.param["data"])

    def SetValue(self, value):
        """Set the text value, stripping a leading newline if present.

        Args:
            value: String or bytes value to set. A single leading
                newline is stripped for cleaner display.
        """
        if value.startswith("\n"):
            value2 = value[1:]
        else:
            value2 = value
        if isinstance(value2, str):
            return wx.TextCtrl.SetValue(self, value2)
        else:
            return wx.TextCtrl.SetValue(self, value2.decode("utf-8"))


# Aliases for backward compatibility
AUTOCOMPLETE = STYLEDTEXT
"""Alias for STYLEDTEXT; may be replaced by plugins at runtime."""

STANDARDSTYLEDTEXT = STYLEDTEXT
"""Alias for STYLEDTEXT; the standard styled text implementation."""


class MASKTEXT(masked.TextCtrl, SchBaseCtrl):
    """Masked text input control with format validation.

    Handles ctrlmasktext tag. Supports mask patterns and
    autoformat strings via the 'src' attribute. When src
    starts with '!', it is treated as an autoformat string;
    otherwise it is used as a mask pattern.

    Tag arguments:
        value: Initial value.
        src: Mask pattern or autoformat string ('!' prefix).
        valuetype: Used to determine if mask/autoformat applies.
    """

    def __init__(self, parent, **kwds):
        """Initialize the masked text control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to masked.TextCtrl. If valuetype
                and src are set, configures mask or autoformat.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.valuetype:
            if self.src:
                if self.src.startswith("!"):
                    kwds["autoformat"] = self.src[1:]
                else:
                    kwds["mask"] = self.src
        masked.TextCtrl.__init__(self, parent, **kwds)
        self._autofit = False
