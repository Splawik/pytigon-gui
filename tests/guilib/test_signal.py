"""Tests for pytigon_gui.guilib.signal - Signal publish/subscribe."""

import pytest


class TestSignal:
    """Tests for the Signal class."""

    def test_init_empty(self):
        """Signal initializes with empty registry."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()
        assert sig._signals == {}

    def test_register_signal(self):
        """Object can be registered for a signal."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()

        class Listener:
            def on_test(self, **kwargs):
                pass

        listener = Listener()
        sig.register_signal(listener, "on_test")
        assert "on_test" in sig._signals
        assert listener in sig._signals["on_test"]

    def test_register_duplicate(self):
        """Registering same object twice does not duplicate."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()

        class Listener:
            def on_test(self, **kwargs):
                pass

        listener = Listener()
        sig.register_signal(listener, "on_test")
        sig.register_signal(listener, "on_test")
        assert len(sig._signals["on_test"]) == 1

    def test_unregister_signal(self):
        """Object can be unregistered from a signal."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()

        class Listener:
            def on_test(self, **kwargs):
                pass

        listener = Listener()
        sig.register_signal(listener, "on_test")
        sig.unregister_signal(listener, "on_test")
        assert listener not in sig._signals["on_test"]

    def test_unregister_nonexistent_signal(self):
        """Unregistering from non-existent signal does not raise."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()

        class Listener:
            def on_test(self, **kwargs):
                pass

        listener = Listener()
        # Should not raise
        sig.unregister_signal(listener, "nonexistent")

    def test_unregister_nonexistent_object(self):
        """Unregistering a non-registered object is safe."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()

        class Listener:
            def on_test(self, **kwargs):
                pass

        listener1 = Listener()
        listener2 = Listener()
        sig.register_signal(listener1, "on_test")
        # listener2 was not registered, should not raise
        sig.unregister_signal(listener2, "on_test")

    def test_signal_dispatch(self):
        """Signal calls registered handler with args."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()
        called_with = []

        class Listener:
            def on_test(self, *args, **kwargs):
                called_with.append({"args": args, "kwargs": kwargs})

        listener = Listener()
        sig.register_signal(listener, "on_test")
        sig.signal("on_test", "hello", data=42)

        assert len(called_with) == 1
        assert called_with[0]["args"] == ("hello",)
        assert called_with[0]["kwargs"] == {"data": 42}

    def test_signal_dispatch_multiple_listeners(self):
        """Signal calls all registered handlers."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()
        results = []

        class Listener1:
            def on_test(self, **kwargs):
                results.append("L1")

        class Listener2:
            def on_test(self, **kwargs):
                results.append("L2")

        sig.register_signal(Listener1(), "on_test")
        sig.register_signal(Listener2(), "on_test")
        sig.signal("on_test")

        assert results == ["L1", "L2"]

    def test_signal_returns_values(self):
        """Signal returns non-None values from handlers."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()

        class Listener:
            def on_test(self, **kwargs):
                return "result1"

        class Listener2:
            def on_test(self, **kwargs):
                return None  # Should be excluded

        class Listener3:
            def on_test(self, **kwargs):
                return "result3"

        sig.register_signal(Listener(), "on_test")
        sig.register_signal(Listener2(), "on_test")
        sig.register_signal(Listener3(), "on_test")

        ret = sig.signal("on_test")
        assert ret == ["result1", "result3"]

    def test_signal_nonexistent(self):
        """Signaling non-existent name returns empty list."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()
        ret = sig.signal("nonexistent")
        assert ret == []

    def test_multiple_signals(self):
        """Same object can listen to multiple signals."""
        from pytigon_gui.guilib.signal import Signal

        sig = Signal()
        results = []

        class Listener:
            def on_a(self, **kwargs):
                results.append("a")

            def on_b(self, **kwargs):
                results.append("b")

        listener = Listener()
        sig.register_signal(listener, "on_a")
        sig.register_signal(listener, "on_b")
        sig.signal("on_a")
        sig.signal("on_b")

        assert results == ["a", "b"]
