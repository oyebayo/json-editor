# Makefile for json-editor
# Python 3.10+ required

APP_NAME := json-editor
PYTHON := python3
PYTHON_MIN_VERSION := 3.10

# Installation paths
PREFIX ?= $(HOME)/.local
ifeq ($(PREFIX), /usr/local)
    BIN := /usr/local/bin
    SHARE := /usr/local/share
    INSTALL_MODE := system
else
    BIN := $(HOME)/.local/bin
    SHARE := $(HOME)/.local/share
    INSTALL_MODE := user
endif

# Specific paths
ICON_INSTALL_DIR := $(SHARE)/icons/hicolor/scalable/apps
DESKTOP_INSTALL_DIR := $(SHARE)/applications

# Virtual environment
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python3
VENV_PYTEST := $(VENV)/bin/pytest

# Source paths
SRC_DIR := src
ICON_SRC := assets/$(APP_NAME).svg
DESKTOP_SRC := assets/$(APP_NAME).desktop

# Python package name (if different from app name)
PKG_NAME := editor

.PHONY: help install uninstall clean test run build check-python check-gtk4

help:
	@echo "json-editor Makefile"
	@echo ""
	@echo "Usage: make [target] [PREFIX=/path]"
	@echo ""
	@echo "Targets:"
	@echo "  install      - Install json-editor to user or system location"
	@echo "  uninstall    - Remove json-editor and all installed files"
	@echo "  test         - Run tests"
	@echo "  build        - Lint and build the package"
	@echo "  run          - Run json-editor from source"
	@echo "  clean        - Remove build artifacts"
	@echo "  help         - Show this help"
	@echo ""
	@echo "Variables:"
	@echo "  PREFIX=$(PREFIX)          - Installation prefix (current: $(INSTALL_MODE) mode)"
	@echo ""
	@echo "Examples:"
	@echo "  make install              # Install to ~/.local"
	@echo "  sudo make install PREFIX=/usr/local  # System-wide install"
	@echo "  make uninstall            # Remove user installation"
	@echo "  sudo make uninstall PREFIX=/usr/local # Remove system installation"

check-python:
	@echo "Checking Python version..."
	@command -v $(PYTHON) >/dev/null 2>&1 || { \
	    echo "Error: $(PYTHON) not found"; \
	    exit 1; \
	}
	@$(PYTHON) -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" || { \
	    echo "Error: Python 3.10+ is required"; \
	    echo "Current version: $$($(PYTHON) --version)"; \
	    exit 1; \
	}
	@echo "✓ Python version OK"

check-gtk4:
	@echo "Checking GTK4 development files..."
	@command -v pkg-config >/dev/null 2>&1 || { \
	    echo "Error: pkg-config not found"; \
	    echo "Install with: sudo apt-get install pkg-config (Debian/Ubuntu)"; \
	    exit 1; \
	}
	@pkg-config --exists gtk4 || { \
	    echo "Error: GTK4 development files not found"; \
	    echo "Install with:"; \
	    echo "  Debian/Ubuntu: sudo apt-get install libgtk-4-dev"; \
	    echo "  Fedora/RHEL:   sudo dnf install gtk4-devel"; \
	    echo "  Arch:          sudo pacman -S gtk4"; \
	    exit 1; \
	}
	@echo "✓ GTK4 development files found"

run: check-python check-gtk4
	@echo "Running json-editor from source..."
	@cd $(SRC_DIR) && $(PYTHON) -m editor.main ../tests/test.json

install: check-python check-gtk4
	@echo "Installing json-editor ($(INSTALL_MODE) mode)..."

	# Create directories
	@mkdir -p $(ICON_INSTALL_DIR)
	@mkdir -p $(DESKTOP_INSTALL_DIR)

	# Install Python package using pip (creates executable via entry_points)
	$(PYTHON) -m pip install --$(INSTALL_MODE) --break-system-packages .

	# Install icon
	@if [ -f $(ICON_SRC) ]; then \
	    echo "Installing icon..."; \
	    cp $(ICON_SRC) $(ICON_INSTALL_DIR)/; \
	else \
	    echo "Warning: $(ICON_SRC) not found"; \
	fi

	# Install and configure desktop entry
	@if [ -f $(DESKTOP_SRC) ]; then \
	    echo "Installing desktop entry..."; \
	    cp $(DESKTOP_SRC) $(DESKTOP_INSTALL_DIR)/; \
	    echo "Configuring desktop entry..."; \
	    sed -i 's|^Exec=.*|Exec=$(BIN)/$(APP_NAME) %F|' $(DESKTOP_INSTALL_DIR)/$(APP_NAME).desktop; \
	else \
	    echo "Warning: $(DESKTOP_SRC) not found"; \
	fi

	# Update desktop database
	@echo "Updating desktop database..."; \
	update-desktop-database $(DESKTOP_INSTALL_DIR) 2>/dev/null || true

	@echo "✓ Installation complete!"
	@echo ""
	@echo "You can now run: $(APP_NAME)"
	@echo "Desktop entry installed in $(DESKTOP_INSTALL_DIR)"

uninstall: check-python
	@echo "Uninstalling json-editor..."

	# Uninstall Python package (removes executable created by entry_points)
	-$(PYTHON) -m pip uninstall --break-system-packages -y $(PKG_NAME) 2>/dev/null || \
	$(PYTHON) -m pip uninstall --break-system-packages -y $(APP_NAME) 2>/dev/null || \
	echo "Package not found in pip"

	# Remove icon
	@if [ -f $(ICON_INSTALL_DIR)/$(APP_NAME).svg ]; then \
	    echo "Removing icon..."; \
	    rm -f $(ICON_INSTALL_DIR)/$(APP_NAME).svg; \
	fi

	# Remove desktop entry
	@if [ -f $(DESKTOP_INSTALL_DIR)/$(APP_NAME).desktop ]; then \
	    echo "Removing desktop entry..."; \
	    rm -f $(DESKTOP_INSTALL_DIR)/$(APP_NAME).desktop; \
	fi

	# Update desktop database
	@echo "Updating desktop database..."; \
	update-desktop-database $(DESKTOP_INSTALL_DIR) 2>/dev/null || true

	@echo "✓ Uninstallation complete"

test: check-python $(VENV_PYTEST)
	@echo "Running tests..."
	@PYTHONPATH=$(SRC_DIR) $(VENV_PYTEST) tests/ -v

build: check-python $(VENV_PYTEST)
	@echo "Linting..."
	@$(VENV_PYTHON) -m flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	@$(VENV_PYTHON) -m flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics
	@echo "Building..."
	@$(VENV_PYTHON) -m pip install --quiet build
	@$(VENV_PYTHON) -m build
	@echo "✓ Build complete"

$(VENV_PYTEST):
	@echo "Creating virtual environment and installing dependencies..."
	@$(PYTHON) -m venv $(VENV) --system-site-packages
	@$(VENV_PYTHON) -m pip install -r requirements.txt

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/
	@rm -rf dist/
	@find . -type d -name "*.egg-info" -delete 2>/dev/null || true
	@rm -rf __pycache__
	@rm -rf */__pycache__
	@rm -rf src/*/__pycache__ 2>/dev/null || true
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@rm -rf $(VENV)
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete 2>/dev/null || true
	@echo "✓ Clean complete"

# Install with specific prefix (convenience targets)
install-system:
	@echo "Installing system-wide (requires sudo)..."
	sudo make install PREFIX=/usr/local

uninstall-system:
	@echo "Removing system-wide installation (requires sudo)..."
	sudo make uninstall PREFIX=/usr/local
