"""
Primary tag handler classes for the SchForm widget system.

Converts HTML ctrl-* tags into wxPython widget instances by
dispatching to the appropriate widget class from guictrl.ctrl.

Classes:
    CtrlTag, ComponentTag
"""

from urllib.parse import unquote
import ast
import logging

import wx
from pytigon_lib.schhtml.tags.table_tags import TableTag
from pytigon_lib.schhtml.basehtmltags import (
    BaseHtmlElemParser,
    register_tag_map,
)
from pytigon_lib.schparser.html_parsers import Td
from pytigon_lib.schtools.tools import is_null
from pytigon_lib.schtools.schhtmlgen import make_start_tag

import pytigon_gui.guictrl.ctrl as schctrl

logger = logging.getLogger(__name__)

# Deferred imports to avoid circular dependency at module level.
# These are imported at function-call time within handle_ctrl / __init__.
# from pytigon_gui.guictrl.tag_parsers import (
#     TreeList, TreeUl, TreeLi, Data, OptionTag, CompositeChildTag,
# )

# Attributes forwarded from HTML tag attrs to widget kwargs.
_ATTRIBUTES = (
    "name",
    "href",
    "label",
    "target",
    "valuetype",
    "defaultvalue",
    "length",
    "maxlength",
    "readonly",
    "src",
    "param",
    "fields",
    "hidden",
    "checked",
    "style",
    "id",
    "onload",
)


class CtrlTag(TableTag):
    """Handler for all tags starting with 'ctrl-'.

    Parses the HTML tag attributes, collects child data (tdata, ldata),
    calculates relative sizes, and creates the corresponding wxPython
    widget via schctrl (pytigon_gui.guictrl.ctrl).

    Lifecycle:
        1. __init__ - Parse attributes, calculate sizes
        2. Child tags populate tdata/ldata via helper parsers
        3. close() - Build kwargs, create or update widget
        4. render() - Position and size the widget in the layout
    """

    def __init__(self, parent, parser, tag, attrs):
        """Initialize the ctrl tag handler.

        Args:
            parent: Parent HTML element parser.
            parser: The HTML parser instance.
            tag: Full tag name (e.g. 'ctrl-text', 'ctrl-button').
            attrs: Tag attributes dict.
        """
        TableTag.__init__(self, parent, parser, tag, attrs)

        self.list = None
        self.child_tags += ["ul", "li", "data", "option", "div"]
        self.subtab = True
        self.kwargs = {}
        self.classObj = None
        self.data2 = None
        self.obj = None
        self.width_best = -1
        self.width_min = -1
        self.width_max = -1
        self.tdata = []

        if self.parser.parse_only:
            return
        self._calc_relative_size()

        # Initialize composite data storage
        if self.tag == "ctrl-composite":
            self.data2 = []

    # ------------------------------------------------------------------
    # Tree data support
    # ------------------------------------------------------------------

    def append_to_tree(self, elem):
        """Append a tree element (from <ul>/<li> parsing).

        Creates a TreeList on first call.

        Args:
            elem: A tree data element.
        """
        from pytigon_gui.guictrl.tag_parsers import TreeList

        if not self.list:
            self.list = TreeList()
        self.list.append_to_tree(elem)

    # ------------------------------------------------------------------
    # Size calculation
    # ------------------------------------------------------------------

    def _calc_relative_size(self):
        """Calculate width and height from percentage/relative attributes.

        Resolves percentage sizes against the parent window dimensions
        and the parser's device context width.
        """
        if "width" in self.attrs:
            width, height2 = self.get_parent_window().GetSize()
            if width == 1 and height2 == 1:
                width, height2 = (
                    self.get_parent_window().GetParent().GetParent().GetSize()
                )
            if self.parser.dc.width > 0 and self.parser.dc.width < width:
                width = self.parser.dc.width
            m = self._get_parent_pseudo_margins()
            width = max(0, (width - m[0]) - m[1])
            self.width = self._norm_sizes([self.attrs["width"]], width)[0]

        if "height" in self.attrs:
            width2, height = self.get_parent_window().GetSize()
            if width2 == 1 and height == 1:
                width2, height = (
                    self.get_parent_window().GetParent().GetParent().GetSize()
                )
            m = self._get_parent_pseudo_margins()
            height = max(0, (height - m[2]) - m[3] - 3)
            self.height = self._norm_sizes([self.attrs["height"]], height)[0]

    def get_context(self):
        """Return layout context with button sizes and top offset.

        Returns:
            Dict with button_size_dx, button_size_dy, and top keys.
        """
        if self.parent and hasattr(self.parent, "y"):
            _y = self.parent.y + 3
        else:
            _y = 1
        return {
            "button_size_dx": wx.Button.GetDefaultSize()[0] + 14,
            "button_size_dy": wx.Button.GetDefaultSize()[1] + 14,
            "top": _y,
        }

    def calc_col_sizes(self):
        """Calculate column sizes for table layout.

        Falls back to width 400 if best size is negative.
        """
        sizes = self.calc_width()
        if sizes[0] >= 0:
            self.width = sizes[0] + self.extra_space[0] + self.extra_space[1]
        else:
            self.width = 400

    def get_height(self):
        """Calculate and return the widget height.

        Returns:
            Integer height value, minimum 200.
        """
        height = self.calc_height()
        if height >= 0:
            self.height = height + self.extra_space[2] + self.extra_space[3]
        else:
            self.height = 200
        return self.height

    def calc_width(self):
        """Calculate width from widget best/min/max sizes.

        Returns:
            Tuple of (best_width, min_width, max_width).
        """
        d = self.extra_space[0] + self.extra_space[1]
        if self.width < 0:
            if self.obj:
                self.width_best, self.height_best = self.obj.GetBestSize()
                self.width_min, height_min = self.obj.GetMinSize()
                self.width_max, height_max = self.obj.GetMaxSize()
                return (
                    self.width_best + d,
                    self.width_min + d,
                    self.width_max + d,
                )
            else:
                return (d, d, d)
        else:
            return (self.width, self.width, self.width)

    def calc_height(self):
        """Calculate height from widget best size.

        Returns:
            Integer height including extra space.
        """
        if self.height >= 0:
            return self.height
        if self.obj:
            self.width_best, self.height_best = self.obj.GetBestSize()
        else:
            self.height_best = 30
        self.height = self.height_best + self.extra_space[2] + self.extra_space[3]
        return self.height

    # ------------------------------------------------------------------
    # Child tag handling
    # ------------------------------------------------------------------

    def handle_data(self, data):
        """Process raw text data.

        For ctrl-checkbox, text data is suppressed.

        Args:
            data: Raw text data.

        Returns:
            Result from parent handle_data.
        """
        if self.tag == "ctrl-checkbox":
            pass
        return BaseHtmlElemParser.handle_data(self, data)

    def handle_starttag(self, parser, tag, attrs):
        """Dispatch child tag to the appropriate parser.

        Routes <ul>, <li>, <data>, <option> to their helper parsers.
        For ctrl-composite, delegates to CompositeChildTag.

        Args:
            parser: The HTML parser.
            tag: Child tag name.
            attrs: Child tag attributes.

        Returns:
            A parser instance for the child tag, or None.
        """
        from pytigon_gui.guictrl.tag_parsers import (
            TreeUl,
            TreeLi,
            Data,
            OptionTag,
            CompositeChildTag,
        )

        if self.tag == "ctrl-checkbox":
            pass

        if self.tag == "ctrl-composite":
            return CompositeChildTag(self, parser, tag, attrs)

        if tag[:3] + "*" in self.child_tags:
            return self.class_from_tag_name(tag[:3] + "*")(self, parser, tag, attrs)
        elif tag == "ul":
            return TreeUl(self, parser, tag, attrs)
        elif tag == "li":
            return TreeLi(self, parser, tag, attrs)
        elif tag == "data":
            return Data(self, parser, tag, attrs)
        elif tag == "option":
            return OptionTag(self, parser, tag, attrs)
        elif tag in self.child_tags:
            o = self.class_from_tag_name(tag)
            if o:
                return o(self, parser, tag, attrs)
            return None
        return None

    # ------------------------------------------------------------------
    # TData (table data) handling
    # ------------------------------------------------------------------

    def _append_to_tdata(self):
        """Convert parsed <tr>/<td> rows into tdata format.

        Each cell becomes a Td object with text, attrs, and nested
        object table.
        """
        if len(self.tr_list) > 0:
            for tr in self.tr_list:
                row = []
                for td in tr:
                    td_obj = Td(td.to_txt(), td.attrs, td.to_obj_tab())
                    row.append(td_obj)
                self.tdata.append(row)

    # ------------------------------------------------------------------
    # Widget creation and layout
    # ------------------------------------------------------------------

    def close(self):
        """Finalize tag parsing and create/update the widget.

        In parse_only mode, registers tdata for later use.
        Otherwise, calls handle_ctrl to instantiate the widget.
        """
        self._append_to_tdata()
        if self.parser.parse_only:
            if hasattr(self.parser, "register_tdata"):
                self.parser.register_tdata(self.tdata, self.tag, self.attrs)
        else:
            self.handle_ctrl(self.tag)
        return TableTag.close(self)

    def render(self, dc):
        """Position and size the widget within the layout.

        Args:
            dc: Device context for rendering.

        Returns:
            Tuple of (height, False) for layout continuation.
        """
        if dc.rec and self.obj:
            self.obj.SetSize(
                int(dc.x + self.extra_space[0]),
                int(dc.y + self.extra_space[2]),
                max(0, int((self.width - self.extra_space[0]) - self.extra_space[1])),
                max(0, int((self.height - self.extra_space[2]) - self.extra_space[3])),
            )
        return (self.height, False)

    def draw_atom(self, dc, style, x, y, dx, dy):
        """Draw the widget atomically at the given position.

        Args:
            dc: Device context.
            style: Drawing style (unused).
            x, y: Position.
            dx, dy: Size hints (unused).
        """
        dc2 = dc.subdc(x, y, self.width, self.height)
        cont = True
        while cont:
            dy, cont = self.render(dc2)
            dc2.y += dy

    def get_parent_window(self):
        """Get the wxPython parent window for widget creation.

        Returns:
            The parent window from the parser.
        """
        return self.parser.get_parent_window()

    def handle_ctrl(self, tag):
        """Create or update the wxPython widget for this ctrl tag.

        This is the main dispatch method that:
        1. Resolves the widget name (with deduplication)
        2. Builds kwargs from tag attributes
        3. Looks up the widget class from schctrl
        4. Pops an existing widget or creates a new one
        5. Sets the initial value and triggers after_create

        Args:
            tag: The ctrl tag name (e.g. 'ctrl-text').
        """
        # Resolve widget name
        if "name" in self.attrs:
            name_reg = is_null(self.attrs["name"], "")
            parent = self.parent
            while parent:
                if hasattr(parent, "reg_field"):
                    name_reg = parent.reg_field(self.attrs["name"])
                    break
                parent = parent.parent
            name = name_reg
        else:
            name = tag[4:]
        self.attrs["name"] = name

        parent = self.get_parent_window()
        if parent:
            gparent = parent.GetParent()
            tmp = name
            i = 1
            while gparent.test_ctrl(tmp):
                tmp = name + "__" + str(i)
                i += 1
            name = tmp

        # Build kwargs from attributes
        for atrybut in _ATTRIBUTES:
            if atrybut in self.attrs:
                attr_val = self.attrs[atrybut]
                self.kwargs[atrybut] = "" if attr_val is None else attr_val

        # Resolve value
        valuetype = "data"
        if "valuetype" in self.attrs:
            if self.attrs["valuetype"] == "ref":
                valuetype = "ref"
            if self.attrs["valuetype"] == "str":
                valuetype = "str"
        if "value" in self.attrs:
            if valuetype == "str":
                value = unquote(self.attrs["value"])
            else:
                try:
                    value = ast.literal_eval(self.attrs["value"])
                except (ValueError, SyntaxError):
                    logger.warning("Value error: %s", self.attrs["value"])
                    value = None
        else:
            value = None
        if "strvalue" in self.attrs:
            value = self.attrs["strvalue"]

        # Set size from calculated dimensions
        self.kwargs["size"] = wx.Size(
            max(0, int((self.width - self.extra_space[0]) - self.extra_space[1])),
            max(0, int((self.height - self.extra_space[2]) - self.extra_space[3])),
        )

        # Look up widget class by tag name
        try:
            if tag.upper().startswith("CTRL-"):
                self.classObj = getattr(schctrl, tag[5:].upper())
            elif tag.startswith("_"):
                self.classObj = getattr(schctrl, tag[1:].upper())
            else:
                self.classObj = getattr(schctrl, tag.upper())
        except AttributeError:
            return True

        # Attach tdata and ldata to kwargs
        if len(self.tdata) > 0:
            self.kwargs["tdata"] = self.tdata
        self.kwargs["param"] = dict(self.attrs)
        self.kwargs["param"]["table_lp"] = str(self.parser.table_lp)
        self.kwargs["param"]["tag"] = tag.lower()
        if self.data2 is not None:
            self.kwargs["param"]["data"] = is_null(self.data2, "")
        else:
            self.kwargs["param"]["data"] = "".join(self.data)
        if self.list:
            l = self.list.get_list()
            self.kwargs["ldata"] = l

        # Create or update widget
        if parent:
            gparent = parent.GetParent()
            obj = gparent.pop_ctrl(name)
            if obj:
                if parent.update_controls:
                    if hasattr(obj, "process_refr_data"):
                        obj.process_refr_data(**self.kwargs)
                    elif not (hasattr(obj, "is_ctrl_block") and obj.is_ctrl_block()):
                        obj.SetValue(value)
                parent.append_ctrl(obj)
            else:
                obj = self.classObj(parent, **self.kwargs)
                if not obj:
                    logger.error("ERROR: %s", self.classObj)
                obj.set_unique_name(name)
                if value is not None and valuetype in ("data", "str"):
                    obj.SetValue(value)
                obj.after_create()
                parent.append_ctrl(obj)
            self.obj = obj


# Register CtrlTag as the handler for all ctr* tags
register_tag_map("ctr*", CtrlTag)


class ComponentTag(CtrlTag):
    """Handler for _component tags with nested child tracking.

    Extends CtrlTag to support web components that contain
    nested HTML. Tracks tag depth via a counter and manages
    the close_tag for proper nesting.

    Window dimensions from 'window-width' and 'window-height'
    attributes are forwarded as 'width' and 'height'.
    """

    def __init__(self, parent, parser, tag, attrs):
        """Initialize the component tag handler.

        Args:
            parent: Parent HTML element parser.
            parser: The HTML parser instance.
            tag: Tag name.
            attrs: Tag attributes dict.
        """
        super().__init__(parent, parser, tag, attrs)
        self.data.append(make_start_tag(attrs["_tag"], attrs))
        self.count = 1
        self._close_tag = None

    def close(self):
        """Close the component tag, forwarding window dimensions.

        Returns:
            Result from parent close().
        """
        if "window-width" in self.attrs:
            self.attrs["width"] = self.attrs["window-width"]
        if "window-height" in self.attrs:
            self.attrs["height"] = self.attrs["window-height"]
        return super().close()

    def handle_starttag(self, parser, tag, attrs):
        """Handle nested start tags within component.

        Uses _tag attribute for the actual tag name if present.
        Increments the depth counter and returns self for
        continued nesting.

        Args:
            parser: The HTML parser.
            tag: Tag name.
            attrs: Tag attributes dict.

        Returns:
            self to continue nesting.
        """
        tag2 = attrs.get("_tag", tag)
        self.data.append(make_start_tag(tag2, attrs))
        if not self._close_tag:
            self._close_tag = self.close_tag
        self.count += 1
        return self

    def handle_endtag(self, tag):
        """Handle nested end tags with depth tracking.

        Decrements the counter. When it reaches zero, restores
        the original close_tag and delegates to the parent.

        Args:
            tag: The closing tag name.

        Returns:
            self while nested, or parent result when complete.
        """
        self.data.append("</" + tag + ">")
        self.count -= 1
        if self.count == 0:
            if self._close_tag:
                self.close_tag = self._close_tag
            return super().handle_endtag(tag)
        else:
            return self


# Register ComponentTag as handler for _component tags
register_tag_map("_component", ComponentTag)
