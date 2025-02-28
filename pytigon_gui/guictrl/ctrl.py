"""Module contains all widget class which can be used on SchForm"""

from base64 import b64encode
import os
import platform
import datetime

import wx

from wx import ComboCtrl
from wx.adv import BitmapComboBox, CalendarCtrl, EditableListBox, DatePickerCtrl
from wx.lib.agw.hypertreelist import HyperTreeList as TreeListCtrl
from wx.lib import ticker, masked, colourselect, filebrowsebutton

import wx.lib.imagebrowser
import wx.lib.platebtn as platebtn
import wx.lib.buttons as buttons

from pytigon_lib.schtools import createparm
from pytigon_lib.schparser.html_parsers import ShtmlParser

from pytigon_lib.schhtml.wxdc import DcDc
from pytigon_lib.schhtml.htmlviewer import HtmlViewerParser, tdata_from_html
from pytigon_lib.schparser.html_parsers import Td
from pytigon_lib.schtools.tools import is_null

from pytigon_gui.guictrl.grid import grid, gridtable_from_proxy, tabproxy
from pytigon_gui.guiframe import page
from pytigon_gui.guilib.image import bitmap_from_href

from pytigon_gui.guictrl.grid.gridtable_from_html_table import SimpleDataTable
from pytigon_gui.guictrl.grid.gridpanel import SchGridPanel
from pytigon_gui.guictrl.popup.popuphtml import DataPopupControl
from pytigon_gui.guictrl.popup.select2 import Select2Base
from pytigon_gui.guictrl.basectrl import SchBaseCtrl, handle_best_size
from pytigon_gui.guictrl.button.toolbarbutton import BitmapTextButton

from django.utils.translation import gettext_lazy as _


def SELECT(parent, **kwds):
    """SELECT handle ctrlselect tag

    Tag arguments:
        multiple -
    """
    size = 1
    multiple = False

    if "param" in kwds:
        param = kwds["param"]
        if "multiple" in param:
            multiple = True
        if "size" in param:
            size = int(param["size"])
        if multiple and size == 1:
            size = 10

        if "schtype" in param and param["schtype"] in (
            "HeavySelect2Field",
            "HeavySelect2MultipleField",
            "ModelSelect2Field",
            "ModelSelect2MultipleField",
        ):
            kwds["param"]["data"] = [
                kwds["param"],
            ]
            kwds["param"]["data"][0]["attrs"] = kwds["param"]

            return SELECT2(parent, **kwds)
    else:
        size = 1

    if size == 1:
        kwds["readonly"] = True
        return DBCHOICE(parent, **kwds)
    else:
        kwds["length"] = size
        #        return HTMLLISTBOX(parent, **kwds)
        # return CHECKLIST(parent, **kwds)
        return CHECKLISTBOX(parent, **kwds)


def BUTTON(parent, **kwds):
    """BUTTON handle ctrlbutton tag

    Tag arguments:
        src - link to button bitmap

    Subclass:
        SIMPLE_BUTTON
        BITMAPBUTTON
        PLATEBUTTON
        GENBITMAPBUTTON
        GENBITMAPTEXTBUTTON
        GENBITMAPBUTTONTXT
        GENBITMAPBUTTONTXT_SMALL
        NOBG_BUTTON
        NOBG_BUTTON_TXT
        CLOSEBUTTON
        MENUBUTTON
        MENUTOOLBARBUTTON
    """
    if "param" in kwds and "btn-class" in kwds["param"]:
        c = kwds["param"]["btn-class"]
        if c == "SIMPLE_BUTTON":
            return SIMPLE_BUTTON(parent, **kwds)
        elif c == "BITMAPBUTTON":
            return BITMAPBUTTON(parent, **kwds)
        elif c == "PLATEBUTTON":
            return PLATEBUTTON(parent, **kwds)
        elif c == "GENBITMAPBUTTON":
            return GENBITMAPBUTTON(parent, **kwds)
        elif c == "GENBITMAPBUTTONTXT":
            return GENBITMAPBUTTONTXT(parent, **kwds)
        elif c == "GENBITMAPBUTTONTXT_SMALL":
            return GENBITMAPBUTTONTXT_SMALL(parent, **kwds)
        elif c == "NOBG_BUTTON":
            return NOBG_BUTTON(parent, **kwds)
        elif c == "NOBG_BUTTON_TXT":
            return NOBG_BUTTON_TXT(parent, **kwds)
        elif c == "CLOSEBUTTON":
            return CLOSEBUTTON(parent, **kwds)
        elif c == "MENUBUTTON":
            return MENUBUTTON(parent, **kwds)
        elif c == "MENUTOOLBARBUTTON":
            return MENUTOOLBARBUTTON(parent, **kwds)
    if "src" in kwds:
        ctrl = BITMAPBUTTON(parent, **kwds)
    else:
        ctrl = SIMPLE_BUTTON(parent, **kwds)
    return ctrl


def _make_button_class(
    base_class, is_bitmap_button=False, is_close_button=False, icon_size=2
):
    class BUTTONCLASS(base_class, SchBaseCtrl):
        def __init__(self, parent, **kwds):
            SchBaseCtrl.__init__(self, parent, kwds)
            if is_bitmap_button:
                self._set_bitmap()
                if (
                    base_class == buttons.GenBitmapButton
                    or base_class == BitmapTextButton
                ):
                    if "style" in kwds:
                        style = kwds["style"] | wx.NO_BORDER
                        kwds["style"] = style
                    else:
                        style = wx.NO_BORDER
                        kwds["style"] = wx.NO_BORDER
                    kwds["bitmap"] = self.bmp
                elif base_class == buttons.GenBitmapTextButton:
                    kwds["bitmap"] = self.bmp
                elif base_class == platebtn.PlateButton:
                    kwds["style"] = (
                        platebtn.PB_STYLE_SQUARE | platebtn.PB_STYLE_GRADIENT
                    )
                    kwds["bmp"] = self.bmp
                else:
                    if "style" in kwds:
                        style = kwds["style"]
                    else:
                        kwds["style"] = 0
                        style = 0
                    kwds["bitmap"] = self.bmp

                if base_class != wx.BitmapButton:
                    if self.label:
                        kwds["label"] = self.label.replace("&", "")
            else:
                if "style" not in kwds:
                    kwds["style"] = 0
                    style = 0
                if self.label:
                    kwds["label"] = self.label.replace("&", "")
                if self.nr_id:
                    try:
                        nr_id = int(self.nr_id)
                    except:
                        if "wx." in self.nr_id:
                            nr_id = eval(self.nr_id)
                        else:
                            nr_id = None
                    if nr_id != None:
                        kwds["id"] = nr_id

            if "fields" in kwds:
                self.fields = kwds["fields"]
                del kwds["fields"]
            else:
                self.fields = None

            base_class.__init__(self, parent, **kwds)

            if self.defaultvalue:
                self.SetDefault()
                self.parent.any_parent_command("set_default_button", self)

            if is_bitmap_button and self.label:
                self.SetToolTip(self.label.replace("&", ""))

            if is_close_button:
                self.Bind(wx.EVT_BUTTON, self.on_exit)
            else:
                self.Bind(wx.EVT_BUTTON, self.on_click, self)

            if self.label and base_class == BitmapTextButton:
                self.SetToolTip(wx.ToolTip(self.label.replace("&", "")))

            if self.label and "&" in self.label:
                id = self.label.find("&")
                l = self.label[id + 1 : id + 2]
                if l:
                    aTable = [
                        (wx.ACCEL_ALT, ord("N"), self.on_acc_click),
                    ]
                    self.set_acc_key_tab(aTable)

            self.init2()

        def on_acc_click(self, event):
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            wx.PostEvent(self, evt)

        def _set_bitmap(self):
            self.bmp = None
            if is_bitmap_button:
                if is_close_button:
                    self.src = "png://emblems/emblem-unreadable.png"
                if self.src:
                    self.bmp = bitmap_from_href(self.src, icon_size)

        def process_refr_data(self, **kwds):
            self.init_base(kwds)

            if is_bitmap_button:
                self._set_bitmap()

                if base_class == platebtn.PlateButton:
                    kwds["bmp"] = self.bmp
                else:
                    kwds["bitmap"] = self.bmp

            if "fields" in kwds:
                self.fields = kwds["fields"]
                del kwds["fields"]
            else:
                self.fields = None

            if "href" in kwds:
                self.href = kwds["href"]
                del kwds["href"]

            if self.defaultvalue:
                self.SetDefault()

            self.init2()

        def init2(self):
            if self.href == "_hide":
                self.Hide()
            else:
                self.Show()
            if self.href == "_disable":
                self.Enable(False)
            else:
                self.Enable(True)
            if not self.style:
                self.style = 0

        def CanAcceptFocus(self):
            return False

        if is_close_button:

            def on_exit(self, event):
                def fun():
                    self.GetParent().any_parent_command("on_child_form_cancel")

                wx.CallAfter(fun)

        else:

            def on_click(self, event):
                upload = False
                if self.valuetype == "upload":
                    upload = True
                if hasattr(self, "href"):
                    href = self.href
                else:
                    href = ""
                self.get_parent_form().href_clicked(
                    self, {"href": href, "target": self.target}, upload, self.fields
                )

    return BUTTONCLASS


SIMPLE_BUTTON = _make_button_class(wx.Button)
BITMAPBUTTON = _make_button_class(wx.BitmapButton, is_bitmap_button=True)
PLATEBUTTON = _make_button_class(platebtn.PlateButton, is_bitmap_button=True)
GENBITMAPBUTTON = _make_button_class(buttons.GenBitmapButton, is_bitmap_button=True)
GENBITMAPTEXTBUTTON = _make_button_class(
    buttons.GenBitmapTextButton, is_bitmap_button=True
)
GENBITMAPBUTTONTXT = _make_button_class(BitmapTextButton, is_bitmap_button=True)
GENBITMAPBUTTONTXT_SMALL = _make_button_class(
    BitmapTextButton, is_bitmap_button=True, icon_size=1
)
NOBG_BUTTON = GENBITMAPBUTTONTXT
NOBG_BUTTON_TXT = GENBITMAPBUTTONTXT
CLOSEBUTTON = _make_button_class(
    BitmapTextButton, is_bitmap_button=True, is_close_button=True
)


def _make_menu_button_class(base_class):
    class _MENUBUTTON(base_class):
        def __init__(self, parent, **kwds):
            base_class.__init__(self, parent, **kwds)
            ldata = self.get_ldata()
            self._menu = None
            self.href_dict = {}
            if ldata:
                menu = wx.Menu()
                for row in ldata:
                    if row[0].replace("-", "").strip():
                        menu.Append(wx.NewId(), row[0], row[2]["href"])
                        self.href_dict[row[0]] = row[2]
                    else:
                        menu.AppendSeparator()
                self.SetMenu(menu)

            self.Bind(wx.EVT_MENU, self.on_menu)
            self.Bind(wx.EVT_BUTTON, self.on_button)

        def on_button(self, evt):
            self.ShowMenu()

        def on_menu(self, evt):
            e_obj = evt.GetEventObject()
            mitem = e_obj.FindItemById(evt.GetId())
            if mitem != wx.NOT_FOUND:
                label = mitem.GetItemLabel()
                item = self.href_dict[label]
                self.GetParent().href_clicked(self, item)

        def SetMenu(self, menu):
            self._menu = menu

        def ShowMenu(self):
            self.PopupMenu(self._menu, 1, self.GetSize()[1] - 1)

    return _MENUBUTTON


MENUBUTTON = _make_menu_button_class(SIMPLE_BUTTON)
MENUTOOLBARBUTTON = _make_menu_button_class(GENBITMAPBUTTONTXT)


class CHECKBOX(wx.CheckBox, SchBaseCtrl):
    """CHECKBOX handle ctrlcheckbox tag

    Tag arguments:
        checked - check checkbock
        value - if True checkbock is check else is not check
        label - checkbox label
    """

    def __init__(self, parent, **kwds):
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
        value = wx.CheckBox.GetValue(self)
        if value == True:
            if self.value:
                return str(self.value)
            else:
                return True
        else:
            return None

    def SetValue(self, value):
        if type(value) == bool:
            return wx.CheckBox.SetValue(self, value)
        else:
            self.value = value


@handle_best_size
class CHECKLISTBOX(wx.CheckListBox, SchBaseCtrl):
    """CHECKBOXLIST handle ctrlchecklistbox tag

    Tag arguments:
        checked - check checkbock
        value - if True checkbock is check else is not check
        label - checkbox label
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)

        if "style" in kwds:
            kwds["style"] |= wx.WANTS_CHARS
        else:
            kwds["style"] = wx.WANTS_CHARS
        wx.CheckListBox.__init__(self, parent, **kwds)
        self.init_data(self.get_tdata())

    def init_data(self, data):
        checked_items = []
        if data:
            for row in data:
                id = self.Append(row[0].data)
                if "selected" in row[0].attrs:
                    checked_items.append(id)
        if checked_items:
            self.SetCheckedItems(checked_items)

    def process_refr_data(self, **kwds):
        self.init_base(kwds)
        self.Clear()
        self.init_data(self.get_tdata())

    def GetBestSize(self):
        return (300, 68)

    def GetMinSize(self):
        return self.GetBestSize()

    def GetValue(self):
        ret = []
        data = self.get_tdata()
        items = self.GetCheckedItems()
        for item in items:
            if hasattr(data[item][0], "attrs") and "value" in data[item][0].attrs:
                ret.append(data[item][0].attrs["value"])
            else:
                ret.append(data[item][0].data)
        return ret


class BITMAPCOMBOBOX(BitmapComboBox, SchBaseCtrl):
    """BITMAPCOMBOBOX handle ctrlbitmapcombobox tag"""

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        BitmapComboBox.__init__(self, parent, **kwds)
        self.init_default_icons = False
        self._first_use = True
        self.accept_focus = False

    def after_create(self):
        super().after_create()
        if self.init_default_icons:

            def _fun():
                self.init_embeded_icons()
                self.init_fa_icons()

            wx.CallAfter(_fun)

    def init_wx_icons(self):
        for id in sorted([pos for pos in dir(wx) if pos.startswith("ART_")]):
            artid = getattr(wx, id)
            bmp = wx.ArtProvider.GetBitmap(artid, wx.ART_TOOLBAR, (22, 22))
            if bmp.IsOk():
                self.Append(id, bmp, id)

    def init_embeded_icons(self):
        base_path = wx.GetApp().src_path + "/static/icons/22x22/"
        return self._init_icons(base_path, "png://")

    def init_fa_icons(self):
        base_path = wx.GetApp().src_path + "/static/fonts/fork-awesome/fonts/22x22/"
        return self._init_icons(base_path, "fa://")

    def init_extern_icons(self, base_path, prefix):
        return self._init_icons(base_path, prefix)

    def _init_icons(self, base_path, prefix, subpath=None):
        if subpath:
            dirname = os.path.join(base_path, subpath)
        else:
            dirname = base_path

        if os.path.exists(dirname):
            for ff in os.listdir(dirname):
                if os.path.isdir(os.path.join(dirname, ff)):
                    if subpath:
                        self._init_icons(base_path, prefix, os.path.join(subpath, ff))
                    else:
                        self._init_icons(base_path, prefix, ff)
                else:
                    if ".png" in ff.lower():
                        try:
                            path = dirname + "/" + ff
                            image = wx.Image(path)
                            bmp = wx.Bitmap(image)
                            if subpath:
                                id = prefix + subpath + "/" + ff
                            else:
                                id = prefix + ff
                            self.Append(id.replace("\\", "/"), bmp, id)
                        except:
                            pass
                wx.Yield()

    def GetValue(self):
        ret = super().GetValue()
        if ret:
            return ret
        else:
            return ""

    def SetValue(self, value):
        if value:
            ret = super().SetValue(value)
        else:
            ret = super().SetValue("")
        return ret


class GAUGE(wx.Gauge, SchBaseCtrl):
    """GAUBE handle ctrlgauge tag

    Tag arguments:
        value - if True checkbock is check else is not check
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.Gauge.__init__(self, parent, **kwds)

    def process_refr_data(self, **kwds):
        self.init_base(kwds)
        if self.value:
            self.SetValue(self.value)


class LISTBOX(wx.ListBox, SchBaseCtrl):
    """LISTBOX handle ctrllistbox tag

    Tag arguments:
        value - if True checkbock is check else is not check
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        self._norefresh = False

        if self.param and "multiple" in self.param:
            style = 0
            if "style" in kwds:
                style = kwds["style"]
            style = style | wx.LB_MULTIPLE
            kwds["style"] = style

        wx.ListBox.__init__(self, parent, **kwds)

        self.init_choices(self.get_tdata())

    def block_refresh(self):
        self._norefresh = True

    def find_and_select(self, item):
        """find first occurrence of item in list and select it"""
        l = self.GetStrings()
        for i in range(len(l)):
            if l[i].startswith(item):
                self.SetSelection(i)
                return

    def process_refr_data(self, **kwds):
        self.init_base(kwds)
        if not self._norefresh:
            self.Clear()
            self.refresh_tdata()
            self.init_choices(self.get_tdata())

    def init_choices(self, data):
        self.choices = []
        self.selected_rows = []
        if data:
            i = 0
            for row in data:
                value = row[0].data
                self.Append(value)
                if "value" in row[0].attrs:
                    self.choices.append(row[0].attrs["value"])
                else:
                    self.choices.append(value)
                if "selected" in row[0].attrs:
                    self.selected_rows.append(i)
                i += 1
        if self.selected_rows:
            for j in self.selected_rows:
                self.SetSelection(j)

    def GetValue(self):
        ret = []
        sel = self.GetSelections()
        for s in sel:
            ret.append(self.choices[s])
        return ret


class LIST(wx.ListCtrl, SchBaseCtrl):
    """LIST handle ctrllist tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)

        if "style" in kwds:
            kwds["style"] = kwds["style"] | wx.LC_REPORT
        else:
            kwds["style"] = wx.LC_REPORT
        kwds["size"] = wx.Size(-1, -1)

        wx.ListCtrl.__init__(self, parent, **kwds)

        tdata = self.get_tdata()
        l = 0
        if tdata:
            test = False
            for row in tdata:
                if test == False:
                    test = True
                    l = len(row)
                    for i in range(l):
                        self.InsertColumn(i, row[i].data)
                else:
                    index = self.InsertItem(0, row[0].data)
                    for i in range(1, l):
                        self.SetItem(index, i, row[i].data)

            for i in range(0, l):
                self.SetColumnWidth(i, -1)

    def process_refr_data(self, **kwds):
        self.init_base(kwds)
        self.ClearAll()
        tdata = self.get_tdata()
        if tdata:
            test = False
            for row in tdata:
                if test == False:
                    test = True
                    l = len(row)
                    for i in range(l):
                        self.InsertColumn(i, row[i].data)
                else:
                    index = self.InsertStringItem(0, row[0].data)
                    for i in range(1, l):
                        self.SetStringItem(index, i, row[i].data)


class CHECKLIST(LIST):
    def __init__(self, parent, **kwds):
        super().__init__(parent, **kwds)
        self.EnableCheckBoxes()
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

    def ToggleItem(self, index):
        toggle = not self.IsItemChecked(index)
        self.CheckItem(index, toggle)

    def OnItemActivated(self, evt):
        self.ToggleItem(evt.Index)

    def GetBestSize(self):
        return (400, 48)


class TABLE(SchGridPanel, SchBaseCtrl):
    """TABLE handle ctrltable tag

    Tag arguments:
        value
    """

    def get_table_lp(self):
        return self._table_lp

    def set_table_lp(self, table_lp):
        self._table_lp = table_lp

    table_lp = property(get_table_lp, set_table_lp)

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param and "table_lp" in self.param:
            self.table_lp = int(self.param["table_lp"])
        else:
            self.table_lp = 0

        if "name" in kwds:
            name = kwds["name"]
        else:
            name = "LIST"

        if "size" in kwds:
            SchGridPanel.__init__(self, parent, size=kwds["size"], name=name)
        else:
            SchGridPanel.__init__(self, parent, name=name)

        tdata = self.get_tdata()
        if not tdata:
            print("no tdata:", self.href, self.src)
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
        # self.get_parent_page().register_signal(self, "refresh_controls")
        self.create_toolbar(self.grid)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self._table = table
        for signal_name in ("update_row_ok", "new_row_ok", "delete_row_ok"):
            self.get_parent_page().register_signal(self, signal_name)

    def on_close(self, event):
        for signal_name in ("update_row_ok", "new_row_ok", "delete_row_ok"):
            self.get_parent_page().unregister_signal(self, signal_name)
        event.Skip()

    def delete_row_ok(self, data):
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
        return self._row_ok(data, insert=False)

    def new_row_ok(self, data):
        return self._row_ok(data, insert=True)

    def _row_ok(self, data, insert=False):
        url = self.GetParent().address
        if url:
            if "id" in data:
                pk = data["id"]
            else:
                pk = data["pk"]
            if "?" in url:
                url += "&pk=" + str(pk)
            else:
                url += "?pk=" + str(pk)
            http = wx.GetApp().get_http(self)
            response = http.get(self, url)
            if response.ret_code == 404:
                return
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

    def GetMinSize(self):
        return SchGridPanel.GetMinSize(self)

    def process_refr_data(self, **kwds):
        self.grid.last_action = ""
        self.init_base(kwds)
        tdata = self.get_tdata()
        return self.do_refresh(tdata)

    def do_refresh(self, tdata):
        oldRow = self.grid.GetGridCursorRow()
        self._table.replace_tab(tdata)
        # self.grid.AutoSizeColumns(False)
        # self.grid.AutoSizeRows(True)
        if self.grid.last_action == "insert":
            newRow = self.grid.GetGridCursorRow() + 1
            if newRow < self.grid.GetTable().GetNumberRows():
                self.grid.SetGridCursor(newRow, 0)
                self.grid.MakeCellVisible(newRow, 0)
        else:  # self.grid.last_action == 'edit':
            if oldRow < self.grid.GetTable().GetNumberRows():
                if oldRow < 0:
                    oldRow = 0
                self.grid.SetGridCursor(oldRow, 0)
                self.grid.MakeCellVisible(oldRow, 0)
            else:
                self.grid.goto_last_row()

    def refresh_from_source(self, html_src):
        self.refresh_tdata(html_src)
        tdata = self.get_tdata()
        return self.do_refresh(tdata)

    # def refresh_controls(self):
    #    self.get_parent_form().enable_ctrls((self,))
    #    ret = self.get_parent_page()._refresh_html()
    #    self.get_parent_form().enable_ctrls(None)
    #    return ret


class RADIOBOX(wx.RadioBox, SchBaseCtrl):
    """RADIOBOX handle ctrlradiobox tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        tdata = self.get_tdata()
        if tdata:
            choices = []

            for row in tdata:
                choices.append(row[0].data)

            kwds["choices"] = choices
        wx.RadioBox.__init__(self, parent, **kwds)

    def process_refr_data(self, **kwds):
        self.init_base(kwds)
        self.Clear()
        self.refresh_tdata()
        tdata = self.get_tdata()
        if tdata:
            for row in tdata:
                self.Append(row[0].data)


class RADIOBUTTON(wx.RadioButton, SchBaseCtrl):
    """RADIOBUTTON handle ctrlradiobutton tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if "name" in kwds:
            name = kwds["name"]
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
        value = wx.RadioButton.GetValue(self)
        if value == True:
            if self.value:
                return str(self.value)
            else:
                return None
        else:
            return None

    def SetValue(self, value):
        if value.__class__ == bool:
            return wx.RadioButton.SetValue(self, value)
        else:
            self.value = value


class SLIDER(wx.Slider, SchBaseCtrl):
    """SLIDER handle ctrlslider tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.Slider.__init__(self, parent, **kwds)


# class SPINBUTTON(wx.SpinButton, SchBaseCtrl):
#    """SPINBUTTON handle ctrlspinbutton tag
#
#    Tag arguments:
#        value
#    """
#
#    def __init__(self, parent, **kwds):
#        SchBaseCtrl.__init__(self, parent, kwds)
#        wx.SpinButton.__init__(self, parent, **kwds)


class SPIN(wx.SpinCtrl, SchBaseCtrl):
    """SPIN handle ctrlspinbutton tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.SpinCtrl.__init__(self, parent, **kwds)


class STATICTEXT(wx.StaticText, SchBaseCtrl):
    """STATICTEXT handle ctrlstatictext tag

    Tag arguments:
        label
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.StaticText.__init__(self, parent, **kwds)
        if self.label:
            self.SetLabel(self.label)


class ERRORLIST(BitmapTextButton, SchBaseCtrl):
    """ERRORLIST handle ctrlerrorlist tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)

        self.bmp = bitmap_from_href("client://status/dialog-error.png", 1)

        kwds["style"] = wx.NO_BORDER
        kwds["bitmap"] = self.bmp

        BitmapTextButton.__init__(self, parent, **kwds)
        if self.ldata:
            self.SetToolTip(wx.ToolTip(self.ldata[0][0]))
        else:
            if "data" in self.param:
                self.SetToolTip(wx.ToolTip(self.param["data"]))


class TEXT(SchBaseCtrl, wx.TextCtrl):
    """TEXT handle ctrltext tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param and "process_enter" in self.param:
            kwds["style"] = wx.TE_PROCESS_ENTER
        wx.TextCtrl.__init__(self, parent, **kwds)
        if self.hidden:
            self.Enable(False)
        if self.maxlength:
            self.SetMaxLength(int(self.maxlength))

    def SetValue(self, value):
        if type(value) == str:
            return wx.TextCtrl.SetValue(self, value)
        else:
            return wx.TextCtrl.SetValue(self, value.decode("utf-8"))

    def GetValue(self):
        return super().GetValue()

    def GetBestSize(self):
        size = super().GetBestSize()
        return (4 * size[0], size[1])


class SEARCH(wx.SearchCtrl, SchBaseCtrl):
    """SEARCH handle ctrlsearch tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if wx.Platform in [
            "__WXGTK__",
        ]:
            kwds["size"] = (200, 28)
        else:
            kwds["size"] = (200, -1)
        if self.param and "process_enter" in self.param:
            kwds["style"] = wx.TE_PROCESS_ENTER

        wx.SearchCtrl.__init__(self, parent, **kwds)

        if wx.Platform in ["__WXGTK__", "__WXMSW__"]:
            for child in list(self.GetChildren()):
                if isinstance(child, wx.TextCtrl):
                    child.Bind(wx.EVT_KEY_DOWN, self.on_key_down_base)
                    break


class PASSWORD(TEXT, SchBaseCtrl):
    """PASSWORD handle ctrlpassword tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        if "style" in kwds:
            kwds["style"] = kwds["style"] | wx.TE_PASSWORD
        else:
            kwds["style"] = wx.TE_PASSWORD

        TEXT.__init__(self, parent, **kwds)


class TREE(wx.TreeCtrl, SchBaseCtrl):
    """TREE handle ctrltree tag

    Tag arguments:
        value
    """

    def _append_list(self, parent, list):
        for row in list:
            child = self.AppendItem(parent, row[0])
            self.SetItemData(child, dict(row[2]))
            if len(row[1]) > 0:
                self.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
                self.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)
                self._append_list(child, row[1])
            else:
                self.SetItemImage(child, self.fileidx, wx.TreeItemIcon_Normal)
                self.SetItemImage(child, self.fileidxmark, wx.TreeItemIcon_Selected)

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

        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_activated)

    def on_activated(self, event):
        item_id = event.GetItem()
        if item_id.IsOk():
            item = self.GetPyData(item_id)
            # print "OnActivated:", item
            if "href" in item:
                self.GetParent().href_clicked(self, item)
        event.Skip()


class COLOURSELECT(colourselect.ColourSelect, SchBaseCtrl):
    """COLOURSELECT handle ctrlcolourselect tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if "name" in kwds:
            del kwds["name"]
        colourselect.ColourSelect.__init__(self, parent, id=-1, **kwds)


class GENERICDIR(wx.GenericDirCtrl, SchBaseCtrl):
    """GENERICDIR handle ctrlgenericdir tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.GenericDirCtrl.__init__(self, parent, **kwds)


class TREELIST(TreeListCtrl, SchBaseCtrl):
    """TREELIST handle ctrltreelist tag

    Tag arguments:
        value
    """

    def append_list(self, parent, list):
        for row in list:
            l = row[0].split("||")
            child = self.AppendItem(parent, l[0])
            try:
                self.SetItemData(child, None)
            except:
                pass

            for i in range(len(l) - 1):
                self.SetItemText(child, l[i + 1], i + 1)

            if len(row[1]) > 0:
                self.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)

                self.append_list(child, row[1])
            else:
                self.SetItemImage(child, self.fileidx, wx.TreeItemIcon_Normal)

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

        l = self.label.split("||")
        for pos in l:
            try:
                self.AppendColumn(pos)
            except:
                self.AddColumn(pos)

        self.SetColumnWidth(0, 175)
        self.root = self.AddRoot("/")
        ldata = self.get_ldata()
        if ldata:
            self.append_list(self.root, ldata)
        self.Refresh()


class CALENDAR(CalendarCtrl, SchBaseCtrl):
    """CALENDAR handle ctrlcalendar tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        try:
            CalendarCtrl.__init__(
                self,
                parent,
                style=wx.adv.CAL_MONDAY_FIRST
                | wx.adv.CAL_SHOW_HOLIDAYS
                | wx.adv.CAL_SEQUENTIAL_MONTH_SELECTION,
                **kwds,
            )
        except:
            CalendarCtrl.__init__(
                self,
                parent,
                style=wx.calendar.CAL_MONDAY_FIRST
                | wx.calendar.CAL_SHOW_HOLIDAYS
                | wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION,
                **kwds,
            )


class EDITABLELISTBOX(EditableListBox, SchBaseCtrl):
    """EDITABLELISTBOX handle ctrleditablelistbox tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        EditableListBox.__init__(self, parent, **kwds)


class FILEBROWSEBUTTON(filebrowsebutton.FileBrowseButton, SchBaseCtrl):
    """FILEBROWSEBUTTON handle ctrlfilebrowsebutton tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        kwds["labelText"] = ""
        kwds["buttonText"] = str(_("Browse"))
        kwds["size"] = (400, -1)
        filebrowsebutton.FileBrowseButton.__init__(self, parent, **kwds)

    def GetValue(self):
        return "@" + super(FILEBROWSEBUTTON, self).GetValue()


class IMAGEBROWSEBUTTON(FILEBROWSEBUTTON, SchBaseCtrl):
    """IMAGEBROWSEBUTTON handle ctrlimagebrowsebutton tag

    Tag arguments:
        value
    """

    def OnBrowse(self, event=None):
        current = self.GetValue()
        directory = os.path.split(current)
        if os.path.isdir(current):
            directory = current
            current = ""
        elif directory and os.path.isdir(directory[0]):
            current = directory[1]
            directory = directory[0]
        else:
            directory = self.startDirectory
            current = ""

        dlg = wx.lib.imagebrowser.ImageDialog(self, current)

        if dlg.ShowModal() == wx.ID_OK:
            self.SetValue(dlg.GetFile())
        dlg.Destroy()


class MASKTEXT(masked.TextCtrl, SchBaseCtrl):
    """MASKTEXT handle ctrlmasktext tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.valuetype:
            if self.src:
                if self.src.startswith("!"):
                    kwds["autoformat"] = self.src[1:]
                else:
                    kwds["mask"] = self.src
        masked.TextCtrl.__init__(self, parent, **kwds)
        self._autofit = False


class NUM(wx.SpinCtrl, SchBaseCtrl):
    """NUM handle ctrlnum tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param and "process_enter" in self.param:
            kwds["style"] = wx.TE_PROCESS_ENTER
        if self.readonly:
            style = 0
            if "style" in kwds:
                style = kwds["style"]
            style = style | wx.TE_READONLY
            kwds["style"] = style
        wx.SpinCtrl.__init__(self, parent, **kwds)


class AMOUNT(wx.SpinCtrlDouble, SchBaseCtrl):
    """handle ctrlfloat tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param and "process_enter" in self.param:
            kwds["style"] = wx.TE_PROCESS_ENTER
        if self.readonly:
            style = 0
            if "style" in kwds:
                style = kwds["style"]
            style = style | wx.TE_READONLY
            kwds["style"] = style

        kwds["inc"] = 1

        if self.param and "min" in self.param:
            kwds["min"] = float(self.param["min"])
        else:
            kwds["min"] = -100000000
        if self.param and "max" in self.param:
            kwds["max"] = float(self.param["max"])
        else:
            kwds["max"] = 100000000

        kwds["style"] = wx.SP_ARROW_KEYS | wx.ALIGN_RIGHT

        wx.SpinCtrlDouble.__init__(self, parent, **kwds)
        self.SetDigits(2)


class FLOAT(wx.SpinCtrlDouble, SchBaseCtrl):
    """handle ctrlfloat tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param and "process_enter" in self.param:
            kwds["style"] = wx.TE_PROCESS_ENTER
        if self.readonly:
            style = 0
            if "style" in kwds:
                style = kwds["style"]
            style = style | wx.TE_READONLY
            kwds["style"] = style

        kwds["inc"] = 1

        if self.param and "min" in self.param:
            kwds["min"] = float(self.param["min"])
        else:
            kwds["min"] = -100000000
        if self.param and "max" in self.param:
            kwds["max"] = float(self.param["max"])
        else:
            kwds["max"] = 100000000

        kwds["style"] = wx.SP_ARROW_KEYS | wx.ALIGN_RIGHT

        wx.SpinCtrlDouble.__init__(self, parent, **kwds)

        self.SetDigits(6)


class TIME(masked.TimeCtrl, SchBaseCtrl):
    """TIME handle ctrltime tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        masked.TimeCtrl.__init__(self, parent, **kwds)

        # self.SetEmptyBackgroundColour(wx.Colour(1,0,0))
        # self.SetValidBackgroundColour("Red")
        # self.SetInvalidBackgroundColour(wx.Colour(1,0,0))
        # self._validBackgroundColour = wx.Colour(1,0,0)


class STYLEDTEXT(wx.TextCtrl, SchBaseCtrl):
    """STYLEDTEXT handle ctrlstyledtext tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        if "style" in kwds:
            style = kwds["style"]
            style = style | wx.TE_MULTILINE
            kwds["style"] = style
        else:
            kwds["style"] = wx.TE_MULTILINE
        wx.TextCtrl.__init__(self, parent, **kwds)
        if "data" in self.param:
            self.SetValue(self.param["data"])

    def SetValue(self, value):
        if value.startswith("\n"):
            value2 = value[1:]
        else:
            value2 = value
        if type(value2) == str:
            return wx.TextCtrl.SetValue(self, value2)
        else:
            return wx.TextCtrl.SetValue(self, value2.decode("utf-8"))


AUTOCOMPLETE = STYLEDTEXT
STANDARDSTYLEDTEXT = STYLEDTEXT


def TEXTAREA(parent, **kwds):
    """TEXTAREA handle ctrltextarea tag

    Tag arguments:
        value
    """

    if "param" in kwds:
        if "data" in kwds["param"]:
            data = kwds["param"]["data"].replace("\r", "")
            if data.startswith("\n"):
                data = data[1:]
                kwds["param"]["data"] = data

    size = [-1, -1]

    if not "width" in kwds["param"]:
        if "cols" in kwds["param"]:
            width = 7 * int(is_null(kwds["param"]["cols"], "80"))
            if width > 480:
                width = 480
            kwds["param"]["width"] = str(width)
            size[0] = width
        else:
            kwds["param"]["width"] = "100%"
    if not "height" in kwds["param"]:
        if "rows" in kwds["param"]:
            size[1] = 14 + 14 * int(is_null(kwds["param"]["rows"], "3"))
            kwds["param"]["height"] = str(size[1])
        else:
            kwds["param"]["height"] = "100%"

    kwds["size"] = size

    if "cols" in kwds:
        del kwds["cols"]

    if "rows" in kwds:
        del kwds["rows"]

    if "src" in kwds:
        if kwds["src"] in ("c", "python", "html"):
            ret = STYLEDTEXT(parent, **kwds)
        else:
            ret = AUTOCOMPLETE(parent, **kwds)
    else:
        ret = STYLEDTEXT(parent, **kwds)
    return ret


class TICKER(ticker.Ticker, SchBaseCtrl):
    """TICKER handle ctrlticker tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        ticker.Ticker.__init__(self, parent, **kwds)

    def SetValue(self, value):
        self.SetText(value)

    def CanClose(self):
        self.Stop()
        return True


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
    """HTMLLISTBOX handle ctrlhtmllist tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        self.choices = []
        self.getItemFunct = None
        self.h = None
        if self.param and "multiple" in self.param:
            style = 0
            if "style" in kwds:
                style = kwds["style"]
            style = style | wx.LB_MULTIPLE
            kwds["style"] = style

        if "size" in kwds:
            size = kwds["size"]
            if size[1] == -1:
                kwds["size"] = (size[0], 100)

        tdata = self.get_tdata()
        if tdata:
            for row in tdata:
                if hasattr(row[0], "attrs") and "value" in row[0].attrs:
                    if "selected" in row[0].attrs:
                        selected = True
                    else:
                        selected = False
                    self._append_html(row[0].attrs["value"], selected, row[0].data)
                else:
                    self.append_html(row[0].data)

        wx.VListBox.__init__(self, parent, **kwds)

        self.SetItemCount(len(self.choices))
        i = 0
        for choice in self.choices:
            if choice[1]:
                self.SetSelection(i)
            i += 1

        self.ScrollToRow(0)

    def _append_html(self, id, sel, html_txt):
        self.choices.append((id, sel, html_txt.replace("[", "<").replace("]", ">")))

    def append_html(self, html_txt):
        self._append_html(-1, False, html_txt)

    def append_text(self, txt):
        self.append_html(txt.replace("\n", ""))
        self.SetItemCount(len(self.choices))
        self.Refresh()

    def append_texts(self, txt_list):
        for txt in txt_list:
            self.append_html(txt.replace("\n", ""))
        self.SetItemCount(len(self.choices))
        self.SetSelection(len(self.choices) - 1)
        self.Refresh()

    def GetValue(self):
        ret = []
        if self.HasMultipleSelection():
            item, cookie = self.GetFirstSelected()
            while item != wx.NOT_FOUND:
                ret.append(self.choices[item][0])
                item, cookie = self.GetNextSelected(cookie)
        return ret

    def _calc_or_draw(self, n, dc, rect, calc_only):
        w = self.GetSize()[0]
        value = "<html><body>" + (self.choices)[n][2] + "</body></html>"
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
        except:
            print("ERROR:", value)

        w2, h2 = p.get_max_sizes()
        if not self.h:
            self.h = h2
        return w2, h2

    def OnMeasureItem(self, n):
        dc = wx.ClientDC(self)
        w, h = self._calc_or_draw(n, dc, None, True)
        return h

    def OnDrawItem(self, dc, rect, n):
        self._calc_or_draw(n, dc, rect, False)

    def CanAcceptFocus(self):
        return False

    def GetBestSize(self):
        if self.h:
            return (400, self.h + 2)
        else:
            return (400, 200)

    def scroll_to_line(self, line_no):
        nr = line_no
        count = self.GetItemCount()
        if count > 0:
            if nr >= count:
                nr = count - 1
            if nr < 0:
                nr = 0
            self.SetSelection(nr)

    def process_refr_data(self, **kwds):
        self.init_base(kwds)
        self.choices = []
        tdata = self.get_tdata()

        if tdata:
            for row in tdata:
                if hasattr(row[0], "attrs") and "value" in row[0].attrs:
                    if "selected" in row[0].attrs:
                        selected = True
                    else:
                        selected = False
                    self._append_html(row[0].attrs["value"], selected, row[0].data)
                else:
                    self.append_html(row[0].data)
        self.SetItemCount(len(self.choices))
        i = 0
        for choice in self.choices:
            if choice[1]:
                self.SetSelection(i)
            i += 1

        self.ScrollToRow(0)

        # if tdata:
        #    for row in tdata:
        #        self.append_html(row[0].data)


#        self.SetItemCount(len(self.choices))
#        self.SetSelection(len(self.choices) - 1)


class HTML(page.SchPage, SchBaseCtrl):
    """HTML handle ctrlhtml tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        page.SchPage.__init__(self, parent, self.src, None)
        if self.src:
            value = self.load_string_from_server(self.src)
            self._set_value(value, False)
        elif self.param and "data" in self.param and len(self.param["data"]) > 0:
            self._set_value(self.param["data"], False)
        else:
            self._value = None
        self.body.Refresh()
        self.body.Update()

    def CanAcceptFocus(self):
        return False

    def SetValue(self, value):
        self._set_value(value)

    def _set_value(self, value, refresh=True):
        if not "<html" in value:
            self._value = "<html><body>%s</body></html>" % value
        else:
            self._value = value
        mp = ShtmlParser()
        mp.process(self._value)
        mp.address = None
        body = mp.get_body()
        self.body.show_page(body)
        if refresh:
            self.body.wxdc = None
            self.body.draw_background()

    def GetValue(self):
        return self._value


HTML2 = None


class NOTEBOOK(wx.Notebook, SchBaseCtrl):
    """NOTEBOOK handle ctrlnotebook tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        self.children = []
        wx.Notebook.__init__(self, parent, **kwds)
        if self.tdata:
            for row in self.tdata:
                h = page.SchPage(self, row[1].data, {})
                self.AddPage(h, row[0].data)
                self.children.append(h)


class GRID(grid.SchTableGrid, SchBaseCtrl):
    """GRID handle ctrlgrid tag

    Tag arguments:
        value
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
        if self.GetParent().IsShown():
            parm = createparm.create_parm(self.src, self.GetParent().get_parm_obj())
            if parm:
                if self.proxy.set_address_parm(parm[2]):
                    self.GetTable().refresh(False)

    def OnSize(self, event=None):
        """Handles The wx.EVT_SIZE Event For TabCtrl."""

        if event != None:
            size = event.GetSize()
            old = self.GetSize()
            if old[1] != size[1] - 8:
                self.SetSize((size[0], size[1] - 8))
                self.GetParent().RefrPage()
            event.Skip()


class UPDATEGRIDBUTTON(wx.Button, SchBaseCtrl):
    """UPDATEGRIDBUTTON handle ctrlupdategridbutton tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.Button.__init__(self, parent, **kwds)

        self.Bind(wx.EVT_BUTTON, self.OnClick, self)
        self.Enable()

    def OnClick(self, event):
        rec = dict()
        keys = list(self.GetParent().GetWidgets().keys())
        for k in keys:
            ctrl = self.GetParent().GetItem(k)
            if hasattr(ctrl, "GetValue"):
                rec[k] = self.GetParent().GetItem(k).GetValue()
        self.GetParent().GetPrevWin().ActiveCtrl.OnUpRecFromForm(rec)
        self.GetParent().any_parent_command("OnCancel", None)


class POPUPHTML(DataPopupControl, SchBaseCtrl):
    """POPUPHTML handle ctrlpopuphtml tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        """Constructor

        href - base address,
            href + "dialog" - address of dialog window
            href+ "test?value=" - address of records which starts with value parameter
        """

        SchBaseCtrl.__init__(self, parent, kwds)
        DataPopupControl.__init__(self, parent, **kwds)
        if self.param:
            if "IN_NEW_WIN" in self.param:
                self.simpleDialog = False

    def GetBestSize(self):
        dx, dy = DataPopupControl.GetBestSize(self)
        return (250, dy)


if platform.system() == "Linux":

    class DATEPICKER(POPUPHTML):
        """DATEPICKER handle ctrldatepicker tag

        Tag arguments:
            value
        """

        def __init__(self, parent, **kwds):
            kwds["href"] = wx.GetApp().make_href("/schsys/datedialog/")

            if "style" in kwds:
                kwds["style"] = kwds["style"] | wx.WANTS_CHARS
            else:
                kwds["style"] = wx.WANTS_CHARS

            if "size" in kwds:
                kwds["size"] = wx.Size(150, kwds["size"].height)
            else:
                kwds["size"] = wx.Size(150, -1)

            POPUPHTML.__init__(self, parent, **kwds)

            if self.value:
                self.set_rec(self.value, Td(self.value))
            else:
                self.set_rec(
                    wx.DateTime.Today().FormatISODate(),
                    Td(wx.DateTime.Today().FormatISODate()),
                    False,
                )

            wx.CallAfter(
                self.to_masked,
                mask="####-##-##",
                formatcodes="F",
                validRegex=r"\d{4}-\d{2}-\d{2}",
            )
            # wx.CallAfter(self.to_masked,autoformat="EUDATEYYYYMMDD.")

        def GetValue(self):
            value = self.get_rec()
            # if type(value) == tuple and len(value)>0:
            #    return value[1][0]
            if value.data:
                return value.data
            else:
                return value
            return None

        def GetBestSize(self):
            dx, dy = POPUPHTML.GetBestSize(self)
            return (130, dy)

else:

    class DATEPICKER(DatePickerCtrl, SchBaseCtrl):
        def __init__(self, parent, **kwds):
            SchBaseCtrl.__init__(self, parent, kwds)
            kwds["size"] = (120, -1)
            try:
                kwds["style"] = (
                    wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY | wx.adv.DP_ALLOWNONE
                )
            except:
                kwds["style"] = wx.DP_DROPDOWN | wx.DP_SHOWCENTURY | wx.DP_ALLOWNONE
            DatePickerCtrl.__init__(self, parent, **kwds)

        def SetValue(self, value):
            if value:
                date = wx.DateTime()
                date.ParseDate(value)
                DatePickerCtrl.SetValue(self, date)
            else:
                DatePickerCtrl.SetValue(self, None)

        def GetValue(self):
            value = DatePickerCtrl.GetValue(self)
            if value:
                return value.FormatISODate()
            else:
                return None


class DATETIMEPICKER(POPUPHTML):
    """DATETIMEPICKER handle ctrldatetimepicker tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        kwds["href"] = wx.GetApp().make_href("/schsys/datedialog/")

        if "style" in kwds:
            kwds["style"] = kwds["style"] | wx.WANTS_CHARS
        else:
            kwds["style"] = wx.WANTS_CHARS

        if "size" in kwds:
            kwds["size"] = wx.Size(200, kwds["size"].height)
        else:
            kwds["size"] = wx.Size(200, -1)

        POPUPHTML.__init__(self, parent, **kwds)

        # self.to_masked(autoformat="EUDATE24HRTIMEYYYYMMDD.HHMM")
        # self.to_masked(autoformat="EUDATE24HRTIMEYYYYMMDD.HHMM")
        self.to_masked(
            mask="####-##-## ##:##",
            formatcodes="F",
            validRegex=r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}",
        )
        # self.win.SetValidBackgroundColour("Red")
        # self.win.SetValidBackgroundColour(wx.Colour(1,0,0))
        # self.win.SetValidBackgroundColour(
        #    wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        # )

        if self.value:
            self.set_rec(self.value, Td(self.value))
        else:
            now = datetime.datetime.now().isoformat().replace("T", " ")[:16]
            self.set_rec(now, Td(now), False)

    def set_rec(self, value, value_rec, dismiss=False):
        if len(value) == 16:
            return super().set_rec(value, value_rec, dismiss)
        elif len(value) == 10:
            value_rec.data = value_rec.data + " 00:00"
            return super().set_rec(value + " 00:00", value_rec, dismiss)
        else:
            return super().set_rec("0000.00.00 00:00", value_rec, dismiss)

    def GetValue(self):
        value = self.get_rec()
        value2 = self.GetTextCtrl().GetValue()
        if value2 and value2[0] != " ":
            if value.data:
                return value.data
            else:
                return [
                    datetime.datetime.strptime(value2, "%Y-%m-%d %H:%M"),
                ]
        return None

    def GetBestSize(self):
        dx, dy = POPUPHTML.GetBestSize(self)
        return (180, dy)


class CHOICE(POPUPHTML):
    """CHOICE handle ctrlchoice tag

    Tag arguments:d
        value
    """

    def __init__(self, parent, **kwds):
        if not ("href" in kwds or "href" in kwds):
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

        self.init_choices(self.get_tdata())

        aTable = [
            (0, wx.WXK_F2, self.on_ext_button_click),
        ]
        self.set_acc_key_tab(aTable)

    def init_choices(self, data):
        self.choices = []
        if data:
            i = 0
            for row in data:
                self.choices.append(row[0])
                if "selected" in row[0].attrs:
                    value = row[0].data
                    ComboCtrl.SetValue(self, value)
                    if "value" in row[0].attrs:
                        self.set_rec(row[0].attrs["value"], row[0], dismiss=False)
                    else:
                        self.set_rec(value, row[0], dismiss=False)

    def on_ext_button_click(self, event):
        ret = self.alternate_button_click()
        if self.page:
            self.page.body.choices = self.choices
            wx.CallAfter(self.page.body.refr)
        else:
            self.popup.html.body.choices = self.choices
            wx.CallAfter(self.page.body.refr)
        return ret

    def OnButtonClick(self):
        if self.simpleDialog:
            ret = POPUPHTML.OnButtonClick(self)
            self.popup.html.body.choices = self.choices
            wx.CallAfter(self.popup.html.body.refr)
        else:
            ret = POPUPHTML.OnButtonClick(self)
            self.page.body.choices = self.choices
            wx.CallAfter(self.popup.html.body.refr)
        return ret

    def GetValue(self):
        if self.readonly:
            value = self.get_rec()
            return value[0]
        else:
            return POPUPHTML.GetValue(self)
        return None

    def GetBestSize(self):
        dx, dy = POPUPHTML.GetBestSize(self)
        return (dx, dy)

    def GetMinSize(self):
        return self.GetBestSize()

    def GetMaxSize(self):
        return self.GetBestSize()


class DBCHOICE(CHOICE):
    """DBCHOICE handle ctrldbchoice tag

    Tag arguments:
        value
    """

    def GetValue(self):
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
        return None


class DBCHOICE_EXT(POPUPHTML):
    """DBCHOICE_EXT handle ctrldbchoice_ext tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        if "style" in kwds:
            kwds["style"] = kwds["style"] | wx.CB_READONLY
        else:
            kwds["style"] = wx.CB_READONLY

        POPUPHTML.__init__(self, parent, **kwds)

    def SetValue(self, value):
        if type(value) == dict:
            val = value["value"]
            title = value["title"]
            sel = value["selected"]
            if sel:
                self.set_rec(val, Td(title, {"value": val}), dismiss=False)
        else:
            if "!!" in value:
                id = value.split(":")[0]
                name = value[len(id) + 1 :].replace("!!", "")
                self.set_rec(name, [id, name], dismiss=False)

        POPUPHTML.SetValue(self, value)

    def GetValue(self):
        if self.readonly:
            value = self.get_rec()
            if value.__class__ == tuple and len(value) > 0:
                return value[1][0]
            if len(value) > 0:
                return value[0]
            else:
                return None
        else:
            return POPUPHTML.GetValue(self)
        return None

    def get_parm(self, parm):
        if len(self.rec_value) > 0:
            id = self.rec_value[0]
            return b64encode(str(id).encode("utf-8")) if parm == "value" else None
        else:
            return None


class COLLAPSIBLE_PANEL(wx.CollapsiblePane, SchBaseCtrl):
    """COLLAPSIBLE_PANEL handle ctrlcollapsible_panel tag

    Tag arguments:
        value
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        kwds["label"] = self.label
        kwds["style"] = wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE
        if "size" in kwds:
            tmp = kwds["size"]
            self._size = [tmp[0], tmp[1]]
            del kwds["size"]
        else:
            self._size = [400, 300]

        self._height = 0

        if "collapse_height" in self.param:
            self._size[1] = int(self.param["collapse_height"])

        wx.CollapsiblePane.__init__(self, parent, **kwds)
        try:
            self.GetPane().SetBackgroundStyle(wx.BG_STYLE_ERASE)
        except:
            self.GetPane().SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        if "data" in self.param and self.param["data"].strip():
            self.set_html(self.param["data"])
        else:
            self.html = None
            self.SetSize((0, 0))
            self.Hide()
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

    def set_html(self, html_txt):
        mp = ShtmlParser()
        mp.process(
            "<html><body>" + self.param["data"].decode("utf-8") + "</body></html>"
        )
        mp.address = None
        if not self.html:
            self.html = page.SchPage(self.GetPane(), mp, {})
            self.html.init_frame()
            self.html.activate_page()
            width = self._size[0] if self._size[0] > 0 else 400
            self._height = self._size[1] if self._size[1] > 0 else 300
            self.html.SetSize((width, self._height))
            sizer = wx.BoxSizer()
            sizer.Add(self.html, 1, wx.EXPAND | wx.ALL, 5)
            self.GetPane().SetSizer(sizer)
            self.on_pane_changed(None)
        else:
            self.html.set_adr_and_param(mp, None)
            self.on_pane_changed(None)

    def on_pane_changed(self, event):
        if self.html:
            self.GetParent().GetParent().refresh_html()
            self.html.refresh_html()

    def GetBestSize(self):
        ret = wx.CollapsiblePane.GetBestSize(self)
        if self.IsExpanded():
            return (ret[0], ret[1] + self._height)
        elif not self.IsShown():
            return (0, 0)
        else:
            if ret[1] - self._height > 0:
                return (ret[0], ret[1] - self._height)
            else:
                return (ret[0], ret[1])

    def SetValue(self, value):
        if not self.html:
            pass

    def process_refr_data(self, **kwds):
        if "param" in kwds:
            self.param = kwds["param"]
            if "data" in self.param and self.param["data"].strip():
                self.Show(True)
                self.set_html(self.param["data"])


def button_from_parm(parent, param):
    if "children" in param and param["children"]:
        icon = param["children"][0]["attrs"]["class"]
        href = param["attrs"]["href"]
        button = BUTTON(parent, src="fa://" + icon + "?size=0", href=href)
        return button
    else:
        return None


class CompositePanel(wx.Panel, SchBaseCtrl):
    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.Panel.__init__(self, parent, **kwds)
        self.ctrl = None

    def set_main_ctrl(self, ctrl):
        self.ctrl = ctrl

    def GetValue(self):
        if self.ctrl:
            return str(self.ctrl.GetValue())
        else:
            return None


def SELECT2(parent, **kwds):
    data = kwds["param"]["data"]
    panel = CompositePanel(parent, size=(460, -1))
    ctrl = Select2Base(panel, **kwds)
    panel.set_main_ctrl(ctrl)
    if (
        len(data) > 1
        and "children" in data[1]
        and data[1]["children"]
        and len(data[1]["children"]) > 0
    ):
        button1 = button_from_parm(panel, param=data[1]["children"][0])
    else:
        button1 = None
    if (
        len(data) > 1
        and "children" in data[1]
        and data[1]["children"]
        and len(data[1]["children"]) > 1
    ):
        button2 = button_from_parm(panel, param=data[1]["children"][1])
    else:
        button2 = None

    ctrl.init(button1, button2)

    def ret_ok(id, title):
        ctrl.set_value(id, title)
        wx.CallAfter(ctrl.SetFocus)

    ctrl.ret_ok = ret_ok
    if button1:
        button1.ret_ok = ret_ok
    if button2:
        button2.ret_ok = ret_ok

    box = wx.BoxSizer(wx.HORIZONTAL)
    box.Add(ctrl, 0, wx.EXPAND)
    if button1:
        box.Add(button1)
    if button2:
        box.Add(button2)

    panel.SetSizer(box)
    panel.SetAutoLayout(True)
    panel.Fit()

    return panel


def COMPOSITE(parent, **kwds):
    cls = kwds["param"]["class"].upper()
    if cls in globals():
        return globals()[cls](parent, **kwds)


def COMPONENT(parent, **kwds):
    http = wx.GetApp().get_http(parent)
    response = http.get(
        parent, wx.GetApp().make_href("/schsys/widget_web?browser_type=1")
    )
    buf = response.str()

    colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE).GetAsString(
        flags=wx.C2S_HTML_SYNTAX
    )
    buf = buf.replace("<component>", kwds["param"]["data"]).replace("[[color]]", colour)

    if HTML2:
        kwds["component"] = True
        obj = HTML2(parent, **kwds)
        obj.load_str(buf, "http://127.0.0.2")
        return obj
    else:
        return None
