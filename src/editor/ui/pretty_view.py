import json
import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, GtkSource  # noqa: E402

from editor.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


class PrettyView(Gtk.ScrolledWindow):
    """Read-only pretty-printed JSON view using GtkSourceView."""

    def __init__(self):
        super().__init__()
        logger.debug("Initializing PrettyView")

        # Initialize GtkSource resources
        GtkSource.init()

        # Set up the source view
        self._setup_source_view()

        # Apply custom styling
        self._apply_custom_styles()

        # Follow system color scheme changes
        Adw.StyleManager.get_default().connect("notify::color-scheme", self._on_theme_changed)

    def _setup_source_view(self):
        """Configure the GtkSourceView with JSON language support."""
        # Create buffer with JSON language specification
        self.buffer = GtkSource.Buffer()
        self._setup_json_language()

        # Create the source view
        self.source_view = GtkSource.View.new_with_buffer(self.buffer)
        self.source_view.set_editable(False)
        self.source_view.set_cursor_visible(False)
        self.source_view.set_monospace(True)
        self.source_view.set_show_line_numbers(True)
        self.source_view.set_auto_indent(True)
        self.source_view.set_tab_width(4)
        self.source_view.set_indent_width(4)
        self.source_view.set_insert_spaces_instead_of_tabs(True)

        # Enable syntax highlighting
        self.source_view.set_highlight_current_line(False)

        # Set the source view as the child of the scrolled window
        self.set_child(self.source_view)

        # Set policy for scrolling
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

    def _setup_json_language(self):
        """Set up JSON language specification for syntax highlighting."""
        # Get the language manager
        language_manager = GtkSource.LanguageManager.get_default()

        # Add user language specs directory if needed
        # For system JSON spec, it should already be available
        json_language = language_manager.get_language("json")

        if json_language:
            logger.debug("JSON language specification found")
            self.buffer.set_language(json_language)
        else:
            logger.warning(
                "JSON language specification not found, syntax highlighting disabled"
            )

    def _apply_custom_styles(self):
        """Apply custom color scheme based on system theme."""
        style_manager = Adw.StyleManager.get_default()
        self._update_style_scheme(style_manager.get_color_scheme())

    def _get_scheme_name(self, color_scheme):
        """Pick light or dark scheme based on Adw.ColorScheme flags."""
        prefer_dark = color_scheme & (Adw.ColorScheme.PREFER_DARK or 0x1)
        return "json-editor-dark" if prefer_dark else "json-editor-light"

    def _update_style_scheme(self, color_scheme=None):
        """Resolve and apply the best available scheme."""
        style_scheme_manager = GtkSource.StyleSchemeManager.new()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        styles_dir = os.path.join(current_dir, "styles")
        if os.path.exists(styles_dir):
            style_scheme_manager.prepend_search_path(styles_dir)

        preferred = self._get_scheme_name(color_scheme) if color_scheme is not None else "json-editor-light"
        scheme = style_scheme_manager.get_scheme(preferred)
        if not scheme:
            fallback = "json-editor-dark" if preferred == "json-editor-light" else "json-editor-light"
            scheme = style_scheme_manager.get_scheme(fallback)
        if not scheme:
            scheme = style_scheme_manager.get_scheme("classic")
        if not scheme:
            scheme = style_scheme_manager.get_scheme("kate")

        if scheme:
            logger.debug(f"Using style scheme: {scheme.get_name()}")
            self.buffer.set_style_scheme(scheme)
        else:
            logger.warning("No suitable style scheme found")

    def _on_theme_changed(self, _manager, _pspec):
        """Re-apply editor colors when system light/dark mode changes."""
        style_manager = Adw.StyleManager.get_default()
        self._update_style_scheme(style_manager.get_color_scheme())

    def load_json(self, data, pretty=True):
        """Load JSON data into the view.

        Args:
            data: JSON string, dict, or list to display
            pretty: If True, format with indentation (default: True)
        """
        try:
            # Parse if it's a string
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data

            # Format as pretty JSON
            if pretty:
                formatted = json.dumps(parsed, indent=4, sort_keys=False)
            else:
                formatted = json.dumps(parsed)

            # Set the text in the buffer
            self.buffer.set_text(formatted)
            logger.info("JSON loaded successfully in pretty view")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            error_msg = f"Error: Invalid JSON\n\n{str(e)}"
            self.buffer.set_text(error_msg)
        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            error_msg = f"Error: Failed to load data\n\n{str(e)}"
            self.buffer.set_text(error_msg)

    def clear(self):
        """Clear the view content."""
        self.buffer.set_text("")
        logger.debug("Pretty view cleared")
