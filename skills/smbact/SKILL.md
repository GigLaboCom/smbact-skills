---
name: smbact
description: Start here for anything done with SMBAct, the window manager for macOS, Windows and Linux, through its MCP server or smbact-cli. Holds which SMBAct skill to use, how to connect (MCP tools, else smbact-cli), how to find out what the installed version supports, the safety rules, error and exit codes, its files, and what SMBAct cannot do. Use when the user mentions SMBAct or smbact-cli, asks to move, arrange, focus, place or close application windows, or when an SMBAct tool or command fails. Not for windows of the agent's own browser automation or for terminal multiplexer panes.
---

# SMBAct (router)

SMBAct arranges application windows: named layouts (halves, thirds, …), exact frames, several windows at once,
other displays, macOS desktops (Spaces). An agent reaches it two ways: the **MCP server** (tools such as
`list_windows`) or **`smbact-cli`** on the shell, which hands its commands over to the running app.

Verified against smbact-app `93372cf` (SMBAct 2.0.0 build 709). The tool, action, key and CLI tables in `references/` are
generated from that source by `scripts/gen.mjs`; read them, never work from memory.

**Uses:** `get_capabilities` `get_version` `list_windows` `smbact-cli mcp status` `smbact-cli windows` `smbact-cli displays`

## Pick the skill

| The user wants | Skill |
|---|---|
| A named layout for one window: left half, maximize, center, next display, focus it, minimize all, close | `smbact-windows` |
| An exact geometry: "60 % left", "1200×800 at the top right", a grid, several windows in one request | `smbact-place` |
| A whole arrangement: "my coding setup", save the current layout, bring it back later | `smbact-layouts` |
| macOS desktops (Spaces): send a window to Desktop 2, follow it there | `smbact-desktops` |
| Setup and trouble: SMBAct not reachable, a tool missing, connect a client (Claude Code, Codex, Cursor, Claude Desktop) | `smbact-doctor` |

## First: connect and detect (every session, before acting)

Do not assume the version: every build says `2.0.0`. Detect what this install has.

1. **MCP tools present?** Look for SMBAct tools in your tool list (the client may prefix them, e.g.
   `mcp__smbact__list_windows`). If present:
   - `get_capabilities` exists → call it (no license needed). Read `tools[].enabled`, `license.allowed`,
     `platform`, `coordinates`, `window_actions`, `placement` (null = no `place_windows`), `notes`. Call
     `get_version` for `version` and `variant`.
   - `get_capabilities` is missing → an older build (before the action catalog, e.g. 2.0.0 build 659): use only the
     tools in the list, `list_windows` takes only `app` / `title`, there is no `place_windows`,
     `set_window_frame`, `get_window` or `move_window_to_display`. Say once that the user's SMBAct is older.
   - A write tool can be missing because the user switched it off: `get_capabilities.tools[].enabled` tells which.
2. **No MCP tools → the CLI.** `smbact-cli --version` and `smbact-cli mcp status --json`
   (`smbact_running`, `app.channel`). With SMBAct running, CLI commands go through the app (macOS, Linux).
   The CLI may not be on PATH: on macOS it is `SMBAct.app/Contents/Resources/bin/smbact-cli`; the plugin's `bin/`
   provides a wrapper, `SMBACT_CLI` overrides it.
3. **SMBAct not running, macOS only:** the CLI acts alone (`--standalone` behaviour): `windows`, `displays`,
   `run`, `focus`, `minimize-all`. No `place`, no desktops. Never `close` this way (rule 2).
4. **Nothing works** → `smbact-doctor`. Never fall back to AppleScript, `xdotool`, keyboard shortcuts or other
   window tools to do SMBAct's job.

## Safety rules (every skill that acts follows them)

1. **Not the agent's own window.** Never move, resize, minimize or close the terminal or IDE the agent runs in
   unless the user names it. `window_id: "active"` is usually that window: use it only when the user says "this
   window" and means a window that is not the agent's. Nothing in SMBAct marks the agent's window: the window that
   was `active` when you started is the best guess; ask when unsure.
2. **Close only on an explicit confirmation** in the conversation that names the windows. "Close application"
   closes every window of that app: say so first. Never switch `close_window` on or `confirmClose` off. Never close
   through a standalone `smbact-cli close` (no confirmation dialog there).
3. **`minimize_all` only when asked** in so many words ("minimize everything"), never as a side effect.
4. **Never print or write** the MCP token, `mcp.json`, `settings.json`, the output of `smbact-cli mcp token`,
   `smbact-cli mcp snippets` (holds the live token) or `smbact-cli license status` (holds the license owner's
   email). Do not copy window titles into repo files or commit messages: titles can hold private documents and chats.
5. **No settings changes without asking**: `smbact-cli mcp config …`, tool switches, port, token.
6. **Dry run first** for any change to more than one window: `place_windows` with `dry_run`, show the plan, then
   apply.
7. **Report what happened, not what was asked**: `adjusted` / `failed` rows with their reasons, `followed: false`
   with its `note`. On Windows a "done" on an elevated (admin) window may be false (UIPI): say so.

## Windows and ids

- Ids are `"<pid>:<handle>"` from `list_windows` (`0:<window>` on X11 when the app sets no `_NET_WM_PID`), or
  `"active"`. Ids die with the window: re-list after an app restarts.
- List first, then act by `window_id`. Target by `app` / `title` only when the match is unique or the user said
  "all" / "the frontmost": with several matches SMBAct silently takes the frontmost (`multiple_matches` warning).
  If several match, ask the user which (name app, title, display), never just ids.
- SMBAct's own windows are not listed and refused (`window_not_allowed`). Black-listed apps are listed with
  `black_listed: true` and refused by layout tools: leave them alone.
- Frames: top-left origin; macOS points, Windows and X11 physical pixels, GNOME / KWin logical pixels
  (`get_capabilities.coordinates`).

## Errors (MCP)

A failed call returns `isError: true` and `{"error": "<code>", "message": "…"}`. Full list: `references/errors.md`.

<!-- error-codes -->
| Code | Do this |
|---|---|
| `invalid_params` | Fix the argument the message names; do not retry unchanged |
| `tool_unavailable` | The tool is off or unknown: tell the user it can be switched on (SMBAct › MCP page, or `smbact-cli mcp config tool.<name>=on`); do not switch it yourself |
| `license_required` | No license or trial: tell the user; only `get_capabilities` / `get_version` work |
| `window_not_found` | The window is gone or its id changed: `list_windows` again, retry once with the new id |
| `window_not_allowed` | It is an SMBAct window: pick another |
| `window_black_listed` | The app is on SMBAct's black list: tell the user, do not work around it |
| `declined` | The user refused the close dialog: stop |
| `app_not_ready` | SMBAct is starting: wait 2 s, retry once |
| `timeout` | Retry once; then `smbact-doctor` |
| `unsupported` | Not available on this OS / version: say so |
| `busy` | Placement queue full: send requests one at a time |
| `rate_limited` | Over 10 placement requests a second: slow down |
| `engine_unavailable` | SMBAct's window engine is restarting or failed: wait, then `smbact-doctor` |
<!-- /error-codes -->

Placement codes (`window_on_other_desktop`, `target_offscreen`, `constraint`, …): `smbact-place`.

## Exit codes (smbact-cli)

<!-- exit-codes -->
| Code | Meaning |
|---|---|
| `0` | Done (also: skipped a black-listed or SMBAct window; `place` applied or dry run) |
| `1` | Error: failed, no SMBAct for `place`, channel failure, tool switched off |
| `2` | Usage error or invalid request (`place`: also when every failed row is `invalid_params` / `display_not_found`) |
| `3` | `place`: partial, some placements failed |
| `64` | Unknown action, or one the CLI does not implement |
| `65` | No active license or trial |
| `77` | Accessibility permission missing (standalone, macOS) |
<!-- /exit-codes -->

## Files

| File | What | Rule |
|---|---|---|
| userData: macOS `~/Library/Application Support/SMBAct`, Linux `~/.config/SMBAct`, Windows `%APPDATA%\SMBAct` | SMBAct's settings folder (both build variants share it) | Read nothing there except through the CLI |
| `<userData>/mcp.json` | MCP settings and the token (mode 600) | Never print, copy or upload |
| `<userData>/smbact-cli.sock` | The CLI's channel to the running app (macOS, Linux) | Its presence = the app is up |
| `<userData>/logs/app.smbact.log` | SMBAct's log | Quote only the relevant lines |
| `SMBAct.app/Contents/Resources/bin/smbact-cli` | The CLI (bundled on macOS only) | Linux / Windows: a separate download |

## Cannot do (don't invent)

- No CLI subcommand for desktops, `move-to-display`, `get-version` / capabilities, scenes or URLs;
  `smbact-cli actions` has no `--json`. These exist only as MCP tools (or not at all).
- No saved scenes, `run_scene` or `smbact://` links yet; the placement keys `scene`, `focus`, `raise`,
  `atomic`, `key` are not accepted. Saved layouts live in `smbact-layouts`' own files.
- No undo of a placement. The `restore` action returns one window to its frame before the last SMBAct action.
- No launching apps, typing into windows or reading window content. No creating desktops.
- Desktops (Spaces) are macOS only; on macOS a window on a hidden desktop cannot be placed (`window_on_other_desktop`).
- Windows: no hand-over (`smbact-cli` cannot reach the app), `place` prints an `smbact://` link and exits 1.
- Nothing identifies the agent's own window (rule 1).

## Known behaviour

- The server's `instructions` text says "on this Mac" on every OS.
- `minimize_all` and `focus_window` work across apps; black-listed apps are skipped by `minimize_all`.
- Read-only tools are always listed; a write tool switched off disappears from `tools/list`.

## References

| File | Holds |
|---|---|
| `references/tools.md` | every MCP tool: arguments, types, defaults, annotations, switch, app_only, license |
| `references/errors.md` | every MCP error code with its meaning |
| `references/cli.md` | `smbact-cli --help` of every subcommand, verbatim |
