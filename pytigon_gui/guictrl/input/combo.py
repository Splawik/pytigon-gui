"""
Combo box and choice widget classes for the SchForm GUI framework.

Provides wxPython combo/choice controls integrated with SchBaseCtrl:
bitmap combo box, choice (popup-based), database choice, and
extended database choice.

Classes:
    BITMAPCOMBOBOX, CHOICE, DBCHOICE, DBCHOICE_EXT
"""

import os
from pathlib import Path
from base64 import b64encode

import wx
from wx import ComboCtrl
from wx.adv import BitmapComboBox

from pytigon_gui.guictrl.basectrl import SchBaseCtrl
from pytigon_gui.guictrl.display import POPUPHTML
from pytigon_lib.schparser.html_parsers import Td


class BITMAPCOMBOBOX(BitmapComboBox, SchBaseCtrl):
    """Bitmap combo box with icon support.

    Handles ctrlbitmapcombobox tag. Displays a dropdown with
    optional icons loaded from filesystem paths. Supports
    embedded wxArt icons, PNG icons from static files, and
    Fork Awesome font icons.

    Tag arguments:
        value: Initial selection value.
    """

    def __init__(self, parent, **kwds):
        """Initialize the bitmap combo box.

        Args:
            parent: Parent window.
            **kwds: Forwarded to BitmapComboBox.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        BitmapComboBox.__init__(self, parent, **kwds)
        self.init_default_icons = False
        self._first_use = True
        self.accept_focus = False

    def after_create(self):
        """Load icons after the control is fully created.

        Uses wx.CallAfter to defer icon loading until the
        event loop is idle, ensuring the control is properly
        sized and ready.
        """
        super().after_create()
        if self.init_default_icons:

            def _load_icons():
                self.init_embeded_icons()
                self.init_fa_icons()

            wx.CallAfter(_load_icons)

    def init_wx_icons(self):
        """Load standard wxArtProvider icons into the combo box."""
        for art_id in sorted([pos for pos in dir(wx) if pos.startswith("ART_")]):
            artid = getattr(wx, art_id)
            bmp = wx.ArtProvider.GetBitmap(artid, wx.ART_TOOLBAR, (22, 22))
            if bmp.IsOk():
                self.Append(art_id, bmp, art_id)

    def init_embeded_icons(self):
        """Load embedded PNG icons from the static/icons/22x22 directory."""
        base_path = str(wx.GetApp().src_path) + "/static/icons/22x22/"
        return self._init_icons(base_path, "png://")

    def init_fa_icons(self):
        """Load Fork Awesome font icons from the static/fonts directory."""
        base_path = (
            str(wx.GetApp().src_path) + "/static/fonts/fork-awesome/fonts/22x22/"
        )
        return self._init_icons(base_path, "fa://")

    def init_extern_icons(self, base_path, prefix):
        """Load icons from an external directory.

        Args:
            base_path: Filesystem path to the icon directory.
            prefix: URL-style prefix for icon identifiers (e.g. 'png://').
        """
        return self._init_icons(base_path, prefix)

    def _init_icons(self, base_path, prefix, subpath=None):
        """Recursively load PNG icons from a directory tree.

        Args:
            base_path: Root directory for icon search.
            prefix: URL-style prefix for icon identifiers.
            subpath: Current subdirectory relative to base_path (or None).
        """
        if subpath:
            dirname = Path(base_path) / subpath
        else:
            dirname = Path(base_path)

        if Path(dirname).exists():
            for ff in os.listdir(dirname):
                full_path = Path(dirname) / ff
                if Path(full_path).is_dir():
                    new_sub = str(Path(subpath) / ff) if subpath else ff
                    self._init_icons(base_path, prefix, new_sub)
                else:
                    if ".png" in ff.lower():
                        try:
                            path = dirname + "/" + ff
                            image = wx.Image(path)
                            bmp = wx.Bitmap(image)
                            if subpath:
                                icon_id = prefix + subpath + "/" + ff
                            else:
                                icon_id = prefix + ff
                            self.Append(icon_id.replace("\\", "/"), bmp, icon_id)
                        except Exception:
                            pass
                wx.Yield()

    def GetValue(self):
        """Get the current combo box value.

        Returns:
            The current value string, or empty string if None.
        """
        ret = super().GetValue()
        if ret:
            return ret
        else:
            return ""

    def SetValue(self, value):
        """Set the combo box value.

        Args:
            value: Value to select. Empty/None sets empty string.
        """
        if value:
            ret = super().SetValue(value)
        else:
            ret = super().SetValue("")
        return ret


class CHOICE(POPUPHTML):
    """Choice control with popup-based selection dialog.

    Handles ctrlchoice tag. Extends POPUPHTML to provide a
    dropdown choice with optional extended popup dialog.
    Supports keyboard accelerator (F2) for the extended dialog.

    Tag arguments:
        value: Initial selection value.
    """

    def __init__(self, parent, **kwds):
        """Initialize the choice control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to POPUPHTML. Sets default href
                to the list dialog if not provided.
        """
        if "href" not in kwds:
            kwds["href"] = wx.GetApp().make_href("/schsys/listdialog/")

        if "style" in kwds:
            kwds["style"] = kwds["style"] | wx.WANTS_CHARS
        else:
            kwds["style"] = wx.WANTS_CHARS

        if "size" not in kwds:
            kwds["size"] = wx.Size(250, -1)
        self.height = 250
        kwds["dialog_with_value"] = False
        POPUPHTML.__init__(self, parent, **kwds)

        self._init_choices(self.get_tdata())

        accel_table = [
            (0, wx.WXK_F2, self._on_ext_button_click),
        ]
        self.set_acc_key_tab(accel_table)

    def _init_choices(self, data):
        """Initialize choices from tdata.

        Args:
            data: List of rows from tdata. Each row[0] is a Td
                object. Pre-selects items with 'selected' in attrs.
        """
        self.choices = []
        if data:
            for row in data:
                self.choices.append(row[0])
                if "selected" in row[0].attrs:
                    value = row[0].data
                    ComboCtrl.SetValue(self, value)
                    if "value" in row[0].attrs:
                        self.set_rec(row[0].attrs["value"], row[0], dismiss=False)
                    else:
                        self.set_rec(value, row[0], dismiss=False)

    def _on_ext_button_click(self, event):
        """Handle F2 accelerator for extended dialog.

        Refreshes the popup/page body with the current choices list.

        Args:
            event: The key event.

        Returns:
            Result from alternate_button_click().
        """
        ret = self.alternate_button_click()
        target = self.page if self.page else self.popup.html
        target.body.choices = self.choices
        wx.CallAfter(target.body.refr)
        return ret

    def OnButtonClick(self):
        """Handle the dropdown button click.

        Opens the popup dialog and populates it with current choices.
        """
        if self.simpleDialog:
            ret = POPUPHTML.OnButtonClick(self)
            self.popup.html.body.choices = self.choices
            wx.CallAfter(self.popup.html.body.refr)
        else:
            ret = POPUPHTML.OnButtonClick(self)
            self.page.body.choices = self.choices
            wx.CallAfter(self.page.body.refr)
        return ret

    def GetValue(self):
        """Get the current choice value.

        When readonly, returns the value from the stored record.
        Otherwise delegates to POPUPHTML.

        Returns:
            The selected value or None.
        """
        if self.readonly:
            value = self.get_rec()
            return value[0]
        else:
            return POPUPHTML.GetValue(self)

    def GetBestSize(self):
        """Return the best size, delegating to POPUPHTML.

        Returns:
            Tuple of (width, height).
        """
        dx, dy = POPUPHTML.GetBestSize(self)
        return (dx, dy)

    def GetMinSize(self):
        """Return the minimum size (same as best size)."""
        return self.GetBestSize()

    def GetMaxSize(self):
        """Return the maximum size (same as best size)."""
        return self.GetBestSize()


class DBCHOICE(CHOICE):
    """Database-bound choice control.

    Handles ctrldbchoice tag. Extends CHOICE to return the
    'value' attribute from the selected item's attrs when in
    readonly mode, making it suitable for database key selection.

    Tag arguments:
        value: Initial selection value.
    """

    def GetValue(self):
        """Get the database value of the selected item.

        When readonly, returns the 'value' attribute from the
        selected item's attrs dict (typically a database key).
        Otherwise delegates to POPUPHTML.

        Returns:
            The database value string or None.
        """
        if self.readonly:
            value = self.get_rec()
            if value:
                if hasattr(value, "attrs") and "value" in value.attrs:
                    return value.attrs["value"]
                else:
                    return value.data
            else:
                return None
        else:
            return POPUPHTML.GetValue(self)


class DBCHOICE_EXT(POPUPHTML):
    """Extended database choice control with read-only style.

    Handles ctrldbchoice_ext tag. Similar to DBCHOICE but always
    uses CB_READONLY style. Supports setting values from dicts
    with 'value', 'title', 'selected' keys, or from '!!'-delimited
    strings.

    Tag arguments:
        value: Initial selection value.
    """

    def __init__(self, parent, **kwds):
        """Initialize the extended database choice.

        Args:
            parent: Parent window.
            **kwds: Forwarded to POPUPHTML with CB_READONLY style.
        """
        if "style" in kwds:
            kwds["style"] = kwds["style"] | wx.CB_READONLY
        else:
            kwds["style"] = wx.CB_READONLY

        POPUPHTML.__init__(self, parent, **kwds)

    def SetValue(self, value):
        """Set the choice value.

        Supports multiple input formats:
        - dict with 'value', 'title', 'selected' keys
        - '!!'-delimited string: 'id:name!!' format

        Args:
            value: The value to set, in one of the supported formats.
        """
        if isinstance(value, dict):
            val = value["value"]
            title = value["title"]
            sel = value["selected"]
            if sel:
                self.set_rec(val, Td(title, {"value": val}), dismiss=False)
        else:
            if "!!" in value:
                id_part = value.split(":")[0]
                name = value[len(id_part) + 1 :].replace("!!", "")
                self.set_rec(name, [id_part, name], dismiss=False)

        POPUPHTML.SetValue(self, value)

    def GetValue(self):
        """Get the current choice value.

        When readonly, extracts the stored record value.
        Otherwise delegates to POPUPHTML.

        Returns:
            The selected value or None.
        """
        if self.readonly:
            value = self.get_rec()
            if isinstance(value, tuple) and len(value) > 0:
                return value[1][0]
            if len(value) > 0:
                return value[0]
            else:
                return None
        else:
            return POPUPHTML.GetValue(self)

    def get_parm(self, parm):
        """Get a parameter from the stored record value.

        Used for URL parameter encoding (base64).

        Args:
            parm: Parameter name ('value' supported).

        Returns:
            Base64-encoded value or None.
        """
        if len(self.rec_value) > 0:
            id_val = self.rec_value[0]
            if parm == "value":
                return b64encode(str(id_val).encode("utf-8"))
            return None
        else:
            return None
