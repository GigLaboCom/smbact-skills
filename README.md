<p align="center">
  <img src=".claude-plugin/icon.png" alt="SMBAct" width="96" height="96">
</p>

<h1 align="center">SMBAct agent skills: window management for AI agents</h1>

<p align="center">
  <b>Let Claude Code, Codex, Cursor or Copilot arrange your windows.</b><br>
  Agent Skills and a Claude Code plugin for the MCP server built into
  <a href="https://smblob.com/products/smbact/">SMBAct</a>, a window manager for macOS, Windows and Linux.
</p>

<p align="center">
  <img alt="macOS" src="https://img.shields.io/badge/macOS-supported-black">
  <img alt="Windows" src="https://img.shields.io/badge/Windows-supported-blue">
  <img alt="Linux" src="https://img.shields.io/badge/Linux-X11%20%C2%B7%20GNOME%20%26%20KDE%20Wayland-orange">
  <img alt="MCP" src="https://img.shields.io/badge/MCP-14%20tools-8a2be2">
  <img alt="Agent Skills" src="https://img.shields.io/badge/Agent%20Skills-6-2ea44f">
  <img alt="License" src="https://img.shields.io/badge/skills-MIT-lightgrey">
</p>

---

**smbact-skills** teaches an AI agent to find, focus, tile, move and resize application windows. You say "editor on
the left two thirds, terminal on the right, browser on the other monitor", and the agent does it through
[SMBAct](https://smblob.com/products/smbact/)'s MCP server or `smbact-cli`. It works on macOS, on Windows and on
Linux, including GNOME and KDE Plasma on Wayland, where `wmctrl` and `xdotool` cannot move windows. The skills follow
the open [Agent Skills](https://agentskills.io/specification) format, so Claude Code, OpenAI Codex, Cursor, GitHub
Copilot and Gemini CLI can all load them.

**Contents:** [Install](#install) · [What you can ask](#what-you-can-ask) · [Skills](#skills) ·
[Setup per OS](#setup-per-os) · [Connect a client](#connect-a-client) · [MCP tools](#the-14-mcp-tools) ·
[Safety](#safety) · [Pricing](#pricing-and-license) · [FAQ](#faq) · [How it is built](#how-it-is-built-and-how-to-keep-it-right)

## Install

You need [SMBAct](https://smblob.com/products/smbact/download/) installed and running (14-day trial, then a paid
license; see [Pricing](#pricing-and-license)).

**Claude Code plugin** (the skills plus the MCP server over stdio, no token):

```text
/plugin marketplace add GigLaboCom/smbact-skills
/plugin install smbact@smbact
```

**Any agent** with the [skills](https://github.com/vercel-labs/skills) installer (Claude Code, Codex, Cursor,
Copilot, Gemini CLI and others):

```bash
npx skills add GigLaboCom/smbact-skills
```

**From a checkout:**

```bash
git clone https://github.com/GigLaboCom/smbact-skills.git && cd smbact-skills
scripts/install.sh            # ~/.claude/skills
scripts/install.sh --agents   # ~/.agents/skills  (Codex, Cursor, Copilot, Gemini)
scripts/install.sh --to DIR   # one project
scripts/install.sh --link …   # symlink, tracks this checkout
claude --plugin-dir .         # or try the whole plugin without installing it
```

Only the plugin connects the MCP server for you, and only on macOS (see [Setup per OS](#setup-per-os)). With the
skills alone, [connect SMBAct's MCP server](#connect-a-client) to your client yourself.

## What you can ask

Plain requests. The router skill picks the job skill, the agent lists the windows first and does a dry run before
it moves several at once.

| You say | What happens |
|---|---|
| "Put Chrome on the left half and Slack on the right" | two named layout actions (`smbact-windows`) |
| "Send the terminal to the other monitor" | `move_window_to_display` |
| "Make Safari 60 % wide on the left and Terminal the rest" | one exact placement for two windows (`smbact-place`) |
| "A 3×2 grid of my editor windows with 10 px gaps" | grid placement, dry run first |
| "1200×800 in the top right corner of the LG display" | exact frame on a named display |
| "Set up my coding layout" / "Save this arrangement as coding" / "Bring back my morning layout" | saved layouts (`smbact-layouts`) |
| "Send this window to Desktop 2 and go with it" | macOS Spaces (`smbact-desktops`) |
| "Minimize everything" | `minimize_all`, only when asked in so many words |
| "My client does not see SMBAct" / "How do I connect SMBAct to Cursor?" | read-only diagnosis (`smbact-doctor`) |

More prompts, including the ones that must *not* trigger a skill and the safety cases: [`evals/prompts.md`](evals/prompts.md).

## Skills

| Skill | For |
|---|---|
| [`smbact`](skills/smbact/SKILL.md) | Router: which skill, how to connect and detect the version, safety rules, error / exit codes, files, what SMBAct cannot do |
| [`smbact-windows`](skills/smbact-windows/SKILL.md) | One window, named actions: halves, thirds, fourths, sixths, eighths, center, maximize, fullscreen, next display, focus, minimize all, close |
| [`smbact-place`](skills/smbact-place/SKILL.md) | Exact geometry for one or many windows: px, %, fractions, anchors, grids, gaps, margins, dry run, per-window result |
| [`smbact-layouts`](skills/smbact-layouts/SKILL.md) | Whole arrangements across displays; save, list, restore, delete |
| [`smbact-desktops`](skills/smbact-desktops/SKILL.md) | macOS desktops (Spaces): move windows, follow them |
| [`smbact-doctor`](skills/smbact-doctor/SKILL.md) | Read-only diagnosis and client configuration |

How a request flows:

```text
agent ──▶ smbact (router) ──▶ smbact-windows | -place | -layouts | -desktops | -doctor
                                   │
                                   ▼
                 SMBAct MCP server (stdio via smbact-cli, or HTTP 127.0.0.1:5057)
                                   │
                                   ▼
        SMBAct window engine ──▶ macOS Accessibility · Win32 · X11 · GNOME Shell extension · KWin script
```

## Setup per OS

| OS | What the agent talks to | Notes |
|---|---|---|
| **macOS** (Apple Silicon, Intel) | `smbact-cli mcp serve` (stdio), shipped inside `SMBAct.app` | The plugin finds it in `/Applications`, `~/Applications` or through Spotlight. Elsewhere (e.g. a `*.noindex` folder): `export SMBACT_CLI=/path/to/SMBAct.app/Contents/Resources/bin/smbact-cli`. SMBAct needs Accessibility; Screen Recording for titles of other desktops. |
| **Windows** (x64) | HTTP, `http://127.0.0.1:5057/mcp` with a bearer token | No CLI hand-over on Windows. Turn on the server on SMBAct's MCP page and copy the token from there. |
| **Linux** (x64; X11, GNOME 46–51 and KDE Plasma 6 on Wayland) | HTTP, as on Windows | On Wayland SMBAct sees every window through its [GNOME Shell extension or KWin script](https://github.com/GigLaboCom/smbact-shell): [GNOME](https://smblob.com/products/smbact/documentation/gnome-wayland/), [KDE Plasma](https://smblob.com/products/smbact/documentation/kde-plasma-wayland/). Details: [docs/wayland.md](docs/wayland.md). |

Install guides: [macOS](https://smblob.com/products/smbact/documentation/install-macos/),
[Windows](https://smblob.com/products/smbact/documentation/install-windows/), all downloads on the
[download page](https://smblob.com/products/smbact/download/).

## Connect a client

The plugin does this for you on macOS. Otherwise register SMBAct's MCP server in your client. `<cli>` is the full path
of `smbact-cli` (macOS: `/Applications/SMBAct.app/Contents/Resources/bin/smbact-cli`); `<token>` comes from SMBAct's
MCP page.

| Client | stdio (macOS) | HTTP (Windows, Linux, or any OS) |
|---|---|---|
| Claude Code | `claude mcp add smbact -- <cli> mcp serve` | `claude mcp add --transport http smbact http://127.0.0.1:5057/mcp --header "Authorization: Bearer <token>"` |
| Cursor, VS Code (`.mcp.json`) | `{"mcpServers": {"smbact": {"command": "<cli>", "args": ["mcp", "serve"]}}}` | `{"mcpServers": {"smbact": {"type": "http", "url": "http://127.0.0.1:5057/mcp", "headers": {"Authorization": "Bearer <token>"}}}}` |
| OpenAI Codex (`~/.codex/config.toml`) | `[mcp_servers.smbact]` `command = "<cli>"` `args = ["mcp", "serve"]` | |
| Claude Desktop | `{"mcpServers": {"smbact": {"command": "<cli>", "args": ["mcp", "serve"]}}}` | through `npx -y mcp-remote http://127.0.0.1:5057/mcp` |

The server binds 127.0.0.1 only, checks `Host` and `Origin`, and asks for the token by default. Trouble: ask the agent
"why doesn't my client see SMBAct?" and the `smbact-doctor` skill runs the checks.

## The 14 MCP tools

| Tool | Does |
|---|---|
| `list_windows`, `get_window` | Open windows: id, app, title, frame, display, state; filters by app, title, class, display |
| `list_displays` | Displays with their frame and work area |
| `window_action` | One of 46 named actions: halves, thirds, fourths, quarters, sixths, eighths, center, move to an edge, maximize, fullscreen, minimize, restore, next / previous display |
| `place_windows` | One to 32 windows at any geometry in one request: px, dip, %, fractions, anchors, grids, gaps, margins, dry run, a result per window |
| `set_window_frame` | One window at an exact frame |
| `move_window_to_display` | To another monitor, keeping its place and size relative to the work area |
| `focus_window`, `minimize_all`, `close_window` | Focus; minimize all; close (off by default, with a confirmation dialog) |
| `list_desktops`, `move_window_to_desktop` | macOS Spaces |
| `get_capabilities`, `get_version` | What this install supports; work without a license |

Every argument, generated from SMBAct's source: [`skills/smbact/references/tools.md`](skills/smbact/references/tools.md).
The 46 actions: [`skills/smbact-windows/references/actions.md`](skills/smbact-windows/references/actions.md). The
placement keys: [`skills/smbact-place/references/placement-keys.md`](skills/smbact-place/references/placement-keys.md).

## Safety

The router skill holds the rules every job skill follows:

- It never moves, resizes or closes the agent's own terminal or IDE unless you name it.
- It closes only after you confirm, naming the windows. `close_window` stays off unless you switch it on yourself.
- It does a dry run before it moves more than one window, and reports what happened (`adjusted`, `failed` and why),
  not what was asked.
- It never prints the MCP token, the license or settings files, and never copies window titles into repo files.
- When SMBAct is unreachable it runs the diagnosis. It does not fall back to AppleScript, `xdotool` or synthetic keys.

## Pricing and license

- **The skills and scripts in this repo:** MIT.
- **SMBAct** is a paid app: a 14-day trial with every feature, then a one-time license from €14.99. One license
  covers 3 devices in any mix of macOS, Windows and Linux. Prices: [smblob.com/products/smbact](https://smblob.com/products/smbact/).
- MCP tool calls need the trial or a license. `get_capabilities` and `get_version` answer without one, so an agent
  can tell you what is missing.

## FAQ

**Can Claude Code move and resize my windows?**
Yes, with SMBAct running and this plugin installed (or SMBAct's MCP server added to Claude Code). Claude lists the
windows, then places them with named actions or exact frames.

**Is there a window manager MCP server for macOS?**
SMBAct has one built in: 14 tools for listing, focusing, tiling, placing and moving windows, plus macOS Spaces. It
runs on 127.0.0.1 and needs no cloud service.

**Does it work on Windows and Linux?**
Yes. On Windows and Linux the agent connects over HTTP with a token. On Linux it works on X11 and on GNOME and KDE
Plasma Wayland sessions.

**Does it work on Wayland, where wmctrl and xdotool don't?**
Yes, on GNOME 46–51 and KDE Plasma 6. SMBAct moves windows through its own GNOME Shell extension or KWin script, so
native Wayland windows are included. See [docs/wayland.md](docs/wayland.md).

**Does it work with Cursor, Codex, Copilot or Gemini CLI?**
The skills are plain Agent Skills (`SKILL.md`), and the MCP server is standard MCP (stdio or Streamable HTTP). Any
client that reads either can use them. Snippets: [Connect a client](#connect-a-client).

**Can the agent click buttons or type into apps?**
No. SMBAct arranges windows; it does not launch apps, type, or read window content. For that, use a UI-automation MCP
server next to it.

**Can it save and restore window layouts?**
Yes: "save this as coding", "bring back coding". The `smbact-layouts` skill stores each layout as a `place_windows`
request and replays it.

**Is it safe to give an agent control of my windows?**
The rules are in [Safety](#safety). SMBAct adds its own: per-tool switches on its MCP page, `close_window` off by
default, a confirmation dialog for closing, and a black list of apps it never touches.

## How it is built (and how to keep it right)

- **One router, one skill per job.** Not a skill per tool: the router holds what every skill needs (connection,
  detection, safety, codes), the job skills hold recipes with an MCP form and a CLI form each, how to read the
  result, "Cannot do (don't invent)" and "Known behaviour".
- **Nothing in `references/` is written by hand.** `scripts/gen.mjs` generates it from SMBAct's own sources:
  `tools.manifest.json`, `actions-catalog.manifest.json`, `placement.manifest.json`, the error table in
  `docs/mcp.md`, and `--help` of every `smbact-cli` subcommand. SKILL.md text links to them instead of copying
  tool arguments.
- **Drift check.** `node scripts/gen.mjs --repo <smbact-app> --cli <smbact-cli built from it> --check` exits 1 when
  a reference is stale or a SKILL.md claim fails: the frontmatter (name = folder, description ≤ 1024), each
  `**Uses:**` line (only existing tools and subcommands), the router's exit-code table (against `cli/src/main.rs`
  and `cli/src/place.rs`) and error-code table (against `docs/mcp.md`). Run it in CI next to `npm run test:catalog`.
- **Detect, don't assume.** Every build reports version `2.0.0`; the skills read `tools/list` and
  `get_capabilities` and degrade on older builds.

Built for SMBAct 2.0.0 from smbact-app master `93372cf` (see `VERIFIED.json`); the matching release build is 709.
Regenerate after SMBAct changes:

```bash
cargo build --release --locked --manifest-path <smbact-app>/cli/Cargo.toml --target-dir /tmp/smbact-cli-target
node scripts/gen.mjs --repo <smbact-app> --cli /tmp/smbact-cli-target/release/smbact-cli
```

Then re-read the SKILL.md files the change touches and update their "Verified against" line.

## Verification

Status: **v1 draft, not yet run by an agent against a live SMBAct.**

| Check | State |
|---|---|
| Generator + drift check | runs; see `VERIFIED.json`. Also passes with the `smbact-cli` shipped in build 709 |
| Surface of build 709 (macOS, read only) | `tools/list` 13 tools + `close_window` (off) = 14; `get_capabilities` and `get_version` answer |
| Format: `claude plugin validate` | passed, nothing to report (2026-11-15) |
| Triggering and safety evals (`evals/prompts.md`) | written, **not run** |
| Live tasks (Linux Xvfb, macOS, Windows) | **not run**: needs a master build and a test display (spec D-8) |

## Links

- SMBAct: [product page](https://smblob.com/products/smbact/) · [download](https://smblob.com/products/smbact/download/) ·
  [documentation](https://smblob.com/products/smbact/documentation/) · [roadmap](https://smblob.com/products/smbact/roadmap/)
- Comparisons: [SMBAct vs Rectangle](https://smblob.com/products/smbact/compare/smbact-vs-rectangle/) ·
  [vs Magnet](https://smblob.com/products/smbact/compare/smbact-vs-magnet/) ·
  [vs Moom](https://smblob.com/products/smbact/compare/smbact-vs-moom/) ·
  [all alternatives](https://smblob.com/products/smbact/smbact-alternatives/)
- [GigLaboCom/smbact-shell](https://github.com/GigLaboCom/smbact-shell): the GNOME Shell extension and KWin script
  behind Wayland support (GPL-2.0-or-later)

## License

MIT for the skill texts and scripts (confirmed by the owner, 2026-11-14). SMBAct itself is commercial software.
