class Signal:
    """Helper class for sending signals between windows"""

    def __init__(self):
        self._signals = {}

    def register_signal(self, obj, signal_name):
        """Register obj to receive signal.
        Object must have a function with name: signal_name
        Function must accept arguments passed to method: signal

        Args:
            obj - object to receive signals
            signal_name - name of signal
        """
        if signal_name not in self._signals:
            self._signals[signal_name] = []
        if not obj in self._signals[signal_name]:
            self._signals[signal_name].append(obj)

    def unregister_signal(self, obj, signal_name):
        """Unregister obj to receive signal

        Args:
            obj - object to receive signals
            signal_name - name of signal
        """
        if obj in self._signals[signal_name]:
            id = self._signals[signal_name].index(obj)
            del self._signals[signal_name][id]

    def signal(self, signal_name, *argi, **argv):
        """Send signal

        Args:
            signal_name - name of signal
            *argi, **argv - parameters of signal
        """
        ret = []
        if signal_name in self._signals:
            for obj in self._signals[signal_name]:
                x = getattr(obj, signal_name)(*argi, **argv)
                if x is not None:
                    ret.append(x)
        return ret
