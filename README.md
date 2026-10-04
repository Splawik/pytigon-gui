# pytigon-gui

**wxPython desktop frontend for the Pytigon framework** — a rich GUI toolkit that connects to the Django web backend via an embedded HTTP client and WebSocket.

## Key Features

- **Tag-based UI** — Define layouts with an html-like syntax (`<panel>`, `<form>`, `<grid>`) parsed into native wxPython widgets
- **Rich component set** — Frames, notebook tabs, forms, data grids, popups, and modern/classic/tree toolbars
- **Django integration** — Embedded HTTP client + WebSocket bridge for real-time backend communication
- **Signal system** — Event-driven communication between components
- **Cross-platform** — Runs on Linux, Windows, and macOS

## Usage

Install the desktop application:

```
pip install pytigon-gui
ptigw
```

It installs `pytigon-batteries` for you, so the standard projects and the full
web-server package set are available to the embedded Django server. To serve the
same backend without the GUI, install `pytigon-batteries` instead.

For the framework overview, usage examples and full documentation, see the main
[Pytigon](https://github.com/Splawik/pytigon) project.

## Main dependencies

- Python 3.12+
- [wxPython](https://wxpython.org/) 4.x+
- [Django](https://www.djangoproject.com/) >= 6.0
- [pytigon](https://github.com/Splawik/pytigon) (base framework)
- [pytigon-batteries](https://github.com/Splawik/pytigon-batteries) (web-server package set)

## Documentation

Full documentation is available in the [`docs/`](docs/index.md) directory, covering the module architecture, API reference, and usage patterns.

## License

LGPL-2.1 © Sławomir Chołaj
