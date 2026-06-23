import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from editor.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

APP_NAME = "JSON Editor"

# Fixed-width constants (in characters)
FIXED_WIDTH_MODE = 8
FIXED_WIDTH_NODE = 20
FIXED_WIDTH_MODIFIED = 10
FIXED_WIDTH_SIZE = 12
FIXED_WIDTH_ENCODING = 10
FIXED_WIDTH_APP = 14


class StatusBar(Gtk.Box):
    """Status bar displayed at the bottom of the application window.

    Displays different fields depending on the current view mode:
    - TreeView Mode: mode | node name | path | app name
    - Pretty Mode:   mode | modified | message | file size | encoding | app name

    Fields are separated by vertical bar characters.
    """

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        logger.debug("Initializing StatusBar")

        # Prevent vertical expansion - status bar should only be as tall as its content
        self.set_vexpand(False)
        self.set_valign(Gtk.Align.START)

        # Apply status bar styling
        self.add_css_class("toolbar")
        self.add_css_class("statusbar")

        # Current state
        self._is_tree_mode = False
        self._modified = False
        self._file_size = ""
        self._encoding = "UTF-8"
        self._message = ""
        self._node_name = ""
        self._node_path = ""

        # --- Build TreeView mode widgets ---
        self.tree_mode_label = self._make_fixed_label("Tree", FIXED_WIDTH_MODE)
        self.tree_node_label = self._make_fixed_label("", FIXED_WIDTH_NODE)
        self.tree_path_label = Gtk.Label(xalign=0.0, label="")
        self.tree_path_label.set_hexpand(True)
        self.tree_path_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self.tree_app_label = self._make_fixed_label(APP_NAME, FIXED_WIDTH_APP)

        # --- Build Pretty mode widgets ---
        self.pretty_mode_label = self._make_fixed_label("Pretty", FIXED_WIDTH_MODE)
        self.pretty_modified_label = self._make_fixed_label("", FIXED_WIDTH_MODIFIED)
        self.pretty_message_label = Gtk.Label(xalign=0.0, label="")
        self.pretty_message_label.set_hexpand(True)
        self.pretty_message_label.set_ellipsize(3)
        self.pretty_size_label = self._make_fixed_label("", FIXED_WIDTH_SIZE)
        self.pretty_encoding_label = self._make_fixed_label(
            "UTF-8", FIXED_WIDTH_ENCODING
        )
        self.pretty_app_label = self._make_fixed_label(APP_NAME, FIXED_WIDTH_APP)

        # Build both layouts (only one visible at a time)
        self._tree_box = self._build_tree_box()
        self._pretty_box = self._build_pretty_box()

        self.append(self._tree_box)
        self.append(self._pretty_box)

        # Start in Pretty mode
        self._pretty_box.set_visible(True)
        self._tree_box.set_visible(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_mode(self, is_tree: bool):
        """Switch the status bar layout to match the current view mode."""
        self._is_tree_mode = is_tree
        self._tree_box.set_visible(is_tree)
        self._pretty_box.set_visible(not is_tree)
        logger.debug(f"StatusBar mode set to {'Tree' if is_tree else 'Pretty'}")

    def set_node_info(self, name: str, path: str):
        """Update the current node name and XPath-style path (TreeView mode)."""
        self._node_name = name
        self._node_path = path
        self.tree_node_label.set_label(name)
        self.tree_path_label.set_label(path)

    def set_modified(self, modified: bool):
        """Update the modified indicator (Pretty mode)."""
        self._modified = modified
        text = "Modified" if modified else ""
        self.pretty_modified_label.set_label(text)

    def set_message(self, message: str):
        """Update the status message (Pretty mode)."""
        self._message = message
        self.pretty_message_label.set_label(message)

    def set_file_size(self, size_bytes: int):
        """Update the file size display (Pretty mode)."""
        self._file_size = self._format_size(size_bytes)
        self.pretty_size_label.set_label(self._file_size)

    def set_encoding(self, encoding: str):
        """Update the file encoding display (Pretty mode)."""
        self._encoding = encoding
        self.pretty_encoding_label.set_label(encoding)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_tree_box(self) -> Gtk.Box:
        """Build the TreeView mode status bar layout."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.set_vexpand(False)
        box.append(self.tree_mode_label)
        box.append(self._separator())
        box.append(self.tree_node_label)
        box.append(self._separator())
        box.append(self.tree_path_label)
        box.append(self._separator())
        box.append(self.tree_app_label)
        return box

    def _build_pretty_box(self) -> Gtk.Box:
        """Build the Pretty mode status bar layout."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.set_vexpand(False)
        box.append(self.pretty_mode_label)
        box.append(self._separator())
        box.append(self.pretty_modified_label)
        box.append(self._separator())
        box.append(self.pretty_message_label)
        box.append(self._separator())
        box.append(self.pretty_size_label)
        box.append(self._separator())
        box.append(self.pretty_encoding_label)
        box.append(self._separator())
        box.append(self.pretty_app_label)
        return box

    def _separator(self) -> Gtk.Label:
        """Create a vertical bar separator between fields."""
        sep = Gtk.Label(label=" | ")
        sep.add_css_class("dim-label")
        return sep

    def _make_fixed_label(self, text: str, width_chars: int) -> Gtk.Label:
        """Create a label with a fixed width in characters."""
        label = Gtk.Label(label=text, xalign=0.0)
        label.set_width_chars(width_chars)
        label.set_max_width_chars(width_chars)
        label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        return label

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format a byte count into a human-readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
