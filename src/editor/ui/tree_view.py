import copy
import json
import os
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gdk, Gio, GObject, Gtk  # noqa: E402

from editor.logger import get_logger  # noqa: E402
from editor.ui.property_inspector import PropertyInspector  # noqa: E402

logger = get_logger(__name__)


def _load_tree_css():
    """Load custom CSS for tree expander icons and indentation."""
    css_path = os.path.join(os.path.dirname(__file__), "styles", "tree-view.css")
    if os.path.exists(css_path):
        provider = Gtk.CssProvider()
        try:
            provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
            logger.info(f"Loaded tree view CSS from {css_path}")
        except Exception as e:
            logger.error(f"Failed to load tree view CSS: {e}")
    else:
        logger.warning(f"Tree view CSS file not found: {css_path}")


class JsonTreeNode(GObject.Object):
    """Represents a node in the JSON tree structure."""

    __gtype_name__ = "JsonTreeNode"

    def __init__(self, key: str, value: Any, children: list = None):
        super().__init__()
        self.key = key
        self.value = value
        self.children_data = children or []

    def get_children(self):
        """Return children for tree model."""
        if isinstance(self.value, dict):
            return [JsonTreeNode(k, v) for k, v in self.value.items()]
        elif isinstance(self.value, list):
            return [JsonTreeNode(f"[{i}]", item) for i, item in enumerate(self.value)]
        return []


class JsonTreeExpander(Gtk.Box):
    """Custom tree expander with zoom icons right before node name.

    Uses zoom-in-symbolic for collapsed and zoom-out-symbolic for expanded.
    Icons are hidden for leaf nodes (scalars, empty containers).
    Indentation is applied manually per depth level.
    """

    INDENT_PER_LEVEL = 24  # pixels

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        # Hidden TreeExpander for model binding (no built-in arrow, no auto-indent)
        self._tree_expander = Gtk.TreeExpander()
        self._tree_expander.set_hide_expander(True)
        self._tree_expander.set_indent_for_depth(False)

        # Icon (zoom-in = collapsed, zoom-out = expanded)
        self._icon = Gtk.Image.new_from_icon_name("zoom-in-symbolic")
        self._icon.set_cursor_from_name("pointer")
        click = Gtk.GestureClick()
        click.connect("pressed", self._on_icon_clicked)
        self._icon.add_controller(click)

        # Label
        self._label = Gtk.Label(xalign=0)
        self._label.set_ellipsize(3)

        # Content box: icon + label (right next to each other)
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        content.append(self._icon)
        content.append(self._label)

        self._tree_expander.set_child(content)
        self.append(self._tree_expander)

    def _on_icon_clicked(self, gesture, n_press, x, y):
        """Toggle expand state when icon is clicked."""
        row = self._tree_expander.get_list_row()
        if row is not None:
            row.set_expanded(not row.get_expanded())

    def set_list_row(self, tree_row):
        """Set the TreeListRow and configure icon/indentation."""
        self._tree_expander.set_list_row(tree_row)
        self._tree_row = tree_row  # For context menu hit testing
        if tree_row is not None:
            # Manual indentation based on depth
            depth = tree_row.get_depth()
            self.set_margin_start(depth * self.INDENT_PER_LEVEL)

            # Hide icon for leaf nodes (scalars, empty containers)
            node = tree_row.get_item()
            has_children = isinstance(node.value, (dict, list)) and len(node.value) > 0
            self._icon.set_visible(has_children)

            # Set initial icon state
            if tree_row.get_expanded():
                self._icon.set_from_icon_name("zoom-out-symbolic")
            else:
                self._icon.set_from_icon_name("zoom-in-symbolic")

            # Listen for expand state changes
            tree_row.connect("notify::expanded", self._on_row_expanded_changed)

    def _on_row_expanded_changed(self, row, _pspec):
        """Update icon when row expand state changes."""
        if row.get_expanded():
            self._icon.set_from_icon_name("zoom-out-symbolic")
        else:
            self._icon.set_from_icon_name("zoom-in-symbolic")

    def set_label(self, text):
        """Set the node name label."""
        self._label.set_label(text)


class JsonTreePanel(Gtk.Box):
    """Interactive tree view panel for editing JSON structure."""

    __gsignals__ = {
        "context-menu-add": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "context-menu-duplicate": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "context-menu-delete": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        logger.debug("Initializing TreeView panel")

        self.json_data = None
        self.tree_model = None
        self.selection_model = None

        # Load custom CSS for tree expander icons
        _load_tree_css()

        # Set up the tree view and inspector
        self._setup_tree_view()

    def _setup_tree_view(self):
        """Initialize the column view for tree display."""
        # Create column view
        self.column_view = Gtk.ColumnView()
        self.column_view.set_show_row_separators(True)
        self.column_view.set_show_column_separators(True)
        self.column_view.set_hexpand(True)

        # Set up Key column
        key_factory = Gtk.SignalListItemFactory()
        key_factory.connect("setup", self._on_key_setup)
        key_factory.connect("bind", self._on_key_bind)

        key_column = Gtk.ColumnViewColumn.new("Key", key_factory)
        key_column.set_expand(True)
        key_column.set_resizable(True)
        self.column_view.append_column(key_column)

        # Set up Value column
        value_factory = Gtk.SignalListItemFactory()
        value_factory.connect("setup", self._on_value_setup)
        value_factory.connect("bind", self._on_value_bind)

        value_column = Gtk.ColumnViewColumn.new("Value", value_factory)
        value_column.set_expand(True)
        value_column.set_resizable(True)
        self.column_view.append_column(value_column)

        # Tree in scrolled window (left side)
        tree_scrolled = Gtk.ScrolledWindow()
        tree_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        tree_scrolled.set_child(self.column_view)
        tree_scrolled.set_hexpand(True)
        self.append(tree_scrolled)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.append(separator)

        # Property Inspector (right side, fixed width)
        self.inspector = PropertyInspector()
        self.append(self.inspector)

        # Context menu
        self._setup_context_menu()

    def _setup_context_menu(self):
        """Set up right-click context menu for the tree view."""
        # Create actions for menu items
        self._ctx_actions = Gio.SimpleActionGroup()
        for name in ("add", "duplicate", "delete"):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda a, p, n=name: self._fire_ctx(n))
            self._ctx_actions.add_action(action)
        self.column_view.insert_action_group("ctx", self._ctx_actions)

        # Build menu model
        menu = Gio.Menu()
        menu.append("Add Node", "ctx.add")
        menu.append("Duplicate", "ctx.duplicate")
        menu.append("Delete", "ctx.delete")

        # Create popover menu from model
        self._ctx_popover = Gtk.PopoverMenu.new_from_model(menu)
        self._ctx_popover.set_has_arrow(False)
        self._ctx_popover.set_parent(self.column_view)

        gesture = Gtk.GestureClick()
        gesture.set_button(3)  # Secondary (right) button
        gesture.connect("pressed", self._on_ctx_click)
        self.column_view.add_controller(gesture)

    def _fire_ctx(self, action):
        """Emit the corresponding context menu signal."""
        self._ctx_popover.hide()
        if action == "add":
            self.emit("context-menu-add")
        elif action == "duplicate":
            self.emit("context-menu-duplicate")
        elif action == "delete":
            self.emit("context-menu-delete")

    def _on_ctx_click(self, gesture, n_press, x, y):
        """Handle right-click on the column view."""
        if self.selection_model is None or self.tree_model is None:
            gesture.set_state(Gtk.EventSequenceState.DENIED)
            return

        # Pick the widget at the click position and walk up the parent
        # chain to find the TreeListRow stored during bind.
        picked = self.column_view.pick(x, y, Gtk.PickFlags.DEFAULT)
        if picked is None:
            gesture.set_state(Gtk.EventSequenceState.DENIED)
            return

        tree_row = None
        widget = picked
        while widget is not None:
            tree_row = getattr(widget, "_tree_row", None)
            if tree_row is not None:
                break
            widget = widget.get_parent()

        if tree_row is None:
            gesture.set_state(Gtk.EventSequenceState.DENIED)
            return

        # Find position of this TreeListRow in the selection model
        n_items = self.selection_model.get_n_items()
        pos = Gtk.INVALID_LIST_POSITION
        for i in range(n_items):
            if self.selection_model.get_item(i) is tree_row:
                pos = i
                break

        if pos == Gtk.INVALID_LIST_POSITION:
            gesture.set_state(Gtk.EventSequenceState.DENIED)
            return

        self.selection_model.set_selected(pos)

        # Update action sensitivity
        state = self.get_selection_state()
        is_container = state["is_container"]
        can_edit = state["has_selection"] and not state["is_root"]

        self._ctx_actions.lookup_action("add").set_enabled(is_container)
        self._ctx_actions.lookup_action("duplicate").set_enabled(can_edit)
        self._ctx_actions.lookup_action("delete").set_enabled(can_edit)

        # Position popover at click coordinates
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        self._ctx_popover.set_pointing_to(rect)
        self._ctx_popover.popup()

    def _on_key_setup(self, factory, list_item):
        """Set up the key column cell with tree expander."""
        expander = JsonTreeExpander()
        list_item.set_child(expander)

    def _on_key_bind(self, factory, list_item):
        """Bind data to key column cell."""
        expander = list_item.get_child()
        tree_row = list_item.get_item()
        node = tree_row.get_item()

        expander.set_list_row(tree_row)
        expander.set_label(str(node.key))

    def _on_value_setup(self, factory, list_item):
        """Set up the value column cell."""
        label = Gtk.Label(xalign=0)
        label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        list_item.set_child(label)

    def _on_value_bind(self, factory, list_item):
        """Bind data to value column cell."""
        label = list_item.get_child()
        tree_row = list_item.get_item()
        node = tree_row.get_item()

        # Format value for display
        value = node.value
        if isinstance(value, dict):
            label.set_label(f"{{{len(value)} keys}}")
            label.add_css_class("dim-label")
        elif isinstance(value, list):
            label.set_label(f"[{len(value)} items]")
            label.add_css_class("dim-label")
        else:
            label.set_label(str(value))
            label.remove_css_class("dim-label")
        label._tree_row = tree_row

    def load_json(self, data):
        """Load JSON data into the tree view.

        Args:
            data: JSON string, dict, or list
        """
        try:
            # Parse if string
            if isinstance(data, str):
                self.json_data = json.loads(data)
            else:
                self.json_data = data

            # Create root node
            root_node = JsonTreeNode("Root", self.json_data)

            # Create tree model
            root_store = Gio.ListStore.new(JsonTreeNode)
            root_store.append(root_node)

            self.tree_model = Gtk.TreeListModel.new(
                root_store,
                passthrough=False,
                autoexpand=True,
                create_func=self._create_model_func,
            )

            # Create selection model
            self.selection_model = Gtk.SingleSelection.new(self.tree_model)
            self.column_view.set_model(self.selection_model)

            logger.info("JSON loaded successfully in tree view")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            self.json_data = None
        except Exception as e:
            logger.error(f"Failed to load JSON into tree: {e}")
            self.json_data = None

    def _create_model_func(self, node, *args):
        """Create child model for tree expansion."""
        children = node.get_children()
        if children:
            store = Gio.ListStore.new(JsonTreeNode)
            for child in children:
                store.append(child)
            return store
        return None

    def get_json_data(self):
        """Return the current JSON data."""
        return self.json_data

    def get_selected_node_info(self):
        """Return (node_name, xpath) for the currently selected tree node.

        Returns:
            Tuple of (name: str, path: str) or ("", "/") if nothing is selected.
        """
        if self.selection_model is None:
            return ("", "/")

        pos = self.selection_model.get_selected()
        if pos == Gtk.INVALID_LIST_POSITION:
            return ("", "/")

        tree_row = self.selection_model.get_item(pos)
        if tree_row is None:
            return ("", "/")

        node = tree_row.get_item()
        if node is None:
            return ("", "/")

        name = str(node.key)
        path = self._build_xpath(tree_row)
        return (name, path)

    def _build_xpath(self, tree_row) -> str:
        """Build a JSON XPath-style path by walking up the tree rows."""
        segments = []
        row = tree_row
        while row is not None:
            node = row.get_item()
            if node is not None:
                key = node.key
                # Array indices like [0] are already bracketed
                if key.startswith("[") and key.endswith("]"):
                    segments.append(key)
                else:
                    segments.append(f"/{key}")
            row = row.get_parent()

        segments.reverse()
        path = "".join(segments)
        if not path.startswith("/"):
            path = "/" + path
        return path

    def get_selected_node_data(self):
        """Return (node, parent_container, key) for the selected node.

        Returns:
            Tuple of (JsonTreeNode, parent_dict_or_list, key_or_index) or None.
        """
        if self.selection_model is None:
            return None

        pos = self.selection_model.get_selected()
        if pos == Gtk.INVALID_LIST_POSITION:
            return None

        tree_row = self.selection_model.get_item(pos)
        if tree_row is None:
            return None

        node = tree_row.get_item()
        if node is None:
            return None

        # Build path from root to this node by walking up
        path_keys = []
        row = tree_row
        while row is not None:
            n = row.get_item()
            if n is not None:
                path_keys.append(n.key)
            row = row.get_parent()

        path_keys.reverse()

        # path_keys[0] is "Root" wrapping json_data
        if len(path_keys) <= 1:
            return (node, None, None)

        # Navigate to parent container
        current = self.json_data
        for key in path_keys[1:-1]:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list):
                current = current[int(key.strip("[]"))]

        last_key = path_keys[-1]
        if isinstance(current, list):
            return (node, current, int(last_key.strip("[]")))
        return (node, current, last_key)

    def get_selection_state(self) -> dict:
        """Return state info about the current selection for button sensitivity.

        Returns:
            Dict with keys: has_selection, is_root, is_container.
        """
        data = self.get_selected_node_data()
        if data is None:
            return {"has_selection": False, "is_root": False, "is_container": False}

        node, parent_container, key = data
        is_root = parent_container is None
        is_container = isinstance(node.value, (dict, list))
        return {
            "has_selection": True,
            "is_root": is_root,
            "is_container": is_container,
        }

    def add_child_node(self, key: str, value: Any) -> str | None:
        """Add a child node to the currently selected node.

        Args:
            key: Key name (used if selected node is a dict).
            value: Value to add.

        Returns:
            XPath of the new node, or None on failure.
        """
        data = self.get_selected_node_data()
        if data is None:
            return None

        node, _parent, _key = data
        target = node.value

        if isinstance(target, dict):
            if not key:
                return None
            # Ensure unique key
            base_key = key
            counter = 1
            while key in target:
                key = f"{base_key}_{counter}"
                counter += 1
            target[key] = value
            _, parent_path = self.get_selected_node_info()
            new_node_path = f"{parent_path}/{key}"
        elif isinstance(target, list):
            new_index = len(target)
            target.append(value)
            _, parent_path = self.get_selected_node_info()
            new_node_path = f"{parent_path}[{new_index}]"
        else:
            return None

        logger.info(f"Added child node to '{node.key}'")

        self.refresh_tree()
        return new_node_path

    def duplicate_selected_node(self) -> str | None:
        """Duplicate the currently selected node as a sibling.

        Returns:
            XPath of the new duplicate, or None on failure.
        """
        data = self.get_selected_node_data()
        if data is None:
            return None

        node, parent_container, key = data
        if parent_container is None:
            # Can't duplicate root
            return None

        value_copy = copy.deepcopy(node.value)

        if isinstance(parent_container, dict):
            if not isinstance(key, str):
                return None
            new_key = f"{node.key}_copy"
            counter = 1
            while new_key in parent_container:
                new_key = f"{node.key}_copy{counter}"
                counter += 1
            parent_container[new_key] = value_copy
            logger.info(f"Duplicated node '{node.key}' as '{new_key}'")
            _, current_path = self.get_selected_node_info()
            sibling_path = self._get_parent_path(current_path)
            new_node_path = f"{sibling_path}/{new_key}"
        elif isinstance(parent_container, list):
            if not isinstance(key, int):
                return None
            insert_pos = key + 1
            parent_container.insert(insert_pos, value_copy)
            logger.info(f"Duplicated node at index {key} to index {insert_pos}")
            _, current_path = self.get_selected_node_info()
            sibling_path = self._get_parent_path(current_path)
            new_node_path = f"{sibling_path}[{insert_pos}]"
        else:
            return None

        self.refresh_tree()
        return new_node_path

    def remove_selected_node(self) -> str | None:
        """Remove the currently selected node from its parent.

        Returns:
            XPath of the selected node after deletion, or None on failure.
        """
        data = self.get_selected_node_data()
        if data is None:
            return None

        node, parent_container, key = data
        if parent_container is None:
            # Can't remove root
            return None

        # Build parent path before removal
        _, current_path = self.get_selected_node_info()
        parent_path = self._get_parent_path(current_path)

        # Compute fallback selection: nearest sibling, then parent
        fallback_path = None
        if isinstance(parent_container, dict):
            if not isinstance(key, str):
                return None
            keys = list(parent_container.keys())
            try:
                idx = keys.index(key)
                if idx + 1 < len(keys):
                    fallback_path = f"{parent_path}/{keys[idx + 1]}"
                elif idx > 0:
                    fallback_path = f"{parent_path}/{keys[idx - 1]}"
            except ValueError:
                pass
            del parent_container[key]
            logger.info(f"Removed node '{node.key}'")
        elif isinstance(parent_container, list):
            if not isinstance(key, int):
                return None
            del parent_container[key]
            # Compute after deletion so indices reflect current state
            if key < len(parent_container):
                fallback_path = f"{parent_path}[{key}]"
            elif key > 0:
                fallback_path = f"{parent_path}[{key - 1}]"
            logger.info(f"Removed node at index {key}")
        else:
            return None

        self.refresh_tree()

        # Return the path that should be selected (sibling first, then parent)
        if fallback_path:
            return fallback_path
        return parent_path

    def _get_parent_path(self, path: str) -> str:
        """Get the parent path from a given path.

        Args:
            path: The current path (e.g., "/Root/key1/child1" or "/Root/arr[0]")

        Returns:
            The parent path (e.g., "/Root/key1" or "/Root/arr")
        """
        if not path or path == "/Root":
            return ""

        # Remove trailing slash if present
        path = path.rstrip("/")

        # Handle array index suffix like "child3[1]"
        # The parent of child3[1] is child3
        if path.endswith("]"):
            bracket_start = path.rfind("[")
            if bracket_start > 0:
                return path[:bracket_start]

        # For regular keys, find the last "/" and return everything before it
        last_slash = path.rfind("/")
        if last_slash <= 0:
            return "/Root"

        return path[:last_slash]

    def refresh_tree(self):
        """Reload tree model from current json_data."""
        if self.json_data is not None:
            self.load_json(self.json_data)

    def has_data(self) -> bool:
        """Return True if JSON data is loaded."""
        return self.json_data is not None

    def select_node_by_path(self, target_path: str) -> bool:
        """Find and select the node matching the given XPath.

        Args:
            target_path: XPath string to find (e.g., "/Root/key1/[0]")

        Returns:
            True if the node was found and selected.
        """
        if self.selection_model is None or not target_path:
            return False
        if self.tree_model is None:
            return False

        # Iterate through all items in the flat tree model and find the matching path
        n_items = self.tree_model.get_n_items()
        for i in range(n_items):
            tree_row = self.tree_model.get_item(i)
            if tree_row is None:
                continue

            # Build the path for this row
            row_path = self._build_xpath(tree_row)

            if row_path == target_path:
                # Found it! Select this position in the selection model
                self.selection_model.set_selected(i)
                self.column_view.scroll_to(i, None, Gtk.ListScrollFlags.FOCUS)
                return True

        return False

    def _find_position_in_model(self, target_tree_row) -> int:
        """Find the position of a TreeListRow in the selection model."""
        if self.selection_model is None:
            return Gtk.INVALID_LIST_POSITION

        n_items = self.selection_model.get_n_items()
        for i in range(n_items):
            item = self.selection_model.get_item(i)
            if item is target_tree_row:
                return i

        return Gtk.INVALID_LIST_POSITION
