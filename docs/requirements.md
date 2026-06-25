# Overview
A GTK4 desktop application for GNOME that reads JSON files, displays them in a prettified format, and provides an interactive tree-view editor for making JSON-valid modifications. The application supports local files, URLs, and network shares as data sources.

---

## 1. Platform & Technology
- Target Platform: GNOME desktop (Linux)
- UI Toolkit: GTK4 with libadwaita
- Language: Python with PyGObject for GTK4 native integration

---

## 2. User Interface
Application uses modern GTK4 concepts with libadwaita for Adwaita styling and system theme integration. No legacy GTK3 implementation methods.

### 2.0 Theme Support
- Uses libadwaita (`Adw.Application`, `Adw.Window`, `Adw.ToolbarView`) for native Adwaita window decorations and styling
- Follows system color scheme (light/dark mode) via `Adw.StyleManager`
- GtkSourceView editor theme switches dynamically between light and dark variants based on system preference
- Theme changes apply immediately when system toggles between light/dark mode

### 2.1 Application Header
- Header is made up of three sections
  - Tool Icons (aligned left)
  - Header text (aligned center)
  - Hamburger menu (aligned  right)

Layout
```text
+--------------------------------------------------+
| [Vw]|[Ad][Dp][Dl]|[Sv]|      hdr txt       | ... |
+--------------------------------------------------+
```

#### 2.1.1 Tool Icons
- **View Group**: Toggle image button (between Pretty Mode and Tree Mode)
  - The icon represents the mode the user will switch TO when clicked
  - In Pretty Mode: shows tree icon (click to enter Tree Mode)
  - In Tree Mode: shows eye icon (click to return to Pretty Mode)
- **Edit Group**: Image buttons: Add Node, Duplicate Node, Delete Node. All disabled in Pretty Mode
- **Other Group**: Save

#### 2.1.2 Header text
- Name of open file

#### 2.1.3 Hamburger Menu
- **File group**: Open, Open URL, Save As
- **Preferences group**: Preferences 
- **View group**: TreeView Mode (with checkmark toggle)
- **About group**: About JSON Editor
 
### 2.2 Status Bar
 - In TreeView mode: displays fields separated by bars
    - mode indicator (fixed width)
    - current node name (fixed width)
    - JSON XPath style path of selected node (variable width)
    - App Name (fixed width)
 - In Pretty Mode: displays fields separated by bars
    - mode indicator (fixed width)
    - Modified indicator (fixed width)
    - message (variable width)
    - file size (fixed width)
    - encoding (fixed width)
    - App Name (fixed width)

### 2.3 Content window
Two alternating view modes
- Pretty View (Read-Only)
- Tree View (Edit Mode)

#### 2.3.1 Pretty View (Read-Only)
- Default view when a file is opened
- Standard pretty-printed JSON output (indented, syntax-highlighted, line numbers in gutter)
    - uses GtkSourceView control
    - light theme: light gray background, darker gray gutter
    - dark theme: dark background with matching syntax colors
    - theme switches automatically with system color scheme
- No editing capability in this mode
- No expand/collapse function on the JSON nodes
- Flat display of the entire JSON structure
- Line numbers column with synchronized scrolling

#### 2.3.2 Tree View (Edit Mode)
Layout
```text
+---------------------+----------------------------+
| Tree View (Left)    | Side Panel (Right)         |
|                     |                            |
| ▼ root              | Field Name:  [name]        |
|   ▼ key1            | Field Type:  [string ▼]    |
|     ▼ key2          | Field Value: [value]       |
|       ▼ [0]         | [✓] No Value               |
|         name: "foo" |                            |
|         age: 30     |                            |
|       ▼ [1]         |                            |
|         name: "bar" |                            |
|   ▼ key3            |                            |
|                     |      [ Apply Changes ]     |
+---------------------+----------------------------+
```
##### 2.3.2a Left Panel (Tree)
Interactive tree structure showing JSON hierarchy
- Collapsible/expandable tree, expanded fully by default
- Expand/collapse icons use Adwaita `zoom-in-symbolic` (collapsed) and `zoom-out-symbolic` (expanded)
- Icons are placed immediately before the node name, not at the far left of the row:
  ```text
  [-] parent
      [-] child
  [+] parent-sibling
  ```
- Single-value array elements (scalars, empty containers) are leaf nodes and do not show an expand/collapse icon
- Indentation is 24px per depth level, applied manually (not via TreeExpander's built-in indent)
- **Movable** divider between `Key` and `Value` columns of TreeView
- User can modify, add, and delete nodes using tool buttons and context menu

##### 2.3.2b Side Panel (Property Inspector)
Detail editor for selected node
- Maintains width at all times
- When a tree node is selected, the side panel displays the controls listed below

-  Field Name
  - Editable display of the current key name
  - For array indices, show the index number (e.g., [0]) 

- Field Type
  - Dropdown selector showing the detected type:
    - string
    - number
    - boolean
    - object
    - array
  - Changing type converts the value accordingly

- Field Value
  - Input widget varies by type:
    - String: Text entry field; auto-adds quotes when saved
    - Number: Text entry with numeric validation
    - Boolean: Toggle
    - Object/Array: Not directly editable, disabled text entry with "[...]" display
  - Input widget is hidden when "No Value" is checked

- No-Value Checkbox
  - Label: "No Value"
  - When checked: hides all field value input widgets
  - Sets the underlying JSON value to null
  - Key remains in the tree and is clickable

- Others
  - `Apply Changes` action button at the bottom, center-aligned (not full width)

- Field Name, Field Type, Field Value, No-Value Checkbox are vertically aligned

### 2.4. Preferences Dialog
Launched from `Preferences` in Hamburger menu, opens a dialog (modal "preferences" window, stays on top)
```text
+--------------------------------------------+
|  Preferences - JSON Editor                 |
+--------------------------------------------+
|                                            |
|  [x] Set as default handler for JSON files |
|                                            |
|  +---------------------------------------+ |
|                                            |
|  [Close]                                   |
+--------------------------------------------+
```

- Toggle to set default handler status
  - Updates checkbox state automatically, based on if app is current default handler
  - Set JSON Editor as the default handler for `.json` files via `xdg-mime
  - Unchecking tries to restore system default (gedit/TextEditor)
  - Users can always change back

### 2.5. Open URL Dialog
Launched from `Open URL` in Hamburger menu, opens a modal dialog for entering a URL
```text
+--------------------------------------------------+
|  Open URL                                        |
+--------------------------------------------------+
|                                                  |
|  Enter URL of JSON file:                         |
|  +--------------------------------------------+  |
|  | https://example.com/data.json              |  |
|  +--------------------------------------------+  |
|                                                  |
|                                    [Cancel] [Open]|
+--------------------------------------------------+
```

- Dialog width: 500px
- Content margins: 18px on all sides
- Entry field: 50 characters wide, placeholder text "https://example.com/data.json"
- Buttons: right-aligned, 8px spacing between them
- Button margins: 18px on all sides, 6px gap above buttons
- Open button has "suggested-action" style (highlighted)
- Enter key submits the dialog

---

## 3. Behaviours

### 3.1 Open
- Open from the hamburger menu
  - launches the File chooser dialog. 
  - user can load local files or files from network share
- Open from command line
  - passing a filename as first argument to app
  - if file is missing or read-protected, app still launches but with error message
- Open URL from the hamburger menu
  - does a web fetch and loads the content of the url. 
  - No code/content is to be executed for security reasons.
  - the url is displayed in the title as filename. 
    - if longer than 40 characters or longer than available area for text, shorten the beginging with ellipsis.
- last part of the path to file (filename and extension) is printed in header on successful open
- For all file-open routes, if parsing fails, error message is shown to user and the situation is logged

### 3.2 Save
- **Direct save**: When the file is a writable local file, Save writes directly without prompting
- **Save As dialog**: Shown only when 
  - the file was loaded from a URL
  - the original file lacks write permissions
  - the user used the `Save As` hamburger menu item
- The chosen destination becomes the current file path for subsequent saves. this reflects in the header as well.

### 3.3 Logging
The application includes a logging system with four levels: DEBUG, INFO, WARN, and ERROR. Logs are written to `stderr` with timestamps and source location.
- **Default level**: INFO
- **Enable debug logging**: Run with `--debug` flag

Log output format:
```text
[2026-06-21 05:01:03] [DEBUG] src/json/json_ops.c:254 (json_op_add_node): Adding node: parent_path='/root' key='new_key' value='new_value'
```
### 3.4 Add Node
When the user clicks add node, he is presented with a dialog here he can specify the name of the new node, the type, and the value
  - The Add Node button is disabled when the selected node's value type is neither object nor array. A child node can only be added to container types.
  - If the selected Node has a type of array, the dialog doesnt show the name input field. On success, a new array element is added.
  - If selected node is not an array, the dialog shows the name input field, and on success a new child node is added

### 3.5 Selection Persistence
  - After Add or Duplicate: the newly created node is selected and highlighted
  - After Delete: selection moves to the parent node, or if that's not available, to the nearest sibling
  - Selection is tracked via JSON XPath and restored after tree refresh
  - Property inspector updates to reflect the newly selected node after any operation
  - Tree view automatically scrolls to make the selected node visible after any selection change

### 3.6 Context Menu
Right-clicking on a node in the tree view opens a context menu with three items: Add Node, Duplicate, and Delete.
  - The right-clicked node becomes selected using the same mechanism as left-click (status bar and side panel update accordingly) before the menu is shown
  - The same enable/disable rules as the toolbar apply:
    - Add Node: enabled only when the selected node is an object or array
    - Duplicate: enabled for all nodes except the root
    - Delete: enabled for all nodes except the root
  - Selecting a menu item performs the same action as the corresponding toolbar button
  - Clicking outside the menu dismisses it without performing any action

### 3.7 Expand / Collapse
Clicking the expand/collapse icon toggles the node's expanded state.
  - Collapsed nodes show `zoom-in-symbolic`; expanded nodes show `zoom-out-symbolic`
  - Leaf nodes (scalars, empty containers) have no expand/collapse icon and cannot be expanded
  - Indentation is applied per depth level so the visual hierarchy is clear
  - The tree is fully expanded by default when a file is loaded

## 4. Install (done by Makefile)
### Install dependencies
```bash
# Debian/Ubuntu
sudo apt-get install libgtk-4-dev

# Fedora/RHEL
sudo dnf install gtk4-devel

# Arch
sudo pacman -S gtk4
```

### Other actions
- Install [json-editor.svg](assets/json-editor.svg) to `<selected prefix>/share/icons/hicolor/scalable/apps/`
- Install [json-editor.desktop](assets/json-editor.desktop) to `<selected prefix>/share/applications/`
- Update executable path in `<selected prefix>/share/applications/json-editor.dekstop`
- run `update-desktop-database <selected prefix>/share/applications/ 2>/dev/null || true`
