#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

# Pytigon - wxpython and django application framework

# author: "Slawomir Cholaj (slawomir.cholaj@gmail.com)"
# copyright: "Copyright (C) ????/2012 Slawomir Cholaj"
# license: "LGPL 3.0"
# version: "0.1a"

import os
import wx
import pytigon_gui.guictrl.ctrl

from pytigon_gui.guilib.tools import import_plugin


class SchBaseFrame(wx.Frame):
    """
    This is main window of pytigon application
    """

    def __init__(
        self,
        parent,
        gui_style="tree(toolbar,statusbar)",
        id=-1,
        title="",
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.WANTS_CHARS,
        name="MainWindow",
    ):
        wx.Frame.__init__(self, None, wx.ID_ANY, title, pos, size, style, "MainWindow")
        self.run_on_close = []
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def init_plugins(self):
        home_dir = wx.GetApp().get_working_dir()
        app_plugins = os.path.join(wx.GetApp().cwd, "plugins")
        dirnames = [
            os.path.join(wx.GetApp().pytigon_path, "appdata", "plugins"),
            os.path.join(wx.GetApp().data_path, "plugins"),
            app_plugins,
        ]
        auto_plugins = wx.GetApp().config["Global settings"]["auto_plugins"].split(";")
        for dirname in dirnames:
            if not os.path.exists(dirname):
                continue
            for ff in os.listdir(dirname):
                if os.path.isdir(os.path.join(dirname, ff)):
                    dirname2 = os.path.join(dirname, ff)
                    pliki = []
                    for f in os.listdir(dirname2):
                        pliki.append(f)
                    pliki.sort()

                    for f in pliki:
                        if True:
                            if os.path.isdir(os.path.join(dirname2, f)):
                                # p = dirname2.split('/')
                                mod_name = ff + "." + f
                                x = mod_name.replace(".", "/")
                                if (
                                    ff == "auto"
                                    or (
                                        wx.GetApp().plugins and x in wx.GetApp().plugins
                                    )
                                    or x in auto_plugins
                                ):
                                    if ".__" in mod_name:
                                        break
                                    mod = import_plugin(mod_name)
                                    if hasattr(mod, "init_plugin"):
                                        destroy = mod.init_plugin(
                                            wx.GetApp(),
                                            self,
                                            self.desktop,
                                            self._mgr,
                                            self.get_menu_bar(),
                                            self.toolbar_interface,
                                            self.aTable,
                                        )
                                        if destroy != None:
                                            self.destroy_fun_tab.append(destroy)
                        # except:
                        #    import traceback
                        #    print("Error load plugin: ", mod_name)
                        #    print(sys.exc_info()[0])
                        #    print(traceback.print_exc())

    def on_close(self, event):
        for fun in self.run_on_close:
            fun(self)
        event.Skip()
