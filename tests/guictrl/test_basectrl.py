"""Tests for pytigon_gui.guictrl.basectrl - base control class."""

import pytest
from unittest.mock import MagicMock, patch


class TestExtractKwarg:
    """Tests for _extract_kwarg helper function."""

    def test_key_exists(self):
        """Returns value and removes key from dict when key exists."""
        from pytigon_gui.guictrl.basectrl import _extract_kwarg

        kwds = {"href": "/test", "label": "Test"}
        result = _extract_kwarg(kwds, "href")
        assert result == "/test"
        assert "href" not in kwds

    def test_key_missing_default(self):
        """Returns default when key is missing."""
        from pytigon_gui.guictrl.basectrl import _extract_kwarg

        kwds = {"label": "Test"}
        result = _extract_kwarg(kwds, "href", "default_value")
        assert result == "default_value"

    def test_key_missing_no_default(self):
        """Returns None when key is missing and no default."""
        from pytigon_gui.guictrl.basectrl import _extract_kwarg

        kwds = {"label": "Test"}
        result = _extract_kwarg(kwds, "href")
        assert result is None

    def test_multiple_extractions(self):
        """Multiple extractions work sequentially."""
        from pytigon_gui.guictrl.basectrl import _extract_kwarg

        kwds = {"href": "/test", "label": "Test", "id": "myid"}

        href = _extract_kwarg(kwds, "href")
        label = _extract_kwarg(kwds, "label")
        id_val = _extract_kwarg(kwds, "id")

        assert href == "/test"
        assert label == "Test"
        assert id_val == "myid"
        assert kwds == {}


class TestSchBaseCtrlInitBase:
    """Tests for SchBaseCtrl.init_base() method."""

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_init_base_extracts_href(self, mock_wx):
        """init_base extracts href from kwds."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({"href": "/test/page", "label": "Page"})

        assert ctrl.href == "/test/page"
        assert ctrl.label == "Page"

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_init_base_extracts_id(self, mock_wx):
        """init_base extracts id as nr_id."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({"id": "mycontrol"})

        assert ctrl.nr_id == "mycontrol"

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_init_base_defaults(self, mock_wx):
        """init_base sets sensible defaults."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({})

        assert ctrl.href == ""
        assert ctrl.target == "_blank"
        assert ctrl.valuetype == "data"
        assert ctrl.length == 0
        assert ctrl.maxlength == 0
        assert ctrl.readonly == False
        assert ctrl.hidden == False

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_init_base_readonly_true(self, mock_wx):
        """init_base sets readonly when kwarg present."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({"readonly": True})

        assert ctrl.readonly == True

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_init_base_hidden(self, mock_wx):
        """init_base sets hidden when kwarg present."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({"hidden": True})

        assert ctrl.hidden == True

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_init_base_length_values(self, mock_wx):
        """init_base converts length/maxlength to int."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({"length": "30", "maxlength": "100"})

        assert ctrl.length == 30
        assert ctrl.maxlength == 100

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_init_base_data_unquoted(self, mock_wx):
        """init_base URL-decodes data attribute."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({"data": "hello%20world"})

        assert ctrl.data == "hello world"

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_init_base_tag_from_param(self, mock_wx):
        """init_base extracts tag from param dict."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({"param": {"tag": "ctrltext"}})

        assert ctrl.tag == "ctrltext"

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_init_base_hooks_called(self, mock_wx):
        """init_base calls registered ctrl_process hooks for the tag."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        hook_called = []

        def my_hook(ctrl):
            hook_called.append(ctrl)

        mock_app = MagicMock()
        mock_app.ctrl_process = {"my_tag": [my_hook]}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({"param": {"tag": "my_tag"}})

        assert len(hook_called) == 1
        assert hook_called[0] is ctrl


class TestSchBaseCtrlMethods:
    """Tests for SchBaseCtrl utility methods."""

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_set_and_get_unique_name(self, mock_wx):
        """unique_name can be set and retrieved."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({})

        ctrl.set_unique_name("test_ctrl_001")
        assert ctrl.get_unique_name() == "test_ctrl_001"

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_get_parent_form(self, mock_wx):
        """get_parent_form walks up to find SchForm."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        mock_form = MagicMock()
        mock_form.__class__.__name__ = "SchForm"

        mock_intermediate = MagicMock()
        mock_intermediate.GetParent.return_value = mock_form

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({})
        ctrl.parent = mock_intermediate

        result = ctrl.get_parent_form()
        assert result is mock_form

    @patch("pytigon_gui.guictrl.basectrl.wx")
    def test_get_parent_form_none(self, mock_wx):
        """get_parent_form returns None when no SchForm ancestor."""
        from pytigon_gui.guictrl.basectrl import SchBaseCtrl

        mock_app = MagicMock()
        mock_app.ctrl_process = {}
        mock_wx.GetApp.return_value = mock_app

        mock_window = MagicMock()
        mock_window.__class__.__name__ = "wxPanel"
        mock_window.GetParent.return_value = None

        ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
        ctrl.init_base({})
        ctrl.parent = mock_window

        result = ctrl.get_parent_form()
        assert result is None


class TestHandleBestSize:
    """Tests for handle_best_size decorator."""

    def test_decorator_returns_class(self):
        """handle_best_size returns a class."""
        from pytigon_gui.guictrl.basectrl import handle_best_size

        class MockWidget:
            def GetBestSize(self):
                return (100, 50)

        Derived = handle_best_size(MockWidget)
        assert issubclass(Derived, MockWidget)

    def test_get_best_size_default(self):
        """GetBestSize uses base class when no param width/height."""
        from pytigon_gui.guictrl.basectrl import handle_best_size

        class MockWidget:
            def GetBestSize(self):
                return (100, 50)

        Derived = handle_best_size(MockWidget)
        widget = Derived()
        widget.param = {}

        result = widget.GetBestSize()
        assert result == (100, 50)

    def test_get_best_size_with_param_width(self):
        """GetBestSize uses param width when available."""
        from pytigon_gui.guictrl.basectrl import handle_best_size

        class MockWidget:
            def GetBestSize(self):
                return (100, 50)

        Derived = handle_best_size(MockWidget)
        widget = Derived()
        widget.param = {"width": "200"}

        result = widget.GetBestSize()
        assert result == (200, 50)

    def test_get_best_size_with_param_height(self):
        """GetBestSize uses param height when available."""
        from pytigon_gui.guictrl.basectrl import handle_best_size

        class MockWidget:
            def GetBestSize(self):
                return (100, 50)

        Derived = handle_best_size(MockWidget)
        widget = Derived()
        widget.param = {"height": "75"}

        result = widget.GetBestSize()
        assert result == (100, 75)

    def test_get_best_size_with_both_params(self):
        """GetBestSize uses both param width and height."""
        from pytigon_gui.guictrl.basectrl import handle_best_size

        class MockWidget:
            def GetBestSize(self):
                return (100, 50)

        Derived = handle_best_size(MockWidget)
        widget = Derived()
        widget.param = {"width": "200", "height": "75"}

        result = widget.GetBestSize()
        assert result == (200, 75)

    def test_get_best_size_invalid_param(self):
        """GetBestSize falls back when param values are invalid."""
        from pytigon_gui.guictrl.basectrl import handle_best_size

        class MockWidget:
            def GetBestSize(self):
                return (100, 50)

        Derived = handle_best_size(MockWidget)
        widget = Derived()
        widget.param = {"width": "not_a_number"}

        result = widget.GetBestSize()
        # Falls back to base width
        assert result == (100, 50)


class TestHtmlBool:
    """Tests for the _html_bool helper (HTML boolean attributes)."""

    def test_absent_is_false(self):
        from pytigon_gui.guictrl.basectrl import _html_bool

        assert _html_bool({}, "disabled") is False

    def test_present_empty_is_true(self):
        from pytigon_gui.guictrl.basectrl import _html_bool

        assert _html_bool({"disabled": ""}, "disabled") is True

    def test_present_none_is_true(self):
        from pytigon_gui.guictrl.basectrl import _html_bool

        assert _html_bool({"disabled": None}, "disabled") is True

    def test_explicit_false(self):
        from pytigon_gui.guictrl.basectrl import _html_bool

        assert _html_bool({"disabled": "false"}, "disabled") is False

    def test_explicit_true(self):
        from pytigon_gui.guictrl.basectrl import _html_bool

        assert _html_bool({"required": "required"}, "required") is True


class TestSchBaseCtrlHtml5Attrs:
    """Tests for HTML5 / global attributes extracted by init_base()."""

    def _make_ctrl(self, param):
        from unittest.mock import MagicMock, patch

        with patch("pytigon_gui.guictrl.basectrl.wx") as mock_wx:
            mock_app = MagicMock()
            mock_app.ctrl_process = {}
            mock_wx.GetApp.return_value = mock_app
            from pytigon_gui.guictrl.basectrl import SchBaseCtrl

            ctrl = SchBaseCtrl.__new__(SchBaseCtrl)
            ctrl.init_base({"param": param})
        return ctrl

    def test_all_attributes(self):
        ctrl = self._make_ctrl(
            {
                "placeholder": "p",
                "required": "",
                "disabled": "",
                "autofocus": "1",
                "multiple": "multiple",
                "pattern": "[0-9]+",
                "min": "1",
                "max": "9",
                "step": "2",
                "list": "ids",
                "title": "tip",
                "tabindex": "4",
                "data-role": "x",
                "data-count": "3",
            }
        )
        assert ctrl.placeholder == "p"
        assert ctrl.required is True
        assert ctrl.disabled is True
        assert ctrl.autofocus is True
        assert ctrl.multiple is True
        assert ctrl.pattern == "[0-9]+"
        assert ctrl.min == "1"
        assert ctrl.max == "9"
        assert ctrl.step == "2"
        assert ctrl.list_id == "ids"
        assert ctrl.title_attr == "tip"
        assert ctrl.tabindex == 4
        assert ctrl.data_attrs == {"role": "x", "count": "3"}

    def test_defaults(self):
        ctrl = self._make_ctrl({})
        assert ctrl.placeholder is None
        assert ctrl.required is False
        assert ctrl.disabled is False
        assert ctrl.autofocus is False
        assert ctrl.multiple is False
        assert ctrl.list_id is None
        assert ctrl.tabindex is None
        assert ctrl.data_attrs == {}


class TestApplyCommonAttrs:
    """Tests for SchBaseCtrl._apply_common_attrs()."""

    def test_applies_placeholder_title_disabled(self):
        from unittest.mock import MagicMock, patch

        with patch("pytigon_gui.guictrl.basectrl.wx"):
            from pytigon_gui.guictrl.basectrl import SchBaseCtrl

            ctrl = MagicMock()
            ctrl.placeholder = "hint"
            ctrl.title_attr = "tip"
            ctrl.disabled = True
            ctrl.autofocus = False
            SchBaseCtrl._apply_common_attrs(ctrl)

        ctrl.SetHint.assert_called_once_with("hint")
        ctrl.SetToolTip.assert_called_once_with("tip")
        ctrl.Disable.assert_called_once()

    def test_autofocus_only_when_accepted(self):
        from unittest.mock import MagicMock, patch

        with patch("pytigon_gui.guictrl.basectrl.wx") as mock_wx:
            from pytigon_gui.guictrl.basectrl import SchBaseCtrl

            ctrl = MagicMock()
            ctrl.placeholder = None
            ctrl.title_attr = None
            ctrl.disabled = False
            ctrl.autofocus = True
            ctrl.IsBeingDeleted.return_value = False
            ctrl.CanAcceptFocus.return_value = False
            SchBaseCtrl._apply_common_attrs(ctrl)

            # Focus is deferred, so CallAfter is registered...
            mock_wx.CallAfter.assert_called_once()
            ctrl.SetFocus.assert_not_called()

            # ...but the deferred call must not focus when it is refused.
            mock_wx.CallAfter.call_args[0][0]()
            ctrl.SetFocus.assert_not_called()

    def test_autofocus_focuses_when_accepted(self):
        from unittest.mock import MagicMock, patch

        with patch("pytigon_gui.guictrl.basectrl.wx") as mock_wx:
            from pytigon_gui.guictrl.basectrl import SchBaseCtrl

            ctrl = MagicMock()
            ctrl.placeholder = None
            ctrl.title_attr = None
            ctrl.disabled = False
            ctrl.autofocus = True
            ctrl.IsBeingDeleted.return_value = False
            ctrl.CanAcceptFocus.return_value = True
            SchBaseCtrl._apply_common_attrs(ctrl)

            mock_wx.CallAfter.call_args[0][0]()
            ctrl.SetFocus.assert_called_once()
