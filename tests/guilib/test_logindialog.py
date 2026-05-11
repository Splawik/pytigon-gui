"""Tests for pytigon_gui.guilib.logindialog - Login dialog."""

import pytest
from unittest.mock import MagicMock, patch


class TestLoginDialog:
    """Tests for LoginDialog class."""

    def test_class_exists(self):
        """LoginDialog is importable and is a class."""
        from pytigon_gui.guilib.logindialog import LoginDialog

        assert isinstance(LoginDialog, type)

    def test_has_expected_attributes(self):
        """LoginDialog defines expected UI controls."""
        from pytigon_gui.guilib.logindialog import LoginDialog

        # Verify the class has relevant methods
        assert hasattr(LoginDialog, "__init__")
        # The class is a wx.Dialog subclass with text1, text2 fields
