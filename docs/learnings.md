# Learnings

## Adw.Window Structure

- Call `Adw.init()` before creating any Adw widgets
- Use `Adw.ToolbarView` for header bars — `set_titlebar()` and `set_child()` are not supported on `Adw.Window`
- Use `StyleManager.get_dark()` for theme detection, not `get_color_scheme()` (returns `DEFAULT` when system is dark but user didn't explicitly set preference)
- Connect `"notify::color-scheme"` to re-apply custom themes on system toggle
- `Adw.Window` segfaults if destroyed without being realized — use `Gtk.ApplicationWindow` in tests
- Create windows in `activate`, not `startup`

## Gtk.AboutDialog

- No `"response"` or `"close"` signal — just call `present()`, GTK manages lifecycle
- Do not attempt to connect those signals, both fail at runtime

## Gtk.ColumnView Click Mapping

- `Gtk.ListItem` is a `GObject`, not a `GtkWidget` — never in the widget parent chain
- Store `TreeListRow` reference on cell widgets during bind (`box._tree_row = tree_row`)
- On click, use `pick(x, y, Gtk.PickFlags.DEFAULT)` then walk up `get_parent()` to find stored reference
- Find position by identity search (`is`) in selection model
- Do not use font metrics — breaks with indentation/variable row heights

## Gtk.TreeExpander Custom Icons

- Internal expander arrow is not CSS-stylable
- Wrap in `Gtk.Box`: hide built-in arrow (`set_hide_expander(True)`), disable indent (`set_indent_for_depth(False)`), place custom `Gtk.Image` + `Gtk.Label` as child
- Expand state lives on `TreeListRow`, not `TreeExpander` — use `row.set_expanded()` / `row.get_expanded()`
- Listen to `tree_row.connect("notify::expanded", ...)` for state changes
- Manual indent: `set_margin_start(depth * 24)`

## Gtk.TreeListModel Selection Persistence

- After `refresh_tree()` (full model rebuild), all `TreeListRow` references are invalid
- Save selection as XPath string before refresh, restore by path matching after
- **Add node**: use selected node's path as parent → `f"{parent_path}/{key}"`
- **Duplicate node**: derive parent from selected node's path (go UP one level)
- **Delete dict key**: compute fallback BEFORE `del` (key ordering stable)
- **Delete list item**: compute fallback AFTER `del` (indices shift)
- Connect signal handler BEFORE calling `select_node_by_path()` or dependent UI won't update
- After selecting, call `column_view.scroll_to(i, None, Gtk.ListScrollFlags.FOCUS)`
