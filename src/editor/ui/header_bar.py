import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gio, Gtk


class HeaderBar(Gtk.HeaderBar):
    def __init__(self):
        super().__init__()

        # Left side: Tool buttons
        self._setup_tool_buttons()

        # Center: Title
        self._setup_title()

        # Right side: Hamburger menu
        self._setup_menu()

    def _setup_tool_buttons(self):
        # View group: Toggle between Pretty Mode and Tree Mode
        # Icon shows the mode you'll switch TO (tree → go to tree, eye → go to pretty)
        self.view_icon = Gtk.Image.new_from_icon_name("view-dual-symbolic")
        self.view_button = Gtk.ToggleButton(child=self.view_icon)
        self.view_button.set_tooltip_text("Toggle View Mode")
        self.view_button.connect("toggled", self._on_view_toggled)
        self.pack_start(self.view_button)

        # Separator
        sep1 = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.pack_start(sep1)

        # Edit group: Add, Duplicate, Delete (disabled in Pretty Mode by default)
        self.add_button = Gtk.Button()
        add_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
        self.add_button.set_child(add_icon)
        self.add_button.set_tooltip_text("Add Node")
        self.add_button.set_sensitive(False)
        self.pack_start(self.add_button)

        self.duplicate_button = Gtk.Button()
        duplicate_icon = Gtk.Image.new_from_icon_name("edit-copy-symbolic")
        self.duplicate_button.set_child(duplicate_icon)
        self.duplicate_button.set_tooltip_text("Duplicate Node")
        self.duplicate_button.set_sensitive(False)
        self.pack_start(self.duplicate_button)

        self.delete_button = Gtk.Button()
        delete_icon = Gtk.Image.new_from_icon_name("list-remove-symbolic")
        self.delete_button.set_child(delete_icon)
        self.delete_button.set_tooltip_text("Delete Node")
        self.delete_button.set_sensitive(False)
        self.pack_start(self.delete_button)

        # Separator
        sep2 = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        self.pack_start(sep2)

        # Save button
        self.save_button = Gtk.Button()
        save_icon = Gtk.Image.new_from_icon_name("document-save-symbolic")
        self.save_button.set_child(save_icon)
        self.save_button.set_tooltip_text("Save")
        self.save_button.set_action_name("app.save")
        self.pack_start(self.save_button)

    def _on_view_toggled(self, button):
        if button.get_active():
            self.view_icon.set_from_icon_name("view-reveal-symbolic")
        else:
            self.view_icon.set_from_icon_name("view-dual-symbolic")

    def update_edit_buttons(self, is_tree_mode, has_selection, is_root, is_container):
        """Update edit button sensitivity based on current state.

        Args:
            is_tree_mode: Whether we are in tree view mode.
            has_selection: Whether a node is selected.
            is_root: Whether the selected node is the root.
            is_container: Whether the selected node is a dict or list.
        """
        can_add = is_tree_mode and has_selection and is_container
        can_duplicate = is_tree_mode and has_selection and not is_root
        can_remove = is_tree_mode and has_selection and not is_root

        self.add_button.set_sensitive(can_add)
        self.duplicate_button.set_sensitive(can_duplicate)
        self.delete_button.set_sensitive(can_remove)

    def _setup_title(self):
        self.title_label = Gtk.Label(label="Untitled")
        self.title_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self.set_title_widget(self.title_label)

    def set_title_text(self, text):
        """Update the header title text."""
        self.title_label.set_label(text)

    def _setup_menu(self):
        # Build menu structure
        menu = Gio.Menu.new()

        # File group
        file_section = Gio.Menu.new()
        file_section.append("Open", "app.open")
        file_section.append("Open URL", "app.open-url")
        file_section.append("Save As", "app.save-as")
        menu.append_section(None, file_section)

        # Preferences group
        prefs_section = Gio.Menu.new()
        prefs_section.append("Preferences", "app.preferences")
        menu.append_section(None, prefs_section)

        # View group
        view_section = Gio.Menu.new()
        view_section.append("TreeView Mode", "app.treeview-mode")
        menu.append_section(None, view_section)

        # About group
        about_section = Gio.Menu.new()
        about_section.append("About JSON Editor", "app.about")
        menu.append_section(None, about_section)

        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_menu_model(menu)
        self.pack_end(menu_button)
