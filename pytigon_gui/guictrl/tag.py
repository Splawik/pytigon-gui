"""
Backward-compatibility shim for pytigon_gui.guictrl.tag.

This module re-exports all tag parser classes and preprocess functions
from the refactored submodules. The actual implementations now live in:

    guictrl/tag_parsers.py     - TreeList, TreeUl, TreeLi, Data,
                                 OptionTag, CompositeChildTag
    guictrl/tag_ctrltag.py     - CtrlTag, ComponentTag + register_tag_map calls
    guictrl/tag_preprocess.py  - All preprocess functions + register calls

Importing this module triggers all register_tag_map and
register_tag_preprocess_map calls needed by the HTML parser.
"""

# Import parsers (helper classes for tree data, options, composites)
# Import primary tag handlers (also triggers register_tag_map calls)
from pytigon_gui.guictrl.tag_ctrltag import (
    _ATTRIBUTES,
    ComponentTag,
    CtrlTag,
)
from pytigon_gui.guictrl.tag_parsers import (
    CompositeChildTag,
    Data,
    OptionTag,
    TreeLi,
    TreeList,
    TreeUl,
)

# Import preprocess functions (also triggers register_tag_preprocess_map calls)
from pytigon_gui.guictrl.tag_preprocess import (
    HIDDEN_DIVS,
    SCHTYPE_MAP,
    a_to_button,
    component_convert,
    div_convert,
    error_p_to_error,
    error_span_to_error,
    input_to_ctrltab,
    label_to_th,
    select_to_ctrltab,
    table_to_ctrltab,
    textarea_to_ctrltab,
    ul_convert,
)
