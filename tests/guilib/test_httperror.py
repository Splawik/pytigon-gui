"""Tests for pytigon_gui.guilib.httperror - HTTP error dialog."""

import pytest
from unittest.mock import MagicMock, patch


class TestHttpErrorDialog:
    """Tests for HttpErrorDialog class (mocked wx)."""

    def test_class_exists(self):
        """HttpErrorDialog is importable."""
        from pytigon_gui.guilib.httperror import HttpErrorDialog

        assert HttpErrorDialog is not None


class TestHttpErrorFunction:
    """Tests for http_error() and _http_error() functions."""

    @patch("pytigon_gui.guilib.httperror.wx")
    def test_http_error_schedules_callafter(self, mock_wx):
        """http_error uses wx.CallAfter to defer execution."""
        from pytigon_gui.guilib.httperror import http_error

        mock_wx.CallAfter = MagicMock()

        http_error(None, "error content")

        mock_wx.CallAfter.assert_called_once()

    @patch("pytigon_gui.guilib.httperror.wx")
    @patch("pytigon_gui.guilib.httperror.HttpErrorDialog")
    def test_http_error_content_string(self, mock_dlg_class, mock_wx):
        """_http_error handles string content."""
        from pytigon_gui.guilib.httperror import _http_error

        mock_wx.CallAfter = MagicMock()
        mock_app = MagicMock()
        mock_app.lock = False
        mock_app.GetTopWindow.return_value = MagicMock()
        mock_wx.GetApp.return_value = mock_app
        mock_wx.ID_CANCEL = 5101
        mock_wx.PlatformInfo = ""

        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = 5100  # Not cancel
        mock_dlg_class.return_value = mock_dlg

        _http_error(None, "<html>test error</html>")

        mock_dlg.Destroy = MagicMock()
        assert mock_app.lock == False


class TestHttpErrorContentHandling:
    """Tests for content type handling in http_error."""

    @patch("pytigon_gui.guilib.httperror.wx")
    @patch("pytigon_gui.guilib.httperror.HttpErrorDialog")
    def test_bytes_content_decoded(self, mock_dlg_class, mock_wx):
        """Bytes content is decoded to UTF-8 string."""
        from pytigon_gui.guilib.httperror import _http_error

        mock_app = MagicMock()
        mock_app.lock = False
        mock_app.GetTopWindow.return_value = MagicMock()
        mock_wx.GetApp.return_value = mock_app
        mock_wx.ID_CANCEL = 5101
        mock_wx.PlatformInfo = ""

        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = 5100
        mock_dlg_class.return_value = mock_dlg

        _http_error(None, b"<html>binary error</html>")

        mock_dlg_class.assert_called_once()
        args, _ = mock_dlg_class.call_args
        assert isinstance(args[2], str)
        assert "binary error" in args[2]

    @patch("pytigon_gui.guilib.httperror.wx")
    @patch("pytigon_gui.guilib.httperror.HttpErrorDialog")
    def test_cancel_exits(self, mock_dlg_class, mock_wx):
        """When Cancel is clicked, sys.exit is called."""
        from pytigon_gui.guilib.httperror import _http_error

        mock_app = MagicMock()
        mock_app.lock = False
        mock_app.GetTopWindow.return_value = MagicMock()
        mock_wx.GetApp.return_value = mock_app
        mock_wx.ID_CANCEL = 5101
        mock_wx.PlatformInfo = ""

        mock_dlg = MagicMock()
        mock_dlg.ShowModal.return_value = 5101  # Cancel
        mock_dlg_class.return_value = mock_dlg

        with patch("pytigon_gui.guilib.httperror.sys.exit") as mock_exit:
            _http_error(None, "error")
            mock_exit.assert_called_once()

    @patch("pytigon_gui.guilib.httperror.wx")
    def test_locked_app_skips(self, mock_wx):
        """When app.lock is True, dialog is not shown."""
        from pytigon_gui.guilib.httperror import _http_error

        mock_app = MagicMock()
        mock_app.lock = True
        mock_wx.GetApp.return_value = mock_app
        mock_wx.PlatformInfo = ""

        result = _http_error(None, "error")
        assert result is None
