import collections
import wx

from pytigon_gui.guilib.image import bitmap_from_href

_ = wx.GetTranslation


class SchGridPanel(wx.Panel):
    """Panel for grid widget with toolbar"""

    def __init__(self, *args, **argv):
        self.grid = None
        self.icon_size = 2
        wx.Panel.__init__(self, *args, **argv)
        self.vertical = False
        self._bitmaps = {
            "edit": "wx.ART_FILE_OPEN",
            "edit_inline": "wx.ART_FILE_OPEN",
            "delete": "wx.ART_DELETE",
            "view_row": "wx.ART_INFORMATION",
        }
        self._menu_buttons = collections.OrderedDict()

    def set_bitmap(self, action, path):
        self._bitmaps[action] = path

    def set_bitmaps(self, action_dict):
        for key in action_dict:
            self.set_bitmap(key, action_dict[key])

    def set_vertical(self, enable=True):
        self.vertical = enable

    def _get_bmp(self, id_str):
        if id_str in self._bitmaps:
            value = self._bitmaps[id_str]
            return bitmap_from_href(value, self.icon_size)
        return wx.ArtProvider.GetBitmap(wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (32, 32))

    def _add_action(self, action):
        test = False
        if "name" in action:
            name = action["name"]
            label = action["data"]
            if "title" in action:
                title = action["title"]
                if not label:
                    label = title
            else:
                title = ""
            if (
                not name in ("insert", "edit", "delete", "new", "get_row", "view_row")
                and not name in self.commands
            ):
                if name in self._bitmaps:
                    b = self._get_bmp(name)
                else:
                    if "src" in action:
                        b = bitmap_from_href(action["src"])
                    else:
                        b = bitmap_from_href("fa://fa-chevron-right?size=1")
                if "(" in label and ")" in label:
                    x = label.split("(")
                    label1 = x[0]
                    label2 = x[1].split(")")[0]
                    if not label2 in self._menu_buttons:
                        self.toolbar.AddTool(
                            self.lp2,
                            label2,
                            b,
                            wx.NullBitmap,
                            wx.ITEM_NORMAL,
                            label2,
                            title,
                        )
                        self._menu_buttons[label2] = []
                        self.lp2 += 1
                    tab_menu = self._menu_buttons[label2]
                    tab_menu.append((self.lp, label1))
                else:
                    self.toolbar.AddTool(
                        self.lp, label, b, wx.NullBitmap, wx.ITEM_NORMAL, label, title
                    )
                self.commands.append(name)
                test = True
                self.lp += 1
        return test

    def create_toolbar(self, grid):
        self.GetParent().signal_from_child(self, "set_bitmap_list")
        self.grid = grid
        self.spanel = wx.ScrolledWindow(
            self, style=wx.VSCROLL if self.vertical else wx.HSCROLL
        )
        self.commands = []
        self.lp = 101
        self.lp2 = 201
        (standard, akcje) = grid.get_action_list()
        if standard or akcje and len(akcje) > 0:
            if self.vertical:
                self.toolbar = wx.ToolBar(
                    self.spanel, -1, wx.DefaultPosition, wx.DefaultSize, wx.TB_VERTICAL
                )
            else:
                self.toolbar = wx.ToolBar(
                    self.spanel, -1, wx.DefaultPosition, wx.DefaultSize, 0
                )
            tsize = (32, 32)
            self.toolbar.SetToolBitmapSize(tsize)
            if standard:
                self.toolbar.AddTool(
                    self.lp,
                    _("Edit"),
                    self._get_bmp("edit"),
                    wx.NullBitmap,
                    wx.ITEM_NORMAL,
                    _("Edit"),
                    _("Edit"),
                )
                self.toolbar.AddTool(
                    self.lp + 1,
                    _("Delete"),
                    self._get_bmp("delete"),
                    wx.NullBitmap,
                    wx.ITEM_NORMAL,
                    _("Delete"),
                    _("Delete"),
                )
                self.toolbar.AddTool(
                    self.lp + 2,
                    _("view_row"),
                    self._get_bmp("view_row"),
                    wx.NullBitmap,
                    wx.ITEM_NORMAL,
                    _("View row"),
                    _("View row"),
                )
                self.toolbar.AddSeparator()
                self.commands.append("edit")
                self.commands.append("delete")
                self.commands.append("view_row")
                self.lp += 3
            if akcje:
                for action in akcje:
                    self._add_action(action)
            self.toolbar.Realize()
            self.toolbar.Bind(wx.EVT_TOOL, self.on_tool_click)
            self.Bind(wx.EVT_MENU, self.on_tool_click)

            self.toolbar.SetSize(self.toolbar.GetBestSize())
            if self.vertical:
                self.spanel.SetScrollRate(0, 20)
            else:
                self.spanel.SetScrollRate(20, 0)
            self.spanel.SetVirtualSize(self.toolbar.GetSize())
        grid.set_panel(self)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.on_size()

    def on_size(self, event=None):
        if event:
            panel_size = event.GetSize()
        else:
            panel_size = self.GetSize()
        toolbar_size = self.toolbar.GetSize()
        if self.vertical:
            if toolbar_size[1] >= panel_size[1]:
                dx = toolbar_size[0] + wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
            else:
                dx = toolbar_size[0]
            self.spanel.SetRect(wx.Rect(0, 0, dx, panel_size[1]))
            self.grid.SetRect(
                wx.Rect(dx + 2, 0, (panel_size[1] - dx) - 2, panel_size[1])
            )
        else:
            if toolbar_size[0] >= panel_size[0]:
                dy = toolbar_size[1] + wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y)
            else:
                dy = toolbar_size[1]
            self.spanel.SetRect(wx.Rect(0, 0, panel_size[0], dy))
            self.grid.SetRect(
                wx.Rect(0, dy + 2, panel_size[0], (panel_size[1] - dy) - 2)
            )
        if event:
            event.Skip()

    def on_tool_click(self, event):
        id = event.GetId()
        if id > 200:
            id2 = id - 201
            tab_menu = list(self._menu_buttons.values())[id2]
            menu = wx.Menu()
            for pos in tab_menu:
                menu.Append(pos[0], pos[1])
            self.PopupMenu(menu)
            menu.Destroy()
        else:
            self.grid.action(self.commands[id - 101])

    def refresh(self, row):
        if self.grid.GetTable().GetNumberRows() > 0:
            akcje = self.grid.get_action_list(row)[1]
            akcje_dict = {}
            test = False
            if akcje:
                for action in akcje:
                    if not "name" in action:
                        continue
                    akcje_dict[action["name"]] = akcje
                    if self._add_action(action):
                        test = True
            if test:
                self.toolbar.Realize()
                self.toolbar.SetSize(self.toolbar.GetBestSize())
            i = 101
            for command in self.commands:
                if command in akcje_dict:
                    self.toolbar.EnableTool(i, True)
                else:
                    self.toolbar.EnableTool(i, False)
                i = i + 1
