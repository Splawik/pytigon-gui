"""Pytigon application installation wizard module.

Provides a wxWizard-based installer for .ptig archive files.
"""

import wx

try:
    from wx.adv import Wizard, WizardPageSimple, EVT_WIZARD_PAGE_CHANGING
except ImportError:
    from wx.wizard import Wizard, WizardPageSimple

    EVT_WIZARD_PAGE_CHANGING = wx.wizard.EVT_WIZARD_PAGE_CHANGING

import configparser
import logging
from pathlib import Path

from pytigon_lib.schtools.install import Ptig
from pytigon_gui.guilib.tools import create_desktop_shortcut

_ = wx.GetTranslation
logger = logging.getLogger(__name__)


def make_page_title(wiz_pg, title):
    """Create a standard title block for a wizard page.

    Args:
        wiz_pg: Wizard page instance.
        title: Title text to display.

    Returns:
        wx.BoxSizer containing the title layout.
    """
    sizer = wx.BoxSizer(wx.VERTICAL)
    wiz_pg.SetSizer(sizer)
    title_ctrl = wx.StaticText(wiz_pg, -1, title)
    title_ctrl.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
    sizer.Add(title_ctrl, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
    sizer.Add(wx.StaticLine(wiz_pg, -1), 0, wx.EXPAND | wx.ALL, 5)
    return sizer


class TitledPage(WizardPageSimple):
    """A wizard page with a pre-formatted title."""

    def __init__(self, parent, lp, title):
        """Initialize the titled page.

        Args:
            parent: Parent wizard.
            lp: Logical page number.
            title: Page title.
        """
        WizardPageSimple.__init__(self, parent)
        self.sizer = make_page_title(self, title)
        self.lp = lp


class InstallWizard(Wizard):
    """Installation wizard for .ptig application archives."""

    def __init__(self, file_name):
        """Initialize the wizard.

        Args:
            file_name: Path to the .ptig archive file.
        """
        Wizard.__init__(self, None, -1, "Install app")
        self.Bind(EVT_WIZARD_PAGE_CHANGING, self.on_wiz_page_changing)
        self.ptig = Ptig(file_name)

        page1 = TitledPage(self, 1, _("Program description"))
        self.page1 = page1
        page2 = TitledPage(self, 2, _("License"))
        page3 = TitledPage(self, 3, _("Run"))

        r_txt = wx.TextCtrl(
            page1, -1, size=wx.Size(600, 300), style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        r_txt.SetValue(self.ptig.get_readme())
        page1.sizer.Add(r_txt)
        self.FitToPage(page1)

        l_txt = wx.TextCtrl(
            page2,
            -1,
            self.ptig.get_license(),
            size=wx.Size(600, 300),
            style=wx.TE_MULTILINE | wx.TE_READONLY,
        )
        page2.sizer.Add(l_txt)
        page2.sizer.AddSpacer(5)
        self.licence = wx.CheckBox(page2, -1, _("Accept"))
        page2.sizer.Add(self.licence)

        page3.sizer.Add(
            wx.StaticText(page3, -1, _("Run the installed program or cancel"))
        )

        WizardPageSimple.Chain(page1, page2)
        WizardPageSimple.Chain(page2, page3)
        self.GetPageAreaSizer().Add(page1)

    def run(self):
        """Run the wizard and return whether installation completed.

        Returns:
            True if the wizard finished successfully, False otherwise.
        """
        ret = self.RunWizard(self.page1)
        wx.CallAfter(self.Destroy)
        return ret

    def on_wiz_page_changing(self, event):
        """Handle page changing event - validate license acceptance.

        Args:
            event: wxWizardEvent.
        """
        if event.GetPage().lp == 2 and event.GetDirection():
            if not self.licence.GetValue():
                wx.MessageBox(
                    _("You must accept the license or cancel the installation!"),
                    _("Installation"),
                )
                event.Veto()
                return
            else:
                if not self.install():
                    wx.MessageBox(_("Installation error!"), _("Installation"))
                    event.Veto()
                    return
        if event.GetPage().lp == 3 and not event.GetDirection():
            wx.MessageBox(
                _("Program installed, use the uninstaller!"), _("Installation")
            )
            event.Veto()
            return
        event.Skip()

    def install(self):
        """Extract the .ptig archive and create desktop shortcut.

        Returns:
            True always (installation errors are logged).
        """
        try:
            self.ptig.extract_ptig()
        except Exception:
            logger.exception("Failed to extract ptig archive")
            return False

        ini_file = Path(self.ptig.extract_to) / "install.ini"
        shortcut_created = False

        if Path(ini_file).exists():
            try:
                config = configparser.ConfigParser()
                config.read(ini_file)
                if "INSTALL" in config.sections():
                    install = config["INSTALL"]
                    title = install.get("Title", self.ptig.prj_name)
                    parameters = install.get("Parameters", "")
                    create_desktop_shortcut(self.ptig.prj_name, title, parameters)
                    shortcut_created = True
            except Exception:
                logger.exception("Error reading install.ini")

        if not shortcut_created:
            create_desktop_shortcut(self.ptig.prj_name, self.ptig.prj_name)

        return True


def install(ptig_path):
    """Launch the installation wizard for a .ptig file.

    Args:
        ptig_path: Path to the .ptig archive.

    Returns:
        True if installation completed, False otherwise.
    """
    wizard = InstallWizard(ptig_path)
    return wizard.run()
