# JSON Editor — Stub Completion Plan

## Design Decisions

1. **Path representation**: String path stored in GtkTreeStore (e.g., `$.metadata.tags[0]`)
2. **Tree refresh**: Full rebuild from JsonDocument after any edit
3. **URL/Network I/O**: Use libsoup for HTTP, GIO for network paths
4. **Array Editor**: Up/down arrow buttons instead of drag-to-reorder

## Implementation Phases

### Phase A: Tree Selection Sync
**Goal**: Connect tree selection to side panel and breadcrumb

- Add `COL_PATH` column to GtkTreeStore (string path like `$.key1[0].name`)
- Connect `GtkTreeView::cursor-changed` signal
- On selection: extract path string, look up JsonNode, populate side panel fields
- Update breadcrumb from path string
- Update status bar (node name, JSON path)

**Files**: `tree_view.c/h`, `side_panel.c/h`, `breadcrumb.c/h`, `main.c`

---

### Phase B: Breadcrumb
**Goal**: Clickable navigation path

- Parse path string into segments (`root`, `metadata`, `tags`, `[0]`, `name`)
- Create clickable button for each segment
- On click: navigate tree to that node (expand parents, select)
- Show `depth: N` on right side

**Files**: `breadcrumb.c/h`

---

### Phase C: Apply Changes / Delete Node Buttons
**Goal**: Commit sidebar edits to JSON document

**Apply Changes**:
- Read Field Name, Type, Value from side panel
- Locate node by stored path
- Modify JsonNode (change key, type, value)
- Full tree rebuild
- Preserve selected node: capture XPath before rebuild, restore after
    - If a dict key was renamed, update the path's last segment to the new name
- Preserve scroll position: save vadjustment before rebuild, restore after layout
- Clear unsaved indicator

**Delete Node**:
- Locate node by stored path
- Remove from parent (object or array)
- Full tree rebuild
- Restore selection to parent or nearest sibling
- Update breadcrumb

**Files**: `side_panel.c/h`, `json_ops.c/h`, `tree_view.c/h`

---

### Phase D: Delete / Duplicate Menu Operations
**Goal**: Wire Edit menu items to operations

**Delete**: Same as button (Phase C)

**Duplicate**:
- Copy selected JsonNode
- Insert as sibling in parent
- Full tree rebuild

**Files**: `json_ops.c/h`, `menu.c`

---

### Phase E: File Open/Save Dialogs
**Goal**: Load and save JSON files

**Open**:
- GtkFileChooserDialog with JSON filter
- Read file → parse with json_parser_load_from_data()
- Populate tree + pretty view
- Store file path in JsonDocument

**Save**:
- GtkFileChooserDialog (or re-save to same path)
- Serialize JsonDocument with json_to_string()
- Write file

**Files**: `menu.c`, `json_io.c/h`, `json_model.c/h`

---

### Phase F: Open URL / Open Network
**Goal**: Load JSON from remote sources

**Open URL**:
- Dialog for URL input
- Use libsoup to download
- Parse JSON → populate views

**Open Network**:
- Dialog for network path (SMB/NFS)
- Use GIO `g_file_new_for_uri()` to read
- Parse JSON → populate views

**Files**: `menu.c`, `json_io.c/h`

---

### Phase G: Array Editor
**Goal**: Edit array items in side panel

- When selected node is array: populate ListBox with items
- Each row: index label + value entry + delete button
- Add item button → append to array
- Up/down buttons → reorder items
- Apply Changes commits array edits

**Files**: `side_panel.c/h`, `json_ops.c/h`

---

### Phase H: About Dialog
**Goal**: Application info dialog

- GtkAboutDialog with app name, version, icon, license
- Wire to Help → About menu item

**Files**: new `about.c/h`, `menu.c`

---

## Dependency Graph

```
A (Tree Selection Sync)
├── B (Breadcrumb)
── C (Apply/Delete Buttons)
│   └── D (Delete/Duplicate Menu)
└── G (Array Editor)

E (File Open/Save) — independent
F (Open URL/Network) — independent
H (About Dialog) — independent
```

## Estimated Effort

| Phase | Complexity | Key Challenge |
|-------|-----------|---------------|
| A | Medium | Path string generation during tree population |
| B | Low | Parsing path string into clickable segments |
| C | Medium | Modifying JsonNode in-place, then rebuild |
| D | Low | Copying JsonNode and inserting sibling |
| E | Medium | File chooser integration, serialization |
| F | Medium | libsoup integration, async download |
| G | High | ListBox row management, array mutation |
| H | Low | Standard GtkAboutDialog setup |

## Next Steps

1. Review and approve this plan
2. Implement Phase A (Tree Selection Sync)
3. Proceed through phases in dependency order
