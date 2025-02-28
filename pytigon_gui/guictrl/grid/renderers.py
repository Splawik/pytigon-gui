"""Module contains helper classes for grid renderers"""

import textwrap
import wx

from pytigon_gui.guilib.image import SchImage


class ExtStringRenderer(wx.grid.GridCellRenderer):
    def __init__(self):
        """Enhanced version of string renderer"""
        wx.grid.GridCellRenderer.__init__(self)

    def Draw(self, grid, attr, dc, rect, row, col, is_selected):
        rect2 = wx.Rect(rect.x + 1, rect.y + 1, rect.width - 2, rect.height - 2)
        dc.SetBackgroundMode(wx.SOLID)
        if grid.IsEnabled():
            if is_selected:
                dc.SetBrush(wx.Brush(grid.GetSelectionBackground(), wx.SOLID))
            else:
                dc.SetBrush(wx.Brush(attr.GetBackgroundColour(), wx.SOLID))
        else:
            dc.SetBrush(
                wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE), wx.SOLID)
            )
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
        (h_align, v_align) = attr.GetAlignment()
        dc.SetBackgroundMode(wx.TRANSPARENT)
        if grid.IsEnabled():
            if is_selected:
                dc.SetTextBackground(grid.GetSelectionBackground())
                dc.SetTextForeground(grid.GetSelectionForeground())
            else:
                dc.SetTextBackground(attr.GetBackgroundColour())
                dc.SetTextForeground(attr.GetTextColour())
        else:
            dc.SetTextBackground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
        dc.SetFont(attr.GetFont())

        text = self.get_text(grid, row, col)
        if text.find("#:#") >= 0:
            # dc.DrawLabel(text.split("#:#")[1], rect2, alignment=h_align | v_align)
            dc.DrawLabel(text.split("#:#")[1], rect2, alignment=h_align)
        else:
            # dc.DrawLabel(text, rect2, alignment=h_align | v_align)
            dc.DrawLabel(text, rect2, alignment=h_align)

    def get_text(self, grid, row, col):
        return grid.GetCellValue(row, col)

    def GetBestSize(self, grid, attr, dc, row, col):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        (w, h) = dc.GetTextExtent(text)
        return wx.Size(w, h)

    def Clone(self):
        return ExtStringRenderer()


class MultiLineStringRenderer(ExtStringRenderer):
    """Multiline string renderer"""

    def __init__(self, width):
        self.width = width
        ExtStringRenderer.__init__(self)

    def get_text(self, grid, row, col):
        text = grid.GetCellValue(row, col)
        if len(text) > self.width:
            text2 = textwrap.fill(text, self.width)
        else:
            text2 = text
        return text2

    def GetBestSize(
        self,
        grid,
        attr,
        dc,
        row,
        col,
    ):
        text = grid.GetCellValue(row, col)
        if len(text) > self.width:
            text2 = textwrap.wrap(text, self.width)
            dc.SetFont(attr.GetFont())
            (w, h) = dc.GetTextExtent("x" * self.width)
            return wx.Size(w, h * len(text2))
        else:
            return ExtStringRenderer.GetBestSize(self, grid, attr, dc, row, col)


class IconAndStringRenderer(MultiLineStringRenderer):
    """String renderer extended for rendering icons"""

    def __init__(self):
        MultiLineStringRenderer.__init__(self, 64)
        self.cache = {}

    def get_image_from_cache(self, image):
        if not image in self.cache:
            self.cache[image] = SchImage(image)
        return self.cache[image].bmp

    def get_image(self, grid, row, col):
        children = grid.GetTable().get_children(row, col)
        if children:
            for child_id in children:
                child = children[child_id]
                if child.tag in ("image", "img"):
                    if "src" in child.attrs:
                        return self.get_image_from_cache(child.attrs["src"])
        return None

    def Draw(self, grid, attr, dc, rect, row, col, is_selected):
        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
        image = self.get_image(grid, row, col)
        image2 = None
        if not image:
            text = grid.GetCellValue(row, col)
            if text == "+":
                image2 = wx.ArtProvider.GetBitmap(
                    wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR, (24, 24)
                )
                if image2:
                    image = image2
        if image:
            rect2 = wx.Rect(
                rect.x + image.GetWidth(),
                rect.y,
                rect.width - image.GetWidth(),
                rect.height,
            )
        else:
            rect2 = rect
        if not image2:
            ExtStringRenderer.Draw(self, grid, attr, dc, rect2, row, col, is_selected)
        if image:
            dc.DrawBitmap(image, rect.x, rect.y, True)

    def GetBestSize(self, grid, attr, dc, row, col):
        image = self.get_image(grid, row, col)
        if image:
            text = grid.GetCellValue(row, col)
            dc.SetFont(attr.GetFont())
            (w, h) = dc.GetTextExtent(text)
            if image.GetHeight() > h:
                h = image.GetHeight()
            w += image.GetWidth()
            return wx.Size(w, h)
        else:
            text = grid.GetCellValue(row, col)
            if text == "+":
                return wx.Size(24, 24)
            else:
                return MultiLineStringRenderer.GetBestSize(
                    self, grid, attr, dc, row, col
                )


class DateTimeRenderer(wx.grid.GridCellRenderer):
    """DateTime renderer"""

    def __init__(self):
        wx.grid.GridCellRenderer.__init__(self)
        self.best_size = None

    def Draw(self, grid, attr, dc, rect, row, col, is_selected):
        rect2 = wx.Rect(rect.x + 2, rect.y + 5, rect.width - 3, rect.height - 6)
        # rect2 = rect
        dc.SetBackgroundMode(wx.SOLID)
        if grid.IsEnabled():
            if is_selected:
                dc.SetBrush(wx.Brush(grid.GetSelectionBackground(), wx.SOLID))
            else:
                dc.SetBrush(wx.Brush(attr.GetBackgroundColour(), wx.SOLID))
        else:
            dc.SetBrush(
                wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE), wx.SOLID)
            )
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
        (h_align, v_align) = attr.GetAlignment()
        dc.SetBackgroundMode(wx.TRANSPARENT)
        if grid.IsEnabled():
            if is_selected:
                dc.SetTextBackground(grid.GetSelectionBackground())
                dc.SetTextForeground(grid.GetSelectionForeground())
            else:
                dc.SetTextBackground(attr.GetBackgroundColour())
                dc.SetTextForeground(attr.GetTextColour())
        else:
            dc.SetTextBackground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
        dc.SetFont(attr.GetFont())

        d = grid.GetCellValue(row, col)
        text = d[:16]
        dc.DrawLabel(text, rect2, alignment=h_align | v_align)

    def GetBestSize(self, grid, attr, dc, row, col):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        if not self.best_size:
            if text:
                self.best_size = dc.GetTextExtent(text[:16])
            else:
                return wx.Size(0, 0)
        return wx.Size(self.best_size[0], self.best_size[1])

    def Clone(self):
        return ExtStringRenderer()
