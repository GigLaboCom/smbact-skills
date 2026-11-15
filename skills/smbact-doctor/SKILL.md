---
name: smbact-doctor
description: Diagnose SMBAct read-only and connect it to an AI client — is it installed and running, is its MCP server on, which tools are switched off, version and capabilities, license state without printing it, macOS permissions, the log, and the client configuration for Claude Code, Codex, Cursor, VS Code or Claude Desktop. Use when SMBAct tools are missing or failing, "SMBAct does not respond", "my client does not see SMBAct", "how do I connect SMBAct to Cursor". Not for arranging windows.
---

# SMBAct doctor

Verified against smbact-app `93372cf` (SMBAct 2.0.0 build 709). Everything here reads; it changes nothing unless the user asks
for that one change. Follow the `smbact` skill's safety rules: never print the token, `mcp.json`, `settings.json`,
`smbact-cli mcp snippets` or `smbact-cli license status` output.

**Uses:** `get_capabilities` `get_version` `smbact-cli mcp status` `smbact-cli mcp config` `smbact-cli license status`

## The rule

Diagnose before advising, and report each check as ✓ / ✗ with the evidence in one line.

## Checks

1. **MCP connected?** If SMBAct tools are in your tool list: `get_version` (`version`, `variant`) and
   `get_capabilities` (`license.allowed`, `engine.state`, `engine.backend`, `tools[].enabled`, `notes`). No
   `get_capabilities` → an older SMBAct (before 2.0.0's action catalog): say so.
2. **CLI found?** `smbact-cli --version`. macOS: `SMBAct.app/Contents/Resources/bin/smbact-cli`
   (`/Applications`, `~/Applications`, or wherever the user keeps it; `SMBACT_CLI` overrides). Linux / Windows: a
   separate download.
3. **App and server:** `smbact-cli mcp status --json` → `settings.enabled`, `settings.port`,
   `settings.requireToken`, `settings.tools` (false = switched off), `smbact_running`, `app.channel`,
   `port_in_use`, `url`. `smbact-cli mcp config` (no arguments) shows the same settings.
   - `enabled: false` → the HTTP server is off (SMBAct › MCP page). stdio (`smbact-cli mcp serve`) works anyway.
   - `smbact_running: false` → start SMBAct; until then a standalone `mcp serve` has 11 of the 14 tools (no
     desktops, no `place_windows`), and on Linux / Windows it cannot move windows at all.
   - `port_in_use: true` while SMBAct is not running → another program holds the port.
4. **License:** `smbact-cli license status >/dev/null 2>&1; echo $?` — only the exit code: 0 = licensed or in
   trial, 65 = not. Discard the output unread (it holds the owner's email); over MCP, `get_capabilities.license`
   (`allowed`, `state`, `reason`) is enough.
5. **macOS permissions:** `smbact-cli windows` exits 77 → Accessibility is missing for SMBAct / smbact-cli
   (System Settings › Privacy & Security › Accessibility). Titles of other-desktop windows missing or previews
   absent → Screen Recording (same panel). The log line `screen recording: granted|denied` says which.
6. **Log:** `<userData>/logs/app.smbact.log` (macOS `~/Library/Application Support/SMBAct/logs/`). Quote only the
   relevant `[warn]` / `[error]` lines; never the whole file.

## Connect a client

Write the snippet yourself with a placeholder; never paste `smbact-cli mcp snippets` output (it holds the live
token). Prefer stdio: no port, no token, it goes through the running app (macOS; Linux with the CLI installed).

| Client | stdio (recommended) | HTTP (`requireToken` on → the user adds the token) |
|---|---|---|
| Claude Code | `claude mcp add smbact -- <cli> mcp serve` | `claude mcp add --transport http smbact http://127.0.0.1:5057/mcp --header "Authorization: Bearer <token>"` |
| Cursor / VS Code (`.mcp.json`) | `{"mcpServers": {"smbact": {"command": "<cli>", "args": ["mcp", "serve"]}}}` | `{"mcpServers": {"smbact": {"type": "http", "url": "http://127.0.0.1:5057/mcp", "headers": {"Authorization": "Bearer <token>"}}}}` |
| Codex (`~/.codex/config.toml`) | `[mcp_servers.smbact]` with `command = "<cli>"`, `args = ["mcp", "serve"]` | — (use stdio) |
| Claude Desktop | `{"mcpServers": {"smbact": {"command": "<cli>", "args": ["mcp", "serve"]}}}` | via `npx -y mcp-remote http://127.0.0.1:5057/mcp` |

`<cli>` = the full path from check 2. Windows has no hand-over: use HTTP with the token there. The user registers
the server; do not run `claude mcp add` or edit client configs unless asked. The token: the user copies it from
SMBAct's MCP page (masked until Show) — never fetch it for them with `smbact-cli mcp token`.

## Cannot do (don't invent)

- No `smbact-cli doctor`, `version --json`, `capabilities` or `snippets --redact` subcommand.
- No reading of `mcp.json` / `settings.json` to "check" them: use `mcp status --json`.
- No granting macOS permissions: only the user can, in System Settings.

## Known behaviour

- The default port is 5057 and SMBAct never moves to another port.
- The HTTP server binds 127.0.0.1 only and refuses other Host / Origin headers (403).
- `mcp serve --http` refuses to start while SMBAct runs (the app already serves HTTP).
- The Codex snippet above is not produced by SMBAct and was not verified against Codex's current docs.
