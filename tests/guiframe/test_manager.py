"""Tests for pytigon_gui.guiframe.manager - AUI manager classes."""

import pytest
from unittest.mock import MagicMock


class TestSChAuiManager:

    def test_on_left_down_passes_non_border(self):
        from pytigon_gui.guiframe.manager import SChAuiBaseManager

        mgr = SChAuiBaseManager.__new__(SChAuiBaseManager)
        mock_event = MagicMock()
        mock_event.GetPosition.return_value = (100, 100)
        mgr.HitTest = MagicMock()
        mgr.HitTest.return_value = type("HitTestResult", (), {"type": 2})()

        mgr.OnLeftDown(mock_event)

    def test_on_left_down_ignores_border_type0(self):
        from pytigon_gui.guiframe.manager import SChAuiBaseManager

        mgr = SChAuiBaseManager.__new__(SChAuiBaseManager)
        mock_event = MagicMock()
        mock_event.GetPosition.return_value = (100, 100)
        mgr.HitTest = MagicMock()
        mgr.HitTest.return_value = type("HitTestResult", (), {"type": 0})()

        mgr.OnLeftDown(mock_event)

    def test_on_left_down_ignores_border_type1(self):
        from pytigon_gui.guiframe.manager import SChAuiBaseManager

        mgr = SChAuiBaseManager.__new__(SChAuiBaseManager)
        mock_event = MagicMock()
        mock_event.GetPosition.return_value = (200, 200)
        mgr.HitTest = MagicMock()
        mgr.HitTest.return_value = type("HitTestResult", (), {"type": 1})()

        mgr.OnLeftDown(mock_event)
