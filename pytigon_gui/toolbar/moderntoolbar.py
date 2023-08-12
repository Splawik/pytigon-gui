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
from functools import cmp_to_key

# import wx.lib.agw.ribbon as RB
import wx.lib.agw.ribbon as RB
from wx.lib.agw.ribbon import art
from wx.lib.agw.ribbon.art import *

from pytigon_gui.guilib.events import *
from pytigon_gui.toolbar.basetoolbar import (
    BaseHtmlPanel,
    ToolbarBar,
    ToolbarPage,
    ToolbarPanel,
    ToolbarButton,
)

_ = wx.GetTranslation


MSW_STYLE = True
ORG_LIKE_PRIMARY = None


def like_primary(primary_hsl, h, s, l, x=None):
    if x != None:
        c1 = ORG_LIKE_PRIMARY(primary_hsl, h, 0, l * 1.5, x)
    else:
        c1 = ORG_LIKE_PRIMARY(primary_hsl, h, 0, l * 1.5)
    c2 = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)
    r2 = c2.Red()
    g2 = c2.Green()
    b2 = c2.Blue()
    if r2 == 0:
        r2 = 1
    if g2 == 0:
        g2 = 1
    if b2 == 0:
        b2 = 1
    m = ((1.0 * c1.Red()) / r2 + (1.0 * c1.Green()) / g2 + (1.0 * c1.Blue()) / b2) / 3
    x1 = int(c2.Red() * m)
    x2 = int(c2.Green() * m)
    x3 = int(c2.Blue() * m)
    if x1 > 255:
        x1 = 255
    if x2 > 255:
        x2 = 255
    if x3 > 255:
        x3 = 255
    c3 = wx.Colour(x1, x2, x3)
    return c3


class ModernHtmlPanel(BaseHtmlPanel):
    def get_width(self):
        return self.page.parent_bar.get_bar_width()

    def get_height(self):
        return self.page.parent_bar.get_bar_height()

    def set_page(self, html_page):
        super().set_page(html_page)
        self.page.parent_bar.update()
        self.page.parent_bar.SetActivePage(self.page)


class ModernToolbarButton(ToolbarButton):
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


class ModernToolbarPanel(ToolbarPanel, RB.RibbonPanel):
    def __init__(self, parent_page, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        RB.RibbonPanel.__init__(
            self,
            parent_page,
            wx.ID_ANY,
            title,
            wx.NullBitmap,
            wx.DefaultPosition,
            wx.DefaultSize,
            RB.RIBBON_PANEL_NO_AUTO_MINIMISE,
        )
        ToolbarPanel.__init__(self, parent_page, title, kind)

        if self.kind == ToolbarPanel.TYPE_PANEL_TOOLBAR:
            self.toolbar = RB.RibbonToolBar(self)
            # self.toolbar = SchRibbonToolBar(self)
        elif self.kind == ToolbarPanel.TYPE_PANEL_BUTTONBAR:
            self.toolbar = RB.RibbonButtonBar(self)

        self.lock = False

    def OnInternalIdle(self):
        if not self.lock:
            self.lock = True
            if self.toolbar:
                self.toolbar.UpdateWindowUI(wx.UPDATE_UI_FROMIDLE)
            self.lock = False

    def Append(self, b):
        if self.kind == ToolbarPanel.TYPE_PANEL_TOOLBAR:
            if b.kind == ToolbarButton.TYPE_SIMPLE:
                self.toolbar.AddSimpleTool(b.id, b.bitmap, b.title)
            elif b.kind == ToolbarButton.TYPE_DROPDOWN:
                self.toolbar.AddDropdownTool(b.id, b.bitmap, b.title)
            elif b.kind == ToolbarButton.TYPE_HYBRID:
                self.toolbar.AddHybridTool(b.id, b.bitmap, b.title)
            elif b.kind == ToolbarButton.TYPE_TOOGLE:
                self.toolbar.AddToggleTool(b.id, b.bitmap, b.title)
            elif b.kind == ToolbarButton.TYPE_PANEL:
                pass
            elif b.kind == ToolbarButton.TYPE_SEPARATOR:
                self.toolbar.AddSeparator()
        elif self.kind == ToolbarPanel.TYPE_PANEL_BUTTONBAR:
            if b.kind == ToolbarButton.TYPE_SIMPLE:
                self.toolbar.AddSimpleButton(b.id, b.title, b.bitmap, "")
            elif b.kind == ToolbarButton.TYPE_DROPDOWN:
                self.toolbar.AddDropdownButton(b.id, b.title, b.bitmap, "")
            elif b.kind == ToolbarButton.TYPE_HYBRID:
                self.toolbar.AddHybridButton(b.id, b.title, b.bitmap, "")
            elif b.kind == ToolbarButton.TYPE_TOOGLE:
                self.toolbar.AddToggleButton(b.id, b.title, b.bitmap, "")
            elif b.kind == ToolbarButton.TYPE_PANEL:
                pass
            # elif b.kind == ToolbarButton.TYPE_SEPARATOR:
            #    self.toolbar.AddSeparator()
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
        b = ModernToolbarButton(self, id, title, bitmap, bitmap_disabled, kind)
        self.Append(b)
        return b

    def add_separator(self):
        b = ModernToolbarButton(
            self, 0, "", None, None, kind=ToolbarButton.TYPE_SEPARATOR
        )
        self.Append(b)
        return b


class ModernToolbarPage(ToolbarPage, RB.RibbonPage):
    def __init__(self, parent_bar, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        ToolbarPage.__init__(self, parent_bar, title, kind)
        RB.RibbonPage.__init__(self, parent_bar, wx.ID_ANY, self.title)

    def create_panel(self, title, kind=ToolbarPanel.TYPE_PANEL_TOOLBAR):
        return ModernToolbarPanel(self, title, kind)

    def create_html_panel(self, title):
        p = self.create_panel(title)
        return ModernHtmlPanel(self, p)


class ModernToolbarBar(ToolbarBar, RB.RibbonBar):
    def __init__(self, parent, gui_style):
        RB.RibbonBar.__init__(self, parent, wx.ID_ANY)
        ToolbarBar.__init__(self, parent, gui_style)

    def create_page(self, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        return ModernToolbarPage(self, title, kind)

    def create(self):
        self.Realize()

        def _realize():
            for child in self.Children:
                child.Realize()

        wx.CallAfter(_realize)

    def close(self):
        self.Close()

    def update(self):
        size = self.GetSize()
        self.SetSize(wx.Size(size.GetWidth() - 1, size.GetHeight()))
        self.SetSize(wx.Size(size.GetWidth(), size.GetHeight()))

    def bind_ui(self, fun, id=wx.ID_ANY):
        self.Bind(wx.EVT_UPDATE_UI, fun, id=id)

    def bind(self, fun, id=wx.ID_ANY, e=None):
        if e:
            self.Bind(e, fun, id=id)
        else:
            self.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, fun, id=id)
            self.Bind(RB.EVT_RIBBONTOOLBAR_CLICKED, fun, id=id)

    def bind_dropdown(self, fun, id):
        self.bar.Bind(RB.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED, fun, id=id)

    def un_bind(self, id, e=None):
        if e:
            self.Unbind(e, id=id)
        else:
            self.Unbind(RB.EVT_RIBBONBUTTONBAR_CLICKED, id=id)

    def get_bar_height(self):
        s = (48, 48)
        ret = self.GetArtProvider().GetButtonBarButtonSize(
            self,
            self,
            art.RIBBON_BUTTON_NORMAL,
            art.RIBBON_BUTTONBAR_BUTTON_LARGE,
            "TXT",
            s,
            s,
        )
        size_ret = ret[1]
        return size_ret.GetHeight()

    def get_bar_width(self):
        return 2000

    def remove_page(self, title):
        self.SetActivePage(0)
        for page_info in self._pages:
            if page_info.page.title == title:
                self._pages.remove(page_info)
        self.Update()
        super().remove_page(title)

    def Realize(self):
        if MSW_STYLE:
            global ORG_LIKE_PRIMARY
            if not ORG_LIKE_PRIMARY:
                ORG_LIKE_PRIMARY = RB.art_msw.LikePrimary
                RB.art_msw.LikePrimary = like_primary
            provider = RB.RibbonMSWArtProvider()
            (dummy, secondary, tertiary) = provider.GetColourScheme(None, 1, 1)
            colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)
            colour2 = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT)
            provider.SetColourScheme(colour, secondary, colour2)
            provider._tab_label_colour = colour2
            provider._button_bar_label_colour = colour2
        else:
            provider = RB.RibbonAUIArtProvider()
        self.SetArtProvider(provider)
        RB.RibbonBar.Realize(self)

    def RecalculateTabSizes(self):
        """Recalculates the :class:`RibbonBar` tab sizes."""

        numtabs = len(self._pages)

        if numtabs == 0:
            return

        width = (
            self.GetSize().GetWidth() - self._tab_margin_left - self._tab_margin_right
        )
        tabsep = self._art.GetMetric(RIBBON_ART_TAB_SEPARATION_SIZE)
        x = self._tab_margin_left
        y = 0

        if width >= self._tabs_total_width_ideal:
            # Simple case: everything at ideal width
            for info in self._pages:
                info.rect.x = x
                info.rect.y = y
                info.rect.width = info.ideal_width
                info.rect.height = self._tab_height
                x += info.rect.width + tabsep

            self._tab_scroll_buttons_shown = False
            self._tab_scroll_left_button_rect.SetWidth(0)
            self._tab_scroll_right_button_rect.SetWidth(0)

        elif width < self._tabs_total_width_minimum:
            # Simple case: everything minimum with scrollbar
            for info in self._pages:
                info.rect.x = x
                info.rect.y = y
                info.rect.width = info.minimum_width
                info.rect.height = self._tab_height
                x += info.rect.width + tabsep

            if not self._tab_scroll_buttons_shown:
                self._tab_scroll_left_button_state = RIBBON_SCROLL_BTN_NORMAL
                self._tab_scroll_right_button_state = RIBBON_SCROLL_BTN_NORMAL
                self._tab_scroll_buttons_shown = True

            temp_dc = wx.ClientDC(self)
            self._tab_scroll_left_button_rect.SetWidth(
                self._art.GetScrollButtonMinimumSize(
                    temp_dc,
                    self,
                    RIBBON_SCROLL_BTN_LEFT
                    | RIBBON_SCROLL_BTN_NORMAL
                    | RIBBON_SCROLL_BTN_FOR_TABS,
                ).GetWidth()
            )
            self._tab_scroll_left_button_rect.SetHeight(self._tab_height)
            self._tab_scroll_left_button_rect.SetX(self._tab_margin_left)
            self._tab_scroll_left_button_rect.SetY(0)
            self._tab_scroll_right_button_rect.SetWidth(
                self._art.GetScrollButtonMinimumSize(
                    temp_dc,
                    self,
                    RIBBON_SCROLL_BTN_RIGHT
                    | RIBBON_SCROLL_BTN_NORMAL
                    | RIBBON_SCROLL_BTN_FOR_TABS,
                ).GetWidth()
            )
            self._tab_scroll_right_button_rect.SetHeight(self._tab_height)
            self._tab_scroll_right_button_rect.SetX(
                self.GetClientSize().GetWidth()
                - self._tab_margin_right
                - self._tab_scroll_right_button_rect.GetWidth()
            )
            self._tab_scroll_right_button_rect.SetY(0)

            if self._tab_scroll_amount == 0:
                self._tab_scroll_left_button_rect.SetWidth(0)

            elif self._tab_scroll_amount + width >= self._tabs_total_width_minimum:
                self._tab_scroll_amount = self._tabs_total_width_minimum - width
                self._tab_scroll_right_button_rect.SetX(
                    self._tab_scroll_right_button_rect.GetX()
                    + self._tab_scroll_right_button_rect.GetWidth()
                )
                self._tab_scroll_right_button_rect.SetWidth(0)

            for info in self._pages:
                info.rect.x -= self._tab_scroll_amount

        else:
            self._tab_scroll_buttons_shown = False
            self._tab_scroll_left_button_rect.SetWidth(0)
            self._tab_scroll_right_button_rect.SetWidth(0)
            # Complex case: everything sized such that: minimum <= width < ideal
            #
            #   Strategy:
            #     1) Uniformly reduce all tab widths from ideal to small_must_have_separator_width
            #     2) Reduce the largest tab by 1 pixel, repeating until all tabs are same width (or at minimum)
            #     3) Uniformly reduce all tabs down to their minimum width
            #
            smallest_tab_width = 10000
            total_small_width = tabsep * (numtabs - 1)

            for info in self._pages:
                if info.small_must_have_separator_width < smallest_tab_width:
                    smallest_tab_width = info.small_must_have_separator_width

                total_small_width += info.small_must_have_separator_width

            if width >= total_small_width:
                # Do (1)
                total_delta = self._tabs_total_width_ideal - total_small_width
                total_small_width -= tabsep * (numtabs - 1)
                width -= tabsep * (numtabs - 1)
                for info in self._pages:
                    delta = info.ideal_width - info.small_must_have_separator_width
                    info.rect.x = x
                    info.rect.y = y
                    info.rect.width = (
                        info.small_must_have_separator_width
                        + delta * (width - total_small_width) // total_delta
                    )
                    info.rect.height = self._tab_height

                    x += info.rect.width + tabsep
                    total_delta -= delta
                    total_small_width -= info.small_must_have_separator_width
                    width -= info.rect.width

            else:
                total_small_width = tabsep * (numtabs - 1)
                for info in self._pages:
                    if info.minimum_width < smallest_tab_width:
                        total_small_width += smallest_tab_width
                    else:
                        total_small_width += info.minimum_width

                if width >= total_small_width:
                    # Do (2)
                    sorted_pages = []
                    for info in self._pages:
                        # Sneaky obj array trickery to not copy the tab descriptors
                        sorted_pages.append(info)

                    sorted_pages.sort(
                        key=cmp_to_key(self.OrderPageTabInfoBySmallWidthAsc)
                    )
                    width -= tabsep * (numtabs - 1)

                    for i, info in enumerate(self._pages):
                        if (
                            info.small_must_have_separator_width * (numtabs - i)
                            <= width
                        ):
                            info.rect.width = info.small_must_have_separator_width
                        else:
                            info.rect.width = width // (numtabs - i)

                        width -= info.rect.width

                    for i, info in enumerate(self._pages):
                        info.rect.x = x
                        info.rect.y = y
                        info.rect.height = self._tab_height
                        x += info.rect.width + tabsep
                        sorted_pages.pop(numtabs - (i + 1))

                else:
                    # Do (3)
                    total_small_width = (smallest_tab_width + tabsep) * numtabs - tabsep
                    total_delta = total_small_width - self._tabs_total_width_minimum
                    total_small_width = self._tabs_total_width_minimum - tabsep * (
                        numtabs - 1
                    )
                    width -= tabsep * (numtabs - 1)

                    for info in self._pages:
                        delta = smallest_tab_width - info.minimum_width
                        info.rect.x = x
                        info.rect.y = y
                        info.rect.width = (
                            info.minimum_width
                            + delta * (width - total_small_width) // total_delta
                        )
                        info.rect.height = self._tab_height

                        x += info.rect.width + tabsep
                        total_delta -= delta
                        total_small_width -= info.minimum_width
                        width -= info.rect.width
