"""Tests for tree view selection persistence behavior."""

from unittest.mock import MagicMock

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk  # noqa: E402

from editor.ui.tree_view import JsonTreePanel  # noqa: E402


class TestSelectionPersistence:
    """Tests for selection persistence after add/duplicate/delete operations."""

    def setup_method(self):
        """Create a fresh JsonTreePanel instance with test data."""
        self.panel = JsonTreePanel()
        self.test_data = {
            "root_key": {
                "child1": "value1",
                "child2": {"nested": "data"},
                "child3": [1, 2, 3],
            },
            "another_key": "simple_value",
        }
        self.panel.load_json(self.test_data)

    def _select_node_by_path(self, target_path: str) -> bool:
        """Helper to select a node by its XPath."""
        return self.panel.select_node_by_path(target_path)

    def _get_selected_path(self) -> str:
        """Helper to get the XPath of the currently selected node."""
        _, path = self.panel.get_selected_node_info()
        return path

    def test_add_node_selects_new_node_in_dict(self):
        """Test that adding a child to a dict node selects the newly created node."""
        self._select_node_by_path("/Root/root_key/child2")
        initial_path = self._get_selected_path()
        assert initial_path == "/Root/root_key/child2"

        new_path = self.panel.add_child_node("new_key", "new_value")
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child2/new_key"

        assert "new_key" in self.panel.json_data["root_key"]["child2"]

    def test_add_node_selects_new_node_in_list(self):
        """Test that adding to a list node selects the newly created element."""
        self._select_node_by_path("/Root/root_key/child3")
        initial_path = self._get_selected_path()
        assert initial_path == "/Root/root_key/child3"

        new_path = self.panel.add_child_node("", 4)
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child3[3]"

        assert len(self.panel.json_data["root_key"]["child3"]) == 4

    def test_duplicate_node_selects_duplicate_in_dict(self):
        """Test that duplicating a dict entry selects the newly created duplicate."""
        self._select_node_by_path("/Root/root_key/child1")
        initial_path = self._get_selected_path()
        assert initial_path == "/Root/root_key/child1"

        new_path = self.panel.duplicate_selected_node()
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child1_copy"

        assert "child1_copy" in self.panel.json_data["root_key"]

    def test_duplicate_node_selects_duplicate_in_list(self):
        """Test that duplicating a list item selects the newly created duplicate."""
        self._select_node_by_path("/Root/root_key/child3[0]")
        initial_path = self._get_selected_path()
        assert initial_path == "/Root/root_key/child3[0]"

        new_path = self.panel.duplicate_selected_node()
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child3[1]"

        assert len(self.panel.json_data["root_key"]["child3"]) == 4
        assert self.panel.json_data["root_key"]["child3"][0] == 1
        assert self.panel.json_data["root_key"]["child3"][1] == 1

    def test_delete_node_selects_next_sibling_in_dict(self):
        """Test that deleting a dict entry selects the next sibling."""
        self._select_node_by_path("/Root/root_key/child1")
        initial_path = self._get_selected_path()
        assert initial_path == "/Root/root_key/child1"

        new_path = self.panel.remove_selected_node()
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child2"

        assert "child1" not in self.panel.json_data["root_key"]

    def test_delete_node_selects_next_sibling_in_list(self):
        """Test that deleting a list item selects the next sibling."""
        self._select_node_by_path("/Root/root_key/child3[1]")
        initial_path = self._get_selected_path()
        assert initial_path == "/Root/root_key/child3[1]"

        new_path = self.panel.remove_selected_node()
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child3[1]"

        assert len(self.panel.json_data["root_key"]["child3"]) == 2

    def test_delete_only_child_selects_parent(self):
        """Test deleting the only child selects the parent (no siblings available)."""
        self._select_node_by_path("/Root/root_key/child2/nested")
        initial_path = self._get_selected_path()
        assert initial_path == "/Root/root_key/child2/nested"

        new_path = self.panel.remove_selected_node()
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child2"

        assert "nested" not in self.panel.json_data["root_key"]["child2"]

    def test_delete_last_list_item_selects_previous_sibling(self):
        """Test deleting the last list item selects the previous sibling."""
        self._select_node_by_path("/Root/root_key/child3[2]")
        assert self._get_selected_path() == "/Root/root_key/child3[2]"

        new_path = self.panel.remove_selected_node()
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child3[1]"

    def test_delete_last_dict_key_selects_previous_sibling(self):
        """Test deleting the last dict key selects the previous sibling."""
        self._select_node_by_path("/Root/root_key/child3")
        assert self._get_selected_path() == "/Root/root_key/child3"

        new_path = self.panel.remove_selected_node()
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child2"

    def test_add_node_with_key_collision_selects_renamed_key(self):
        """Test that adding a node with a colliding key selects the renamed node."""
        self.panel.json_data["root_key"]["child2"]["new_key"] = "existing"
        self.panel.refresh_tree()

        self._select_node_by_path("/Root/root_key/child2")

        new_path = self.panel.add_child_node("new_key", "new_value")
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child2/new_key_1"

    def test_duplicate_with_collision_selects_renamed_duplicate(self):
        """Test that duplicating with key collision selects the renamed duplicate."""
        self.panel.json_data["root_key"]["child1_copy"] = "existing"
        self.panel.refresh_tree()

        self._select_node_by_path("/Root/root_key/child1")

        new_path = self.panel.duplicate_selected_node()
        assert new_path is not None
        self.panel.select_node_by_path(new_path)

        final_path = self._get_selected_path()
        assert final_path == "/Root/root_key/child1_copy1"

    def test_select_node_by_path_simple_key(self):
        """Test selecting a node by simple key path."""
        success = self._select_node_by_path("/Root/root_key")
        assert success
        path = self._get_selected_path()
        assert path == "/Root/root_key"

    def test_select_node_by_path_nested_key(self):
        """Test selecting a node by nested key path."""
        success = self._select_node_by_path("/Root/root_key/child2/nested")
        assert success
        path = self._get_selected_path()
        assert path == "/Root/root_key/child2/nested"

    def test_select_node_by_path_array_index(self):
        """Test selecting a node by array index path."""
        success = self._select_node_by_path("/Root/root_key/child3[2]")
        assert success
        path = self._get_selected_path()
        assert path == "/Root/root_key/child3[2]"

    def test_select_node_by_path_invalid_path(self):
        """Test selecting with invalid path returns False."""
        success = self._select_node_by_path("/nonexistent/path")
        assert not success

    def test_select_node_by_path_calls_scroll_to(self):
        """Test that select_node_by_path scrolls to the selected node."""
        self.panel.column_view.scroll_to = MagicMock()

        success = self._select_node_by_path("/Root/root_key/child2")
        assert success

        self.panel.column_view.scroll_to.assert_called_once()
        args = self.panel.column_view.scroll_to.call_args
        assert isinstance(args[0][0], int)
        assert args[0][1] is None

    def test_duplicate_unique_key_generation(self):
        """Test that duplicate generates unique keys."""
        self.panel.json_data["root_key"]["child1_copy"] = "existing"

        self._select_node_by_path("/Root/root_key/child1")

        new_path = self.panel.duplicate_selected_node()
        assert new_path is not None

        assert "child1_copy" in self.panel.json_data["root_key"]
        assert "child1_copy1" in self.panel.json_data["root_key"]


class TestSelectionState:
    """Tests for get_selection_state method."""

    def setup_method(self):
        """Create a fresh JsonTreePanel instance with test data."""
        self.panel = JsonTreePanel()
        self.test_data = {"key1": "value1", "key2": {"nested": "data"}}
        self.panel.load_json(self.test_data)

    def test_selection_state_root_node(self):
        """Test selection state for root node."""
        self.panel.select_node_by_path("/Root")
        state = self.panel.get_selection_state()

        assert state["has_selection"]
        assert state["is_root"]
        assert state["is_container"]

    def test_selection_state_dict_node(self):
        """Test selection state for a dict node."""
        self.panel.select_node_by_path("/Root/key2")
        state = self.panel.get_selection_state()

        assert state["has_selection"]
        assert not state["is_root"]
        assert state["is_container"]

    def test_add_child_node_rejected_for_scalar(self):
        """add_child_node must return None when selected node is not dict or array."""
        self.panel.select_node_by_path("/Root/key1")
        result = self.panel.add_child_node("new_key", "new_value")
        assert result is None

    def test_add_child_node_rejected_for_number(self):
        """add_child_node must return None for a number node."""
        self.panel.json_data["num"] = 42
        self.panel.refresh_tree()
        self.panel.select_node_by_path("/Root/num")
        result = self.panel.add_child_node("x", 1)
        assert result is None

    def test_selection_state_scalar_node(self):
        """Test selection state for a scalar node."""
        self.panel.select_node_by_path("/Root/key1")
        state = self.panel.get_selection_state()

        assert state["has_selection"]
        assert not state["is_root"]
        assert not state["is_container"]

    def test_selection_state_no_selection(self):
        """Test selection state when nothing is selected."""
        empty_panel = JsonTreePanel()
        state = empty_panel.get_selection_state()

        assert not state["has_selection"]
        assert not state["is_root"]
        assert not state["is_container"]
