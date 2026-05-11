"""Tests for pytigon_gui.guictrl.tag - re-export shim module.

Verifies that the backward-compatibility shim correctly re-exports
classes, functions, and globals from the refactored submodules.
"""

import pytest


class TestTagShim:
    """Verify tag.py correctly re-exports all expected symbols."""

    def test_imports_tree_parsers(self):
        """tag.py re-exports TreeList, TreeUl, TreeLi, Data, OptionTag,
        CompositeChildTag from tag_parsers."""
        from pytigon_gui.guictrl.tag import (
            TreeList,
            TreeUl,
            TreeLi,
            Data,
            OptionTag,
            CompositeChildTag,
        )

        from pytigon_gui.guictrl.tag_parsers import (
            TreeList as TL2,
            TreeUl as TU2,
            TreeLi as TLi2,
            Data as D2,
            OptionTag as OT2,
            CompositeChildTag as CCT2,
        )

        assert TreeList is TL2
        assert TreeUl is TU2
        assert TreeLi is TLi2
        assert Data is D2
        assert OptionTag is OT2
        assert CompositeChildTag is CCT2

    def test_imports_ctrl_tag(self):
        """tag.py re-exports CtrlTag, ComponentTag, _ATTRIBUTES
        from tag_ctrltag."""
        from pytigon_gui.guictrl.tag import CtrlTag, ComponentTag, _ATTRIBUTES

        from pytigon_gui.guictrl.tag_ctrltag import (
            CtrlTag as CT2,
            ComponentTag as CpT2,
            _ATTRIBUTES as A2,
        )

        assert CtrlTag is CT2
        assert ComponentTag is CpT2
        assert _ATTRIBUTES is A2

    def test_imports_preprocess(self):
        """tag.py re-exports preprocess globals from tag_preprocess."""
        from pytigon_gui.guictrl.tag import (
            SCHTYPE_MAP,
            HIDDEN_DIVS,
            table_to_ctrltab,
            input_to_ctrltab,
            textarea_to_ctrltab,
            select_to_ctrltab,
            a_to_button,
            div_convert,
            label_to_th,
            error_span_to_error,
            error_p_to_error,
            ul_convert,
            component_convert,
        )

        # Just verify they are callable or dict-like
        assert isinstance(SCHTYPE_MAP, dict)
        assert isinstance(HIDDEN_DIVS, list)
        assert callable(table_to_ctrltab)
        assert callable(input_to_ctrltab)
        assert callable(textarea_to_ctrltab)
        assert callable(select_to_ctrltab)
        assert callable(a_to_button)
        assert callable(div_convert)
        assert callable(label_to_th)
        assert callable(error_span_to_error)
        assert callable(error_p_to_error)
        assert callable(ul_convert)
        assert callable(component_convert)


class TestCtrlShim:
    """Verify ctrl.py correctly re-exports widget classes and factories."""

    def test_imports_basectrl(self):
        """ctrl.py re-exports SchBaseCtrl and handle_best_size."""
        from pytigon_gui.guictrl.ctrl import SchBaseCtrl, handle_best_size
        from pytigon_gui.guictrl.basectrl import (
            SchBaseCtrl as SBC2,
            handle_best_size as HBS2,
        )

        assert SchBaseCtrl is SBC2
        assert handle_best_size is HBS2

    def test_imports_button_classes(self):
        """ctrl.py re-exports button widget classes."""
        from pytigon_gui.guictrl.ctrl import (
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

        # Verify they are classes
        assert isinstance(SIMPLE_BUTTON, type)
        assert isinstance(BITMAPBUTTON, type)

    def test_imports_input_classes(self):
        """ctrl.py re-exports input widget classes."""
        from pytigon_gui.guictrl.ctrl import TEXT, PASSWORD, SEARCH, NUM, AMOUNT, FLOAT

        assert isinstance(TEXT, type)
        assert isinstance(PASSWORD, type)
        assert isinstance(NUM, type)

    def test_imports_choice_classes(self):
        """ctrl.py re-exports choice widget classes."""
        from pytigon_gui.guictrl.ctrl import CHECKBOX, LISTBOX, LIST

        assert isinstance(CHECKBOX, type)
        assert isinstance(LISTBOX, type)

    def test_imports_combo_classes(self):
        """ctrl.py re-exports combo widget classes."""
        from pytigon_gui.guictrl.ctrl import BITMAPCOMBOBOX, CHOICE, DBCHOICE

        assert isinstance(CHOICE, type)

    def test_imports_datetime_classes(self):
        """ctrl.py re-exports datetime widget classes."""
        from pytigon_gui.guictrl.ctrl import CALENDAR, DATEPICKER, TIME

        assert isinstance(CALENDAR, type)

    def test_imports_display_classes(self):
        """ctrl.py re-exports display widget classes."""
        from pytigon_gui.guictrl.ctrl import STATICTEXT, TREE, TREELIST, POPUPHTML

        assert isinstance(STATICTEXT, type)
        assert isinstance(TREE, type)

    def test_imports_panel_classes(self):
        """ctrl.py re-exports panel widget classes."""
        from pytigon_gui.guictrl.ctrl import HTML, NOTEBOOK, COLLAPSIBLE_PANEL

        assert isinstance(HTML, type)
        assert isinstance(NOTEBOOK, type)

    def test_imports_grid_classes(self):
        """ctrl.py re-exports grid widget classes."""
        from pytigon_gui.guictrl.ctrl import TABLE, GRID, UPDATEGRIDBUTTON

        assert isinstance(TABLE, type)
        assert isinstance(GRID, type)

    def test_imports_factory_functions(self):
        """ctrl.py re-exports factory functions."""
        from pytigon_gui.guictrl.ctrl import SELECT, BUTTON, TEXTAREA, SELECT2

        assert callable(SELECT)
        assert callable(BUTTON)
        assert callable(TEXTAREA)
        assert callable(SELECT2)

    def test_html2_is_none(self):
        """HTML2 is initially None (set by plugins at runtime)."""
        from pytigon_gui.guictrl.ctrl import HTML2

        assert HTML2 is None

    def test_imports_toolbarbutton(self):
        """ctrl.py re-exports BitmapTextButton."""
        from pytigon_gui.guictrl.ctrl import BitmapTextButton
        from pytigon_gui.guictrl.button.toolbarbutton import (
            BitmapTextButton as BMTB2,
        )

        assert BitmapTextButton is BMTB2
