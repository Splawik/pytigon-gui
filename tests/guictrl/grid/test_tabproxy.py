"""Tests for pytigon_gui.guictrl.grid.tabproxy - DataProxy class."""

import pytest
from unittest.mock import MagicMock, patch


class TestProcessPostParm:
    """Tests for process_post_parm helper."""

    def test_converts_values_to_json(self):
        """All dict values are converted to JSON strings."""
        from pytigon_gui.guictrl.grid.tabproxy import process_post_parm

        result = process_post_parm({"cmd": 1, "nr": 1})
        assert result == {"cmd": "1", "nr": "1"}

    def test_handles_string_values(self):
        """String values are encoded via schjson.dumps."""
        from pytigon_gui.guictrl.grid.tabproxy import process_post_parm
        from pytigon_lib.schtools import schjson

        result = process_post_parm({"key": "hello"})
        # schjson.dumps uses URL-encoded format
        assert result == {"key": schjson.dumps("hello")}

    def test_handles_list_values(self):
        """List values are encoded via schjson.dumps."""
        from pytigon_gui.guictrl.grid.tabproxy import process_post_parm
        from pytigon_lib.schtools import schjson

        result = process_post_parm({"items": [1, 2, 3]})
        assert result == {"items": schjson.dumps([1, 2, 3])}

    def test_empty_dict(self):
        """Empty dict returns empty dict."""
        from pytigon_gui.guictrl.grid.tabproxy import process_post_parm

        result = process_post_parm({})
        assert result == {}


class TestDataProxyConstants:
    """Tests for DataProxy command constants."""

    def test_cmd_constants(self):
        """Verify command constants are correct integers."""
        from pytigon_gui.guictrl.grid.tabproxy import (
            CMD_INFO,
            CMD_PAGE,
            CMD_COUNT,
            CMD_SYNC,
            CMD_AUTO,
            CMD_RECASSTR,
            CMD_EXEC,
        )

        assert CMD_INFO == 1
        assert CMD_PAGE == 2
        assert CMD_COUNT == 3
        assert CMD_SYNC == 4
        assert CMD_AUTO == 5
        assert CMD_RECASSTR == 6
        assert CMD_EXEC == 7


class TestDataProxy:
    """Tests for DataProxy class."""

    def _create_mock_response(self, data_dict):
        """Helper to create a mock HTTP response."""
        import json

        response = MagicMock()
        response.str.return_value = json.dumps(data_dict)
        return response

    def test_init_sets_basic_attributes(self):
        """DataProxy.__init__ sets basic attributes."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id", "name"],'
            '"col_types": ["long", "string"],'
            '"default_rec": [0, ""],'
            '"col_length": [10, 100],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.max_count == 1000000
        assert dp.var_count == -1
        assert dp.tabaddress == "/api/table/"
        assert dp.col_names == ["id", "name"]
        assert dp.col_types == ["long", "string"]
        assert dp.default_rec == [0, ""]
        assert dp.col_size == [10, 32]  # 100 -> clamped to 32
        assert dp.auto_cols == []

    def test_init_clamps_col_size(self):
        """col_size values > 32 are clamped to 32."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id", "desc"],'
            '"col_types": ["long", "string"],'
            '"default_rec": [0, ""],'
            '"col_length": [10, 500],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.col_size == [10, 32]

    def test_col_types2_parsing(self):
        """col_types2 stores the first part before colon."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id", "type"],'
            '"col_types": ["long:IntegerField", "string:CharField"],'
            '"default_rec": [0, ""],'
            '"col_length": [10, 50],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.col_types2 == ["long", "string"]

    def test_set_parent(self):
        """set_parent updates the parent attribute."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        mock_parent = MagicMock()
        dp.set_parent(mock_parent)
        assert dp.parent is mock_parent

    def test_get_address(self):
        """get_address returns current tabaddress."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.get_address() == "/api/table/"

    def test_set_address(self):
        """set_address appends to the base address."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        dp.set_address("/filter/")
        assert dp.tabaddress == "/api/table//filter/"

    def test_set_address_parm_new(self):
        """set_address_parm returns True for new parm."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        result = dp.set_address_parm({"key": "val"})
        assert result == True
        assert dp.parm == {"key": "val"}

    def test_set_address_parm_same(self):
        """set_address_parm returns False for same parm."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        dp.set_address_parm({"key": "val"})
        result = dp.set_address_parm({"key": "val"})
        assert result == False

    def test_conw_long(self):
        """conw_long converts to int or None."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.conw_long("42") == 42
        assert dp.conw_long(0) is None  # 0 is falsy -> None
        assert dp.conw_long("") is None
        assert dp.conw_long(None) is None

    def test_conw_float(self):
        """conw_float converts to float or None."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.conw_float("3.14") == 3.14
        assert dp.conw_float("") is None

    def test_conw_bool(self):
        """conw_bool converts to bool or None."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        # conw_bool: if b: return bool(b) else return None
        assert dp.conw_bool(True) == True
        assert dp.conw_bool(1) == True
        assert dp.conw_bool("true") == True
        assert dp.conw_bool(0) is None  # 0 is falsy
        assert dp.conw_bool(False) is None  # False is falsy
        assert dp.conw_bool(None) is None
        assert dp.conw_bool("") is None

    def test_conw_none(self):
        """conw_none replaces None with empty string."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.conw_none("hello") == "hello"
        assert dp.conw_none(None) == ""

    def test_get_page(self):
        """get_page fetches a page of data."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        # First POST for init
        init_response = MagicMock()
        init_response.str.return_value = (
            '{"col_names": ["id", "name"],'
            '"col_types": ["long", "string"],'
            '"default_rec": [0, ""],'
            '"col_length": [10, 50],'
            '"auto_cols": []}'
        )
        # Second POST for get_page
        page_response = MagicMock()
        page_response.str.return_value = '{"page": [[1, "Alice"], [2, "Bob"]]}'
        mock_http.post.side_effect = [init_response, page_response]

        dp = DataProxy(mock_http, "/api/table/")
        result = dp.get_page(0)
        assert result == [[1, "Alice"], [2, "Bob"]]

    @patch("pytigon_gui.guictrl.grid.tabproxy.wx")
    def test_get_page_empty(self, mock_wx):
        """get_page returns empty list when page data is missing."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        init_response = MagicMock()
        init_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        # Page response with missing 'page' key
        page_response = MagicMock()
        page_response.str.return_value = '{"other": "data"}'

        mock_http.post.side_effect = [init_response, page_response]

        # Mock wx.GetApp for http.show fallback
        mock_app = MagicMock()
        mock_wx.GetApp.return_value = mock_app

        dp = DataProxy(mock_http, "/api/table/")
        result = dp.get_page(0)
        assert result == []

    def test_get_count(self):
        """get_count fetches record count."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        init_response = MagicMock()
        init_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        count_response = MagicMock()
        count_response.str.return_value = '{"count": 42}'
        mock_http.post.side_effect = [init_response, count_response]

        dp = DataProxy(mock_http, "/api/table/")
        result = dp.get_count()
        assert result == 42
        assert dp.max_count == 42

    def test_get_col_names(self):
        """GetColNames returns column names."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id", "name", "email"],'
            '"col_types": ["long", "string", "string"],'
            '"default_rec": [0, "", ""],'
            '"col_length": [10, 50, 100],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.GetColNames() == ["id", "name", "email"]

    def test_get_col_types(self):
        """GetColTypes returns column types."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long:IntegerField"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.GetColTypes() == ["long:IntegerField"]

    def test_get_col_size(self):
        """GetColSize returns column sizes."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id", "desc"],'
            '"col_types": ["long", "string"],'
            '"default_rec": [0, ""],'
            '"col_length": [10, 500],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.GetColSize() == [10, 32]

    def test_get_default_rec(self):
        """get_default_rec returns default record."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id", "name"],'
            '"col_types": ["long", "string"],'
            '"default_rec": [0, ""],'
            '"col_length": [10, 50],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.get_default_rec() == [0, ""]

    def test_get_auto_cols(self):
        """GetAutoCols returns auto-computed columns."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": ["total"]}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.GetAutoCols() == ["total"]

    def test_get_col_icons(self):
        """GetColIcons returns None (not implemented)."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        assert dp.GetColIcons() is None

    def test_clone(self):
        """clone creates a copy with same parm."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        dp.set_address_parm({"filter": "active"})

        clone = dp.clone()
        assert clone is not dp
        assert clone.tabaddress == dp.tabaddress
        assert clone.get_address_parm() == dp.get_address_parm()

    def test_set_parm(self):
        """set_parm adds a key to parm dict."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id"],'
            '"col_types": ["long"],'
            '"default_rec": [0],'
            '"col_length": [10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        dp.set_parm("filter", "active")
        assert dp.parm == {"filter": "active"}

    def test_reformat_rec(self):
        """_reformat_rec converts values using type converters."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id", "name", "score"],'
            '"col_types": ["long", "string", "double"],'
            '"default_rec": [0, "", 0.0],'
            '"col_length": [10, 50, 10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        result = dp._reformat_rec(["42", "Alice", "3.14"])
        assert result == [42, "Alice", 3.14]

    def test_reformat_rec_nulls(self):
        """_reformat_rec handles null/empty values."""
        from pytigon_gui.guictrl.grid.tabproxy import DataProxy

        mock_http = MagicMock()
        mock_response = MagicMock()
        mock_response.str.return_value = (
            '{"col_names": ["id", "txt", "flag"],'
            '"col_types": ["long", "string", "bool"],'
            '"default_rec": [0, "", false],'
            '"col_length": [10, 50, 10],'
            '"auto_cols": []}'
        )
        mock_http.post.return_value = mock_response

        dp = DataProxy(mock_http, "/api/table/")
        # long: "" -> None (falsy), string: None -> "", bool: "" -> None
        result = dp._reformat_rec(["", None, ""])
        assert result == [None, "", None]
