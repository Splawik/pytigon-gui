"""
Top-level AUI manager classes for Pytigon window layout management.

Provides SChAuiBaseManager (base) and SChAuiManager, which wrap
wx.lib.agw.aui to add pane activation and hit-test refinements.
"""

import wx
from wx.lib.agw import aui
import logging

logger = logging.getLogger(__name__)


class SChAuiBaseManager(aui.framemanager.AuiManager):
    """Extended AuiManager that restricts sash dragging to non-client areas.

    Overrides OnLeftDown so that drag operations are only initiated when
    the hit-test type is not a pane border (types 0 or 1).
    """

    def __init__(self, *argi, **argv):
        aui.framemanager.AuiManager.__init__(self, *argi, **argv)
        self.Bind(wx.EVT_WINDOW_CREATE, self.DoUpdateEvt)

    def OnLeftDown(self, event):
        """Handle left mouse down, restricting drag to non-border areas.

        Only propagates the event to the parent handler if the hit-test
        result is a client or title-bar type.
        """
        part = self.HitTest(*event.GetPosition())
        if part.type not in (0, 1):
            super().OnLeftDown(event)


class SChAuiManager(SChAuiBaseManager):
    """AUI manager that stores pane info on added windows via SetPanel."""

    def __init__(self, *argi, **argv):
        aui.AuiManager.__init__(self, *argi, **argv)

    def AddPane(self, window, arg1, *argi, **argv):
        """Add a pane and call SetPanel on the window if supported.

        Args:
            window: The wx.Window to add as a pane.
            arg1: Pane info or direction argument.
            *argi: Additional positional arguments.
            **argv: Additional keyword arguments.

        Returns:
            Result of the parent AddPane call.
        """
        ret = aui.AuiManager.AddPane(self, window, arg1, *argi, **argv)
        if hasattr(window, "SetPanel"):
            window.SetPanel(arg1)
        return ret

    def ActivatePane(self, window):
        """Activate a pane, returning None on failure instead of raising.

        Args:
            window: The wx.Window whose pane should be activated.

        Returns:
            Result of parent ActivatePane, or None if it fails.
        """
        try:
            return aui.AuiManager.ActivatePane(self, window)
        except Exception:
            logger.debug("ActivatePane failed for window: %s", window, exc_info=True)
            return None
