import pyautogui
import sys
import os
import traceback
import datetime
import wx

from pytigon.pytigon_run import run
from asyncio import sleep


class WxAuto:
    def __init__(self, script_name, pos, size):
        self.script_name = script_name
        self.pos = pos
        self.size = size
        self.subtitle_id = 1
        self.start_time = datetime.datetime.now()
        self.time_unit = 0.5
        self.sys_time_unit = 0.5

    def get_region(self):
        return (
            self.pos.x,
            self.pos.y,
            self.size.GetWidth(),
            self.size.GetHeight(),
        )

    async def auto_move_and_focus(self, window_name, set_focus=True):
        await sleep(self.sys_time_unit / 3)
        win = wx.Window.FindWindowByName(window_name)
        if win and set_focus:
            win.SetFocus()
            await sleep(self.sys_time_unit / 3)
        if not win:
            print("ERROR! ", window_name)
        pos = win.GetScreenPosition()
        size = win.GetSize()
        pyautogui.moveTo(
            pos[0] + int(size.GetWidth() / 2), pos[1] + int(size.GetHeight() / 2)
        )
        # pyautogui.click()
        await sleep(self.sys_time_unit / 3)
        return win

    async def auto_click(self, window_name):
        await self.auto_move_and_focus(window_name)
        pyautogui.click()

    async def auto_focus_on_img(self, image_name):
        await sleep(self.sys_time_unit / 2)
        location = pyautogui.locateOnScreen(image_name, region=self.get_region())
        x, y = pyautogui.center(location)
        pyautogui.moveTo(x, y)
        await sleep(self.sys_time_unit / 2)

    async def auto_click_on_img(self, image_name):
        await self.auto_focus_on_img(image_name)
        pyautogui.click()

    async def dropdown(self, delta):
        delta2 = int(delta)
        pyautogui.keyDown("alt")
        pyautogui.press("down")
        pyautogui.keyUp("alt")
        await sleep(1)
        if delta2 > 0:
            for i in range(0, delta2):
                pyautogui.press("down")
                await sleep(0.1)
        else:
            for i in range(0, -1 * delta2):
                pyautogui.press("up")
                await sleep(0.1)
        pyautogui.press("enter")
        await sleep(1)

    async def __lshift__(self, txt):
        if not txt:
            return
        delta = datetime.datetime.now() - self.start_time
        t1 = datetime.datetime(year=2000, month=1, day=1, hour=0, minute=0) + delta
        t2 = t1 + datetime.timedelta(seconds=3)
        s = "%d\n%02d:%02d:%02d,%d --> %02d:%02d:%02d,%d\n" % (
            self.subtitle_id,
            t1.hour,
            t1.minute,
            t1.second,
            t1.microsecond // 1000,
            t2.hour,
            t2.minute,
            t2.second,
            t2.microsecond // 1000,
        )
        with open(
            self.script_name + ".srt", "wt" if self.subtitle_id == 1 else "at"
        ) as f:
            f.write(s)
            f.write(txt)
            f.write("\n\n")
        self.subtitle_id += 1

    async def process(self, txt, change_tab=None):
        if txt.startswith("@"):
            with open(txt[1:], "rt") as f:
                txt2 = f.read()
        else:
            txt2 = txt
        if change_tab:
            if type(change_tab) == str:
                change_tab2 = change_tab.replace(";;", "\n").split("\n")
            else:
                change_tab2 = change_tab
            change_tab2.reverse()
            for item in change_tab2:
                if ":" in item:
                    x = item.split(":", 1)
                    txt2 = txt2.replace("$" + x[0], x[1])

        for line in txt2.split("\n"):
            l = line.strip()
            if l.startswith("."):
                await sleep(len(l) * self.time_unit)
            elif l.startswith("^"):
                x = l.split(":")
                if len(x) > 1:
                    await getattr(self, x[0][1:])(x[1])
                else:
                    await getattr(self, x[0][1:])()
            elif l.startswith("#"):
                pass
            elif l.startswith("<<"):
                x = l[2:].split(" ")
                for item in x:
                    item2 = item.strip()
                    if item2.startswith("^"):
                        pyautogui.keyUp(item2[1:])
                    elif item2.startswith("_"):
                        pyautogui.keyDown(item2[1:])
                    elif item2.startswith("-"):
                        await sleep((len(item2) - 1) * self.time_unit / 10)
                    else:
                        pyautogui.press(item2)
            else:
                if "<<" in l:
                    x = l.split("<<")
                    await (getattr(self, x[0].strip()) << x[1].strip())
                else:
                    await (self << l.strip())

    def __getattr__(self, item):
        if item.endswith("_png"):
            return ImgProxy(self, item.replace("__", "/").replace("_png", ".png"))
        else:
            return ControlProxy(self, item)


class ControlProxy:
    def __init__(self, wx_auto, control_name):
        self.wx_auto = wx_auto
        self.control_name = control_name

    async def __lshift__(self, txt):
        ctrl = await self.wx_auto.auto_move_and_focus(self.control_name)
        if txt == "click":
            pyautogui.click()
        else:
            if txt == "focus":
                pass
            else:
                ctrl.SetValue(txt)


class ImgProxy:
    def __init__(self, wx_auto, img_name):
        self.img = None
        self.wx_auto = wx_auto
        self.img_name = img_name

    async def __lshift__(self, txt):
        await self.wx_auto.auto_focus_on_img(self.img_name)
        pyautogui.click()


SCRIPT = sys.argv[-1]


def autoit(win):
    if win:
        pos = win.GetScreenPosition()
        size = win.GetSize()
    wx_auto = WxAuto(SCRIPT, pos, size)

    async def astart():
        try:
            await sleep(1)
            if os.path.exists(SCRIPT + ".txt"):
                await wx_auto.process("@" + SCRIPT + ".txt")
            else:
                scr = __import__(SCRIPT, globals(), locals(), [], 0)
                await scr.wxauto(wx_auto, pyautogui, wx)
        except:
            print(sys.exc_info()[0])
            print(traceback.print_exc())

    wx.GetApp().StartCoroutine(astart, win)


if __name__ == "__main__":
    setattr(wx, "pseudoimport", autoit)

    sys.argv = [
        __file__.replace("pytigon-gui", "pytigon").replace("wxauto.py", "ptig.py"),
        "--video=%s.avi" % SCRIPT,
        "--rpc=8090",
        "schdevtools",
        "--inspection",
    ]

    run()
