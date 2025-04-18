"""This module extends pytigon_lib.html module of additional class designed to implement widgets in the form."""

from urllib.parse import unquote
from base64 import b64decode

from pytigon_lib.schhtml.tags.table_tags import TableTag  # , TdTag
from pytigon_lib.schhtml.basehtmltags import (
    BaseHtmlElemParser,
    register_tag_map,
    register_tag_preprocess_map,
)
from pytigon_lib.schhtml.htmltools import superstrip
from pytigon_lib.schparser.html_parsers import Td
from pytigon_lib.schtools.tools import is_null
from pytigon_lib.schtools.schhtmlgen import make_start_tag
import wx

import pytigon_gui.guictrl.ctrl as schctrl


_ATTRIBUTES = (
    "name",
    "href",
    "label",
    "target",
    "valuetype",
    "defaultvalue",
    "length",
    "maxlength",
    "readonly",
    "src",
    "param",
    "fields",
    "hidden",
    "checked",
    "style",
    "id",
    "onload",
)


class TreeList(object):
    def __init__(self):
        self.children = []

    def append_to_tree(self, elem):
        self.children.append(elem)

    def get_list(self):
        return self.children


class TreeUl(BaseHtmlElemParser):
    def __init__(self, parent, parser, tag, attrs):
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)
        self.child_tags += ["li"]
        self.children = []

    def close(self):
        self.parent.append_to_tree(["", self.children, self.attrs])

    def append_to_tree(self, elem):
        self.children.append(elem)

    def handle_starttag(
        self,
        parser,
        tag,
        attrs,
    ):
        if tag == "li":
            return TreeLi(self, parser, tag, attrs)
        else:
            return None


class TreeLi(BaseHtmlElemParser):
    def __init__(
        self,
        parent,
        parser,
        tag,
        attrs,
    ):
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)
        self.child = None

    def close(self):
        if self.child:
            self.child[0] = superstrip("".join(self.data))
            self.child[2] = self.attrs
            self.parent.append_to_tree(self.child)
        else:
            self.parent.append_to_tree([superstrip("".join(self.data)), [], self.attrs])

    def append_to_tree(self, elem):
        self.child = elem

    def handle_starttag(self, parser, tag, attrs):
        if tag == "ul":
            return TreeUl(self, parser, tag, attrs)
        elif tag == "a" or tag == "ctrl-button":
            self.attrs["href"] = attrs["href"]
        else:
            return None


class Data(BaseHtmlElemParser):
    def __init__(self, parent, parser, tag, attrs):
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)
        self.data = None

    def close(self):
        if self.data:
            self.parent.data2 = b64decode(self.data.encode("utf-8")).decode("utf-8")
        else:
            self.parent.data2 = ""

    def handle_data(self, data):
        if self.data:
            self.data += data.rstrip(" \n")
        else:
            self.data = data.rstrip(" \n")


class OptionTag(BaseHtmlElemParser):
    def __init__(self, parent, parser, tag, attrs):
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)

    def close(self):
        if self.data and len(self.data) > 0:
            data = "".join(self.data).replace("\n", "").replace("\r", "").strip()
            # if 'selected' in self.attrs:
            #    data = '!!' + data
            # if 'value' in self.attrs:
            #    value = self.attrs['value']
            #    data = value + ':' + data
            # else:
            #    data = ':' + data
            self.parent.tdata.append([Td(data, self.attrs)])


class CompositeChildTag(BaseHtmlElemParser):
    """Class handle ctrlcomposite tag"""

    def __init__(self, parent, parser, tag, attrs):
        """Constructor

        Args:
            parent - parent tag
            parser - html parser object
            tag - tag
            attrs - attrs
        """
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)
        self.composite_data = {}
        self.composite_data["tag"] = tag
        self.composite_data["attrs"] = attrs
        self.composite_data["data"] = None
        self.composite_data["children"] = []

    def close(self):
        if self.data:
            self.composite_data["data"] = self.data
        if type(self.parent) == CompositeChildTag:
            self.parent.composite_data["children"].append(self.composite_data)
        elif type(self.parent).__name__ == "CtrlTag":
            self.parent.data2.append(self.composite_data)

    def handle_starttag(
        self,
        parser,
        tag,
        attrs,
    ):
        return CompositeChildTag(self, parser, tag, attrs)


class CtrlTag(TableTag):
    """Class which handle all tags startings with 'ctrl-'"""

    def __init__(self, parent, parser, tag, attrs):
        """Constructor

        Args:
            parent - parent tag
            parser - html parser object
            tag - tag
            attrs - attrs
        """

        TableTag.__init__(self, parent, parser, tag, attrs)

        self.list = None
        self.child_tags += ["ul", "li", "data", "option", "div"]
        self.subtab = True
        self.kwargs = {}
        self.classObj = None
        self.data2 = None
        self.obj = None
        self.width_best = -1
        self.width_min = -1
        self.width_max = -1
        self.tdata = []

        if self.parser.parse_only:
            return
        self._calc_relative_size()

        if self.tag == "ctrl-checkbox":
            pass

        if self.tag == "ctrl-composite":
            self.data2 = []

    def append_to_tree(self, elem):
        if not self.list:
            self.list = TreeList()
        self.list.append_to_tree(elem)

    def _calc_relative_size(self):
        if "width" in self.attrs:
            (width, height2) = self.get_parent_window().GetSize()
            if width == 1 and height2 == 1:
                (width, height2) = (
                    self.get_parent_window().GetParent().GetParent().GetSize()
                )
            if self.parser.dc.width > 0 and self.parser.dc.width < width:
                width = self.parser.dc.width
            m = self._get_parent_pseudo_margins()
            width = (width - m[0]) - m[1]
            self.width = self._norm_sizes([self.attrs["width"]], width)[0]

        if "height" in self.attrs:
            (width2, height) = self.get_parent_window().GetSize()
            if width2 == 1 and height == 1:
                (width2, height) = (
                    self.get_parent_window().GetParent().GetParent().GetSize()
                )

            m = self._get_parent_pseudo_margins()
            height = (height - m[2]) - m[3] - 3
            # if False:
            #    if '99.9%' in self.attrs['height']:
            #        height -= wx.Button.GetDefaultSize()[1]
            #    if '99.8%' in self.attrs['height']:
            #        height += m[2]+m[3]
            #    if '99.7%' in self.attrs['height']:
            #        height += m[2]+m[3]-wx.Button.GetDefaultSize()[1]
            # if '100%' in self.attrs['height']:
            #    if self.parent and hasattr(self.parent,'y'):
            #        height -= self.parent.y - +m[3]
            #    else:
            #        height += m[3]

            self.height = self._norm_sizes([self.attrs["height"]], height)[0]
            # if self.attrs["height"].strip() == "100%":
            #    self.height -= self.get_context()["top"]

    def get_context(self):
        if self.parent and hasattr(self.parent, "y"):
            _y = self.parent.y + 3
        else:
            _y = 1

        context = {
            "button_size_dx": wx.Button.GetDefaultSize()[0] + 14,
            "button_size_dy": wx.Button.GetDefaultSize()[1] + 14,
            "top": _y,
        }
        return context

    def handle_data(self, data):
        if self.tag == "ctrl-checkbox":
            pass
        return BaseHtmlElemParser.handle_data(self, data)

    def handle_starttag(self, parser, tag, attrs):
        if self.tag == "ctrl-checkbox":
            pass

        if self.tag == "ctrl-composite":
            return CompositeChildTag(self, parser, tag, attrs)

        if tag[:3] + "*" in self.child_tags:
            return self.class_from_tag_name(tag[:3] + "*")(self, parser, tag, attrs)
        elif tag == "ul":
            return TreeUl(self, parser, tag, attrs)
        elif tag == "li":
            return TreeLi(self, parser, tag, attrs)
        elif tag == "data":
            return Data(self, parser, tag, attrs)
        elif tag == "option":
            return OptionTag(self, parser, tag, attrs)
        elif tag in self.child_tags:
            o = self.class_from_tag_name(tag)
            if o:
                return o(self, parser, tag, attrs)
            else:
                return None
        else:
            return None

    def calc_col_sizes(self):
        sizes = self.calc_width()
        if sizes[0] >= 0:
            self.width = sizes[0] + self.extra_space[0] + self.extra_space[1]
        else:
            self.width = 400

    def get_height(self):
        height = self.calc_height()
        if height >= 0:
            self.height = height + self.extra_space[2] + self.extra_space[3]
        else:
            self.height = 200
        return self.height

    def calc_width(self):
        d = self.extra_space[0] + self.extra_space[1]
        if self.width < 0:
            if self.obj:
                (self.width_best, self.height_best) = self.obj.GetBestSize()
                (self.width_min, height_min) = self.obj.GetMinSize()
                (self.width_max, height_max) = self.obj.GetMaxSize()
                return (self.width_best + d, self.width_min + d, self.width_max + d)
            else:
                return (d, d, d)
        else:
            return (self.width, self.width, self.width)

    def calc_height(self):
        height = -1
        if self.height >= 0:
            return self.height
        if self.obj:
            (self.width_best, self.height_best) = self.obj.GetBestSize()
        else:
            self.height_best = 30
        self.height = self.height_best + self.extra_space[2] + self.extra_space[3]
        return self.height

    def _append_to_tdata(self):
        if len(self.tr_list) > 0:
            for tr in self.tr_list:
                row = []
                for td in tr:
                    td_obj = Td(td.to_txt(), td.attrs, td.to_obj_tab())
                    row.append(td_obj)
                self.tdata.append(row)

    def close(self):
        self._append_to_tdata()
        if self.parser.parse_only:
            if hasattr(self.parser, "register_tdata"):
                self.parser.register_tdata(self.tdata, self.tag, self.attrs)
        else:
            self.handle_ctrl(self.tag)
        return TableTag.close(self)

    def render(self, dc):
        if dc.rec:
            if self.obj:
                self.obj.SetSize(
                    int(dc.x + self.extra_space[0]),
                    int(dc.y + self.extra_space[2]),
                    int((self.width - self.extra_space[0]) - self.extra_space[1]),
                    int((self.height - self.extra_space[2]) - self.extra_space[3]),
                )
                x2 = self.obj.GetSize()
        return (self.height, False)

    def draw_atom(self, dc, style, x, y, dx, dy):
        dc2 = dc.subdc(x, y, self.width, self.height)
        cont = True
        while cont:
            (dy, cont) = self.render(dc2)
            dc2.y += dy

    def get_parent_window(self):
        return self.parser.get_parent_window()

    def handle_ctrl(self, tag):
        value = None
        width = -1
        height = -1
        if "name" in self.attrs:
            name_reg = is_null(self.attrs["name"], "")
            parent = self.parent
            while parent:
                if hasattr(parent, "reg_field"):
                    name_reg = parent.reg_field(self.attrs["name"])
                    break
                parent = parent.parent
            name = name_reg
        else:
            name = tag[4:]
        self.attrs["name"] = name
        parent = self.get_parent_window()
        if parent:
            gparent = parent.GetParent()
            tmp = name
            i = 1
            while gparent.test_ctrl(tmp):
                tmp = name + "__" + str(i)
                i += 1
            name = tmp
        for atrybut in _ATTRIBUTES:
            if atrybut in self.attrs:
                if self.attrs[atrybut] == None:
                    self.kwargs[atrybut] = ""
                else:
                    self.kwargs[atrybut] = self.attrs[atrybut]

        valuetype = "data"
        if "valuetype" in self.attrs:
            if self.attrs["valuetype"] == "ref":
                valuetype = "ref"
            if self.attrs["valuetype"] == "str":
                valuetype = "str"
        if "value" in self.attrs:
            if valuetype == "str":
                value = self.attrs["value"]
                value = unquote(value)
            else:
                try:
                    value = eval(self.attrs["value"])
                except:
                    print("Value error:", self.attrs["value"])
                    value = None
        else:
            value = None
        if "strvalue" in self.attrs:
            value = self.attrs["strvalue"]

        self.kwargs["size"] = wx.Size(
            int((self.width - self.extra_space[0]) - self.extra_space[1]),
            int((self.height - self.extra_space[2]) - self.extra_space[3]),
        )
        try:
            if tag.upper().startswith("CTRL-"):
                self.classObj = getattr(schctrl, tag[5:].upper())
            # elif tag.upper().startswith('CTRL'):
            #    self.classObj = getattr(schctrl, tag[4:].upper())
            elif tag.startswith("_"):
                self.classObj = getattr(schctrl, tag[1:].upper())
            else:
                self.classObj = getattr(schctrl, tag.upper())
        except:
            return True

        if len(self.tdata) > 0:
            self.kwargs["tdata"] = self.tdata
        self.kwargs["param"] = dict(self.attrs)
        self.kwargs["param"]["table_lp"] = str(self.parser.table_lp)
        self.kwargs["param"]["tag"] = tag.lower()
        if self.data2 != None:
            self.kwargs["param"]["data"] = is_null(self.data2, "")
        else:
            self.kwargs["param"]["data"] = "".join(self.data)
        if self.list:
            l = self.list.get_list()
            self.kwargs["ldata"] = l

        obj = None
        if parent:
            gparent = parent.GetParent()

            obj = gparent.pop_ctrl(name)
            if obj:
                if parent.update_controls:
                    if obj and hasattr(obj, "process_refr_data"):
                        obj.process_refr_data(**self.kwargs)
                    elif not (hasattr(obj, "is_ctrl_block") and obj.is_ctrl_block()):
                        obj.SetValue(value)
                parent.append_ctrl(obj)
            else:
                obj = self.classObj(parent, **self.kwargs)
                if not obj:
                    print("ERROR:", self.classObj)
                obj.set_unique_name(name)
                if value != None and (valuetype == "data" or valuetype == "str"):
                    obj.SetValue(value)
                obj.after_create()
                parent.append_ctrl(obj)
            self.obj = obj


register_tag_map("ctr*", CtrlTag)


class ComponentTag(CtrlTag):
    def __init__(self, parent, parser, tag, attrs):
        super().__init__(parent, parser, tag, attrs)
        self.data.append(make_start_tag(attrs["_tag"], attrs))
        self.count = 1
        self._close_tag = None

    def close(self):
        # self.count -= 1
        # if self.count < 0:

        if "window-width" in self.attrs:
            self.attrs["width"] = self.attrs["window-width"]

        if "window-height" in self.attrs:
            self.attrs["height"] = self.attrs["window-height"]

        return super().close()

    def handle_starttag(
        self,
        parser,
        tag,
        attrs,
    ):
        if "_tag" in attrs:
            tag2 = attrs["_tag"]
        else:
            tag2 = tag
        self.data.append(make_start_tag(tag2, attrs))
        if not self._close_tag:
            self._close_tag = self.close_tag
        self.count += 1
        return self

    def handle_endtag(self, tag):
        self.data.append("</" + tag + ">")
        self.count -= 1
        if self.count == 0:
            if self._close_tag:
                self.close_tag = self._close_tag
            return super().handle_endtag(tag)
        else:
            return self


register_tag_map("_component", ComponentTag)


def table_to_ctrltab(parent, attrs):
    if "class" in attrs:
        if "tabsort" in attrs["class"]:
            attrs["minheight"] = "60px"
            return ("ctrl-table", attrs)
        if "listctrl" in attrs["class"]:
            return ("ctrl-list", attrs)
    return ("table", attrs)


register_tag_preprocess_map("table", table_to_ctrltab)


SCHTYPE_MAP = {
    "FloatField": "float",
    "IntegerField": "num",
    "DecimalField": "amount",
    "TimeField": "time",
    "DateTimeField": "datetimepicker",
}


def input_to_ctrltab(parent, attrs):
    global SCHTYPE_MAP
    attrs_ret = {}
    ret = "text"
    upload = False
    if "type" in attrs:
        type = attrs["type"]
    else:
        type = "text"
    if "schtype" in attrs:
        schtype = attrs["schtype"]
    else:
        schtype = "text"
    if "class" in attrs:
        classname = attrs["class"]
    else:
        classname = "text"
    if schtype in SCHTYPE_MAP:
        ret = SCHTYPE_MAP[schtype]
    elif type == "text":
        if classname == "dateinput":
            ret = "datepicker"
        elif classname == "datetimeinput":
            ret = "datetimepicker"
        else:
            ret = "text"
    elif type == "button":
        ret = "button"
    elif type == "email":
        ret = "masktext"
        attrs_ret = {"src": "!EMAIL", "width": "250", "valuetype": "str"}
        if "value" in attrs:
            attrs_ret["value"] = attrs["value"]
    elif type == "hidden":
        ret = "text"
        attrs_ret = {"hidden": "1", "width": "0", "height": "0"}
    elif type == "password":
        ret = "password"
    elif type == "radio":
        ret = "radiobutton"
        if "checked" in attrs:
            attrs_ret["checked"] = "1"
        if "value" in attrs:
            attrs_ret["value"] = attrs["value"]
            attrs_ret["valuetype"] = "str"
    elif type == "checkbox":
        ret = "checkbox"
        if "checked" in attrs:
            attrs_ret["checked"] = "1"
        if "value" in attrs:
            attrs_ret["value"] = attrs["value"]
            attrs_ret["valuetype"] = "str"
    elif type == "file":
        ret = "filebrowsebutton"
        upload = True
    elif type == "submit":
        ret = "button"
        if "target" in attrs:
            target = attrs["target"]
        else:
            target = "_parent_refr"
        attrs_ret = {
            "defaultvalue": "1",
            "param": "post",
            "target": target,
            "id": "wx.ID_OK",
        }
        href = "."
        fields = None
        p = parent
        while p:
            if hasattr(p, "gethref"):
                href = p.gethref()
                fields = p.get_fields()
                if p.get_upload():
                    attrs_ret["valuetype"] = "upload"
                break
            p = p.parent
        if href == None:
            href = ""
        attrs_ret["href"] = href
        if fields:
            attrs_ret["fields"] = fields
    if "size" in attrs and type in ("text", "email"):
        width_text = 10 * int(is_null(attrs["size"], 20))
        if width_text > 400:
            width_text = 8 * int(is_null(attrs["size"], 20))
        if width_text > 480:
            width_text = 480
        attrs_ret["width"] = str(width_text)
    if "maxlength" in attrs and type in ("text",):
        attrs_ret["maxlength"] = str(is_null(attrs["maxlength"], "80"))
    elif "max_length" in attrs and type in ("text",):
        attrs_ret["maxlength"] = str(is_null(attrs["max_length"], "80"))
    else:
        if "size" in attrs:
            attrs_ret["maxlength"] = str(int(is_null(attrs["size"], "80")))
    if "value" in attrs and type in ("text", "hidden", "checkbox"):
        attrs_ret["value"] = is_null(attrs["value"], "")
        attrs_ret["valuetype"] = "str"
    if "value" in attrs and type in ("button", "submit"):
        attrs_ret["label"] = is_null(attrs["value"], "")
    if "title" in attrs and type in "checkbox":
        attrs_ret["label"] = is_null(attrs["title"], "")
    if "name" in attrs:
        p = parent
        while p:
            if p.form_obj:
                if upload:
                    p.form_obj.set_upload(upload)
                break
            p = p.parent
        attrs_ret["name"] = attrs["name"]
        if ret == "text":
            if "date_" in attrs["name"]:
                ret = "datepicker"
    for attr in attrs:
        if not attr in attrs_ret and attr != "value":
            attrs_ret[attr] = attrs[attr]
    return ("ctrl-" + ret, attrs_ret)


register_tag_preprocess_map("input", input_to_ctrltab)


def textarea_to_ctrltab(parent, attrs):
    attrs_ret = {}
    if "cols" in attrs:
        attrs_ret["cols"] = attrs["cols"]
    if "rows" in attrs:
        attrs_ret["rows"] = attrs["rows"]
    if "src" in attrs:
        attrs_ret["src"] = attrs["src"]
    if "name" in attrs:
        attrs_ret["name"] = attrs["name"]
    return ("ctrl-textarea", attrs_ret)


register_tag_preprocess_map("textarea", textarea_to_ctrltab)


def select_to_ctrltab(parent, attrs):
    return ("ctrl-select", attrs)


register_tag_preprocess_map("select", select_to_ctrltab)


def a_to_button(parent, attrs):
    if "class" in attrs:
        if (
            "popup" in attrs["class"]
            or "button" in attrs["class"]
            or "btn" in attrs["class"]
            or "schbtn" in attrs["class"]
        ):
            if "schbtn" in attrs["class"]:
                try:
                    if parent.parent.parent.tag == "ctrl-table":
                        return ("ctrl-button", attrs)
                except:
                    return ("a", attrs)
            else:
                try:
                    if parent.parent.parent.tag == "ctrl-table":
                        return ("a", attrs)
                except:
                    pass
                return ("ctrl-button", attrs)
    return ("a", attrs)


register_tag_preprocess_map("a", a_to_button)


HIDDEN_DIVS = [
    "ajax-region",
    "td_information",
    "td_action",
]


def div_convert(parent, attrs):
    if "class" in attrs:
        if "popup" in attrs["class"]:
            return ("div", attrs)
        if "form-group" in attrs["class"]:
            return ("tr", attrs)
        if "controls" in attrs["class"]:
            return ("td", attrs)
        if "tree" in attrs["class"]:
            return ("ctrl-tree", attrs)
        if "select2" in attrs["class"]:
            return ("ctrl-composite", attrs)
        if "checkbox" in attrs["class"]:
            obj = parent.parent.handle_starttag(parent.parser, "th", {})
            if obj:
                obj.handle_endtag("th")
            return ("th", attrs)
        for div in HIDDEN_DIVS:
            if div in attrs["class"]:
                return ("none", attrs)
    return ("div", attrs)


register_tag_preprocess_map("div", div_convert)


def label_to_th(parent, attrs):
    return ("th", attrs)


register_tag_preprocess_map("label", label_to_th)


def error_span_to_error(parent, attrs):
    if "class" in attrs and attrs["class"] == "help-block":
        return ("ctrl-errorlist", attrs)
    else:
        return ("span", attrs)


register_tag_preprocess_map("span", error_span_to_error)


def error_p_to_error(parent, attrs):
    if "class" in attrs and attrs["class"] == "help-block":
        return ("comment", attrs)
    else:
        return ("p", attrs)


register_tag_preprocess_map("p", error_p_to_error)


def ul_convert(parent, attrs):
    if "class" in attrs:
        if "root" in attrs["class"]:
            return ("ldata", attrs)
        if attrs["class"] == "errorlist":
            return ("ctrl-errorlist", attrs)
    return ("ul", attrs)


register_tag_preprocess_map("ul", ul_convert)


def component_convert(parent, attrs):
    return ("_component", attrs)


register_tag_preprocess_map("*-*", component_convert, "ctr*")
