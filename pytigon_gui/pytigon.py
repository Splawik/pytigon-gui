"""This is the main Pytigon client module. Function :func:`~pytigon_gui.pytigon.main` create SchApp object, which extends wxPython wx.App.
Function :func:`~pytigon_gui.pytigon.main` process pytigon command line arguments. Module supports:

- instalation of pytigon applications,

- Remote Procedure Calling protocol

- login to server process
"""

import os
import sys
from pathlib import Path
import time
import platform
import zipfile
import getopt
import configparser
import logging
from urllib.parse import urljoin
import contextlib
import pytigon

logger = logging.getLogger(__name__)

if platform.system() == "Windows":
    # grouping pytigon applicactions in the windows taskbar
    import ctypes

    myappid = "slawomir_cholaj.pytigon.main.01"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

CWD_PATH = Path.cwd().parent
SRC_PATH = Path(pytigon.__file__).parent

ROOT_PATH = str(SRC_PATH)

if ROOT_PATH.startswith("."):
    ROOT_PATH = str(CWD_PATH / ROOT_PATH)
sys.path.append(ROOT_PATH)
sys.path.append(str(Path(ROOT_PATH) / "appdata"))

os.environ["EMBEDED_DJANGO_SERVER"] = "1"

from pytigon_lib import init_paths

init_paths()

from pytigon_lib.schtools.env import get_environ

if platform.system() == "Windows":
    sys.path.insert(0, str(SRC_PATH / "ext_lib_cli_win"))
else:
    sys.path.insert(0, str(SRC_PATH / "ext_lib_cli_lin"))

_INSPECTION = False
_DEBUG = False
_TRACE = False
_VIDEO = False
_VIDEO_NAME = ""
_APP_SIZE = (1024, 768)
_RPC = False
_WEBSOCKET = None


def usage():
    sys.stdout.write(str(process_argv.__doc__) + "\n")


def process_argv(argv):
    """Run pytigon application: pytigon [option]... arg

    command line arguments:
        arg: project name, schdevtools for example
             or address of http server, http://www.pytigon.cloud for example
             or pytigon script name, test.schdevtools.schsimplescripts.ptig for example
             or pytigon installation file name
             or django management command in format: manage_[[package name]], manage_schdevtools runserver for example
             or python script, test.py for example

        options:
            -h, --help - show help

            -b --embededbrowser - run embeded browseer window
            -s --embededserver - run in background embeded http server
            --listen=<address>:<port> - set address and port for embeded serwer
            --menu_always - show menu event then configuration says otherwise
            --no_splash - do not show splash window
            --no_gui - run program without gui
            --server_only - run only http server
            --channels - start with channels library
            --websocket_id=relative address - embed websocket client, address can be mulitipart,
                           parts separated by a semicolon
            --no_gui - run program without gui

            --migrate - run django command: manage.py migrate
            --loaddb - run django command: manage.py loaddb

            --rpc=<port> - set tcp port of rpc
            --video - record video session
            -p <parameters>, --param=<parameters> - parametres of request to http server

            -d --debug - debug mode

            --inspection - turn on wxPython inspection
            --trace - show trace of python calls
    """
    try:
        (opts, args) = getopt.gnu_getopt(
            argv,
            "h:dmpbsu:p:",
            [
                "help",
                "username=",
                "password=",
                "embededbrowser",
                "embededserver",
                "embededtaskqueue",
                "websocket_id=",
                "channels",
                "migrate",
                "loaddb",
                "server_only",
                "debug",
                "rpc=",
                "param=",
                "inspection",
                "trace",
                "video=",
                "no_gui",
                "no_splash",
                "menu_always",
                "listen=",
                "import=",
                "extra=",
            ],
        )
    except getopt.GetoptError:
        usage()
        return None

    ret = {"args": args}

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            return None
        elif opt == "--migrate":
            ret["sync"] = True
        elif opt == "--loaddb":
            ret["loaddb"] = True
        elif opt == "--server_only":
            ret["server_only"] = True
        elif opt in ("-u", "--username"):
            ret["username"] = arg
        elif opt in ("-p", "--password"):
            ret["password"] = arg
        elif opt in ("--listen",):
            ret["listen"] = arg
        elif opt in ("--extra",):
            ret["extra"] = arg
        elif opt in ("--import",):
            ret["import"] = arg
        elif opt in ("-b", "--embededbrowser"):
            ret["embeded_browser"] = True
        elif opt in ("-s", "--embededserver"):
            ret["address"] = "embeded"
            ret["extern_prj"] = True
        elif opt in ("--embededtaskqueue",):
            ret["embeded_taskqueue"] = True
        elif opt == "--no_gui":
            ret["nogui"] = True
        elif opt in ("--menu_always",):
            ret["menu_always"] = True
        elif opt in ("--rpc"):
            ret["rpc"] = int(arg)
        elif opt in ("-p", "--param"):
            ret["param"] = arg
        elif opt in ("--channels"):
            ret["channels"] = True
        elif opt in ("--websocket_id",):
            ret["websocket"] = arg
        elif opt in ("--no_splash"):
            ret["no_splash"] = True
        elif opt in ("-d", "--debug"):
            global _DEBUG
            _DEBUG = True
        elif opt in ("--inspection",):
            global _INSPECTION
            _INSPECTION = True
        elif opt in ("--trace",):
            global _TRACE
            _TRACE = True
        elif opt in ("--video",):
            global _VIDEO, _APP_SIZE, _VIDEO_NAME
            _APP_SIZE = (1280, 720)
            _VIDEO = True
            _VIDEO_NAME = arg
            if not _VIDEO_NAME:
                _VIDEO_NAME = "video.avi"
    return ret


_PARAM = process_argv(sys.argv[1:])
if _PARAM is None:
    sys.exit(0)

import asyncio
from asyncio import get_event_loop, set_event_loop_policy

if sys.platform == "win32":
    set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from pytigon_lib.schtools.main_paths import get_main_paths

if "PRJ_NAME" in os.environ:
    PRJ_NAME = os.environ["PRJ_NAME"]
    PATHS = get_main_paths(os.environ["PRJ_NAME"])
else:
    PRJ_NAME = None
    PATHS = get_main_paths()

sys.path.append(PATHS["PRJ_PATH"])

from pytigon_lib.schtools.install_init import init

DATA_PATH = PATHS["DATA_PATH"]
PYTIGON_PATH = PATHS["PYTIGON_PATH"]

init(
    "_schall",
    PATHS["ROOT_PATH"],
    PATHS["DATA_PATH"],
    PATHS["PRJ_PATH"],
    PATHS["STATIC_PATH"],
    [PATHS["MEDIA_PATH"], PATHS["UPLOAD_PATH"]] if PRJ_NAME else None,
)

import wx

_ = wx.GetTranslation


def process_adv_argv():
    global _PARAM
    if not ("args" in _PARAM and len(_PARAM["args"]) > 0):
        _app = wx.App()

        choices = [
            ff
            for ff in os.listdir(PATHS["PRJ_PATH"])
            if not ff.startswith("_")
            and (Path(PATHS["PRJ_PATH"]) / ff).is_dir()
            and (Path(PATHS["PRJ_PATH"]) / ff / "settings_app.py").exists()
        ]
        dlg = wx.SingleChoiceDialog(
            None,
            _("select the application to run"),
            _("Pytigon"),
            choices,
            wx.CHOICEDLG_STYLE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            arg = dlg.GetStringSelection()
            dlg.Destroy()

        else:
            dlg.Destroy()
            sys.exit(0)

        _app.MainLoop()
        _app = None

    else:
        arg = _PARAM["args"][0].strip()
    if not (arg == "embeded" or "." in arg or "/" in arg):
        CWD_PATH = Path(PATHS["PRJ_PATH"]) / arg
        if not (Path(CWD_PATH) / "settings_app.py").exists():
            logger.error(_("Application pack: '%s' does not exists"), arg)
            sys.exit(0)
        else:
            sys.path.insert(0, str(CWD_PATH))

            import settings_app

            if hasattr(settings_app, "GUI_COMMAND_LINE"):
                x = settings_app.GUI_COMMAND_LINE.split(" ")
                param = process_argv(x)
                for key, value in param.items():
                    if key not in _PARAM:
                        _PARAM[key] = value


process_adv_argv()

if "channels" in _PARAM or "rpc" in _PARAM or "websocket" in _PARAM:
    try:
        from wxasync import AsyncBind, WxAsyncApp, StartCoroutine
    except ImportError:
        asyncio.futures.CancelledError = asyncio.CancelledError
        from wxasync import AsyncBind, WxAsyncApp, StartCoroutine

    class SchAsyncApp(WxAsyncApp):
        async def MainLoop(self):
            evtloop = wx.GUIEventLoop()
            with wx.EventLoopActivator(evtloop):
                while not self.exiting:
                    if platform.system() == "Darwin":
                        evtloop.DispatchTimeout(0)
                    else:
                        while self.HasPendingEvents():
                            self.ProcessPendingEvents()
                        while evtloop.Pending():
                            evtloop.Dispatch()
                    await asyncio.sleep(0.005)
                    evtloop.ProcessIdle()


from pytigon_gui.guilib import image
from pytigon_gui.guilib import pytigon_install
from pytigon_gui.guilib.logindialog import LoginDialog
from pytigon_gui.guiframe import appframe
from pytigon_gui.guilib.threadwindow import SchThreadManager
from pytigon_lib.schfs.vfstools import extractall
from pytigon_lib.schparser.html_parsers import SimpleTabParser
from pytigon_gui.guilib.tools import standard_tab_colour, colour_to_html
from pytigon_lib.schhttptools import httpclient
from pytigon_gui.guilib.httperror import http_error
from pytigon_lib.schhttptools.httpclient import HttpResponse
from pytigon_gui.guiframe import browserframe
from pytigon_lib.schtools import createparm
from pytigon_lib.schparser.html_parsers import ShtmlParser
from pytigon_lib.schtools.schjson import json_dumps, json_loads
import pytigon_gui.guictrl.tag

if "rpc" in _PARAM or "websocket" in _PARAM:
    import twisted.internet.asyncioreactor

    twisted.internet.asyncioreactor.install()

    from twisted.internet import reactor
    import twisted

    if "rpc" in _PARAM:
        from twisted.web import xmlrpc, server

        _RPC = True
    if "websocket" in _PARAM:
        # from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS
        from pytigon_lib.schhttptools.websocket import create_websocket_client

        _WEBSOCKET = _PARAM["websocket"]

if "channels" not in _PARAM:
    os.environ["PYTIGON_WITHOUT_CHANNELS"] = "1"

wx.RegisterId(10000)
wx.outputWindowClass = None

if _INSPECTION:
    os.environ["GTK_THEME"] = "Adwaita"

    import wx.lib.mixins.inspection

    if "channels" in _PARAM or "rpc" in _PARAM or "websocket" in _PARAM:

        class InspectableApp(SchAsyncApp, wx.lib.mixins.inspection.InspectionMixin):
            def OnInit(self):
                self.InitInspection()
                return True

        App = InspectableApp
    else:
        App = wx.lib.mixins.inspection.InspectableApp

    if _TRACE:

        def trace_calls(frame, event, arg):
            if event != "call":
                return
            co = frame.f_code
            func_name = co.co_name
            if func_name == "write":
                # Ignore write() calls from print statements
                return
            for pos in ("process_window_event", "idle", "timer", "update_ui"):
                if pos in func_name:
                    return
            func_line_no = frame.f_lineno
            func_filename = co.co_filename
            if not "wx/core" in func_filename:
                return
            caller = frame.f_back
            caller_line_no = caller.f_lineno
            caller_filename = caller.f_code.co_filename
            logger.debug(
                "Call to %s on line %s of %s from line %s of %s",
                func_name,
                func_line_no,
                func_filename,
                caller_line_no,
                caller_filename,
            )
            return

        sys.settrace(trace_calls)

else:
    if "channels" in _PARAM or "rpc" in _PARAM or "websocket" in _PARAM:
        App = SchAsyncApp
    else:
        App = wx.App

if _RPC:
    _BASE_APP = xmlrpc.XMLRPC
else:

    class _base:
        pass

    _BASE_APP = _base


class SchApp(App, _BASE_APP):
    """It is a subclass of wxPython wx.App. Depending on the command line parameters it is also subclass of
    xmlrpc.XMLRPC and wx.lib.mixins.inspection.InspectableApp.
    """

    def __init__(self):
        """Construct an application."""
        global _PARAM
        App.__init__(self)
        if _RPC:
            xmlrpc.XMLRPC.__init__(self)

        if (
            not "no_splash" in _PARAM
            and not "nogui" in _PARAM
            and not "server_only" in _PARAM
        ):
            img = wx.svg.SVGimage.CreateFromFile(str(SRC_PATH / "pytigon.svg"))
            bitmap = img.ConvertToBitmap(
                scale=2, width=int(img.width * 2), height=int(img.height * 2)
            )
            splash = wx.adv.SplashScreen(
                bitmap,
                wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
                1000,
                None,
                -1,
                wx.DefaultPosition,
                wx.DefaultSize,
                wx.BORDER_SIMPLE | wx.STAY_ON_TOP,
            )
            splash.Update()
            wx.Yield()

        config_name = SRC_PATH / "pytigon.ini"
        self.config = configparser.ConfigParser()
        self.config.read(config_name)

        self.app_size = _APP_SIZE

        self.locale = None
        self.ext_app = []
        self.ext_app_http = {}
        self.lock = None

        self.base_address = None

        self.src_path = SRC_PATH
        self.root_path = ROOT_PATH
        self.cwd_path = CWD_PATH
        self.data_path = DATA_PATH
        self.pytigon_path = PYTIGON_PATH

        self.http = None
        self.images = None
        self.mp = None

        self.server = None
        self.cwd = None
        self.inst_dir = None
        self.start_pages = []

        self.csrf_token = None
        self.title = None
        self.plugins = None
        self.extern_data = {}

        self.thread_manager = None
        self.task_manager = None

        self.menu_always = False
        self.authorized = False
        self.rpc = None

        self.websockets = {}
        self.websockets_callbacks = {}

        self.gui_style = (
            "app.gui_style = tree(toolbar(file(exit,open),clipboard, statusbar))"
        )

        self.COLOUR_HIGHLIGHT = colour_to_html(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        )
        self.COLOUR_BACKGROUND = colour_to_html(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)
        )
        self.COLOUR_SHADOW = colour_to_html(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DSHADOW)
        )
        self.COLOUR_DKSHADOW = colour_to_html(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DDKSHADOW)
        )
        self.COLOUR_ACTIVECATPION = colour_to_html(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVECAPTION)
        )
        self.COLOUR_INFOBK = colour_to_html(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK)
        )

        self.ctrl_process = {}

        class callback:
            def on_websocket_message(msg):
                # pass
                logger.debug("CALLBACK: %s", msg)

        self.add_websoket_callback("/schbuilder/clock/channel/", callback)

    def register_ctrl_process_fun(self, tag, fun):
        """Register function, which is called when widget connected to the specified tag is created.

        Args:
            tag: it must be the name of class in pytigon_gui/guictrl/schctrl typed in lowercase, preceded by "ctrl".
            For example: ctrlgrid, ctrltable, ctrllistbox are valid tag names.

            fun: a callback function with is called with one parameter - widget defined in pytigon_gui/guictrl/schctrl instance.

        Returns:
            None

        Example:
            see: appdata/plugins/standard/keymap/__init__.py
        """

        if tag in self.ctrl_process:
            self.ctrl_process[tag].append(fun)
        else:
            self.ctrl_process[tag] = [fun]

    # some XML-RPC function calls for twisted server
    def xmlrpc_stop(self):
        """Closes the wx application."""
        top_window = self.GetTopWindow()
        if top_window:
            top_window.Close()
        return "Shutdown initiated"

    def xmlrpc_title(self, title):
        """Set the main window title.

        Args:
            title: new title of application top window

        Returns:
            The title that was set, or None if no top window exists.
        """
        top_window = self.GetTopWindow()
        if top_window:
            top_window.SetTitle(title)
        return title

    def get_locale_object(self):
        """Get locale object

        Returns:
            application wx.Locale object
        """
        return self.locale

    def _init2(self, address, app):
        self.base_address = address
        self.base_app = app
        if self.base_app:
            self.base_path = urljoin(self.base_address, self.base_app)
        else:
            self.base_path = self.base_address
        if app and app != "":
            href = "/" + app + "/"
        else:
            href = "/"

        self.http = httpclient.AppHttp(address + "/", self)
        response = self.http.get(self, href)
        if response is None:
            return 0
        if response.ret_code != 200:
            if not login(href, auth_type="basic"):
                return 0
            else:
                self.authorized = True
            response = self.http.get(self, href)

        if response is None or response.ret_code != 200:
            return response if response else 0

        if app and app != "":
            self.images = image.SchImage("/" + app + "/site_media/app.png")
            response = self.http.get(self, "/" + app + "/")
        else:
            self.images = image.SchImage("/site_media/app.png")
            response = self.http.get(self, "/")

        ret_str = response.str()

        self.mp = SimpleTabParser()
        self.mp.feed(ret_str)
        self.mp.close()

        return response.ret_code

    def _re_init(self, address, app):
        """Re-initialize the application connection after login.

        Args:
            address: base URL address of the server.
            app: application name.
        """
        self.base_address = address
        self.base_app = app
        if self.base_app:
            self.base_path = urljoin(self.base_address, self.base_app)
        else:
            self.base_path = self.base_address

        if app and app != "":
            response = self.http.get(self, "/" + app + "/")
        else:
            response = self.http.get(self, "/")
        if response is None:
            return
        ret = response.str()
        self.mp = SimpleTabParser()
        self.mp.feed(ret)
        self.mp.close()

    async def test_websockets(self):
        logger.debug("-" * 65)
        logger.debug("%s", self.websockets)
        await self.websocket_send("/schtasks/show_task_events/channel/", {"id": "test"})
        logger.debug("=" * 65)

        count = 999
        while True:
            await asyncio.sleep(1)
            await self.websocket_send(
                "/schbuilder/clock/channel/", {"title": f"Hello world {count}"}
            )
            count -= 1

    async def init_websockets(self):
        from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer

        obj = self
        old_init = WebsocketConsumer.__init__
        old_init_async = AsyncWebsocketConsumer.__init__

        def accept(self):
            pass

        async def accept_async(self):
            pass

        def init(self, *args, **kwargs):
            old_init(self, *args, **kwargs)
            self.connect()

        def init_async(self, *args, **kwargs):
            nonlocal obj
            old_init_async(self, *args, **kwargs)
            if hasattr(self, "Bind"):
                obj.StartCoroutine(self.connect, self)
            else:

                def _bind(x, y, z):
                    pass

                self.Bind = _bind

        WebsocketConsumer.__init__ = init
        AsyncWebsocketConsumer.__init__ = init_async
        WebsocketConsumer.accept = accept
        AsyncWebsocketConsumer.accept = accept_async

        tasks = []
        if self.websockets:
            for key, value in self.websockets.items():
                if value.status == 1:
                    value.status = 2
                    tasks.append(
                        asyncio.create_task(
                            httpclient.local_websocket(
                                self.base_address.replace("http://", "ws://") + key,
                                value.input_queue,
                                value,
                            )
                        )
                    )
            if tasks:
                done, pending = await asyncio.wait(tasks)
                assert not pending
                (future,) = done  # unpack a set of length one
                logger.debug("Websocket init result: %s", future.result())

    def create_websocket(self, websocket_id, callback):
        local = True if self.base_address.startswith("http://127.0.0.2") else False
        create_websocket_client(self, websocket_id, local, callback)
        if local:
            tasks = []
            if self.websockets:
                for key, value in self.websockets.items():
                    if value.status == 1:
                        value.status = 2
                        tasks.append(
                            httpclient.local_websocket(
                                self.base_address.replace("http://", "ws://") + key,
                                value.input_queue,
                                value,
                            )
                        )
                if tasks:

                    async def reinit_websockets():
                        nonlocal tasks
                        done, pending = await asyncio.wait(tasks)
                        # done, pending = yield from asyncio.wait([raise_exception()], timeout=1)
                        assert not pending
                        (future,) = done  # unpack a set of length one
                        logger.debug("Websocket reinit result: %s", future.result())

                    self.StartCoroutine(reinit_websockets, self.GetTopWindow())

    def make_href(self, href):
        if self.base_app and href.startswith("/"):
            return "/" + self.base_app + href
        else:
            return href

    def SetTopWindow(self, frame):
        wx.App.SetTopWindow(self, frame)
        icon = wx.Icon(str(SRC_PATH / "pytigon.ico"), wx.BITMAP_TYPE_ICO)
        frame.SetIcon(icon)

        if hasattr(frame, "statusbar") and frame.statusbar:
            self.thread_manager = SchThreadManager(self, frame.statusbar)
        if _INSPECTION:
            self.ShowInspectionTool()

        if hasattr(self, "StartCoroutine"):
            if self.base_address and self.base_address.startswith("http://127.0.0.2"):
                wx.CallAfter(self.StartCoroutine, self.init_websockets, frame)

    def register_extern_app(self, address, app):
        self.ext_app.append((app, address))

    def get_http_for_adr(self, address):
        for app in self.ext_app:
            if address.upper().startswith(app[1]):
                if app[0] in self.ext_app_http:
                    return self.ext_app_http[app[0]]
                else:
                    http = httpclient.AppHttp(app[1], app[0])
                    self.ext_app_http[app[0]] = http
                    return http
        return self.http

    def get_http(self, win):
        """Get :class:`~pytigon_lib.schhttptools.httpclient.HttpClient` object

        With returned object you can directly make requests to http server.

        Args:
            win - wx.Window derived object

        Returns:
            :class:`~pytigon_lib.schhttptools.httpclient.HttpClient` object
        """
        winparent = win
        while winparent:
            if hasattr(winparent, "get_app_http"):
                return winparent.get_app_http()
            winparent = winparent.GetParent()
        return self.http

    def read_html(self, win, address_or_parser, parameters):
        """Prepare request to http server and read result

        Args:
            win: wx.Window derived object
            address_or_parser: can be: address of read_htmlhttp page (str type) or
            :class:'~pytigon_lib.schparser.html_parsers.ShtmlParser'
            parameters: dict

        Returns :class:'~pytigon_lib.schparser.html_parsers.ShtmlParser' object
        """
        if isinstance(address_or_parser, str):
            http = self.get_http(win)

            if parameters and isinstance(parameters, dict):
                adr = address_or_parser
                response = http.post(self, adr, parm=parameters)
            else:
                if parameters:
                    adrtmp = createparm.create_parm(address_or_parser, parameters)
                    if adrtmp:
                        adr = adrtmp[0] + adrtmp[1] + adrtmp[2]
                    else:
                        adr = address_or_parser
                else:
                    adr = address_or_parser
                response = http.get(win, adr)
            if response is None or response.ret_code == 404:
                raise ValueError(f"HTTP request failed with 404 for address: {adr}")
            ptr = response.str()
            mp = ShtmlParser()
            mp.process(ptr, address_or_parser)
            mp.address = adr
        elif isinstance(address_or_parser, HttpResponse):
            adr = address_or_parser.url
            ptr = address_or_parser.str()
            mp = ShtmlParser()
            mp.process(ptr, adr)
            mp.address = adr
        else:
            adr = None
            mp = address_or_parser if address_or_parser else ShtmlParser()
            if not address_or_parser:
                mp.process("<html><body></body></html>")
                mp.address = None
        return (mp, adr)

    def get_tab(self, nr):
        """Return setup tab

        When pytigon client connect to server it receive html page with few configuration tables.
        This function return rendered table.

        Args:
            nr: table number

        Returns:
            table - :class:'~pytigon_lib.schparser.html_parsers.SimpleTabParser' object

        """
        if self.mp:
            return self.mp.tables[nr]
        else:
            return None

    def get_working_dir(self):
        """Return pytigon working directory - ~/pytigon_data/."""
        return Path.home() / "pytigon_data/"

    def _get_parm_for_server(self):
        """Build a parameter string containing colour settings for the server.

        Returns:
            A comma-separated string of colour name:value pairs without '#' prefixes.
        """
        return ",".join(f"{pos[0]}:{pos[1]}" for pos in standard_tab_colour()).replace(
            "#", ""
        )

    def _is_safe_zip_member(self, member_name, target_path):
        resolved = os.path.realpath(os.path.join(target_path, member_name))
        target_real = os.path.realpath(target_path)
        return os.path.commonpath([resolved, target_real]) == target_real

    def _install_plugins(self):
        """Install plugins from the server if they are not already cached locally.

        Downloads plugin zip files from the server and extracts them into the
        local plugin cache directory. Path traversal is prevented.
        """
        home_dir = self.get_working_dir()
        p = self.plugins
        if not p:
            return
        sys.path.append(home_dir)
        for plugin in p:
            if not plugin or "/" not in plugin:
                continue
            if plugin.startswith("standard/"):
                continue
            try:
                logger.info("Installing plugin: %s", plugin)
                app_name = plugin.split("/")[0]
                plugin_name = plugin.split("/")[1]
                plugins_cache = "" if plugin_name == "install" else "plugins_cache/"
                plugin_dir = Path(home_dir) / plugins_cache / str(app_name)
                if not Path(plugin_dir).exists():
                    os.makedirs(str(plugin_dir), exist_ok=True)
                    init_path = Path(plugin_dir) / "__init__.py"
                    with open(str(init_path), "w") as ini:
                        ini.write(" ")
                zip_path = Path(home_dir) / plugins_cache / (str(plugin) + ".zip")
                if not Path(zip_path).exists():
                    http = wx.GetApp().http
                    response = http.get(self, "/schsys/plugins/" + str(plugin) + "/")
                    if response and response.ret_code == 200:
                        z_data = response.ptr()
                        if z_data:
                            with open(str(zip_path), "wb") as x:
                                x.write(z_data)
                            try:
                                zip_handle = zipfile.ZipFile(str(zip_path))
                                for member in zip_handle.infolist():
                                    if member.filename.endswith(("/", "\\")):
                                        os.makedirs(
                                            os.path.join(str(plugin_dir), member.filename),
                                            exist_ok=True,
                                        )
                                    elif self._is_safe_zip_member(
                                        member.filename, str(plugin_dir)
                                    ):
                                        zip_handle.extract(member, str(plugin_dir))
                                    else:
                                        logger.warning(
                                            "Skipping unsafe plugin zip entry: %s",
                                            member.filename,
                                        )
                                zip_handle.close()
                            except (zipfile.BadZipFile, OSError) as e:
                                logger.error(
                                    "Error extracting plugin %s: %s", plugin, e
                                )
            except Exception as e:
                logger.error("Error installing plugin %s: %s", plugin, e)

    def on_exit(self):
        """Clean up resources when the application exits.

        Terminates the task manager if it is running.
        """
        if self.task_manager:
            with contextlib.suppress(Exception):
                self.task_manager.terminate()

    def run_script(self, app_name, script_path):
        """Run a script file and send its content to the server.

        Args:
            app_name: name of the application.
            script_path: path to the script file to execute.
        """
        try:
            with open(script_path, "rb") as s:
                top_window = self.GetTopWindow()
                if top_window and hasattr(top_window, "new_main_page"):
                    wx.CallAfter(
                        top_window.new_main_page,
                        "/" + app_name + "/run_script/",
                        "Run script",
                        {"script": s.read()},
                    )
        except OSError as e:
            logger.error("Error reading script %s: %s", script_path, e)

    def add_websoket_callback(self, websocket_id, callback):
        """Register a callback for websocket events on a given websocket ID.

        Args:
            websocket_id: the websocket endpoint identifier.
            callback: object with websocket event handler methods.
        """
        if websocket_id in self.websockets_callbacks:
            self.websockets_callbacks[websocket_id].append(callback)
        else:
            self.websockets_callbacks[websocket_id] = [callback]

    def remove_websocket_callback(self, websocket_id, callback):
        """Unregister a previously registered websocket callback.

        Args:
            websocket_id: the websocket endpoint identifier.
            callback: the callback object to remove.
        """
        if websocket_id in self.websockets_callbacks:
            if callback in self.websockets_callbacks[websocket_id]:
                self.websockets_callbacks[websocket_id].remove(callback)

    async def websocket_send(self, websocket_id, msg):
        """Send a message through a websocket connection.

        Args:
            websocket_id: the websocket endpoint identifier.
            msg: message to send (will be JSON-serialized by the transport).
        """
        if websocket_id in self.websockets:
            obj = self.websockets[websocket_id].send_message(msg)
            if obj:
                await obj

    def on_websocket_callback(self, client, event_name, argv):
        """Dispatch a websocket event to all registered callbacks.

        Args:
            client: the websocket client instance.
            event_name: name of the event (e.g. 'on_websocket_message').
            argv: event arguments dictionary.
        """
        if client.websocket_id in self.websockets_callbacks:
            for callback in self.websockets_callbacks[client.websocket_id]:
                if hasattr(callback, event_name):
                    if "channel" in argv:
                        if hasattr(callback, "accept_channel"):
                            if not getattr(callback, "accept_channel")(argv["channel"]):
                                continue
                    try:
                        getattr(callback, event_name)(**argv)
                    except Exception as e:
                        logger.error(
                            "Websocket callback error for %s: %s", event_name, e
                        )

    def on_websocket_connect(self, client, websocket_id, response):
        """Handle websocket connect event."""
        return self.on_websocket_callback(
            client, "on_websocket_connect", {"response": response}
        )

    def on_websocket_open(self, client, websocket_id):
        """Handle websocket open event."""
        return self.on_websocket_callback(client, "on_websocket_open", {})

    def on_websocket_message(self, client, websocket_id, msg):
        """Handle websocket message event."""
        return self.on_websocket_callback(client, "on_websocket_message", msg)


def login(base_href, auth_type=None, username=None):
    """Show the login dialog and attempt authentication against the server.

    Args:
        base_href: base URL for authentication requests.
        auth_type: authentication type ('basic' for HTTP basic auth, None for form-based).
        username: pre-filled username (optional).

    Returns:
        True if login succeeded, False otherwise.
    """
    dlg = LoginDialog(None, 101, _("Pytigon - login"), username=username)

    while dlg.ShowModal() == wx.ID_OK:
        try:
            username = dlg.text1.GetValue()
            password = dlg.text2.GetValue()

            parm = {
                "username": username,
                "password": password,
                "next": "/schsys/ok/",
                "client_param": wx.GetApp()._get_parm_for_server(),
            }
            if auth_type is None:
                ret = wx.GetApp().http.post(
                    wx.GetApp(),
                    "/schsys/do_login/?from_pytigon=1",
                    parm,
                    credentials=(username, password),
                )

                if ret is None:
                    dlg.message.SetLabel(_("Connection error!"))
                    continue

                ret_str = ret.str()

                if "$$RETURN_OK" in ret_str:
                    dlg.Destroy()
                    return True
                else:
                    if "id_password" not in ret_str:
                        dlg.Destroy()
                        return False
                    else:
                        dlg.message.SetLabel(_("Failed login attempt!"))
            else:
                result = wx.GetApp().http.get(
                    wx.GetApp(), base_href, credentials=(username, password)
                )
                if result is not None and result.ret_code == 200:
                    dlg.Destroy()
                    return True
                else:
                    ret_code = result.ret_code if result else "N/A"
                    dlg.message.SetLabel(
                        _(f"Failed login attempt! http error: {ret_code}")
                    )
        except Exception as e:
            dlg.message.SetLabel(_(f"Login error: {str(e)}"))
    dlg.Destroy()
    return False


def _setup_app_params():
    global CWD_PATH, _PARAM, app

    args = _PARAM["args"]
    apps = []
    address = "http://127.0.0.2"
    app_title = _("Pytigon")
    app_name = ""

    app = SchApp()
    if "menu_always" in _PARAM:
        app.menu_always = True
    if "rpc" in _PARAM:
        app.rpc = int(_PARAM["rpc"])
    if "param" in _PARAM:
        app.param = _PARAM["param"]
    if "embeded_browser" in _PARAM:
        app.embeded_browser = True
    else:
        app.embeded_browser = False
    if "extern_prj" in _PARAM:
        extern_prj = True
    else:
        extern_prj = False
    if "address" in _PARAM:
        address = _PARAM["address"]

    return args, apps, address, app_title, app_name, extern_prj


def _process_args(args, address, app_name, extern_prj):
    global CWD_PATH

    if len(args) > 0:
        if ".ptig" in args[0].lower():
            prg_name = args[0].replace("\\", "/").split("/")[-1]
            x = prg_name.split(".")
            if len(x) == 2 or (len(x) > 2 and x[-2].lower() == "inst"):
                prg_name2 = x[0]
                path = Path(PATHS["PRJ_PATH_ALT"]) / "_schremote"
                sys.path.append(str(path))
                if not pytigon_install.install(args[0]):
                    return None, None, None
                CWD_PATH = Path(PATHS["PRJ_PATH"]) / prg_name2
                return None, None, None
            else:
                if len(x) > 3:
                    prg_name2 = x[0]
                    app_name2 = x[-2]
                    prj = x[-3]
                    CWD_PATH = Path(PATHS["PRJ_PATH"]) / prj.strip()
                    if not (Path(CWD_PATH) / "settings_app.py").exists():
                        logger.error(
                            _("Application pack: '%s' does not exists"), prj.strip()
                        )
                        return None, None, None
                    wx.CallAfter(app.run_script, app_name2, args[0])
                else:
                    logger.error(_("Name of script: '%s' is not valid"), prg_name)
                    return None, None, None
        else:
            arg = args[0].strip()
            if arg == "embeded" or "." in arg or "/" in arg:
                if arg != "embeded":
                    CWD_PATH = Path(PATHS["PRJ_PATH_ALT"]) / "_schremote"

                tmp = arg.replace("//", "$$$")
                if "/" in arg:
                    x = tmp.split("/", 1)
                    address = x[0].replace("$$$", "//")
                    if len(x) > 1:
                        app_name = x[1]
                        if app_name.endswith("/"):
                            app_name = app_name[:-1]
                else:
                    address = arg

                extern_prj = True
            else:
                CWD_PATH = Path(PATHS["PRJ_PATH"]) / arg
                if not (Path(CWD_PATH) / "settings_app.py").exists():
                    logger.error(_("Application pack: '%s' does not exists"), arg)
                    return None, None, None

    return address, app_name, extern_prj


def _setup_django(apps):
    sys.path.insert(0, str(CWD_PATH))
    httpclient.init_embeded_django()

    if not ("channels" in _PARAM or "rpc" in _PARAM):
        wx.Yield()
    import settings_app

    os.environ["DJANGO_SETTINGS_MODULE"] = "settings_app"
    from django.conf import settings

    if wx.Font.CanUsePrivateFont():
        fonts_path = Path(settings.STATIC_ROOT) / "fonts"
        font_names = [
            "DejaVuSansCondensed.ttf",
            "DejaVuSansCondensed-Bold.ttf",
            "DejaVuSansCondensed-Oblique.ttf",
            "DejaVuSansCondensed-BoldOblique.ttf",
            "DejaVuSerifCondensed.ttf",
            "DejaVuSerifCondensed-Bold.ttf",
            "DejaVuSerifCondensed-Italic.ttf",
            "DejaVuSerifCondensed-BoldItalic.ttf",
            "DejaVuSansMono.ttf",
            "DejaVuSansMono-Bold.ttf",
            "DejaVuSansMono-Oblique.ttf",
            "DejaVuSansMono-BoldOblique.ttf",
        ]
        for font_name in font_names:
            wx.Font.AddPrivateFont(str(Path(fonts_path) / font_name))

    if "sync" in _PARAM:
        from django.core.management.commands.migrate import Command as migrate_command

        migrate = migrate_command()
        with contextlib.suppress(SystemExit):
            migrate.run_from_argv(["manage.py", "migrate"])
    if "loaddb" in _PARAM:
        from django.core.management.commands.loaddata import Command as load_command

        load = load_command()
        with contextlib.suppress(SystemExit):
            load.run_from_argv(["manage.py", "loaddata"])

    cwd = str(CWD_PATH)
    inst_dir = str(SRC_PATH)
    if inst_dir == "":
        inst_dir = cwd

    settings.TEMPLATES[0]["DIRS"].insert(0, inst_dir + "/appdata/plugins")
    settings.TEMPLATES[0]["DIRS"].insert(0, cwd + "/appdata/plugins")
    settings.TEMPLATES[0]["DIRS"].insert(0, inst_dir + "/../templates")
    settings.TEMPLATES[0]["DIRS"].insert(0, cwd + "/templates")

    for a in apps:
        settings.INSTALLED_APPS.append(a)

    return settings, cwd, inst_dir


def _setup_server(address):
    port = 0
    if "server_only" in _PARAM:
        port = 8000
        if ":" in address:
            l = address.split(":")
            if len(l) == 3:
                port = int(l[2])
        address = "embeded"
    if address == "embeded":
        import socket
        from pytigon_lib.schdjangoext.server import run_server

        if "server_only" in _PARAM:
            address = "127.0.0.1"
            if "listen" in _PARAM:
                if ":" in _PARAM["listen"]:
                    address, port = _PARAM["listen"].split(":")
                    port = int(port)
                else:
                    address = _PARAM["listen"]
                    port = 8000
        else:
            address = "127.0.0.3"
        if port == 0:
            port = 8000
        test = True
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while test:
            try:
                s.bind((address, port))
                s.close()
                s = None
                test = False
            except OSError:
                port += 1

        if "extra" in _PARAM:
            server = run_server(address, port, prod=False, params=_PARAM["extra"])
        else:
            server = run_server(address, port, prod=False)
        address = "http://" + address + ":" + str(port)
    else:
        server = None

    return address, server


def _start_task_queue():
    if "embeded_taskqueue" in _PARAM:
        from multiprocessing import Process
        from django_q.management.commands.qcluster import Command as qcluster_command

        qcluster = qcluster_command()
        app.task_manager = Process(
            target=qcluster.run_from_argv, args=(["manage.py", "qcluster"],)
        )
        app.task_manager.start()
        logger.info("Task manager started")


def _do_login_flow(app_name, address):
    tab = app.get_tab(0)

    autologin = True
    if "server_only" in _PARAM:
        app.gui_style = "app.gui_style = tray(file(exit,open))"
        app.authorized = True
        reinit = False
    else:
        reinit = True
        for row in tab:
            if row[0].data == "autologin":
                autologin = row[1].data == "1"
            elif row[0].data == "gui_style":
                app.gui_style = row[1].data
            elif row[0].data == "csrf_token":
                app.csrf_token = row[1].data
            elif "start_page" in row[0].data:
                app.start_pages.extend(
                    [x for x in row[1].data.split(";") if x and x != "None"]
                )
            elif row[0].data == "title":
                app.title = row[1].data
            elif row[0].data == "plugins":
                if row[1].data and row[1].data != "":
                    app.plugins = row[1].data.split(";")

    app._install_plugins()

    ready_to_run = True

    if not app.authorized and (
        (autologin and "username" not in _PARAM)
        or ("username" in _PARAM and "password" in _PARAM)
    ):
        if "username" in _PARAM:
            username2 = _PARAM["username"]
            password2 = _PARAM["password"]
        else:
            env = get_environ(ROOT_PATH)
            username2 = env("USERNAME")
            password2 = env("PASSWORD")

        ready_to_run = False
        response = app.http.post(
            app,
            "/" + app_name + "/schsys/do_login/?from_pytigon=1"
            if app_name
            else "/schsys/do_login/?from_pytigon",
            {
                "username": username2,
                "password": password2,
                "next": address + "/" + app_name + "/schsys/ok/"
                if app_name
                else address + "/schsys/ok/",
                "client_param": app._get_parm_for_server(),
            },
        )
        ret_str = response.str()
        if "$$RETURN_OK" in ret_str:
            app.authorized = True
            ready_to_run = True
        else:
            logger.error("Login error: %s", ret_str)
    if not app.authorized and "username" in _PARAM:
        ready_to_run = False
        href = "/" + app_name + "/" if app_name else "/"
        if login(href, auth_type=None, username=_PARAM["username"]):
            app.authorized = True
            ready_to_run = True
    if reinit:
        app._re_init(address, app_name)
    return ready_to_run


def _main_init():
    """Initialize the Pytigon application: parse args, set up Django, connect to server.

    Returns:
        Tuple of (ready_to_run: bool, nogui: bool), or (None, None) on failure.
    """
    global CWD_PATH, _PARAM, app

    args, apps, address, app_title, app_name, extern_prj = _setup_app_params()

    os.environ["DJANGO_SETTINGS_MODULE"] = "settings_app"
    result = _process_args(args, address, app_name, extern_prj)
    if result[0] is None:
        return (None, None)
    address, app_name, extern_prj = result

    settings, cwd, inst_dir = _setup_django(apps)

    address, server = _setup_server(address)

    _start_task_queue()

    settings.BASE_URL = "http://" + address
    settings.URL_ROOT_FOLDER = ""
    if "server_only" not in _PARAM:
        init_ret = app._init2(address, app_name)
        if init_ret != 200:
            return (False, False)

    app.server = server
    app.cwd = cwd
    app.inst_dir = inst_dir

    app.title = app_title
    ready_to_run = _do_login_flow(app_name, address)

    return (ready_to_run, "nogui" in _PARAM)


def _main_run():
    """Create the main application frame and start the wx event loop."""
    app = wx.GetApp()
    app.locale = wx.Locale(wx.LANGUAGE_DEFAULT)
    app.locale.AddCatalogLookupPathPrefix(str(SRC_PATH / "pytigon_gui/locale"))

    app.locale.AddCatalog("wx")
    app.locale.AddCatalog("pytigon")

    if app.embeded_browser:
        frame = browserframe.SchBrowserFrame(
            None,
            app.gui_style,
            wx.ID_ANY,
            app.title,
            wx.DefaultPosition,
            wx.Size(_APP_SIZE[0], _APP_SIZE[1]),
        )
    else:
        frame = appframe.SchAppFrame(
            app.gui_style,
            app.title,
            wx.DefaultPosition,
            wx.Size(_APP_SIZE[0], _APP_SIZE[1]),
            video_name=_VIDEO_NAME,
        )

    frame.CenterOnScreen()

    wx.Log.SetActiveTarget(wx.LogStderr())

    destroy_fun_tab = frame.destroy_fun_tab
    httpclient.set_http_error_func(http_error)

    def idle_fun():
        wx.GetApp().web_ctrl.OnIdle(None)

    httpclient.set_http_idle_func(idle_fun)

    if _RPC:
        reactor.listenTCP(app.rpc, server.Site(app))

    if _WEBSOCKET and app.base_address:
        if ";" in _WEBSOCKET:
            websockets = _WEBSOCKET.split(";")
        else:
            websockets = [_WEBSOCKET]

        local = (
            True
            if app.base_address and app.base_address.startswith("http://127.0.0.2")
            else False
        )

        for websocket_id in websockets:
            create_websocket_client(app, websocket_id, local)

    if "import" in _PARAM:
        x = __import__(_PARAM["import"])

        def s():
            nonlocal frame, x
            x(frame)

        wx.CallAfter(s)

    if hasattr(wx, "pseudoimport"):
        x = getattr(wx, "pseudoimport")

        def s():
            nonlocal frame, x
            x(frame)

        wx.CallAfter(s)

    if "channels" in _PARAM or "rpc" in _PARAM or "websocket" in _PARAM:
        asyncio.run(app.MainLoop())
    else:
        app.MainLoop()

    if app.server:
        app.server.stop()
    del app
    for pos in destroy_fun_tab:
        pos()


def main():
    ready_to_run, nogui = _main_init()
    if ready_to_run:
        if nogui:
            while True:
                time.sleep(100)
        else:
            _main_run()
    os._exit(0)


if __name__ == "__main__":
    main()
