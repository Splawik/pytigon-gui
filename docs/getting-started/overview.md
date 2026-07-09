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
│   ├── basectrl.py        # Base control class
│   ├── ctrl.py            # Control system core
│   ├── display.py         # Display controls
│   ├── factory.py         # Control factory
│   ├── grids.py           # Grid definitions
│   ├── panels.py          # Panel controls
│   ├── tag.py             # Tag parser
│   ├── tag_ctrltag.py     # Tag → wxPython widget bridge
│   ├── tag_parsers.py     # XML-like tag parser
│   ├── tag_preprocess.py  # Tag preprocessor
│   ├── button/           # Button controls
│   ├── grid/             # Data grid with table proxies
│   ├── input/            # Form input controls
│   └── popup/            # Popup dialogs (HTML, select2)
├── guiframe/             # Frame management
│   ├── appframe.py       # Main application frame
│   ├── baseframe.py      # Base frame
│   ├── browserframe.py   # Embedded browser frame
│   ├── form.py           # Dynamic form generation
│   ├── manager.py        # Frame manager
│   ├── notebook.py       # Tabbed notebook
│   ├── notebookpage.py   # Individual notebook pages
│   └── page.py           # Base page component
├── guilib/               # Shared GUI utilities
│   ├── events.py         # Event definitions
│   ├── httperror.py      # HTTP error handling
│   ├── image.py          # Image loading/caching
│   ├── logindialog.py    # Login dialog
│   ├── pytigon_install.py# Pytigon installation helper
│   ├── signal.py         # Event signaling
│   ├── threadwindow.py   # Threaded window operations
│   ├── tools.py          # General utilities
│   └── websocket.py      # Django Channels bridge
└── toolbar/              # Toolbar system
    ├── basetoolbar.py    # Base toolbar
    ├── generictoolbar.py # Generic toolbar
    ├── menubar.py        # Menu bar
    ├── moderntoolbar.py  # Modern ribbon-style toolbar
    ├── standardtoolbar.py# Classic toolbar
    ├── standardtoolbarbuttons.py  # Standard toolbar buttons
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
