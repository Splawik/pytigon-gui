"""Pytigon GUI frame layer -- window hierarchy and layout management.

Window hierarchy:
    appframe.SChAppFrame (or browserframe.SChBrowserFrame)
        └── Notebook (SChNotebook) -- manages tab pages
            └── SChNotebookPage -- one tab, hosts SChPage windows
                └── SChPage -- container for up to 4 SChForm instances
                    ├── header  : SChForm (optional sash window at top)
                    ├── body    : SChForm (mandatory, fills center)
                    ├── footer  : SChForm (optional sash window at bottom)
                    └── panel   : SChForm (optional sash window at left)

Modules:
    baseframe      - SChBaseFrame base class
    appframe       - SChAppFrame: main desktop application window
    browserframe   - SChBrowserFrame: embedded webview variant
    manager        - SChAuiManager / SChAuiBaseManager: AUI helpers
    notebook       - SChNotebook: tab container
    notebookpage   - SChNotebookPage: single tab with split layout
    page           - SChPage: manages body/header/footer/panel forms
    form           - SChForm: HTML-rendered scrollable panel
"""
