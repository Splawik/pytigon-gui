"""Tests for pytigon_gui.wxauto - GUI automation utilities."""

import pytest
from unittest.mock import MagicMock, patch


class TestWxAuto:
    """Tests for WxAuto standalone methods."""

    def test_get_region_with_pos_and_size(self):
        from pytigon_gui.wxauto import WxAuto

        auto = WxAuto.__new__(WxAuto)
        mock_pos = MagicMock()
        mock_pos.x = 10
        mock_pos.y = 20
        auto.pos = mock_pos
        mock_size = MagicMock()
        mock_size.GetWidth.return_value = 800
        mock_size.GetHeight.return_value = 600
        auto.size = mock_size

        region = auto.get_region()
        assert region == (10, 20, 800, 600)

    def test_get_region_none(self):
        from pytigon_gui.wxauto import WxAuto

        auto = WxAuto.__new__(WxAuto)
        auto.pos = None
        auto.size = None

        assert auto.get_region() is None

    def test_get_region_pos_only(self):
        from pytigon_gui.wxauto import WxAuto

        auto = WxAuto.__new__(WxAuto)
        mock_pos = MagicMock()
        mock_pos.x = 50
        mock_pos.y = 100
        auto.pos = mock_pos
        auto.size = None

        assert auto.get_region() is None

    def test_get_region_size_only(self):
        from pytigon_gui.wxauto import WxAuto

        auto = WxAuto.__new__(WxAuto)
        auto.pos = None
        auto.size = (1024, 768)

        assert auto.get_region() is None


class TestControlProxy:
    """Tests for ControlProxy utility methods."""

    def test_init(self):
        from pytigon_gui.wxauto import ControlProxy

        mock_auto = MagicMock()
        proxy = ControlProxy(mock_auto, "my_button")
        assert proxy.wx_auto is mock_auto
        assert proxy.control_name == "my_button"


class TestImgProxy:
    """Tests for ImgProxy utility methods."""

    def test_init(self):
        from pytigon_gui.wxauto import ImgProxy

        mock_auto = MagicMock()
        proxy = ImgProxy(mock_auto, "my_image.png")
        assert proxy.wx_auto is mock_auto
        assert proxy.img_name == "my_image.png"
        assert proxy.img is None
