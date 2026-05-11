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
from pytigon_gui.guictrl.tag_parsers import (
    TreeList,
    TreeUl,
    TreeLi,
    Data,
    OptionTag,
    CompositeChildTag,
)

# Import primary tag handlers (also triggers register_tag_map calls)
from pytigon_gui.guictrl.tag_ctrltag import (
    CtrlTag,
    ComponentTag,
    _ATTRIBUTES,
)

# Import preprocess functions (also triggers register_tag_preprocess_map calls)
from pytigon_gui.guictrl.tag_preprocess import (
    SCHTYPE_MAP,
    HIDDEN_DIVS,
    table_to_ctrltab,
    input_to_ctrltab,
    textarea_to_ctrltab,
    select_to_ctrltab,
    a_to_button,
    div_convert,
    label_to_th,
    error_span_to_error,
    error_p_to_error,
    ul_convert,
    component_convert,
)
