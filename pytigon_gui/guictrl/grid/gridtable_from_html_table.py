#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

# Pytigon - wxpython and django application framework

# author: "Slawomir Cholaj (slawomir.cholaj@gmail.com)"
# copyright: "Copyright (C) ????/2012 Slawomir Cholaj"
# license: "LGPL 3.0"
# version: "0.1a"

import urllib
import wx
import time

from .gridtable_base import SchGridTableBase
from pytigon_lib.schhtml.htmlviewer import tdata_from_html
from pytigon_gui.guilib.tools import colour_to_html


class KeyForRec:
    def __init__(self, rec, tabsort):
        self.rec = rec
        self.tabsort = tabsort

    def __lt__(self, other):
        if self.rec[0].data.strip() == "-":
            return 1
        if other.rec[0].data.strip() == "-":
            return -1

        for pos in self.tabsort:
            if pos > 0:
                x = self.rec[pos - 1].data.lower() < other.rec[pos - 1].data.lower()
            else:
                x = (
                    self.rec[-1 * pos - 1].data.lower()
                    > other.rec[-1 * pos - 1].data.lower()
                )
            if x:
                return x
        return False


def make_key(tabsort):
    return lambda rec: KeyForRec(rec, tabsort)


class PageData(object):
    def __init__(self, parent, page_len, count, titles, first_page):
        self.count = count
        self.page_len = page_len
        self.pages = {}
        self.pages[0] = first_page
        self.parent = parent
        self.titles = titles
        self.inserted = []
        self.sizes = []
        if first_page:
            self.calculate_sizes(titles, 0, first_page)

    def get_page(self, nr):
        href = self.parent.GetParent().get_parm_obj().address
        if "?" in href:
            addr = href + "&page=" + str(nr + 1)
        else:
            addr = href + "?page=" + str(nr + 1)
        html = self.parent.load_data_from_server(addr).decode("utf-8")
        tab = tdata_from_html(html, wx.GetApp().http)
        if tab:
            self.calculate_sizes(tab[0], nr, tab[1:], True)
            return tab[1:]
        else:
            return []

    def __getitem__(self, id):
        if (
            len(self.inserted) > 0
            and self.count > 0
            and id >= self.count - len(self.inserted)
        ):
            return self.inserted[id - (self.count - len(self.inserted))]

        page = id // self.page_len
        id2 = id % self.page_len
        if page in self.pages:
            try:
                ret = self.pages[page][id2]
            except:
                ret = None
            return ret
        else:
            wx.BeginBusyCursor()

            def y(self):
                time.sleep(0.1)

            old_y = wx.GetApp().Yield
            wx.GetApp().Yield = y
            data = self.get_page(page)
            self.pages[page] = data
            wx.GetApp().Yield = old_y
            wx.EndBusyCursor()
            return self.__getitem__(id)

    def sort(self, key):
        data = []
        for i in range(0, self.count):
            data.append(self.__getitem__(i))
        data.sort(key=key)
        self.pages = {}
        self.pages[0] = data
        self.page_len = self.count

    def __len__(self):
        return self.count

    def set_rec(self, id, row):
        if (
            len(self.inserted) > 0
            and self.count > 0
            and id >= self.count - len(self.inserted)
        ):
            self.inserted[id - (self.count - len(self.inserted))] = row
            return

        page = id // self.page_len
        id2 = id % self.page_len
        if page in self.pages:
            try:
                self.pages[page][id2] = row
            except:
                pass

    def append_row(self, row):
        self.inserted.append(row)
        self.count += 1

    def calculate_sizes(self, titles, start_id, page, refresh_if_changed=False):
        l = len(titles)
        row_h = {}
        changed = False
        if not self.sizes:
            self.sizes = [0] * l
        j = start_id - 1
        for row in [
            titles,
        ] + page:
            for i in range(0, l):
                s = len(row[i].data)
                if j == start_id - 1:
                    s *= 1.25
                if s > 64:
                    s = 64
                if s > self.sizes[i]:
                    self.sizes[i] = s
                    changed = True
                if j >= start_id:
                    h = 0
                    if "\n" in row[i].data:
                        h = row[i].data.count("\n")
                    elif len(row[i].data) > 64:
                        h += 1 + len(row[i].data) // 64
                    if h > 0:
                        if j not in row_h or row_h[j] < h:
                            row_h[j] = h
            j += 1
        if refresh_if_changed and changed:
            self.parent.grid.set_col_width(self.sizes)

        if row_h:

            def set_h():
                nonlocal row_h, self
                for key, value in row_h.items():
                    self.parent.grid.SetRowSize(
                        key, value * self.parent.grid.GetDefaultRowSize()
                    )

            wx.CallAfter(set_h)

    def get_sizes(self):
        return self.sizes


class SimpleDataTable(SchGridTableBase):
    def __init__(self, parent, tab):
        SchGridTableBase.__init__(self)
        self._parent = parent
        self.init_data(tab)
        # self.last_row_count = len(self.data)
        self.last_row_count = self.count

    def init_data(self, tab):
        self.colLabels = tab[0]
        self.dataTypes = []
        for col in self.colLabels:
            self.dataTypes.append("s")
        l = tab[0][0].data.split(":")
        self.count = len(tab) - 1
        self.per_page = 0
        if len(l) > 1:
            pages = l[1].split("/")
            if len(pages) > 1:
                self.per_page = int(pages[0])
                self.count = int(pages[1])
                self.colLabels[0].data = l[0]

        if self.per_page > 0:
            self.simple_data = False
            # if self.count > 128:
            #    self.auto_size = "short"
            #    self.data = PageData(
            #        self._parent,
            #        int(self.per_page),
            #        int(self.per_page),
            #        tab[0],
            #        tab[1 : self.per_page + 1],
            #    )
            # else:
            self.data = PageData(
                self._parent,
                int(self.per_page),
                self.count,
                tab[0],
                tab[1 : self.per_page + 1],
            )
        else:
            self.data = PageData(
                self._parent,
                len(tab) - 1,
                len(tab) - 1,
                tab[0],
                tab[1:],
            )
            # self.data = tab[1:]
            # self.per_page = len(self.data)
            self.simple_data = True
        self.attrs = {}
        self.enabled = False

    def replace_tab(self, new_tab):
        SchGridTableBase.replace_tab(self, new_tab)
        self.init_data(new_tab)
        self.refr_count(self.count)

    def refresh_page_data(self, tab):
        old_data = self.data
        self.data = PageData(
            old_data.parent,
            int(self.per_page),
            int(len(tab) - 1),
            tab[0],
            tab[1 : self.per_page + 1],
        )

    def enable(self, enabled):
        self.enabled = enabled
        if not self.simple_data:
            self.data.count = self.count

    def get_action_list(self, row, col=None):
        try:
            if col == None:
                col2 = self.GetNumberCols()
            else:
                col2 = col
            attrs = []
            td = self.data[row][col2]
            attrs.append(td.attrs)
            children = td.children
            if children:
                for sys_id in sorted(list(children)):
                    a = children[sys_id].attrs
                    txt = ""
                    for atom in children[sys_id].atom_list.atom_list:
                        txt += atom.data
                    a["data"] = txt
                    attrs.append(a)
            if col2 != 0:
                attrs2 = self.get_action_list(row, 0)
                for pos in attrs2:
                    attrs.append(pos)
            return attrs
        except:
            return []

    def sort(self, column, append):
        SchGridTableBase.sort(self, column, append)
        if self.count < 4096:
            key = make_key(self.tabsort)
            self.data.sort(key=key)
        else:
            pass
        self.GetView().ForceRefresh()

    def get_ext_attr(self, row, col):
        try:
            tdattr = {}
            td = self.data[row][col]
            tdattr.update(td.attrs)
            if td.children:
                for sys_id in td.children:
                    child = td.children[sys_id]
                    tag = child.tag
                    if tag in tdattr:
                        tdattr[tag] += (child.attrs,)
                    else:
                        tdattr[tag] = (child.attrs,)
        except:
            print("GetExtAttr:", row, col)
            tdattr = None
        return tdattr

    def get_children(self, row, col):
        try:
            td = self.data[row][col]
            return td.children
        except:
            return None

    def filter_cmp(self, pos, key):
        if self.filter_id >= 0:
            if str(pos[self.filter_id].data).upper().startswith(key.upper()):
                return True
            else:
                return False
        else:
            return False

    def GetAttr(self, row, col, kind):
        if row >= self.GetNumberRows():
            attr = self.attr_normal
            attr.IncRef()
            return attr
        try:
            tdattr = self.data[row][col].attrs
        except:
            tdattr = None
            # print("<<<")
            # print("rows:", self.GetNumberRows())
            # print("cols:", self.GetNumberCols())
            # attr = self.attr_normal
            # attr.IncRef()
            # return attr
            # print("len:", len(self.data[row]))
            # print(self.data[row][col])
            # print("Error", row, col)
            # print(">>>")
        if not tdattr:
            attr = self.attr_normal
            attr.IncRef()
            return attr
        bgcolor = None
        color = None
        strong = None
        if "bgcolor" in tdattr:
            bgcolor = tdattr["bgcolor"]
            if bgcolor[0] != "#":
                bgcolor = None
        if "color" in tdattr:
            color = tdattr["color"]
            if color[0] != "#":
                color = None
        if "strong" in tdattr:
            strong = "s"
        if self._is_sel(row):
            bgcolor = colour_to_html(self.sel_colour)
            strong = "s"

        key = ""
        key += bgcolor if bgcolor else "_"
        key += color if color else "_"
        key += strong if strong else "_"
        if "align" in tdattr:
            if tdattr["align"].lower() == "center":
                key += "c"
            elif tdattr["align"].lower() == "right":
                key += "r"
            else:
                key += "_"
        else:
            key += "_"

        if key:
            if key in self.attrs:
                attr = self.attrs[key]
            else:
                attr = wx.grid.GridCellAttr()
                if bgcolor:
                    attr.SetBackgroundColour(bgcolor)
                if color:
                    attr.SetTextColour(color)
                if strong:
                    font = self.GetView().GetDefaultCellFont()
                    font.SetWeight(wx.FONTWEIGHT_BOLD)
                    attr.SetFont(font)
                self.attrs[key] = attr
        else:
            attr = self.attr_normal

        if "align" in tdattr:
            if tdattr["align"].lower() == "center":
                attr.SetAlignment(wx.ALIGN_CENTER, -1)
            elif tdattr["align"].lower() == "right":
                attr.SetAlignment(wx.ALIGN_RIGHT, -1)

        attr.IncRef()
        return attr

    def _get_number_rows(self):
        return self.count

    def GetNumberCols(self):
        if len(self.colLabels) > 0:
            if self.no_actions:
                return len(self.colLabels)
            else:
                return len(self.colLabels) - 1
        else:
            return 0

    def GetValue(self, row, col):
        try:
            ret = self.data[row][col].data
            return ret
        except IndexError:
            return ""

    def SetValue(self, row, col, value):
        try:
            self.data[row][col] = value
        except IndexError:
            self.data.append([""] * self.GetNumberCols())
            self.SetValue(row, col, value)
            msg = wx.grid.GridTableMessage(
                self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1
            )
            self.GetView().ProcessTableMessage(msg)

    def GetColLabelValue(self, col):
        return self.colLabels[col].data

    def GetTypeName(self, row, col):
        return self.dataTypes[col]

    def CanGetValueAs(self, row, col, type_name):
        col_type = self.dataTypes[col].split(":")[0]
        if type_name == col_type:
            return True
        else:
            return False

    def GetColNames(self):
        return [item.data for item in self.colLabels]

    def CanSetValueAs(self, row, col, type_name):
        return self.CanGetValueAs(row, col, type_name)

    def refresh(self, storePos):
        self.GetView().GetParent().get_parent_form().any_parent_command("refresh_html")

    def set_rec(self, id, row):
        return self.data.set_rec(id, row)

    def append_row(self, row):
        ret = self.data.append_row(row)
        self.count += 1
        return ret

    def get_sizes(self):
        if self.data:
            return self.data.get_sizes()
        else:
            return None

    def copy(self):
        href_base = self._parent.GetParent().get_parm_obj().address
        href = urllib.parse.urljoin(href_base, "../table_action/")
        if self.rec_selected:
            href += "?pk=" + ",".join([str(pos.data) for pos in self.get_sel_rows()[0]])
        data = {
            "action": "copy",
        }
        http = wx.GetApp().get_http(self._parent)
        response = http.post(self._parent, href, parm=data, json_data=True)
        try:
            s = response.json()
        except:
            s = None
        return s

    def paste(self, data):
        href_base = self._parent.GetParent().get_parm_obj().address
        href = urllib.parse.urljoin(href_base, "../table_action/")

        data2 = {"action": "paste", "data": data}
        http = wx.GetApp().get_http(self._parent)
        response = http.post(self._parent, href, parm=data2, json_data=True)
        try:
            s = response.json()
        except:
            s = None
        return s
