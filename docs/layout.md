# Project Layout

```text
├── Makefile                    # Build, install, test, run targets
├── README.md                   # Brief overview and quick-start
├── setup.py                    # setuptools entry point
── .gitignore                  # Git ignore rules
├── src/
│   └── editor/                 # Main Python package
│       ├── json/               # File and URL loading, saving
│       └── ui/                 # GTK4 widgets (window, tree, inspector, etc.)
├── assets/
│   ├── json-editor.svg         # Application icon
│   ── json-editor.desktop     # Desktop entry file
├── tests/                      # Unit tests and fixtures
├── docs/
│   ├── requirements.md         # Full UI and behaviour specification
│   ├── checklist.md            # Implementation tracking checklist
│   └── layout.md               # This file
├── build/                      # Build artifacts (gitignored)
└── dist/                       # Distributable packages (gitignored)
```
