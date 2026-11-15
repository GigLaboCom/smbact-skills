# Move and resize windows on Wayland from an AI agent or a script

**Short answer:** on a GNOME or KDE Plasma Wayland session, `wmctrl` and `xdotool` cannot move native Wayland
windows. [SMBAct](https://smblob.com/products/smbact/) can, through its own GNOME Shell extension (GNOME 46–51) or
KWin script (Plasma 6). Its local MCP server then lets Claude Code, Codex, Cursor or a plain `curl` script list,
tile, move and resize every window, Wayland and XWayland alike.

## Why wmctrl and xdotool stop working on Wayland

Under X11 any client may read the window list (`_NET_CLIENT_LIST`) and move other programs' windows. Wayland removed
that on purpose: only the compositor knows and moves windows. `wmctrl` and `xdotool` still talk X11, so on a Wayland
session they see and move only XWayland windows. Native Wayland windows (GNOME apps, Firefox, Qt 6 apps, recent
Electron apps) are invisible to them. On GNOME 49 and later (Ubuntu 25.10, 26.04) there is no X11 session to switch
back to.

The way through is code inside the compositor. SMBAct ships a small GNOME Shell extension and a KWin script (open
source: [GigLaboCom/smbact-shell](https://github.com/GigLaboCom/smbact-shell), GPL-2.0-or-later) that list, move,
resize and focus windows on SMBAct's behalf.

## Setup

1. Install SMBAct for Linux x64 (AppImage or rpm) from the [download page](https://smblob.com/products/smbact/download/).
2. GNOME: click **Install** in SMBAct's banner and log out once, so GNOME Shell loads the extension
   ([guide](https://smblob.com/products/smbact/documentation/gnome-wayland/)). KDE Plasma: SMBAct loads its KWin
   script itself ([guide](https://smblob.com/products/smbact/documentation/kde-plasma-wayland/)).
3. In SMBAct, open the **MCP** page, turn the server on and copy the token.
4. Connect your agent over HTTP (`smbact-cli` is not shipped for Linux, so there is no stdio hand-over):

   ```bash
   claude mcp add --transport http smbact http://127.0.0.1:5057/mcp --header "Authorization: Bearer <token>"
   ```

   Other clients: [README › Connect a client](../README.md#connect-a-client).
5. Install the skills (`npx skills add GigLaboCom/smbact-skills`, or `scripts/install.sh`), so the agent knows the
   recipes and the safety rules.

Then ask: "put Firefox on the left half and the terminal on the right", "move Files to the other monitor",
"a 2×2 grid of my editor windows".

## From a script, without an agent

The server speaks MCP's Streamable HTTP in its stateless JSON form: one JSON-RPC request per `POST`, no session.
That makes it callable from a shell script, which is the closest thing to `wmctrl -r … -e` on Wayland:

```bash
TOKEN=...   # from SMBAct's MCP page; keep it out of your shell history and repos
mcp() {
  curl -s http://127.0.0.1:5057/mcp \
    -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"$1\",\"arguments\":$2}}"
}

mcp list_windows '{"fields":["id","app","title","frame"]}'
mcp window_action '{"window_id":"<id from list_windows>","action":"left-half"}'
mcp place_windows '{"placements":[{"app":"Firefox","frame":"0,0,60%,100%"},{"bundle_id":"kitty","frame":"60%,0,40%,100%"}]}'
# on Linux, bundle_id matches the window class (WM_CLASS / app id) that list_windows reports as "class"
```

A rough map for `wmctrl` / `xdotool` users:

| X11 habit | SMBAct tool |
|---|---|
| `wmctrl -l` | `list_windows` |
| `wmctrl -r <win> -e 0,x,y,w,h`, `xdotool windowmove` / `windowsize` | `set_window_frame`, or `place_windows` with `"area": "screen"` |
| `wmctrl -a <win>`, `xdotool windowactivate` | `focus_window` |
| `wmctrl -r <win> -b add,maximized_vert,maximized_horz` | `window_action` `maximize` |
| a tiling script with `xrandr` math | `place_windows` with `%`, fractions, `grid` + `cell`, `gap`, `display` |

Arguments of every tool: [`skills/smbact/references/tools.md`](../skills/smbact/references/tools.md).

## What to expect

- **Coordinates** on GNOME and KDE Wayland are logical pixels, top-left origin. `get_capabilities` says which units the
  session uses.
- **Results are read back:** `place_windows` reports a row per window (`exact`, `adjusted` with reasons, `failed`),
  because a compositor may refuse a size (minimum sizes, size increments).
- **Desktops:** moving windows between workspaces is macOS-only for now (`list_desktops`, `move_window_to_desktop`).
- **License:** tool calls need SMBAct's 14-day trial or a license (one-time, from €14.99, 3 devices in any mix of
  Linux, macOS and Windows). `get_capabilities` and `get_version` work without one.
- **Not supported:** other Wayland compositors (Sway, Hyprland, …). On those SMBAct manages XWayland windows only.
