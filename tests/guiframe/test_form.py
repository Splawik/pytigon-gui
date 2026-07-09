"""Tests for pytigon_gui.guiframe.form - SchForm utility methods."""

import pytest
from unittest.mock import MagicMock


class TestSchFormUtilityMethods:

    def test_bestsize_property(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form._bestsize = None
        assert form.bestsize is None
        form.bestsize = (800, 600)
        assert form.bestsize == (800, 600)

    def test_set_css(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form.init_css_str = None
        form.set_css("body { color: red; }")
        assert form.init_css_str == "body { color: red; }"

    def test_enable_ctrls(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form._enabled_controls = False
        form.enable_ctrls(["ctrl1", "ctrl2"])
        assert form._enabled_controls == ["ctrl1", "ctrl2"]

    def test_is_ctrl_block_no_controls(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form._enabled_controls = False
        assert form.is_ctrl_block("any_ctrl") is True

    def test_is_ctrl_block_with_controls(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form._enabled_controls = ["allowed1", "allowed2"]
        assert form.is_ctrl_block("allowed1") is False
        assert form.is_ctrl_block("not_allowed") is True

    def test_set_best_size(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form._bestsize = None
        form.set_best_size((1024, 768))
        assert form._bestsize == (1024, 768)

    def test_set_htm_type(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form.form_type = None
        form.set_htm_type("footer")
        assert form.form_type == "footer"

    def test_get_parent_page(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        mock_page = MagicMock()
        form.page = mock_page
        assert form.get_parent_page() is mock_page

    def test_get_gparent_page(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        parent_page = MagicMock()
        grand_parent = MagicMock()
        parent_page.get_parent_page.return_value = grand_parent
        form.page = parent_page
        assert form.get_gparent_page() is grand_parent

    def test_get_gparent_page_none(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form.page = None
        assert form.get_gparent_page() is None

    def test_get_parent_form(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        gpage = MagicMock()
        gpage.active_form = "form1"
        page = MagicMock()
        page.get_parent_page.return_value = gpage
        form.page = page
        assert form.get_parent_form() == "form1"

    def test_get_parent_form_none(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        page = MagicMock()
        page.get_parent_page.return_value = None
        form.page = page
        assert form.get_parent_form() is None

    def test_set_address_parm_simple(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form.address = None
        form.set_address_parm("http://example.com/page/")
        assert form.address == "http://example.com/page/"

    def test_set_address_parm_no_trailing_slash(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form.address = None
        form.set_address_parm("http://example.com/page")
        assert form.address == "http://example.com/page/"

    def test_set_address_parm_with_params(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form.address = None
        form.set_address_parm("http://example.com/page|param1|param2")
        assert form.address == "http://example.com/page/|param1"

    def test_set_address_parm_none(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form.address = "existing"
        form.set_address_parm(None)
        assert form.address == "existing"

    def test_pre_process_page_no_handlers(self):
        from pytigon_gui.guiframe.form import SchForm, _PRE_PRECESS_LIB

        form = SchForm.__new__(SchForm)
        original = list(_PRE_PRECESS_LIB)
        _PRE_PRECESS_LIB.clear()

        result = form.pre_process_page("<html>test</html>")
        assert result == "<html>test</html>"

        _PRE_PRECESS_LIB[:] = original

    def test_pre_process_page_with_handler(self):
        from pytigon_gui.guiframe.form import SchForm, _PRE_PRECESS_LIB, install_pre_process_lib

        form = SchForm.__new__(SchForm)
        original = list(_PRE_PRECESS_LIB)
        _PRE_PRECESS_LIB.clear()

        def my_handler(f, page):
            return page.replace("test", "modified")

        install_pre_process_lib(my_handler)
        result = form.pre_process_page("<html>test</html>")
        assert result == "<html>modified</html>"

        _PRE_PRECESS_LIB[:] = original

    def test_signal_from_child(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form.signal_from_child("child", "signal_name")

    def test_set_acc_key_tab_new_win(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        form.acc_tabs = {}
        win = MagicMock()
        form.set_acc_key_tab(win, [("flags", "key", "handler")])
        assert win in form.acc_tabs
        assert form.acc_tabs[win] == [[("flags", "key", "handler")]]

    def test_set_acc_key_tab_existing_win(self):
        from pytigon_gui.guiframe.form import SchForm

        form = SchForm.__new__(SchForm)
        win = MagicMock()
        form.acc_tabs = {win: [["tab1"]]}
        form.set_acc_key_tab(win, ["tab2"])
        assert len(form.acc_tabs[win]) == 2

    def test_install_pre_process_lib(self):
        from pytigon_gui.guiframe.form import install_pre_process_lib, _PRE_PRECESS_LIB

        original = list(_PRE_PRECESS_LIB)
        _PRE_PRECESS_LIB.clear()

        handler = MagicMock()
        install_pre_process_lib(handler)
        assert handler in _PRE_PRECESS_LIB

        _PRE_PRECESS_LIB[:] = original


class TestSchPageUtilityMethods:

    def test_set_vertical_position(self):
        from pytigon_gui.guiframe.page import SchPage

        page = SchPage.__new__(SchPage)
        page.vertical_position = None
        page.set_vertical_position("top")
        assert page.vertical_position == "top"

    def test_set_vertical_position_none(self):
        from pytigon_gui.guiframe.page import SchPage

        page = SchPage.__new__(SchPage)
        page.set_vertical_position(None)
        assert page.vertical_position is None

    def test_is_active(self):
        from pytigon_gui.guiframe.page import SchPage

        page = SchPage.__new__(SchPage)
        page._active = True
        assert page.is_active() is True
        page._active = False
        assert page.is_active() is False

    def test_deactivate_page(self):
        from pytigon_gui.guiframe.page import SchPage

        page = SchPage.__new__(SchPage)
        page._active = True
        page.deactivate_page()
        assert page._active is False

    def test_activate_page(self):
        from pytigon_gui.guiframe.page import SchPage

        page = SchPage.__new__(SchPage)
        page._active = False
        page.body = MagicMock()
        page.body.SetFocus = MagicMock()
        page.activate_page()
        assert page._active is True
        page.body.SetFocus.assert_called_once()
