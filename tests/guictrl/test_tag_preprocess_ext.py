"""Tests for HTML5 form/structural preprocessing in tag_preprocess."""

import xml.etree.ElementTree as ET

from pytigon_lib.schparser.html_parsers import Td


class FakeParser:
    pass


class FakeParent:
    """Minimal stand-in for a tag parser."""

    def __init__(self, tree=None, form=None):
        self.parent = None
        self.form_obj = form
        self.parser = FakeParser()
        if tree is not None:
            self.parser._tree = tree


class FakeForm:
    """Minimal stand-in for a <form> parser."""

    def __init__(self, href, fields=None, upload=False):
        self._href = href
        self._fields = fields
        self._upload = upload

    def gethref(self):
        return self._href

    def get_fields(self):
        return self._fields

    def get_upload(self):
        return self._upload


class TestHTML5InputTypes:
    def test_number(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        tag, attrs = input_to_ctrltab(
            FakeParent(), {"type": "number", "value": "5", "step": "2"}
        )
        assert tag == "ctrl-num"
        assert attrs["value"] == "5"
        assert attrs["inc"] == "2"

    def test_range(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        tag, attrs = input_to_ctrltab(
            FakeParent(), {"type": "range", "min": "0", "max": "10"}
        )
        assert tag == "ctrl-slider"
        assert attrs["min"] == "0"
        assert attrs["max"] == "10"

    def test_color(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        tag, attrs = input_to_ctrltab(
            FakeParent(), {"type": "color", "value": "#ff0000"}
        )
        assert tag == "ctrl-colourselect"
        assert attrs["valuetype"] == "str"

    def test_search(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        assert input_to_ctrltab(FakeParent(), {"type": "search"})[0] == "ctrl-search"

    def test_date(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        assert input_to_ctrltab(FakeParent(), {"type": "date"})[0] == "ctrl-datepicker"

    def test_time(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        assert input_to_ctrltab(FakeParent(), {"type": "time"})[0] == "ctrl-time"

    def test_datetime_local(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        assert (
            input_to_ctrltab(FakeParent(), {"type": "datetime-local"})[0]
            == "ctrl-datetimepicker"
        )

    def test_tel(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        assert input_to_ctrltab(FakeParent(), {"type": "tel"})[0] == "ctrl-text"

    def test_url(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        assert input_to_ctrltab(FakeParent(), {"type": "url"})[0] == "ctrl-text"

    def test_reset(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        tag, attrs = input_to_ctrltab(FakeParent(), {"type": "reset"})
        assert tag == "ctrl-button"
        assert attrs["target"] == "_parent"

    def test_image(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        tag, attrs = input_to_ctrltab(FakeParent(), {"type": "image", "alt": "Go"})
        assert tag == "ctrl-button"
        assert attrs["label"] == "Go"

    def test_month_falls_back_to_text(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        assert input_to_ctrltab(FakeParent(), {"type": "month"})[0] == "ctrl-text"

    def test_global_attrs_forwarded(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        _, attrs = input_to_ctrltab(
            FakeParent(),
            {
                "type": "text",
                "placeholder": "hi",
                "required": "",
                "disabled": "",
                "title": "tip",
                "tabindex": "3",
                "data-x": "1",
            },
        )
        assert attrs["placeholder"] == "hi"
        assert "required" in attrs
        assert "disabled" in attrs
        assert attrs["title"] == "tip"
        assert attrs["tabindex"] == "3"
        assert attrs["data-x"] == "1"

    def test_tel_value_is_forwarded(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        tag, attrs = input_to_ctrltab(
            FakeParent(), {"type": "url", "value": "https://x"}
        )
        assert tag == "ctrl-text"
        assert attrs["value"] == "https://x"
        assert attrs["valuetype"] == "str"

    def test_schtype_still_wins(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        tag, _ = input_to_ctrltab(
            FakeParent(), {"type": "text", "schtype": "IntegerField"}
        )
        assert tag == "ctrl-num"


class TestSubmitAttrs:
    def test_submit_uses_form_action(self):
        from pytigon_gui.guictrl.tag_preprocess import _submit_attrs

        parent = FakeParent()
        parent.form_obj = FakeForm("/save", fields="POST:x", upload=True)
        # form_obj must also be reachable through the attribute used in the loop
        parent.gethref = parent.form_obj.gethref
        parent.get_fields = parent.form_obj.get_fields
        parent.get_upload = parent.form_obj.get_upload

        attrs = _submit_attrs(parent, {})
        assert attrs["href"] == "/save"
        assert attrs["fields"] == "POST:x"
        assert attrs["valuetype"] == "upload"
        assert attrs["param"] == "post"

    def test_submit_defaults(self):
        from pytigon_gui.guictrl.tag_preprocess import _submit_attrs

        attrs = _submit_attrs(FakeParent(), {})
        assert attrs["href"] == "."
        assert attrs["target"] == "_parent_refr"

    def test_submit_survives_form_without_action(self):
        """A <form> without 'action' must not abort parsing."""
        from pytigon_gui.guictrl.tag_preprocess import _submit_attrs

        def boom():
            raise KeyError("action")

        parent = FakeParent()
        parent.gethref = boom
        attrs = _submit_attrs(parent, {})
        assert attrs["href"] == "."

    def test_formaction_and_formmethod_override(self):
        from pytigon_gui.guictrl.tag_preprocess import _submit_attrs

        attrs = _submit_attrs(FakeParent(), {"formaction": "#", "formmethod": "get"})
        assert attrs["href"] == "#"
        assert attrs["param"] == "get"


class TestButtonTag:
    def test_default_is_submit(self):
        from pytigon_gui.guictrl.tag_preprocess import button_to_ctrltab

        tag, attrs = button_to_ctrltab(FakeParent(), {})
        assert tag == "ctrl-button"
        assert attrs["param"] == "post"

    def test_plain_button(self):
        from pytigon_gui.guictrl.tag_preprocess import button_to_ctrltab

        tag, attrs = button_to_ctrltab(FakeParent(), {"type": "button", "value": "X"})
        assert tag == "ctrl-button"
        assert attrs["label"] == "X"

    def test_reset(self):
        from pytigon_gui.guictrl.tag_preprocess import button_to_ctrltab

        tag, attrs = button_to_ctrltab(FakeParent(), {"type": "reset"})
        assert tag == "ctrl-button"
        assert attrs["target"] == "_parent"
        assert attrs["label"] == "Reset"


class TestFormElements:
    def test_datalist_suppressed(self):
        from pytigon_gui.guictrl.tag_preprocess import datalist_to_comment

        assert datalist_to_comment(FakeParent(), {})[0] == "comment"

    def test_datalist_feeds_input_list(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        root = ET.fromstring(
            "<html><body><datalist id='colors'>"
            "<option value='#f00'>Red</option>"
            "<option value='#0f0'>Green</option>"
            "</datalist><input type='text' list='colors'/></body></html>"
        )
        tag, attrs = input_to_ctrltab(
            FakeParent(root), {"type": "text", "list": "colors"}
        )
        assert tag == "ctrl-combobox"
        assert [row[0].data for row in attrs["_choices"]] == ["Red", "Green"]
        assert [row[0].attrs["value"] for row in attrs["_choices"]] == ["#f00", "#0f0"]

    def test_list_without_datalist_stays_text(self):
        from pytigon_gui.guictrl.tag_preprocess import input_to_ctrltab

        root = ET.fromstring("<html><body><input list='missing'/></body></html>")
        tag, _ = input_to_ctrltab(FakeParent(root), {"type": "text", "list": "missing"})
        assert tag == "ctrl-text"

    def test_output(self):
        from pytigon_gui.guictrl.tag_preprocess import output_to_ctrlstatictext

        assert output_to_ctrlstatictext(FakeParent(), {})[0] == "ctrl-statictext"

    def test_progress(self):
        from pytigon_gui.guictrl.tag_preprocess import progress_to_ctrlgauge

        tag, attrs = progress_to_ctrlgauge(FakeParent(), {"value": "1", "max": "10"})
        assert tag == "ctrl-gauge"
        assert attrs["max"] == "10"

    def test_meter(self):
        from pytigon_gui.guictrl.tag_preprocess import meter_to_ctrlgauge

        assert meter_to_ctrlgauge(FakeParent(), {"value": "1"})[0] == "ctrl-gauge"

    def test_fieldset_and_legend(self):
        from pytigon_gui.guictrl.tag_preprocess import (
            fieldset_to_ctrlstaticbox,
            legend_to_ctrlstatictext,
        )

        assert fieldset_to_ctrlstaticbox(FakeParent(), {})[0] == "ctrl-staticbox"
        assert legend_to_ctrlstatictext(FakeParent(), {})[0] == "ctrl-statictext"

    def test_textarea_forwards_attrs(self):
        from pytigon_gui.guictrl.tag_preprocess import textarea_to_ctrltab

        tag, attrs = textarea_to_ctrltab(
            FakeParent(), {"cols": "10", "placeholder": "p", "value": "drop-me"}
        )
        assert tag == "ctrl-textarea"
        assert attrs["placeholder"] == "p"
        assert "value" not in attrs


class TestSemanticTags:
    def test_all_semantic_tags_map(self):
        from pytigon_gui.guictrl import tag_preprocess as tp

        assert tp.SEMANTIC_TAG_MAP["figure"] == "div"
        assert tp.SEMANTIC_TAG_MAP["mark"] == "span"
        assert tp.SEMANTIC_TAG_MAP["dt"] == "b"
        assert tp.SEMANTIC_TAG_MAP["dd"] == "div"
        assert tp.SEMANTIC_TAG_MAP["summary"] == "b"
        # section and main are deliberately NOT mapped: rewriting them to a div
        # broke the page layout, so they are handled by the renderer instead.
        assert "section" not in tp.SEMANTIC_TAG_MAP
        assert "main" not in tp.SEMANTIC_TAG_MAP
        # header/footer are reserved for printed page headers/footers.
        assert "header" not in tp.SEMANTIC_TAG_MAP
        assert "footer" not in tp.SEMANTIC_TAG_MAP

    def test_const_converter(self):
        from pytigon_gui.guictrl import tag_preprocess as tp

        fn = tp._const_tag_convert("div")
        assert fn(FakeParent(), {"a": "1"}) == ("div", {"a": "1"})


class TestOptGroup:
    def _make(self, label="Group"):
        from pytigon_gui.guictrl.tag_parsers import OptGroupTag

        og = OptGroupTag.__new__(OptGroupTag)
        og.tdata = [[Td("one", {"value": "1"})], [Td("two", {"value": "2"})]]
        og.label = label
        og.parent = type("Parent", (), {"tdata": []})()
        return og

    def test_labels_are_prefixed(self):
        og = self._make()
        og.close()
        assert [row[0].data for row in og.parent.tdata] == [
            "Group: one",
            "Group: two",
        ]
        assert og.parent.tdata[0][0].attrs["optgroup"] == "Group"

    def test_empty_label_keeps_options(self):
        og = self._make(label="")
        og.close()
        assert [row[0].data for row in og.parent.tdata] == ["one", "two"]


class TestRegistrations:
    """The new preprocessors must be wired into the global tag map."""

    def test_tag_preprocessors_registered(self):
        from pytigon_lib.schhtml.basehtmltags import get_tag_preprocess_map
        from pytigon_gui.guictrl import tag_preprocess as tp

        tmap = get_tag_preprocess_map()
        expected = {
            "button": tp.button_to_ctrltab,
            "fieldset": tp.fieldset_to_ctrlstaticbox,
            "legend": tp.legend_to_ctrlstatictext,
            "output": tp.output_to_ctrlstatictext,
            "progress": tp.progress_to_ctrlgauge,
            "meter": tp.meter_to_ctrlgauge,
            "datalist": tp.datalist_to_comment,
        }
        for tag, fn in expected.items():
            assert tmap.get_handler(tag) is fn

    def test_semantic_tags_registered(self):
        import pytigon_gui.guictrl.tag_preprocess  # noqa: F401 - registers the map

        from pytigon_lib.schhtml.basehtmltags import get_tag_preprocess_map

        tmap = get_tag_preprocess_map()
        for tag in ("article", "nav", "aside", "figure", "mark"):
            assert tmap.get_handler(tag) is not None
        # section and main are not remapped on purpose: rewriting them to a div
        # broke the page layout, so they must stay unregistered here and be
        # left to the renderer.
        for tag in ("section", "main"):
            assert tmap.get_handler(tag) is None, f"{tag} should not be remapped"


class TestWidgetBases:
    """Regression guards for widgets exposed by the new HTML5 mappings."""

    def test_datetimepicker_is_a_wx_control(self):
        import wx

        from pytigon_gui.guictrl.input.datetime import DATETIMEPICKER

        # It must be a real wx control, otherwise POPUPHTML.__init__ cannot
        # run ComboCtrl.__init__ on it.
        assert issubclass(DATETIMEPICKER, wx.ComboCtrl)

    def test_colourselect_is_a_wx_control(self):
        import wx

        from pytigon_gui.guictrl.display import COLOURSELECT

        assert issubclass(COLOURSELECT, wx.Window)
