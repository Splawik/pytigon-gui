# How to Use the Pytigon GUI Documentation

Generate and serve API documentation for `pytigon_gui` using **MkDocs**
with the **Material for MkDocs** theme and **mkdocstrings**.

---

## Quick Start

```bash
cd pytigon_gui
./gen_docs.sh install    # one-time
./gen_docs.sh serve      # http://127.0.0.1:8000
./gen_docs.sh build      # static HTML → site/
```

---

## File Structure

```
pytigon_gui/
├── mkdocs.yml                    # Configuration
├── gen_docs.sh                   # Build/serve/clean/install/deploy
├── docs/
│   ├── index.md                  # Landing page
│   ├── HOWTO.md                  # This file
│   ├── getting-started/
│   │   ├── overview.md           # Architecture + tag system
│   │   └── quick-import.md       # Import cheat sheet
│   └── api/                      # 43 API reference pages
│       ├── pytigon_gui.md        # Root package
│       ├── pytigon_main.md       # Main app
│       ├── wxauto.md             # Automation
│       ├── guictrl*.md           # 16 control pages
│       ├── guiframe*.md          # 9 frame pages
│       ├── guilib*.md            # 10 library pages
│       └── toolbar*.md           # 8 toolbar pages
└── site/                         # Built output
```

---

## Commands

| Command | Description |
|---------|-------------|
| `./gen_docs.sh install` | Install mkdocs + material + mkdocstrings |
| `./gen_docs.sh build` | Generate static HTML |
| `./gen_docs.sh serve` | Live-reload dev server on :8000 |
| `./gen_docs.sh clean` | Remove site/ |
| `./gen_docs.sh deploy` | GitHub Pages deploy |

## Adding a Module

1. Create `docs/api/new_module.md` with `::: pytigon_gui.new_module`
2. Add to `mkdocs.yml` → `nav` section
3. Rebuild: `./gen_docs.sh build`

## Note

Documentation covers **all subfolders** of `pytigon_gui/`, including the
complete `guictrl/`, `guiframe/`, `guilib/`, and `toolbar/` packages.
Non-Python content (locale/ translations) is excluded.
