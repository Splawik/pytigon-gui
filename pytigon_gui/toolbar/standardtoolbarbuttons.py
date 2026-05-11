"""Standard toolbar button creation and event handling.

Defines the StandardButtons class that creates File, Edit, Operations,
Browse, and Address panels with their associated event handlers.
Also includes the SchAutoComplete widget for the address bar.
"""

import wx
from pytigon_gui.guilib.events import *
from autocomplete import TextCtrlAutoComplete
from pytigon_gui.guilib.image import bitmaps_from_art_id
from pytigon_gui.guilib.tools import colour_to_html, find_focus_in_form
from wx.lib.agw import flatmenu as FM

_ = wx.GetTranslation

# Platform style flag (currently always True)
MSW_STYLE = True

# Default address bar history entries
ADDRESS_HISTORY = [
    "www.allegro.pl",
    "www.onet.pl",
    "www.google.pl",
    "www.sourceforge.org",
    "www.freshmeat.net",
    "127.0.0.2",
    "127.0.0.1:8000",
    "books.evc-cit.info/index.html",
    "www.un.org/Depts/Cartographic/map/profile/poland.pdf",
]

TYPE_TOOLBAR = 0
TYPE_BUTTONBAR = 1
TYPE_PANELBAR = 2


class WebHistory(object):
    """A simple list-like object providing address bar history.

    Wraps the ADDRESS_HISTORY list and exposes a limited subset.
    """

    def __iter__(self):
        """Iterate over all history entries."""
        for x in ADDRESS_HISTORY:
            yield x

    def __getitem__(self, idx):
        """Return a history entry by index.

        Args:
            idx: Index into the history.

        Returns:
            str: The history entry at the given index.

        Raises:
            IndexError: If idx is out of range (>= 4).
        """
        if idx < 4:
            return ADDRESS_HISTORY[idx]
        else:
            raise IndexError("WebHistory index out of range")

    def __len__(self):
        """Return the number of history entries available."""
        return 4

    def __contains__(self, x):
        """Check if an address is in the history.

        Args:
            x: Address string to check.

        Returns:
            bool: True if the address is in the history.
        """
        return x in ADDRESS_HISTORY


class SchAutoComplete(TextCtrlAutoComplete):
    """Address bar auto-complete control with dynamic web history.

    Extends TextCtrlAutoComplete to provide URL auto-completion
    from a WebHistory instance.
    """

    def __init__(self, *argi, **argv):
        """Initialize the auto-complete control.

        Args:
            *argi: Positional arguments for TextCtrlAutoComplete.
            **argv: Keyword arguments; 'choices' will be overridden
                with a WebHistory instance if provided.
        """
        self.dynamic_choices = WebHistory()
        argv["choices"] = self.dynamic_choices
        TextCtrlAutoComplete.__init__(self, *argi, **argv)
        self.SetEntryCallback(self.set_dynamic_choices)
        self.SetMatchFunction(self.match)
        self.Bind(wx.EVT_KEY_DOWN, self.on_return_key_down, self)

    def on_return_key_down(self, event):
        """Handle Return key: trigger callback if dropdown is hidden.

        Args:
            event: wx.KeyEvent.
        """
        if not self.dropdown.IsShown() and event.GetKeyCode() == wx.WXK_RETURN:
            self.fun(self.GetValue())
        else:
            event.Skip()

    def set_callback_fun(self, fun):
        """Set the callback invoked when a URL is selected or entered.

        Args:
            fun: Callable that accepts a URL string.
        """
        self.fun = fun

    def match(self, text, choice):
        """Determine if a choice matches the entered text.

        Matches against the raw choice, the choice without 'http://',
        and the choice without 'www.'.

        Args:
            text: User-entered text (lowercase).
            choice: A history entry to match against.

        Returns:
            bool: True if the choice matches.
        """
        t = text.lower()
        c = choice.lower()
        if c.startswith(t):
            return True
        if c.startswith("http://"):
            c = c[7:]
        if c.startswith(t):
            return True
        if c.startswith("www."):
            c = c[4:]
        return c.startswith(t)

    def set_dynamic_choices(self):
        """Filter choices based on the current text input."""
        ctrl = self
        text = ctrl.GetValue().lower()
        current_choices = ctrl.GetChoices()
        choices = [
            choice for choice in self.dynamic_choices if self.match(text, choice)
        ]
        if choices != current_choices:
            ctrl.SetChoices(choices)

    def _set_value_from_selected(self):
        """Override to trigger the callback after a dropdown selection.

        Returns:
            The value from the parent implementation.
        """
        x = TextCtrlAutoComplete._setValueFromSelected(self)
        self.fun(self.GetValue())
        return x


class EmptyControl(object):
    """A stub control used when no real address bar is available.

    Provides SetValue/GetValue with no-op behavior.
    """

    def __init__(self):
        self.value = None

    def SetValue(self, value):
        """Store a value (no-op visually).

        Args:
            value: Value to store.
        """
        self.value = value

    def GetValue(self):
        """Return the stored value.

        Returns:
            The stored value or None.
        """
        return self.value


class EmptyBar(object):
    """A stub toolbar bar used when a browser panel is not enabled.

    Provides a no-op refr method for compatibility.
    """

    def __init__(self):
        pass

    def refr(self):
        """No-op refresh method."""
        pass


class StandardButtons(object):
    """Creates and manages standard toolbar buttons and their event handlers.

    Reads the gui_style string to determine which panels (File, Clipboard,
    Operations, Browser, Address) should be created and configures
    event bindings for each.
    """

    def __init__(self, toolbar_interface, gui_style):
        """Initialize standard buttons.

        Args:
            toolbar_interface: The toolbar bar instance (ToolbarBar subclass).
            gui_style: String describing which features to enable.
        """
        self.toolbar_interface = toolbar_interface
        self.gui_style = gui_style
        self.ti = self.toolbar_interface
        self.tbs = self.ti.toolbars
        self._object_list = {}
        self.webobject = None
        self.file = "file" in self.gui_style
        self.clipboard = "clipboard" in self.gui_style
        self.operations = "operations" in self.gui_style
        self.browse = "browse" in self.gui_style
        self.nav = "nav" in self.gui_style
        self.address_bar = "address_bar" in self.gui_style
        self.bg = colour_to_html(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.bg_info = colour_to_html(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK))
        self.bg_h = colour_to_html(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        self.progress = 0
        self.info = ""
        self.address_txt = ""

    def make_ui_handler(self, fun_name, event_id, propagate=False):
        """Create a UI update handler that enables/disables based on focus.

        Walks up the focus chain calling the named method; enables
        the event if any focused control returns True.

        Args:
            fun_name: Name of the method to call (e.g. 'CanCopy').
            event_id: wx event ID to bind to.
            propagate: If True, walk up the parent chain.
        """

        def on_update_ui(event):
            win = find_focus_in_form()
            while win:
                if hasattr(win, fun_name):
                    if getattr(win, fun_name)():
                        event.Enable(True)
                        return
                if propagate:
                    win = win.GetParent()
                else:
                    break
            event.Enable(False)

        self.toolbar_interface.parent.Bind(wx.EVT_UPDATE_UI, on_update_ui, id=event_id)

    def make_handler(self, fun_name, event_id, propagate=False):
        """Create a command handler that delegates to the focused control.

        Walks up the focus chain calling the named method on the first
        control that has it.

        Args:
            fun_name: Name of the method to call (e.g. 'Copy').
            event_id: wx event ID to bind to.
            propagate: If True, walk up the parent chain.
        """

        def on_command(event):
            win = find_focus_in_form()
            while win:
                if hasattr(win, fun_name):
                    getattr(win, fun_name)()
                if propagate:
                    win = win.GetParent()
                else:
                    break

        self.toolbar_interface.bind(on_command, id=event_id)

    def make_handlers(self, event_id, fun_name, fun_name2=None, propagate=False):
        """Create both command and UI update handlers for a button.

        Args:
            event_id: wx event ID to bind to.
            fun_name: Name of the command method (e.g. 'Copy').
            fun_name2: Name of the UI update method (e.g. 'CanCopy').
                If None, the button is always enabled.
            propagate: If True, walk up the parent chain.
        """
        self.make_handler(fun_name, event_id, propagate)
        if fun_name2:
            self.make_ui_handler(fun_name2, event_id, propagate)
        else:

            def on_update_ui(event):
                event.Enable(True)

            self.toolbar_interface.parent.Bind(
                wx.EVT_UPDATE_UI, on_update_ui, id=event_id
            )

    def create_file_panel(self, toolbar_page):
        """Create the File panel with Open, Save, Print, and Exit buttons.

        Args:
            toolbar_page: The toolbar page to add panels to (unused; buttons
                are added to the main page).
        """
        if self.file:
            bar = self.ti.create_panel_in_main_page(_("File"), TYPE_TOOLBAR)
            self.tbs["file"] = {}
            self.tbs["file"]["bar"] = bar
            if "exit" in self.gui_style:
                self.tbs["file"]["exit"] = bar.add_simple_tool(
                    wx.ID_EXIT,
                    _("Exit"),
                    bitmaps_from_art_id(wx.ART_QUIT, wx.Size(32, 32)),
                )
            test = False
            if "open" in self.gui_style:
                bar.add_separator()
                self.tbs["file"]["open"] = bar.add_simple_tool(
                    wx.ID_OPEN,
                    _("Open"),
                    bitmaps_from_art_id(wx.ART_FILE_OPEN, wx.Size(32, 32)),
                )
                test = True
            if "save" in self.gui_style:
                if not test:
                    bar.add_separator()
                self.tbs["file"]["save"] = bar.add_simple_tool(
                    wx.ID_SAVE,
                    _("Save"),
                    bitmaps_from_art_id(wx.ART_FILE_SAVE, wx.Size(32, 32)),
                )
                self.make_handlers(wx.ID_SAVE, "Save", "CanSave", propagate=True)
                if "save_as" in self.gui_style:
                    self.tbs["file"]["save_as"] = bar.add_simple_tool(
                        wx.ID_SAVEAS,
                        _("Save as"),
                        bitmaps_from_art_id(wx.ART_FILE_SAVE_AS, wx.Size(32, 32)),
                    )
                    self.make_handlers(
                        wx.ID_SAVEAS, "SaveAs", "CanSaveAs", propagate=True
                    )
                test = True
            if "print" in self.gui_style:
                if test:
                    bar.add_separator()
                    self.tbs["file"]["print"] = bar.add_hybrid_tool(
                        ID_PRINT,
                        _("Print"),
                        bitmaps_from_art_id(wx.ART_PRINT, wx.Size(32, 32)),
                    )
                    bar.add_separator()
                else:
                    self.tbs["file"]["print"] = bar.add_hybrid_tool(
                        ID_PRINT,
                        _("Print"),
                        bitmaps_from_art_id(wx.ART_PRINT, wx.Size(32, 32)),
                    )
                self.make_handlers(ID_PRINT, "Print", "CanPrint", propagate=True)
                self.ti.bind_dropdown(self.on_print, ID_PRINT)

    def create_edit_panel(self, toolbar_page):
        """Create the Clipboard panel with Copy, Cut, and Paste buttons.

        Args:
            toolbar_page: The toolbar page (unused).
        """
        if self.clipboard:
            self.tbs["clipboard"] = {}
            bar = self.ti.create_panel_in_main_page(_("Clipboard"), TYPE_BUTTONBAR)
            bar.Refr = self.clipboard_refr
            self.tbs["clipboard"]["bar"] = bar
            self.tbs["clipboard"]["copy"] = bar.add_simple_tool(
                wx.ID_COPY, _("Copy"), bitmaps_from_art_id(wx.ART_COPY, wx.Size(32, 32))
            )
            self.tbs["clipboard"]["cut"] = bar.add_simple_tool(
                wx.ID_CUT, _("Cut"), bitmaps_from_art_id(wx.ART_CUT, wx.Size(32, 32))
            )
            self.tbs["clipboard"]["paste"] = bar.add_simple_tool(
                wx.ID_PASTE,
                _("Paste"),
                bitmaps_from_art_id(wx.ART_PASTE, wx.Size(32, 32)),
            )

            self.make_handlers(wx.ID_COPY, "Copy", "CanCopy")
            self.make_handlers(wx.ID_CUT, "Cut", "CanCut")
            self.make_handlers(wx.ID_PASTE, "Paste", "CanPaste")

    def create_operations_panel(self, toolbar_page):
        """Create the Operations panel with Undo, Redo, Find, etc.

        Args:
            toolbar_page: The toolbar page (unused).
        """
        if self.operations:
            self.tbs["operations"] = {}
            bar = self.ti.create_panel_in_main_page(_("Operations"), TYPE_TOOLBAR)
            self.tbs["operations"]["bar"] = bar
            self.tbs["operations"]["undo"] = bar.add_simple_tool(
                wx.ID_UNDO, _("Undo"), bitmaps_from_art_id(wx.ART_UNDO, wx.Size(32, 32))
            )
            self.tbs["operations"]["redo"] = bar.add_simple_tool(
                wx.ID_REDO, _("Redo"), bitmaps_from_art_id(wx.ART_REDO, wx.Size(32, 32))
            )
            self.tbs["operations"]["find"] = bar.add_hybrid_tool(
                ID_FIND, _("Find"), bitmaps_from_art_id(wx.ART_FIND, wx.Size(32, 32))
            )
            bar.add_separator()
            self.tbs["operations"]["filemanager"] = bar.add_simple_tool(
                wx.ID_ANY,
                _("File manager"),
                bitmaps_from_art_id(wx.ART_FOLDER_OPEN, wx.Size(32, 32)),
            )
            self.tbs["operations"]["editor"] = bar.add_simple_tool(
                wx.ID_ANY,
                _("Editor"),
                bitmaps_from_art_id(wx.ART_NORMAL_FILE, wx.Size(32, 32)),
            )
            self.ti.bind_dropdown(self.on_find, ID_FIND)

            self.make_handlers(wx.ID_UNDO, "Undo", "CanUndo")
            self.make_handlers(wx.ID_REDO, "Redo", "CanRedo")
            self.make_handlers(ID_FIND, "Find", "CanFind")

    def create_browse_panel(self, toolbar_page):
        """Create the Browser panel with navigation buttons.

        Args:
            toolbar_page: The toolbar page (unused).
        """
        if self.browse or self.nav:
            self.tbs["browser"] = {}
            bar = self.ti.create_panel_in_main_page(_("Browser"), TYPE_BUTTONBAR)
            bar.Refr = self.web_refr
            self.webobject = None
            self.tbs["browser"]["bar"] = bar
            self.tbs["browser"]["back"] = bar.add_simple_tool(
                ID_WEB_BACK,
                _("Back"),
                bitmaps_from_art_id(wx.ART_GO_BACK, wx.Size(32, 32)),
            )
            self.tbs["browser"]["forward"] = bar.add_simple_tool(
                ID_WEB_FORWARD,
                _("Forward"),
                bitmaps_from_art_id(wx.ART_GO_FORWARD, wx.Size(32, 32)),
            )
            self.make_handlers(ID_WEB_BACK, "WebBack", "CanWebBack", propagate=True)
            self.make_handlers(
                ID_WEB_FORWARD, "WebForward", "CanWebForward", propagate=True
            )

            if self.browse:
                self.tbs["browser"]["stop"] = bar.add_simple_tool(
                    ID_WEB_STOP,
                    _("Stop"),
                    bitmaps_from_art_id(wx.ART_CROSS_MARK, wx.Size(32, 32)),
                )
                self.tbs["browser"]["refresh"] = bar.add_simple_tool(
                    ID_WEB_REFRESH,
                    _("Refresh"),
                    bitmaps_from_art_id(wx.ART_GO_TO_PARENT, wx.Size(32, 32)),
                )
                self.tbs["browser"]["addbookmark"] = bar.add_simple_tool(
                    ID_WEB_ADDBOOKMARK,
                    _("Add bookmark"),
                    bitmaps_from_art_id(wx.ART_ADD_BOOKMARK, wx.Size(32, 32)),
                )
                self.tbs["browser"]["newpage"] = bar.add_simple_tool(
                    ID_WEB_NEW_WINDOW,
                    _("New page"),
                    bitmaps_from_art_id(wx.ART_NEW, wx.Size(32, 32)),
                )

                self.make_handlers(ID_WEB_STOP, "WebStop", "CanWebStop", propagate=True)
                self.make_handlers(
                    ID_WEB_REFRESH, "WebRefresh", "CanWebRefresh", propagate=True
                )
                self.make_handlers(
                    ID_WEB_ADDBOOKMARK,
                    "WebAddBookmark",
                    "CanWebAddBookmark",
                    propagate=True,
                )
                self.make_handlers(ID_WEB_NEW_WINDOW, "WebNewWindow", propagate=False)
        else:
            self.tbs["browser"] = {}
            self.tbs["browser"]["bar"] = EmptyBar()

    def create_address_panel(self, toolbar_page):
        """Create the Address bar panel with auto-complete and web menu.

        Args:
            toolbar_page: The toolbar page (unused).
        """
        if self.address_bar:
            bar = self.ti.create_panel_in_main_page(_("Address"), TYPE_PANELBAR)
            if hasattr(bar, "panel"):
                width = 350
                panel = bar.panel
                self.address = SchAutoComplete(panel, size=wx.Size(width, -1))
                self.address.set_callback_fun(self.open_page)
                self.tbs["browser"]["address"] = self.address
                self.webmenu = FM.FlatMenuBar(panel, spacer=5)
                self.webmenu.GetRendererManager().SetTheme(FM.Style2007)
                self.tbs["browser"]["webmenu"] = self.webmenu
                webmenu_source = self.web_menu()
                self.web_info = wx.html.HtmlWindow(
                    panel, style=wx.html.HW_SCROLLBAR_NEVER, size=(width, 25)
                )
                self.web_info.SetBorders(0)
                self._info_clear()
                self.make_menu(self.webmenu, webmenu_source)
                controls = (self.webmenu, self.web_info, self.address)
                bar.AddPanel(controls)
            else:
                self.tbs["browser"]["address"] = EmptyControl()
                self.web_info = None
        else:
            self.tbs["browser"]["address"] = EmptyControl()
            self.web_info = None

    def load_page(self, address):
        """Load a URL in the browser panel if one is active.

        Args:
            address: URL to load.
        """
        if "browser" in self._object_list and self._object_list["browser"]:
            self._object_list["browser"].Go(address)

    def _title_from_address(self, address):
        """Extract a short display title from a URL.

        Args:
            address: Full URL string.

        Returns:
            str: Truncated title suitable for display.
        """
        x = address.replace("http://", "")
        if len(x) > 20:
            x = x[:16] + " ..."
        return x

    def _status(self, tab):
        """Update enabled/disabled state for a set of toolbar buttons.

        Args:
            tab: List of (enabled, panel_key, button_key) tuples.
        """
        start_status = []
        dis = self.ti.status_tool_disabled()
        for pos in tab:
            start_status.append(self.tbs[pos[1]][pos[2]].state & dis)
            if pos[0]:
                self.tbs[pos[1]][pos[2]].state &= ~dis
            else:
                self.tbs[pos[1]][pos[2]].state |= dis
        i = 0
        for pos in tab:
            if start_status[i] != self.tbs[pos[1]][pos[2]].state & dis:
                self.tbs[pos[1]]["bar"].Refresh()
                return
            i += 1

    def clipboard_refr(self, editctrl):
        """Refresh clipboard buttons based on the focused control's capabilities.

        Args:
            editctrl: The currently focused edit control, or None.
        """
        if self.clipboard:
            tab_status = []
            if editctrl:
                tab_status.append(
                    (
                        hasattr(editctrl, "CanCopy") and editctrl.CanCopy(),
                        "clipboard",
                        "copy",
                    )
                )
                tab_status.append(
                    (
                        hasattr(editctrl, "CanCut") and editctrl.CanCut(),
                        "clipboard",
                        "cut",
                    )
                )
                tab_status.append(
                    (
                        hasattr(editctrl, "CanPaste") and editctrl.CanPaste(),
                        "clipboard",
                        "paste",
                    )
                )
            else:
                tab_status.append((False, "clipboard", "copy"))
                tab_status.append((False, "clipboard", "cut"))
                tab_status.append((False, "clipboard", "paste"))
            return self._status(tab_status)

    def operations_refr(self, editctrl):
        """Refresh operations buttons based on the focused control's capabilities.

        Args:
            editctrl: The currently focused edit control, or None.
        """
        if self.operations:
            tab_status = []
            if editctrl:
                tab_status.append(
                    (
                        hasattr(editctrl, "CanRedo") and editctrl.CanRedo(),
                        "operations",
                        "redo",
                    )
                )
                tab_status.append(
                    (
                        hasattr(editctrl, "CanUndo") and editctrl.CanUndo(),
                        "operations",
                        "undo",
                    )
                )
            else:
                tab_status.append((False, "operations", "redo"))
                tab_status.append((False, "operations", "undo"))
            return self._status(tab_status)

    def web_refr(self, webobject):
        """Refresh browser navigation buttons based on web view state.

        Args:
            webobject: The web view control, or None.
        """
        if self.browse or self.nav:
            tab_status = []
            if webobject:
                tab_status.append((webobject.CanGoBack(), "browser", "back"))
                tab_status.append((webobject.CanGoForward(), "browser", "forward"))
                if self.browse:
                    tab_status.append((True, "browser", "stop"))
                    tab_status.append((True, "browser", "refresh"))
                    tab_status.append((True, "browser", "addbookmark"))
                    tab_status.append((True, "browser", "newpage"))
            else:
                tab_status.append((False, "browser", "back"))
                tab_status.append((False, "browser", "forward"))
                if self.browse:
                    tab_status.append((False, "browser", "stop"))
                    tab_status.append((False, "browser", "refresh"))
                    tab_status.append((False, "browser", "addbookmark"))
                    tab_status.append((False, "browser", "newpage"))
            return self._status(tab_status)

    def address_refr(self, panel):
        """Refresh the address bar based on the active panel's web status.

        Args:
            panel: The active panel, or None.
        """
        if self.address_bar:
            if panel is not None and hasattr(panel.body, "WEB"):
                ctrl = panel.body.WEB
                if hasattr(ctrl, "GetStatus"):
                    status = ctrl.GetStatus()
                    if status["progress"] >= 0:
                        self._info_proc(
                            status["txt"].replace("INFO:", "").replace("ERROR:", ""),
                            status["progress"],
                        )
                    else:
                        if status["txt"] and status["txt"] != "":
                            if "ERROR:" in status["txt"]:
                                self._info_alarm(status["txt"].replace("ERROR:", ""))
                            else:
                                self._info_txt(status["txt"].replace("INFO:", ""))
                        else:
                            self._info_clear()
                    if self.address_txt != status["address"]:
                        if status["address"]:
                            self.address.SetValue(status["address"])
                            self.address_txt = status["address"]
                        else:
                            self.address.SetValue("")
                            self.address_txt = ""
            else:
                if self.address_txt != "":
                    self.address.SetValue("")
                    self.address_txt = ""
                self._info_clear()

    def _info_proc(self, txt, proc):
        """Display a progress bar in the web info area.

        Args:
            txt: Status text.
            proc: Progress percentage (0-100).
        """
        if self.web_info and (txt != self.info or proc != self.progress):
            if txt:
                self.web_info.SetPage(
                    "<body bgcolor='%s'><table width='100%%'>"
                    "<tr><td bgcolor='%s' width='%s%%'></td><td></td></tr>"
                    "<tr><td colspan='2' bgcolor='%s'><small>%s</small></td></tr>"
                    "</table></body>" % (self.bg, self.bg_h, proc, self.bg_info, txt)
                )
            else:
                self.web_info.SetPage(
                    "<body bgcolor='%s'><table width='100%%'>"
                    "<tr><td bgcolor='%s' width='%s%%'></td><td></td></tr>"
                    "</table></body>" % (self.bg, self.bg_h, proc)
                )
            self.info = txt
            self.progress = proc

    def _info_txt(self, txt):
        """Display informational text in the web info area.

        Args:
            txt: Informational message.
        """
        if self.web_info and txt != self.info:
            self.web_info.SetPage(
                "<body bgcolor='%s'><table width='100%%'>"
                "<tr><td bgcolor='%s'><strong><small>%s</small></strong></td></tr>"
                "</table></body>" % (self.bg, self.bg_info, txt)
            )
            self.info = txt
            self.progress = -1

    def _info_alarm(self, txt):
        """Display an error/alarm message in the web info area.

        Args:
            txt: Error message.
        """
        if self.web_info and txt != self.info:
            self.web_info.SetPage(
                "<body bgcolor='%s'><table width='100%%'>"
                "<tr><td bgcolor='%s'><strong><small>%s</small></strong></td></tr>"
                "</table></body>" % (self.bg, self.bg_info, txt)
            )
            self.info = txt
            self.progress = -1

    def _info_clear(self):
        """Clear the web info area."""
        if self.web_info and (self.info != "" or self.progress != -1):
            self.web_info.SetPage("<body bgcolor='%s'></body>" % self.bg)
            self.info = ""
            self.progress = -1

    def open_page(self, page):
        """Open a URL in a new web view page.

        Args:
            page: URL to open.

        Returns:
            bool: True on success.
        """
        name = self._title_from_address(page)
        okno = (
            wx.GetApp()
            .GetTopWindow()
            .new_main_page("^standard/webview/widget_web.html", name)
        )
        okno.body.WEB.Go(page)
        return True

    def on_print(self, event):
        """Show the print dropdown menu.

        Args:
            event: The dropdown event.
        """
        menu = FM.FlatMenu()
        menu.Append(wx.ID_ANY, _("Print"), _("Print"), wx.ITEM_NORMAL)
        menu.Append(wx.ID_ANY, _("Print preview"), _("Print preview"), wx.ITEM_NORMAL)
        menu.Append(
            wx.ID_ANY, _("Printer settings"), _("Printer settings"), wx.ITEM_NORMAL
        )
        self.ti.popup_menu(event, menu)

    def on_find(self, event):
        """Show the find/replace dropdown menu.

        Args:
            event: The dropdown event.
        """
        menu = FM.FlatMenu()
        menu.Append(wx.ID_ANY, _("Find"), _("Find"), wx.ITEM_NORMAL)
        menu.Append(wx.ID_ANY, _("Replace"), _("Replace"), wx.ITEM_NORMAL)
        event.PopupMenu(menu)

    def make_menu(self, menubar, menulist):
        """Build a flat menu bar from a nested menu definition.

        Args:
            menubar: The FlatMenuBar to populate.
            menulist: List of (title, ((label, id), ...)) tuples.
        """
        for item in menulist:
            menu = FM.FlatMenu()
            for pos in item[1]:
                menuitem = FM.FlatMenuItem(menu, pos[1], pos[0], pos[0], wx.ITEM_NORMAL)
                menu.AppendItem(menuitem)
            menubar.Append(menu, item[0])

    def memke_menu(self, menubar, menulist):
        """Backward compatibility alias for make_menu.

        Args:
            menubar: The FlatMenuBar to populate.
            menulist: List of (title, ((label, id), ...)) tuples.
        """
        self.make_menu(menubar, menulist)

    def web_menu(self):
        """Return the web menu structure definition.

        Returns:
            tuple: Nested menu definition for the web toolbar menu.
        """
        menu = (
            (
                _("View"),
                (
                    (_("Zoom"), ID_ZOOM),
                    (_("Block elements"), ID_PAGE_BLOCK),
                    (_("View elements"), ID_PAGE_VIEW),
                    (_("View page source"), ID_WEB_SOURCE),
                    (_("Edit page"), ID_WEB_EDIT),
                ),
            ),
            (
                _("History"),
                (
                    (_("Show history panel"), ID_HISTORY_SHOW),
                    (_("Clear history"), ID_CLEAR_HISTORY),
                ),
            ),
            (
                _("Bookmarks"),
                (
                    (_("Add to bookmarks"), ID_BOOKMARK_ADD),
                    (_("Show bookmarks panel"), ID_SHOW_BOOKMARKS),
                ),
            ),
            (
                _("Downloads"),
                (
                    (_("Show download panel"), ID_SHOW_DOWNLOAD),
                    (_("Options"), ID_DOWNLOAD_OPTIONS),
                ),
            ),
            (
                _("Tools"),
                (
                    (_("Show download panel"), ID_SHOW_DOWNLOAD),
                    (_("Options"), ID_DOWNLOAD_OPTIONS),
                ),
            ),
            (
                _("Options"),
                (
                    (_("General"), ID_GENERAL_OPTIONS),
                    (_("Black list"), ID_DOWNLOAD_OPTIONS),
                ),
            ),
        )
        return menu

    def realize(self):
        """No-op realization method for compatibility."""
        pass


# Backward compatibility alias for renamed class
EmpytControl = EmptyControl
