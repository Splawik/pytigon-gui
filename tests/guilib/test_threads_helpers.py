"""Tests for pytigon_gui.guilib.threads - main-thread marshalling helpers."""

from unittest.mock import MagicMock, patch


class _DeadObject:
    """Object that raises RuntimeError when its truth value is tested."""

    def __bool__(self):
        raise RuntimeError("wrapped C/C++ object has been deleted")


class TestIsAlive:
    """Tests for is_alive()."""

    def test_none_is_not_alive(self):
        from pytigon_gui.guilib.threads import is_alive

        assert is_alive(None) is False

    def test_live_object_is_alive(self):
        from pytigon_gui.guilib.threads import is_alive

        assert is_alive(MagicMock()) is True

    def test_destroyed_object_is_not_alive(self):
        from pytigon_gui.guilib.threads import is_alive

        assert is_alive(_DeadObject()) is False


class TestCallAfterIfAlive:
    """Tests for call_after_if_alive()."""

    def test_skips_dead_window(self):
        from pytigon_gui.guilib import threads

        called = []
        with patch.object(
            threads.wx, "CallAfter", side_effect=lambda fn, *a, **k: fn()
        ):
            threads.call_after_if_alive(None, called.append, 1)
        assert called == []

    def test_calls_for_live_window(self):
        from pytigon_gui.guilib import threads

        called = []
        with patch.object(
            threads.wx, "CallAfter", side_effect=lambda fn, *a, **k: fn()
        ):
            threads.call_after_if_alive(MagicMock(), called.append, 2)
        assert called == [2]


class TestBlockHttpPumping:
    """Tests for block_http_pumping()."""

    def test_counter_balanced(self):
        from pytigon_lib.schhttptools import httpclient
        from pytigon_gui.guilib.threads import block_http_pumping

        start = httpclient.IN_PAINT
        with block_http_pumping():
            assert httpclient.IN_PAINT == start + 1
        assert httpclient.IN_PAINT == start

    def test_counter_balanced_on_exception(self):
        from pytigon_lib.schhttptools import httpclient
        from pytigon_gui.guilib.threads import block_http_pumping

        start = httpclient.IN_PAINT
        try:
            with block_http_pumping():
                raise ValueError("boom")
        except ValueError:
            pass
        assert httpclient.IN_PAINT == start
