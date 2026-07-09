"""Tests for pytigon_gui.guiframe.notebookpage - SchNotebookPage class."""

import pytest
from unittest.mock import MagicMock


def _make_page():
    from pytigon_gui.guiframe.notebookpage import SchNotebookPage

    page = SchNotebookPage.__new__(SchNotebookPage)
    page.child_panels = []
    page.bestx = -1
    page.orient = None
    page.reverse_style = True
    page._layout_style = 0
    page._best_x_y_dx_dy = None
    page._last_x_y_dx_dy = None
    page.Refresh = MagicMock()
    return page


class TestSchNotebookPageBasic:

    def test_init_attributes(self):
        page = _make_page()
        assert page.child_panels == []
        assert page.bestx == -1
        assert page.orient is None
        assert page.reverse_style is True
        assert page._layout_style == 0

    def test_get_page_count(self):
        page = _make_page()
        assert page.get_page_count() == 0

        page.child_panels = [MagicMock(), MagicMock()]
        assert page.get_page_count() == 2

    def test_add_page_sets_child_panels(self):
        page = _make_page()

        mock_child = MagicMock()
        mock_child.disable_parent = False
        mock_child.vertical_position = None
        page._layout = MagicMock()

        page.add_page(mock_child)
        assert page.get_page_count() == 1
        assert page.get_page(0) is mock_child
        assert page.get_page(-1) is mock_child

    def test_add_page_disable_parent(self):
        page = _make_page()
        existing = MagicMock()
        existing.enable_forms = MagicMock()
        existing.disable_parent = False
        page.child_panels = [existing]
        page._layout = MagicMock()

        new_child = MagicMock()
        new_child.disable_parent = True

        page.add_page(new_child)
        existing.enable_forms.assert_called_once_with(False)

    def test_add_page_no_disable_when_false(self):
        page = _make_page()
        existing = MagicMock()
        existing.enable_forms = MagicMock()
        page.child_panels = [existing]
        page._layout = MagicMock()

        new_child = MagicMock()
        new_child.disable_parent = False

        page.add_page(new_child)
        existing.enable_forms.assert_not_called()

    def test_add_page_first_child(self):
        page = _make_page()
        page._layout = MagicMock()

        new_child = MagicMock()
        new_child.disable_parent = False

        page.add_page(new_child)
        assert page.get_page_count() == 1

    def test_get_margins(self):
        page = _make_page()
        assert page.get_margins() == 2

    def test_close_no_del_empty(self):
        page = _make_page()
        assert page.close_no_del() is False

    def test_close_no_del_single_child_can_close(self):
        page = _make_page()
        mock_child = MagicMock()
        mock_child.CanClose.return_value = True
        page.child_panels = [mock_child]

        assert page.close_no_del() is False
        mock_child.Destroy.assert_called_once()

    def test_close_no_del_single_child_cannot_close(self):
        page = _make_page()
        mock_child = MagicMock()
        mock_child.CanClose.return_value = False
        page.child_panels = [mock_child]

        assert page.close_no_del() is True
        mock_child.Destroy.assert_not_called()

    def test_close_no_del_multiple_children(self):
        page = _make_page()
        child1 = MagicMock()
        child1.CanClose.return_value = True
        child1.disable_parent = False
        child2 = MagicMock()
        child2.CanClose.return_value = True
        child2.disable_parent = False
        page.child_panels = [child1, child2]

        page._layout = MagicMock()

        result = page.close_no_del()
        assert result is True
        child2.Destroy.assert_called_once()

    def test_close_no_del_multiple_with_ok(self):
        page = _make_page()
        child1 = MagicMock()
        child1.CanClose.return_value = True
        child1.disable_parent = False
        child2 = MagicMock()
        child2.CanClose.return_value = True
        child2.disable_parent = False
        page.child_panels = [child1, child2]

        page._layout = MagicMock()

        result = page.close_no_del(close_without_refresh=False)
        assert result is True
        child2.Destroy.assert_called_once()

    def test_activate_page_with_children(self):
        page = _make_page()
        mock_child = MagicMock()
        page.child_panels = [mock_child]

        page.activate_page()
        mock_child.activate_page.assert_called_once()

    def test_activate_page_empty(self):
        page = _make_page()
        page.SetFocus = MagicMock()

        page.activate_page()
        page.SetFocus.assert_called_once()

    def test_deactivate_page(self):
        page = _make_page()
        mock_child = MagicMock()
        page.child_panels = [mock_child]

        page.deactivate_page()
        mock_child.deactivate_page.assert_called_once()

    def test_deactivate_page_empty(self):
        page = _make_page()
        page.deactivate_page()

    def test_on_child_form_ok(self):
        page = _make_page()
        page.close_child_page = MagicMock()

        page.on_child_form_ok()
        page.close_child_page.assert_called_once_with(False)

    def test_on_child_form_cancel(self):
        page = _make_page()
        page.close_child_page = MagicMock()

        page.on_child_form_cancel()
        page.close_child_page.assert_called_once_with(True)

    def test_close_child_page_last_page(self):
        page = _make_page()
        page.close_no_del = MagicMock(return_value=False)

        parent = MagicMock()
        parent._tabs = MagicMock()
        parent._tabs._pages = [MagicMock(window=page)]
        parent.DeletePage = MagicMock()
        page.GetParent = MagicMock(return_value=parent)

        page.close_child_page()
        parent.DeletePage.assert_called_once()

    def test_close_child_page_not_last(self):
        page = _make_page()
        page.close_no_del = MagicMock(return_value=True)

        parent = MagicMock()
        parent._tabs = MagicMock()
        parent._tabs._pages = [MagicMock(window=page), MagicMock()]
        parent.DeletePage = MagicMock()
        page.GetParent = MagicMock(return_value=parent)

        result = page.close_child_page()
        assert result is True
        parent.DeletePage.assert_not_called()

    def test_close_child_page_not_found(self):
        page = _make_page()

        parent = MagicMock()
        parent._tabs = MagicMock()
        parent._tabs._pages = [MagicMock(window=MagicMock())]
        page.GetParent = MagicMock(return_value=parent)

        assert page.close_child_page() is False

    def test_layout_single_page(self):
        page = _make_page()
        mock_child = MagicMock()
        mock_child.vertical_position = None

        mock_size = MagicMock()
        mock_size.GetWidth.return_value = 800
        mock_size.GetHeight.return_value = 600
        page.GetSize = MagicMock(return_value=mock_size)

        page.child_panels = [mock_child]
        page._layout()

        assert page._layout_style == 0
        mock_child.SetSize.assert_called_once()

    def test_layout_two_pages(self):
        page = _make_page()
        child1 = MagicMock()
        child1.calculate_best_size.return_value = (200, 300)
        child1.vertical_position = None
        child2 = MagicMock()
        child2.calculate_best_size.return_value = (200, 300)
        child2.vertical_position = None

        mock_size = MagicMock()
        mock_size.GetWidth.return_value = 800
        mock_size.GetHeight.return_value = 600
        page.GetSize = MagicMock(return_value=mock_size)

        page.child_panels = [child1, child2]
        page._layout()

        assert page._layout_style in (1, 2)
        assert child1.SetSize.call_count == 1
        assert child2.SetSize.call_count == 1

    def test_layout_many_pages(self):
        page = _make_page()
        children = []
        for i in range(4):
            child = MagicMock()
            child.calculate_best_size.return_value = (150, 150)
            child.vertical_position = None
            children.append(child)

        mock_size = MagicMock()
        mock_size.GetWidth.return_value = 800
        mock_size.GetHeight.return_value = 600
        page.GetSize = MagicMock(return_value=mock_size)

        page.child_panels = children
        page._layout()

        assert page._layout_style == 3

    def test_get_xy_default(self):
        page = _make_page()
        page._best_x_y_dx_dy = None

        mock_child = MagicMock()
        mock_child.calculate_best_size.return_value = (200, 200)
        page.get_page = MagicMock(return_value=mock_child)

        mock_size = MagicMock()
        mock_size.GetWidth.return_value = 800
        mock_size.GetHeight.return_value = 600

        result = page.get_xy(mock_size, -1)
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_get_xy_with_best(self):
        page = _make_page()
        page._best_x_y_dx_dy = (100, 200, 800, 600)
        page.GetSize = MagicMock(return_value=MagicMock())

        result = page.get_xy()
        assert result == (100, 200, 800, 600)

    def test_get_xy_bestx_cutoff(self):
        page = _make_page()
        page._best_x_y_dx_dy = None

        mock_child = MagicMock()
        mock_child.calculate_best_size.return_value = (900, 700)
        page.get_page = MagicMock(return_value=mock_child)

        mock_size = MagicMock()
        mock_size.GetWidth.return_value = 800
        mock_size.GetHeight.return_value = 600

        result = page.get_xy(mock_size, -1)
        assert result[0] == 80.0

    def test_mouse_drag_flow(self):
        page = _make_page()
        page.CaptureMouse = MagicMock()
        page.ReleaseMouse = MagicMock()
        page.SetCursor = MagicMock()
        page._layout = MagicMock()

        import wx
        wx.Cursor = MagicMock()
        wx.CURSOR_SIZING = 1

        mock_event = MagicMock()
        mock_event.GetPosition.return_value = (100, 100)

        page._last_x_y_dx_dy = (50, 50, 800, 600)

        page.on_left_down(mock_event)
        assert page._start_pos == (100, 100)
        assert page._start_pos_x_y_dx_dy == (50, 50, 800, 600)

        mock_event2 = MagicMock()
        mock_event2.GetPosition.return_value = (120, 100)

        page.reverse_style = False
        page.on_move(mock_event2)
        page._layout.assert_called()

        wx.CURSOR_ARROW = 2
        page.on_left_up(MagicMock())
        assert page._start_pos is None

    def test_mouse_drag_no_start(self):
        page = _make_page()
        page._start_pos = None
        page._start_pos_x_y_dx_dy = None

        mock_event = MagicMock()
        mock_event.GetPosition.return_value = (120, 100)
        page._layout = MagicMock()

        page.on_move(mock_event)
        page._layout.assert_not_called()

    def test_mouse_release_without_drag(self):
        page = _make_page()
        page._start_pos = None
        page._start_pos_x_y_dx_dy = None
        page.ReleaseMouse = MagicMock()
        page.SetCursor = MagicMock()

        page.on_left_up(MagicMock())
        assert page._start_pos is None

    def test_layout_empty(self):
        page = _make_page()
        page._layout()

    def test_get_xy_without_size(self):
        page = _make_page()

        mock_child = MagicMock()
        mock_child.calculate_best_size.return_value = (200, 200)
        page.get_page = MagicMock(return_value=mock_child)

        mock_size = MagicMock()
        mock_size.GetWidth.return_value = 1024
        mock_size.GetHeight.return_value = 768
        page.GetSize = MagicMock(return_value=mock_size)

        result = page.get_xy()
        assert isinstance(result, tuple)
        assert len(result) == 4
