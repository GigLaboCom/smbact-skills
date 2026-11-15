# SMBAct agent skills

Skills that let an AI agent (Claude Code, Codex, Cursor, Copilot — anything that reads
[Agent Skills](https://agentskills.io/specification)) find, arrange, place and move application windows with
[SMBAct](https://smblob.com/products/smbact/), through its MCP server or `smbact-cli`, and diagnose the setup.

Built for SMBAct 2.0.0 from smbact-app master `93372cf` (see `VERIFIED.json`); the matching release build is 709. Status: **v1 draft, not yet run by an
agent against a live SMBAct** (see "Verification").

## Skills

| Skill | For |
|---|---|
| `smbact` | Router: which skill, how to connect and detect the version, safety rules, error / exit codes, files, what SMBAct cannot do |
| `smbact-windows` | One window, named actions: halves, thirds, maximize, next display, focus, minimize all, close |
| `smbact-place` | Exact geometry for one or many windows: px, %, fractions, anchors, grids, dry run, per-window result |
| `smbact-layouts` | Whole arrangements; save, list, restore, delete (stored as `place_windows` requests) |
| `smbact-desktops` | macOS desktops (Spaces): move windows, follow them |
| `smbact-doctor` | Read-only diagnosis and client configuration |

## Install

**Claude Code plugin** (skills + the MCP server over stdio, no token):

```bash
claude --plugin-dir /path/to/agent-skills          # try it
# or from a marketplace that lists this folder: /plugin install smbact@smbact
```

The plugin starts `bin/smbact-cli mcp serve`, which finds the CLI inside SMBAct.app (`/Applications`,
`~/Applications`, Spotlight). If SMBAct lives elsewhere (e.g. a `*.noindex` folder), set
`export SMBACT_CLI=/path/to/SMBAct.app/Contents/Resources/bin/smbact-cli` before starting the client.
Linux: put `smbact-cli` on PATH. Windows has no CLI hand-over: connect over HTTP instead (see `smbact-doctor`).

**Skills only** (any agent; connect SMBAct's MCP yourself or use the CLI):

```bash
scripts/install.sh            # ~/.claude/skills
scripts/install.sh --agents   # ~/.agents/skills  (Codex, Cursor, Copilot, Gemini)
scripts/install.sh --to DIR   # one project
scripts/install.sh --link …   # symlink, tracks this checkout
```

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

Regenerate after SMBAct changes:

```bash
cargo build --release --locked --manifest-path <smbact-app>/cli/Cargo.toml --target-dir /tmp/smbact-cli-target
node scripts/gen.mjs --repo <smbact-app> --cli /tmp/smbact-cli-target/release/smbact-cli
```

Then re-read the SKILL.md files the change touches and update their "Verified against" line.

## Verification

| Check | State |
|---|---|
| Generator + drift check | runs; see `VERIFIED.json`. Also passes with the `smbact-cli` shipped in build 709 |
| Surface of build 709 (macOS, read only) | `tools/list` 13 tools + `close_window` (off) = 14; `get_capabilities` and `get_version` answer |
| Format: `claude plugin validate` | passed, nothing to report (2026-11-15) |
| Triggering and safety evals (`evals/prompts.md`) | written, **not run** |
| Live tasks (Linux Xvfb, macOS, Windows) | **not run**: needs a master build and a test display (spec D-8) |

## License

MIT for the skill texts and scripts (confirmed by the owner, 2026-11-14).
