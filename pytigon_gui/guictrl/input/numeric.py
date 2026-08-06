"""
Numeric input widget classes for the SchForm GUI framework.

Provides wxPython numeric entry controls integrated with SchBaseCtrl:
integer spin, float spin, currency amount, slider, gauge (progress bar),
and ticker (scrolling text).

Classes:
    NUM, AMOUNT, FLOAT, SPIN, SLIDER, GAUGE, TICKER, PROGRESSDIALOG
"""

import wx
from wx.lib import ticker as wx_ticker

from pytigon_gui.guictrl.basectrl import SchBaseCtrl, to_int


class SPIN(wx.SpinCtrl, SchBaseCtrl):
    """Integer spin control.

    Handles ctrlspinbutton tag. Wraps wx.SpinCtrl for integer
    value selection with up/down arrows.

    Tag arguments:
        value: Initial integer value.
    """

    def __init__(self, parent, **kwds):
        """Initialize the integer spin control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.SpinCtrl. Integer bounds read
                from param['min'] / param['max'].
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        minv = to_int(self.param.get("min"), None) if self.param else None
        maxv = to_int(self.param.get("max"), None) if self.param else None
        if minv is not None:
            kwds["min"] = minv
        if maxv is not None:
            kwds["max"] = maxv
        wx.SpinCtrl.__init__(self, parent, **kwds)
        if self.param and "inc" in self.param:
            inc = to_int(self.param["inc"], None)
            if inc is not None:
                self.SetIncrement(inc)


class NUM(wx.SpinCtrl, SchBaseCtrl):
    """Numeric spin control with optional readonly and process_enter.

    Handles ctrlnum tag. Similar to SPIN but supports process_enter
    key handling and readonly mode via TE_READONLY style.

    Tag arguments:
        value: Initial integer value.
        process_enter: If set in param, enables TE_PROCESS_ENTER.
        readonly: If True, adds TE_READONLY style.
    """

    def __init__(self, parent, **kwds):
        """Initialize the numeric spin control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.SpinCtrl with optional
                TE_PROCESS_ENTER and TE_READONLY styles.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param and "process_enter" in self.param:
            kwds["style"] = kwds.get("style", 0) | wx.TE_PROCESS_ENTER
        if self.readonly:
            kwds["style"] = kwds.get("style", 0) | wx.TE_READONLY
        wx.SpinCtrl.__init__(self, parent, **kwds)


class AMOUNT(wx.SpinCtrlDouble, SchBaseCtrl):
    """Currency/amount spin control with double precision (2 digits).

    Handles ctrlamount tag. Supports min/max bounds from param,
    process_enter, readonly mode, and arrow key navigation.

    Tag arguments:
        value: Initial float value.
        process_enter: If set in param, enables TE_PROCESS_ENTER.
        readonly: If True, adds TE_READONLY style.
        min: Minimum value (float, default -100000000).
        max: Maximum value (float, default 100000000).
    """

    def __init__(self, parent, **kwds):
        """Initialize the amount spin control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.SpinCtrlDouble with increment
                of 1, 2 decimal digits, and configurable bounds.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param and "process_enter" in self.param:
            kwds["style"] = kwds.get("style", 0) | wx.TE_PROCESS_ENTER
        if self.readonly:
            kwds["style"] = kwds.get("style", 0) | wx.TE_READONLY

        kwds["inc"] = 1

        if self.param and "min" in self.param:
            kwds["min"] = float(self.param["min"])
        else:
            kwds["min"] = -100000000
        if self.param and "max" in self.param:
            kwds["max"] = float(self.param["max"])
        else:
            kwds["max"] = 100000000

        kwds["style"] = kwds.get("style", 0) | wx.SP_ARROW_KEYS | wx.ALIGN_RIGHT

        wx.SpinCtrlDouble.__init__(self, parent, **kwds)
        self.SetDigits(2)


class FLOAT(wx.SpinCtrlDouble, SchBaseCtrl):
    """Floating-point spin control with high precision (6 digits).

    Handles ctrlfloat tag. Similar to AMOUNT but with 6 decimal
    digits for scientific/general float input.

    Tag arguments:
        value: Initial float value.
        process_enter: If set in param, enables TE_PROCESS_ENTER.
        readonly: If True, adds TE_READONLY style.
        min: Minimum value (float, default -100000000).
        max: Maximum value (float, default 100000000).
    """

    def __init__(self, parent, **kwds):
        """Initialize the float spin control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.SpinCtrlDouble with increment
                of 1, 6 decimal digits, and configurable bounds.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param and "process_enter" in self.param:
            kwds["style"] = wx.TE_PROCESS_ENTER
        if self.readonly:
            style = 0
            if "style" in kwds:
                style = kwds["style"]
            style = style | wx.TE_READONLY
            kwds["style"] = style

        kwds["inc"] = 1

        if self.param and "min" in self.param:
            kwds["min"] = float(self.param["min"])
        else:
            kwds["min"] = -100000000
        if self.param and "max" in self.param:
            kwds["max"] = float(self.param["max"])
        else:
            kwds["max"] = 100000000

        kwds["style"] = kwds.get("style", 0) | wx.SP_ARROW_KEYS | wx.ALIGN_RIGHT

        wx.SpinCtrlDouble.__init__(self, parent, **kwds)
        self.SetDigits(6)


class SLIDER(wx.Slider, SchBaseCtrl):
    """Slider control for selecting a value from a range.

    Handles ctrlslider tag. Thin wrapper around wx.Slider.

    Tag arguments:
        value: Initial slider position.
    """

    def __init__(self, parent, **kwds):
        """Initialize the slider control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.Slider. Range read from
                param['min'] / param['max'].
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        if self.param:
            minv = to_int(self.param.get("min"), None)
            maxv = to_int(self.param.get("max"), None)
            if minv is not None:
                kwds["minValue"] = minv
            if maxv is not None:
                kwds["maxValue"] = maxv
        wx.Slider.__init__(self, parent, **kwds)
        val = to_int(self.value, None)
        if val is not None:
            self.SetValue(val)


class GAUGE(wx.Gauge, SchBaseCtrl):
    """Progress gauge (progress bar) control.

    Handles ctrlgauge tag. Displays progress as a horizontal bar.
    Value can be set via process_refr_data.

    Tag arguments:
        value: Current gauge value (integer).
        min: Minimum range value (from param).
        max: Maximum range value (from param, default 100).
    """

    def __init__(self, parent, **kwds):
        """Initialize the gauge control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.Gauge with range from param.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        maxv = to_int(self.param.get("max"), None) if self.param else None
        if maxv is not None:
            kwds["range"] = maxv
        kwds.setdefault("range", 100)
        wx.Gauge.__init__(self, parent, **kwds)
        val = to_int(self.value, None)
        if val is not None:
            self.SetValue(val)

    def process_refr_data(self, **kwds):
        """Refresh the gauge with new data.

        Args:
            **kwds: New keyword arguments. If 'value' is present
                in the underlying self.value, updates the gauge.
        """
        self.init_base(kwds)
        val = to_int(self.value, None)
        if val is not None:
            self.SetValue(val)


class TICKER(wx_ticker.Ticker, SchBaseCtrl):
    """Scrolling ticker text control.

    Handles ctrlticker tag. Displays scrolling text.
    Stops the ticker when the control is closed.

    Tag arguments:
        value: Text to scroll.
    """

    def __init__(self, parent, **kwds):
        """Initialize the ticker control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.lib.ticker.Ticker.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        wx_ticker.Ticker.__init__(self, parent, **kwds)

    def SetValue(self, value):
        """Set the scrolling text value.

        Args:
            value: Text string to display.
        """
        self.SetText(value)

    def CanClose(self):
        """Stop the ticker before closing.

        Returns:
            True always, after stopping the ticker animation.
        """
        self.Stop()
        return True


class PROGRESSDIALOG(wx.ProgressDialog, SchBaseCtrl):
    """Indeterminate/determinate progress dialog.

    Handles ctrlprogressdialog tag. A modal progress window driven
    by a server task. The dialog is shown when created and updated
    via refresh_value/process_refr_data.

    Tag arguments:
        label: Dialog title/message.
        value: Current progress value.
        length: Total progress length (default 100).
    """

    def __init__(self, parent, **kwds):
        """Initialize the progress dialog.

        Args:
            parent: Parent window.
            **kwds: Forwarded to wx.ProgressDialog. 'length' gives
                the maximum value.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        message = kwds.get("message", self.label or "")
        maximum = to_int(self.length, None) or 100
        kwds["message"] = message
        kwds["maximum"] = maximum
        wx.ProgressDialog.__init__(self, parent, **kwds)
        self.max = maximum
        val = to_int(self.value, None)
        if val is not None:
            self.Refresh(val, "Progress")

    def refresh_value(self, value, message=None):
        """Update the progress dialog value and message.

        Args:
            value: New progress value (0..maximum).
            message: Optional new message text.

        Returns:
            The continue flag (True if the dialog is still open).
        """
        cont, _skip = self.Update(to_int(value, 0), message)
        return cont

    def process_refr_data(self, **kwds):
        """Refresh the progress dialog from new data.

        Args:
            **kwds: New keyword arguments with 'value' and optional
                'label'/'message'.
        """
        self.init_base(kwds)
        val = to_int(self.value, None)
        if val is not None:
            self.Refresh(val, self.label or "")

    def CanAcceptFocus(self):
        """Progress dialogs do not accept keyboard focus."""
        return False

