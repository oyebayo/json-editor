"""Unit tests for the header bar view toggle behavior."""

import unittest

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk  # noqa: E402

from editor.ui.header_bar import HeaderBar  # noqa: E402


class TestViewToggleBehavior(unittest.TestCase):
    """Tests for view toggle button behavior."""

    def setUp(self):
        """Create a fresh HeaderBar instance for each test."""
        self.header_bar = HeaderBar()

    def test_view_button_is_toggle_button(self):
        """Test that view_button is a Gtk.ToggleButton."""
        self.assertIsInstance(self.header_bar.view_button, Gtk.ToggleButton)

    def test_initial_icon_is_tree(self):
        """Test that initial icon is tree (view-dual-symbolic)."""
        icon_name = self.header_bar.view_icon.get_icon_name()
        self.assertEqual(icon_name, "view-dual-symbolic")

    def test_toggle_to_active_shows_eye_icon(self):
        """Test that toggling to active state shows eye icon."""
        # Simulate clicking the toggle button
        self.header_bar.view_button.set_active(True)
        icon_name = self.header_bar.view_icon.get_icon_name()
        self.assertEqual(icon_name, "view-reveal-symbolic")

    def test_toggle_to_inactive_shows_tree_icon(self):
        """Test that toggling back to inactive shows tree icon."""
        # Toggle to active first
        self.header_bar.view_button.set_active(True)
        self.assertEqual(
            self.header_bar.view_icon.get_icon_name(), "view-reveal-symbolic"
        )

        # Toggle back to inactive
        self.header_bar.view_button.set_active(False)
        icon_name = self.header_bar.view_icon.get_icon_name()
        self.assertEqual(icon_name, "view-dual-symbolic")

    def test_toggle_callback_is_connected(self):
        """Test that the toggled signal handler is connected."""
        # Verify the callback is connected by checking handler existence
        # This is a bit indirect, but we can verify by triggering the toggle
        initial_icon = self.header_bar.view_icon.get_icon_name()
        self.header_bar.view_button.set_active(True)
        new_icon = self.header_bar.view_icon.get_icon_name()
        # Icon should change, proving callback is connected
        self.assertNotEqual(initial_icon, new_icon)

    def test_multiple_toggles(self):
        """Test multiple toggle cycles work correctly."""
        # Cycle 1
        self.header_bar.view_button.set_active(True)
        self.assertEqual(
            self.header_bar.view_icon.get_icon_name(), "view-reveal-symbolic"
        )
        self.header_bar.view_button.set_active(False)
        self.assertEqual(
            self.header_bar.view_icon.get_icon_name(), "view-dual-symbolic"
        )

        # Cycle 2
        self.header_bar.view_button.set_active(True)
        self.assertEqual(
            self.header_bar.view_icon.get_icon_name(), "view-reveal-symbolic"
        )
        self.header_bar.view_button.set_active(False)
        self.assertEqual(
            self.header_bar.view_icon.get_icon_name(), "view-dual-symbolic"
        )


class TestAddButtonSensitivity(unittest.TestCase):
    """Tests for Add Node button sensitivity based on selection state."""

    def setUp(self):
        self.header_bar = HeaderBar()

    def test_add_button_disabled_when_not_container(self):
        """Add button must be disabled when selected node is not dict or array."""
        self.header_bar.update_edit_buttons(
            is_tree_mode=True,
            has_selection=True,
            is_root=False,
            is_container=False,
        )
        self.assertFalse(self.header_bar.add_button.get_sensitive())

    def test_add_button_enabled_when_container(self):
        """Add button must be enabled when selected node is dict or array."""
        self.header_bar.update_edit_buttons(
            is_tree_mode=True,
            has_selection=True,
            is_root=False,
            is_container=True,
        )
        self.assertTrue(self.header_bar.add_button.get_sensitive())

    def test_add_button_disabled_in_pretty_mode(self):
        """Add button must be disabled in pretty mode even if container."""
        self.header_bar.update_edit_buttons(
            is_tree_mode=False,
            has_selection=True,
            is_root=False,
            is_container=True,
        )
        self.assertFalse(self.header_bar.add_button.get_sensitive())

    def test_add_button_disabled_without_selection(self):
        """Add button must be disabled when nothing is selected."""
        self.header_bar.update_edit_buttons(
            is_tree_mode=True,
            has_selection=False,
            is_root=False,
            is_container=False,
        )
        self.assertFalse(self.header_bar.add_button.get_sensitive())


class TestHeaderBarStructure(unittest.TestCase):
    """Tests for header bar overall structure."""

    def setUp(self):
        """Create a fresh HeaderBar instance for each test."""
        self.header_bar = HeaderBar()

    def test_header_bar_is_gtk_header_bar(self):
        """Test that HeaderBar is a Gtk.HeaderBar."""
        self.assertIsInstance(self.header_bar, Gtk.HeaderBar)

    def test_title_widget_is_label(self):
        """Test that title widget is a Gtk.Label."""
        title_widget = self.header_bar.get_title_widget()
        self.assertIsInstance(title_widget, Gtk.Label)

    def test_default_title_is_untitled(self):
        """Test that default title is 'Untitled'."""
        title_widget = self.header_bar.get_title_widget()
        self.assertEqual(title_widget.get_text(), "Untitled")
