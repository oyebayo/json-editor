from typing import Any

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from editor.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

TYPE_LABELS = ["string", "number", "boolean", "object", "array"]


def _detect_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "number"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if value is None:
        return "string"
    return "string"


class PropertyInspector(Gtk.Box):
    """Property Inspector side panel for editing selected JSON node values."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        logger.debug("Initializing Property Inspector")

        self.set_size_request(280, -1)

        self._node = None
        self._parent_data = None
        self._key_path = None

        self._build_ui()

    def _build_ui(self):
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(12)
        self.set_margin_bottom(12)

        # --- Field Name ---
        name_label = Gtk.Label(label="Field Name", xalign=0)
        name_label.add_css_class("dim-label")
        self.append(name_label)

        self.name_entry = Gtk.Entry()
        self.append(self.name_entry)

        # --- Field Type ---
        type_label = Gtk.Label(label="Field Type", xalign=0)
        type_label.add_css_class("dim-label")
        self.append(type_label)

        type_model = Gtk.StringList.new(TYPE_LABELS)
        self.type_dropdown = Gtk.DropDown(model=type_model)
        self.type_dropdown.connect("notify::selected", self._on_type_changed)
        self.append(self.type_dropdown)

        # --- Field Value ---
        value_label = Gtk.Label(label="Field Value", xalign=0)
        value_label.add_css_class("dim-label")
        self.append(value_label)

        self._value_widget = None
        self._value_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append(self._value_box)

        # --- No Value checkbox ---
        self.no_value_check = Gtk.CheckButton(label="No Value")
        self.no_value_check.connect("toggled", self._on_no_value_toggled)
        self.append(self.no_value_check)

        # --- Apply button ---
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        self.append(spacer)

        self.apply_btn = Gtk.Button(label="Apply Changes")
        self.apply_btn.add_css_class("suggested-action")
        self.apply_btn.set_halign(Gtk.Align.CENTER)
        self.append(self.apply_btn)

    # --- public API ---

    def load_node(self, node, parent_data, key_path):
        """Populate controls from the selected tree node.

        Args:
            node: The JsonTreeNode selected.
            parent_data: The parent dict or list containing the node's value.
            key_path: The key (str) or index (int) into parent_data.
        """
        self._node = node
        self._parent_data = parent_data
        self._key_path = key_path

        value = node.value
        is_root = parent_data is None

        # Field Name
        self.name_entry.set_text(str(node.key))
        is_array_index = isinstance(parent_data, list)
        self.name_entry.set_sensitive(not is_array_index and not is_root)

        # Field Type
        if value is None:
            detected = "string"
        else:
            detected = _detect_type(value)

        try:
            idx = TYPE_LABELS.index(detected)
            self.type_dropdown.set_selected(idx)
        except ValueError:
            self.type_dropdown.set_selected(0)

        # No Value
        self.no_value_check.set_active(value is None)

        # Value widget
        self._rebuild_value_widget(detected, value)

        self.apply_btn.set_sensitive(not is_root)

    def get_edited_value(self) -> Any:
        """Return the converted value from the current widget state."""
        if self.no_value_check.get_active():
            return None

        type_label = TYPE_LABELS[self.type_dropdown.get_selected()]

        if type_label == "string":
            return self._value_widget.get_text() if self._value_widget else ""
        if type_label == "number":
            text = self._value_widget.get_text() if self._value_widget else "0"
            try:
                if "." in text:
                    return float(text)
                return int(text)
            except ValueError:
                return 0
        if type_label == "boolean":
            return self._value_widget.get_active() if self._value_widget else False
        if type_label in ("object", "array"):
            return self._node.value if self._node else None
        return None

    def apply_changes(self) -> bool:
        """Update JSON data from the inspector controls. Returns True on success."""
        if self._parent_data is None or self._node is None:
            return False

        new_value = self.get_edited_value()
        new_name = self.name_entry.get_text().strip()

        if not new_name:
            logger.warn("Field name cannot be empty")
            return False

        # Rename key if parent is dict and name changed
        if isinstance(self._parent_data, dict) and new_name != str(self._node.key):
            old_key = self._node.key
            if new_name in self._parent_data:
                logger.warn(f"Key '{new_name}' already exists in parent")
                return False
            rebuilt = {}
            for k, v in self._parent_data.items():
                if k == old_key:
                    rebuilt[new_name] = new_value
                else:
                    rebuilt[k] = v
            self._parent_data.clear()
            self._parent_data.update(rebuilt)
        elif isinstance(self._parent_data, dict):
            self._parent_data[self._node.key] = new_value
        elif isinstance(self._parent_data, list):
            self._parent_data[self._key_path] = new_value

        logger.info(f"Applied changes to '{new_name}'")
        return True

    # --- private helpers ---

    def _rebuild_value_widget(self, type_label: str, value: Any):
        for child in list(self._value_box):
            self._value_box.remove(child)

        self._value_widget = None

        if self.no_value_check.get_active():
            return

        if type_label == "string":
            w = Gtk.Entry()
            w.set_text(str(value) if value is not None else "")
            self._value_widget = w
            self._value_box.append(w)
        elif type_label == "number":
            w = Gtk.Entry()
            w.set_text(str(value) if value is not None else "0")
            self._value_widget = w
            self._value_box.append(w)
        elif type_label == "boolean":
            w = Gtk.Switch()
            w.set_active(bool(value))
            w.set_halign(Gtk.Align.START)
            self._value_widget = w
            self._value_box.append(w)
        elif type_label in ("object", "array"):
            w = Gtk.Entry()
            w.set_text("[...]")
            w.set_sensitive(False)
            self._value_widget = w
            self._value_box.append(w)

    def _on_type_changed(self, dropdown, _pspec):
        type_label = TYPE_LABELS[dropdown.get_selected()]
        current_value = self._node.value if self._node else None

        if self.no_value_check.get_active():
            self._rebuild_value_widget(type_label, None)
            return

        converted = self._convert_value(current_value, type_label)
        self._rebuild_value_widget(type_label, converted)

    def _on_no_value_toggled(self, _check):
        type_label = TYPE_LABELS[self.type_dropdown.get_selected()]
        if self.no_value_check.get_active():
            self._rebuild_value_widget(type_label, None)
        else:
            value = self._node.value if self._node else ""
            if value is None:
                value = "" if type_label == "string" else value
            self._rebuild_value_widget(type_label, value)

    @staticmethod
    def _convert_value(value: Any, target_type: str) -> Any:
        if value is None:
            if target_type == "string":
                return ""
            if target_type == "number":
                return 0
            if target_type == "boolean":
                return False
            if target_type in ("object", "array"):
                return {} if target_type == "object" else []
            return None
        if target_type == "string":
            return str(value)
        if target_type == "number":
            try:
                if isinstance(value, str) and "." in value:
                    return float(value)
                return int(float(value))
            except (ValueError, TypeError):
                return 0
        if target_type == "boolean":
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        if target_type == "array":
            if isinstance(value, list):
                return value
            return [value]
        if target_type == "object":
            if isinstance(value, dict):
                return value
            return {}
        return value
