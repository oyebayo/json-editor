# Implementation Checklist

Implementation tracking for the GTK4 JSON Editor desktop application.

---

## 1. Platform & Technology

- [x] Set up project as Python + PyGObject targeting GNOME / GTK4
- [x] Confirm runtime environment is Linux / GNOME desktop

---

## 2. User Interface

### 2.1 Application Header

- [x] Header is split into three sections: Tool Icons (left), Header Text (center), Hamburger Menu (right)
- [x] Tool Icons — View Group
    - [x] Toggle button to switch between Pretty Mode and Tree Mode
- [x] Tool Icons — Edit Group (disabled in Pretty Mode)
    - [x] Add Node button
    - [x] Duplicate Node button
    - [x] Delete Node button
- [x] Tool Icons — Other Group
    - [x] Save button
- [x] Header Text
    - [x] Displays the name of the currently open file
- [x] Hamburger Menu — File group
    - [x] Open
    - [x] Open URL
    - [x] Save As
- [x] Hamburger Menu — Preferences group
    - [x] Preferences
- [x] Hamburger Menu — View group
    - [x] TreeView Mode with checkmark toggle
- [x] Hamburger Menu — About group
    - [x] About JSON Editor

### 2.2 Status Bar

- [x] Status fields are separated by bars
- [x] TreeView Mode status fields
    - [x] Mode indicator (fixed width)
    - [x] Current node name (fixed width)
    - [x] JSON XPath-style path of selected node (variable width)
    - [x] App name (fixed width)
- [x] Pretty Mode status fields
    - [x] Mode indicator (fixed width)
    - [x] Modified indicator (fixed width)
    - [x] Message (variable width)
    - [x] File size (fixed width)
    - [x] Encoding (fixed width)
    - [x] App name (fixed width)

### 2.3 Content Window

- [x] Two alternating view modes: Pretty View (read-only) and Tree View (edit)

#### 2.3.1 Pretty View (Read-Only)

- [x] Default view when a file is opened
- [x] Pretty-printed JSON output with:
    - [x] Indentation
    - [x] Syntax highlighting
    - [x] Line numbers in gutter
- [x] Use GtkSourceView control
- [x] Light gray background
- [x] Gutter color is darker gray than the text area
- [x] No editing capability
- [x] No expand/collapse on JSON nodes

#### 2.3.2 Tree View (Edit Mode)

##### 2.3.2a Left Panel (Tree)

- [x] Interactive tree structure representing JSON hierarchy
- [x] Collapsible/expandable nodes; fully expanded by default
- [x] Expand/collapse icons use Adwaita `zoom-in-symbolic` (collapsed) and `zoom-out-symbolic` (expanded)
- [x] Icons placed immediately before the node name, not at the far left of the row
- [x] Leaf nodes (scalars, empty containers) show no expand/collapse icon
- [x] Indentation is 24px per depth level, applied manually
- [x] Movable divider between Key and Value columns

##### 2.3.2b Side Panel (Property Inspector)

- [x] Maintains fixed width at all times
- [x] Shows controls for the currently selected tree node

- [x] Field Name
    - [x] Editable display of current key name
    - [x] For array indices, displays the index number (e.g., `[0]`)

- [x] Field Type
    - [x] Dropdown selector with detected type
    - [x] Supported types: string, number, boolean, object, array
    - [x] Changing type converts the value accordingly

- [x] Field Value
    - [x] Widget varies by type:
        - [x] String: text entry; quotes auto-added when saved
        - [x] Number: text entry with numeric validation
        - [x] Boolean: toggle
        - [x] Object / Array: disabled entry showing `[...]` (uneditable)
    - [x] Input is hidden when "No Value" is checked

- [x] No-Value Checkbox
    - [x] Label: "No Value"
    - [x] When checked: hides value input widgets
    - [x] Sets the underlying JSON value to `null`
    - [x] Key remains in the tree and is clickable

- [x] Apply Changes button at the bottom, center-aligned (not full width)

- [x] Field Name, Field Type, Field Value, and No-Value Checkbox are vertically aligned

### 2.4 Preferences Dialog

- [x] Launched from Preferences menu entry
- [x] Opens as a modal window that stays on top
- [x] Window title: `Preferences - JSON Editor`
- [x] Toggle: "Set as default handler for JSON files"
    - [x] Reflects current default handler state on open
    - [x] Uses `xdg-mime` to set JSON Editor as default for `.json` files
    - [x] Unchecking restores system default (gedit / TextEditor)

### 2.5 Open URL Dialog

- [x] Launched from Open URL in hamburger menu
- [x] Modal dialog for entering a URL
- [x] Dialog width: 500px
- [x] Content margins: 18px on all sides
- [x] Entry field: 50 characters wide with placeholder text
- [x] Buttons: right-aligned, 8px spacing
- [x] Button margins: 18px on all sides, 6px gap above buttons
- [x] Open button has suggested-action style
- [x] Enter key submits the dialog

---

## 3. Behaviours

### 3.1 Open

- [x] Open from the hamburger menu
    - [x] Launches the File chooser dialog
    - [x] User can load local files or files from network share
- [x] Open from command line
    - [x] Passing a filename as first argument to app
    - [x] If file is missing or read-protected, app still launches but with error message
- [x] Open URL from the hamburger menu
    - [x] Does a web fetch and loads the content of the URL
    - [x] No code/content is executed for security reasons
    - [x] The URL is displayed in the title as filename
        - [x] If longer than 40 characters or available area, shorten the beginning with ellipsis
- [x] Last part of the path to file (filename and extension) is printed in header on successful open
- [x] For all file-open routes, if parsing fails, error message is shown to user and the situation is logged

### 3.2 Save

- [x] Direct save for writable local files (no prompt)
- [x] Save As dialog shown when:
    - [x] File was loaded from a URL, or
    - [x] Original file lacks write permissions, or
    - [x] User used the Save As hamburger menu item
- [x] Chosen destination becomes current file path for subsequent saves; this reflects in the header as well

### 3.3 Logging

- [x] Logging system with four levels: DEBUG, INFO, WARN, ERROR
- [x] Logs written to `stderr` with timestamps and source location
- [x] Default log level is INFO
- [x] Debug logging enabled via `--debug` flag
- [x] Log format matches spec:
    ```
    [2026-06-21 05:01:03] [DEBUG] src/json/json_ops.c:254 (json_op_add_node): ...
    ```

### 3.4 Add Node

- [x] When Add Node is clicked, a dialog is presented for specifying the new node's name, type, and value
- [x] Add Node button is disabled when the selected node is not an object or array
- [x] If the selected node is an array, the dialog hides the name input field and adds a new array element on success
- [x] If the selected node is not an array, the dialog shows the name input field and adds a new child node on success

### 3.5 Selection Persistence

- [x] After Add or Duplicate: the newly created node is selected and highlighted
- [x] After Delete: selection moves to the parent node, or if unavailable, to the nearest sibling
- [x] Selection is tracked via JSON XPath and restored after tree refresh
- [x] Property inspector updates to reflect the newly selected node after any operation
- [x] Tree view automatically scrolls to make the selected node visible after any selection change

### 3.6 Context Menu

- [x] Right-clicking a tree node opens a context menu with Add Node, Duplicate, and Delete
- [x] The right-clicked node becomes selected using the same mechanism as left-click (status bar and side panel update) before the menu is shown
- [x] Add Node is enabled only when the selected node is an object or array
- [x] Duplicate is enabled for all nodes except the root
- [x] Delete is enabled for all nodes except the root
- [x] Selecting a menu item performs the same action as the corresponding toolbar button
- [x] Clicking outside the menu dismisses it without performing any action

### 3.7 Expand / Collapse

- [x] Clicking the expand/collapse icon toggles the node's expanded state
- [x] Collapsed nodes show `zoom-in-symbolic`; expanded nodes show `zoom-out-symbolic`
- [x] Leaf nodes (scalars, empty containers) have no expand/collapse icon and cannot be expanded
- [x] Indentation is applied per depth level so the visual hierarchy is clear
- [x] The tree is fully expanded by default when a file is loaded

---

## 4. Install (Makefile)

- [x] Detect GTK4 development dependency (via pkg-config)
    - [x] Debian/Ubuntu: `libgtk-4-dev`
    - [x] Fedora/RHEL: `gtk4-devel`
    - [x] Arch: `gtk4`
- [x] Install `assets/json-editor.svg` to `<prefix>/share/icons/hicolor/scalable/apps/`
- [x] Install `assets/json-editor.desktop` to `<prefix>/share/applications/`
- [x] Update executable path inside installed `.desktop` file
- [x] Run `update-desktop-database <prefix>/share/applications/ 2>/dev/null || true`

---

## Notes / Open Questions

- Track unresolved questions, blockers, or follow-up tasks here as you progress.
