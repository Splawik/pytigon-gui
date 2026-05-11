# Overview

## What is Pytigon GUI?

Pytigon GUI is the wxPython-based desktop interface for the Pytigon framework.
It renders UI defined in an XML-like tag syntax and connects to the Django backend
via an embedded HTTP client.

## Architecture

```
pytigon_gui/
├── pytigon.py            # Main application (50K lines)
├── wxauto.py             # wxPython automation utilities
├── guictrl/              # GUI control system
│   ├── tag*.py           # Tag parser → wxPython widget bridge
│   ├── button/           # Button controls
│   ├── grid/             # Data grid with table proxies
│   ├── input/            # Form input controls
│   └── popup/            # Popup dialogs (HTML, select2)
├── guiframe/             # Frame management
│   ├── appframe.py       # Main application frame
│   ├── form.py           # Dynamic form generation
│   ├── notebook.py       # Tabbed notebook
│   ├── notebookpage.py   # Individual notebook pages
│   └── page.py           # Base page component
├── guilib/               # Shared GUI utilities
│   ├── image.py          # Image loading/caching
│   ├── signal.py         # Event signaling
│   ├── threadwindow.py   # Threaded window operations
│   ├── websocket.py      # Django Channels bridge
│   └── tools.py          # General utilities
└── toolbar/              # Toolbar system
    ├── moderntoolbar.py  # Modern ribbon-style toolbar
    ├── standardtoolbar.py# Classic toolbar
    └── treetoolbar.py    # Tree-based toolbar
```

## UI Tag System

Pytigon GUI uses a custom XML-like syntax to define UI layout:

```xml
<panel>
  <toolbar type="modern" />
  <form>
    <field name="title" type="char" />
    <button action="save" />
  </form>
  <grid table="mytable" />
</panel>
```

Tags are parsed by `guictrl.tag_parsers` and `guictrl.tag_preprocess`,
then instantiated as wxPython widgets by `guictrl.tag_ctrltag`.

## Dependencies

- **wxPython** 4.x+ – Desktop GUI toolkit
- **Pillow** – Image handling
- **Django** – Backend communication
- **pytigon_lib** – Core library (HTTP client, HTML rendering)
