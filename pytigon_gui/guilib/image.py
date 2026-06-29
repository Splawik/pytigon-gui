"""Module contains helper classes and functions for image operations.

Provides conversion utilities between wx.Bitmap, wx.Image, and PIL images,
as well as functions to load bitmaps from ArtProviders, local files, fonts,
and remote HTTP sources.
"""

import io
import logging
from io import BytesIO
from PIL import Image
from wx.svg import SVGimage

import wx

_ = wx.GetTranslation
logger = logging.getLogger(__name__)

SIZE_DEFAULT = -1
SIZE_SMALL = 0
SIZE_MEDIUM = 1
SIZE_LARGE = 2

# Safe lookup mapping for wx.ART_* identifiers to avoid eval().
# Only includes constants verified to exist in the current wxPython version.
_WX_ART_MAP = {
    "wx.ART_ADD_BOOKMARK": wx.ART_ADD_BOOKMARK,
    "wx.ART_COPY": wx.ART_COPY,
    "wx.ART_CUT": wx.ART_CUT,
    "wx.ART_DELETE": wx.ART_DELETE,
    "wx.ART_FILE_OPEN": wx.ART_FILE_OPEN,
    "wx.ART_FILE_SAVE": wx.ART_FILE_SAVE,
    "wx.ART_FILE_SAVE_AS": wx.ART_FILE_SAVE_AS,
    "wx.ART_FIND": wx.ART_FIND,
    "wx.ART_FIND_AND_REPLACE": wx.ART_FIND_AND_REPLACE,
    "wx.ART_FRAME_ICON": wx.ART_FRAME_ICON,
    "wx.ART_GO_BACK": wx.ART_GO_BACK,
    "wx.ART_GO_DOWN": wx.ART_GO_DOWN,
    "wx.ART_GO_FORWARD": wx.ART_GO_FORWARD,
    "wx.ART_GO_HOME": wx.ART_GO_HOME,
    "wx.ART_GO_TO_PARENT": wx.ART_GO_TO_PARENT,
    "wx.ART_GO_UP": wx.ART_GO_UP,
    "wx.ART_HELP": wx.ART_HELP,
    "wx.ART_MISSING_IMAGE": wx.ART_MISSING_IMAGE,
    "wx.ART_NEW": wx.ART_NEW,
    "wx.ART_PASTE": wx.ART_PASTE,
    "wx.ART_PRINT": wx.ART_PRINT,
    "wx.ART_QUIT": wx.ART_QUIT,
    "wx.ART_REDO": wx.ART_REDO,
    "wx.ART_TIP": wx.ART_TIP,
    "wx.ART_UNDO": wx.ART_UNDO,
}


def _resolve_art_id(art_id_str):
    """Safely resolve a wx.ART_* string to its wxPython constant.

    Args:
        art_id_str: String like 'wx.ART_COPY'.

    Returns:
        wxPython art id constant, or None if not found.
    """
    if art_id_str in _WX_ART_MAP:
        return _WX_ART_MAP[art_id_str]
    try:
        return getattr(wx, art_id_str.split(".")[1], None)
    except (IndexError, AttributeError):
        return None


def bitmap_to_pil(bitmap):
    """Convert wx.Bitmap object to PIL Image."""
    return image_to_pil(bitmap_to_image(bitmap))


def bitmap_to_image(bitmap):
    """Convert wx.Bitmap object to wx.Image object."""
    return wx.ImageFromBitmap(bitmap)


def pil_to_bitmap(pil):
    """Convert PIL Image to wx.Bitmap."""
    return image_to_bitmap(pil_to_image(pil))


def pil_to_image(pil, alpha=True):
    """Convert PIL Image to wx.Image.

    Args:
        pil: PIL Image object.
        alpha: If True, preserve alpha channel.

    Returns:
        wx.Image object.
    """
    if alpha:
        image = wx.Image(*pil.size)
        image.SetData(pil.convert("RGB").tobytes())
        image.SetAlphaBuffer(pil.convert("RGBA").tobytes()[3::4])
    else:
        image = wx.Image(pil.size[0], pil.size[1])
        new_image = pil.convert("RGB")
        data = new_image.tobytes()
        image.SetData(data)
    return image


def image_to_pil(image):
    """Convert wx.Image to PIL Image."""
    pil = Image.new("RGB", (image.GetWidth(), image.GetHeight()))
    pil.frombytes(image.GetData())
    return pil


def image_to_bitmap(image):
    """Convert wx.Image to wx.Bitmap."""
    return image.ConvertToBitmap()


def bitmap_from_art_id(art_id, size):
    """Get bitmap from ArtProvider.

    Args:
        art_id: Bitmap id in ArtProvider.
        size: wx.Size or (width, height) tuple.

    Returns:
        wx.Bitmap.
    """
    return wx.ArtProvider.GetBitmap(art_id, wx.ART_OTHER, size)


def bitmaps_from_art_id(art_id, size):
    """Get a tuple of two bitmaps from ArtProvider.

    The first is the standard bitmap, the second is the same bitmap
    converted to grayscale to emulate a disabled state.

    Args:
        art_id: Bitmap id in ArtProvider.
        size: wx.Size or (width, height) tuple.

    Returns:
        (bitmap, bitmap_disabled) tuple.
    """
    bitmap = wx.ArtProvider.GetBitmap(art_id, wx.ART_OTHER, size)
    img = bitmap.ConvertToImage()
    bitmap_disabled = wx.Bitmap(img.ConvertToGreyscale().AdjustChannels(1, 1, 1, 0.3))
    return (bitmap, bitmap_disabled)


def bitmap_from_href(href, size_type=SIZE_DEFAULT):
    """Load a resource and convert it to a wx.Bitmap.

    Args:
        href: Resource identifier. Supported formats:
            - ArtProvider id, e.g. 'wx.ART_COPY'
            - Font Awesome id, e.g. 'fa://icon_name' or 'fa://bus'
            - Local library image, e.g. 'png://image_name.png'
            - Client-side image, e.g. 'client://image_name.png'
            - Inline SVG data, e.g. 'data:image/svg+xml,...'
            - Remote HTTP/HTTPS URL, e.g. 'http://www.pytigon.cloud/test.png'
        size_type: One of SIZE_DEFAULT, SIZE_SMALL, SIZE_MEDIUM, SIZE_LARGE.

    Returns:
        wx.Bitmap. If the resource cannot be loaded, ART_MISSING_IMAGE is
        returned.
    """
    size_type2 = size_type
    if "?" in href:
        x = href.split("?")
        href2 = x[0]
        if "=" in x[1]:
            try:
                size_type2 = int(x[1].split("=")[1])
            except (ValueError, IndexError):
                size_type2 = 1
    else:
        href2 = href

    if size_type2 == SIZE_SMALL:
        icon_size = 16
    elif size_type2 == SIZE_MEDIUM:
        icon_size = 22
    else:
        icon_size = 32

    if href2[:3] == "wx.":
        if (art_id := _resolve_art_id(href2)) is not None:
            bmp = wx.ArtProvider.GetBitmap(
                art_id, wx.ART_TOOLBAR, (icon_size, icon_size)
            )
        else:
            bmp = wx.ArtProvider.GetBitmap(
                wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (icon_size, icon_size)
            )
    elif href.startswith("client://"):
        image = wx.Image(
            str(wx.GetApp().src_path)
            + f"/static/icons/{icon_size}x{icon_size}/"
            + href2[9:]
        )
        bmp = wx.Bitmap(image)
    elif href.startswith("png://"):
        image = wx.Image(
            str(wx.GetApp().src_path)
            + f"/static/icons/{icon_size}x{icon_size}/"
            + href2[6:]
        )
        bmp = wx.Bitmap(image)
    elif href.startswith("fa://"):
        suffix = "" if ".png" in href.lower() else ".png"
        try:
            image = wx.Image(
                str(wx.GetApp().src_path)
                + f"/static/fonts/fork-awesome/fonts/{icon_size}x{icon_size}/"
                + href2[5:].replace("fa-", "")
                + suffix
            )
            image = image.AdjustChannels(1, 1, 1, 0.55)
            bmp = wx.Bitmap(image)
        except Exception:
            logger.warning("Cannot load image: %s", href2)
            bmp = wx.Bitmap()
    elif href.startswith("data:image/svg+xml"):
        x = href.split(",", 1)
        svg_code = x[1]
        svg = SVGimage.CreateFromBytes(svg_code.encode("utf-8"))
        bmp = svg.ConvertToBitmap(width=icon_size, height=icon_size)
    else:
        if href.lower().startswith("http"):
            http = wx.GetApp().get_http(None)
            response = http.get(None, str(href))
            if response.ret_code != 404:
                s = response.ptr()
                stream = BytesIO(s)
                bmp = wx.Bitmap(wx.Image(stream))
            else:
                bmp = wx.ArtProvider.GetBitmap(
                    wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (32, 32)
                )
        else:
            bmp = wx.ArtProvider.GetBitmap(
                wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (32, 32)
            )
    return bmp


class ArtProviderFromIcon(wx.ArtProvider):
    """Extended ArtProvider that loads bitmaps from a local icon library.

    Reads icon identifiers from static/icons/ids.txt and caches bitmaps
    at 16px, 22px, and 32px sizes.
    """

    def __init__(self):
        wx.ArtProvider.__init__(self)
        self.tab_16 = {}
        self.tab_22 = {}
        self.tab_32 = {}

        ids_path = str(wx.GetApp().src_path) + "/static/icons/ids.txt"
        try:
            with open(ids_path) as ids:
                for line in ids:
                    line = line.strip()
                    if not line:
                        continue
                    l = line.split(",")
                    if len(l) > 1:
                        image_path = l[1]
                        art_key = "wx.ART_" + l[0]
                        if (art_id := _resolve_art_id(art_key)) is not None:
                            self.tab_16[art_id] = [image_path, None]
                            self.tab_22[art_id] = [image_path, None]
                            self.tab_32[art_id] = [image_path, None]
        except FileNotFoundError:
            logger.warning("Icon id file not found: %s", ids_path)
        except Exception:
            logger.exception("Error loading icon id file: %s", ids_path)

    def CreateBitmap(self, artid2, client, size):
        """Create and cache a bitmap for the given art id and size.

        Args:
            artid2: Art id (string).
            client: Client identifier (unused).
            size: Requested size in pixels.

        Returns:
            wx.Bitmap or wx.NullBitmap.
        """
        artid = artid2.encode("utf-8")
        if size not in (16, 22, 32):
            size = 32
        path = None
        cached_table = None

        if size == 16:
            cached_table = self.tab_16
            if artid in self.tab_16:
                if self.tab_16[artid][1]:
                    return self.tab_16[artid][1]
                path = "png://" + self.tab_16[artid][0] + "?size=0"
        elif size == 22:
            cached_table = self.tab_22
            if artid in self.tab_22:
                if self.tab_22[artid][1]:
                    return self.tab_22[artid][1]
                path = "png://" + self.tab_22[artid][0] + "?size=1"
        else:
            cached_table = self.tab_32
            if artid in self.tab_32:
                if self.tab_32[artid][1]:
                    return self.tab_32[artid][1]
                path = "png://" + self.tab_32[artid][0] + "?size=2"

        if path is None:
            return wx.NullBitmap

        try:
            bitmap = bitmap_from_href(path)
        except Exception:
            bitmap = None

        if bitmap and cached_table and artid in cached_table:
            cached_table[artid][1] = bitmap
            return bitmap
        return wx.NullBitmap


class SchImage:
    """Extract individual bitmaps from a sprite sheet image.

    All partial bitmaps should be the same size. Between bitmaps there
    should be a gap of 1 pixel width.

    Usage::

        images = SchImage("http://www.page.com", (32, 32))
        image1 = images[0]
        image2 = images[2]
    """

    def __init__(self, address, one_image_size=(20, 20)):
        """Initialize and load the sprite sheet.

        Args:
            address: URL of the sprite sheet image.
            one_image_size: (width, height) of each sub-image.
        """
        self.one_image_size = one_image_size
        try:
            http = wx.GetApp().http
            response = http.get(self, address)
            if response.ret_code != 200:
                logger.warning("Cannot load image from: %s", address)
                self.bmp = wx.ArtProvider.GetBitmap(
                    wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (32, 32)
                )
            else:
                data = response.ptr()
                stream = io.BytesIO(data)
                self.bmp = wx.Bitmap(wx.Image(stream))
        except Exception:
            logger.exception("Exception while loading image from: %s", address)
            self.bmp = wx.ArtProvider.GetBitmap(
                wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (32, 32)
            )

    def __getitem__(self, key):
        """Extract the sub-bitmap at the given index.

        Args:
            key: Integer index of the sub-image in the sprite sheet.

        Returns:
            wx.Bitmap of the sub-image, or ART_MISSING_IMAGE on failure.
        """
        rect = wx.Rect(
            (self.one_image_size[0] + 1) * int(key),
            0,
            self.one_image_size[0],
            self.one_image_size[1],
        )
        try:
            return self.bmp.GetSubBitmap(rect)
        except Exception:
            return wx.ArtProvider.GetBitmap(
                wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (32, 32)
            )
