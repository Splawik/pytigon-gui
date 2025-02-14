"""
Top window
"""

from wx.lib.agw import aui
import wx


class SChAuiBaseManager(aui.framemanager.AuiManager):
    def __init__(self, *argi, **argv):
        aui.framemanager.AuiManager.__init__(self, *argi, **argv)
        self.Bind(wx.EVT_WINDOW_CREATE, self.DoUpdateEvt)

    # def Update(self):
    #    if '__WXGTK__' in wx.PlatformInfo:
    #        def _fun():
    #            self.DoUpdate()
    #            if self._frame:
    #                self._frame.Refresh()
    #        wx.CallAfter(_fun)
    #    else:
    #        super().Update()

    # def OnRender(self, event):
    #    if self._frame and self._frame.GetHandle():
    #        super().OnRender(event)
    #    else:
    #        event.Skip()

    def OnLeftDown(self, event):
        part = self.HitTest(*event.GetPosition())
        if not part.type in [0, 1]:
            super().OnLeftDown(event)


class SChAuiManager(SChAuiBaseManager):
    def __init__(self, *argi, **argv):
        aui.AuiManager.__init__(self, *argi, **argv)

    def AddPane(self, window, arg1, *argi, **argv):
        ret = aui.AuiManager.AddPane(self, window, arg1, *argi, **argv)
        if hasattr(window, "SetPanel"):
            window.SetPanel(arg1)
        return ret

    def ActivatePane(self, window):
        try:
            ret = aui.AuiManager.ActivatePane(self, window)
        except:
            ret = None
        return ret
