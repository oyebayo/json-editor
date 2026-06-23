# JSON Editor

A GTK4 desktop application for GNOME that reads JSON files, displays them in a prettified format, and provides an interactive tree-view editor for making JSON-valid modifications.

## Features

- **Pretty View**: Read-only, syntax-highlighted JSON with line numbers
- **Tree View**: Interactive editor with collapsible nodes, zoom-in/zoom-out expand icons, and a property inspector side panel
- **Edit operations**: Add, duplicate, and delete nodes via toolbar or right-click context menu
- **Selection persistence**: New nodes are auto-selected after add/duplicate; delete falls back to sibling then parent
- **Open from URL**: Fetch JSON from a URL with MIME-type validation
- **Default handler**: Optionally set as the system default for `.json` files via `xdg-mime`
- **Logging**: Four-level logging (DEBUG/INFO/WARN/ERROR) to stderr, enabled with `--debug`

For full UI and behaviour specifications, see [docs/requirements.md](docs/requirements.md).

## Build Dependencies

- Python 3.10+
- pip (usually included with Python)

System packages for GTK4:

```bash
# Debian/Ubuntu
sudo apt-get install libgtk-4-dev

# Fedora/RHEL
sudo dnf install gtk4-devel

# Arch
sudo pacman -S gtk4
```

## Build and Run

```bash
# Run from source
make run

# Install to ~/.local (default)
make install

# System-wide install
sudo make install PREFIX=/usr/local

# Run tests
make test

# Clean build artifacts
make clean
```

## Project Layout

See [docs/layout.md](docs/layout.md).

## License

See LICENSE file for details.
