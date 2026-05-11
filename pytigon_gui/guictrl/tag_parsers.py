"""
HTML helper parsers for tree-structured data and option handling.

These classes support the CtrlTag parser in building nested tree data
(ldata) and flat option data (tdata) from HTML tags like <ul>, <li>,
<option>, and <data>.

Classes:
    TreeList, TreeUl, TreeLi, Data, OptionTag, CompositeChildTag
"""

from base64 import b64decode

from pytigon_lib.schhtml.basehtmltags import BaseHtmlElemParser
from pytigon_lib.schhtml.htmltools import superstrip
from pytigon_lib.schparser.html_parsers import Td


class TreeList:
    """Simple accumulator for tree-structured data.

    Collects child elements that form a nested tree representation.
    Used by TreeUl and TreeLi to build hierarchical data for tree widgets
    (TREE, TREELIST).
    """

    def __init__(self):
        self.children = []

    def append_to_tree(self, elem):
        """Append a child element to the tree.

        Args:
            elem: A child element (typically a list/tuple row).
        """
        self.children.append(elem)

    def get_list(self):
        """Return the accumulated tree children.

        Returns:
            List of child elements.
        """
        return self.children


class TreeUl(BaseHtmlElemParser):
    """Parser for <ul> tags that builds tree data structures.

    Collects <li> children into a nested list suitable for
    tree widgets (TREE, TREELIST). Each <li> becomes a row
    of [label, children, attrs].
    """

    def __init__(self, parent, parser, tag, attrs):
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)
        self.child_tags += ["li"]
        self.children = []

    def close(self):
        """On close, push the collected children to the parent."""
        self.parent.append_to_tree(["", self.children, self.attrs])

    def append_to_tree(self, elem):
        """Accept a child element into this tree level.

        Args:
            elem: A child element to append.
        """
        self.children.append(elem)

    def handle_starttag(self, parser, tag, attrs):
        """Handle nested <li> tags.

        Args:
            parser: The HTML parser.
            tag: Tag name.
            attrs: Tag attributes dict.

        Returns:
            A TreeLi parser for <li>, or None for other tags.
        """
        if tag == "li":
            return TreeLi(self, parser, tag, attrs)
        return None


class TreeLi(BaseHtmlElemParser):
    """Parser for <li> tags within tree structures.

    Collects text content and optional nested <ul> children,
    producing a [label, children, attrs] row.
    If the <li> contains an <a> or <ctrl-button>, its href
    is captured in the attrs.
    """

    def __init__(self, parent, parser, tag, attrs):
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)
        self.child = None

    def close(self):
        """On close, push the collected data as a tree row."""
        if self.child:
            self.child[0] = superstrip("".join(self.data))
            self.child[2] = self.attrs
            self.parent.append_to_tree(self.child)
        else:
            self.parent.append_to_tree([superstrip("".join(self.data)), [], self.attrs])

    def append_to_tree(self, elem):
        """Store a nested tree element as a pending child.

        Args:
            elem: A child tree element.
        """
        self.child = elem

    def handle_starttag(self, parser, tag, attrs):
        """Handle nested tags.

        <ul> starts a new sub-tree.
        <a> or <ctrl-button> captures href into attrs.

        Args:
            parser: The HTML parser.
            tag: Tag name.
            attrs: Tag attributes dict.

        Returns:
            A TreeUl for <ul>, or None.
        """
        if tag == "ul":
            return TreeUl(self, parser, tag, attrs)
        elif tag in ("a", "ctrl-button"):
            self.attrs["href"] = attrs["href"]
        return None


class Data(BaseHtmlElemParser):
    """Parser for <data> tags with base64-encoded content.

    Decodes base64 content and stores it in the parent's
    data2 attribute for use by CtrlTag.
    """

    def __init__(self, parent, parser, tag, attrs):
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)
        self.data = None

    def close(self):
        """Decode base64 data and store in parent.data2."""
        if self.data:
            self.parent.data2 = b64decode(self.data.encode("utf-8")).decode("utf-8")
        else:
            self.parent.data2 = ""

    def handle_data(self, data):
        """Accumulate text data, stripping trailing whitespace.

        Args:
            data: Raw text data chunk.
        """
        if self.data:
            self.data += data.rstrip(" \n")
        else:
            self.data = data.rstrip(" \n")


class OptionTag(BaseHtmlElemParser):
    """Parser for <option> tags that populate tdata.

    Collects option text and attributes into Td objects
    for use by choice/select widgets.
    """

    def __init__(self, parent, parser, tag, attrs):
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)

    def close(self):
        """On close, create a Td row and append to parent.tdata."""
        if self.data and len(self.data) > 0:
            data = "".join(self.data).replace("\n", "").replace("\r", "").strip()
            self.parent.tdata.append([Td(data, self.attrs)])


class CompositeChildTag(BaseHtmlElemParser):
    """Parser for nested tags within ctrl-composite.

    Builds a composite_data dict tree that mirrors the HTML
    structure inside a composite control. Each nested tag
    becomes a child node with tag, attrs, data, and children.
    """

    def __init__(self, parent, parser, tag, attrs):
        """Initialize composite child tag parser.

        Args:
            parent: Parent parser (CompositeChildTag or CtrlTag).
            parser: The HTML parser.
            tag: Tag name.
            attrs: Tag attributes dict.
        """
        BaseHtmlElemParser.__init__(self, parent, parser, tag, attrs)
        self.composite_data = {
            "tag": tag,
            "attrs": attrs,
            "data": None,
            "children": [],
        }

    def close(self):
        """On close, attach composite data to parent."""
        if self.data:
            self.composite_data["data"] = self.data
        if isinstance(self.parent, CompositeChildTag):
            self.parent.composite_data["children"].append(self.composite_data)
        elif isinstance(self.parent, CtrlTag):
            self.parent.data2.append(self.composite_data)

    def handle_starttag(self, parser, tag, attrs):
        """Handle nested tags within composite.

        Args:
            parser: The HTML parser.
            tag: Tag name.
            attrs: Tag attributes dict.

        Returns:
            A new CompositeChildTag for the nested tag.
        """
        return CompositeChildTag(self, parser, tag, attrs)


# Deferred import to avoid circular dependency at module level.
# Imported here because CompositeChildTag.close() references CtrlTag.
from pytigon_gui.guictrl.tag_ctrltag import CtrlTag
