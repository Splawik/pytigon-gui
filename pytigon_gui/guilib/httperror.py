"""HTTP error dialog module.

Provides a dialog for displaying HTTP error responses to the user,
with options to continue or break the application.
"""

import wx
import sys
import logging

import pytigon_gui.guictrl.ctrl

_ = wx.GetTranslation
logger = logging.getLogger(__name__)


class HttpErrorDialog(wx.Dialog):
    """Dialog that displays an HTML error page returned by an HTTP server.

    Provides Continue and Break buttons. Choosing Break terminates the
    application.
    """

    def __init__(
        self,
        parent,
        title,
        text,
        size=wx.DefaultSize,
        pos=wx.DefaultPosition,
        style=wx.DEFAULT_DIALOG_STYLE,
        use_metal=False,
    ):
        """Initialize the error dialog.

        Args:
            parent: Parent window.
            title: Dialog title.
            text: HTML content to display.
            size: Dialog size (default: wx.DefaultSize).
            pos: Dialog position (default: wx.DefaultPosition).
            style: Dialog style flags.
            use_metal: Use metal look on macOS.
        """
        try:
            pre = wx.PreDialog()
            pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
            pre.Create(parent, wx.ID_ANY, title, pos, size, style)
            self.PostCreate(pre)
        except Exception:
            wx.Dialog.__init__(self, parent, wx.ID_ANY, title, pos, size, style)

        if "wxMac" in wx.PlatformInfo and use_metal:
            self.SetExtraStyle(wx.DIALOG_EX_METAL)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.label = pytigon_gui.guictrl.ctrl.HTML2(
            self, size=(1024, 768), name="webbrowser"
        )

        try:
            sizer.Add(self.label.wb, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        except AttributeError:
            sizer.Add(self.label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK, _("Continue"))
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL, _("Break"))
        btn.SetHelpText(_("The Break button breaks the application"))
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        wx.CallAfter(self.label.load_str, text)

    def set_acc_key_tab(self, ctrl, tab):
        """Placeholder for keyboard accelerator setup (not used)."""
        pass


def _http_error(parent, content):
    """Show a modal dialog with error content returned by an HTTP server.

    Args:
        parent: Parent window.
        content: HTML page returned by HTTP server (str or bytes).
    """
    app = wx.GetApp()
    if app.lock:
        return

    app.lock = True
    val = None

    try:
        if parent and hasattr(parent, "Invalidate"):
            parent.Invalidate()

        if isinstance(content, str):
            c = content
        else:
            c = content.decode("utf-8")

        dlg = HttpErrorDialog(
            app.GetTopWindow(), _("Error message"), c, size=(800, 600)
        )
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
    except Exception as e:
        logger.error("Error displaying HTTP error dialog: %s", e)
    finally:
        app.lock = False

    if val == wx.ID_CANCEL:
        sys.exit()


def http_error(parent, content):
    """Schedule an HTTP error dialog to be shown in the main GUI thread.

    Args:
        parent: Parent window.
        content: HTML error page content.
    """
    wx.CallAfter(_http_error, parent, content)
