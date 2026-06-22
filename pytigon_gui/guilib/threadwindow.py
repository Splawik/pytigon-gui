"""Thread status window module.

Provides a GUI panel displayed in the status bar area that shows progress
and status information for background threads. Includes a manager that
handles layout and periodic updates.
"""

import wx
import wx.html
import logging

from pytigon_lib.schtools import schjson

logger = logging.getLogger(__name__)

schEVT_THREAD_INFO = wx.NewEventType()
EVT_THREAD_INFO = wx.PyEventBinder(schEVT_THREAD_INFO, 1)


class ThreadEvent(wx.PyCommandEvent):
    """Custom event carrying thread status information."""

    def __init__(self, evt_type, id_):
        """Initialize the event.

        Args:
            evt_type: Event type identifier.
            id_: Event source ID.
        """
        wx.PyCommandEvent.__init__(self, evt_type, id_)
        self.info = None

    def set_info(self, val):
        """Set the event payload.

        Args:
            val: Information to attach to the event.
        """
        self.info = val

    def get_info(self):
        """Get the event payload.

        Returns:
            The stored information.
        """
        return self.info


class SchThreadWindow(wx.Panel):
    """Status bar panel showing progress and info for a background thread.

    Displays a progress gauge, HTML description, and expand/kill buttons.
    """

    def __init__(self, manager, thread_name, parent):
        """Initialize the thread window.

        Args:
            manager: The SchThreadManager that owns this window.
            thread_name: Identifier for the background thread.
            parent: Parent window (typically the status bar).
        """
        wx.Panel.__init__(self, parent)
        self.thread_name = thread_name
        self.manager = manager
        self.closed = False

        self.SetBackgroundColour(wx.NamedColour("#eec"))

        self.gauge = wx.Gauge(self, range=100, size=(100, 1))
        self.gauge.SetValue(0)

        self.html = wx.html.HtmlWindow(
            self, size=(50, 50), style=wx.html.HW_SCROLLBAR_NEVER
        )
        self.html.SetBorders(0)
        self.html.SetPage("<body bgcolor='#eec'></body>")

        bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_TO_PARENT, wx.ART_TOOLBAR, (16, 16))
        bmp = bmp.ConvertToImage().Rescale(16, 8).ConvertToBitmap()
        bmp2 = wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR, (16, 16))
        bmp2 = bmp2.ConvertToImage().Rescale(16, 8).ConvertToBitmap()

        button1 = wx.BitmapButton(self, -1, bmp)
        button2 = wx.BitmapButton(self, -1, bmp2)
        self.Bind(wx.EVT_BUTTON, self.on_expand, button1)
        self.Bind(wx.EVT_BUTTON, self.on_kill, button2)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.html, 1, wx.EXPAND)
        box.Add(self.gauge, 0, wx.EXPAND)
        box.Add(button1, 0, wx.EXPAND)
        box.Add(button2, 0, wx.EXPAND)
        self.SetSizer(box)
        box.Fit(self)

    def is_closed(self):
        """Check if the associated thread has completed.

        Returns:
            True if the thread is closed.
        """
        return self.closed

    def timer(self):
        """Periodic update - polls server for thread progress and status."""
        try:
            http = wx.GetApp().http
            response = http.get(
                self,
                "http://local.net/schsys/thread_short_info/" + self.thread_name,
            )
            info_json = response.str()
            info = schjson.loads(info_json)
        except Exception:
            logger.exception("Failed to poll thread info for %s", self.thread_name)
            return

        if isinstance(info, str) and info == "$$$":
            self.closed = True
            evt = ThreadEvent(schEVT_THREAD_INFO, -1)
            evt.set_info(self.thread_name)
            wx.GetApp().GetTopWindow().GetEventHandler().ProcessEvent(evt)
        elif info:
            if "progress" in info:
                try:
                    self.gauge.SetValue(int(info["progress"]))
                except (ValueError, TypeError):
                    pass
            if "description" in info:
                self.html.SetPage(
                    "<body bgcolor='#eec'>" + info["description"] + "</body>"
                )

    def on_expand(self, event):
        """Open a detailed view of the thread."""
        address = "http://local.net/schsys/thread_long_info/" + self.thread_name
        wx.GetApp().GetTopWindow().new_main_page(address, "aplikacja")

    def on_kill(self, event):
        """Request termination of the background thread."""
        try:
            http = wx.GetApp().http
            http.get(self, "http://local.net/schsys/thread_kill/" + self.thread_name)
        except Exception:
            logger.exception("Failed to kill thread %s", self.thread_name)


class SchThreadManager(object):
    """Manages multiple SchThreadWindow instances in a status bar.

    Handles layout, positioning, and periodic polling of thread windows.
    """

    def __init__(self, app, statusbar):
        """Initialize the thread manager.

        Args:
            app: The wx application.
            statusbar: The status bar to place thread windows in.
        """
        self.app = app
        self.statusbar = statusbar
        self.sizeChanged = True
        self.windows = []
        statusbar.Bind(wx.EVT_SIZE, self.on_size)
        statusbar.Bind(wx.EVT_IDLE, self.on_idle)

    def append(self, thread_address):
        """Add a new thread window for the given thread address.

        Args:
            thread_address: Identifier for the background thread.
        """
        self.windows.append(SchThreadWindow(self, thread_address, self.statusbar))
        self.sizeChanged = True

    def reposition(self):
        """Reposition and resize all thread windows in the status bar."""
        count = len(self.windows)
        if count == 0:
            return

        rect = self.statusbar.GetFieldRect(1)
        offset = 0
        for win in self.windows:
            win.SetPosition((int(rect.x + offset + 2), int(rect.y + 2)))
            win.SetSize(
                (
                    max(0, int(rect.width / count - 4)),
                    max(0, int(rect.height - 3)),
                )
            )
            offset += rect.width / count

    def on_size(self, evt):
        """Handle status bar resize event."""
        self.reposition()
        self.sizeChanged = True

    def on_idle(self, evt):
        """Handle idle event - reposition if size changed."""
        if self.sizeChanged:
            self.reposition()
            self.sizeChanged = False

    def timer(self):
        """Periodic update for all thread windows.

        Removes closed windows and polls open ones. Uses list slicing
        to safely iterate while modifying the list.
        """
        if not self.windows:
            return

        # Iterate over a copy to safely remove while iterating
        for win in self.windows[:]:
            if win.is_closed():
                win.Destroy()
                self.windows.remove(win)
                self.sizeChanged = True
            else:
                win.timer()
