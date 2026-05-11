"""
Backward-compatibility shim for pytigon_gui.guictrl.ctrl.

This module re-exports all widget classes and factory functions from
the refactored submodules so that existing code relying on:

    import pytigon_gui.guictrl.ctrl as schctrl

continues to work unchanged. The actual implementations now live in:

    guictrl/button/base.py     - Button classes and factories
    guictrl/input/text.py      - TEXT, PASSWORD, SEARCH, STYLEDTEXT, MASKTEXT
    guictrl/input/numeric.py   - NUM, AMOUNT, FLOAT, SPIN, SLIDER, GAUGE, TICKER
    guictrl/input/choice.py    - CHECKBOX, CHECKLISTBOX, LISTBOX, LIST, CHECKLIST,
                                 RADIOBOX, RADIOBUTTON
    guictrl/input/combo.py     - BITMAPCOMBOBOX, CHOICE, DBCHOICE, DBCHOICE_EXT
    guictrl/input/datetime.py  - CALENDAR, DATEPICKER, DATETIMEPICKER, TIME
    guictrl/display.py         - STATICTEXT, ERRORLIST, TREE, TREELIST,
                                 COLOURSELECT, GENERICDIR, EDITABLELISTBOX,
                                 FILEBROWSEBUTTON, IMAGEBROWSEBUTTON,
                                 HTMLLISTBOX, POPUPHTML
    guictrl/panels.py          - HTML, NOTEBOOK, COLLAPSIBLE_PANEL, CompositePanel
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

# Text input widgets
from pytigon_gui.guictrl.input.text import (
    TEXT,
    PASSWORD,
    SEARCH,
    STYLEDTEXT,
    MASKTEXT,
    AUTOCOMPLETE,
    STANDARDSTYLEDTEXT,
)

# Numeric / value widgets
from pytigon_gui.guictrl.input.numeric import (
    NUM,
    AMOUNT,
    FLOAT,
    SPIN,
    SLIDER,
    GAUGE,
    TICKER,
)

# Choice / selection widgets
from pytigon_gui.guictrl.input.choice import (
    CHECKBOX,
    CHECKLISTBOX,
    LISTBOX,
    LIST,
    CHECKLIST,
    RADIOBOX,
    RADIOBUTTON,
)

# Combo box / database choice widgets
from pytigon_gui.guictrl.input.combo import (
    BITMAPCOMBOBOX,
    CHOICE,
    DBCHOICE,
    DBCHOICE_EXT,
)

# Date / time widgets
from pytigon_gui.guictrl.input.datetime import (
    CALENDAR,
    DATEPICKER,
    DATETIMEPICKER,
    TIME,
)

# Display / popup widgets
from pytigon_gui.guictrl.display import (
    STATICTEXT,
    ERRORLIST,
    TREE,
    TREELIST,
    COLOURSELECT,
    GENERICDIR,
    EDITABLELISTBOX,
    FILEBROWSEBUTTON,
    IMAGEBROWSEBUTTON,
    HTMLLISTBOX,
    POPUPHTML,
)

# Panel / container widgets
from pytigon_gui.guictrl.panels import (
    HTML,
    NOTEBOOK,
    COLLAPSIBLE_PANEL,
    CompositePanel,
)

# Grid / table widgets
from pytigon_gui.guictrl.grids import (
    TABLE,
    GRID,
    UPDATEGRIDBUTTON,
)

# Factory / dispatch functions
from pytigon_gui.guictrl.factory import (
    SELECT,
    BUTTON,
    TEXTAREA,
    SELECT2,
    COMPOSITE,
    COMPONENT,
)

# Toolbar button (kept for direct compatibility)
from pytigon_gui.guictrl.button.toolbarbutton import BitmapTextButton

# ---------------------------------------------------------------------------
# Runtime-extensible globals
# These are dynamically assigned by plugins at startup.
# ---------------------------------------------------------------------------

HTML2 = None
"""Set by webview plugins (cef, wxwebview) to provide an HTML2 viewer class."""
