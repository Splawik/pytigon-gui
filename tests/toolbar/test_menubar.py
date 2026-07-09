"""Tests for pytigon_gui.toolbar.menubar - menu bar classes."""

import pytest
from unittest.mock import MagicMock


class TestMenuToolbarPage:

    def test_init(self):
        from pytigon_gui.toolbar.menubar import MenuToolbarPage

        page = MenuToolbarPage.__new__(MenuToolbarPage)
        page.parent_bar = MagicMock()
        page.name = "File"
        page.panels = []
        assert page.name == "File"


class TestMenuToolbarBar:

    def test_init(self):
        from pytigon_gui.toolbar.menubar import MenuToolbarBar

        bar = MenuToolbarBar.__new__(MenuToolbarBar)
        bar.pages = []
        bar.parent = MagicMock()
        assert bar.pages == []
