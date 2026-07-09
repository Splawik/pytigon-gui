"""Tests for pytigon_gui.guiframe.notebook - SchNotebook class."""

import pytest
from unittest.mock import MagicMock


class TestSchNotebook:

    def test_set_panel_and_get_panel(self):
        from pytigon_gui.guiframe.notebook import SchNotebook

        nb = SchNotebook.__new__(SchNotebook)
        nb.panel = None

        mock_panel = MagicMock()
        nb.SetPanel(mock_panel)
        assert nb.GetPanel() is mock_panel

    def test_freeze_thaw_noop(self):
        from pytigon_gui.guiframe.notebook import SchNotebook

        nb = SchNotebook.__new__(SchNotebook)
        nb.Freeze()
        nb.Thaw()

    def test_activate_page_logic_deactivates_old(self):
        from pytigon_gui.guiframe.notebook import SchNotebook

        mock_self = MagicMock()
        old_page = MagicMock()
        mock_self.last_active = old_page
        new_page = MagicMock()

        SchNotebook.activate_page(mock_self, new_page)

        old_page.deactivate_page.assert_called_once()
        new_page.activate_page.assert_called_once()
        assert mock_self.last_active is new_page

    def test_activate_page_with_none(self):
        from pytigon_gui.guiframe.notebook import SchNotebook

        mock_self = MagicMock()
        old_page = MagicMock()
        mock_self.last_active = old_page

        SchNotebook.activate_page(mock_self, None)

        old_page.deactivate_page.assert_called_once()
        assert mock_self.last_active is None

    def test_activate_page_first_time(self):
        from pytigon_gui.guiframe.notebook import SchNotebook

        mock_self = MagicMock()
        mock_self.last_active = None
        new_page = MagicMock()

        SchNotebook.activate_page(mock_self, new_page)

        assert mock_self.last_active is new_page
        new_page.activate_page.assert_called_once()
