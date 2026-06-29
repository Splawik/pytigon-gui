"""Signal dispatch module.

Provides a simple publish-subscribe mechanism for inter-window communication.
Objects register to receive named signals, and signal senders can broadcast
to all registered listeners.
"""


class Signal:
    """Simple signal/slot mechanism for communication between windows.

    Registered objects must have a method matching the signal name.
    That method must accept the arguments passed to :meth:`signal`.

    Usage::

        sig = Signal()
        sig.register_signal(my_window, "on_data_ready")
        sig.signal("on_data_ready", data=some_data)
        sig.unregister_signal(my_window, "on_data_ready")
    """

    def __init__(self):
        """Initialize an empty signal registry."""
        self._signals = {}

    def register_signal(self, obj, signal_name):
        """Register an object to receive a signal.

        The object must have a method with the name *signal_name* that
        accepts the arguments passed to :meth:`signal`.

        Args:
            obj: Object to receive signals.
            signal_name: Name of the signal (also the method name on obj).
        """
        if signal_name not in self._signals:
            self._signals[signal_name] = []
        if obj not in self._signals[signal_name]:
            self._signals[signal_name].append(obj)

    def unregister_signal(self, obj, signal_name):
        """Unregister an object from receiving a signal.

        Args:
            obj: Object to stop receiving signals.
            signal_name: Name of the signal.

        Raises:
            KeyError: If *signal_name* is not registered.
        """
        if signal_name not in self._signals:
            return
        signal_list = self._signals[signal_name]
        if obj in signal_list:
            idx = signal_list.index(obj)
            del signal_list[idx]

    def signal(self, signal_name, *argi, **argv):
        """Send a signal to all registered listeners.

        Args:
            signal_name: Name of the signal/method to call.
            *argi: Positional arguments forwarded to the handler.
            **argv: Keyword arguments forwarded to the handler.

        Returns:
            List of return values from handlers (excluding None values).
        """
        ret = []
        if signal_name in self._signals:
            for obj in self._signals[signal_name]:
                if (x := getattr(obj, signal_name)(*argi, **argv)) is not None:
                    ret.append(x)
        return ret
