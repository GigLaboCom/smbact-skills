---
name: smbact-desktops
description: Move windows between macOS desktops (Mission Control Spaces) with SMBAct, optionally going with the window, and see which windows are on which desktop. Use for "send this window to Desktop 2", "put all Slack windows on the second desktop", "move it to the other Space and switch there", "what is on my other desktops". macOS only. Not for moving a window to another monitor (smbact-windows) and not for arranging windows on the current desktop (smbact-place).
---

# SMBAct: macOS desktops (Spaces)

Verified against smbact-app `93372cf` (SMBAct 2.0.0 build 709). Start with the `smbact` skill's detection step and safety
rules. Tool arguments: `references/tools.md` (generated).

**Uses:** `list_desktops` `list_windows` `move_window_to_desktop` `focus_window` `get_capabilities`

## The rule

"Desktop N" is a Mission Control desktop of one display, not a monitor. When the user says "desktop" but means a
monitor ("put it on the LG desktop"), use `smbact-windows` (`move_window_to_display`) and say which you did.

## Available?

- macOS 15–27 (26 and 27 measured, 15 by the owner's decision), with SMBAct's window engine. Elsewhere both tools
  answer `unsupported` and `get_capabilities.notes` says "macOS only for now": tell the user, stop.
- Both tools are app-only: through MCP, or `smbact-cli mcp serve` while SMBAct runs (it proxies). There is **no**
  `smbact-cli` subcommand for desktops; a standalone `mcp serve` does not list them.
- Out of the verified macOS range the call answers `unsupported` with the reason (e.g. "bridged move not verified on
  macOS 14"); in SMBAct's popup the desktop rows are greyed out with the same reason.

## Steps

1. `list_desktops` → per display: `display` (index as in `list_displays`), `desktops: [{desktop, current}]`,
   `current_desktop`, `fullscreen_apps`.
2. `list_windows` → each window's `desktop` and `on_current_desktop` (when known).
3. The target desktop must exist on that display; if not, say "add one in Mission Control" instead of calling.
4. `move_window_to_desktop {window_id, desktop, display?, follow?}`:
   - leave `follow` out unless the user asked: the user's SMBAct setting applies (Settings › Desktops: Stay, the
     default, or Go with the window);
   - `follow: true` only for "and go there" / "switch to it";
   - a fullscreen window leaves full screen first (`left_fullscreen: true`): tell the user.
5. Read the result: `window`, `app`, `desktop`, `display`, `ms`, `left_fullscreen`, `followed`, `note`.
   With `follow: true` and `followed: false`, or a `note` like "macOS kept the focus on another window there", say
   so; one `focus_window` on the window fixes the focus.
6. Several windows: one call each, then one `list_windows` to confirm; report moved / not moved.

## Errors

| Answer | Meaning |
|---|---|
| `unsupported` | Not macOS, out of the verified range, engine or helper off, capability off: say the message |
| `invalid_params` | No such desktop ("add one in Mission Control"), only one desktop, unknown display |
| `failed` | A fullscreen window did not leave full screen: try once more |
| `window_not_found` | Re-list; SMBAct already re-looks an id up for 0.5 s after a desktop switch |

## Cannot do (don't invent)

- No creating, removing or renaming desktops; no switching desktops without a window (focus a window there instead).
- No placing a window on a hidden desktop (`place_windows` answers `window_on_other_desktop`): move it here first,
  or focus it (which switches the user's desktop — ask first).
- No desktops on Windows or Linux; no CLI subcommand; no AppleScript or keyboard-shortcut fallback.

## Known behaviour

- After `follow`, macOS may give the focus to another window on the target desktop; SMBAct re-checks and re-focuses
  up to twice and reports it in `note`.
- The pushed window list refreshes every 2 s; read with `list_windows` (fresh) rather than trusting an old list.
- Windows on a hidden desktop have no accessibility element: they cannot be closed politely from here.
- Without Screen Recording, titles of other-desktop windows come from accessibility and may be shorter.
