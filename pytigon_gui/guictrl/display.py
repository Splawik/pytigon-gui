"""
Display and popup widget classes for the SchForm GUI framework.

Provides wxPython display, navigation, and popup controls:
static text, error indicator, tree, tree list, colour selector,
directory browser, editable list, file/image browse, HTML list,
and popup HTML control.

Classes:
    STATICTEXT, ERRORLIST, TREE, TREELIST, COLOURSELECT,
    GENERICDIR, EDITABLELISTBOX, FILEBROWSEBUTTON,
    IMAGEBROWSEBUTTON, HTMLLISTBOX, POPUPHTML
"""

import os
from pathlib import Path
import logging

import wx
from wx.lib import colourselect, filebrowsebutton
from wx.lib.agw.hypertreelist import HyperTreeList as TreeListCtrl
import wx.lib.imagebrowser

from pytigon_gui.guictrl.basectrl import SchBaseCtrl
from pytigon_gui.guictrl.button.toolbarbutton import BitmapTextButton
from pytigon_gui.guictrl.popup.popuphtml import DataPopupControl
from pytigon_gui.guilib.image import bitmap_from_href
from pytigon_lib.schhtml.wxdc import DcDc
from pytigon_lib.schhtml.htmlviewer import HtmlViewerParser
from pytigon_lib.schparser.html_parsers import ShtmlParser

from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Basic display controls
# ---------------------------------------------------------------------------


class STATICTEXT(wx.StaticText, SchBaseCtrl):
    """Static non-editable text label.

    Handles ctrlstatictext tag. Displays read-only text.

    Tag arguments:
        label: The text to display.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.StaticText.__init__(self, parent, **kwds)
        if self.label:
            self.SetLabel(self.label)


class ERRORLIST(BitmapTextButton, SchBaseCtrl):
    """Error indicator button with tooltip.

    Handles ctrlerrorlist tag. Displays an error icon with a
    tooltip showing the error message from ldata or param['data'].

    Tag arguments:
        value: Error data (via ldata or param).
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        self.bmp = bitmap_from_href("client://status/dialog-error.png", 1)
        kwds["style"] = wx.NO_BORDER
        kwds["bitmap"] = self.bmp
        BitmapTextButton.__init__(self, parent, **kwds)
        if self.ldata:
            self.SetToolTip(wx.ToolTip(self.ldata[0][0]))
        elif self.param and "data" in self.param:
            self.SetToolTip(wx.ToolTip(self.param["data"]))


# ---------------------------------------------------------------------------
# Tree controls
# ---------------------------------------------------------------------------


class TREE(wx.TreeCtrl, SchBaseCtrl):
    """Tree control with hierarchical data.

    Handles ctrltree tag. Builds a tree from ldata with folder/file
    icons and supports activation (navigation) on click.

    Tag arguments:
        value: Not directly used; data from ldata.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        kwds["style"] = wx.TR_HIDE_ROOT | wx.TR_DEFAULT_STYLE
        wx.TreeCtrl.__init__(self, parent, **kwds)

        isz = (16, 16)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz)
        )
        self.fldropenidx = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz)
        )
        self.fileidx = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz)
        )
        self.fileidxmark = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_OTHER, isz)
        )
        self.SetImageList(il)
        self.il = il
        self.root = self.AddRoot("/")

        ldata = self.get_ldata()
        if ldata:
            self._append_list(self.root, ldata)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._on_activated)

    def _append_list(self, parent_item, items):
        """Recursively append items from ldata to the tree.

        Args:
            parent_item: Parent wx.TreeItemId.
            items: List of [label, children, attrs] rows.
        """
        for row in items:
            child = self.AppendItem(parent_item, row[0])
            self.SetItemData(child, dict(row[2]))
            if len(row[1]) > 0:
                self.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
                self.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)
                self._append_list(child, row[1])
            else:
                self.SetItemImage(child, self.fileidx, wx.TreeItemIcon_Normal)
                self.SetItemImage(child, self.fileidxmark, wx.TreeItemIcon_Selected)

    def _on_activated(self, event):
        """Handle item activation (Enter/double-click).

        If the item has an 'href' attribute, navigates to it.

        Args:
            event: wx.TreeEvent.
        """
        item_id = event.GetItem()
        if item_id.IsOk():
            item = self.GetPyData(item_id)
            if "href" in item:
                self.GetParent().href_clicked(self, item)
        event.Skip()


class TREELIST(TreeListCtrl, SchBaseCtrl):
    """Tree list with multiple columns.

    Handles ctrltreelist tag. Supports '||' separated column data
    and folder/file icons.

    Tag arguments:
        value: Not directly used.
        label: Column titles separated by '||'.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        kwds["agwStyle"] = wx.TR_HIDE_ROOT
        TreeListCtrl.__init__(self, parent, **kwds)

        isz = (16, 16)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz)
        )
        self.fldropenidx = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz)
        )
        self.fileidx = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz)
        )
        self.fileidxmark = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_OTHER, isz)
        )
        self.SetImageList(il)
        self.il = il

        columns = self.label.split("||")
        for col_title in columns:
            try:
                self.AppendColumn(col_title)
            except AttributeError:
                self.AddColumn(col_title)
        self.SetColumnWidth(0, 175)
        self.root = self.AddRoot("/")

        ldata = self.get_ldata()
        if ldata:
            self._append_list(self.root, ldata)
        self.Refresh()

    def _append_list(self, parent_item, items):
        """Recursively append multi-column items.

        Args:
            parent_item: Parent item ID.
            items: List of ['col0||col1||...', children, attrs] rows.
        """
        for row in items:
            cols = row[0].split("||")
            child = self.AppendItem(parent_item, cols[0])
            try:
                self.SetItemData(child, None)
            except Exception:
                logger.debug("SetItemData failed for tree child", exc_info=True)
            for i in range(len(cols) - 1):
                self.SetItemText(child, cols[i + 1], i + 1)
            if len(row[1]) > 0:
                self.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
                self._append_list(child, row[1])
            else:
                self.SetItemImage(child, self.fileidx, wx.TreeItemIcon_Normal)


# ---------------------------------------------------------------------------
# Selection / file controls
# ---------------------------------------------------------------------------


class COLOURSELECT(colourselect.ColourSelect, SchBaseCtrl):
    """Colour selection dropdown.

    Handles ctrlcolourselect tag.

    Tag arguments:
        value: Initial colour.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if "name" in kwds:
            del kwds["name"]
        colourselect.ColourSelect.__init__(self, parent, id=-1, **kwds)


class GENERICDIR(wx.GenericDirCtrl, SchBaseCtrl):
    """Directory browser tree.

    Handles ctrlgenericdir tag.

    Tag arguments:
        value: Initial directory.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.GenericDirCtrl.__init__(self, parent, **kwds)


class EDITABLELISTBOX(wx.adv.EditableListBox, SchBaseCtrl):
    """Editable list box with add/remove buttons.

    Handles ctrleditablelistbox tag.

    Tag arguments:
        value: Initial list content.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.adv.EditableListBox.__init__(self, parent, **kwds)


class FILEBROWSEBUTTON(filebrowsebutton.FileBrowseButton, SchBaseCtrl):
    """File browse button with text field and Browse button.

    Handles ctrlfilebrowsebutton tag.

    Tag arguments:
        value: Initial file path.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        kwds["labelText"] = ""
        kwds["buttonText"] = str(_("Browse"))
        kwds["size"] = (400, -1)
        filebrowsebutton.FileBrowseButton.__init__(self, parent, **kwds)

    def GetValue(self):
        """Return the file path prefixed with '@'."""
        return "@" + super(FILEBROWSEBUTTON, self).GetValue()


class IMAGEBROWSEBUTTON(FILEBROWSEBUTTON, SchBaseCtrl):
    """Image browse button with preview dialog.

    Handles ctrlimagebrowsebutton tag. Uses ImageDialog for
    visual image selection.

    Tag arguments:
        value: Initial image path.
    """

    def OnBrowse(self, event=None):
        """Open the image browser dialog.

        Args:
            event: Button event (optional).
        """
        current = self.GetValue()
        directory = Path(current).parent
        if Path(current).is_dir():
            directory = current
            current = ""
        elif directory and Path(directory).is_dir():
            current = Path(current).name
            directory = str(directory)
        else:
            directory = self.startDirectory
            current = ""

        dlg = wx.lib.imagebrowser.ImageDialog(self, current)
        if dlg.ShowModal() == wx.ID_OK:
            self.SetValue(dlg.GetFile())
        dlg.Destroy()


# ---------------------------------------------------------------------------
# HTML list box
# ---------------------------------------------------------------------------

INIT_CSS_STR = """
body {font-family:sans-serif;font-size:150%; padding:1;}
table {border:0;vertical-align:top; padding:1;}
td table { padding: 1; }
th {border:0; cellpadding:1;}
td {border:0; vertical-align:top; cellpadding:1;}
strong,b {font-weight:bold;}
p { cellpadding:1; border:0; width:100%; }
"""


class HTMLLISTBOX(wx.VListBox, SchBaseCtrl):
    """HTML-rendered virtual list box.

    Handles ctrlhtmllist tag. Uses HtmlViewerParser to render
    each item as HTML within a virtual scrolling list.

    Tag arguments:
        value: Selection value.
        multiple: If in param, enables multi-select.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        self.choices = []
        self.getItemFunct = None
        self.h = None

        if self.param and "multiple" in self.param:
            style = kwds.get("style", 0)
            style |= wx.LB_MULTIPLE
            kwds["style"] = style

        if "size" in kwds:
            size = kwds["size"]
            if size[1] == -1:
                kwds["size"] = (size[0], 100)

        tdata = self.get_tdata()
        if tdata:
            for row in tdata:
                if hasattr(row[0], "attrs") and "value" in row[0].attrs:
                    selected = "selected" in row[0].attrs
                    self._append_html(row[0].attrs["value"], selected, row[0].data)
                else:
                    self._append_html(-1, False, row[0].data)

        wx.VListBox.__init__(self, parent, **kwds)
        self.SetItemCount(len(self.choices))
        for i, choice in enumerate(self.choices):
            if choice[1]:
                self.SetSelection(i)
        self.ScrollToRow(0)

    def _append_html(self, item_id, selected, html_txt):
        """Append an HTML item. '[' and ']' are converted to '<' and '>'."""
        self.choices.append(
            (item_id, selected, html_txt.replace("[", "<").replace("]", ">"))
        )

    def append_html(self, html_txt):
        """Append a plain HTML item."""
        self._append_html(-1, False, html_txt)

    def append_text(self, txt):
        """Append plain text (newlines stripped)."""
        self.append_html(txt.replace("\n", ""))
        self.SetItemCount(len(self.choices))
        self.Refresh()

    def append_texts(self, txt_list):
        """Append multiple text items."""
        for txt in txt_list:
            self.append_html(txt.replace("\n", ""))
        self.SetItemCount(len(self.choices))
        self.SetSelection(len(self.choices) - 1)
        self.Refresh()

    def GetValue(self):
        """Return selected item IDs (multi-select only)."""
        ret = []
        if self.HasMultipleSelection():
            item, cookie = self.GetFirstSelected()
            while item != wx.NOT_FOUND:
                ret.append(self.choices[item][0])
                item, cookie = self.GetNextSelected(cookie)
        return ret

    def _calc_or_draw(self, n, dc, rect, calc_only):
        """Measure or render item n.

        Args:
            n: Item index.
            dc: wx.DC.
            rect: Drawing rectangle or None.
            calc_only: If True, only measure; else draw.

        Returns:
            (width, height) tuple.
        """
        w = self.GetSize()[0]
        value = "<html><body>" + self.choices[n][2] + "</body></html>"
        wxdc = DcDc(dc, calc_only=calc_only, width=w, height=-1)

        if rect:
            wxdc2 = wxdc.subdc(rect.X + 2, rect.Y, rect.Width - 4, rect.Height)
        else:
            wxdc2 = wxdc

        p = HtmlViewerParser(dc=wxdc2, calc_only=calc_only, init_css_str=INIT_CSS_STR)
        p.set_http_object(wx.GetApp().http)
        p.set_parent_window(self)
        try:
            p.feed(value)
        except Exception:
            logger.error("ERROR: %s", value)

        w2, h2 = p.get_max_sizes()
        if not self.h:
            self.h = h2
        return w2, h2

    def OnMeasureItem(self, n):
        """Measure item n height."""
        dc = wx.ClientDC(self)
        w, h = self._calc_or_draw(n, dc, None, True)
        return h

    def OnDrawItem(self, dc, rect, n):
        """Draw item n."""
        self._calc_or_draw(n, dc, rect, False)

    def CanAcceptFocus(self):
        return False

    def GetBestSize(self):
        if self.h:
            return (400, self.h + 2)
        return (400, 200)

    def scroll_to_line(self, line_no):
        """Scroll to and select line_no."""
        nr = line_no
        count = self.GetItemCount()
        if count > 0:
            if nr >= count:
                nr = count - 1
            if nr < 0:
                nr = 0
            self.SetSelection(nr)

    def process_refr_data(self, **kwds):
        """Refresh from new data."""
        self.init_base(kwds)
        self.choices = []
        tdata = self.get_tdata()
        if tdata:
            for row in tdata:
                if hasattr(row[0], "attrs") and "value" in row[0].attrs:
                    selected = "selected" in row[0].attrs
                    self._append_html(row[0].attrs["value"], selected, row[0].data)
                else:
                    self._append_html(-1, False, row[0].data)
        self.SetItemCount(len(self.choices))
        for i, choice in enumerate(self.choices):
            if choice[1]:
                self.SetSelection(i)
        self.ScrollToRow(0)


# ---------------------------------------------------------------------------
# Popup HTML control
# ---------------------------------------------------------------------------


class POPUPHTML(DataPopupControl, SchBaseCtrl):
    """Popup HTML control with data-driven dialog.

    Handles ctrlpopuphtml tag. A text field with a dropdown button
    that opens an HTML popup for selection. Content is loaded from
    an href endpoint.

    Tag arguments:
        value: Initial value.
        IN_NEW_WIN: If in param, uses full page instead of simple popup.

    The href base address schema:
        href + "dialog"       - address of dialog window
        href + "test?value="  - address for autocomplete records
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        DataPopupControl.__init__(self, parent, **kwds)
        if self.param and "IN_NEW_WIN" in self.param:
            self.simpleDialog = False

    def GetBestSize(self):
        dx, dy = DataPopupControl.GetBestSize(self)
        return (250, dy)
