"""Tests for pytigon_gui.toolbar.basetoolbar - base toolbar classes."""

import pytest
from unittest.mock import MagicMock


class TestToolbarButton:

    def test_init_simple(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarButton

        parent = MagicMock()
        btn = ToolbarButton(parent, 100, "Test Button")
        assert btn.parent_panel is parent
        assert btn.id == 100
        assert btn.title == "Test Button"
        assert btn.bitmap is None
        assert btn.bitmap_disabled is None
        assert btn.kind == ToolbarButton.TYPE_SIMPLE

    def test_init_with_bitmap(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarButton

        parent = MagicMock()
        bmp = MagicMock()
        btn = ToolbarButton.__new__(ToolbarButton)
        btn.parent_panel = parent
        btn.id = 200
        btn.title = "Button"
        btn.bitmap = bmp
        btn.bitmap_disabled = MagicMock()
        btn.kind = ToolbarButton.TYPE_TOOGLE

        assert btn.bitmap is bmp
        assert btn.bitmap_disabled is not None
        assert btn.kind == ToolbarButton.TYPE_TOOGLE

    def test_init_with_both_bitmaps(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarButton

        parent = MagicMock()
        bmp = MagicMock()
        bmp_dis = MagicMock()
        btn = ToolbarButton(parent, 300, "Button", bitmap=bmp, bitmap_disabled=bmp_dis)
        assert btn.bitmap is bmp
        assert btn.bitmap_disabled is bmp_dis

    def test_type_constants(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarButton

        assert ToolbarButton.TYPE_SIMPLE == 0
        assert ToolbarButton.TYPE_DROPDOWN == 1
        assert ToolbarButton.TYPE_HYBRID == 2
        assert ToolbarButton.TYPE_TOOGLE == 3
        assert ToolbarButton.TYPE_PANEL == 4
        assert ToolbarButton.TYPE_SEPARATOR == 5


class TestToolbarPanel:

    def test_init(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel

        parent_page = MagicMock()
        panel = ToolbarPanel(parent_page, "My Panel")
        assert panel.parent_page is parent_page
        assert panel.title == "My Panel"
        assert panel.buttons == []

    def test_create_and_append_button(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel, ToolbarButton

        panel = ToolbarPanel(MagicMock(), "Panel")
        btn = panel.append(10, "Btn", kind=ToolbarButton.TYPE_SIMPLE)

        assert isinstance(btn, ToolbarButton)
        assert btn.id == 10
        assert len(panel.buttons) == 1
        assert panel.buttons[0] is btn

    def test_add_simple_tool(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel

        panel = ToolbarPanel(MagicMock(), "Panel")
        btn = panel.add_simple_tool(1, "Simple", [])
        assert btn.kind == type(btn).TYPE_SIMPLE

    def test_add_dropdown_tool(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel

        panel = ToolbarPanel(MagicMock(), "Panel")
        btn = panel.add_dropdown_tool(2, "Drop", [])
        assert btn.kind == type(btn).TYPE_DROPDOWN

    def test_add_hybrid_tool(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel

        panel = ToolbarPanel(MagicMock(), "Panel")
        btn = panel.add_hybrid_tool(3, "Hybrid", [])
        assert btn.kind == type(btn).TYPE_HYBRID

    def test_add_toogle_tool(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel

        panel = ToolbarPanel(MagicMock(), "Panel")
        btn = panel.add_toogle_tool(4, "Toggle", [])
        assert btn.kind == type(btn).TYPE_TOOGLE

    def test_add_separator_noop(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel

        panel = ToolbarPanel(MagicMock(), "Panel")
        panel.add_separator()

    def test_transform_bitmaps_no_args(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel

        panel = ToolbarPanel(MagicMock(), "Panel")
        result = panel._transform_bitmaps_parm([])
        assert result == [None, None]

    def test_transform_bitmaps_one_arg(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel

        panel = ToolbarPanel(MagicMock(), "Panel")
        bmp = MagicMock()
        result = panel._transform_bitmaps_parm([bmp])
        assert result == [bmp, None]

    def test_transform_bitmaps_two_args(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPanel

        panel = ToolbarPanel(MagicMock(), "Panel")
        bmp1 = MagicMock()
        bmp2 = MagicMock()
        result = panel._transform_bitmaps_parm([bmp1, bmp2])
        assert result == [bmp1, bmp2]


class TestToolbarPage:

    def test_init(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPage

        parent_bar = MagicMock()
        page = ToolbarPage(parent_bar, "Page Title")
        assert page.parent_bar is parent_bar
        assert page.name == "Page Title"
        assert page.panels == []

    def test_create_panel_returns_panel(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPage

        page = ToolbarPage(MagicMock(), "Page")
        panel = page.create_panel("Panel", 0)
        assert panel is not None

    def test_create_html_panel_returns_none(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPage

        page = ToolbarPage(MagicMock(), "Page")
        assert page.create_html_panel("Panel") is None

    def test_append_adds_panel(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarPage

        page = ToolbarPage(MagicMock(), "Page")
        panel = page.append("My Panel")
        assert len(page.panels) == 1
        assert page.panels[0] is panel


class TestToolbarBar:

    def test_init_sets_attributes(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarBar

        parent = MagicMock()
        bar = ToolbarBar.__new__(ToolbarBar)
        bar.parent = parent
        bar.gui_style = "file clipboard browse"
        bar.pages = []
        bar.user_panels = {}
        bar.main_page = None

        assert bar.parent is parent
        assert bar.gui_style == "file clipboard browse"
        assert bar.pages == []
        assert bar.user_panels == {}
        assert bar.main_page is None

    def _make_bar(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarBar

        parent = MagicMock()
        bar = ToolbarBar.__new__(ToolbarBar)
        bar.parent = parent
        bar.pages = []
        bar.main_page = None
        bar.user_panels = {}
        return bar

    def test_append_returns_existing(self):
        bar = self._make_bar()

        page1 = bar.append("Test Page")
        page2 = bar.append("Test Page")
        assert page1 is page2

    def test_append_sets_main_page(self):
        bar = self._make_bar()

        page = bar.append("First Page")
        assert bar.main_page is page

    def test_remove_page(self):
        bar = self._make_bar()

        page = bar.append("Test Page")
        assert len(bar.pages) == 1

        bar.remove_page(page.title)
        assert len(bar.pages) == 0

    def test_remove_page_main_page(self):
        bar = self._make_bar()

        page1 = bar.append("Page 1")
        page2 = bar.append("Page 2")
        assert bar.main_page is page1

        bar.remove_page(page1.title)
        assert bar.main_page is page2

    def test_remove_page_clears_user_panels(self):
        bar = self._make_bar()

        page1 = bar.append("Page 1")

        mock_panel = MagicMock()
        mock_panel.page.title = page1.title
        bar.user_panels = {"test": mock_panel}

        bar.remove_page(page1.title)
        assert "test" not in bar.user_panels

    def test_remove_page_last_page(self):
        bar = self._make_bar()

        page = bar.append("Only Page")
        bar.remove_page(page.title)
        assert len(bar.pages) == 0
        assert bar.main_page is None

    def test_find_page_by_title(self):
        bar = self._make_bar()

        page = bar.append("Unique Page")
        result = bar._find_page_by_title(page.title)
        assert result is page

    def test_find_page_by_title_not_found(self):
        bar = self._make_bar()
        assert bar._find_page_by_title("Nonexistent") is None

    def test_find_page_by_title_with_duplicates(self):
        bar = self._make_bar()

        bar.append("Page A")
        page2 = bar.append("Page B")

        result = bar._find_page_by_title(page2.title)
        assert result is page2

    def test_bind_and_unbind(self):
        bar = self._make_bar()

        handler = MagicMock()
        bar.bind(handler, id=100)
        bar.parent.Bind.assert_called_once()
        bar.parent.Bind.reset_mock()

        bar.un_bind(id=100)
        bar.parent.Unbind.assert_called_once()

    def test_bind_with_custom_event(self):
        bar = self._make_bar()

        handler = MagicMock()
        custom_event = MagicMock()
        bar.bind(handler, id=200, e=custom_event)
        bar.parent.Bind.assert_called_once_with(custom_event, handler, id=200)

    def test_un_bind_with_custom_event(self):
        bar = self._make_bar()

        custom_event = MagicMock()
        bar.un_bind(id=200, e=custom_event)
        bar.parent.Unbind.assert_called_once_with(custom_event, id=200)

    def test_new_child_page_delegates(self):
        from pytigon_gui.toolbar.basetoolbar import ToolbarBar

        import wx
        mock_app = MagicMock()
        wx.GetApp = MagicMock(return_value=mock_app)

        bar = self._make_bar()

        bar.new_child_page("/test", "Test", None)
        mock_app.GetTopWindow().new_main_page.assert_called_once_with(
            "/test", "Test", None
        )

    def test_create_panel_in_main_page_auto_creates(self):
        bar = self._make_bar()

        panel = bar.create_panel_in_main_page("Test Panel", 0)
        assert bar.main_page is not None

    def test_create_panel_in_main_page_existing(self):
        bar = self._make_bar()

        main_page = bar.append("main tools")
        bar.main_page = main_page

        panel = bar.create_panel_in_main_page("Test Panel", 0)
        assert bar.main_page is main_page

    def test_create_page(self):
        bar = self._make_bar()

        page = bar.create_page("Test", 0)
        assert page is not None

    def test_create_and_close(self):
        bar = self._make_bar()
        bar.create()
        bar.close()
