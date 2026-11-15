---
name: smbact-windows
description: Find, focus and arrange single windows with SMBAct's named actions — halves, thirds, fourths, quarters, sixths, eighths, center, move to an edge, maximize, fullscreen, minimize, restore, next or previous display, move to a named display, minimize all, close a window or an application. Use for "put Chrome on the left half", "maximize the terminal", "send Slack to the other monitor", "show me the Figma window", "minimize everything", "close that window". Not for exact sizes or percentages (smbact-place), whole arrangements (smbact-layouts) or macOS desktops (smbact-desktops).
---

# SMBAct: one window, named actions

Verified against smbact-app `93372cf` (SMBAct 2.0.0 build 709). Start with the `smbact` skill's detection step; follow its
safety rules. Action ids and what each does: `references/actions.md` (generated from SMBAct's action catalog).

**Uses:** `list_windows` `get_window` `focus_window` `window_action` `move_window_to_display` `minimize_all` `close_window` `list_displays` `smbact-cli windows` `smbact-cli displays` `smbact-cli run` `smbact-cli focus` `smbact-cli minimize-all` `smbact-cli close`

## The rule

Act on a window you have identified by id, and check the result frame. "Done" is the frame in the result (or a new
`list_windows`), not the absence of an error.

## Find the window

| | MCP | CLI |
|---|---|---|
| By app / title | `list_windows {app: "Chrome"}` (also `title`, `class`, `display`, `include_minimized`, `fields`) | `smbact-cli windows --app Chrome --json` (also `--title`) |
| One window, all fields | `get_window {window_id}` | — |
| Displays | `list_displays` → `index`, `name`, `main`, `frame`, `visible_frame`, `scale` (+ `id` macOS / Windows) | `smbact-cli displays --json` |

Older builds (no `get_capabilities`): `list_windows` takes only `app` and `title`; no `get_window`.

Pick one window: prefer `on_current_desktop: true` (macOS), then `active`. Still several → ask (app, title,
display). Skip `black_listed: true`.

## Recipes

| Want | MCP | CLI (always `--no-repeat`) |
|---|---|---|
| Named layout | `window_action {window_id, action: "left-half"}` | `smbact-cli run left-half --window-id <id> --no-repeat` |
| Focus / un-minimize | `focus_window {window_id}` | `smbact-cli focus <id>` |
| Next / previous display | `window_action {window_id, action: "next-display"}` | `smbact-cli run next-display --window-id <id> --no-repeat` |
| A named display | `move_window_to_display {window_id, display: "LG ULTRAFINE"}` (index, name or `"main"`) | — (MCP only) |
| Minimize everything (only when asked) | `minimize_all {display: "all"}` (`active`, `main`) | `smbact-cli minimize-all --display all` |
| Close (after confirmation) | `close_window {window_id, scope: "window"}` | `smbact-cli close <id>` — only when `smbact-cli mcp status --json` shows `smbact_running: true` |
| Close the whole app (after confirmation) | `close_window {window_id, scope: "application"}` | `smbact-cli close <id> --app` — same condition |

- `window_action` returns `before` and `after` frames and `state`. Compare `after` with the display's
  `visible_frame`; report in words ("Chrome: left half of the LG").
- `move_window_to_display` keeps the window's relative frame; returns `moved`, `before`, `after`, `warnings`.
- To use a layout on another display: move it there first, then apply the layout.
- `maximize`, `maximize-height` and `fullscreen` toggle: read `maximized` / `fullscreen` first.
- `restore` returns the window to its frame before the last SMBAct action on it.

## Cycling

MCP `window_action` never cycles: the action you send is the action applied. The hotkey path cycles (same window,
same action, < 2 s → next step in `references/actions.md` "Cycle"): that is `smbact-cli run <action>` without
`--window-id`, and also the standalone CLI with `--window-id`. Always pass `--no-repeat` on the CLI.

## Close

1. Get an explicit yes that names the window(s). For `scope: "application"` say that every window of that app
   closes (shared hosts such as Java, Python or Electron apps close only the target).
2. If `close_window` is missing or answers `tool_unavailable`, it is switched off (the default): tell the user how
   to switch it on; do not do it yourself.
3. SMBAct shows its own Close / Cancel dialog when `confirmClose` is on; `declined` = the user cancelled.
4. Result: `closed`, `window`, `app`, `title`, `close_requests`, `close_failed`, `target_only`
   (`shared_host` | `no_app_name` | `not_listed`). Report failures.

## Cannot do (don't invent)

- No exact sizes or percentages here (that is `place_windows`, `smbact-place`).
- No CLI subcommand for `move_window_to_display` or `get_window`.
- The desktop actions (`next-desktop`, `desktop-2`, …) are not `window_action` actions: `smbact-desktops`.
- No undo beyond `restore`.

## Known behaviour

- `active` is usually the agent's own terminal or IDE (`smbact` rule 1).
- Linux: after `next-display` / `move_window_to_display` a maximized window comes out un-maximized; on Wayland the
  `after` frame of `window_action` can be stale (it reads once after 300 ms): re-read with `list_windows`; a
  tiled window reads `maximized: false`.
- Windows: an action on an elevated (admin) window can be reported done while nothing moved (UIPI); an app that is
  not per-monitor DPI aware can get the wrong size across displays with different scales.
- macOS: windows on a hidden desktop have no accessibility element, so a polite close cannot reach them.
- `focus_window` and `close_window` do not check the black list: check `black_listed` yourself.
