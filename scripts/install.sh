#!/usr/bin/env bash
#
# Install the SMBAct skills (skills/*) without the plugin.
#
#   scripts/install.sh                 copy to ~/.claude/skills            (Claude Code, user level)
#   scripts/install.sh --agents        copy to ~/.agents/skills            (Codex, Cursor, Copilot, Gemini)
#   scripts/install.sh --to DIR        copy to DIR (e.g. some-project/.claude/skills or .agents/skills)
#   scripts/install.sh --link …        symlink instead of copying, so the skills track this checkout
#
# An existing copy is replaced only if it is recognisably one of these skills (a symlink or a folder with
# SKILL.md); it is moved aside to <name>.replaced-<time> (the Trash on macOS), never deleted.
# The plugin route (skills + the MCP server) is: claude --plugin-dir <this folder>, or a marketplace.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
LINK=0
while [ $# -gt 0 ]; do
  case "$1" in
    --link) LINK=1 ;;
    --agents) TARGET="$HOME/.agents/skills" ;;
    --to) TARGET="${2:?--to needs a directory}"; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

mkdir -p "$TARGET"
stamp=$(date +%Y%m%d-%H%M%S)
for src in "$ROOT"/skills/*/; do
  name=$(basename "$src")
  dest="$TARGET/$name"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    if [ -L "$dest" ] || [ -f "$dest/SKILL.md" ]; then
      if [ -d "$HOME/.Trash" ]; then aside="$HOME/.Trash/$name.replaced-$stamp"; else aside="$dest.replaced-$stamp"; fi
      mv "$dest" "$aside"
      echo "moved the old $name to $aside"
    else
      echo "refusing to replace $dest: it exists and is not a skill" >&2
      exit 1
    fi
  fi
  if [ "$LINK" = 1 ]; then
    ln -s "${src%/}" "$dest"
  else
    cp -R "${src%/}" "$dest"
    find "$dest" -name '.DS_Store' -exec rm -f {} + 2>/dev/null || true
  fi
  echo "installed $name -> $dest"
done
echo "Done. The skills need SMBAct's MCP server connected, or smbact-cli on PATH (or SMBACT_CLI set)."
