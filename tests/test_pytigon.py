"""Tests for pytigon_gui.pytigon.process_argv and related functions.

process_argv is tested in isolation via direct function extraction to avoid
module-level side effects from importing pytigon_gui.pytigon.
"""

import pytest
import sys
import getopt


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
        return None

    ret = {"args": args}

    for opt, arg in opts:
        if opt in ("-h", "--help"):
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
            pass
        elif opt in ("--inspection",):
            pass
        elif opt in ("--trace",):
            pass
        elif opt in ("--video",):
            pass
    return ret


class TestProcessArgv:
    """Tests for process_argv CLI argument parsing."""

    def test_help_returns_none(self):
        assert process_argv(["-h"]) is None

    def test_help_long_returns_none(self):
        assert process_argv(["--help"]) is None

    def test_no_args_returns_dict(self):
        result = process_argv([])
        assert isinstance(result, dict)
        assert result["args"] == []

    def test_embeded_browser_short(self):
        assert process_argv(["-b"])["embeded_browser"] is True

    def test_embeded_browser_long(self):
        assert process_argv(["--embededbrowser"])["embeded_browser"] is True

    def test_embeded_server(self):
        result = process_argv(["-s"])
        assert result["address"] == "embeded"
        assert result["extern_prj"] is True

    def test_server_only(self):
        assert process_argv(["--server_only"])["server_only"] is True

    def test_no_gui(self):
        assert process_argv(["--no_gui"])["nogui"] is True

    def test_rpc(self):
        assert process_argv(["--rpc", "8888"])["rpc"] == 8888

    def test_username_password(self):
        result = process_argv(["--username", "admin", "--password", "secret"])
        assert result["username"] == "admin"
        assert result["password"] == "secret"

    def test_password_long(self):
        result = process_argv(["--password", "secret"])
        assert result["password"] == "secret"

    def test_channels(self):
        assert process_argv(["--channels"])["channels"] is True

    def test_websocket_id(self):
        assert process_argv(["--websocket_id", "/test/channel/"])["websocket"] == "/test/channel/"

    def test_migrate(self):
        assert process_argv(["--migrate"])["sync"] is True

    def test_loaddb(self):
        assert process_argv(["--loaddb"])["loaddb"] is True

    def test_args_captured(self):
        assert process_argv(["schdevtools"])["args"] == ["schdevtools"]

    def test_param_long(self):
        assert process_argv(["--param", "key=value"])["param"] == "key=value"

    def test_listen(self):
        assert process_argv(["--listen", "127.0.0.1:8080"])["listen"] == "127.0.0.1:8080"

    def test_multiple_options(self):
        result = process_argv(
            ["--server_only", "--websocket_id", "/ws/", "-u", "testuser", "myproject"]
        )
        assert result["server_only"] is True
        assert result["websocket"] == "/ws/"
        assert result["username"] == "testuser"
        assert result["args"] == ["myproject"]

    def test_unknown_option_returns_none(self):
        assert process_argv(["--nonexistent"]) is None

    def test_embeded_taskqueue(self):
        assert process_argv(["--embededtaskqueue"])["embeded_taskqueue"] is True

    def test_menu_always(self):
        assert process_argv(["--menu_always"])["menu_always"] is True

    def test_no_splash(self):
        assert process_argv(["--no_splash"])["no_splash"] is True

    def test_import_flag(self):
        assert process_argv(["--import", "mymodule"])["import"] == "mymodule"

    def test_extra(self):
        assert process_argv(["--extra", "some_extra"])["extra"] == "some_extra"
