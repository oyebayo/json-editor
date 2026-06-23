import subprocess
from importlib.metadata import PackageNotFoundError, version

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

from editor.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def _get_app_version():
    try:
        return version("json-editor")
    except PackageNotFoundError:
        return "0.1.0"


def show_about_dialog(win):
    """Show the About dialog for JSON Editor."""
    dialog = Gtk.AboutDialog(
        transient_for=win,
        modal=True,
        program_name="JSON Editor",
        version=_get_app_version(),
        comments="A GTK4 desktop application for GNOME that reads JSON files, "
        "displays them in a prettified format, and provides an interactive "
        "tree-view editor for making JSON-valid modifications.",
        logo_icon_name="json-editor",
    )
    dialog.present()


_ADD_VALUE_TYPES = ["string", "number", "boolean", "null", "object", "array"]


def _default_value_for_type(type_label: str):
    """Return the default value for a given type label."""
    if type_label == "string":
        return ""
    if type_label == "number":
        return 0
    if type_label == "boolean":
        return False
    if type_label == "null":
        return None
    if type_label == "object":
        return {}
    if type_label == "array":
        return []
    return ""


def show_add_node_dialog(win, parent_is_dict, on_add):
    """Show a dialog for adding a new child node.

    Args:
        win: The parent window.
        parent_is_dict: True if the parent node is a dict (needs key entry).
        on_add: Callback(key: str | None, value) invoked with the new node data.
    """
    dialog = Gtk.Dialog(
        title="Add Node",
        transient_for=win,
        modal=True,
        destroy_with_parent=True,
    )
    dialog.set_default_size(400, -1)

    content = dialog.get_content_area()
    content.set_spacing(0)

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    main_box.set_margin_top(18)
    main_box.set_margin_bottom(6)
    main_box.set_margin_start(18)
    main_box.set_margin_end(18)

    key_entry = None
    if parent_is_dict:
        key_label = Gtk.Label(label="Key:", xalign=0)
        key_label.add_css_class("dim-label")
        main_box.append(key_label)

        key_entry = Gtk.Entry()
        key_entry.set_placeholder_text("key name")
        key_entry.set_hexpand(True)
        main_box.append(key_entry)

    type_label_widget = Gtk.Label(label="Value Type:", xalign=0)
    type_label_widget.add_css_class("dim-label")
    main_box.append(type_label_widget)

    type_model = Gtk.StringList.new(_ADD_VALUE_TYPES)
    type_dropdown = Gtk.DropDown(model=type_model)
    main_box.append(type_dropdown)

    value_label_widget = Gtk.Label(label="Value:", xalign=0)
    value_label_widget.add_css_class("dim-label")
    main_box.append(value_label_widget)

    value_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    main_box.append(value_box)

    value_widget = None

    def rebuild_value_widget():
        nonlocal value_widget
        for child in list(value_box):
            value_box.remove(child)
        value_widget = None

        type_name = _ADD_VALUE_TYPES[type_dropdown.get_selected()]
        if type_name == "string":
            value_widget = Gtk.Entry()
            value_widget.set_text("")
            value_box.append(value_widget)
        elif type_name == "number":
            value_widget = Gtk.Entry()
            value_widget.set_text("0")
            value_box.append(value_widget)
        elif type_name == "boolean":
            value_widget = Gtk.Switch()
            value_widget.set_active(False)
            value_widget.set_halign(Gtk.Align.START)
            value_box.append(value_widget)
        elif type_name == "null":
            lbl = Gtk.Label(label="null")
            lbl.add_css_class("dim-label")
            lbl.set_xalign(0)
            value_box.append(lbl)
        elif type_name in ("object", "array"):
            lbl = Gtk.Label(label=f"empty {type_name}")
            lbl.add_css_class("dim-label")
            lbl.set_xalign(0)
            value_box.append(lbl)

    rebuild_value_widget()
    type_dropdown.connect("notify::selected", lambda *_: rebuild_value_widget())

    content.append(main_box)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    button_box.set_halign(Gtk.Align.END)
    button_box.set_margin_top(6)
    button_box.set_margin_bottom(18)
    button_box.set_margin_start(18)
    button_box.set_margin_end(18)

    cancel_button = Gtk.Button(label="Cancel")
    cancel_button.connect("clicked", lambda _: dialog.response(Gtk.ResponseType.CANCEL))
    button_box.append(cancel_button)

    add_button = Gtk.Button(label="Add")
    add_button.add_css_class("suggested-action")
    add_button.connect("clicked", lambda _: dialog.response(Gtk.ResponseType.OK))
    button_box.append(add_button)

    content.append(button_box)
    dialog.set_default_response(Gtk.ResponseType.OK)

    def on_response(_dialog, response):
        if response == Gtk.ResponseType.OK:
            key = None
            if key_entry is not None:
                key = key_entry.get_text().strip()
                if not key:
                    return

            type_name = _ADD_VALUE_TYPES[type_dropdown.get_selected()]
            if type_name == "string":
                value = value_widget.get_text() if value_widget else ""
            elif type_name == "number":
                text = value_widget.get_text() if value_widget else "0"
                try:
                    value = float(text) if "." in text else int(text)
                except ValueError:
                    value = 0
            elif type_name == "boolean":
                value = value_widget.get_active() if value_widget else False
            elif type_name == "null":
                value = None
            elif type_name == "object":
                value = {}
            elif type_name == "array":
                value = []
            else:
                value = ""

            on_add(key, value)
        dialog.destroy()

    dialog.connect("response", on_response)
    dialog.present()


_DESKTOP_FILE = "json-editor.desktop"
_JSON_MIME = "application/json"


def _is_default_handler():
    """Check if JSON Editor is the current default handler for JSON files."""
    try:
        result = subprocess.run(
            ["xdg-mime", "query", "default", _JSON_MIME],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() == _DESKTOP_FILE
    except Exception:
        return False


def _set_default_handler():
    """Set JSON Editor as default handler for JSON files."""
    subprocess.run(
        ["xdg-mime", "default", _DESKTOP_FILE, _JSON_MIME],
        capture_output=True,
        timeout=5,
    )


def _restore_default_handler():
    """Restore system default handler for JSON files."""
    subprocess.run(
        ["xdg-mime", "default", "org.gnome.TextEditor.desktop", _JSON_MIME],
        capture_output=True,
        timeout=5,
    )


def show_preferences_dialog(win):
    """Show the Preferences dialog."""
    dialog = Gtk.Dialog(
        title="Preferences - JSON Editor",
        transient_for=win,
        modal=True,
        destroy_with_parent=True,
    )
    dialog.set_default_size(400, -1)

    content = dialog.get_content_area()
    content.set_spacing(0)

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    main_box.set_margin_top(18)
    main_box.set_margin_bottom(6)
    main_box.set_margin_start(18)
    main_box.set_margin_end(18)

    is_default = _is_default_handler()

    toggle = Gtk.CheckButton(label="Set as default handler for JSON files")
    toggle.set_active(is_default)
    main_box.append(toggle)

    content.append(main_box)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    button_box.set_halign(Gtk.Align.END)
    button_box.set_margin_top(6)
    button_box.set_margin_bottom(18)
    button_box.set_margin_start(18)
    button_box.set_margin_end(18)

    close_button = Gtk.Button(label="Close")
    close_button.add_css_class("suggested-action")

    def on_close_clicked(_):
        if toggle.get_active() and not is_default:
            _set_default_handler()
            logger.info("Set JSON Editor as default handler for JSON files")
        elif not toggle.get_active() and is_default:
            _restore_default_handler()
            logger.info("Restored system default handler for JSON files")
        dialog.destroy()

    close_button.connect("clicked", on_close_clicked)
    button_box.append(close_button)

    content.append(button_box)

    dialog.connect("response", lambda dlg, resp: dlg.destroy())
    dialog.present()


def show_error_dialog(win, title, message):
    """Show an error dialog."""
    dialog = Gtk.MessageDialog(
        transient_for=win,
        modal=True,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(message)
    dialog.connect("response", lambda dlg, resp: dlg.destroy())
    dialog.present()


def show_open_file_dialog(win, on_file_selected):
    """Show a file chooser for JSON files. Calls on_file_selected(path)."""
    logger.info("Opening file chooser dialog")

    dialog = Gtk.FileDialog.new()
    dialog.set_title("Open JSON File")

    filter_json = Gtk.FileFilter()
    filter_json.set_name("JSON files")
    filter_json.add_pattern("*.json")
    filter_json.add_mime_type("application/json")

    filters = Gio.ListStore.new(Gtk.FileFilter)
    filters.append(filter_json)
    dialog.set_filters(filters)

    def on_response(dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                logger.info(f"File selected: {path}")
                on_file_selected(path)
        except GLib.Error as e:
            logger.debug(f"File dialog cancelled or error: {e}")

    dialog.open(win, None, on_response)


def show_url_dialog(win, on_url_submitted):
    """Show a URL entry dialog. Calls on_url_submitted(url)."""
    dialog = Gtk.Dialog(
        title="Open URL",
        transient_for=win,
        modal=True,
        destroy_with_parent=True,
    )
    dialog.set_default_size(500, -1)

    content = dialog.get_content_area()
    content.set_spacing(0)

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    main_box.set_margin_top(18)
    main_box.set_margin_bottom(6)
    main_box.set_margin_start(18)
    main_box.set_margin_end(18)

    label = Gtk.Label(label="Enter URL of JSON file:")
    label.set_xalign(0)
    main_box.append(label)

    entry = Gtk.Entry()
    entry.set_placeholder_text("https://example.com/data.json")
    entry.set_hexpand(True)
    entry.set_width_chars(50)
    main_box.append(entry)

    content.append(main_box)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    button_box.set_halign(Gtk.Align.END)
    button_box.set_margin_top(6)
    button_box.set_margin_bottom(18)
    button_box.set_margin_start(18)
    button_box.set_margin_end(18)

    cancel_button = Gtk.Button(label="Cancel")
    cancel_button.connect("clicked", lambda _: dialog.response(Gtk.ResponseType.CANCEL))
    button_box.append(cancel_button)

    open_button = Gtk.Button(label="Open")
    open_button.add_css_class("suggested-action")
    open_button.connect("clicked", lambda _: dialog.response(Gtk.ResponseType.OK))
    button_box.append(open_button)

    content.append(button_box)
    dialog.set_default_response(Gtk.ResponseType.OK)

    def on_response(dialog, response):
        if response == Gtk.ResponseType.OK:
            url = entry.get_text().strip()
            if url:
                on_url_submitted(url)
        dialog.destroy()

    dialog.connect("response", on_response)
    dialog.present()


def show_save_as_dialog(win, on_file_selected):
    """Show a save-as file chooser for JSON files. Calls on_file_selected(path)."""
    logger.info("Opening save-as dialog")

    dialog = Gtk.FileDialog.new()
    dialog.set_title("Save JSON File As")

    filter_json = Gtk.FileFilter()
    filter_json.set_name("JSON files")
    filter_json.add_pattern("*.json")
    filter_json.add_mime_type("application/json")

    filters = Gio.ListStore.new(Gtk.FileFilter)
    filters.append(filter_json)
    dialog.set_filters(filters)

    def on_response(dialog, result):
        try:
            file = dialog.save_finish(result)
            if file:
                path = file.get_path()
                if not path.endswith(".json"):
                    path += ".json"
                logger.info(f"Save-as path: {path}")
                on_file_selected(path)
        except GLib.Error as e:
            logger.debug(f"Save-as dialog cancelled or error: {e}")

    dialog.save(win, None, on_response)
