"""
Backward-compatibility shim for pytigon_gui.guictrl.ctrl.

This module re-exports all widget classes and factory functions from
the refactored submodules so that existing code relying on:

    import pytigon_gui.guictrl.ctrl as schctrl

continues to work unchanged. The actual implementations now live in:

    guictrl/button/base.py     - Button classes and factories
    guictrl/input/text.py      - TEXT, PASSWORD, SEARCH, STYLEDTEXT, MASKTEXT
    guictrl/input/numeric.py   - NUM, AMOUNT, FLOAT, SPIN, SLIDER, GAUGE, TICKER,
                                 PROGRESSDIALOG
    guictrl/input/choice.py    - CHECKBOX, CHECKLISTBOX, LISTBOX, LIST, CHECKLIST,
                                 RADIOBOX, RADIOBUTTON
    guictrl/input/combo.py     - BITMAPCOMBOBOX, CHOICE, DBCHOICE, DBCHOICE_EXT,
                                 COMBOBOX, OWNERDRAWNCOMBOBOX
    guictrl/input/datetime.py  - CALENDAR, DATEPICKER, DATETIMEPICKER, TIME
    guictrl/input/toggle.py    - TOGGLEBUTTON, BITMAPTOGGLEBUTTON
    guictrl/input/richtext.py  - RICHTEXT
    guictrl/display.py         - STATICTEXT, ERRORLIST, TREE, TREELIST,
                                 COLOURSELECT, GENERICDIR, EDITABLELISTBOX,
                                 FILEBROWSEBUTTON, IMAGEBROWSEBUTTON,
                                 HTMLLISTBOX, POPUPHTML, STATICBITMAP,
                                 STATICLINE, HYPERLINK
    guictrl/panels.py          - HTML, NOTEBOOK, COLLAPSIBLE_PANEL, STATICBOX,
                                 CompositePanel
    guictrl/grids.py           - TABLE, GRID, UPDATEGRIDBUTTON
    guictrl/factory.py         - SELECT, BUTTON, TEXTAREA, SELECT2,
                                 COMPOSITE, COMPONENT

NOTE: This module's namespace is dynamically extended by plugins at
runtime (e.g. HTML2, COMPONENT, STYLEDTEXT, AUTOCOMPLETE, etc. may be
replaced). Keep this file as a thin shim to preserve that capability.
"""

# ---------------------------------------------------------------------------
# Re-export all widget classes and factory functions from submodules.
# Order matters: base classes first, then widgets grouped by category.
# ---------------------------------------------------------------------------

# Base classes (used by plugins via 'from pytigon_gui.guictrl.ctrl import SchBaseCtrl')
from pytigon_gui.guictrl.basectrl import SchBaseCtrl, handle_best_size

# Button classes
from pytigon_gui.guictrl.button.base import (
    BITMAPBUTTON,
    CLOSEBUTTON,
    GENBITMAPBUTTON,
    GENBITMAPBUTTONTXT,
    GENBITMAPBUTTONTXT_SMALL,
    GENBITMAPTEXTBUTTON,
    MENUBUTTON,
    MENUTOOLBARBUTTON,
    NOBG_BUTTON,
    NOBG_BUTTON_TXT,
    PLATEBUTTON,
    SIMPLE_BUTTON,
)

# Toolbar button (kept for direct compatibility)
from pytigon_gui.guictrl.button.toolbarbutton import BitmapTextButton

# Display / popup widgets
from pytigon_gui.guictrl.display import (
    COLOURSELECT,
    EDITABLELISTBOX,
    ERRORLIST,
    FILEBROWSEBUTTON,
    GENERICDIR,
    HTMLLISTBOX,
    HYPERLINK,
    IMAGEBROWSEBUTTON,
    POPUPHTML,
    STATICBITMAP,
    STATICLINE,
    STATICTEXT,
    TREE,
    TREELIST,
)

# Factory / dispatch functions
from pytigon_gui.guictrl.factory import (
    BUTTON,
    COMPONENT,
    COMPOSITE,
    SELECT,
    SELECT2,
    TEXTAREA,
)

# Grid / table widgets
from pytigon_gui.guictrl.grids import (
    GRID,
    TABLE,
    UPDATEGRIDBUTTON,
)

# Choice / selection widgets
from pytigon_gui.guictrl.input.choice import (
    CHECKBOX,
    CHECKLIST,
    CHECKLISTBOX,
    LIST,
    LISTBOX,
    RADIOBOX,
    RADIOBUTTON,
)

# Combo box / database choice widgets
from pytigon_gui.guictrl.input.combo import (
    BITMAPCOMBOBOX,
    CHOICE,
    COMBOBOX,
    DBCHOICE,
    DBCHOICE_EXT,
    OWNERDRAWNCOMBOBOX,
)

# Date / time widgets
from pytigon_gui.guictrl.input.datetime import (
    CALENDAR,
    DATEPICKER,
    DATETIMEPICKER,
    TIME,
)

# Numeric / value widgets
from pytigon_gui.guictrl.input.numeric import (
    AMOUNT,
    FLOAT,
    GAUGE,
    NUM,
    PROGRESSDIALOG,
    SLIDER,
    SPIN,
    TICKER,
)

# Rich text widgets
from pytigon_gui.guictrl.input.richtext import RICHTEXT

# Text input widgets
from pytigon_gui.guictrl.input.text import (
    AUTOCOMPLETE,
    MASKTEXT,
    PASSWORD,
    SEARCH,
    STANDARDSTYLEDTEXT,
    STYLEDTEXT,
    TEXT,
)

# Toggle button widgets
from pytigon_gui.guictrl.input.toggle import (
    BITMAPTOGGLEBUTTON,
    TOGGLEBUTTON,
)

# Panel / container widgets
from pytigon_gui.guictrl.panels import (
    COLLAPSIBLE_PANEL,
    HTML,
    NOTEBOOK,
    STATICBOX,
    CompositePanel,
)

# ---------------------------------------------------------------------------
# Runtime-extensible globals
# These are dynamically assigned by plugins at startup.
# ---------------------------------------------------------------------------

HTML2 = None
"""Set by webview plugins (cef, wxwebview) to provide an HTML2 viewer class."""
