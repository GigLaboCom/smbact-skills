#!/usr/bin/env python3
"""Saved window arrangements for SMBAct, stored as place_windows requests.

    presets.py capture NAME [--app APP]... [--windows FILE --displays FILE]
    presets.py show NAME          # the place_windows request (JSON) to send, dry_run first
    presets.py cli NAME           # the same as a smbact-cli place command line
    presets.py list
    presets.py delete NAME        # moved aside as NAME.json.deleted-<time>, not erased

capture reads `smbact-cli windows --json` and `smbact-cli displays --json` (read-only), or the JSON an agent saved
from MCP list_windows / list_displays (--windows / --displays). Minimized, fullscreen and black-listed windows are
left out. Each window becomes one placement: app (+ title only when the app has several windows), display by name,
frame in pixels inside the display's work area, fit "shrink", if_missing "skip".

File: {"name", "saved", "displays", "windows": [{app, desktop}], "request": {"v": 1, "placements": [...]}}.
"request" is sent as is (it is the future scenes.json body). Store (mode 600):
macOS ~/Library/Application Support/smbact-skills/presets, Linux $XDG_CONFIG_HOME/smbact-skills/presets,
Windows %APPDATA%\\smbact-skills\\presets. Window titles stay in this local store only.
Stdlib only.
"""
import datetime
import json
import os
import pathlib
import platform
import shlex
import subprocess
import sys


def store() -> pathlib.Path:
    home = pathlib.Path.home()
    system = platform.system()
    if system == "Darwin":
        base = home / "Library/Application Support"
    elif system == "Windows":
        base = pathlib.Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
    else:
        base = pathlib.Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    p = base / "smbact-skills" / "presets"
    p.mkdir(parents=True, exist_ok=True)
    os.chmod(p, 0o700)
    return p


def safe_name(name: str) -> str:
    if not name or not all(c.isalnum() or c in "-_" for c in name):
        sys.exit("preset name: letters, digits, - and _ only")
    return name


def cli_json(*args):
    cli = os.environ.get("SMBACT_CLI", "smbact-cli")
    out = subprocess.run([cli, *args, "--json"], capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"{cli} {' '.join(args)} --json failed ({out.returncode}): {out.stderr.strip()}")
    return json.loads(out.stdout)


def load(path):
    data = json.loads(pathlib.Path(path).read_text())
    return data.get("windows", data) if isinstance(data, dict) and "windows" in data else data


def capture(name, apps, windows_file, displays_file):
    windows = load(windows_file) if windows_file else cli_json("windows")
    displays = load(displays_file) if displays_file else cli_json("displays")
    by_index = {d["index"]: d for d in displays}
    rows = [w for w in windows if not (w.get("minimized") or w.get("fullscreen") or w.get("black_listed"))]
    # A window larger than its display is a backdrop (e.g. Finder's desktop window), not something to arrange.
    def backdrop(w):
        d = by_index.get(w["display"])
        return d is None or w["frame"]["width"] > d["frame"]["width"] or w["frame"]["height"] > d["frame"]["height"]
    skipped = [w for w in rows if backdrop(w)]
    rows = [w for w in rows if not backdrop(w)]
    if apps:
        wanted = {a.lower() for a in apps}
        rows = [w for w in rows if w["app"].lower() in wanted]
    per_app = {}
    for w in rows:
        per_app[w["app"].lower()] = per_app.get(w["app"].lower(), 0) + 1
    # Several windows of one app are told apart by title; an untitled one among them cannot be targeted.
    untitled = [w for w in rows if per_app[w["app"].lower()] > 1 and not w.get("title")]
    rows = [w for w in rows if w not in untitled]
    if skipped or untitled:
        print(f"left out: {len(skipped)} backdrop window(s), {len(untitled)} untitled window(s) of apps with several windows")
    if not rows:
        sys.exit("no windows to capture")
    placements, meta = [], []
    for w in rows:
        d = by_index[w["display"]]
        vf, f = d["visible_frame"], w["frame"]
        p = {"app": w["app"]}
        if per_app[w["app"].lower()] > 1 and w.get("title"):
            p["title"] = w["title"]
        p.update({"display": f"name:{d['name']}", "area": "work",
                  "frame": f"{f['x'] - vf['x']},{f['y'] - vf['y']},{f['width']},{f['height']}",
                  "fit": "shrink", "if_missing": "skip"})
        placements.append(p)
        meta.append({"app": w["app"], "desktop": w.get("desktop")})
    if len(placements) > 32:
        sys.exit(f"{len(placements)} windows: a request holds at most 32; capture fewer (--app)")
    doc = {"name": name, "saved": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "displays": [{"index": d["index"], "name": d["name"], "frame": d["frame"]} for d in displays],
           "windows": meta, "request": {"v": 1, "placements": placements}}
    path = store() / f"{safe_name(name)}.json"
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    os.chmod(path, 0o600)
    desktops = sorted({m["desktop"] for m in meta if m["desktop"] is not None})
    print(f"saved {len(placements)} window(s) as '{name}' ({path})")
    if len(desktops) > 1:
        print(f"note: the windows are on desktops {desktops}; a restore places only those on the showing desktop")


def read(name):
    path = store() / f"{safe_name(name)}.json"
    if not path.exists():
        sys.exit(f"no preset '{name}' (presets.py list)")
    return json.loads(path.read_text())


def as_cli(req):
    parts = ["smbact-cli", "place"]
    for i, p in enumerate(req["placements"]):
        if i:
            parts.append("--then")
        for k, v in p.items():
            parts += [f"--{k.replace('_', '-')}", str(v)]
    return " ".join(shlex.quote(x) for x in parts) + " --dry-run --json"


def main(argv):
    if len(argv) >= 3 and argv[1] == "capture":
        apps, wf, df, rest = [], None, None, argv[3:]
        while rest:
            flag, val = rest[0], (rest[1] if len(rest) > 1 else None)
            if flag == "--app" and val:
                apps.append(val)
            elif flag == "--windows" and val:
                wf = val
            elif flag == "--displays" and val:
                df = val
            else:
                sys.exit(__doc__)
            rest = rest[2:]
        if bool(wf) != bool(df):
            sys.exit("--windows and --displays go together")
        capture(argv[2], apps, wf, df)
    elif len(argv) == 3 and argv[1] == "show":
        print(json.dumps(read(argv[2])["request"], indent=2, ensure_ascii=False))
    elif len(argv) == 3 and argv[1] == "cli":
        print(as_cli(read(argv[2])["request"]))
    elif len(argv) == 2 and argv[1] == "list":
        for p in sorted(store().glob("*.json")):
            d = json.loads(p.read_text())
            print(f"{p.stem}\t{len(d['request']['placements'])} window(s)\tsaved {d['saved']}")
    elif len(argv) == 3 and argv[1] == "delete":
        path = store() / f"{safe_name(argv[2])}.json"
        if not path.exists():
            sys.exit(f"no preset '{argv[2]}'")
        path.rename(path.with_name(f"{path.name}.deleted-{datetime.datetime.now():%Y%m%d-%H%M%S}"))
        print(f"moved aside: {argv[2]}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
