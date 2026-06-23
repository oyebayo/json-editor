import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

from editor.json.loader import (  # noqa: E402
    JsonLoadError,
    MimeTypeError,
    UrlLoadError,
    load_file,
    load_url,
)
from editor.json.saver import save_file  # noqa: E402
from editor.logger import get_logger  # noqa: E402
from editor.ui.dialogs import (  # noqa: E402
    show_about_dialog,
    show_add_node_dialog,
    show_error_dialog,
    show_open_file_dialog,
    show_preferences_dialog,
    show_save_as_dialog,
    show_url_dialog,
)
from editor.ui.header_bar import HeaderBar  # noqa: E402
from editor.ui.pretty_view import PrettyView  # noqa: E402
from editor.ui.status_bar import StatusBar  # noqa: E402
from editor.ui.tree_view import JsonTreePanel  # noqa: E402


class AppWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="JSON Editor")
        self.set_default_size(900, 600)

        self.current_file_path = None
        self.current_file_url = None
        self.current_data = None

        self._build_ui()
        self._create_actions(app)
        self._connect_signals()

    def _build_ui(self):
        self.header_bar = HeaderBar()
        self.set_titlebar(self.header_bar)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)

        self.pretty_view = PrettyView()
        self.stack.add_titled(self.pretty_view, "pretty", "Pretty View")

        self.tree_panel = JsonTreePanel()
        self.tree_panel.inspector.apply_btn.connect("clicked", self._on_inspector_apply)
        self.tree_panel.connect("context-menu-add", self._on_add_node)
        self.tree_panel.connect("context-menu-duplicate", self._on_duplicate_node)
        self.tree_panel.connect("context-menu-delete", self._on_remove_node)
        self.stack.add_titled(self.tree_panel, "tree", "Tree View")

        self.status_bar = StatusBar()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.stack.set_vexpand(True)
        main_box.append(self.stack)
        main_box.append(self.status_bar)
        self.set_child(main_box)

    def _create_actions(self, app):
        open_action = Gio.SimpleAction.new("open", None)
        open_action.connect("activate", self._on_open)
        app.add_action(open_action)

        open_url_action = Gio.SimpleAction.new("open-url", None)
        open_url_action.connect("activate", self._on_open_url)
        app.add_action(open_url_action)

        save_action = Gio.SimpleAction.new("save", None)
        save_action.connect("activate", self._on_save)
        app.add_action(save_action)

        save_as_action = Gio.SimpleAction.new("save-as", None)
        save_as_action.connect("activate", self._on_save_as)
        app.add_action(save_as_action)

        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self._on_preferences)
        app.add_action(preferences_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        app.add_action(about_action)

        self.treeview_action = Gio.SimpleAction.new_stateful(
            "treeview-mode", None, GLib.Variant.new_boolean(False)
        )
        self.treeview_action.connect("change-state", self._on_treeview_mode_change)
        app.add_action(self.treeview_action)

    def _connect_signals(self):
        self.header_bar.view_button.connect("toggled", self._on_view_toggle)
        self.header_bar.add_button.connect("clicked", self._on_add_node)
        self.header_bar.duplicate_button.connect("clicked", self._on_duplicate_node)
        self.header_bar.delete_button.connect("clicked", self._on_remove_node)

    # --- event handlers ---

    def _on_view_toggle(self, button):
        logger = get_logger(__name__)
        is_tree = button.get_active()
        if is_tree:
            logger.info("Switching to Tree View mode")
            self.stack.set_visible_child_name("tree")
        else:
            logger.info("Switching to Pretty View mode")
            self.stack.set_visible_child_name("pretty")
        self.status_bar.set_mode(is_tree)
        self.treeview_action.set_state(GLib.Variant.new_boolean(is_tree))
        self._update_edit_buttons()

    def _on_treeview_mode_change(self, action, value):
        logger = get_logger(__name__)
        is_tree = value.get_boolean()
        action.set_state(value)
        if is_tree:
            logger.info("Switching to Tree View mode (via menu)")
            self.stack.set_visible_child_name("tree")
        else:
            logger.info("Switching to Pretty View mode (via menu)")
            self.stack.set_visible_child_name("pretty")
        self.status_bar.set_mode(is_tree)
        self.header_bar.view_button.handler_block_by_func(self._on_view_toggle)
        self.header_bar.view_button.set_active(is_tree)
        self.header_bar.view_button.handler_unblock_by_func(self._on_view_toggle)
        self._update_edit_buttons()

    def _on_tree_selection_changed(self, selection_model, pos, n_items):
        node_name, node_path = self.tree_panel.get_selected_node_info()
        self.status_bar.set_node_info(node_name, node_path)

        data = self.tree_panel.get_selected_node_data()
        if data is not None:
            node, parent_data, key = data
            self.tree_panel.inspector.load_node(node, parent_data, key)

        self._update_edit_buttons()

    def _update_edit_buttons(self):
        """Update the sensitivity of the Add/Duplicate/Delete header buttons."""
        is_tree = self.stack.get_visible_child_name() == "tree"
        state = (
            self.tree_panel.get_selection_state()
            if self.tree_panel.has_data()
            else {
                "has_selection": False,
                "is_root": False,
                "is_container": False,
            }
        )
        self.header_bar.update_edit_buttons(
            is_tree,
            state["has_selection"],
            state["is_root"],
            state["is_container"],
        )

    def _on_add_node(self, _button):
        logger = get_logger(__name__)
        data = self.tree_panel.get_selected_node_data()
        if data is None:
            return

        node, parent, key = data
        target = node.value
        if not isinstance(target, (dict, list)):
            logger.warning("Cannot add child to non-container node")
            return

        parent_is_dict = isinstance(target, dict)

        def do_add(new_key, new_value):
            new_path = self.tree_panel.add_child_node(new_key or "", new_value)
            if new_path:
                self.current_data = self.tree_panel.json_data
                self.pretty_view.load_json(self.current_data)
                self._connect_tree_selection()
                self.tree_panel.select_node_by_path(new_path)
                self._update_edit_buttons()

        show_add_node_dialog(self, parent_is_dict, do_add)

    def _on_duplicate_node(self, _button):
        logger = get_logger(__name__)
        new_path = self.tree_panel.duplicate_selected_node()
        if new_path:
            self.current_data = self.tree_panel.json_data
            self.pretty_view.load_json(self.current_data)
            self._connect_tree_selection()
            self.tree_panel.select_node_by_path(new_path)
            self._update_edit_buttons()
            logger.info("Node duplicated")

    def _on_remove_node(self, _button):
        logger = get_logger(__name__)
        new_path = self.tree_panel.remove_selected_node()
        if new_path:
            self.current_data = self.tree_panel.json_data
            self.pretty_view.load_json(self.current_data)
            self._connect_tree_selection()
            self.tree_panel.select_node_by_path(new_path)
            self._update_edit_buttons()
            logger.info("Node removed")

    def _on_inspector_apply(self, _button):
        success = self.tree_panel.inspector.apply_changes()
        if not success:
            return
        self.current_data = self.tree_panel.json_data
        self.tree_panel.refresh_tree()
        self.pretty_view.load_json(self.current_data)
        self._connect_tree_selection()

    def _connect_tree_selection(self):
        """Connect the tree selection-changed signal to the handler."""
        if self.tree_panel.selection_model:
            self.tree_panel.selection_model.connect(
                "selection-changed", self._on_tree_selection_changed
            )

    def _on_open(self, action, param):
        show_open_file_dialog(self, self._load_and_apply_path)

    def _on_open_url(self, action, param):
        logger = get_logger(__name__)
        logger.info("Opening URL dialog")
        show_url_dialog(self, self._load_and_apply_url)

    def _on_save(self, action, param):
        logger = get_logger(__name__)

        if self.current_data is None:
            logger.info("No data to save")
            return

        if self.current_file_url:
            logger.info("File loaded from URL, showing Save As dialog")
            show_save_as_dialog(self, self._save_to_path)
            return

        if self.current_file_path:
            if not os.access(self.current_file_path, os.W_OK):
                logger.info("File not writable, showing Save As dialog")
                show_save_as_dialog(self, self._save_to_path)
                return

            self._do_save(self.current_file_path)
            return

        logger.info("No file path, showing Save As dialog")
        show_save_as_dialog(self, self._save_to_path)

    def _on_save_as(self, action, param):
        logger = get_logger(__name__)
        logger.info("Save As requested")

        if self.current_data is None:
            logger.info("No data to save")
            return

        show_save_as_dialog(self, self._save_to_path)

    def _on_preferences(self, action, param):
        show_preferences_dialog(self)

    def _on_about(self, action, param):
        show_about_dialog(self)

    def _save_to_path(self, path):
        self._do_save(path, update_path=True)

    def _do_save(self, path, update_path=False):
        logger = get_logger(__name__)
        try:
            meta = save_file(path, self.current_data)
        except Exception as e:
            logger.error(f"Save failed: {e}")
            show_error_dialog(self, "Save Failed", str(e))
            return

        if update_path or self.current_file_url:
            self.current_file_path = meta["path"]
            self.current_file_url = None
            self.header_bar.set_title_text(meta["filename"])

        self.status_bar.set_file_size(meta["file_size"])
        self.status_bar.set_message(f"Saved {meta['filename']}")
        logger.info(f"File saved: {meta['filename']}")

    # --- loading ---

    def _load_and_apply_path(self, path):
        self._load_and_apply(path=path)

    def _load_and_apply_url(self, url):
        self._load_and_apply(url=url)

    def load_initial_file(self, path):
        self._load_and_apply(path=path)

    def _load_and_apply(self, path=None, url=None):
        try:
            if path:
                data, meta = load_file(path)
            else:
                data, meta = load_url(url)
        except JsonLoadError as e:
            show_error_dialog(self, "Invalid JSON", str(e))
            return
        except MimeTypeError as e:
            show_error_dialog(self, "Invalid Content Type", str(e))
            return
        except UrlLoadError as e:
            show_error_dialog(self, "URL Error", str(e))
            return
        except PermissionError:
            show_error_dialog(self, "Permission Denied", f"Cannot read file:\n{path}")
            return
        except FileNotFoundError:
            show_error_dialog(self, "File Not Found", f"File does not exist:\n{path}")
            return
        except Exception as e:
            show_error_dialog(self, "Error", f"Failed to load:\n{e}")
            return

        self.pretty_view.load_json(data)
        self.tree_panel.load_json(data)
        self._connect_tree_selection()
        self._update_edit_buttons()

        self.current_data = data
        self.current_file_path = meta.get("path")
        self.current_file_url = meta.get("url")

        if "filename" in meta:
            self.header_bar.set_title_text(meta["filename"])
        elif "display_url" in meta:
            self.header_bar.set_title_text(meta["display_url"])

        if "file_size" in meta:
            self.status_bar.set_file_size(meta["file_size"])
        if "filename" in meta:
            self.status_bar.set_message(f"Loaded {meta['filename']}")
        else:
            self.status_bar.set_message("Loaded from URL")
