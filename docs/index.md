# Pytigon GUI

**Version:** 0.260511 · **License:** LGPL 3.0 · **Author:** Sławomir Chołaj

---

## Overview

Pytigon GUI is the **wxPython** desktop frontend for the Pytigon framework.
It provides a rich set of GUI components – frames, pages, notebooks, toolbars,
grids, form controls, and popups – all integrated with the Django web backend.

## Module Map

| Module                           | Purpose                                                   |
| -------------------------------- | --------------------------------------------------------- |
| [`pytigon`](api/pytigon_main.md) | Main application entry point (~50K)                       |
| [`wxauto`](api/wxauto.md)        | wxPython automation utilities                             |
| [`guictrl`](api/guictrl.md)      | GUI controls – tags, buttons, grids, inputs, popups       |
| [`guiframe`](api/guiframe.md)    | Application frames – app, browser, form, notebook, page   |
| [`guilib`](api/guilib.md)        | GUI library – events, images, login, threading, WebSocket |
| [`toolbar`](api/toolbar.md)      | Toolbars – modern, standard, tree, generic, menu bar      |

## Quick Start

```python
from pytigon_gui.pytigon import main
main()
```

## Key Design Patterns

- **Tag-based UI** – XML-like tag syntax (`<ctrl>`, `<button>`, `<grid>`) parsed into wxPython widgets
- **Device Context** – Shared rendering abstraction with `pytigon_lib.schhtml`
- **Notebook/Page** – Tabbed document interface with dynamic page creation
- **Signal System** – Event-driven communication between components
- **WebSocket Bridge** – Real-time communication with the Django backend
