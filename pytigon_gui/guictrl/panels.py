"""
Panel and container widget classes for the SchForm GUI framework.

Provides wxPython container controls integrated with SchBaseCtrl:
HTML panel, notebook (tab control), collapsible pane, and
composite panel.

Classes:
    HTML, NOTEBOOK, COLLAPSIBLE_PANEL, CompositePanel
"""

import wx

from pytigon_gui.guictrl.basectrl import SchBaseCtrl
from pytigon_gui.guiframe import page
from pytigon_lib.schparser.html_parsers import ShtmlParser


class HTML(page.SchPage, SchBaseCtrl):
    """HTML content panel.

    Handles ctrlhtml tag. Renders HTML content loaded from a
    server source or provided inline via param['data'].

    Tag arguments:
        value: HTML content.
        src: URL to load HTML from.
        data: Inline HTML from param['data'].
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        page.SchPage.__init__(self, parent, self.src, None)
        if self.src:
            value = self.load_string_from_server(self.src)
            self._set_value(value, False)
        elif self.param and "data" in self.param and len(self.param["data"]) > 0:
            self._set_value(self.param["data"], False)
        else:
            self._value = None
        self.body.Refresh()
        self.body.Update()

    def CanAcceptFocus(self):
        return False

    def SetValue(self, value):
        """Set the HTML content value.

        Args:
            value: HTML string to display.
        """
        self._set_value(value)

    def _set_value(self, value, refresh=True):
        """Internal method to parse and display HTML.

        Args:
            value: HTML string. If it does not contain '<html',
                wraps it in <html><body>...</body></html>.
            refresh: If True, redraws the page body.
        """
        if "<html" not in value:
            self._value = f"<html><body>{value}</body></html>"
        else:
            self._value = value
        mp = ShtmlParser()
        mp.process(self._value)
        mp.address = None
        body = mp.get_body()
        self.body.show_page(body)
        if refresh:
            self.body.wxdc = None
            self.body.draw_background()

    def GetValue(self):
        """Return the raw HTML string."""
        return self._value


class NOTEBOOK(wx.Notebook, SchBaseCtrl):
    """Tabbed notebook container.

    Handles ctrlnotebook tag. Each row in tdata creates a tab
    page: row[0].data is the tab label, row[1].data is the
    content href.

    Tag arguments:
        value: Not directly used; tabs from tdata.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        self.children = []
        wx.Notebook.__init__(self, parent, **kwds)
        if self.tdata:
            for row in self.tdata:
                h = page.SchPage(self, row[1].data, {})
                self.AddPage(h, row[0].data)
                self.children.append(h)


class COLLAPSIBLE_PANEL(wx.CollapsiblePane, SchBaseCtrl):
    """Collapsible panel that can show/hide HTML content.

    Handles ctrlcollapsible_panel tag. Content is loaded from
    param['data'] as HTML and rendered in a SchPage child.

    Tag arguments:
        value: Not directly used.
        collapse_height: Height when collapsed (from param).
        data: HTML content from param['data'].
        label: Panel header label.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        kwds["label"] = self.label
        kwds["style"] = wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE
        if "size" in kwds:
            tmp = kwds["size"]
            self._size = [tmp[0], tmp[1]]
            del kwds["size"]
        else:
            self._size = [400, 300]
        self._height = 0

        if self.param and "collapse_height" in self.param:
            self._size[1] = int(self.param["collapse_height"])

        wx.CollapsiblePane.__init__(self, parent, **kwds)
        try:
            self.GetPane().SetBackgroundStyle(wx.BG_STYLE_ERASE)
        except Exception:
            self.GetPane().SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        if self.param and "data" in self.param and self.param["data"].strip():
            self.set_html(self.param["data"])
        else:
            self.html = None
            self.SetSize((0, 0))
            self.Hide()
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._on_pane_changed)

    def set_html(self, html_txt):
        """Parse and display HTML content in the pane.

        Args:
            html_txt: HTML string to render.
        """
        mp = ShtmlParser()
        mp.process(
            "<html><body>" + self.param["data"].decode("utf-8") + "</body></html>"
        )
        mp.address = None
        if not self.html:
            self.html = page.SchPage(self.GetPane(), mp, {})
            self.html.init_frame()
            self.html.activate_page()
            width = self._size[0] if self._size[0] > 0 else 400
            self._height = self._size[1] if self._size[1] > 0 else 300
            self.html.SetSize((width, self._height))
            sizer = wx.BoxSizer()
            sizer.Add(self.html, 1, wx.EXPAND | wx.ALL, 5)
            self.GetPane().SetSizer(sizer)
            self._on_pane_changed(None)
        else:
            self.html.set_adr_and_param(mp, None)
            self._on_pane_changed(None)

    def _on_pane_changed(self, event):
        """Handle pane expand/collapse events.

        Refreshes the parent and internal HTML layout.

        Args:
            event: CollapsiblePane change event or None.
        """
        if self.html:
            self.GetParent().GetParent().refresh_html()
            self.html.refresh_html()

    def GetBestSize(self):
        """Return best size accounting for expanded content height.

        Returns:
            Tuple of (width, height).
        """
        ret = wx.CollapsiblePane.GetBestSize(self)
        if self.IsExpanded():
            return (ret[0], ret[1] + self._height)
        elif not self.IsShown():
            return (0, 0)
        else:
            if ret[1] - self._height > 0:
                return (ret[0], ret[1] - self._height)
            else:
                return (ret[0], ret[1])

    def SetValue(self, value):
        """Set value (placeholder - HTML is set via set_html)."""
        if not self.html:
            pass

    def process_refr_data(self, **kwds):
        """Refresh from new data.

        Args:
            **kwds: New keyword arguments. If param['data'] is
                non-empty, shows the panel and sets HTML content.
        """
        if "param" in kwds:
            self.param = kwds["param"]
            if "data" in self.param and self.param["data"].strip():
                self.Show(True)
                self.set_html(self.param["data"])


class CompositePanel(wx.Panel, SchBaseCtrl):
    """Composite panel that wraps a primary control.

    Used by SELECT2 to embed a Select2Base control alongside
    optional action buttons in a horizontal layout.

    Tag arguments:
        value: Delegated to the wrapped control.
    """

    def __init__(self, parent, **kwds):
        SchBaseCtrl.__init__(self, parent, kwds)
        wx.Panel.__init__(self, parent, **kwds)
        self.ctrl = None

    def set_main_ctrl(self, ctrl):
        """Set the primary wrapped control.

        Args:
            ctrl: The main wx control to embed.
        """
        self.ctrl = ctrl

    def GetValue(self):
        """Get value from the wrapped control.

        Returns:
            String value or None.
        """
        if self.ctrl:
            return str(self.ctrl.GetValue())
        else:
            return None
