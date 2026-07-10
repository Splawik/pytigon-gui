"""
Base classes for toolbars and menu bar.

Class hierarchy:
    ToolbarBar
        ToolbarPage
            ToolbarPanel
                ToolbarButton
                ToolbarButton
                ...
            ToolbarPanel
            ...
            BaseHtmlPanel
        ...

One ToolbarBar can contain many ToolbarPage objects, one ToolbarPage can
contain many ToolbarPanel objects, etc.

Concrete toolbars and menus based on these abstract classes:
    - MenuToolbarBar
    - GenericToolbarBar
    - StandardToolbarBar
    - ModernToolbarBar
    - TreeToolbarBar
"""

import wx

from pytigon_gui.guilib.events import *
from pytigon_gui.toolbar.standardtoolbarbuttons import StandardButtons
from pytigon_gui.guiframe.page import SchPage

_ = wx.GetTranslation


class BaseHtmlPanel:
    """Base panel that can host an HTML-rendered page within a toolbar.

    This is used by toolbar types that support embedding web content
    (e.g. ModernToolbarBar, TreeToolbarBar).
    """

    def __init__(self, page, real_panel):
        """Initialize the HTML panel wrapper.

        Args:
            page: Parent ToolbarPage object.
            real_panel: The actual wx.Panel that will contain the HTML page.
        """
        self.page = page
        self.real_panel = real_panel
        self.html_page = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.real_panel.SetSizer(self.sizer)

    def get_width(self):
        """Return the preferred width of the panel.

        Override in subclasses to provide actual dimensions.

        Returns:
            int: Width in pixels (0 by default).
        """
        return 0

    def get_height(self):
        """Return the preferred height of the panel.

        Override in subclasses to provide actual dimensions.

        Returns:
            int: Height in pixels (0 by default).
        """
        return 0

    def get_window(self):
        """Return the underlying wx.Window for this panel.

        Returns:
            wx.Window: The real panel window.
        """
        return self.real_panel

    def set_page(self, html_page):
        """Replace the current HTML page with a new one.

        If a page already exists, it is replaced in the sizer and destroyed.
        Otherwise the new page is added to the sizer.

        Args:
            html_page: The new SchPage (or wx.Window) to display.
        """
        if self.html_page:
            self.sizer.Replace(self.html_page, html_page)
            self.html_page.Destroy()
        else:
            self.sizer.Add(html_page, 0, wx.LEFT | wx.TOP | wx.EXPAND | wx.RIGHT, 2)

        self.html_page = html_page

        self.sizer.Fit(self.real_panel)


class ToolbarButton:
    """Represents a single button (or separator) on a toolbar panel.

    This is an abstract data model; the actual wx widget is created by
    the concrete toolbar implementation.

    Button type constants:
        TYPE_SIMPLE = 0     - Simple push button.
        TYPE_DROPDOWN = 1   - Button with a dropdown menu.
        TYPE_HYBRID = 2     - Hybrid button (part button, part dropdown).
        TYPE_TOOGLE = 3     - Toggle button.
        TYPE_PANEL = 4      - Embedded panel.
        TYPE_SEPARATOR = 5  - Visual separator.
    """

    TYPE_SIMPLE = 0
    TYPE_DROPDOWN = 1
    TYPE_HYBRID = 2
    TYPE_TOOGLE = 3
    TYPE_PANEL = 4
    TYPE_SEPARATOR = 5

    def __init__(
        self,
        parent_panel,
        id,
        title,
        bitmap=None,
        bitmap_disabled=None,
        kind=TYPE_SIMPLE,
    ):
        """Create a new toolbar button.

        Args:
            parent_panel: Parent ToolbarPanel object.
            id: An integer by which the tool may be identified.
            title: Button title (display text).
            bitmap: Button bitmap for the normal state.
            bitmap_disabled: Button bitmap for the disabled state.
                Defaults to wx.NullBitmap when bitmap is provided.
            kind: Type of button; one of the TYPE_* class constants.
        """
        self.parent_panel = parent_panel
        self.id = id
        self.title = title
        self.bitmap = bitmap
        if bitmap_disabled is None and bitmap is not None:
            self.bitmap_disabled = wx.NullBitmap
        else:
            self.bitmap_disabled = bitmap_disabled
        self.kind = kind


class ToolbarPanel:
    """A panel within a toolbar page that holds a group of buttons.

    Panel type constants:
        TYPE_PANEL_BUTTONBAR = 0  - Button bar layout.
        TYPE_PANEL_TOOLBAR = 1    - Toolbar layout.
        TYPE_PANEL_PANELBAR = 2   - Custom panel layout.
    """

    TYPE_PANEL_BUTTONBAR = 0
    TYPE_PANEL_TOOLBAR = 1
    TYPE_PANEL_PANELBAR = 2

    def __init__(self, parent_page, title, kind=TYPE_PANEL_BUTTONBAR):
        """Create a new toolbar panel.

        Args:
            parent_page: Parent ToolbarPage object.
            title: Panel title.
            kind: Type of panel; one of the TYPE_PANEL_* class constants.
        """
        self.parent_page = parent_page
        self.title = title
        self.kind = kind
        self.buttons = []

    def _transform_bitmaps_parm(self, bitmaps):
        """Convert a variadic bitmap list into a (normal, disabled) pair.

        Args:
            bitmaps: List of 0, 1, or 2 wx.Bitmap objects.

        Returns:
            list: [normal_bitmap_or_None, disabled_bitmap_or_None]
        """
        b = [None, None]
        if len(bitmaps) > 0:
            b[0] = bitmaps[0]
        if len(bitmaps) > 1:
            b[1] = bitmaps[1]
        return b

    def create_button(
        self,
        id,
        title,
        bitmap=None,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        """Create and return a new ToolbarButton.

        Override in derived classes to return a subclass of ToolbarButton.

        Args:
            id: An integer by which the tool may be identified.
            title: Button title.
            bitmap: Button bitmap for the normal state.
            bitmap_disabled: Button bitmap for the disabled state.
            kind: Type of button; one of ToolbarButton.TYPE_* constants.

        Returns:
            ToolbarButton: The newly created button.
        """
        return ToolbarButton(self, id, title, bitmap, bitmap_disabled, kind)

    def append(
        self,
        id,
        title,
        bitmap=None,
        bitmap_disabled=None,
        kind=ToolbarButton.TYPE_SIMPLE,
    ):
        """Create a button and append it to this panel.

        Args:
            id: An integer by which the tool may be identified.
            title: Button title.
            bitmap: Button bitmap for the normal state.
            bitmap_disabled: Button bitmap for the disabled state.
            kind: Type of button; one of ToolbarButton.TYPE_* constants.

        Returns:
            ToolbarButton: The newly created and appended button.
        """
        button = self.create_button(id, title, bitmap, bitmap_disabled, kind)
        self.buttons.append(button)
        return button

    def add_tool(self, id, title, bitmaps, kind):
        b = self._transform_bitmaps_parm(bitmaps)
        return self.append(id, title, b[0], b[1], kind=kind)

    def add_simple_tool(self, id, title, bitmaps):
        return self.add_tool(id, title, bitmaps, ToolbarButton.TYPE_SIMPLE)

    def add_dropdown_tool(self, id, title, bitmaps):
        return self.add_tool(id, title, bitmaps, ToolbarButton.TYPE_DROPDOWN)

    def add_hybrid_tool(self, id, title, bitmaps):
        return self.add_tool(id, title, bitmaps, ToolbarButton.TYPE_HYBRID)

    def add_toogle_tool(self, id, title, bitmaps):
        return self.add_tool(id, title, bitmaps, ToolbarButton.TYPE_TOOGLE)

    def add_separator(self):
        """Append a visual separator to the panel.

        The default implementation does nothing; override in subclasses.
        """
        pass


class ToolbarPage:
    """A page (tab) within a toolbar bar, containing one or more panels.

    Page type constants:
        TYPE_PAGE_NORMAL = 0  - Standard page.
    """

    TYPE_PAGE_NORMAL = 0

    def __init__(self, parent_bar, title, kind=TYPE_PAGE_NORMAL):
        """Create a new toolbar page.

        Args:
            parent_bar: Parent ToolbarBar object.
            title: Page title (will be translated via wx.GetTranslation).
            kind: Type of page; one of the TYPE_PAGE_* class constants.
        """
        self.parent_bar = parent_bar
        self.name = title
        self.title = _(title)
        self.kind = kind
        self.panels = []

    def create_panel(self, title, kind):
        """Create and return a new ToolbarPanel for this page.

        Override in derived classes to return a subclass of ToolbarPanel.

        Args:
            title: Panel title.
            kind: Type of panel; one of ToolbarPanel.TYPE_PANEL_* constants.

        Returns:
            ToolbarPanel: The newly created panel.
        """
        return ToolbarPanel(self, title, kind=ToolbarPanel.TYPE_PANEL_BUTTONBAR)

    def create_html_panel(self, title):
        """Create an HTML-capable panel within this page.

        Override in derived classes to return a BaseHtmlPanel subclass.

        Args:
            title: Panel title.

        Returns:
            BaseHtmlPanel or None: The panel, or None if not supported.
        """
        return None

    def append(self, title, kind=ToolbarPanel.TYPE_PANEL_BUTTONBAR):
        """Create a new panel and append it to this page.

        Args:
            title: Panel title.
            kind: Type of panel; one of ToolbarPanel.TYPE_PANEL_* constants.

        Returns:
            ToolbarPanel: The newly created panel.
        """
        p = self.create_panel(title, kind)
        self.panels.append(p)
        return p


class ToolbarBar:
    """Base class for all menus and toolbars connected to the top frame window.

    Manages a collection of ToolbarPage objects and provides common
    operations like binding events and creating standard buttons.
    """

    def __init__(self, parent, gui_style):
        """Initialize the toolbar bar.

        Args:
            parent: Parent window - the top wx.Frame derived object.
            gui_style: String description of the GUI interface. Based on
                this string, standard toolbar elements are created.
        """
        self.parent = parent
        self.main_page = None
        self.gui_style = gui_style

        self.toolbars = {}
        self.pages = []
        self.user_panels = {}

        self.standard_buttons = StandardButtons(self, gui_style)
        self.standard_buttons.create_file_panel(self.main_page)
        self.standard_buttons.create_edit_panel(self.main_page)
        self.standard_buttons.create_operations_panel(self.main_page)
        self.standard_buttons.create_browse_panel(self.main_page)
        self.standard_buttons.create_address_panel(self.main_page)

    def _find_page_by_title(self, title):
        """Find a page by its translated title.

        Args:
            title: The translated title to search for.

        Returns:
            ToolbarPage or None if not found.
        """
        for page in self.pages:
            if page.title == title:
                return page
        return None

    def create_page(self, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        """Create and return a new ToolbarPage.

        Override in derived classes to return a subclass of ToolbarPage.

        Args:
            title: Page title.
            kind: Type of page; one of ToolbarPage.TYPE_PAGE_* constants.

        Returns:
            ToolbarPage: The newly created page.
        """
        return ToolbarPage(self, title, kind)

    def remove_page(self, title):
        """Remove the page with the specified title from the toolbar.

        Args:
            title: Title of the page to remove.
        """
        # Remove from pages list
        for page in self.pages:
            if page.title == title:
                self.pages.remove(page)
                break

        # If the main page was removed, pick a new one
        if self.main_page and self.main_page.title == title:
            self.main_page = self.pages[0] if self.pages else None

        # Remove associated user panels (iterate over a static list of keys
        # to avoid "dictionary changed size during iteration" errors)
        for key in list(self.user_panels.keys()):
            panel = self.user_panels[key]
            if panel.page.title == title:
                del self.user_panels[key]
                return

    def append(self, title, kind=ToolbarPage.TYPE_PAGE_NORMAL):
        """Append a page to the toolbar, or return an existing one.

        If a page with the same name and kind already exists, it is
        returned instead of creating a duplicate.

        Args:
            title: Page title.
            kind: Type of page; one of ToolbarPage.TYPE_PAGE_* constants.

        Returns:
            ToolbarPage: The existing or newly created page.
        """
        for page in self.pages:
            if page.name == title and page.kind == kind:
                return page
        p = self.create_page(title, kind)
        if not self.main_page:
            self.main_page = p
        self.pages.append(p)
        return p

    def create(self):
        """Create/realize the toolbar.

        Override in subclasses to perform actual widget creation.
        """
        pass

    def close(self):
        """Close/destroy the toolbar.

        Override in subclasses to perform cleanup.
        """
        pass

    def create_panel_in_main_page(self, title, kind):
        """Create a panel in the main page.

        If no main page exists yet, one is created automatically.

        Args:
            title: New panel's title.
            kind: Type of panel; one of ToolbarPanel.TYPE_PANEL_* constants.

        Returns:
            ToolbarPanel: The newly created panel.
        """
        if not self.main_page:
            self.append("main tools")
        return self.main_page.create_panel(title, kind)

    def bind(self, fun, id=wx.ID_ANY, e=None):
        """Bind an event handler to the toolbar's parent window.

        Args:
            fun: Handler function.
            id: Identifier of the event.
            e: Event type; defaults to wx.EVT_MENU if not specified.
        """
        if e:
            self.parent.Bind(e, fun, id=id)
        else:
            self.parent.Bind(wx.EVT_MENU, fun, id=id)

    def un_bind(self, id=wx.ID_ANY, e=None):
        """Unbind an event handler from the toolbar's parent window.

        Args:
            id: Identifier of the event.
            e: Event type; defaults to wx.EVT_MENU if not specified.
        """
        if e:
            self.parent.Unbind(e, id=id)
        else:
            self.parent.Unbind(wx.EVT_MENU, id=id)

    def create_html_win(
        self, toolbar_page, address_or_parser, parameters, callback=None
    ):
        """Create an HTML page embedded in the toolbar.

        Not all toolbar types support this feature.

        Args:
            toolbar_page: Name of the toolbar page to host the HTML.
                Use '__' to separate page and panel names,
                e.g. 'PageName__PanelName'.
            address_or_parser: Address of the HTTP page or a parser.
            parameters: Parameters for the HTTP request.
            callback: Optional callback invoked after initialization.

        Returns:
            SchPage or None: The created page, or None on failure.
        """
        page = None
        if not toolbar_page:
            u_name = "main tools"
            page_name = _("main tools")
            panel_name = "main tools"
        else:
            u_name = toolbar_page
            names = toolbar_page.split("__")
            if len(names) > 1:
                page_name = names[0].replace("_", " ")
                panel_name = names[1].replace("_", " ")
            else:
                page_name = toolbar_page.replace("_", " ")
                panel_name = page_name

        if u_name in self.user_panels:
            panel = self.user_panels[u_name]
        else:
            page = self._find_page_by_title(page_name)
            if page is None:
                page = self.append(page_name)
            panel = page.create_html_panel(panel_name)

        if panel:
            dx = panel.get_width() + 3
            dy = panel.get_height() + 5

            page2 = SchPage(
                panel.get_window(),
                address_or_parser,
                parameters,
                size=wx.Size(dx, dy),
                pos=wx.Point(2, 2),
            )
            best = page2.body.calculate_best_size()
            page2.SetSize(wx.Size(int(best[0]), int(best[1])))
            panel.set_page(page2)
            self.user_panels[u_name] = panel
            page2.body.toolbar_interface = self
            page2.body.toolbar_interface_page = page

            def init_page(callback):
                page2.init_frame()
                page2.activate_page()
                page2.Update()

            wx.CallAfter(init_page, callback)

            return page2

        return None

    def new_child_page(self, address_or_parser, title="", param=None, callback=None):
        """Create a new child page.

        For toolbar, the child page is transferred to the desktop window.

        Args:
            address_or_parser: Address of the HTTP page or a parser.
            title: Page title.
            param: Optional parameters.
            callback: Optional callback.

        Returns:
            The result of new_main_page on the top window.
        """
        return wx.GetApp().GetTopWindow().new_main_page(address_or_parser, title, param)
