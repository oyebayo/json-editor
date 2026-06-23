"""Unit tests for tree view context menu."""

import unittest

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import GObject  # noqa: E402

from editor.ui.tree_view import JsonTreePanel  # noqa: E402


class TestContextMenuSetup(unittest.TestCase):
    """Tests for context menu creation and signal definitions."""

    def setUp(self):
        self.panel = JsonTreePanel()
        self.test_data = {
            "dict_node": {"child": "value"},
            "list_node": [1, 2, 3],
            "string_node": "hello",
            "number_node": 42,
        }
        self.panel.load_json(self.test_data)

    def test_context_menu_buttons_exist(self):
        """Test that context menu actions are created."""
        self.assertIsNotNone(self.panel._ctx_actions.lookup_action("add"))
        self.assertIsNotNone(self.panel._ctx_actions.lookup_action("duplicate"))
        self.assertIsNotNone(self.panel._ctx_actions.lookup_action("delete"))

    def test_context_menu_signals_defined(self):
        """Test that context menu signals are defined on the panel."""
        signals = GObject.signal_list_names(JsonTreePanel)
        self.assertIn("context-menu-add", signals)
        self.assertIn("context-menu-duplicate", signals)
        self.assertIn("context-menu-delete", signals)

    def test_signal_emission_add(self):
        """Test that context-menu-add signal can be emitted and caught."""
        received = []
        self.panel.connect("context-menu-add", lambda w: received.append(True))
        self.panel.emit("context-menu-add")
        self.assertEqual(len(received), 1)

    def test_signal_emission_duplicate(self):
        """Test that context-menu-duplicate signal can be emitted and caught."""
        received = []
        self.panel.connect(
            "context-menu-duplicate", lambda w: received.append(True)
        )
        self.panel.emit("context-menu-duplicate")
        self.assertEqual(len(received), 1)

    def test_signal_emission_delete(self):
        """Test that context-menu-delete signal can be emitted and caught."""
        received = []
        self.panel.connect("context-menu-delete", lambda w: received.append(True))
        self.panel.emit("context-menu-delete")
        self.assertEqual(len(received), 1)


class TestContextMenuSensitivity(unittest.TestCase):
    """Tests for context menu item sensitivity based on node type."""

    def setUp(self):
        self.panel = JsonTreePanel()
        self.test_data = {
            "dict_node": {"child": "value"},
            "list_node": [1, 2, 3],
            "string_node": "hello",
            "number_node": 42,
        }
        self.panel.load_json(self.test_data)

    def test_sensitivity_for_dict_node(self):
        """All items enabled for a dict node (container, non-root)."""
        self.panel.select_node_by_path("/Root/dict_node")
        state = self.panel.get_selection_state()
        is_container = state["is_container"]
        can_edit = state["has_selection"] and not state["is_root"]

        self.panel._ctx_actions.lookup_action("add").set_enabled(is_container)
        self.panel._ctx_actions.lookup_action("duplicate").set_enabled(can_edit)
        self.panel._ctx_actions.lookup_action("delete").set_enabled(can_edit)

        self.assertTrue(self.panel._ctx_actions.lookup_action("add").get_enabled())
        self.assertTrue(self.panel._ctx_actions.lookup_action("duplicate").get_enabled())
        self.assertTrue(self.panel._ctx_actions.lookup_action("delete").get_enabled())

    def test_sensitivity_for_list_node(self):
        """All items enabled for a list node (container, non-root)."""
        self.panel.select_node_by_path("/Root/list_node")
        state = self.panel.get_selection_state()
        is_container = state["is_container"]
        can_edit = state["has_selection"] and not state["is_root"]

        self.panel._ctx_actions.lookup_action("add").set_enabled(is_container)
        self.panel._ctx_actions.lookup_action("duplicate").set_enabled(can_edit)
        self.panel._ctx_actions.lookup_action("delete").set_enabled(can_edit)

        self.assertTrue(self.panel._ctx_actions.lookup_action("add").get_enabled())
        self.assertTrue(self.panel._ctx_actions.lookup_action("duplicate").get_enabled())
        self.assertTrue(self.panel._ctx_actions.lookup_action("delete").get_enabled())

    def test_sensitivity_for_scalar_node(self):
        """Add disabled for scalar nodes; Duplicate/Delete enabled."""
        self.panel.select_node_by_path("/Root/string_node")
        state = self.panel.get_selection_state()
        is_container = state["is_container"]
        can_edit = state["has_selection"] and not state["is_root"]

        self.panel._ctx_actions.lookup_action("add").set_enabled(is_container)
        self.panel._ctx_actions.lookup_action("duplicate").set_enabled(can_edit)
        self.panel._ctx_actions.lookup_action("delete").set_enabled(can_edit)

        self.assertFalse(self.panel._ctx_actions.lookup_action("add").get_enabled())
        self.assertTrue(self.panel._ctx_actions.lookup_action("duplicate").get_enabled())
        self.assertTrue(self.panel._ctx_actions.lookup_action("delete").get_enabled())

    def test_sensitivity_for_root_node(self):
        """Add enabled for root (container); Duplicate/Delete disabled (root)."""
        self.panel.select_node_by_path("/Root")
        state = self.panel.get_selection_state()
        is_container = state["is_container"]
        can_edit = state["has_selection"] and not state["is_root"]

        self.panel._ctx_actions.lookup_action("add").set_enabled(is_container)
        self.panel._ctx_actions.lookup_action("duplicate").set_enabled(can_edit)
        self.panel._ctx_actions.lookup_action("delete").set_enabled(can_edit)

        self.assertTrue(self.panel._ctx_actions.lookup_action("add").get_enabled())
        self.assertFalse(self.panel._ctx_actions.lookup_action("duplicate").get_enabled())
        self.assertFalse(self.panel._ctx_actions.lookup_action("delete").get_enabled())


if __name__ == "__main__":
    unittest.main()
