"""
Date and time widget classes for the SchForm GUI framework.

Provides wxPython date/time controls integrated with SchBaseCtrl:
calendar, date picker (platform-specific), date-time picker, and time control.

Classes:
    CALENDAR, DATEPICKER, DATETIMEPICKER, TIME
"""

import platform
import datetime

import wx
from wx.adv import CalendarCtrl
from wx.lib import masked

from pytigon_gui.guictrl.basectrl import SchBaseCtrl
from pytigon_lib.schparser.html_parsers import Td


class CALENDAR(CalendarCtrl, SchBaseCtrl):
    """Calendar control for date selection.

    Handles ctrlcalendar tag. Displays a monthly calendar grid
    with Monday as the first day of the week, holiday highlighting,
    and sequential month selection.

    Tag arguments:
        value: Initial date value.
    """

    def __init__(self, parent, **kwds):
        """Initialize the calendar control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to CalendarCtrl with platform-appropriate
                style flags (wx.adv vs wx.calendar namespace).
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        try:
            CalendarCtrl.__init__(
                self,
                parent,
                style=wx.adv.CAL_MONDAY_FIRST
                | wx.adv.CAL_SHOW_HOLIDAYS
                | wx.adv.CAL_SEQUENTIAL_MONTH_SELECTION,
                **kwds,
            )
        except AttributeError:
            CalendarCtrl.__init__(
                self,
                parent,
                style=wx.calendar.CAL_MONDAY_FIRST
                | wx.calendar.CAL_SHOW_HOLIDAYS
                | wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION,
                **kwds,
            )


class TIME(masked.TimeCtrl, SchBaseCtrl):
    """Time input control with mask validation.

    Handles ctrltime tag. Uses wx.lib.masked.TimeCtrl for
    formatted time entry with validation.

    Tag arguments:
        value: Initial time value.
    """

    def __init__(self, parent, **kwds):
        """Initialize the time control.

        Args:
            parent: Parent window.
            **kwds: Forwarded to masked.TimeCtrl.
        """
        SchBaseCtrl.__init__(self, parent, kwds)
        masked.TimeCtrl.__init__(self, parent, **kwds)


# -----------------------------------------------------------------------
# DATEPICKER - platform-specific implementation
# On Linux, uses a popup HTML-based date dialog.
# On other platforms, uses the native wx.adv.DatePickerCtrl.
# -----------------------------------------------------------------------

if platform.system() == "Linux":

    class DATEPICKER(SchBaseCtrl):
        """Date picker control (Linux: popup-based).

        On Linux, uses a popup HTML dialog for date selection
        with a masked text input showing YYYY-MM-DD format.
        Defaults to today's date if no value is provided.

        Tag arguments:
            value: Initial date value in ISO format (YYYY-MM-DD).
        """

        def __init__(self, parent, **kwds):
            """Initialize the Linux date picker.

            Args:
                parent: Parent window.
                **kwds: Forwarded to the underlying POPUPHTML control.
            """
            # Deferred import to avoid circular dependency
            from pytigon_gui.guictrl.display import POPUPHTML

            kwds["href"] = wx.GetApp().make_href("/schsys/datedialog/")

            if "style" in kwds:
                kwds["style"] = kwds["style"] | wx.WANTS_CHARS
            else:
                kwds["style"] = wx.WANTS_CHARS

            if "size" in kwds:
                kwds["size"] = wx.Size(150, kwds["size"].height)
            else:
                kwds["size"] = wx.Size(150, -1)

            SchBaseCtrl.__init__(self, parent, kwds)
            POPUPHTML.__init__(self, parent, **kwds)

            if self.value:
                self.set_rec(self.value, Td(self.value))
            else:
                today = wx.DateTime.Today().FormatISODate()
                self.set_rec(today, Td(today), False)

            wx.CallAfter(
                self.to_masked,
                mask="####-##-##",
                formatcodes="F",
                validRegex=r"\d{4}-\d{2}-\d{2}",
            )

        def GetValue(self):
            """Get the current date value.

            Returns:
                Date string from the stored record, or the raw
                record value.
            """
            value = self.get_rec()
            if value.data:
                return value.data
            else:
                return value

        def GetBestSize(self):
            """Return the best size for the date picker.

            Returns:
                Tuple of (130, height).
            """
            # Deferred import
            from pytigon_gui.guictrl.display import POPUPHTML

            dx, dy = POPUPHTML.GetBestSize(self)
            return (130, dy)

else:

    class DATEPICKER(wx.adv.DatePickerCtrl, SchBaseCtrl):
        """Date picker control (non-Linux: native).

        Uses the platform's native date picker control with
        dropdown calendar, century display, and allow-none support.

        Tag arguments:
            value: Initial date value in ISO format (YYYY-MM-DD).
        """

        def __init__(self, parent, **kwds):
            """Initialize the native date picker.

            Args:
                parent: Parent window.
                **kwds: Forwarded to DatePickerCtrl with dropdown,
                    show-century, and allow-none styles.
            """
            SchBaseCtrl.__init__(self, parent, kwds)
            kwds["size"] = (120, -1)
            try:
                kwds["style"] = (
                    wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY | wx.adv.DP_ALLOWNONE
                )
            except AttributeError:
                kwds["style"] = wx.DP_DROPDOWN | wx.DP_SHOWCENTURY | wx.DP_ALLOWNONE
            wx.adv.DatePickerCtrl.__init__(self, parent, **kwds)

        def SetValue(self, value):
            """Set the date value from a string.

            Args:
                value: Date string in parseable format, or None
                    to clear the selection.
            """
            if value:
                date = wx.DateTime()
                date.ParseDate(value)
                wx.adv.DatePickerCtrl.SetValue(self, date)
            else:
                wx.adv.DatePickerCtrl.SetValue(self, None)

        def GetValue(self):
            """Get the current date in ISO format.

            Returns:
                Date string in YYYY-MM-DD format, or None.
            """
            value = wx.adv.DatePickerCtrl.GetValue(self)
            if value:
                return value.FormatISODate()
            else:
                return None


class DATETIMEPICKER(SchBaseCtrl):
    """Date-time picker control with popup dialog.

    Handles ctrldatetimepicker tag. Provides combined date and time
    selection with a masked input in 'YYYY-MM-DD HH:MM' format.

    Tag arguments:
        value: Initial date-time value in 'YYYY-MM-DD HH:MM' format.
    """

    def __init__(self, parent, **kwds):
        """Initialize the date-time picker.

        Args:
            parent: Parent window.
            **kwds: Forwarded to the underlying POPUPHTML control.
        """
        from pytigon_gui.guictrl.display import POPUPHTML

        kwds["href"] = wx.GetApp().make_href("/schsys/datedialog/")

        if "style" in kwds:
            kwds["style"] = kwds["style"] | wx.WANTS_CHARS
        else:
            kwds["style"] = wx.WANTS_CHARS

        if "size" in kwds:
            kwds["size"] = wx.Size(200, kwds["size"].height)
        else:
            kwds["size"] = wx.Size(200, -1)

        SchBaseCtrl.__init__(self, parent, kwds)
        POPUPHTML.__init__(self, parent, **kwds)

        self.to_masked(
            mask="####-##-## ##:##",
            formatcodes="F",
            validRegex=r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}",
        )

        if self.value:
            self.set_rec(self.value, Td(self.value))
        else:
            now = datetime.datetime.now().isoformat().replace("T", " ")[:16]
            self.set_rec(now, Td(now), False)

    def set_rec(self, value, value_rec, dismiss=False):
        """Set the record value, padding time if needed.

        Args:
            value: Date-time string.
            value_rec: Td record object.
            dismiss: Whether to dismiss the popup.

        Returns:
            Result from parent set_rec.
        """
        from pytigon_gui.guictrl.display import POPUPHTML

        if len(value) == 16:
            return POPUPHTML.set_rec(self, value, value_rec, dismiss)
        elif len(value) == 10:
            value_rec.data = value_rec.data + " 00:00"
            return POPUPHTML.set_rec(self, value + " 00:00", value_rec, dismiss)
        else:
            return POPUPHTML.set_rec(self, "0000.00.00 00:00", value_rec, dismiss)

    def GetValue(self):
        """Get the current date-time value.

        Returns:
            Date-time string from the record, or parsed from
            the text control if the record is empty.
        """
        from pytigon_gui.guictrl.display import POPUPHTML

        value = self.get_rec()
        value2 = self.GetTextCtrl().GetValue()
        if value2 and value2[0] != " ":
            if value.data:
                return value.data
            else:
                return [
                    datetime.datetime.strptime(value2, "%Y-%m-%d %H:%M"),
                ]
        return None

    def GetBestSize(self):
        """Return the best size for the date-time picker.

        Returns:
            Tuple of (180, height).
        """
        from pytigon_gui.guictrl.display import POPUPHTML

        dx, dy = POPUPHTML.GetBestSize(self)
        return (180, dy)
