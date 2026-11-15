---
name: smbact-place
description: Put one or several windows at an exact geometry with SMBAct — pixels, percentages, fractions, relative sizes, anchors, grids, gaps, margins, a chosen display — with a dry run first and an honest per-window result. Use for "make Safari 60 % wide on the left and Terminal the rest", "1200×800 in the top right corner", "a 3×2 grid of these windows", "move it 100 px right", "same size on the other monitor". Not for named one-step layouts like left half or maximize (smbact-windows) or saving and restoring a whole setup (smbact-layouts).
---

# SMBAct: exact placement

Verified against smbact-app `93372cf` (SMBAct 2.0.0 build 709, placement phase 1). Start with the `smbact` skill's detection
step and safety rules. Every key: `references/placement-keys.md`; the request, result, statuses, reasons and
warnings as documented by SMBAct: `references/placing.md`. Both are generated from SMBAct's source.

**Uses:** `place_windows` `set_window_frame` `list_windows` `list_displays` `get_capabilities` `focus_window` `smbact-cli place`

## The rule

Report each window's **actual** result. `exact` means within tolerance; `adjusted` means the window refused part of
the request (min size, size increments, the app moved it) and the row says why; never call a layout exact when a row
says otherwise.

## Is placement available?

`get_capabilities.placement` is an object with `enabled: true` → yes. `null`, or no `get_capabilities` at all →
this SMBAct predates placement: fall back to named actions (`smbact-windows`) and say the result is approximate.
`place_windows` is app-only: a standalone `smbact-cli mcp serve` does not have it; `smbact-cli place` needs the
running app (Windows: it prints an `smbact://` link and exits 1, SMBAct does not open those yet).

## Build the request

1. `list_windows` (and `list_displays` when a display is named). Use `window_id` per placement; use `app` / `title`
   only when unique (`on_multiple` defaults to `first` = the frontmost, with a `multiple_matches` warning).
2. One placement per window, at most 32. Geometry, in this order of preference:
   - a grid: `grid: "3x2"`, `cell: "0,0"` (+ `gap`, `margin`);
   - `frame: "0,0,60%,100%"` (x, y, width, height; an empty item keeps that part);
   - `x`, `y`, `width`, `height` separately, with `anchor` (e.g. `top-right`) for corners and edges.
3. Lengths: integer or `px` (native units), `dip`, `%`, `a/b` fraction, `rel:+100` / `rel:50%` relative to the
   current frame. Area: `work` (default, without menu bar / Dock / taskbar), `full`, `screen` (absolute, refuses
   display, anchor, grid, %, dip). Display: index, `main`, `active`, `cursor`, `current`, `next`, `prev`,
   `name:<name>`, `id:<id>` (not on Linux).
4. `fit: "move"` or `"shrink"` keeps the window inside the area; `allow_offscreen` only if the user asked.
5. `state`: `normalize` (default: leaves fullscreen, un-minimizes, un-maximizes, listed in `state_changes`) or
   `keep` (refuses a window that is not normal with `invalid_window_state`).

## Dry run, then apply

| Step | MCP | CLI |
|---|---|---|
| Plan | `place_windows {placements: [...], dry_run: true}` | `smbact-cli place --window-id <id> --frame 0,0,60%,100% --then --window-id <id2> --frame 60%,0,40%,100% --dry-run --json` |
| Apply | the same without `dry_run` | the same without `--dry-run` |
| One window, absolute frame | `set_window_frame {window_id, x, y, width, height}` (screen coordinates, at least one of the four) | `smbact-cli place --window-id <id> --area screen --frame=<x>,<y>,<w>,<h>` |

Show the dry run as a table (window → display → requested frame; `state_dependent` warning = the frame depends on a
state change that the dry run did not make). Apply after the user agrees when more than one window moves.
`simulate` (with `dry_run`) computes against given displays and a frame without touching any window.

## Read the result

`status`: `applied` | `partial` (some rows failed; not an error) | `failed` (isError, `error` from the first failed
row) | `dry_run`. Per row `status`: `exact`, `adjusted` (+ `reasons`: `size_limited_min`, `size_limited_max`,
`size_increment`, `not_resizable`, `position_limited`, `moved_by_app`, `no_effect`, `not_settled`, `unknown`),
`unchanged`, `would_place`, `skipped` (`if_missing: "skip"`), `failed` (+ `error`), `rolled_back`,
`not_attempted`; plus `requested`, `actual`, `delta`, `attempts` (SMBAct retries once). `strict: true` turns
`adjusted` into `failed` with `constraint`. CLI exit: 0 applied / dry run, 3 partial, 1 failed, 2 invalid, 65 no
license.

Report: one line per window — requested, actual, status and the reason in words ("Terminal: 40 % wanted, 41 % —
its width snaps to character cells").

## Placement errors

| Code | Do this |
|---|---|
| `window_on_other_desktop` | macOS: the window is on a hidden desktop. Focusing it switches the user's desktop: ask, then `focus_window` and place again |
| `target_offscreen` | The frame leaves no title bar to grab: fix the geometry (`allow_offscreen` only if asked) |
| `display_not_found` | The message lists the displays: pick one of them |
| `ambiguous_target` / `duplicate_target` | Use window ids; one placement per window |
| `invalid_window_state` | `state: "keep"` on a minimized / fullscreen / maximized window: drop `keep` or ask |
| `window_not_placeable` | A zero-size window: skip it |
| `constraint` | `strict` and the window ended outside tolerance: report, or retry without `strict` |
| `busy`, `rate_limited` | One request at a time |

## Cannot do (don't invent)

- No `focus`, `raise`, `atomic`, `scene` or `key` keys yet (phase 2–3): they are refused.
- No `desktop: "bring"`: a window on another macOS desktop cannot be placed where you are.
- No undo; save the frames first (`smbact-layouts`) if the user may want them back.
- No standalone placement: without the running app there is none.

## Known behaviour

- Placement is verified live on Linux (X11, GNOME, KWin VMs); on macOS and Windows it is built but not verified
  live: check `actual` against `requested` and say so if they differ.
- With several matching windows on macOS and X11 the front-to-back order is unknown (`order_unreliable`): use ids.
- Terminals and editors snap their size to character cells (`size_increment`); some apps have a minimum size.
- Windows: elevated (admin) windows may report success without moving (UIPI).
