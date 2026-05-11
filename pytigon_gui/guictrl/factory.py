"""
Factory and dispatch functions for the SchForm GUI framework.

These UPPERCASE functions serve as the primary interface for
creating widget instances from HTML tag handlers (tag.py).
They dispatch to the appropriate widget class based on tag
attributes, parameters, and configuration.

Functions:
    SELECT, BUTTON, TEXTAREA, SELECT2, COMPOSITE, COMPONENT
"""

import wx

from pytigon_gui.guictrl.basectrl import SchBaseCtrl
from pytigon_gui.guictrl.button.base import (
    SIMPLE_BUTTON,
    BITMAPBUTTON,
    PLATEBUTTON,
    GENBITMAPBUTTON,
    GENBITMAPTEXTBUTTON,
    GENBITMAPBUTTONTXT,
    GENBITMAPBUTTONTXT_SMALL,
    NOBG_BUTTON,
    NOBG_BUTTON_TXT,
    CLOSEBUTTON,
    MENUBUTTON,
    MENUTOOLBARBUTTON,
)
from pytigon_gui.guictrl.input.text import STYLEDTEXT, AUTOCOMPLETE
from pytigon_gui.guictrl.input.choice import CHECKLISTBOX
from pytigon_gui.guictrl.input.combo import DBCHOICE
from pytigon_gui.guictrl.panels import CompositePanel
from pytigon_gui.guictrl.popup.select2 import Select2Base
from pytigon_gui.guilib.image import bitmap_from_href
from pytigon_lib.schtools.tools import is_null


def SELECT(parent, **kwds):
    """Dispatch function for ctrlselect tag.

    Routes to the appropriate widget based on parameters:
    - HeavySelect2Field / ModelSelect2Field types: SELECT2
    - Single selection (size=1): DBCHOICE (readonly combo)
    - Multi selection (size>1 or 'multiple' param): CHECKLISTBOX

    Args:
        parent: Parent window.
        **kwds: Tag keyword arguments including 'param' dict.

    Returns:
        A wx control instance appropriate for the selection mode.
    """
    size = 1
    multiple = False

    if "param" in kwds:
        param = kwds["param"]
        if "multiple" in param:
            multiple = True
        if "size" in param:
            size = int(param["size"])
        if multiple and size == 1:
            size = 10

        if "schtype" in param and param["schtype"] in (
            "HeavySelect2Field",
            "HeavySelect2MultipleField",
            "ModelSelect2Field",
            "ModelSelect2MultipleField",
        ):
            kwds["param"]["data"] = [kwds["param"]]
            kwds["param"]["data"][0]["attrs"] = kwds["param"]
            return SELECT2(parent, **kwds)

    if size == 1:
        kwds["readonly"] = True
        return DBCHOICE(parent, **kwds)
    else:
        kwds["length"] = size
        return CHECKLISTBOX(parent, **kwds)


def BUTTON(parent, **kwds):
    """Dispatch function for ctrlbutton tag.

    Routes to the appropriate button class based on the
    'btn-class' parameter or the presence of a 'src' attribute
    (bitmap vs text button).

    Supported btn-class values:
        SIMPLE_BUTTON, BITMAPBUTTON, PLATEBUTTON,
        GENBITMAPBUTTON, GENBITMAPBUTTONTXT,
        GENBITMAPBUTTONTXT_SMALL, NOBG_BUTTON,
        NOBG_BUTTON_TXT, CLOSEBUTTON, MENUBUTTON,
        MENUTOOLBARBUTTON

    Args:
        parent: Parent window.
        **kwds: Tag keyword arguments including optional 'param'
            with 'btn-class' key, and optional 'src' for bitmap.

    Returns:
        A button control instance.
    """
    if "param" in kwds and "btn-class" in kwds["param"]:
        btn_class = kwds["param"]["btn-class"]
        class_map = {
            "SIMPLE_BUTTON": SIMPLE_BUTTON,
            "BITMAPBUTTON": BITMAPBUTTON,
            "PLATEBUTTON": PLATEBUTTON,
            "GENBITMAPBUTTON": GENBITMAPBUTTON,
            "GENBITMAPBUTTONTXT": GENBITMAPBUTTONTXT,
            "GENBITMAPBUTTONTXT_SMALL": GENBITMAPBUTTONTXT_SMALL,
            "NOBG_BUTTON": NOBG_BUTTON,
            "NOBG_BUTTON_TXT": NOBG_BUTTON_TXT,
            "CLOSEBUTTON": CLOSEBUTTON,
            "MENUBUTTON": MENUBUTTON,
            "MENUTOOLBARBUTTON": MENUTOOLBARBUTTON,
        }
        if btn_class in class_map:
            return class_map[btn_class](parent, **kwds)

    if "src" in kwds:
        return BITMAPBUTTON(parent, **kwds)
    else:
        return SIMPLE_BUTTON(parent, **kwds)


def TEXTAREA(parent, **kwds):
    """Dispatch function for ctrltextarea tag.

    Handles sizing from 'cols' and 'rows' attributes and
    routes to STYLEDTEXT or AUTOCOMPLETE based on the 'src'
    attribute (code languages get STYLEDTEXT, others get
    AUTOCOMPLETE for code completion).

    Args:
        parent: Parent window.
        **kwds: Tag keyword arguments with optional 'param',
            'cols', 'rows', 'src'.

    Returns:
        A STYLEDTEXT or AUTOCOMPLETE instance.
    """
    if "param" in kwds:
        if "data" in kwds["param"]:
            data = kwds["param"]["data"].replace("\r", "")
            if data.startswith("\n"):
                data = data[1:]
                kwds["param"]["data"] = data

    size = [-1, -1]

    if "param" in kwds and "width" not in kwds["param"]:
        if "cols" in kwds["param"]:
            width = 7 * int(is_null(kwds["param"]["cols"], "80"))
            if width > 480:
                width = 480
            kwds["param"]["width"] = str(width)
            size[0] = width
        else:
            kwds["param"]["width"] = "100%"
    if "param" in kwds and "height" not in kwds["param"]:
        if "rows" in kwds["param"]:
            size[1] = 14 + 14 * int(is_null(kwds["param"]["rows"], "3"))
            kwds["param"]["height"] = str(size[1])
        else:
            kwds["param"]["height"] = "100%"

    kwds["size"] = size

    kwds.pop("cols", None)
    kwds.pop("rows", None)

    if "src" in kwds:
        if kwds["src"] in ("c", "python", "html"):
            return STYLEDTEXT(parent, **kwds)
        else:
            return AUTOCOMPLETE(parent, **kwds)
    else:
        return STYLEDTEXT(parent, **kwds)


def _button_from_parm(parent, param):
    """Create a button from a composite parameter node.

    Used internally by SELECT2 to create action buttons
    alongside the Select2 control.

    Args:
        parent: Parent window.
        param: Parameter dict with 'children' and 'attrs'.

    Returns:
        A BUTTON instance or None.
    """
    if "children" in param and param["children"]:
        icon = param["children"][0]["attrs"]["class"]
        href = param["attrs"]["href"]
        button = BUTTON(parent, src="fa://" + icon + "?size=0", href=href)
        return button
    return None


def SELECT2(parent, **kwds):
    """Create a Select2 composite control with optional action buttons.

    Builds a CompositePanel containing a Select2Base control
    and up to two action buttons from the composite parameter data.

    Args:
        parent: Parent window.
        **kwds: Tag keyword arguments with 'param' containing
            'data' (list of parameter nodes).

    Returns:
        A CompositePanel containing the Select2 control and buttons.
    """
    data = kwds["param"]["data"]
    panel = CompositePanel(parent, size=(460, -1))
    ctrl = Select2Base(panel, **kwds)
    panel.set_main_ctrl(ctrl)

    # Build optional action buttons from composite data
    button1 = None
    button2 = None
    if (
        len(data) > 1
        and "children" in data[1]
        and data[1]["children"]
        and len(data[1]["children"]) > 0
    ):
        button1 = _button_from_parm(panel, param=data[1]["children"][0])
    if (
        len(data) > 1
        and "children" in data[1]
        and data[1]["children"]
        and len(data[1]["children"]) > 1
    ):
        button2 = _button_from_parm(panel, param=data[1]["children"][1])

    ctrl.init(button1, button2)

    # Shared callback for select2 and buttons
    def ret_ok(id, title):
        ctrl.set_value(id, title)
        wx.CallAfter(ctrl.SetFocus)

    ctrl.ret_ok = ret_ok
    if button1:
        button1.ret_ok = ret_ok
    if button2:
        button2.ret_ok = ret_ok

    # Layout: horizontal box with ctrl + buttons
    box = wx.BoxSizer(wx.HORIZONTAL)
    box.Add(ctrl, 0, wx.EXPAND)
    if button1:
        box.Add(button1)
    if button2:
        box.Add(button2)

    panel.SetSizer(box)
    panel.SetAutoLayout(True)
    panel.Fit()

    return panel


def COMPOSITE(parent, **kwds):
    """Dispatch function for ctrlcomposite tag.

    Looks up the widget class by the 'class' parameter (uppercased)
    in the global namespace and instantiates it.

    Args:
        parent: Parent window.
        **kwds: Tag keyword arguments with 'param' containing
            'class' key.

    Returns:
        An instance of the requested widget class.
    """
    cls_name = kwds["param"]["class"].upper()
    if cls_name in globals():
        return globals()[cls_name](parent, **kwds)
    return None


def COMPONENT(parent, **kwds):
    """Create a web component widget.

    Loads a web component via HTTP, replaces placeholder tokens,
    and renders it using the HTML2 viewer if available.

    Args:
        parent: Parent window.
        **kwds: Tag keyword arguments with 'param' containing
            'data' (component name).

    Returns:
        An HTML2 viewer instance or None if HTML2 is not available.
    """
    # HTML2 is dynamically set by plugins at runtime
    from pytigon_gui.guictrl import ctrl as schctrl

    http = wx.GetApp().get_http(parent)
    response = http.get(
        parent,
        wx.GetApp().make_href("/schsys/widget_web?browser_type=1"),
    )
    buf = response.str()

    colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE).GetAsString(
        flags=wx.C2S_HTML_SYNTAX
    )
    buf = buf.replace("<component>", kwds["param"]["data"]).replace("[[color]]", colour)

    if schctrl.HTML2:
        kwds["component"] = True
        obj = schctrl.HTML2(parent, **kwds)
        obj.load_str(buf, "http://127.0.0.2")
        return obj
    else:
        return None
