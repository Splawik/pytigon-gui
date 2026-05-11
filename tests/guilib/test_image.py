"""Tests for pytigon_gui.guilib.image - image conversion utilities."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from io import BytesIO


class TestWxArtMap:
    """Tests for the _WX_ART_MAP lookup table."""

    def test_map_contains_expected_entries(self):
        """The art map should contain known wx.ART_* identifiers."""
        from pytigon_gui.guilib.image import _WX_ART_MAP

        expected = [
            "wx.ART_COPY",
            "wx.ART_CUT",
            "wx.ART_PASTE",
            "wx.ART_FILE_OPEN",
            "wx.ART_FILE_SAVE",
            "wx.ART_DELETE",
        ]
        for key in expected:
            assert key in _WX_ART_MAP

    def test_resolve_art_id_known(self):
        """_resolve_art_id returns correct constant for known IDs."""
        from pytigon_gui.guilib.image import _resolve_art_id, _WX_ART_MAP

        result = _resolve_art_id("wx.ART_COPY")
        assert result is _WX_ART_MAP["wx.ART_COPY"]

    def test_resolve_art_id_unknown(self):
        """_resolve_art_id returns None for unknown IDs."""
        from pytigon_gui.guilib.image import _resolve_art_id

        result = _resolve_art_id("wx.ART_UNKNOWN_THING")
        assert result is None


class TestImageConversions:
    """Tests for bitmap/image/PIL conversion functions."""

    @patch("pytigon_gui.guilib.image.wx")
    def test_bitmap_to_image(self, mock_wx):
        """bitmap_to_image converts wx.Bitmap to wx.Image."""
        from pytigon_gui.guilib.image import bitmap_to_image

        mock_bitmap = MagicMock()
        mock_wx.ImageFromBitmap.return_value = "image_obj"

        result = bitmap_to_image(mock_bitmap)
        assert result == "image_obj"
        mock_wx.ImageFromBitmap.assert_called_once_with(mock_bitmap)

    def test_image_to_bitmap(self):
        """image_to_bitmap converts wx.Image to wx.Bitmap."""
        from pytigon_gui.guilib.image import image_to_bitmap

        mock_image = MagicMock()
        mock_image.ConvertToBitmap.return_value = "bitmap_obj"

        result = image_to_bitmap(mock_image)
        assert result == "bitmap_obj"

    @patch("pytigon_gui.guilib.image.wx")
    def test_bitmap_from_art_id(self, mock_wx):
        """bitmap_from_art_id queries ArtProvider."""
        from pytigon_gui.guilib.image import bitmap_from_art_id

        mock_wx.ArtProvider.GetBitmap.return_value = "bitmap"
        mock_wx.ART_OTHER = 2

        result = bitmap_from_art_id(100, (16, 16))
        assert result == "bitmap"

    @patch("pytigon_gui.guilib.image.wx")
    def test_bitmaps_from_art_id(self, mock_wx):
        """bitmaps_from_art_id returns (bitmap, disabled_bitmap) tuple."""
        from pytigon_gui.guilib.image import bitmaps_from_art_id

        mock_bmp = MagicMock()
        mock_img = MagicMock()
        mock_greyscale = MagicMock()
        mock_adjusted = MagicMock()
        mock_bmp.ConvertToImage.return_value = mock_img
        mock_img.ConvertToGreyscale.return_value = mock_greyscale
        mock_greyscale.AdjustChannels.return_value = mock_adjusted
        mock_wx.ArtProvider.GetBitmap.return_value = mock_bmp
        mock_wx.Bitmap.return_value = "disabled_bmp"
        mock_wx.ART_OTHER = 2

        result = bitmaps_from_art_id(100, (16, 16))
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestBitmapFromHref:
    """Tests for bitmap_from_href() function."""

    @patch("pytigon_gui.guilib.image.wx")
    def test_wx_art_id(self, mock_wx):
        """wx.ART_* hrefs use ArtProvider."""
        from pytigon_gui.guilib.image import bitmap_from_href, SIZE_DEFAULT

        mock_wx.ArtProvider.GetBitmap.return_value = "bitmap"
        mock_wx.ART_TOOLBAR = 3
        mock_wx.ART_MISSING_IMAGE = 100
        mock_wx.ART_COPY = 200

        with patch("pytigon_gui.guilib.image._resolve_art_id", return_value=200):
            result = bitmap_from_href("wx.ART_COPY")
            assert result == "bitmap"

    @patch("pytigon_gui.guilib.image.wx")
    def test_unknown_protocol(self, mock_wx):
        """Unknown hrefs return ART_MISSING_IMAGE."""
        from pytigon_gui.guilib.image import bitmap_from_href

        mock_wx.ArtProvider.GetBitmap.return_value = "missing"
        mock_wx.ART_TOOLBAR = 3
        mock_wx.ART_MISSING_IMAGE = 100

        result = bitmap_from_href("unknown://something")
        assert result == "missing"

    @patch("pytigon_gui.guilib.image.wx")
    def test_size_query_parameter(self, mock_wx):
        """Size query parameter changes icon size."""
        from pytigon_gui.guilib.image import bitmap_from_href

        mock_wx.ArtProvider.GetBitmap.return_value = "bitmap"
        mock_wx.ART_TOOLBAR = 3
        mock_wx.ART_MISSING_IMAGE = 100
        mock_wx.ART_COPY = 200

        with patch("pytigon_gui.guilib.image._resolve_art_id", return_value=200):
            result = bitmap_from_href("wx.ART_COPY?size=0")
            assert result == "bitmap"
            call_args = mock_wx.ArtProvider.GetBitmap.call_args
            assert call_args[0][2] == (16, 16)


class TestSchImage:
    """Tests for SchImage sprite sheet extractor."""

    @patch("pytigon_gui.guilib.image.wx")
    def test_sch_image_initialization(self, mock_wx):
        """SchImage loads image from server."""
        from pytigon_gui.guilib.image import SchImage

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.ret_code = 200
        mock_response.ptr.return_value = b"\x00" * 100
        mock_http.get.return_value = mock_response
        mock_wx.GetApp.return_value.http = mock_http
        mock_wx.Bitmap.return_value = MagicMock()
        mock_wx.Image.return_value = MagicMock()

        img = SchImage("http://example.com/sprite.png", (20, 20))
        assert img.one_image_size == (20, 20)
        assert img.bmp is not None

    @patch("pytigon_gui.guilib.image.wx")
    def test_getitem(self, mock_wx):
        """SchImage extracts sub-bitmaps by index."""
        from pytigon_gui.guilib.image import SchImage

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.ret_code = 200
        mock_response.ptr.return_value = b"\x00" * 100
        mock_http.get.return_value = mock_response
        mock_wx.GetApp.return_value.http = mock_http

        mock_bmp = MagicMock()
        mock_sub = MagicMock()
        mock_bmp.GetSubBitmap.return_value = mock_sub
        mock_wx.Bitmap.return_value = mock_bmp
        mock_wx.Image.return_value = MagicMock()
        mock_wx.Rect.return_value = (0, 0, 20, 20)

        img = SchImage("http://example.com/sprite.png", (20, 20))
        result = img[0]
        assert result is mock_sub
