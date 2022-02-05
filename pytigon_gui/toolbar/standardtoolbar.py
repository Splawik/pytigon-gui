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

import wx

from pytigon_gui.guilib.events import *
from pytigon_gui.toolbar.basetoolbar import (
    ToolbarBar,
    ToolbarPage,
    ToolbarPanel,
    ToolbarButton,
)


_ = wx.GetTranslation


class StandardToolbarButton(ToolbarButton):
    def __init__(
        self,
        parent_panel,
        id,
        title,
        bitmap,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        ToolbarButton.__init__(
            self, parent_panel, id, title, bitmap, bitmap_disabled, kind
        )


class StandardToolbarPanel(ToolbarPanel):
    def __init__(self, parent_page, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        ToolbarPanel.__init__(self, parent_page, title, kind)
        if len(parent_page.panels) > 0:
            parent_page.parent_bar.standard_tool_bar.AddSeparator()

    def _append(self, b):
        item = None
        if self.kind in (
            ToolbarPanel.TYPE_PANEL_TOOLBAR,
            ToolbarPanel.TYPE_PANEL_BUTTONBAR,
        ):
            if b.kind == ToolbarButton.TYPE_SIMPLE:
                item = self.parent_page.parent_bar.standard_tool_bar.AddTool(
                    b.id, b.title, b.bitmap, b.title, kind=wx.ITEM_NORMAL
                )
            elif b.kind == ToolbarButton.TYPE_DROPDOWN:
                item = self.parent_page.parent_bar.standard_tool_bar.AddTool(
                    b.id, b.title, b.bitmap, b.title
                )
            elif b.kind == ToolbarButton.TYPE_HYBRID:
                item = self.parent_page.parent_bar.standard_tool_bar.AddTool(
                    b.id, b.title, b.bitmap, b.title
                )
            elif b.kind == ToolbarButton.TYPE_TOOGLE:
                item = self.parent_page.parent_bar.standard_tool_bar.AddToggleTool(
                    b.id, b.title, b.bitmap
                )
            elif b.kind == ToolbarButton.TYPE_PANEL:
                pass
            elif b.kind == ToolbarButton.TYPE_SEPARATOR:
                self.parent_page.parent_bar.standard_tool_bar.AddSeparator()
        else:
            pass

    def create_button(
        self,
        id,
        title,
        bitmap=None,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        b = StandardToolbarButton(self, id, title, bitmap, bitmap_disabled, kind)
        self._append(b)
        return b

    def add_separator(self):
        b = StandardToolbarButton(
            self, 0, "", None, None, kind=ToolbarButton.TYPE_SEPARATOR
        )
        self._append(b)
        return b


class StandardToolbarPage(ToolbarPage):
    def __init__(self, parent_bar, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        ToolbarPage.__init__(self, parent_bar, title, kind)
        if len(parent_bar.pages) > 0:
            parent_bar.standard_tool_bar.AddSeparator()

    def create_panel(self, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        return StandardToolbarPanel(self, title, kind)


class StandardToolbarBar(ToolbarBar):
    def __init__(self, parent, gui_style):
        self.standard_tool_bar = parent.CreateToolBar()
        ToolbarBar.__init__(self, parent, gui_style)

    def create_page(self, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        return StandardToolbarPage(self, title, kind)

    def bind_ui(self, fun, id=wx.ID_ANY):
        self.parent.Bind(wx.EVT_UPDATE_UI, fun, id=id)

    def bind(self, fun, id=wx.ID_ANY, e=None):
        if e:
            self.parent.Bind(e, fun, id=id)
        else:
            self.parent.Bind(wx.EVT_MENU, fun, id=id)

    def bind_dropdown(self, fun, id):
        self.parent.Bind(wx.EVT_MENU, fun, id=id)

    def un_bind(self, id, e=None):
        if e:
            self.Unbind(e, id=id)
        else:
            self.Unbind(wx.EVT_MENU, id=id)
