"""Tests for pytigon_gui.guiframe.baseframe - base frame classes."""

import pytest
from unittest.mock import MagicMock


class TestSchBaseFrame:

    def test_attributes_after_init(self):
        from pytigon_gui.guiframe.baseframe import SchBaseFrame

        frame = SchBaseFrame.__new__(SchBaseFrame)
        frame.run_on_close = []
        frame.destroy_fun_tab = []
        assert frame.run_on_close == []
        assert frame.destroy_fun_tab == []

    def test_on_close_calls_handlers(self):
        from pytigon_gui.guiframe.baseframe import SchBaseFrame

        frame = SchBaseFrame.__new__(SchBaseFrame)
        called = []

        def handler1(sender):
            called.append(1)

        def handler2(sender):
            called.append(2)

        frame.run_on_close = [handler1, handler2]
        mock_event = MagicMock()
        frame.on_close(mock_event)
        assert called == [1, 2]
        mock_event.Skip.assert_called_once()

    def test_on_close_handler_error(self):
        from pytigon_gui.guiframe.baseframe import SchBaseFrame

        frame = SchBaseFrame.__new__(SchBaseFrame)
        called = []

        def broken_handler(sender):
            raise RuntimeError("fail")

        def ok_handler(sender):
            called.append(1)

        frame.run_on_close = [broken_handler, ok_handler]
        mock_event = MagicMock()
        frame.on_close(mock_event)
        assert called == [1]
