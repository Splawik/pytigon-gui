"""Pytigon GUI frame layer -- window hierarchy and layout management.

Window hierarchy:
    appframe.SchAppFrame (or browserframe.SchBrowserFrame)
        └── Notebook (SchNotebook) -- manages tab pages
            └── SchNotebookPage -- one tab, hosts SchPage windows
                └── SchPage -- container for up to 4 SchForm instances
                    ├── header  : SchForm (optional sash window at top)
                    ├── body    : SchForm (mandatory, fills center)
                    ├── footer  : SchForm (optional sash window at bottom)
                    └── panel   : SchForm (optional sash window at left)

Modules:
    baseframe      - SchBaseFrame base class
    appframe       - SchAppFrame: main desktop application window
    browserframe   - SchBrowserFrame: embedded webview variant
    manager        - SChAuiManager / SChAuiBaseManager: AUI helpers
    notebook       - SchNotebook: tab container
    notebookpage   - SchNotebookPage: single tab with split layout
    page           - SchPage: manages body/header/footer/panel forms
    form           - SchForm: HTML-rendered scrollable panel
"""
