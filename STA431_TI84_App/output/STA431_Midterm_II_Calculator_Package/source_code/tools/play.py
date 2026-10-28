#!/usr/bin/env python3
"""
play.py - drive the STAM2 suite step by step, like pressing keys on the calculator.

A session is a saved list of keypresses. Each command replays the whole list from the
start of the program (the simulator is deterministic) and shows what is on screen now.

  python tools/play.py new  S [PROGRAM]     start session S (default program STAM2)
  python tools/play.py add  S KEY ...       press more keys, then show the new screens
  python tools/play.py undo S [N]           drop the last N keys (default 1), show screens
  python tools/play.py show S [--all]       show screens since the last key (or all)
  python tools/play.py keys S               print the saved key list (copy into a report)

KEY syntax
  m3            choose item 3 of the menu on screen
  m:TEXT        choose the menu item whose text is TEXT (or the one item starting with TEXT),
                e.g. m:SOLVERS  m:BACK  "m:HOMEWORK PRACTICE" (quote texts that contain spaces)
  i:TEXT        type TEXT at an input prompt and press ENTER, e.g. i:{1,2,3}  i:3/4
  k105          a getKey code (105 ENTER, 45 CLEAR, 24 LEFT, 26 RIGHT, 25 UP, 34 DOWN)

Typing rules match the TI keypad: the (-) key is "⁻" (i:⁻1, not i:-1), squares can be
"²" or "^2", e is "𝑒^(", and comparisons are the real tokens < > ≤ ≥ = ≠.
Pause screens continue automatically (as if ENTER was pressed).
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tisim import Sim, render_snapshot  # noqa: E402

STORE = Path(os.environ.get("PLAY_DIR", ROOT / ".play"))


def parse_key(k):
    if k.startswith("i:"):
        return {"input": k[2:]}
    if k.startswith("m:") and len(k) > 2:
        return {"menu": k[2:]}
    if k.startswith("m") and k[1:].isdigit():
        return {"menu": int(k[1:])}
    if k.startswith("k") and k[1:].isdigit():
        return {"key": int(k[1:])}
    raise SystemExit(f"bad key {k!r}: use m<n>, m:<item text>, i:<text>, or k<code>")


def key_text(a):
    if "input" in a:
        return "i:" + a["input"]
    if "menu" in a:
        if isinstance(a["menu"], str):
            return "m:" + a["menu"]
        return f"m{a['menu']}"
    return f"k{a['key']}"


def load(name):
    path = STORE / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"no session {name!r}; run: play.py new {name}")
    return path, json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    STORE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def show(data, since=1, everything=False):
    res = Sim(str(ROOT / "src")).run(data["program"], data["keys"], max_steps=5_000_000)
    screens = res.screens
    # screens that consumed a key carry a "response"; start after the one for key len-since
    consumed = [i for i, s in enumerate(screens) if s.get("response")]
    start = 0
    if not everything and since and len(consumed) >= since:
        start = consumed[-since]
    out = [f"== {len(data['keys'])} keys so far: " + " ".join(key_text(a) for a in data["keys"])]
    out += [render_snapshot(i, screens[i]) for i in range(start, len(screens))]
    tail = f"== ended: {res.ended_reason}"
    if res.ended_reason == "out_of_actions":
        tail = "== waiting for your next key"
    if res.error:
        tail += f"\n== CALCULATOR ERROR: {res.error}"
    out.append(tail)
    print("\n".join(out))


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, name = argv[1], argv[2]
    path = STORE / f"{name}.json"
    if cmd == "new":
        data = {"program": argv[3] if len(argv) > 3 else "STAM2", "keys": []}
        save(path, data)
        show(data, everything=True)
    elif cmd == "add":
        path, data = load(name)
        new = [parse_key(k) for k in argv[3:]]
        data["keys"] += new
        save(path, data)
        show(data, since=len(new) or 1)
    elif cmd == "undo":
        path, data = load(name)
        n = int(argv[3]) if len(argv) > 3 else 1
        data["keys"] = data["keys"][:-n] if n else data["keys"]
        save(path, data)
        show(data)
    elif cmd == "show":
        _, data = load(name)
        show(data, everything="--all" in argv)
    elif cmd == "keys":
        _, data = load(name)
        print(" ".join(key_text(a) for a in data["keys"]))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
