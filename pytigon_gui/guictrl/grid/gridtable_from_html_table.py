"""Grid table data source from server-rendered HTML tables.

Provides SimpleDataTable and PageData: a SchGridTableBase
implementation that loads paginated table data from the server
as HTML and parses it into grid rows. Supports sorting,
column sizing, cell-level attributes, and copy/paste.
"""

import logging
import os
import sys
import urllib
from collections import OrderedDict

import wx

from pytigon_gui.guilib.tools import colour_to_html
from pytigon_lib.schhtml.htmlviewer import tdata_from_html
from pytigon_lib.schhttptools import httpclient
from pytigon_lib.schhtml.htmltools import Td

from .gridtable_base import SchGridTableBase

logger = logging.getLogger(__name__)

# Upper bound on the memory held by one PageData's cached pages.
#
# self.count comes from the server, so scrolling a long table used to cache
# every page ever visited - permanently, since only sort() cleared it. A
# 300x15 page is ~1.9 MB, so scrolling a 60k-row grid accumulated ~374 MB that
# could never be reclaimed.
#
# The budget is deliberately generous so ordinary scrolling never re-fetches.
# At the 128 MB default a 300-row page is ~1.9 MB, so tables up to roughly
# 20,000 rows stay fully cached and a scroll-back costs no extra requests;
# beyond that the least-recently-used pages are dropped.
#
# Override with PYTIGON_GRID_PAGE_CACHE_MB, e.g. "512" for very large tables or
# "0" to disable eviction and keep the original unbounded behaviour.
_PAGE_CACHE_BYTES = int(os.environ.get("PYTIGON_GRID_PAGE_CACHE_MB", "128")) * 1024 * 1024

# Never evict below this many pages, whatever the budget, so that a short
# scroll-back can never turn into extra round-trips to the server.
_PAGE_CACHE_MIN_PAGES = 8


# Calibrated against tracemalloc: the walk below reports 1.32 MB for a page that
# actually occupies 1.87 MB, so scale up to keep the byte budget meaningful.
_PAGE_BYTES_CALIBRATION = 1.4


def _page_bytes(page):
    """Approximate the memory retained by one page of grid rows.

    Specialised for Td (which has __slots__): strings are charged by length
    rather than by object header, and the rare non-empty children list is
    approximated. Costs ~1.5 ms for a 300x15 page, i.e. negligible next to the
    HTTP round trip and HTML parse that produced it.
    """
    total = 56  # the page list itself
    for row in page:
        total += 56
        for td in row:
            if type(td) is not Td:
                total += sys.getsizeof(td)
                continue
            total += 56  # Td object with __slots__
            data = td.data
            if type(data) is str:
                total += 49 + len(data)
            elif data is not None:
                total += sys.getsizeof(data)
            if td.attrs:
                total += 64 + 100 * len(td.attrs)
            if td.children:
                total += 56 + 56 * len(td.children)
    return int(total * _PAGE_BYTES_CALIBRATION)


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


class PageData:
    def __init__(self, parent, page_len, count, titles, first_page):
        self.count = count
        self.page_len = page_len
        self.pages = OrderedDict()
        self.pages_bytes = 0
        self._page_sizes = {}
        self.pages[0] = first_page
        self._page_sizes[0] = _page_bytes(first_page) if first_page else 0
        self.pages_bytes = self._page_sizes[0]
        self.parent = parent
        self.titles = titles
        self.inserted = []
        self.sizes = []
        if first_page:
            self.calculate_sizes(titles, 0, first_page)

    def _cache_page(self, page, data):
        """Store a fetched page and evict old pages to stay inside the budget."""
        # A page may already be held (re-fetch after an eviction); don't
        # double-count it.
        if page in self.pages:
            self.pages_bytes -= self._page_sizes.pop(page)
            del self.pages[page]
        size = _page_bytes(data)
        self.pages[page] = data
        self.pages.move_to_end(page)
        self._page_sizes[page] = size
        self.pages_bytes += size
        self._evict_pages()

    def _evict_pages(self):
        """Drop least-recently-used pages until inside the byte budget.

        Stops at _PAGE_CACHE_MIN_PAGES so that a short scroll-back never
        costs an extra round-trip to the server.
        """
        if not _PAGE_CACHE_BYTES:
            return  # eviction disabled by configuration
        while (
            self.pages_bytes > _PAGE_CACHE_BYTES
            and len(self.pages) > _PAGE_CACHE_MIN_PAGES
        ):
            old_page, _ = self.pages.popitem(last=False)
            self.pages_bytes -= self._page_sizes.pop(old_page, 0)

    def get_page(self, nr):
        href = self.parent.GetParent().get_parm_obj().address
        if "?" in href:
            addr = href + "&page=" + str(nr + 1)
        else:
            addr = href + "?page=" + str(nr + 1)
        html = self.parent.load_data_from_server(addr).decode("utf-8")
        tab = tdata_from_html(html, wx.GetApp().http)
        if tab:
            # calculate_sizes() takes a GLOBAL row index (it seeds j =
            # start_id - 1, treats that row as the header and stores the rest
            # in row_h[j] before calling grid.SetRowSize(j, ...)). nr is the
            # 0-based page index, and __getitem__ maps a row to
            # "page = id // page_len", so page nr starts at nr * page_len.
            self.calculate_sizes(tab[0], nr * self.page_len, tab[1:], True)
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
            self.pages.move_to_end(page)  # mark recently used
            try:
                ret = self.pages[page][id2]
            except (KeyError, IndexError):
                ret = None
            return ret
        else:
            wx.BeginBusyCursor()
            # Loading a page triggers a synchronous HTTP request. Mark the
            # paint as in progress so the HTTP client blocks instead of
            # pumping the GTK event loop from inside cell rendering.
            httpclient.IN_PAINT += 1
            try:
                data = self.get_page(page)
                self._cache_page(page, data)
            finally:
                httpclient.IN_PAINT -= 1
                wx.EndBusyCursor()
            return self.__getitem__(id)

    def sort(self, key):
        data = []
        for i in range(0, self.count):
            data.append(self.__getitem__(i))
        data.sort(key=key)
        self.pages = OrderedDict()
        self._page_sizes = {0: _page_bytes(data)}
        self.pages[0] = data
        self.pages_bytes = self._page_sizes[0]
        self.page_len = self.count

    def __len__(self):
        return self.count

    def append(self, row):
        """Append a locally inserted row (not yet persisted)."""
        self.inserted.append(row)
        self.count += 1

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
            except (KeyError, IndexError):
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
            grid = self.parent.grid
            default_h = grid.GetDefaultRowSize()
            heights = list(row_h.items())

            def set_h():
                for key, value in heights:
                    grid.SetRowSize(key, value * default_h)

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
            data_len = len(tab) - 1
            if data_len < 1:
                data_len = 1
            self.data = PageData(
                self._parent,
                data_len,
                data_len,
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
            if col is None:
                col2 = self.GetNumberCols()
            else:
                col2 = col
            attrs = []
            td = self.data[row][col2]
            attrs.append(td.attrs)
            children = td.children
            if children:
                for sys_id in sorted(children):
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
        except (IndexError, AttributeError, TypeError):
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
        except (IndexError, AttributeError):
            logger.debug("GetExtAttr: row=%s col=%s", row, col)
            tdattr = None
        return tdattr

    def get_children(self, row, col):
        try:
            td = self.data[row][col]
            return td.children
        except (IndexError, AttributeError):
            return None

    def filter_cmp(self, pos, key):
        if self.filter_id is not None and self.filter_id >= 0:
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
        except (IndexError, KeyError, AttributeError):
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
                    # Copy: GetDefaultCellFont() is shared by every cell of
                    # the grid, so mutating it would bold them all.
                    font = wx.Font(self.GetView().GetDefaultCellFont())
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
            href += "?pk=" + ",".join(
                [str(pos.data).strip() for pos in self.get_sel_rows()[0]]
            )
        data = {
            "action": "copy",
        }
        http = wx.GetApp().get_http(self._parent)
        response = http.post(self._parent, href, parm=data, json_data=True)
        try:
            s = response.json()
        except (ValueError, AttributeError):
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
        except (ValueError, AttributeError):
            s = None
        return s
