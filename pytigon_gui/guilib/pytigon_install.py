import wx

try:
    from wx.adv import Wizard, WizardPageSimple
except:
    from wx.wizard import Wizard, WizardPageSimple

import zipfile
import os
import configparser

from pytigon_lib.schtools.install import Ptig
from pytigon_gui.guilib.tools import create_desktop_shortcut

_ = wx.GetTranslation


def make_page_title(wiz_pg, title):
    sizer = wx.BoxSizer(wx.VERTICAL)
    wiz_pg.SetSizer(sizer)
    title = wx.StaticText(wiz_pg, -1, title)
    title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
    sizer.Add(title, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
    sizer.Add(wx.StaticLine(wiz_pg, -1), 0, wx.EXPAND | wx.ALL, 5)
    return sizer


class TitledPage(WizardPageSimple):
    def __init__(self, parent, lp, title):
        WizardPageSimple.__init__(self, parent)
        self.sizer = make_page_title(self, title)
        self.lp = lp


class InstallWizard(Wizard):
    def __init__(self, file_name):
        Wizard.__init__(self, None, -1, "Install app")
        self.Bind(wx.adv.EVT_WIZARD_PAGE_CHANGING, self.on_wiz_page_changing)
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
        ret = self.RunWizard(self.page1)
        wx.CallAfter(self.Destroy)
        return ret

    def on_wiz_page_changing(self, event):
        if event.GetPage().lp == 2 and event.GetDirection():
            value = self.licence.GetValue()
            if not value:
                wx.MessageBox(
                    _("You must accept the license or cancel the installation!"),
                    _("Installation"),
                )
                event.Veto()
                return
            else:
                if self.install():
                    return
                else:
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
        self.ptig.extract_ptig()

        ini_file = os.path.join(self.ptig.extract_to, "install.ini")
        created = False
        if os.path.exists(ini_file):
            config = configparser.ConfigParser()
            config.read(ini_file)
            if "INSTALL" in config.sections():
                install = config["INSTALL"]
                title = install.get("Title", self.ptig.prj_name)
                parameters = install.get("Parameters", "")
                create_desktop_shortcut(self.ptig.prj_name, title, parameters)

        if not created:
            create_desktop_shortcut(self.ptig.prj_name, self.ptig.prj_name)

        return True


def install(ptig_path):
    wizard = InstallWizard(ptig_path)
    if wizard.run():
        return True
    else:
        return False
