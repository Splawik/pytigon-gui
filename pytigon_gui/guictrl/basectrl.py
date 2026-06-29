"""Base control class for the SchForm GUI framework.

Defines SchBaseCtrl -- the mixin base class for all wxPython widgets
managed by the SchForm framework. Provides attribute initialization
from HTML tag kwargs, parent form navigation, data loading from server,
and keyboard event handling.

Also provides the handle_best_size decorator for auto-sizing widgets.
"""

import wx

from pytigon_lib.schhtml.htmlviewer import tdata_from_html

from urllib.parse import unquote
from pytigon_lib.schparser.html_parsers import TreeParser


# ---------------------------------------------------------------------------
# Helper: extract kwarg value with default
# ---------------------------------------------------------------------------


def _extract_kwarg(kwds, key, default=None):
    """Remove and return key from kwds, or return default if absent."""
    if key in kwds:
        val = kwds[key]
        del kwds[key]
        return val
    return default


# ---------------------------------------------------------------------------
# SchBaseCtrl
# ---------------------------------------------------------------------------


class SchBaseCtrl:
    """Base mixin class for all SchForm wxPython widgets.

    Provides:
    - Attribute initialization from HTML tag keyword arguments
    - Parent form/page navigation
    - Server data loading for tdata (table data) and ldata (list data)
    - Common keyboard handling (Escape, Tab)
    - Widget lifecycle: after_create signal, unique name management
    """

    def __init__(self, parent, kwds):
        """Initialize base control attributes.

        Args:
            parent: Parent wxPython window.
            kwds: Keyword argument dict parsed from HTML tag attributes.
        """
        self.unique_name = None
        self.init_base(kwds, parent)
        self.accept_focus = True
        self.acc_tab_bind = False
        form = self.get_parent_form()
        if form:
            form.signal_from_child(self, "__init__")

    def init_base(self, kwds, parent=None):
        """Initialize all control attributes from kwds.

        Extracts well-known attributes (href, label, id, target, value,
        valuetype, defaultvalue, length, maxlength, readonly, hidden,
        src, onload, tdata, ldata, data, param, style) from kwds
        and assigns them as instance attributes.

        Args:
            kwds: Keyword argument dict parsed from HTML tag attributes.
            parent: Optional parent window reference.
        """
        if parent:
            self.parent = parent

        self.ldatabuf = None

        self.tag = None
        if "param" in kwds and "tag" in kwds["param"]:
            self.tag = kwds["param"]["tag"]

        self.href = _extract_kwarg(kwds, "href", None)
        if self.href is None:
            self.href = ""

        self.label = _extract_kwarg(kwds, "label", None)
        self.nr_id = _extract_kwarg(kwds, "id", None)
        self.target = _extract_kwarg(kwds, "target", "_blank")
        self.value = _extract_kwarg(kwds, "value", None)
        self.valuetype = _extract_kwarg(kwds, "valuetype", "data")
        self.defaultvalue = _extract_kwarg(kwds, "defaultvalue", None)
        self.length = int(_extract_kwarg(kwds, "length", 0))
        self.maxlength = int(_extract_kwarg(kwds, "maxlength", 0))
        self.readonly = _extract_kwarg(kwds, "readonly", False)
        self.hidden = True if _extract_kwarg(kwds, "hidden", False) else False
        self.src = _extract_kwarg(kwds, "src", None)
        self.onload = _extract_kwarg(kwds, "onload", None)

        # tdata / tdatabuf: table data (already parsed) or lazily loaded
        self.tdata = _extract_kwarg(kwds, "tdata", None)
        self.tdatabuf = None
        if self.tdata is not None:
            self.tdatabuf = None

        # ldata: hierarchical list data (already parsed) or lazily loaded
        self.ldata = _extract_kwarg(kwds, "ldata", None)

        # data: URL-encoded string data
        raw_data = _extract_kwarg(kwds, "data", None)
        self.data = unquote(raw_data) if raw_data is not None else None

        self.param = _extract_kwarg(kwds, "param", None)
        self.style = _extract_kwarg(kwds, "style", None)

        # Invoke any registered ctrl_process hooks for this tag type
        ctrl_process = wx.GetApp().ctrl_process
        if self.tag in ctrl_process:
            for fun in ctrl_process[self.tag]:
                fun(self)

    def after_create(self):
        """Called immediately after the widget is fully constructed.

        Binds keyboard events, executes the 'onload' script (if any),
        calls the __ext_init__ hook if present, and signals the parent
        form that this child is ready.
        """
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down_base)
        if self.onload:
            d = {"wx": wx, "self": self}
            try:
                exec(self.onload, d)
            except Exception:
                pass

        if hasattr(self, "__ext_init__"):
            self.__ext_init__()

        self.get_parent_form().signal_from_child(self, "after_create")

    def CanAcceptFocus(self):
        """Return True if the control can accept keyboard focus."""
        if self.IsShown() and self.IsEnabled():
            return self.accept_focus
        return False

    def CanAcceptFocusFromKeyboard(self):
        """Return True if the control accepts focus from keyboard navigation."""
        return self.CanAcceptFocus()

    def set_unique_name(self, name):
        """Assign a unique name identifier to this control."""
        self.unique_name = name

    def get_unique_name(self):
        """Return the unique name identifier."""
        return self.unique_name

    def set_acc_key_tab(self, tab):
        """Register an accelerator table for this widget.

        Args:
            tab: List or tuple of accelerator elements. Each element has
                structure: (flag, keycode, callback function).

        Returns:
            Result from the parent's set_acc_key_tab method.
        """
        return self.GetParent().set_acc_key_tab(self, tab)

    def on_key_down_base(self, event):
        """Default key-down handler for Escape and Tab navigation.

        Args:
            event: wx.KeyEvent.
        """
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            wx.CallAfter(self.GetParent().cancel)
        elif event.GetKeyCode() == wx.WXK_TAB:
            if event.ShiftDown():
                self.GetParent().Navigate(self, True)
            else:
                self.GetParent().Navigate(self, False)
        else:
            event.Skip()

    def is_ctrl_block(self):
        """Return True if this control is a block-level element."""
        return self.GetParent().is_ctrl_block(self)

    def load_data_from_server(self, path):
        """Load raw binary data from a server URL.

        Args:
            path: URL path to fetch.

        Returns:
            Raw response data (bytes).
        """
        http = wx.GetApp().get_http(self.parent)
        response = http.get(self, str(path))
        return response.ptr()

    def load_string_from_server(self, path):
        """Load a text response from a server URL.

        Args:
            path: URL path to fetch.

        Returns:
            Response body as a string.
        """
        http = wx.GetApp().get_http(self.parent)
        response = http.get(self, str(path))
        return response.str()

    def refresh_tdata(self, html_src=None):
        """Refresh table data from the server or provided HTML source.

        Args:
            html_src: Optional HTML string containing table data.
                If None, loads from self.src.
        """
        if self.tdata is None and self.src:
            if html_src:
                tables = html_src
            else:
                tables = self.load_data_from_server(self.src).decode("utf-8")
            self.tdatabuf = tdata_from_html(tables, wx.GetApp().http)

    def get_tdata(self):
        """Return table data, loading from server if necessary.

        Returns:
            Table data (list of rows), or None if unavailable.
        """
        if self.tdata is not None:
            return self.tdata
        if self.tdatabuf is not None:
            return self.tdatabuf
        if self.src:
            self.refresh_tdata()
        return self.tdatabuf

    def refresh_ldata(self):
        """Refresh hierarchical list data from the server.

        Loads from self.src and parses into self.ldatabuf using TreeParser.
        """
        if self.ldata is None and self.src:
            lista = self.load_data_from_server(self.src)
            mp = TreeParser()
            mp.feed(lista)
            mp.close()
            self.ldatabuf = mp.tree_parent[0][1]

    def get_ldata(self):
        """Return hierarchical list data, loading from server if necessary.

        Returns:
            List data (nested tree structure), or None if unavailable.
        """
        if self.ldata is not None:
            return self.ldata
        if self.ldatabuf is not None:
            return self.ldatabuf
        if self.src:
            self.refresh_ldata()
        return self.ldatabuf

    def get_parent_form(self):
        """Walk up the widget hierarchy to find the parent SchForm.

        Returns:
            The SchForm ancestor, or None if not found.
        """
        parent = self.parent
        while parent is not None:
            if type(parent).__name__ == "SchForm":
                return parent
            parent = parent.GetParent()
        return None

    def get_parent_page(self):
        """Return the parent page that contains this control's form.

        Returns:
            The parent SchPage, or None if not found.
        """
        form = self.get_parent_form()
        if form:
            return form.get_parent_page()
        return None


def handle_best_size(base_class):
    """Decorator that adds GetBestSize() using param width/height hints.

    When applied to a widget class, this makes GetBestSize() first check
    for explicit 'width' and 'height' values in self.param, falling back
    to the widget's default best size.

    Args:
        base_class: A wxPython widget class to wrap.

    Returns:
        A derived class with custom GetBestSize() logic.
    """

    class _Derived(base_class):
        def GetBestSize(self):
            w = 0
            h = 0
            if self.param and "width" in self.param:
                try:
                    w = int(self.param["width"])
                except (ValueError, TypeError):
                    pass
            if self.param and "height" in self.param:
                try:
                    h = int(self.param["height"])
                except (ValueError, TypeError):
                    pass
            if w == 0 or h == 0:
                base_size = super().GetBestSize()
                if w == 0:
                    w = base_size[0]
                if h == 0:
                    h = base_size[1]
            return (w, h)

    return _Derived
