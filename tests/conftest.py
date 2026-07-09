"""Pytest configuration and fixtures for pytigon_gui tests."""

import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="session", autouse=True)
def _mock_missing_modules():
    """Mock modules that are unavailable or platform-specific in test env."""

    mock_autocomplete = MagicMock()
    mock_autocomplete.TextCtrlAutoComplete = MagicMock()
    sys.modules["autocomplete"] = mock_autocomplete

    try:
        import wx

        wx.svg = MagicMock()
        wx.lib = MagicMock()
        wx.lib.agw = MagicMock()
        wx.lib.agw.aui = MagicMock()
        wx.lib.agw.aui.framemanager = MagicMock()
        wx.lib.agw.aui.aui_constants = MagicMock()
        wx.lib.agw.aui.aui_utilities = MagicMock()
        wx.lib.agw.ribbon = MagicMock()
        wx.lib.agw.ribbon.art = MagicMock()
        wx.lib.agw.customtreectrl = MagicMock()
        wx.lib.agw.flatmenu = MagicMock()
        wx.lib.scrolledpanel = MagicMock()
        wx.lib.platebtn = MagicMock()
        wx.lib.newevent = MagicMock()
        wx.lib.masked = MagicMock()
        wx.lib.masked.numctrl = MagicMock()
        wx.lib.masked.textctrl = MagicMock()
        wx.lib.masked.combobox = MagicMock()
        wx.lib.intctrl = MagicMock()
        wx.lib.calendar = MagicMock()
        wx.lib.buttons = MagicMock()
        wx.adv = MagicMock()
        wx.html = MagicMock()
    except ImportError:
        pass

    yield
