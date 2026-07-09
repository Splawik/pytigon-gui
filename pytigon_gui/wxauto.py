"""Pytigon GUI automation module using pyautogui and wxPython.

This module provides a lightweight scripting engine for automating wxPython
GUI interactions. It is primarily used for:
  - Automated UI testing (simulating user clicks, keyboard input, navigation).
  - Recording and replaying user sessions (generating SRT subtitle files
    synchronized with video recordings).
  - Scripting complex UI workflows from plain-text `.txt` files or Python modules.

Architecture
------------
The module uses a command-overloading pattern based on Python's ``<<`` operator
(left-shift / ``__lshift__``). Each line of an automation script is dispatched
to a handler:

  - **WxAuto** is the core controller. It owns the pyautogui interface,
    tracks timing for subtitle generation, and interprets script commands.
  - **ControlProxy** wraps a named wx.Window. Writing ``control << "value"``
    moves the mouse to the control, focuses it, and sets its value.
  - **ImgProxy** wraps an image file path. Writing ``img_png << ""``
    locates the image on screen and clicks at its center.

Script Syntax
-------------
Automation scripts are plain text files (or multi-line strings) where each
line is a command. The format is intentionally simple:

  ``.`` (dot)
      Sleep for ``len(line) * time_unit`` seconds. Multiple dots mean longer
      pauses. Example: ``....`` sleeps for 4 * 0.5 = 2 seconds.

  ``^method_name`` or ``^method_name:argument``
      Call a method on the WxAuto instance. The method name is taken from
      everything after ``^`` up to the optional ``:``. If a ``:`` is present,
      the text after it is passed as a single string argument.
      Example: ``^auto_click:my_button`` calls ``auto_click("my_button")``.

  ``<<key1 key2 ^key3 ...``
      Simulate raw keyboard input using pyautogui. Each token is processed:
        - ``^X`` → release key X (keyUp).
        - ``_X`` → press and hold key X (keyDown).
        - ``-`` followed by more dashes → sleep (each dash after the first
          adds ``time_unit / 10`` seconds).
        - Anything else → press and release the key.
      Example: ``<<enter`` presses Enter. ``<<_ctrl c ^ctrl`` does Ctrl+C.

  ``# comment``
      Ignored line (comment).

  ``@filename``
      Load commands from an external file. The file content can use Django
      template syntax if ``argv`` context is provided.

  ``control_name << value``
      Dispatch to a ControlProxy or ImgProxy. If ``control_name`` ends with
      ``_png``, an ImgProxy is used (image-based click). Otherwise a
      ControlProxy is used (window-name-based interaction).

  Any other text
      Treated as a subtitle entry and written to the SRT file via
      ``WxAuto.__lshift__``.

Integration
-----------
The module hooks into the Pytigon application lifecycle through
``wx.pseudoimport``. When ``wxauto.py`` is run directly, it sets
``wx.pseudoimport = autoit`` and launches the main Pytigon application
with ``--video`` and ``--rpc`` flags. The application frame calls
``wx.pseudoimport(frame)`` after initialization, which triggers
the automation coroutine.

Dependencies
------------
- **pyautogui**: cross-platform GUI automation (mouse, keyboard, screen).
- **wxPython**: window lookup via ``wx.Window.FindWindowByName``.
- **Django template engine**: optional, for templated script files.
- **asyncio**: all automation actions are async coroutines.
"""

import sys
import os
import traceback
import logging
import datetime
import importlib
import wx
from asyncio import sleep

from django.template import Template, Context

from pytigon.pytigon_run import run

logger = logging.getLogger(__name__)


# =============================================================================
# Core Automation Controller
# =============================================================================


class WxAuto:
    """Automation controller for wxPython applications.

    This is the central class that drives GUI automation. It wraps pyautogui
    for low-level mouse/keyboard control and wxPython for window discovery.
    It also manages subtitle (SRT) file generation for screen recordings.

    The controller is designed to be driven by a script (either a plain text
    file or a Python module) that issues commands line by line.

    Attributes:
        script_name (str):
            Base name used for the output subtitle file (``<name>.srt``).
        pos (wx.Point or None):
            Screen position of the application window. Used to constrain
            image-based lookups to the application region. May be None
            if the window is not yet shown.
        size (wx.Size or None):
            Dimensions of the application window.
        subtitle_id (int):
            Sequential counter for SRT subtitle entries. Starts at 1.
        start_time (datetime.datetime):
            Timestamp captured when the WxAuto instance is created. Used
            as the zero-point for subtitle timing.
        time_unit (float):
            Base time multiplier in seconds. Each ``.`` in a script line
            adds ``time_unit`` seconds of delay. Default 0.5.
        sys_time_unit (float):
            Delay inserted between system-level operations (focus changes,
            mouse movements) to ensure the UI has time to react. Default 0.5.
        pyautogui (module):
            Reference to the pyautogui module for mouse/keyboard control.
    """

    def __init__(self, script_name, pos, size):
        """Initialize the automation controller.

        Args:
            script_name (str):
                Base name used for the output subtitle file and for
                referencing the script in error messages.
            pos (wx.Point or None):
                Screen position of the application window. Pass None if
                the window position is not yet known.
            size (wx.Size or None):
                Dimensions of the application window. Pass None if unknown.

        Raises:
            ImportError:
                If pyautogui is not installed. Install with:
                ``pip install pyautogui``.
        """
        #: str: Base name for subtitle file (script_name.srt).
        self.script_name = script_name
        #: wx.Point or None: Application window screen position.
        self.pos = pos
        #: wx.Size or None: Application window dimensions.
        self.size = size
        #: int: Sequential subtitle counter, starting at 1.
        self.subtitle_id = 1
        #: datetime: Reference timestamp for subtitle timing offsets.
        self.start_time = datetime.datetime.now()
        #: float: Base delay per dot character in script lines.
        self.time_unit = 0.5
        #: float: Delay between system UI operations.
        self.sys_time_unit = 0.5
        self._window_cache = {}

        # Lazy-import pyautogui with a clear error message if missing.
        try:
            import pyautogui

            self.pyautogui = pyautogui
        except ImportError as e:
            raise ImportError(
                "pyautogui is required for WxAuto. Install it with: "
                "pip install pyautogui"
            ) from e

    # -------------------------------------------------------------------------
    # Region & Window Utilities
    # -------------------------------------------------------------------------

    def get_region(self):
        """Return the screen region occupied by the application window.

        The region is used by pyautogui's ``locateOnScreen`` to restrict
        image searches to the application area, improving both performance
        and accuracy.

        Returns:
            tuple or None:
                ``(x, y, width, height)`` if both position and size are known,
                ``None`` otherwise.
        """
        if self.pos is None or self.size is None:
            return None
        return (
            self.pos.x,
            self.pos.y,
            self.size.GetWidth(),
            self.size.GetHeight(),
        )

    # -------------------------------------------------------------------------
    # Mouse & Focus Actions
    # -------------------------------------------------------------------------

    async def auto_move_and_focus(self, window_name, set_focus=True):
        """Move the mouse cursor to the center of a named wx.Window.

        Uses ``wx.Window.FindWindowByName`` to locate the window by its
        internal name (set via ``wx.Window.SetName``). After moving the
        mouse, optionally sets keyboard focus to the window.

        Delays are inserted before and after each UI operation to give
        the window system time to process events.

        Args:
            window_name (str):
                Internal name of the wx.Window to find.
            set_focus (bool):
                If True, call ``SetFocus()`` on the found window before
                moving the mouse. Default True.

        Returns:
            wx.Window or None:
                The found window, or None if no window with the given
                name exists.
        """
        await sleep(self.sys_time_unit / 3)

        win = self._window_cache.get(window_name)
        if win is None or not win:
            win = wx.Window.FindWindowByName(window_name)
            if win:
                self._window_cache[window_name] = win
        if win and set_focus:
            win.SetFocus()
            await sleep(self.sys_time_unit / 3)

        if not win:
            logger.warning("window '%s' not found", window_name)
            return None

        # Calculate the center of the window in screen coordinates.
        pos = win.GetScreenPosition()
        size = win.GetSize()
        self.pyautogui.moveTo(
            pos[0] + int(size.GetWidth() / 2),
            pos[1] + int(size.GetHeight() / 2),
        )
        await sleep(self.sys_time_unit / 3)
        return win

    async def auto_click(self, window_name):
        """Move the mouse to a named window and perform a left click.

        This is a convenience wrapper around :meth:`auto_move_and_focus`
        followed by ``pyautogui.click()``.

        Args:
            window_name (str):
                Internal name of the wx.Window to click on.
        """
        await self.auto_move_and_focus(window_name)
        self.pyautogui.click()

    # -------------------------------------------------------------------------
    # Image-based Interaction
    # -------------------------------------------------------------------------

    async def auto_focus_on_img(self, image_name):
        """Locate an image on screen and move the mouse to its center.

        Uses pyautogui's ``locateOnScreen`` to find the given image within
        the application region (see :meth:`get_region`). This is useful for
        clicking buttons or icons that cannot be found by window name.

        Args:
            image_name (str):
                Path to the PNG image file to search for on screen.

        Raises:
            TypeError:
                If the image cannot be found within the search region.
        """
        await sleep(self.sys_time_unit / 2)

        region = self.get_region()
        location = self.pyautogui.locateOnScreen(image_name, region=region)
        if location is None:
            raise TypeError(
                "Image '%s' not found on screen (region: %s)" % (image_name, region)
            )

        # Calculate the geometric center of the matched region.
        x, y = self.pyautogui.center(location)
        self.pyautogui.moveTo(x, y)
        await sleep(self.sys_time_unit / 2)

    async def auto_click_on_img(self, image_name):
        """Locate an image on screen and click on its center.

        Convenience wrapper: calls :meth:`auto_focus_on_img` and then
        ``pyautogui.click()``.

        Args:
            image_name (str):
                Path to the PNG image file to locate and click.
        """
        await self.auto_focus_on_img(image_name)
        self.pyautogui.click()

    # -------------------------------------------------------------------------
    # Keyboard & Dropdown Simulation
    # -------------------------------------------------------------------------

    async def dropdown(self, delta):
        """Simulate opening a dropdown combo and selecting an item.

        The sequence is:
          1. Press Alt+Down to open the dropdown.
          2. Press Down/Up arrow keys ``abs(delta)`` times to navigate.
          3. Press Enter to confirm the selection.

        Args:
            delta (str or int):
                Number of items to move down (positive) or up (negative)
                from the top of the dropdown list.
        """
        delta2 = int(delta)

        # Open the dropdown.
        self.pyautogui.keyDown("alt")
        self.pyautogui.press("down")
        self.pyautogui.keyUp("alt")
        await sleep(1)

        # Navigate through the dropdown items.
        if delta2 > 0:
            for _ in range(0, delta2):
                self.pyautogui.press("down")
                await sleep(0.1)
        else:
            for _ in range(0, -delta2):
                self.pyautogui.press("up")
                await sleep(0.1)

        # Confirm selection.
        self.pyautogui.press("enter")
        await sleep(1)

    # -------------------------------------------------------------------------
    # Subtitle (SRT) Generation
    # -------------------------------------------------------------------------

    async def __lshift__(self, txt):
        """Write a subtitle entry to an SRT file.

        This is the handler for plain text lines in automation scripts
        (lines that don't start with ``.``, ``^``, ``#``, ``<<``, or ``@``).
        It generates an SRT (SubRip) subtitle entry with:

          - An incrementing subtitle ID.
          - A timestamp range from ``start_time + elapsed`` to
            ``start_time + elapsed + 3 seconds``.
          - The provided text as the subtitle content.

        The first entry opens the file in write mode (``"wt"``), subsequent
        entries append (``"at"``).

        Args:
            txt (str):
                The subtitle text to write. If empty or None, the method
                returns immediately without writing anything.
        """
        if not txt:
            return

        # Calculate timecodes relative to the automation start time.
        delta = datetime.datetime.now() - self.start_time
        t1 = datetime.datetime(year=2000, month=1, day=1, hour=0, minute=0) + delta
        t2 = t1 + datetime.timedelta(seconds=3)

        # Format the SRT timecode block:
        #   <id>
        #   HH:MM:SS,mmm --> HH:MM:SS,mmm
        s = "%d\n%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n" % (
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

        # First entry writes a fresh file; subsequent entries append.
        mode = "wt" if self.subtitle_id == 1 else "at"
        try:
            with open(self.script_name + ".srt", mode) as f:
                f.write(s)
                f.write(txt)
                f.write("\n\n")
            self.subtitle_id += 1
        except OSError as e:
            logger.error("Error writing subtitle file: %s", e)

    # -------------------------------------------------------------------------
    # Script Processing Engine
    # -------------------------------------------------------------------------

    async def process(self, txt, argv=None, change_tab=None):
        """Interpret and execute an automation script.

        This is the main entry point for running automation scripts. It can
        process either inline script text or load commands from a file
        (when ``txt`` starts with ``@``).

        When loading from a file, Django template rendering is optionally
        applied using the ``argv`` dictionary as template context.

        The ``change_tab`` parameter allows placeholder substitution before
        script execution. Replacements are specified as ``key:value`` pairs
        separated by ``;;`` (or passed as a list). Each ``$key`` in the
        script text is replaced by its corresponding value.

        Args:
            txt (str):
                Script content. If it starts with ``@``, the rest is treated
                as a filename to load. Otherwise, the string itself is the
                script.
            argv (dict or None):
                Optional template context variables. Only used when loading
                a script from file (``txt`` starts with ``@``).
            change_tab (str or list or None):
                Optional placeholder replacements.
                - If a string: use ``;;`` as separator between
                  ``key:value`` pairs, ``\\n`` as pair separator.
                - If a list: each element should be a ``key:value`` string.

        Script Command Reference
        ------------------------
        See the module-level documentation for the full script syntax.
        """
        # ---- Step 1: Load script content (from string or file) ------------
        if txt.startswith("@"):
            # Load commands from an external file.
            try:
                with open(txt[1:], "rt") as f:
                    txt2 = f.read()
                    # Optionally render Django template variables.
                    if argv:
                        t = Template(txt2)
                        c = Context(argv)
                        txt2 = t.render(c)
            except OSError as e:
                logger.error("Error reading script file '%s': %s", txt[1:], e)
                return
            except Exception as e:
                logger.error("Error rendering template '%s': %s", txt[1:], e)
                return
        else:
            txt2 = txt

        # ---- Step 2: Apply placeholder substitutions ----------------------
        if change_tab:
            # Normalize to a list of "key:value" strings.
            if isinstance(change_tab, str):
                change_tab2 = change_tab.replace(";;", "\n").split("\n")
            else:
                change_tab2 = list(change_tab)

            # Process in reverse so that nested $references work correctly
            # (later replacements don't interfere with earlier ones).
            change_tab2.reverse()
            for item in change_tab2:
                if ":" in item:
                    key, value = item.split(":", 1)
                    txt2 = txt2.replace("$" + key, value)

        # ---- Step 3: Interpret script line by line ------------------------
        for line in txt2.split("\n"):
            stripped = line.strip()

            # Skip empty lines entirely.
            if not stripped:
                continue

            # --- Pause: '.' lines ---
            # Each character adds time_unit seconds of delay.
            if stripped.startswith("."):
                await sleep(len(stripped) * self.time_unit)

            # --- Method call: '^method' or '^method:arg' ---
            # Calls a method on this WxAuto instance dynamically.
            elif stripped.startswith("^"):
                parts = stripped.split(":")
                try:
                    if len(parts) > 1:
                        # ^method_name:argument
                        method_name = parts[0][1:]  # strip leading '^'
                        await getattr(self, method_name)(parts[1])
                    else:
                        # ^method_name (no argument)
                        method_name = parts[0][1:]
                        await getattr(self, method_name)()
                except AttributeError as e:
                    logger.error("Unknown automation command: %s (%s)", parts[0], e)
                except Exception as e:
                    logger.error("Error executing command '%s': %s", stripped, e)

            # --- Comment: '#' lines ---
            # Ignored - used for documentation within scripts.
            elif stripped.startswith("#"):
                pass

            # --- Raw keyboard: '<<key1 key2 ...' ---
            # Sends raw key events via pyautogui.
            elif stripped.startswith("<<"):
                tokens = stripped[2:].split(" ")
                for token in tokens:
                    token = token.strip()
                    if not token:
                        continue
                    if token.startswith("^"):
                        # Release (keyUp) the key.
                        self.pyautogui.keyUp(token[1:])
                    elif token.startswith("_"):
                        # Press and hold (keyDown) the key.
                        self.pyautogui.keyDown(token[1:])
                    elif token.startswith("-"):
                        # Dash-based timing: each dash after the first
                        # adds time_unit/10 seconds of delay.
                        await sleep((len(token) - 1) * self.time_unit / 10)
                    else:
                        # Press and release a regular key.
                        self.pyautogui.press(token)

            # --- Proxy dispatch: 'name << value' or plain text ---
            else:
                if "<<" in stripped:
                    # Split on '<<' to get proxy_name and value.
                    parts = stripped.split("<<")
                    proxy_name = parts[0].strip()
                    value = parts[1].strip()
                    # Dynamically create a ControlProxy or ImgProxy.
                    await (getattr(self, proxy_name) << value)
                else:
                    # Plain text: write as subtitle entry.
                    await (self << stripped)

    # -------------------------------------------------------------------------
    # Dynamic Proxy Factory
    # -------------------------------------------------------------------------

    def __getattr__(self, item):
        """Create a ControlProxy or ImgProxy on demand.

        This enables the natural script syntax:

            my_button << "new label"     → ControlProxy
            icon_png << ""               → ImgProxy

        When the attribute name ends with ``_png``, an :class:`ImgProxy`
        is returned (image-based interaction). Otherwise, a
        :class:`ControlProxy` is returned (window-name-based interaction).

        The ``__`` in attribute names is converted to ``/`` to support
        file paths in image names.

        Args:
            item (str):
                The attribute name being accessed.

        Returns:
            ControlProxy or ImgProxy:
                A proxy object that handles the ``<<`` operator.
        """
        if item.endswith("_png"):
            # Convert '__' back to '/' for file paths,
            # and '_png' back to '.png'.
            img_path = item.replace("__", "/").replace("_png", ".png")
            return ImgProxy(self, img_path)
        else:
            return ControlProxy(self, item)


# =============================================================================
# Proxy Classes
# =============================================================================


class ControlProxy:
    """Proxy for interacting with a named wxPython control.

    In automation scripts, writing::

        button_name << "click"

    causes the mouse to move to the window named ``button_name`` and
    perform an action. The action depends on the value:

      - ``"click"`` → left mouse click at the control's center.
      - ``"focus"`` → only set keyboard focus, no click, no text.
      - Any other string → set the control's value via ``SetValue()``.

    This proxy is created automatically by :meth:`WxAuto.__getattr__`
    when an unknown attribute name is accessed.
    """

    def __init__(self, wx_auto, control_name):
        """Initialize the control proxy.

        Args:
            wx_auto (WxAuto):
                The parent WxAuto controller instance.
            control_name (str):
                Internal name of the wx.Window to target (set via
                ``wx.Window.SetName``).
        """
        #: WxAuto: Reference to the parent automation controller.
        self.wx_auto = wx_auto
        #: str: Name of the target wx.Window.
        self.control_name = control_name

    async def __lshift__(self, txt):
        """Execute an action on the target control.

        Args:
            txt (str):
                Action specifier:
                - ``"click"`` → click the control.
                - ``"focus"`` → focus only (no further action).
                - Any other string → call ``SetValue(txt)`` on the control.
        """
        # Move mouse to the control and optionally focus it.
        ctrl = await self.wx_auto.auto_move_and_focus(self.control_name)

        if txt == "click":
            self.wx_auto.pyautogui.click()
        elif txt == "focus":
            # Focus already set by auto_move_and_focus; nothing more to do.
            pass
        else:
            # Treat txt as a value to set on the control (e.g., text input).
            if ctrl is not None:
                ctrl.SetValue(txt)


class ImgProxy:
    """Proxy for interacting with a UI element identified by an image file.

    In automation scripts, writing::

        icon_png << ""

    causes pyautogui to search the screen for the image file ``icon.png``
    and click at its center.

    The image search is constrained to the application window region
    (see :meth:`WxAuto.get_region`) for better performance.

    This proxy is created automatically by :meth:`WxAuto.__getattr__`
    when the attribute name ends with ``_png``.
    """

    def __init__(self, wx_auto, img_name):
        """Initialize the image proxy.

        Args:
            wx_auto (WxAuto):
                The parent WxAuto controller instance.
            img_name (str):
                Path to the PNG image file to locate on screen.
        """
        #: WxAuto: Reference to the parent automation controller.
        self.wx_auto = wx_auto
        #: str: Path to the image file for screen matching.
        self.img_name = img_name
        #: None: Reserved for future use (cached image data).
        self.img = None

    async def __lshift__(self, txt):
        """Locate the image on screen and click its center.

        Args:
            txt (str):
                Currently unused. Reserved for future extensions
                (e.g., right-click, double-click).
        """
        await self.wx_auto.auto_focus_on_img(self.img_name)
        self.wx_auto.pyautogui.click()


# =============================================================================
# Module Entry Points
# =============================================================================

#: str: The last command-line argument, used as the script identifier.
#: When running as ``python wxauto.py myscript``, SCRIPT is ``"myscript"``.
SCRIPT = sys.argv[-1]


def autoit(win):
    """Entry point for wxPython automation from the main application frame.

    This function is called by the Pytigon application after the main
    window has been created. It sets up a :class:`WxAuto` instance and
    launches an async coroutine to execute the automation script.

    Two script types are supported:

    1. **Plain text** (``.txt`` files):
       The file is loaded and processed line by line by
       :meth:`WxAuto.process`.

    2. **Python module** (``.py`` files, or dotted module names):
       The module is imported and its ``wxauto(wx_auto, pyautogui, wx)``
       function is called. This gives full programmatic control over
       the automation.

    Errors during script execution are caught and printed via
    ``traceback.format_exc()`` to avoid crashing the application.

    Args:
        win (wx.Window or None):
            The main application window. Used to capture the screen
            position and size for region-constrained image searches.
            May be None if the window hasn't been created yet.
    """
    # Capture window geometry for region-constrained image matching.
    if win:
        pos = win.GetScreenPosition()
        size = win.GetSize()
    else:
        pos = None
        size = None

    wx_auto = WxAuto(SCRIPT, pos, size)

    async def astart():
        """Async entry point that runs the automation script."""
        try:
            # Give the application a moment to fully render.
            await sleep(1)

            if SCRIPT.endswith(".txt"):
                # Plain text script: load and process line by line.
                await wx_auto.process("@" + SCRIPT)
            else:
                # Python module: import and call wxauto().
                sys.path.insert(0, os.getcwd())
                module_name = SCRIPT.rsplit(".", 1)[0]
                scr = importlib.import_module(module_name)
                await scr.wxauto(wx_auto, wx_auto.pyautogui, wx)
        except Exception:
            logger.error("Automation error: %s", traceback.format_exc())

    # Schedule the automation coroutine on the wx event loop.
    wx.GetApp().StartCoroutine(astart, win)


# =============================================================================
# Direct Execution (python wxauto.py <script>)
# =============================================================================

if __name__ == "__main__":
    # Register the autoit function so that the main application frame
    # can discover and call it after initialization.
    setattr(wx, "pseudoimport", autoit)

    # Rewrite sys.argv to launch the main pytigon application with
    # video recording, RPC server, and inspection tool enabled.
    # Path adjustments handle the difference between the source
    # layout (pytigon-gui) and the installed layout (pytigon).
    sys.argv = [
        __file__.replace("pytigon-gui", "pytigon").replace("wxauto.py", "ptig.py"),
        "--video=%s.avi" % SCRIPT,
        "--rpc=8090",
        "schdevtools",
        "--inspection",
    ]

    # Launch the Pytigon application.
    run()
