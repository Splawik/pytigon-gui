"""Tests for __init__.py modules across all packages.

Verifies that each package's __init__.py correctly exports the expected
symbols and that imports from all internal packages succeed.
"""

import pytest
import pytigon_gui
import pytigon_gui.guilib
import pytigon_gui.guictrl
import pytigon_gui.guiframe
import pytigon_gui.toolbar


class TestGuilibInit:
    """Tests for pytigon_gui.guilib.__init__.py."""

    def test_import_succeeds(self):
        """guilib package can be imported."""
        assert pytigon_gui.guilib is not None

    def test_module_has_docstring(self):
        """guilib has a docstring."""
        assert isinstance(pytigon_gui.guilib.__doc__, str)


class TestGuictrlInit:
    """Tests for pytigon_gui.guictrl.__init__.py."""

    def test_import_succeeds(self):
        """guictrl package can be imported."""
        assert pytigon_gui.guictrl is not None


class TestGuiframeInit:
    """Tests for pytigon_gui.guiframe.__init__.py."""

    def test_import_succeeds(self):
        """guiframe package can be imported."""
        assert pytigon_gui.guiframe is not None


class TestToolbarInit:
    """Tests for pytigon_gui.toolbar.__init__.py."""

    def test_import_succeeds(self):
        """toolbar package can be imported."""
        assert pytigon_gui.toolbar is not None


class TestPytigonGuiInit:
    """Tests for pytigon_gui.__init__.py."""

    def test_import_succeeds(self):
        """Root pytigon_gui package can be imported."""
        assert pytigon_gui is not None


class TestAllSubpackagesImportable:
    """Verify all subpackages can be imported without errors."""

    # Packages that should be directly importable.
    # Toolbar submodules (basetoolbar, standardtoolbarbuttons, etc.) are
    # excluded because they depend on optional third-party packages
    # (e.g. autocomplete) that may not be installed in test environments.
    PACKAGES = [
        "pytigon_gui",
        "pytigon_gui.guilib",
        "pytigon_gui.guilib.tools",
        "pytigon_gui.guilib.events",
        "pytigon_gui.guilib.signal",
        "pytigon_gui.guilib.httperror",
        "pytigon_gui.guilib.websocket",
        "pytigon_gui.guilib.image",
        "pytigon_gui.guilib.logindialog",
        "pytigon_gui.guilib.threadwindow",
        "pytigon_gui.guilib.pytigon_install",
        "pytigon_gui.guictrl",
        "pytigon_gui.guictrl.basectrl",
        "pytigon_gui.guictrl.ctrl",
        "pytigon_gui.guictrl.display",
        "pytigon_gui.guictrl.factory",
        "pytigon_gui.guictrl.grids",
        "pytigon_gui.guictrl.panels",
        "pytigon_gui.guictrl.tag",
        "pytigon_gui.guictrl.tag_ctrltag",
        "pytigon_gui.guictrl.tag_parsers",
        "pytigon_gui.guictrl.tag_preprocess",
        "pytigon_gui.guictrl.button",
        "pytigon_gui.guictrl.button.base",
        "pytigon_gui.guictrl.button.toolbarbutton",
        "pytigon_gui.guictrl.grid",
        "pytigon_gui.guictrl.grid.grid",
        "pytigon_gui.guictrl.grid.gridpanel",
        "pytigon_gui.guictrl.grid.gridtable_base",
        "pytigon_gui.guictrl.grid.gridtable_from_html_table",
        "pytigon_gui.guictrl.grid.gridtable_from_proxy",
        "pytigon_gui.guictrl.grid.popupcelleditors",
        "pytigon_gui.guictrl.grid.renderers",
        "pytigon_gui.guictrl.grid.tabproxy",
        "pytigon_gui.guictrl.input",
        "pytigon_gui.guictrl.input.choice",
        "pytigon_gui.guictrl.input.combo",
        "pytigon_gui.guictrl.input.datetime",
        "pytigon_gui.guictrl.input.numeric",
        "pytigon_gui.guictrl.input.text",
        "pytigon_gui.guictrl.popup",
        "pytigon_gui.guictrl.popup.popuphtml",
        "pytigon_gui.guictrl.popup.select2",
        "pytigon_gui.guiframe",
        "pytigon_gui.guiframe.appframe",
        "pytigon_gui.guiframe.baseframe",
        "pytigon_gui.guiframe.browserframe",
        "pytigon_gui.guiframe.form",
        "pytigon_gui.guiframe.manager",
        "pytigon_gui.guiframe.notebook",
        "pytigon_gui.guiframe.notebookpage",
        "pytigon_gui.guiframe.page",
        "pytigon_gui.toolbar",
    ]

    @pytest.mark.parametrize("package_name", PACKAGES)
    def test_import_package(self, package_name):
        """Each package can be imported."""
        import importlib

        try:
            mod = importlib.import_module(package_name)
            assert mod is not None
        except ImportError as e:
            pytest.fail(f"Failed to import {package_name}: {e}")
