"""Module contains helper classes and functions for operate with images"""

import io
from io import BytesIO
from PIL import Image
from wx.svg import SVGimage

import wx

_ = wx.GetTranslation


SIZE_DEFAULT = -1
SIZE_SMALL = 0
SIZE_MEDIUM = 1
SIZE_LARGE = 2


# def get_app_icon():
#    icon = wx.EmptyIcon()
#    b = wx.ArtProvider.GetBitmap(wx.ART_FRAME_ICON, wx.ART_TOOLBAR, (32, 32))
#    icon.CopyFromBitmap(b)
#    return icon


def bitmap_to_pil(bitmap):
    """Convert wx.Bitmap object to PIL bitmap"""
    return image_to_pil(bitmap_to_image(bitmap))


def bitmap_to_image(bitmap):
    """Convert wx.Bitmap object to wx.Image object"""
    return wx.ImageFromBitmap(bitmap)


def pil_to_bitmap(pil):
    """Convert PIL bitmap to wx.Bitmap"""
    return image_to_bitmap(pil_to_image(pil))


def pil_to_image(pil, alpha=True):
    """Convert PIL bitmap to wx.Image"""
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
    """Convert wx.Image to PIL image"""
    pil = Image.new("RGB", (image.GetWidth(), image.GetHeight()))
    pil.fromstring(image.GetData())
    return pil


def image_to_bitmap(image):
    """Convert wx.Image to wx.Bitmap"""
    return image.ConvertToBitmap()


def bitmap_from_art_id(art_id, size):
    """Get bitmap from ArtProvider

    Args:
        art_id - Bitmap id in ArtProvider
        size
    """
    return wx.ArtProvider.GetBitmap(art_id, wx.ART_OTHER, size)


def bitmaps_from_art_id(art_id, size):
    """Get tuple with 2 bitmaps from ArtProvider, first is standard bitmap, second is first bitmap convertet
    to grayscale to emulate disabled elements

    Args:
        art_id - Bitmap id in ArtProvider
        size
    """
    bitmap = wx.ArtProvider.GetBitmap(art_id, wx.ART_OTHER, size)
    img = bitmap.ConvertToImage()
    bitmap_disabled = wx.Bitmap(img.ConvertToGreyscale().AdjustChannels(1, 1, 1, 0.3))
    return (bitmap, bitmap_disabled)


def bitmap_from_href(href, size_type=SIZE_DEFAULT):
    """Load resource and convert to bitmap

    Args:
        href - can be:
            - ArtProvider id - for example "wx.ART_COPY"
            - Font Awesome id, format: "fa://icon_name", for example "fa://bus"
            - path to image in local library, format: "png://image_name",
              for example: "png://mimetypes/text-x-script.png".
              Local library is located in path: "/appdata/media/size/"
            - path to image in web, for example: "http://www.pytigon.cloud/test.png"

        size
    """
    size_type2 = size_type
    if "?" in href:
        x = href.split("?")
        href2 = x[0]
        if "=" in x[1]:
            try:
                size_type2 = int(x[1].split("=")[1])
            except:
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
        bmp = wx.ArtProvider.GetBitmap(
            eval(href2), wx.ART_TOOLBAR, (icon_size, icon_size)
        )
    elif href.startswith("client://"):
        image = wx.Image(
            wx.GetApp().src_path
            + "/static/icons/%dx%d/" % (icon_size, icon_size)
            + href2[9:]
        )
        bmp = wx.Bitmap(image)
    elif href.startswith("png://"):
        image = wx.Image(
            wx.GetApp().src_path
            + "/static/icons/%dx%d/" % (icon_size, icon_size)
            + href2[6:]
        )
        bmp = wx.Bitmap(image)
    elif href.startswith("fa://"):
        if ".png" in href.lower():
            suffix = ""
        else:
            suffix = ".png"
        try:
            image = wx.Image(
                wx.GetApp().src_path
                + "/static/fonts/fork-awesome/fonts/%dx%d/" % (icon_size, icon_size)
                + href2[5:].replace("fa-", "")
                + suffix
            )
            image = image.AdjustChannels(1, 1, 1, 0.55)
            bmp = wx.Bitmap(image)
        except:
            print("Error, can't load image: ", href2)
            bmp = wx.Bitmap()
    elif href.startswith("data:image/svg+xml"):
        x = href.split(",", 1)
        svg_code = x[1]
        svg = SVGimage.CreateFromBytes(svg_code.encode("utf-8"))
        # _bmp = svg.ConvertToBitmap(scale=10, width=icon_size*10, height=icon_size*10)
        # image = wx.ImageFromBitmap(_bmp)
        # image = image.Scale(width=icon_size, height=icon_size, quality=wx.IMAGE_QUALITY_HIGH)
        # bmp = wx.Bitmap(image)
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
    """Extended version of wx.ArtProvider - class loads bitmaps from local library"""

    def __init__(self):
        wx.ArtProvider.__init__(self)
        self.tab_16 = {}
        self.tab_22 = {}
        self.tab_32 = {}

        ids = open(wx.GetApp().src_path + "/static/icons/ids.txt")
        for line in ids:
            l = line.replace("\n", "").split(",")
            if len(l) > 1:
                image_path = l[1]
                i = "wx.ART_" + l[0]
                try:
                    wxid = eval(i)
                    self.tab_16[wxid] = [image_path, None]
                    self.tab_22[wxid] = [image_path, None]
                    self.tab_32[wxid] = [image_path, None]
                except:
                    pass
        ids.close()

    def CreateBitmap(self, artid2, client, size):
        artid = artid2.encode("utf-8")
        if size != 16 and size != 22 and size != 32:
            size = 32
        path = None
        if size == 16:
            if artid in self.tab_16:
                if self.tab_16[artid][1]:
                    return self.tab_16[artid][1]
                path = "png://" + self.tab_16[artid][0] + "?size=0"
        elif size == 22:
            if artid in self.tab_22:
                if self.tab_22[artid][1]:
                    return self.tab_22[artid][1]
                path = "png://" + self.tab_22[artid][0] + "?size=1"
        else:
            if artid in self.tab_32:
                if self.tab_32[artid][1]:
                    return self.tab_32[artid][1]
                path = "png://" + self.tab_32[artid][0] + "?size=2"
        try:
            bitmap = bitmap_from_href(path)
        except:
            bitmap = None
        if bitmap:
            if size == 16:
                self.tab_16[artid][1] = bitmap
            elif size == 22:
                self.tab_22[artid][1] = bitmap
            else:
                self.tab_32[artid][1] = bitmap
            return bitmap
        else:
            return wx.NullBitmap


class SchImage:
    """Class which extract bitmaps from image with multiple images aranged one behind other.
    All partial bitmaps should be the same size. Between bitmaps should be a gap with a 1 pixel width.

    images = SchImage("http://wwww.page.com", (32,32))
    image1 = images[0]
    image2 = images[2]
    """

    def __init__(self, address, one_image_size=(20, 20)):
        self.one_image_size = one_image_size
        try:
            http = wx.GetApp().http
            response = http.get(self, address)
            if response.ret_code != 200:
                print("I can't load image from:", address)
                self.bmp = wx.ArtProvider.GetBitmap(
                    wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (32, 32)
                )
            else:
                str = response.ptr()
                stream = io.BytesIO(str)
                self.bmp = wx.Bitmap(wx.Image(stream))
        except:
            print(_("The exception while loading image from:"), address)
            self.bmp = wx.ArtProvider.GetBitmap(
                wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (32, 32)
            )

    def __getitem__(self, key):
        rect = wx.Rect(
            (self.one_image_size[0] + 1) * int(key),
            0,
            self.one_image_size[0],
            self.one_image_size[1],
        )
        try:
            ret = self.bmp.GetSubBitmap(rect)
        except:
            ret = wx.ArtProvider.GetBitmap(
                wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR, (32, 32)
            )
        return ret
