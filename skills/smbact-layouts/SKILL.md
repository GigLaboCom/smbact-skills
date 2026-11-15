---
name: smbact-layouts
description: Set up, save and restore whole window arrangements with SMBAct — several apps across displays at once ("my coding setup: editor left two thirds, terminal right, browser on the LG"), "save this layout as coding", "bring back my morning layout", list or delete saved layouts. Use when the request is about an arrangement of several windows, or about saving and restoring one. Not for one window (smbact-windows), not for a single exact geometry (smbact-place), not for moving windows between macOS desktops (smbact-desktops).
---

# SMBAct: arrangements and saved layouts

Verified against smbact-app `93372cf` (SMBAct 2.0.0 build 709, placement phase 1). Start with the `smbact` skill's detection
step and safety rules. Keys: `references/placement-keys.md` (generated). Placing itself follows `smbact-place`.

**Uses:** `list_windows` `list_displays` `place_windows` `get_capabilities` `smbact-cli windows` `smbact-cli displays` `smbact-cli place`

## The rule

Nothing moves before the user has seen the plan. Every arrangement is a dry run first, then one apply, then a report
of each window's actual result.

## Set up an arrangement the user describes

1. `list_windows`, `list_displays`. Map each named app to one window (ask if an app has several and the user did
   not say which). Apps that are not open: list them; do not launch them.
2. Write one `place_windows` request: one placement per window, `window_id` targets, `grid` / `frame` / `anchor`
   geometry, `display` by name or index (see `smbact-place`).
3. `dry_run: true` → show a table: window, display, requested frame, warnings. Windows on another macOS desktop
   fail with `window_on_other_desktop`: offer `smbact-desktops` (moves them here) or leave them out.
4. On a yes, send the same request without `dry_run`. Report each row (`exact` / `adjusted` + reason / `failed`).

## Save the current arrangement

Saved layouts are files of this skill, not SMBAct settings (SMBAct's own scenes are not built yet). A saved layout
holds the exact `place_windows` request that restores it.

| Step | Command |
|---|---|
| Save (CLI present) | `python3 scripts/presets.py capture coding [--app Code --app Terminal …]` |
| Save (MCP only) | write the `list_windows` and `list_displays` results to two temp files, then `python3 scripts/presets.py capture coding --windows w.json --displays d.json` |
| List | `python3 scripts/presets.py list` |
| Delete (asks first) | `python3 scripts/presets.py delete coding` (moved aside, not erased) |

Each window becomes a placement: `app` (+ `title` only when that app has several windows), `display: "name:<name>"`,
`area: "work"`, `frame` in pixels inside the work area, `fit: "shrink"` (a smaller display still fits),
`if_missing: "skip"` (a closed app does not fail the rest). Minimized, fullscreen and black-listed windows are left
out. The store is local (macOS `~/Library/Application Support/smbact-skills/presets/`, Linux
`~/.config/smbact-skills/presets/`, Windows `%APPDATA%\smbact-skills\presets\`, files mode 600): titles stay there,
never in a repo. Without Python, write the same JSON yourself (format in the script's docstring).

## Restore a saved arrangement

1. `python3 scripts/presets.py show coding` → the request. With MCP: `place_windows` with it plus
   `dry_run: true`. With the CLI: `python3 scripts/presets.py cli coding` prints the `smbact-cli place … --then …
   --dry-run --json` line.
2. Show the plan; rows `skipped` = app not open, `failed` with `display_not_found` = that display is not connected
   (offer `display: "main"` instead).
3. Apply without `dry_run`; report per window.

## Cannot do (don't invent)

- No SMBAct-side scenes, `run_scene`, `list_scenes` or `smbact://scene` links yet; no `scene` key.
- No restoring windows onto hidden macOS desktops; no launching closed apps; no restoring minimized or fullscreen
  state (those windows are not saved).
- No more than 32 windows in one request.

## Known behaviour

- Titles change (documents, tabs): a saved `title` that no longer matches makes that row `skipped`; re-save.
- Several windows of one app saved without titles all match the same app: the first placement takes the frontmost.
- Terminals and editors snap to character cells: expect `adjusted` with `size_increment`.
- On macOS and Windows placement is not verified live yet: compare `actual` with `requested`.
