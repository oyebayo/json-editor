"""Unit tests for tree view selection persistence behavior."""

import unittest

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk  # noqa: E402

from editor.ui.tree_view import JsonTreePanel  # noqa: E402


class TestSelectionPersistence(unittest.TestCase):
    """Tests for selection persistence after add/duplicate/delete operations."""

    def setUp(self):
        """Create a fresh JsonTreePanel instance with test data."""
        self.panel = JsonTreePanel()
        # Test data with nested structure
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
        # Select the dict node
        self._select_node_by_path("/Root/root_key/child2")
        initial_path = self._get_selected_path()
        self.assertEqual(initial_path, "/Root/root_key/child2")

        # Add a child node
        new_path = self.panel.add_child_node("new_key", "new_value")
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # Selection should be on the newly created node
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child2/new_key")

        # Verify the new node was actually added
        self.assertIn("new_key", self.panel.json_data["root_key"]["child2"])

    def test_add_node_selects_new_node_in_list(self):
        """Test that adding to a list node selects the newly created element."""
        # Select the list node
        self._select_node_by_path("/Root/root_key/child3")
        initial_path = self._get_selected_path()
        self.assertEqual(initial_path, "/Root/root_key/child3")

        # Add a child node (key is ignored for lists)
        new_path = self.panel.add_child_node("", 4)
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # Selection should be on the newly added element
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child3[3]")

        # Verify the new item was added
        self.assertEqual(len(self.panel.json_data["root_key"]["child3"]), 4)

    def test_duplicate_node_selects_duplicate_in_dict(self):
        """Test that duplicating a dict entry selects the newly created duplicate."""
        # Select a dict entry
        self._select_node_by_path("/Root/root_key/child1")
        initial_path = self._get_selected_path()
        self.assertEqual(initial_path, "/Root/root_key/child1")

        # Duplicate the node
        new_path = self.panel.duplicate_selected_node()
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # Selection should be on the duplicate
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child1_copy")

        # Verify the duplicate was created
        self.assertIn("child1_copy", self.panel.json_data["root_key"])

    def test_duplicate_node_selects_duplicate_in_list(self):
        """Test that duplicating a list item selects the newly created duplicate."""
        # Select a list item
        self._select_node_by_path("/Root/root_key/child3[0]")
        initial_path = self._get_selected_path()
        self.assertEqual(initial_path, "/Root/root_key/child3[0]")

        # Duplicate the item
        new_path = self.panel.duplicate_selected_node()
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # Selection should be on the duplicate (inserted at index 1)
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child3[1]")

        # Verify the duplicate was inserted at index 1
        self.assertEqual(len(self.panel.json_data["root_key"]["child3"]), 4)
        self.assertEqual(self.panel.json_data["root_key"]["child3"][0], 1)
        self.assertEqual(self.panel.json_data["root_key"]["child3"][1], 1)

    def test_delete_node_selects_next_sibling_in_dict(self):
        """Test that deleting a dict entry selects the next sibling."""
        # Select a child node
        self._select_node_by_path("/Root/root_key/child1")
        initial_path = self._get_selected_path()
        self.assertEqual(initial_path, "/Root/root_key/child1")

        # Delete the node
        new_path = self.panel.remove_selected_node()
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # Selection should now be on the next sibling
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child2")

        # Verify the node was actually deleted
        self.assertNotIn("child1", self.panel.json_data["root_key"])

    def test_delete_node_selects_next_sibling_in_list(self):
        """Test that deleting a list item selects the next sibling."""
        # Select a list item
        self._select_node_by_path("/Root/root_key/child3[1]")
        initial_path = self._get_selected_path()
        self.assertEqual(initial_path, "/Root/root_key/child3[1]")

        # Delete the item
        new_path = self.panel.remove_selected_node()
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # Selection should now be on the next sibling (old [2] shifted to [1])
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child3[1]")

        # Verify the item was deleted
        self.assertEqual(len(self.panel.json_data["root_key"]["child3"]), 2)

    def test_delete_only_child_selects_parent(self):
        """Test deleting the only child selects the parent (no siblings available)."""
        # Select a nested value
        self._select_node_by_path("/Root/root_key/child2/nested")
        initial_path = self._get_selected_path()
        self.assertEqual(initial_path, "/Root/root_key/child2/nested")

        # Delete the node
        new_path = self.panel.remove_selected_node()
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # Selection should be on the immediate parent
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child2")

        # Verify the node was deleted
        self.assertNotIn("nested", self.panel.json_data["root_key"]["child2"])

    def test_delete_last_list_item_selects_previous_sibling(self):
        """Test deleting the last list item selects the previous sibling."""
        # Select the last list item [2]
        self._select_node_by_path("/Root/root_key/child3[2]")
        self.assertEqual(self._get_selected_path(), "/Root/root_key/child3[2]")

        new_path = self.panel.remove_selected_node()
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # No next sibling, should select previous ([1])
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child3[1]")

    def test_delete_last_dict_key_selects_previous_sibling(self):
        """Test deleting the last dict key selects the previous sibling."""
        # Select child3 (last key in root_key dict)
        self._select_node_by_path("/Root/root_key/child3")
        self.assertEqual(self._get_selected_path(), "/Root/root_key/child3")

        new_path = self.panel.remove_selected_node()
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # No next sibling, should select previous (child2)
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child2")

    def test_add_node_with_key_collision_selects_renamed_key(self):
        """Test that adding a node with a colliding key selects the renamed node."""
        # Pre-add a key that will collide
        self.panel.json_data["root_key"]["child2"]["new_key"] = "existing"
        self.panel.refresh_tree()

        # Select the dict node
        self._select_node_by_path("/Root/root_key/child2")

        # Add with colliding key
        new_path = self.panel.add_child_node("new_key", "new_value")
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # Should select the renamed key (new_key_1)
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child2/new_key_1")

    def test_duplicate_with_collision_selects_renamed_duplicate(self):
        """Test that duplicating with key collision selects the renamed duplicate."""
        # Pre-add a key that will collide with the default duplicate name
        self.panel.json_data["root_key"]["child1_copy"] = "existing"
        self.panel.refresh_tree()

        # Select child1
        self._select_node_by_path("/Root/root_key/child1")

        new_path = self.panel.duplicate_selected_node()
        self.assertIsNotNone(new_path)
        self.panel.select_node_by_path(new_path)

        # Should select child1_copy1 (since child1_copy already exists)
        final_path = self._get_selected_path()
        self.assertEqual(final_path, "/Root/root_key/child1_copy1")

    def test_select_node_by_path_simple_key(self):
        """Test selecting a node by simple key path."""
        success = self._select_node_by_path("/Root/root_key")
        self.assertTrue(success)
        path = self._get_selected_path()
        self.assertEqual(path, "/Root/root_key")

    def test_select_node_by_path_nested_key(self):
        """Test selecting a node by nested key path."""
        success = self._select_node_by_path("/Root/root_key/child2/nested")
        self.assertTrue(success)
        path = self._get_selected_path()
        self.assertEqual(path, "/Root/root_key/child2/nested")

    def test_select_node_by_path_array_index(self):
        """Test selecting a node by array index path."""
        success = self._select_node_by_path("/Root/root_key/child3[2]")
        self.assertTrue(success)
        path = self._get_selected_path()
        self.assertEqual(path, "/Root/root_key/child3[2]")

    def test_select_node_by_path_invalid_path(self):
        """Test selecting with invalid path returns False."""
        success = self._select_node_by_path("/nonexistent/path")
        self.assertFalse(success)

    def test_select_node_by_path_calls_scroll_to(self):
        """Test that select_node_by_path scrolls to the selected node."""
        from unittest.mock import MagicMock

        # Mock the column_view.scroll_to method
        self.panel.column_view.scroll_to = MagicMock()

        # Select a node
        success = self._select_node_by_path("/Root/root_key/child2")
        self.assertTrue(success)

        # Verify scroll_to was called with the correct position
        self.panel.column_view.scroll_to.assert_called_once()
        args = self.panel.column_view.scroll_to.call_args
        # First arg is position (int), second is None (column), third is flags
        self.assertIsInstance(args[0][0], int)
        self.assertIsNone(args[0][1])

    def test_duplicate_unique_key_generation(self):
        """Test that duplicate generates unique keys."""
        # Add a key that will conflict
        self.panel.json_data["root_key"]["child1_copy"] = "existing"

        # Select child1
        self._select_node_by_path("/Root/root_key/child1")

        # Duplicate should create child1_copy1 (since child1_copy already exists)
        new_path = self.panel.duplicate_selected_node()
        self.assertIsNotNone(new_path)

        # Verify both copies exist
        self.assertIn("child1_copy", self.panel.json_data["root_key"])
        self.assertIn("child1_copy1", self.panel.json_data["root_key"])


class TestSelectionState(unittest.TestCase):
    """Tests for get_selection_state method."""

    def setUp(self):
        """Create a fresh JsonTreePanel instance with test data."""
        self.panel = JsonTreePanel()
        self.test_data = {"key1": "value1", "key2": {"nested": "data"}}
        self.panel.load_json(self.test_data)

    def test_selection_state_root_node(self):
        """Test selection state for root node."""
        self.panel.select_node_by_path("/Root")
        state = self.panel.get_selection_state()

        self.assertTrue(state["has_selection"])
        self.assertTrue(state["is_root"])
        self.assertTrue(state["is_container"])

    def test_selection_state_dict_node(self):
        """Test selection state for a dict node."""
        self.panel.select_node_by_path("/Root/key2")
        state = self.panel.get_selection_state()

        self.assertTrue(state["has_selection"])
        self.assertFalse(state["is_root"])
        self.assertTrue(state["is_container"])

    def test_add_child_node_rejected_for_scalar(self):
        """add_child_node must return None when selected node is not dict or array."""
        # Select a scalar (string) node
        self.panel.select_node_by_path("/Root/key1")
        result = self.panel.add_child_node("new_key", "new_value")
        self.assertIsNone(result)

    def test_add_child_node_rejected_for_number(self):
        """add_child_node must return None for a number node."""
        self.panel.json_data["num"] = 42
        self.panel.refresh_tree()
        self.panel.select_node_by_path("/Root/num")
        result = self.panel.add_child_node("x", 1)
        self.assertIsNone(result)

    def test_selection_state_scalar_node(self):
        """Test selection state for a scalar node."""
        self.panel.select_node_by_path("/Root/key1")
        state = self.panel.get_selection_state()

        self.assertTrue(state["has_selection"])
        self.assertFalse(state["is_root"])
        self.assertFalse(state["is_container"])

    def test_selection_state_no_selection(self):
        """Test selection state when nothing is selected."""
        # Create a panel without data
        empty_panel = JsonTreePanel()
        state = empty_panel.get_selection_state()

        self.assertFalse(state["has_selection"])
        self.assertFalse(state["is_root"])
        self.assertFalse(state["is_container"])


if __name__ == "__main__":
    unittest.main()
