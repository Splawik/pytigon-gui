"""Module containing all user-defined wx event IDs.

Provides a centralized registry of wx.Window.NewControlId() identifiers used throughout
the application for menu commands, toolbar actions, and custom events.
"""

import wx

# ---- Navigation and tab management ----
ID_START = wx.Window.NewControlId()
ID_NEXTTAB = wx.Window.NewControlId()
ID_PREVTAB = wx.Window.NewControlId()
ID_CLOSETAB = wx.Window.NewControlId()
ID_NEXTPAGE = wx.Window.NewControlId()
ID_PREVPAGE = wx.Window.NewControlId()
ID_REFRESHTAB = wx.Window.NewControlId()

# ---- Application control ----
ID_EXIT = wx.Window.NewControlId()
ID_RESET = wx.Window.NewControlId()

# ---- Edit operations ----
ID_UNDO = wx.Window.NewControlId()
ID_REDO = wx.Window.NewControlId()
ID_CUT = wx.Window.NewControlId()
ID_COPY = wx.Window.NewControlId()
ID_PASTE = wx.Window.NewControlId()
ID_SELALL = wx.Window.NewControlId()

# ---- Help ----
ID_HELP = wx.Window.NewControlId()

# ---- Panel/view navigation ----
ID_GOTOHEADER = wx.Window.NewControlId()
ID_GOTOPANEL = wx.Window.NewControlId()
ID_GOTOFOOTER = wx.Window.NewControlId()
ID_GOTODESKTOP = wx.Window.NewControlId()
ID_SHOWHEADER = wx.Window.NewControlId()
ID_SHOWPANEL = wx.Window.NewControlId()
ID_SHOWFOOTER = wx.Window.NewControlId()
ID_SHOWDESKTOP = wx.Window.NewControlId()
ID_SHOWTOOLBAR1 = wx.Window.NewControlId()
ID_SHOWTOOLBAR2 = wx.Window.NewControlId()
ID_SHOWSTATUSBAR = wx.Window.NewControlId()

# ---- Return value ----
ID_RETVALUE = wx.Window.NewControlId()

# ---- Page/zoom operations ----
ID_ZOOM = wx.Window.NewControlId()
ID_PAGE_SOURCE = wx.Window.NewControlId()
ID_PAGE_BLOCK = wx.Window.NewControlId()
ID_PAGE_VIEW = wx.Window.NewControlId()

# ---- History and bookmarks ----
ID_HISTORY_SHOW = wx.Window.NewControlId()
ID_CLEAR_HISTORY = wx.Window.NewControlId()
ID_BOOKMARK_ADD = wx.Window.NewControlId()
ID_SHOW_BOOKMARKS = wx.Window.NewControlId()

# ---- Download and options ----
ID_SHOW_DOWNLOAD = wx.Window.NewControlId()
ID_DOWNLOAD_OPTIONS = wx.Window.NewControlId()
ID_GENERAL_OPTIONS = wx.Window.NewControlId()

# ---- Find/Replace ----
ID_FIND = wx.Window.NewControlId()
ID_REPLACE = wx.Window.NewControlId()

# ---- Print operations ----
ID_PRINT = wx.Window.NewControlId()
ID_PRINT_PREVIEW = wx.Window.NewControlId()
ID_PRINT_SETTINGS = wx.Window.NewControlId()

# ---- Web browser navigation ----
ID_WEB_BACK = wx.Window.NewControlId()
ID_WEB_FORWARD = wx.Window.NewControlId()
ID_WEB_STOP = wx.Window.NewControlId()
ID_WEB_REFRESH = wx.Window.NewControlId()
ID_WEB_ADDBOOKMARK = wx.Window.NewControlId()
ID_WEB_NEW_WINDOW = wx.Window.NewControlId()
ID_WEB_SOURCE = wx.Window.NewControlId()
ID_WEB_UP = wx.Window.NewControlId()
ID_WEB_DOWN = wx.Window.NewControlId()
ID_WEB_EDIT = wx.Window.NewControlId()

# ---- Taskbar control ----
ID_TASKBAR_SHOW = wx.Window.NewControlId()
ID_TASKBAR_HIDE = wx.Window.NewControlId()
ID_TASKBAR_CLOSE = wx.Window.NewControlId()
ID_TASKBAR_TOGGLE = wx.Window.NewControlId()

# ---- File operations ----
ID_LOAD = wx.Window.NewControlId()
ID_SAVE = wx.Window.NewControlId()
ID_SAVE_AS = wx.Window.NewControlId()

# ---- Sentinel / end marker ----
ID_END = wx.Window.NewControlId()
