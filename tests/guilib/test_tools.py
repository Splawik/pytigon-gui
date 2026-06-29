"""Tests for pytigon_gui.guilib.tools - utility functions."""

import pytest
import sys
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# norm_colour2
# ---------------------------------------------------------------------------


class TestNormColour2:
    """Tests for norm_colour2() - single channel clamping."""

    def test_within_range(self):
        """Value within 0-255 stays unchanged."""
        from pytigon_gui.guilib.tools import norm_colour2

        assert norm_colour2(100) == 100

    def test_zero(self):
        """Zero stays zero."""
        from pytigon_gui.guilib.tools import norm_colour2

        assert norm_colour2(0) == 0

    def test_max_value(self):
        """255 stays 255."""
        from pytigon_gui.guilib.tools import norm_colour2

        assert norm_colour2(255) == 255

    def test_above_range(self):
        """Value above 255 is clamped to 255."""
        from pytigon_gui.guilib.tools import norm_colour2

        assert norm_colour2(300) == 255

    def test_negative(self):
        """Negative values pass through (int conversion preserves them)."""
        from pytigon_gui.guilib.tools import norm_colour2

        assert norm_colour2(-10) == -10

    def test_float_truncation(self):
        """Float values are truncated to int."""
        from pytigon_gui.guilib.tools import norm_colour2

        assert norm_colour2(100.7) == 100


# ---------------------------------------------------------------------------
# norm_colour
# ---------------------------------------------------------------------------


class TestNormColour:
    """Tests for norm_colour() - RGB color interpolation."""

    def test_no_change(self):
        """proc=1 returns same color."""
        from pytigon_gui.guilib.tools import norm_colour

        result = norm_colour(100, 150, 200, 1.0)
        assert result == [100, 150, 200]

    def test_darken(self):
        """proc<1 blends toward black."""
        from pytigon_gui.guilib.tools import norm_colour

        result = norm_colour(100, 150, 200, 0.5)
        assert result == [50, 75, 100]

    def test_lighten(self):
        """proc>1 blends toward white."""
        from pytigon_gui.guilib.tools import norm_colour

        result = norm_colour(100, 150, 200, 1.5)
        assert result == [177, 202, 227]

    def test_darken_zero(self):
        """proc=0 gives pure black."""
        from pytigon_gui.guilib.tools import norm_colour

        result = norm_colour(100, 150, 200, 0.0)
        assert result == [0, 0, 0]

    def test_lighten_max(self):
        """proc=2 gives pure white."""
        from pytigon_gui.guilib.tools import norm_colour

        result = norm_colour(100, 150, 200, 2.0)
        assert result == [255, 255, 255]

    def test_clamp_overflow(self):
        """Values above 255 are clamped."""
        from pytigon_gui.guilib.tools import norm_colour

        result = norm_colour(200, 200, 200, 1.9)
        assert all(v <= 255 for v in result)


# ---------------------------------------------------------------------------
# colour_to_html
# ---------------------------------------------------------------------------


class TestColourToHtml:
    """Tests for colour_to_html() - wx.Colour to HTML hex string."""

    @patch("pytigon_gui.guilib.tools.wx")
    def test_red(self, mock_wx):
        """Red colour becomes #RRGGBB."""
        from pytigon_gui.guilib.tools import colour_to_html

        mock_colour = MagicMock()
        mock_colour.Red.return_value = 255
        mock_colour.Green.return_value = 0
        mock_colour.Blue.return_value = 0

        mock_wx.Colour.return_value = MagicMock()
        mock_wx.Colour.return_value.GetAsString.return_value = "#FF0000"
        mock_wx.C2S_HTML_SYNTAX = 1

        result = colour_to_html(mock_colour)
        assert result == "#FF0000"

    @patch("pytigon_gui.guilib.tools.wx")
    def test_black(self, mock_wx):
        """Black colour."""
        from pytigon_gui.guilib.tools import colour_to_html

        mock_colour = MagicMock()
        mock_colour.Red.return_value = 0
        mock_colour.Green.return_value = 0
        mock_colour.Blue.return_value = 0

        mock_wx.Colour.return_value = MagicMock()
        mock_wx.Colour.return_value.GetAsString.return_value = "#000000"

        result = colour_to_html(mock_colour)
        assert result == "#000000"


# ---------------------------------------------------------------------------
# get_colour
# ---------------------------------------------------------------------------


class TestGetColour:
    """Tests for get_colour() - system color with optional blend."""

    @patch("pytigon_gui.guilib.tools.wx")
    def test_no_blend(self, mock_wx):
        """Without proc, returns HTML string directly."""
        from pytigon_gui.guilib.tools import get_colour

        mock_sys_colour = MagicMock()
        mock_sys_colour.Red.return_value = 128
        mock_sys_colour.Green.return_value = 128
        mock_sys_colour.Blue.return_value = 128

        mock_wx.SystemSettings.GetColour.return_value = mock_sys_colour
        mock_wx.Colour.return_value = MagicMock()
        mock_wx.Colour.return_value.GetAsString.return_value = "#808080"
        mock_wx.SYS_COLOUR_3DFACE = 15

        result = get_colour(15)
        assert result == "#808080"

    @patch("pytigon_gui.guilib.tools.wx")
    def test_with_blend(self, mock_wx):
        """With proc, blends the colour."""
        from pytigon_gui.guilib.tools import get_colour

        mock_sys_colour = MagicMock()
        mock_sys_colour.Red.return_value = 100
        mock_sys_colour.Green.return_value = 100
        mock_sys_colour.Blue.return_value = 100

        mock_wx.SystemSettings.GetColour.return_value = mock_sys_colour
        mock_wx.Colour.return_value = MagicMock()
        mock_wx.Colour.return_value.GetAsString.return_value = "#323232"
        mock_wx.SYS_COLOUR_3DFACE = 15

        result = get_colour(15, proc=0.5)
        assert result == "#323232"


# ---------------------------------------------------------------------------
# standard_tab_colour
# ---------------------------------------------------------------------------


class TestStandardTabColour:
    """Tests for standard_tab_colour() - CSS color variables for tabs."""

    @patch("pytigon_gui.guilib.tools.wx")
    def test_returns_tuple_of_pairs(self, mock_wx):
        """Returns a tuple of (name, color) pairs."""
        from pytigon_gui.guilib.tools import standard_tab_colour

        mock_sys_colour = MagicMock()
        mock_sys_colour.Red.return_value = 200
        mock_sys_colour.Green.return_value = 200
        mock_sys_colour.Blue.return_value = 200

        mock_wx.SystemSettings.GetColour.return_value = mock_sys_colour
        mock_wx.Colour.return_value = MagicMock()
        mock_wx.Colour.return_value.GetAsString.return_value = "#C8C8C8"
        mock_wx.SYS_COLOUR_3DFACE = 15
        mock_wx.SYS_COLOUR_3DHIGHLIGHT = 16
        mock_wx.SYS_COLOUR_3DSHADOW = 17
        mock_wx.SYS_COLOUR_INFOBK = 18

        result = standard_tab_colour()

        assert isinstance(result, tuple)
        assert len(result) > 0
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], str)

    @patch("pytigon_gui.guilib.tools.wx")
    def test_contains_expected_keys(self, mock_wx):
        """Contains known CSS variable names."""
        from pytigon_gui.guilib.tools import standard_tab_colour

        mock_sys_colour = MagicMock()
        mock_sys_colour.Red.return_value = 200
        mock_sys_colour.Green.return_value = 200
        mock_sys_colour.Blue.return_value = 200

        mock_wx.SystemSettings.GetColour.return_value = mock_sys_colour
        mock_wx.Colour.return_value = MagicMock()
        mock_wx.Colour.return_value.GetAsString.return_value = "#C8C8C8"
        mock_wx.SYS_COLOUR_3DFACE = 15
        mock_wx.SYS_COLOUR_3DHIGHLIGHT = 16
        mock_wx.SYS_COLOUR_3DSHADOW = 17
        mock_wx.SYS_COLOUR_INFOBK = 18

        result = standard_tab_colour()
        keys = {item[0] for item in result}

        assert "color_body" in keys
        assert "color_body_0_5" in keys
        assert "color_higlight" in keys
        assert "color_shadow" in keys
        assert "color_info" in keys


# ---------------------------------------------------------------------------
# import_plugin
# ---------------------------------------------------------------------------


class TestImportPlugin:
    """Tests for import_plugin() function."""

    BASE_CONFIG = {
        "PYTIGON_PATH": "/tmp/pytigon",
        "DATA_PATH": "/tmp/data",
        "PRJ_PATH": "/tmp/prj",
        "PRJ_PATH_ALT": "/tmp/prj_alt",
    }

    @patch("pytigon_gui.guilib.tools.importlib.import_module")
    @patch("pathlib.Path.exists")
    @patch("pytigon_gui.guilib.tools.get_main_paths")
    def test_import_success_no_project(self, mock_paths, mock_exists, mock_import):
        """Imports a plugin without project name."""
        from pytigon_gui.guilib.tools import import_plugin

        mock_paths.return_value = dict(self.BASE_CONFIG)
        mock_exists.return_value = True
        mock_import.return_value = "plugin_module"

        result = import_plugin("plugins.myplugin")
        assert result == "plugin_module"

    @patch("pytigon_gui.guilib.tools.importlib.import_module")
    @patch("pathlib.Path.exists")
    @patch("pytigon_gui.guilib.tools.get_main_paths")
    def test_import_with_project(self, mock_paths, mock_exists, mock_import):
        """Imports a plugin with project name."""
        from pytigon_gui.guilib.tools import import_plugin

        mock_paths.return_value = dict(self.BASE_CONFIG)
        mock_exists.return_value = True
        mock_import.return_value = "plugin_module"

        result = import_plugin("plugins.myplugin", prj_name="myproject")
        assert result == "plugin_module"

    @patch("pathlib.Path.exists")
    @patch("pytigon_gui.guilib.tools.get_main_paths")
    def test_path_not_found(self, mock_paths, mock_exists):
        """Returns None when plugin path not found."""
        from pytigon_gui.guilib.tools import import_plugin

        mock_paths.return_value = dict(self.BASE_CONFIG)
        mock_exists.return_value = False

        result = import_plugin("plugins.nonexistent")
        assert result is None

    @patch("pytigon_gui.guilib.tools.importlib.import_module")
    @patch("pathlib.Path.exists")
    @patch("pytigon_gui.guilib.tools.get_main_paths")
    def test_import_failure(self, mock_paths, mock_exists, mock_import):
        """Returns None when import fails."""
        from pytigon_gui.guilib.tools import import_plugin

        mock_paths.return_value = dict(self.BASE_CONFIG)
        mock_exists.return_value = True
        mock_import.side_effect = ImportError("No module named 'bad'")

        result = import_plugin("plugins.badplugin")
        assert result is None


# ---------------------------------------------------------------------------
# Size constants
# ---------------------------------------------------------------------------


class TestSizeConstants:
    """Verify size constants are defined."""

    def test_constants(self):
        """SIZE_DEFAULT, SIZE_SMALL, SIZE_MEDIUM, SIZE_LARGE are correct."""
        from pytigon_gui.guilib.tools import (
            SIZE_DEFAULT,
            SIZE_SMALL,
            SIZE_MEDIUM,
            SIZE_LARGE,
        )

        assert SIZE_DEFAULT == -1
        assert SIZE_SMALL == 0
        assert SIZE_MEDIUM == 1
        assert SIZE_LARGE == 2
