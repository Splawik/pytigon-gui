"""SchPage is a container for four SchForm sub-windows: body, header,
footer and panel.  Only the 'body' form is mandatory; the others are
created on demand from the HTML response."""

import wx
import logging

logger = logging.getLogger(__name__)

try:
    from wx.adv import LayoutAlgorithm
except ImportError:
    from wx import LayoutAlgorithm

from pytigon_gui.guilib import events
from pytigon_gui.guilib.signal import Signal
from pytigon_lib.schtools import createparm
from pytigon_lib.schparser.html_parsers import ShtmlParser
from pytigon_lib.schhttptools.httpclient import HttpResponse
from pytigon_gui.guiframe.form import SchForm
from pytigon_gui.guilib.events import *


class SchPage(wx.Window, Signal):
    """Container that manages up to four SchForm instances.

    Reads an HTML response from the server and distributes its
    sections (header, body, footer, panel) into corresponding
    sash-layout sub-windows.
    """

    def __init__(
        self, parent, address_or_parser, parameters, pos=(0, 0), size=wx.DefaultSize
    ):
        """Construct a SchPage.

        Args:
            parent: Parent SchNotebookPage.
            address_or_parser: HTTP address (str) or ShtmlParser instance.
            parameters: Dictionary of request parameters.
            pos: Initial position.
            size: Initial size.
        """
        self._active = True
        self._ctrl_dict_old = {}
        self._ctrl_dict = {}
        self._last_size = None
        self._disable_setfocus = 0
        self._signal_handlers = []

        self.address_or_parser = address_or_parser
        self.parameters = parameters
        self.default_button = None
        self.parent_page = None
        self.last_control_with_focus = None
        self.vertical_position = None

        self.header = None
        self.panel = None
        self.body = None
        self.footer = None
        self.active_form = None
        self.active_ctrl = None

        Signal.__init__(self)
        wx.Window.__init__(
            self, parent, -1, pos, size, style=wx.WANTS_CHARS, name="SchPage"
        )

        self.exists = True

        mp = self._read_html(address_or_parser, parameters)
        if not mp:
            logger.error("ERROR READ HTML: %s %s", address_or_parser, parameters)

        self.address = mp.address

        header = mp.get_header()
        body = mp.get_body()
        footer = mp.get_footer()
        panel = mp.get_panel()
        config = mp.var

        vscroll = True
        hscroll = True

        if "no_vscrollbar" in config:
            vscroll = False
        if "no_hscrollbar" in config:
            hscroll = False
        if "vertical_position" in config:
            self.set_vertical_position(config["vertical_position"])

        self.title = mp.title

        if "disable_parent" in config:
            self.disable_parent = config["disable_parent"] != "0"
        else:
            self.disable_parent = True

        winids = []

        if header[0]:
            topwin = wx.adv.SashLayoutWindow(
                self,
                -1,
                wx.DefaultPosition,
                (100, 5),
                wx.adv.SW_3D,
                style=wx.WANTS_CHARS,
            )
            topwin.SetOrientation(wx.adv.LAYOUT_HORIZONTAL)
            topwin.SetAlignment(wx.adv.LAYOUT_TOP)
            topwin.SetSashVisible(wx.adv.SASH_BOTTOM, True)
            self.header = SchForm(topwin, page=self, form_type="header")
            self.header.show_form(header)
            dy = self.header.calculate_best_size()[1]
            topwin.SetDefaultSize((1000, dy))
            self._top_window = topwin
            winids.append(topwin.GetId())
        else:
            self._top_window = None

        if footer[0]:
            bottomwin = wx.adv.SashLayoutWindow(
                self, -1, wx.DefaultPosition, (1000, 5), wx.adv.SW_3D
            )
            bottomwin.SetOrientation(wx.adv.LAYOUT_HORIZONTAL)
            bottomwin.SetAlignment(wx.adv.LAYOUT_BOTTOM)
            bottomwin.SetSashVisible(wx.adv.SASH_TOP, True)
            self.footer = SchForm(bottomwin, page=self, form_type="footer")
            self.footer.show_form(footer)
            bottomwin.SetDefaultSize((1000, self.footer.calculate_best_size()[1]))
            self._bottom_window = bottomwin
            winids.append(bottomwin.GetId())
        else:
            self._bottom_window = None

        if panel[0]:
            leftwin = wx.adv.SashLayoutWindow(
                self, -1, wx.DefaultPosition, (5, 100), wx.adv.SW_3D
            )
            leftwin.SetOrientation(wx.adv.LAYOUT_VERTICAL)
            leftwin.SetAlignment(wx.adv.LAYOUT_LEFT)
            leftwin.SetSashVisible(wx.adv.SASH_RIGHT, True)
            self.panel = SchForm(leftwin, page=self, form_type="panel")
            self.panel.show_form(panel)
            xy = self.panel.calculate_best_size()
            leftwin.SetDefaultSize(xy)
            self._left_window = leftwin
            winids.append(leftwin.GetId())
        else:
            self._left_window = None

        self.body = SchForm(self, self, hscroll, vscroll)
        self.body.set_htm_type("body")
        attrs = mp.get_body_attrs()
        if "width" in attrs and "height" in attrs:
            w = attrs["width"]
            h = attrs["height"]
            self.body.bestsize = (int(w) * 4 / 3, int(h) * 4 / 3)
        self.body.show_form(body, parameters)
        self.body.set_address_parm(self.address)
        if "refresh" in mp.var:
            self.body.refresh_time(int(mp.var["refresh"]))

        if winids:
            self.Bind(
                wx.adv.EVT_SASH_DRAGGED_RANGE,
                self.on_sash_drag,
                id=min(winids),
                id2=max(winids),
            )

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.body.Bind(wx.EVT_CHILD_FOCUS, self.on_child_focus)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)

        self.register_signal(self, "child_closed_with_ok")

    # ------------------------------------------------------------------
    # Signal handling
    # ------------------------------------------------------------------

    def child_closed_with_ok(self, win=None):
        """Refresh HTML when a child window closes with OK."""
        wx.CallAfter(self.refresh_html)

    def reg_application_signal_handler(self, fun, signal):
        """Register a callback for a PyDispatcher signal.

        Args:
            fun: Callback function.
            signal: Signal name.
        """
        for existing in self._signal_handlers:
            if existing[1] == signal:
                break
        dispatcher.connect(fun, signal, sender=dispatcher.Any)
        self._signal_handlers.append((fun, signal))

    def unreg_application_signal_handler(self, signal):
        """Unregister a previously registered signal handler.

        Args:
            signal: Signal name.
        """
        i = 0
        found = None
        for pos in self._signal_handlers:
            if pos[1] == signal:
                found = pos
                break
            i += 1
        if found:
            dispatcher.disconnect(found[0], found[1], sender=dispatcher.Any)
            del self._signal_handlers[i]

    # ------------------------------------------------------------------
    # HTML reading and control management
    # ------------------------------------------------------------------

    def _read_html(self, address_or_parser, parameters):
        """Fetch and parse an HTML response.

        Args:
            address_or_parser: HTTP address (str) or ShtmlParser instance.
            parameters: Request parameters dict.

        Returns:
            Parsed ShtmlParser instance.
        """
        mp, adr = wx.GetApp().read_html(self, address_or_parser, parameters)
        return mp

    def append_ctrl(self, obj):
        """Register a widget with its unique name.

        Args:
            obj: The widget to register.
        """
        self._ctrl_dict[obj.get_unique_name()] = obj

    def restart_ctrl_lp(self):
        """Begin a new control lifecycle, preserving the old map."""
        self._ctrl_dict_old = self._ctrl_dict
        self._ctrl_dict = {}

    def pop_ctrl(self, name):
        """Retrieve and remove a widget from the previous lifecycle.

        Args:
            name: Unique widget name.

        Returns:
            The widget or None if not found.
        """
        return self._ctrl_dict_old.pop(name, None)

    def test_ctrl(self, name):
        """Check if a widget exists in the current lifecycle.

        Args:
            name: Unique widget name.

        Returns:
            True if the widget exists.
        """
        return name in self._ctrl_dict

    def remove_old_ctrls(self):
        """Destroy all widgets from the previous lifecycle."""
        for name, win in list(self._ctrl_dict_old.items()):
            win.Destroy()
        self._ctrl_dict_old = {}

    def __getitem__(self, key):
        return self._ctrl_dict[key]

    def get_widgets(self):
        """Return the current widget dictionary."""
        return self._ctrl_dict

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def init_frame(self, callback=None):
        """Initialize header, footer, panel, and body forms.

        Args:
            callback: Optional callable invoked after body init.
        """
        if self.header:
            self.header.init()
        if self.footer:
            self.footer.init()
        if self.panel:
            self.panel.init()

        self.body.init(callback)

    # ------------------------------------------------------------------
    # Parent / title / navigation
    # ------------------------------------------------------------------

    def get_parent_page(self):
        """Return the parent SchPage, if any."""
        return self.parent_page

    def set_default_button(self, button):
        """Set the default button activated by Enter.

        Args:
            button: The wx.Button-like control.
        """
        self.default_button = button

    def on_key_down(self, event):
        """Handle key down: Enter triggers the default button."""
        if event.KeyCode == wx.WXK_RETURN and self.default_button:
            self.default_button.OnClick(event)
        else:
            event.Skip()

    def on_char_hook(self, event):
        """Handle character input: Escape cancels the child form."""
        if event.KeyCode == wx.WXK_ESCAPE:
            parent = self.GetParent()
            if hasattr(parent, "on_child_form_cancel"):
                parent.on_child_form_cancel()
            else:
                event.Skip()
        else:
            event.Skip()

    def get_title(self):
        """Return the page title."""
        return self.title

    def set_adr_and_param(self, address_or_parser, param):
        """Change the source address and request parameters.

        Args:
            address_or_parser: New address or parser.
            param: New parameters dict.
        """
        self.address_or_parser = address_or_parser
        self.parameters = param

    # ------------------------------------------------------------------
    # Refresh / reload
    # ------------------------------------------------------------------

    def _refresh(self):
        """Re-fetch and re-display the page content.

        Returns:
            True on success, False if the request failed.
        """
        if isinstance(self.address_or_parser, ShtmlParser):
            if self.address_or_parser.address:
                mp = self._read_html(self.address_or_parser.address, self.parameters)
            else:
                mp = self._read_html(self.address_or_parser, self.parameters)
        elif isinstance(self.address_or_parser, HttpResponse):
            mp = self._read_html(self.address_or_parser.url, self.parameters)
        else:
            mp = self._read_html(self.address_or_parser, self.parameters)

        if not mp:
            return False

        header = mp.get_header()
        body = mp.get_body()
        footer = mp.get_footer()
        panel = mp.get_panel()
        self.title = mp.title

        if self.header:
            if not self.header.show_form(
                '<html encoding="utf-8">' + header + "</html>"
            ):
                return False
        if self.body:
            if not self.body.show_form(body, self.parameters):
                return False
        if self.footer:
            if not self.footer.show_form(
                '<html encoding="utf-8">' + footer + "</html>"
            ):
                return False
        if self.panel:
            if not self.panel.show_form('<html encoding="utf-8">' + panel + "</html>"):
                return False

        if self.header:
            self.header.init()
        if self.footer:
            self.footer.init()
        if self.panel:
            self.panel.init()

        self.body.Refresh()
        self.body.init()
        return True

    def CanClose(self):
        """Check whether all child forms can be closed.

        If all forms agree, their ``_on_close`` methods are called
        and signal handlers are disconnected.

        Returns:
            True if all forms can close.
        """
        for form in (self.body, self.header, self.footer, self.panel):
            if form and not form.CanClose():
                return False

        if self.header:
            self.header._on_close()
        if self.body:
            self.body._on_close()
        if self.footer:
            self.footer._on_close()
        if self.panel:
            self.panel._on_close()

        for handler in self._signal_handlers:
            dispatcher.disconnect(handler[0], handler[1], sender=dispatcher.Any)

        return True

    # ------------------------------------------------------------------
    # Focus management
    # ------------------------------------------------------------------

    def on_set_focus(self, evt):
        """Delegate focus to the body form."""
        if self.body:
            self.body.SetFocus()

    def on_child_focus(self, evt):
        """Track which widget last received focus.

        Ensures the owning HtmlPanel tab is selected and calls
        KillFocus on the previously focused widget.
        """
        if self._disable_setfocus:
            evt.Skip()
            return

        new_win = evt.GetWindow()
        parent = new_win.GetParent()
        while parent is not None:
            if parent.__class__.__name__ == "HtmlPanel":
                parent.SelectTab()
                break
            parent = parent.GetParent()

        while new_win is not None:
            if (
                new_win.GetParent()
                and new_win.GetParent().GetWindowStyleFlag() & wx.TAB_TRAVERSAL != 0
            ):
                break
            new_win = new_win.GetParent()

        if new_win is not self.last_control_with_focus:
            if self.last_control_with_focus and hasattr(
                self.last_control_with_focus, "KillFocus"
            ):
                self._disable_setfocus = True
                self.last_control_with_focus.KillFocus()
                self._disable_setfocus = False
            self.last_control_with_focus = new_win

        evt.Skip()

    def set_focus(self):
        """Restore focus to the last focused control or this window."""
        if self.last_control_with_focus:
            self.last_control_with_focus.SetFocus()
        else:
            super().SetFocus()

    # ------------------------------------------------------------------
    # Sash resize handling
    # ------------------------------------------------------------------

    def on_sash_drag(self, event):
        """Handle sash drag events for header, footer, and panel."""
        if event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            return
        eobj = event.GetEventObject()
        if eobj is self._top_window:
            self._top_window.SetDefaultSize((1000, event.GetDragRect().height))
        elif eobj is self._left_window:
            self._left_window.SetDefaultSize((event.GetDragRect().width, 1000))
        elif eobj is self._bottom_window:
            self._bottom_window.SetDefaultSize((1000, event.GetDragRect().height))
        LayoutAlgorithm().LayoutWindow(self, self.body)
        self.body.Refresh()

    def on_size(self, event):
        """Handle size changes, re-laying out the sash windows."""
        LayoutAlgorithm().LayoutWindow(self, self.body)
        self.body.Refresh()
        if event:
            event.Skip()

    def get_last_control_with_focus(self):
        """Return the last control that had focus."""
        return self.last_control_with_focus

    # ------------------------------------------------------------------
    # Refresh helpers
    # ------------------------------------------------------------------

    def refresh_html(self, method=0):
        """Reload page content from the server.

        Args:
            method: Refresh method (reserved for future use).
        """
        return self._refresh_html(method)

    def _refresh_html(self, method=0):
        """Internal refresh: re-parse, reset DC, and redraw."""
        ret = self._refresh()
        if self.body:
            self.body.wxdc = None
            self.body.update_controls = True
            self.body.Refresh()
        return ret

    # ------------------------------------------------------------------
    # Control lookup
    # ------------------------------------------------------------------

    def has_parm(self, param):
        """Check if a named control exists.

        Args:
            param: Control name.

        Returns:
            True if the control is found.
        """
        return param in self._ctrl_dict or self.item_exist(param)

    def get_parm(self, param):
        """Get the value of a named control.

        Args:
            param: Control name.

        Returns:
            The control's value, or None if not found.
        """
        ctrl = self._ctrl_dict.get(param) or self.get_item(param)
        if ctrl:
            return ctrl.GetValue()
        return None

    def get_item(self, ctrl_name):
        """Look up a control by name across all child forms.

        Args:
            ctrl_name: Name of the control.

        Returns:
            The control widget, or None.
        """
        if ctrl_name in self._ctrl_dict:
            return self._ctrl_dict[ctrl_name]
        for form in (self.body, self.header, self.panel, self.footer):
            if form is not None and hasattr(form, ctrl_name):
                return getattr(form, ctrl_name)
        return None

    def item_exist(self, ctrl_name):
        """Check whether a named control exists in any child form.

        Args:
            ctrl_name: Name of the control.

        Returns:
            True if found.
        """
        if ctrl_name in self._ctrl_dict:
            return True
        for form in (self.body, self.header, self.panel, self.footer):
            if form is not None and hasattr(form, ctrl_name):
                return True
        return False

    def __getitem__(self, key):
        return self.get_item(key)

    # ------------------------------------------------------------------
    # Sizing and state
    # ------------------------------------------------------------------

    def calculate_best_size(self):
        """Compute the best size based on all child forms.

        Returns:
            Tuple (width, height).
        """
        if self._last_size:
            dx = self._last_size.GetWidth()
            dy = self._last_size.GetHeight()
            self._last_size = None
            return (dx, dy)

        dx = 0
        dy = 0

        if self.header:
            x, y = self.header.calculate_best_size()
            dy += y
        if self.body:
            x, y = self.body.calculate_best_size()
            dx += x
            dy += y
        if self.footer:
            x, y = self.footer.calculate_best_size()
            dy += y
        if self.panel:
            x, y = self.panel.calculate_best_size()
            dx += x
            if y > dy:
                dy = y
        return (dx, dy)

    def enable_forms(self, enable):
        """Enable or disable all managed forms.

        Args:
            enable: If True, enable; if False, disable.
        """
        if not enable:
            self._last_size = self.GetSize()

        if enable or self.disable_parent:
            for form in (self.header, self.body, self.footer, self.panel):
                if form is not None:
                    form.enable(enable)

    def change_notebook_page_title(self, new_title):
        """Update the tab caption that contains this SchPage.

        Args:
            new_title: New tab text.
        """
        p = self.GetParent()
        tab = p.GetParent()
        sel = tab.GetPageIndex(p)
        tab.SetPageText(sel, new_title)

    def set_new_href(self, href):
        """Change the source address.

        Args:
            href: New address string.
        """
        self.address_or_parser = href

    def activate_page(self):
        """Activate this page and focus the body."""
        self._active = True
        self.body.SetFocus()

    def deactivate_page(self):
        """Deactivate this page."""
        self._active = False

    def is_active(self):
        """Return whether this page is active."""
        return self._active

    def set_page(self, page_source):
        """Replace the body form's HTML content.

        Args:
            page_source: New HTML string.
        """
        self.body.set_page(page_source)

    def set_vertical_position(self, position):
        """Set the placement preference for child forms.

        Args:
            position: 'top', 'bottom', None, or 'default'.
        """
        self.vertical_position = position

    def close(self):
        """Initiate cancellation of this page."""
        self.GetParent().on_child_form_cancel()
