"""Tests for the About dialog."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gio, Gtk  # noqa: E402

from editor.ui.dialogs import _get_app_version, show_about_dialog  # noqa: E402


class TestGetAppVersion:
    """Tests for the _get_app_version helper."""

    def test_returns_string(self):
        result = _get_app_version()
        assert isinstance(result, str)

    def test_non_empty(self):
        result = _get_app_version()
        assert len(result) > 0


class TestAboutDialog:
    """Tests for the About dialog."""

    def setup_method(self):
        self.app = Gtk.Application(
            application_id="com.test.about",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.win = Gtk.ApplicationWindow(application=self.app)

    def teardown_method(self):
        self.win.destroy()

    def test_show_about_dialog_creates_dialog(self):
        """show_about_dialog must present an AboutDialog without error."""
        show_about_dialog(self.win)

    def test_about_action_registered(self):
        """The app.about action must be usable with Gio.SimpleAction."""
        about_action = Gio.SimpleAction.new("about", None)
        activated = []
        about_action.connect("activate", lambda a, p: activated.append(True))
        self.app.add_action(about_action)

        action = self.app.lookup_action("about")
        assert action is not None
        action.activate(None)
        assert len(activated) == 1

    def test_about_dialog_comments_match_readme(self):
        """The About dialog comments should use the README's first paragraph."""
        expected = (
            "A GTK4 desktop application for GNOME that reads JSON files, "
            "displays them in a prettified format, and provides an interactive "
            "tree-view editor for making JSON-valid modifications."
        )
        dialog = Gtk.AboutDialog(comments=expected)
        assert dialog.get_comments() == expected
        dialog.destroy()
