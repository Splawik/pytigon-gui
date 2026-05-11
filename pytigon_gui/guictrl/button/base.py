"""
Button widget classes for the SchForm GUI framework.

Provides factory functions that create wxPython button subclasses
integrated with the SchBaseCtrl mixin. All button classes are
created dynamically through factory functions to reduce code
duplication while allowing each button type to customize its
behavior (bitmap handling, close behavior, menu handling, etc.).

Classes:
    SIMPLE_BUTTON, BITMAPBUTTON, PLATEBUTTON,
    GENBITMAPBUTTON, GENBITMAPTEXTBUTTON, GENBITMAPBUTTONTXT,
    GENBITMAPBUTTONTXT_SMALL, NOBG_BUTTON, NOBG_BUTTON_TXT,
    CLOSEBUTTON, MENUBUTTON, MENUTOOLBARBUTTON

Factory functions:
    _make_button_class, _make_menu_button_class
"""

import wx
from wx.adv import BitmapComboBox
import wx.lib.platebtn as platebtn
import wx.lib.buttons as buttons

from pytigon_gui.guictrl.basectrl import SchBaseCtrl
from pytigon_gui.guictrl.button.toolbarbutton import BitmapTextButton
from pytigon_gui.guilib.image import bitmap_from_href


def _make_button_class(
    base_class, is_bitmap_button=False, is_close_button=False, icon_size=2
):
    """Create a button widget class dynamically.

    This factory generates a class that inherits from both a wxPython
    button base class and SchBaseCtrl. It handles bitmap loading,
    label parsing for accelerators (via '&' prefix), default button
    behavior, tooltip generation, and click/close event binding.

    Args:
        base_class: The wxPython button class to subclass
            (e.g. wx.Button, wx.BitmapButton, platebtn.PlateButton).
        is_bitmap_button: If True, loads a bitmap from the 'src'
            attribute and configures the button accordingly.
        is_close_button: If True, binds the button to an exit/close
            handler instead of the standard click handler.
        icon_size: Size index passed to bitmap_from_href (2=normal, 1=small).

    Returns:
        A new class combining base_class and SchBaseCtrl with button
        behavior customized according to the parameters.
    """

    class _ButtonClass(base_class, SchBaseCtrl):
        """Dynamically generated button widget class.

        Inherits from a wxPython button base class and SchBaseCtrl.
        Provides unified handling for bitmap buttons, labeled buttons,
        accelerator keys, tooltips, default button behavior, and
        click/close events.
        """

        def __init__(self, parent, **kwds):
            """Initialize the button widget.

            Sets up bitmap (if applicable), label, accelerator keys,
            tooltips, and default button behavior before delegating
            to the wxPython base class constructor.

            Args:
                parent: Parent window.
                **kwds: Keyword arguments forwarded to the base class.
                    May include 'style', 'fields', 'bitmap', 'bmp',
                    'label', 'id', etc.
            """
            SchBaseCtrl.__init__(self, parent, kwds)

            if is_bitmap_button:
                self._set_bitmap()
                if base_class in (buttons.GenBitmapButton, BitmapTextButton):
                    if "style" in kwds:
                        style = kwds["style"] | wx.NO_BORDER
                        kwds["style"] = style
                    else:
                        style = wx.NO_BORDER
                        kwds["style"] = wx.NO_BORDER
                    kwds["bitmap"] = self.bmp
                elif base_class == buttons.GenBitmapTextButton:
                    kwds["bitmap"] = self.bmp
                elif base_class == platebtn.PlateButton:
                    kwds["style"] = (
                        platebtn.PB_STYLE_SQUARE | platebtn.PB_STYLE_GRADIENT
                    )
                    kwds["bmp"] = self.bmp
                else:
                    if "style" not in kwds:
                        kwds["style"] = 0
                    kwds["bitmap"] = self.bmp

                # GenBitmapButton/BitmapTextButton/GenBitmapTextButton
                # use 'label' kwarg; wx.BitmapButton does not.
                if base_class not in (wx.BitmapButton,):
                    if self.label:
                        kwds["label"] = self.label.replace("&", "")
            else:
                if "style" not in kwds:
                    kwds["style"] = 0
                if self.label:
                    kwds["label"] = self.label.replace("&", "")
                # Support numeric or symbolic wx.Window ID.
                # NOTE: Using truthiness check for nr_id means value 0
                # (a valid wx.ID) is treated as None. In practice, nr_id
                # values are strings like "wx.ID_OK" or positive integers.
                if self.nr_id:
                    try:
                        nr_id = int(self.nr_id)
                    except (ValueError, TypeError):
                        if isinstance(self.nr_id, str) and "wx." in self.nr_id:
                            nr_id = eval(self.nr_id)
                        else:
                            nr_id = None
                    if nr_id is not None:
                        kwds["id"] = nr_id

            # Store fields for form submission context
            if "fields" in kwds:
                self.fields = kwds["fields"]
                del kwds["fields"]
            else:
                self.fields = None

            base_class.__init__(self, parent, **kwds)

            # Set as default button if configured
            if self.defaultvalue:
                self.SetDefault()
                self.parent.any_parent_command("set_default_button", self)

            # Tooltip from label for bitmap buttons
            if is_bitmap_button and self.label:
                self.SetToolTip(self.label.replace("&", ""))

            # Bind appropriate event handler
            if is_close_button:
                self.Bind(wx.EVT_BUTTON, self._on_exit)
            else:
                self.Bind(wx.EVT_BUTTON, self._on_click, self)

            # Additional tooltip for BitmapTextButton
            if self.label and base_class == BitmapTextButton:
                self.SetToolTip(wx.ToolTip(self.label.replace("&", "")))

            # Register accelerator key from '&' prefix in label
            if self.label and "&" in self.label:
                amp_pos = self.label.find("&")
                accel_char = self.label[amp_pos + 1 : amp_pos + 2]
                if accel_char:
                    accel_table = [
                        (wx.ACCEL_ALT, ord(accel_char.upper()), self._on_acc_click),
                    ]
                    self.set_acc_key_tab(accel_table)

            self.init2()

        def _on_acc_click(self, event):
            """Handle accelerator key press by posting a button click event.

            Args:
                event: The key event (unused; a synthetic button event
                    is posted instead).
            """
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            wx.PostEvent(self, evt)

        def _set_bitmap(self):
            """Load the button bitmap from the configured source.

            For close buttons, uses a default 'unreadable' emblem if
            no source is specified. Delegates to bitmap_from_href for
            icon loading.
            """
            self.bmp = None
            if is_bitmap_button:
                if is_close_button:
                    self.src = "png://emblems/emblem-unreadable.png"
                if self.src:
                    self.bmp = bitmap_from_href(self.src, icon_size)

        def process_refr_data(self, **kwds):
            """Refresh the button's data from new keyword arguments.

            Re-initializes base attributes, reloads the bitmap,
            updates fields/href, and reapplies default button state.

            Args:
                **kwds: New keyword arguments (may include 'fields',
                    'href', etc.).
            """
            self.init_base(kwds)

            if is_bitmap_button:
                self._set_bitmap()
                if base_class == platebtn.PlateButton:
                    kwds["bmp"] = self.bmp
                else:
                    kwds["bitmap"] = self.bmp

            if "fields" in kwds:
                self.fields = kwds["fields"]
                del kwds["fields"]
            else:
                self.fields = None

            if "href" in kwds:
                self.href = kwds["href"]
                del kwds["href"]

            if self.defaultvalue:
                self.SetDefault()

            self.init2()

        def init2(self):
            """Apply visibility and enable state based on href settings.

            Special href values:
                '_hide': Hide the button.
                '_disable': Disable the button.
            """
            if self.href == "_hide":
                self.Hide()
            else:
                self.Show()
            if self.href == "_disable":
                self.Enable(False)
            else:
                self.Enable(True)
            if not self.style:
                self.style = 0

        def CanAcceptFocus(self):
            """Buttons do not accept keyboard focus by default.

            Returns:
                False always, preventing the button from receiving
                keyboard focus.
            """
            return False

        if is_close_button:

            def _on_exit(self, event):
                """Handle close button click by canceling the child form.

                Uses wx.CallAfter to defer the cancel operation to
                avoid reentrancy issues.

                Args:
                    event: The button click event (unused).
                """

                def _cancel_form():
                    self.GetParent().any_parent_command("on_child_form_cancel")

                wx.CallAfter(_cancel_form)

        else:

            def _on_click(self, event):
                """Handle standard button click by navigating to href.

                If valuetype is 'upload', the click triggers an upload
                action. Otherwise it navigates to the configured href
                target.

                Args:
                    event: The button click event.
                """
                upload = self.valuetype == "upload"
                href = getattr(self, "href", "")
                self.get_parent_form().href_clicked(
                    self,
                    {"href": href, "target": self.target},
                    upload,
                    self.fields,
                )

    return _ButtonClass


# Concrete button classes generated by the factory.
# These are the public UPPERCASE interface names used by tag.py
# and other modules to instantiate button widgets.

SIMPLE_BUTTON = _make_button_class(wx.Button)
"""Standard push button without bitmap."""

BITMAPBUTTON = _make_button_class(wx.BitmapButton, is_bitmap_button=True)
"""Button with a bitmap, based on wx.BitmapButton."""

PLATEBUTTON = _make_button_class(platebtn.PlateButton, is_bitmap_button=True)
"""Styled plate button with gradient background and bitmap."""

GENBITMAPBUTTON = _make_button_class(buttons.GenBitmapButton, is_bitmap_button=True)
"""Generic bitmap button with no border."""

GENBITMAPTEXTBUTTON = _make_button_class(
    buttons.GenBitmapTextButton, is_bitmap_button=True
)
"""Generic bitmap button with text label."""

GENBITMAPBUTTONTXT = _make_button_class(BitmapTextButton, is_bitmap_button=True)
"""Bitmap text button (normal icon size)."""

GENBITMAPBUTTONTXT_SMALL = _make_button_class(
    BitmapTextButton, is_bitmap_button=True, icon_size=1
)
"""Bitmap text button (small icon size)."""

# Aliases for compatibility
NOBG_BUTTON = GENBITMAPBUTTONTXT
"""Alias for a button without background (same as GENBITMAPBUTTONTXT)."""

NOBG_BUTTON_TXT = GENBITMAPBUTTONTXT
"""Alias for a text button without background."""

CLOSEBUTTON = _make_button_class(
    BitmapTextButton, is_bitmap_button=True, is_close_button=True
)
"""Close button that cancels the child form when clicked."""


def _make_menu_button_class(base_class):
    """Create a menu-button widget class dynamically.

    Generates a class that displays a popup menu when clicked.
    The menu items are built from the control's list data (ldata).
    Each item's label and href are extracted from the list data rows.

    Args:
        base_class: A button class (typically SIMPLE_BUTTON or
            GENBITMAPBUTTONTXT) that this menu button will extend.

    Returns:
        A new class that acts as a button with an associated popup menu.
    """

    class _MenuButton(base_class):
        """Button that displays a popup menu on click.

        Menu items are constructed from the control's ldata.
        Each row in ldata provides [label, children, attrs];
        the label and attrs['href'] define each menu item.
        Rows with empty/dash-only labels become separators.
        """

        def __init__(self, parent, **kwds):
            """Initialize the menu button.

            Builds the wx.Menu from ldata and binds menu/button events.

            Args:
                parent: Parent window.
                **kwds: Keyword arguments forwarded to the base class.
            """
            base_class.__init__(self, parent, **kwds)
            ldata = self.get_ldata()
            self._menu = None
            self._href_dict = {}
            if ldata:
                menu = wx.Menu()
                for row in ldata:
                    label = row[0].replace("-", "").strip()
                    if label:
                        menu.Append(wx.ID_ANY, label, row[2]["href"])
                        self._href_dict[label] = row[2]
                    else:
                        menu.AppendSeparator()
                self.SetMenu(menu)

            self.Bind(wx.EVT_MENU, self._on_menu)
            self.Bind(wx.EVT_BUTTON, self._on_button)

        def _on_button(self, evt):
            """Show the popup menu when the button is pressed.

            Args:
                evt: The button click event.
            """
            self.ShowMenu()

        def _on_menu(self, evt):
            """Handle menu item selection by navigating to the href.

            Args:
                evt: The menu selection event.
            """
            e_obj = evt.GetEventObject()
            mitem = e_obj.FindItemById(evt.GetId())
            if mitem != wx.NOT_FOUND:
                label = mitem.GetItemLabel()
                item = self._href_dict[label]
                self.GetParent().href_clicked(self, item)

        def SetMenu(self, menu):
            """Store the popup menu for later display.

            Args:
                menu: A wx.Menu instance.
            """
            self._menu = menu

        def ShowMenu(self):
            """Display the popup menu below the button."""
            self.PopupMenu(self._menu, 1, self.GetSize()[1] - 1)

    return _MenuButton


MENUBUTTON = _make_menu_button_class(SIMPLE_BUTTON)
"""Menu button based on a simple push button."""

MENUTOOLBARBUTTON = _make_menu_button_class(GENBITMAPBUTTONTXT)
"""Menu button styled as a toolbar button with bitmap and text."""
