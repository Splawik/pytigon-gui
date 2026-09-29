"""Tests for pytigon_gui.guictrl.tag and related shim re-exports."""

import pytest


class TestTagReexports:
    def test_parsers_re_exported(self):
        from pytigon_gui.guictrl.tag_parsers import TreeList, TreeUl, TreeLi
        from pytigon_gui.guictrl.tag import TreeList as TL2, TreeUl as TU2

        assert TL2 is TreeList
        assert TU2 is TreeUl


class TestCollectWxKwargs:
    """CSS 'style' must never be forwarded as a wx style bitmask."""

    def test_css_style_is_filtered(self):
        from pytigon_gui.guictrl.tag_ctrltag import _collect_wx_kwargs

        kw = _collect_wx_kwargs({"id": "x", "style": "width:10px", "name": "n"})
        assert "style" not in kw
        assert kw["id"] == "x"
        assert kw["name"] == "n"

    def test_integer_style_is_kept(self):
        from pytigon_gui.guictrl.tag_ctrltag import _collect_wx_kwargs

        assert _collect_wx_kwargs({"style": 5})["style"] == 5

    def test_none_becomes_empty_string(self):
        from pytigon_gui.guictrl.tag_ctrltag import _collect_wx_kwargs

        assert _collect_wx_kwargs({"id": None})["id"] == ""

    def test_unknown_attributes_are_ignored(self):
        from pytigon_gui.guictrl.tag_ctrltag import _collect_wx_kwargs

        assert _collect_wx_kwargs({"data-x": "1", "id": "a"}) == {"id": "a"}


class TestStandardToolbarButtons:
    def test_empty_control(self):
        from pytigon_gui.toolbar.standardtoolbarbuttons import EmptyControl

        ec = EmptyControl()
        assert ec.GetValue() is None
        ec.SetValue("test")
        assert ec.GetValue() == "test"

    def test_empty_bar(self):
        from pytigon_gui.toolbar.standardtoolbarbuttons import EmptyBar

        bar = EmptyBar()
        bar.refr()

    def test_web_history_iter(self):
        from pytigon_gui.toolbar.standardtoolbarbuttons import WebHistory

        wh = WebHistory()
        items = list(wh)
        assert len(items) > 0

    def test_web_history_getitem(self):
        from pytigon_gui.toolbar.standardtoolbarbuttons import WebHistory

        wh = WebHistory()
        assert isinstance(wh[0], str)

    def test_web_history_getitem_out_of_range(self):
        from pytigon_gui.toolbar.standardtoolbarbuttons import WebHistory

        wh = WebHistory()
        with pytest.raises(IndexError):
            wh[100]

    def test_web_history_len(self):
        from pytigon_gui.toolbar.standardtoolbarbuttons import WebHistory

        wh = WebHistory()
        assert len(wh) == 4

    def test_web_history_contains(self):
        from pytigon_gui.toolbar.standardtoolbarbuttons import WebHistory

        wh = WebHistory()
        assert "www.google.pl" in wh
        assert "nonexistent.example.com" not in wh

    def test_type_constants(self):
        from pytigon_gui.toolbar.standardtoolbarbuttons import (
            TYPE_TOOLBAR,
            TYPE_BUTTONBAR,
            TYPE_PANELBAR,
        )

        assert TYPE_TOOLBAR == 0
        assert TYPE_BUTTONBAR == 1
        assert TYPE_PANELBAR == 2
