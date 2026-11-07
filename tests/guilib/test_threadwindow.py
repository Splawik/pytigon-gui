"""Tests for pytigon_gui.guilib.threadwindow - thread status panel."""

import pytest
from unittest.mock import MagicMock, patch


class TestThreadEvent:
    """Tests for ThreadEvent custom event class."""

    def test_event_creation(self):
        """ThreadEvent can be created and store info."""
        from pytigon_gui.guilib.threadwindow import ThreadEvent, schEVT_THREAD_INFO

        evt = ThreadEvent(schEVT_THREAD_INFO, -1)
        assert evt.info is None
        assert hasattr(evt, "info")

    def test_set_and_get_info(self):
        """Info can be set and retrieved."""
        from pytigon_gui.guilib.threadwindow import ThreadEvent, schEVT_THREAD_INFO

        evt = ThreadEvent(schEVT_THREAD_INFO, -1)
        evt.set_info("test_data")
        assert evt.get_info() == "test_data"

    def test_info_dict(self):
        """Info can be a dictionary."""
        from pytigon_gui.guilib.threadwindow import ThreadEvent, schEVT_THREAD_INFO

        evt = ThreadEvent(schEVT_THREAD_INFO, -1)
        evt.set_info({"progress": 50})
        assert evt.get_info() == {"progress": 50}


class TestSchThreadManager:
    """Tests for SChThreadManager."""

    def test_class_exists(self):
        """SChThreadManager is importable."""
        from pytigon_gui.guilib.threadwindow import SChThreadManager

        assert SChThreadManager is not None

    @patch("pytigon_gui.guilib.threadwindow.SChThreadWindow")
    def test_init(self, mock_win):
        """SChThreadManager initializes with empty windows list."""
        from pytigon_gui.guilib.threadwindow import SChThreadManager

        mock_app = MagicMock()
        mock_statusbar = MagicMock()

        mgr = SChThreadManager(mock_app, mock_statusbar)
        assert mgr.windows == []
        assert mgr.sizeChanged == True

    @patch("pytigon_gui.guilib.threadwindow.SChThreadWindow")
    def test_append(self, mock_win_class):
        """append adds a SChThreadWindow to the list."""
        from pytigon_gui.guilib.threadwindow import SChThreadManager

        mock_app = MagicMock()
        mock_statusbar = MagicMock()
        mock_win = MagicMock()
        mock_win_class.return_value = mock_win

        mgr = SChThreadManager(mock_app, mock_statusbar)
        mgr.append("thread_1")

        assert len(mgr.windows) == 1
        assert mgr.sizeChanged == True

    def test_reposition_empty(self):
        """reposition does nothing when no windows."""
        from pytigon_gui.guilib.threadwindow import SChThreadManager

        mock_app = MagicMock()
        mock_statusbar = MagicMock()

        mgr = SChThreadManager(mock_app, mock_statusbar)
        mgr.reposition()  # Should not raise

    @patch("pytigon_gui.guilib.threadwindow.SChThreadWindow")
    def test_timer_removes_closed_windows(self, mock_win_class):
        """timer destroys and removes closed windows."""
        from pytigon_gui.guilib.threadwindow import SChThreadManager

        mock_app = MagicMock()
        mock_statusbar = MagicMock()

        mock_win = MagicMock()
        mock_win.is_closed.return_value = True
        mock_win_class.return_value = mock_win

        mgr = SChThreadManager(mock_app, mock_statusbar)
        mgr.append("thread_1")
        mgr.timer()

        assert len(mgr.windows) == 0
        mock_win.Destroy.assert_called_once()

    @patch("pytigon_gui.guilib.threadwindow.SChThreadWindow")
    def test_timer_polls_open_windows(self, mock_win_class):
        """timer calls timer() on open windows."""
        from pytigon_gui.guilib.threadwindow import SChThreadManager

        mock_app = MagicMock()
        mock_statusbar = MagicMock()

        mock_win = MagicMock()
        mock_win.is_closed.return_value = False
        mock_win_class.return_value = mock_win

        mgr = SChThreadManager(mock_app, mock_statusbar)
        mgr.append("thread_1")
        mgr.timer()

        mock_win.timer.assert_called_once()


class TestEventBindings:
    """Tests for event type and binder exports."""

    def test_event_type_exists(self):
        """schEVT_THREAD_INFO is defined."""
        from pytigon_gui.guilib.threadwindow import schEVT_THREAD_INFO

        assert schEVT_THREAD_INFO is not None

    def test_event_binder_exists(self):
        """EVT_THREAD_INFO binder is defined."""
        from pytigon_gui.guilib.threadwindow import EVT_THREAD_INFO

        assert EVT_THREAD_INFO is not None


class TestSchThreadWindow:
    """Simple tests for SChThreadWindow."""

    def test_class_exists(self):
        """SChThreadWindow is importable."""
        from pytigon_gui.guilib.threadwindow import SChThreadWindow

        assert SChThreadWindow is not None
