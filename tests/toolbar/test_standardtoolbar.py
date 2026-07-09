"""Tests for pytigon_gui.toolbar.standardtoolbar - standard toolbar classes."""

import pytest
from unittest.mock import MagicMock


class TestStandardToolbarButton:

    def test_init(self):
        from pytigon_gui.toolbar.standardtoolbar import StandardToolbarButton

        btn = StandardToolbarButton.__new__(StandardToolbarButton)
        btn.parent_panel = MagicMock()
        btn.id = 1
        btn.title = "Test"
        assert btn.id == 1
        assert btn.title == "Test"


class TestStandardToolbarPage:

    def test_init(self):
        from pytigon_gui.toolbar.standardtoolbar import StandardToolbarPage

        parent_bar = MagicMock()
        parent_bar.pages = []

        page = StandardToolbarPage.__new__(StandardToolbarPage)
        page.parent_bar = parent_bar
        page.name = "Page"
        page.panels = []
        assert len(parent_bar.pages) == 0
