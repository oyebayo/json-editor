"""Tests for tree view context menu."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import GObject  # noqa: E402

from editor.ui.tree_view import JsonTreePanel  # noqa: E402


class TestContextMenuSetup:
    """Tests for context menu creation and signal definitions."""

    def setup_method(self):
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
        assert self.panel._ctx_actions.lookup_action("add") is not None
        assert self.panel._ctx_actions.lookup_action("duplicate") is not None
        assert self.panel._ctx_actions.lookup_action("delete") is not None

    def test_context_menu_signals_defined(self):
        """Test that context menu signals are defined on the panel."""
        signals = GObject.signal_list_names(JsonTreePanel)
        assert "context-menu-add" in signals
        assert "context-menu-duplicate" in signals
        assert "context-menu-delete" in signals

    def test_signal_emission_add(self):
        """Test that context-menu-add signal can be emitted and caught."""
        received = []
        self.panel.connect("context-menu-add", lambda w: received.append(True))
        self.panel.emit("context-menu-add")
        assert len(received) == 1

    def test_signal_emission_duplicate(self):
        """Test that context-menu-duplicate signal can be emitted and caught."""
        received = []
        self.panel.connect("context-menu-duplicate", lambda w: received.append(True))
        self.panel.emit("context-menu-duplicate")
        assert len(received) == 1

    def test_signal_emission_delete(self):
        """Test that context-menu-delete signal can be emitted and caught."""
        received = []
        self.panel.connect("context-menu-delete", lambda w: received.append(True))
        self.panel.emit("context-menu-delete")
        assert len(received) == 1


class TestContextMenuSensitivity:
    """Tests for context menu item sensitivity based on node type."""

    def setup_method(self):
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

        assert self.panel._ctx_actions.lookup_action("add").get_enabled()
        assert self.panel._ctx_actions.lookup_action("duplicate").get_enabled()
        assert self.panel._ctx_actions.lookup_action("delete").get_enabled()

    def test_sensitivity_for_list_node(self):
        """All items enabled for a list node (container, non-root)."""
        self.panel.select_node_by_path("/Root/list_node")
        state = self.panel.get_selection_state()
        is_container = state["is_container"]
        can_edit = state["has_selection"] and not state["is_root"]

        self.panel._ctx_actions.lookup_action("add").set_enabled(is_container)
        self.panel._ctx_actions.lookup_action("duplicate").set_enabled(can_edit)
        self.panel._ctx_actions.lookup_action("delete").set_enabled(can_edit)

        assert self.panel._ctx_actions.lookup_action("add").get_enabled()
        assert self.panel._ctx_actions.lookup_action("duplicate").get_enabled()
        assert self.panel._ctx_actions.lookup_action("delete").get_enabled()

    def test_sensitivity_for_scalar_node(self):
        """Add disabled for scalar nodes; Duplicate/Delete enabled."""
        self.panel.select_node_by_path("/Root/string_node")
        state = self.panel.get_selection_state()
        is_container = state["is_container"]
        can_edit = state["has_selection"] and not state["is_root"]

        self.panel._ctx_actions.lookup_action("add").set_enabled(is_container)
        self.panel._ctx_actions.lookup_action("duplicate").set_enabled(can_edit)
        self.panel._ctx_actions.lookup_action("delete").set_enabled(can_edit)

        assert not self.panel._ctx_actions.lookup_action("add").get_enabled()
        assert self.panel._ctx_actions.lookup_action("duplicate").get_enabled()
        assert self.panel._ctx_actions.lookup_action("delete").get_enabled()

    def test_sensitivity_for_root_node(self):
        """Add enabled for root (container); Duplicate/Delete disabled (root)."""
        self.panel.select_node_by_path("/Root")
        state = self.panel.get_selection_state()
        is_container = state["is_container"]
        can_edit = state["has_selection"] and not state["is_root"]

        self.panel._ctx_actions.lookup_action("add").set_enabled(is_container)
        self.panel._ctx_actions.lookup_action("duplicate").set_enabled(can_edit)
        self.panel._ctx_actions.lookup_action("delete").set_enabled(can_edit)

        assert self.panel._ctx_actions.lookup_action("add").get_enabled()
        assert not self.panel._ctx_actions.lookup_action("duplicate").get_enabled()
        assert not self.panel._ctx_actions.lookup_action("delete").get_enabled()
