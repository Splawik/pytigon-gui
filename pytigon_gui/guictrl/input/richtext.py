"""
Rich text widget class for the SchForm GUI framework.

Provides a wxPython rich-text editor integrated with SchBaseCtrl for
formatted multi-line text editing (fonts, colours, styles).

Classes:
    RICHTEXT
"""

import wx
import wx.richtext

from pytigon_gui.guictrl.basectrl import SchBaseCtrl


class RICHTEXT(wx.richtext.RichTextCtrl, SchBaseCtrl):
    """Rich text editor control.

    Handles ctrlrichtext tag. A full-featured formatted text editor
    supporting bold/italic/underline, colours, fonts, and embedded
    images via wx.richtext.RichTextCtrl.

    Tag arguments:
        value: Initial HTML/plain text content.
        readonly: If set, the editor is read-only.
    """

    def __init__(self, parent, **kwds):
        """Initialize the rich text control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.richtext.RichTextCtrl with
                multi-line style.
        """
        SchBaseCtrl.__init__(self, parent, kwds)

        style = kwds.get("style", 0)
        style |= wx.richtext.RE_MULTILINE
        if self.readonly:
            style |= wx.richtext.RE_READONLY
        kwds["style"] = style

        if "size" not in kwds:
            kwds["size"] = wx.Size(400, 200)

        wx.richtext.RichTextCtrl.__init__(self, parent, **kwds)

        if self.value:
            self.SetValue(self.value)

    def SetValue(self, value):
        """Set the rich text content.

        Args:
            value: Text or HTML-string content. Bytes are decoded.
        """
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        wx.richtext.RichTextCtrl.SetValue(self, value)

    def GetValue(self):
        """Get the current content as plain text.

        Returns:
            The text content.
        """
        return wx.richtext.RichTextCtrl.GetValue(self)
