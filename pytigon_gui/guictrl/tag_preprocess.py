"""
Tag preprocess functions for converting standard HTML tags to ctrl-* tags.

These functions are registered via register_tag_preprocess_map and are
called by the HTML parser before normal tag handling. They transform
standard HTML elements (<input>, <select>, <textarea>, <a>, <div>, etc.)
into the corresponding ctrl-* tags that the CtrlTag class can handle.

Each function receives (parent, attrs) and returns (new_tag, new_attrs)
or the original (tag, attrs) if no conversion is needed.

Constants:
    SCHTYPE_MAP, HIDDEN_DIVS

Functions:
    table_to_ctrltab, input_to_ctrltab, textarea_to_ctrltab,
    select_to_ctrltab, a_to_button, div_convert, label_to_th,
    error_span_to_error, error_p_to_error, ul_convert, component_convert
"""

import wx
from pytigon_lib.schhtml.basehtmltags import register_tag_preprocess_map
from pytigon_lib.schtools.tools import is_null


# ---------------------------------------------------------------------------
# Mapping from Django model field types to ctrl widget names
# ---------------------------------------------------------------------------
SCHTYPE_MAP = {
    "FloatField": "float",
    "IntegerField": "num",
    "DecimalField": "amount",
    "TimeField": "time",
    "DateTimeField": "datetimepicker",
}

# ---------------------------------------------------------------------------
# CSS classes that cause divs to be hidden in the form layout
# ---------------------------------------------------------------------------
HIDDEN_DIVS = [
    "ajax-region",
    "td_information",
    "td_action",
]


# ---------------------------------------------------------------------------
# Tag preprocess functions
# ---------------------------------------------------------------------------


def table_to_ctrltab(parent, attrs):
    """Convert <table> to ctrl-table or ctrl-list based on CSS class.

    - 'tabsort' class → ctrl-table with minheight 60px
    - 'listctrl' class → ctrl-list
    - Otherwise → unchanged <table>

    Args:
        parent: Parent parser.
        attrs: Table tag attributes.

    Returns:
        Tuple of (new_tag, new_attrs).
    """
    if "class" in attrs:
        if "tabsort" in attrs["class"]:
            attrs["minheight"] = "60px"
            return ("ctrl-table", attrs)
        if "listctrl" in attrs["class"]:
            return ("ctrl-list", attrs)
    return ("table", attrs)


def input_to_ctrltab(parent, attrs):
    """Convert <input> to the appropriate ctrl-* tag.

    Maps HTML input types to ctrl widget types based on:
    - schtype attribute (Django field type → SCHTYPE_MAP)
    - type attribute (text, button, email, hidden, password, radio,
      checkbox, file, submit)
    - class attribute (dateinput, datetimeinput)
    - name attribute (date_ prefix → datepicker)

    Also handles size, maxlength, value, and label attribute propagation.

    Args:
        parent: Parent parser.
        attrs: Input tag attributes.

    Returns:
        Tuple of (new_tag, new_attrs).
    """
    attrs_ret = {}
    ret = "text"
    upload = False

    input_type = attrs.get("type", "text")
    schtype = attrs.get("schtype", "text")
    classname = attrs.get("class", "text")

    # Determine widget type from schtype (Django field mapping)
    if schtype in SCHTYPE_MAP:
        ret = SCHTYPE_MAP[schtype]
    elif input_type == "text":
        if classname == "dateinput":
            ret = "datepicker"
        elif classname == "datetimeinput":
            ret = "datetimepicker"
        else:
            ret = "text"
    elif input_type == "button":
        ret = "button"
    elif input_type == "email":
        ret = "masktext"
        attrs_ret = {"src": "!EMAIL", "width": "250", "valuetype": "str"}
        if "value" in attrs:
            attrs_ret["value"] = attrs["value"]
    elif input_type == "hidden":
        ret = "text"
        attrs_ret = {"hidden": "1", "width": "0", "height": "0"}
    elif input_type == "password":
        ret = "password"
    elif input_type == "radio":
        ret = "radiobutton"
        if "checked" in attrs:
            attrs_ret["checked"] = "1"
        if "value" in attrs:
            attrs_ret["value"] = attrs["value"]
            attrs_ret["valuetype"] = "str"
    elif input_type == "checkbox":
        ret = "checkbox"
        if "checked" in attrs:
            attrs_ret["checked"] = "1"
        if "value" in attrs:
            attrs_ret["value"] = attrs["value"]
            attrs_ret["valuetype"] = "str"
    elif input_type == "file":
        ret = "filebrowsebutton"
        upload = True
    elif input_type == "submit":
        ret = "button"
        target = attrs.get("target", "_parent_refr")
        attrs_ret = {
            "defaultvalue": "1",
            "param": "post",
            "target": target,
            "id": "wx.ID_OK",
        }
        href = "."
        fields = None
        p = parent
        while p:
            if hasattr(p, "gethref"):
                href = p.gethref()
                fields = p.get_fields()
                if p.get_upload():
                    attrs_ret["valuetype"] = "upload"
                break
            p = p.parent
        if href is None:
            href = ""
        attrs_ret["href"] = href
        if fields:
            attrs_ret["fields"] = fields

    # Width from size attribute
    if "size" in attrs and input_type in ("text", "email"):
        width_text = 10 * int(is_null(attrs["size"], 20))
        if width_text > 400:
            width_text = 8 * int(is_null(attrs["size"], 20))
        if width_text > 480:
            width_text = 480
        attrs_ret["width"] = str(width_text)

    # Maxlength handling: prefer maxlength, then max_length, then size
    if "maxlength" in attrs and input_type in ("text",):
        attrs_ret["maxlength"] = str(is_null(attrs["maxlength"], "80"))
    elif "max_length" in attrs and input_type in ("text",):
        attrs_ret["maxlength"] = str(is_null(attrs["max_length"], "80"))
    elif "size" in attrs:
        attrs_ret["maxlength"] = str(int(is_null(attrs["size"], "80")))

    # Value propagation for text-like inputs
    if "value" in attrs and input_type in ("text", "hidden", "checkbox"):
        attrs_ret["value"] = is_null(attrs["value"], "")
        attrs_ret["valuetype"] = "str"

    # Label from value for buttons
    if "value" in attrs and input_type in ("button", "submit"):
        attrs_ret["label"] = is_null(attrs["value"], "")

    # Checkbox label from title
    if "title" in attrs and input_type == "checkbox":
        attrs_ret["label"] = is_null(attrs["title"], "")

    # Upload flag propagation
    if "name" in attrs:
        p = parent
        while p:
            if p.form_obj:
                if upload:
                    p.form_obj.set_upload(upload)
                break
            p = p.parent
        attrs_ret["name"] = attrs["name"]
        # Auto-detect date fields by name prefix
        if ret == "text" and "date_" in attrs["name"]:
            ret = "datepicker"

    # Forward remaining attributes not already set
    for attr in attrs:
        if attr not in attrs_ret and attr != "value":
            attrs_ret[attr] = attrs[attr]

    return ("ctrl-" + ret, attrs_ret)


def textarea_to_ctrltab(parent, attrs):
    """Convert <textarea> to ctrl-textarea.

    Forwards cols, rows, src, and name attributes.

    Args:
        parent: Parent parser.
        attrs: Textarea attributes.

    Returns:
        Tuple of ('ctrl-textarea', new_attrs).
    """
    attrs_ret = {}
    for key in ("cols", "rows", "src", "name"):
        if key in attrs:
            attrs_ret[key] = attrs[key]
    return ("ctrl-textarea", attrs_ret)


def select_to_ctrltab(parent, attrs):
    """Convert <select> to ctrl-select.

    Args:
        parent: Parent parser.
        attrs: Select attributes.

    Returns:
        Tuple of ('ctrl-select', attrs).
    """
    return ("ctrl-select", attrs)


def a_to_button(parent, attrs):
    """Convert <a> tags with button-like classes to ctrl-button.

    Converts <a> tags whose class contains 'popup', 'button', 'btn',
    or 'schbtn' into ctrl-button tags. The 'schbtn' class has special
    handling: inside a ctrl-table it remains as <a>, otherwise it
    becomes a ctrl-button.

    Args:
        parent: Parent parser.
        attrs: Anchor attributes.

    Returns:
        Tuple of ('ctrl-button', attrs) or ('a', attrs).
    """
    if "class" not in attrs:
        return ("a", attrs)

    classes = attrs["class"]
    is_button_class = any(c in classes for c in ("popup", "button", "btn", "schbtn"))
    if not is_button_class:
        return ("a", attrs)

    if "schbtn" in classes:
        try:
            if parent.parent.parent.tag == "ctrl-table":
                return ("ctrl-button", attrs)
        except AttributeError:
            return ("a", attrs)
    else:
        try:
            if parent.parent.parent.tag == "ctrl-table":
                return ("a", attrs)
        except AttributeError:
            pass
        return ("ctrl-button", attrs)

    return ("a", attrs)


def div_convert(parent, attrs):
    """Convert <div> tags based on CSS class.

    Mapping:
    - 'popup'                    → <div> (unchanged)
    - 'form-group'               → <tr>
    - 'controls'                 → <td>
    - 'tree'                     → ctrl-tree
    - 'select2'                  → ctrl-composite
    - 'checkbox'                 → <th> (adds empty <th> before)
    - Classes in HIDDEN_DIVS     → 'none' (removed from output)

    Args:
        parent: Parent parser.
        attrs: Div attributes.

    Returns:
        Tuple of (new_tag, attrs).
    """
    if "class" not in attrs:
        return ("div", attrs)

    classes = attrs["class"]

    if "popup" in classes:
        return ("div", attrs)
    if "form-group" in classes:
        return ("tr", attrs)
    if "controls" in classes:
        return ("td", attrs)
    if "tree" in classes:
        return ("ctrl-tree", attrs)
    if "select2" in classes:
        return ("ctrl-composite", attrs)
    if "checkbox" in classes:
        # Insert empty <th> before the checkbox cell
        obj = parent.parent.handle_starttag(parent.parser, "th", {})
        if obj:
            obj.handle_endtag("th")
        return ("th", attrs)

    for hidden_cls in HIDDEN_DIVS:
        if hidden_cls in classes:
            return ("none", attrs)

    return ("div", attrs)


def label_to_th(parent, attrs):
    """Convert <label> to <th> for table-based form layout.

    Args:
        parent: Parent parser.
        attrs: Label attributes.

    Returns:
        Tuple of ('th', attrs).
    """
    return ("th", attrs)


def error_span_to_error(parent, attrs):
    """Convert <span class="help-block"> to ctrl-errorlist.

    Args:
        parent: Parent parser.
        attrs: Span attributes.

    Returns:
        Tuple of ('ctrl-errorlist', attrs) or ('span', attrs).
    """
    if "class" in attrs and attrs["class"] == "help-block":
        return ("ctrl-errorlist", attrs)
    return ("span", attrs)


def error_p_to_error(parent, attrs):
    """Convert <p class="help-block"> to a comment.

    Strips error message paragraphs from the output by converting
    them to comments.

    Args:
        parent: Parent parser.
        attrs: Paragraph attributes.

    Returns:
        Tuple of ('comment', attrs) or ('p', attrs).
    """
    if "class" in attrs and attrs["class"] == "help-block":
        return ("comment", attrs)
    return ("p", attrs)


def ul_convert(parent, attrs):
    """Convert <ul> based on CSS class.

    - 'root' class → ldata (tree data container)
    - 'errorlist' class → ctrl-errorlist

    Args:
        parent: Parent parser.
        attrs: UL attributes.

    Returns:
        Tuple of (new_tag, attrs).
    """
    if "class" in attrs:
        if "root" in attrs["class"]:
            return ("ldata", attrs)
        if attrs["class"] == "errorlist":
            return ("ctrl-errorlist", attrs)
    return ("ul", attrs)


def component_convert(parent, attrs):
    """Convert custom element tags (*-*) to _component.

    Used for web component custom elements.

    Args:
        parent: Parent parser.
        attrs: Component attributes.

    Returns:
        Tuple of ('_component', attrs).
    """
    return ("_component", attrs)


# ---------------------------------------------------------------------------
# Register all preprocess functions
# ---------------------------------------------------------------------------

register_tag_preprocess_map("table", table_to_ctrltab)
register_tag_preprocess_map("input", input_to_ctrltab)
register_tag_preprocess_map("textarea", textarea_to_ctrltab)
register_tag_preprocess_map("select", select_to_ctrltab)
register_tag_preprocess_map("a", a_to_button)
register_tag_preprocess_map("div", div_convert)
register_tag_preprocess_map("label", label_to_th)
register_tag_preprocess_map("span", error_span_to_error)
register_tag_preprocess_map("p", error_p_to_error)
register_tag_preprocess_map("ul", ul_convert)
register_tag_preprocess_map("*-*", component_convert, "ctr*")
