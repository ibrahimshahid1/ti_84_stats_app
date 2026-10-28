#!/usr/bin/env python3
"""m2test - shared helpers for the STA 431 Midterm II simulator tests (PLAN.md section 5).

    from m2test import ROOT, SRC, INIT, m, i, k, run, screen, after, num

    m(x)        {'menu': x}: x is a 1-based int OR the item text (exact match, else the one item that
                starts with x). Prefer text; never hard-code BACK positions: m('BACK').
    i(v)        Input action. Negative numbers use the (-) key '⁻'; Fraction -> 'p/q'; str passed through.
    k(code)     getKey action (105 ENTER, 45 CLEAR, 24 LEFT, 26 RIGHT, 25 UP, 34 DOWN).
    run(prog, actions, init=None, max_steps=3_000_000, allow_lists=False, ends=True)
                runs prog in the simulator and asserts: no error, leaks == 0, no display warnings,
                ended 'end'/'return' (when ends), the user's INIT variables preserved, and (unless
                allow_lists) no ʟM2* list left behind. Returns the tisim Result.
    screen(r, title)        stripped rows of the LAST pause screen whose row 1 starts with title.
    after(r, title, label)  stripped text of the row after the row equal to label on that screen.
    num(s)                  '⁻1/36', '1ᴇ⁻5', '.25', '2', '-3' -> float.

Expected values in tests come from sympy or fractions.Fraction computed in the test, never from a
run of the app.
"""
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(ROOT / "tools"))
from tisim import Sim  # noqa: E402

# User data that every program must leave alone (graph equations and the built-in lists).
INIT = {"Y1": "X²+1", "Y9": "X+3", "L₁": [91, 92], "L₂": [71, 72]}

ENTER, CLEAR, LEFT, RIGHT, UP, DOWN = 105, 45, 24, 26, 25, 34


def m(x):
    """Menu action: 1-based position or item text (prefer text)."""
    return {"menu": x}


def _typed(v):
    if isinstance(v, str):
        return v
    if isinstance(v, Fraction):
        s = str(abs(v.numerator)) if v.denominator == 1 else f"{abs(v.numerator)}/{v.denominator}"
        return ("⁻" if v < 0 else "") + s
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, (int, float)):
        s = repr(abs(v)) if isinstance(v, float) else str(abs(v))
        if s.endswith(".0"):
            s = s[:-2]
        if "e" in s:                                   # 1e-05 -> 1ᴇ⁻5 (the EE key)
            mant, ex = s.split("e")
            ex = int(ex)
            s = mant + "ᴇ" + ("⁻" if ex < 0 else "") + str(abs(ex))
        return ("⁻" + s) if v < 0 else s
    return str(v)


def i(v):
    """Input action: what the student types, then ENTER."""
    return {"input": _typed(v)}


def k(code):
    """getKey action."""
    return {"key": code}


def run(prog, actions, init=None, max_steps=3_000_000, allow_lists=False, ends=True):
    start = dict(INIT)
    if init:
        start.update(init)
    r = Sim(str(SRC)).run(prog, actions, max_steps=max_steps, init_vars=start)
    assert r.error is None, f"{prog}: {r.error}\n{r.text[-6000:]}"
    assert r.leaks == 0, f"{prog}: {r.leaks} block frames leaked\n{r.text[-4000:]}"
    assert not r.warnings, f"{prog}: display warnings {r.warnings}"
    if ends:
        assert r.ended_reason in ("end", "return"), f"{prog}: ended {r.ended_reason}\n{r.text[-4000:]}"
    for key, value in INIT.items():
        if init and key in init:
            continue
        assert r.var(key) == value, f"{prog}: user variable {key} changed to {r.var(key)!r}"
    if not allow_lists:
        left = sorted(n for n in r.vars["lists"] if n.startswith("M2"))
        assert not left, f"{prog}: private lists left behind: {left}"
    return r


def _pauses(r, title):
    return [s for s in r.screens if s["event"] == "pause" and s["rows"][0].strip().startswith(title)]


def screen(r, title):
    """Stripped rows of the LAST pause screen whose first row starts with title."""
    found = _pauses(r, title)
    assert found, f"no pause screen titled {title!r}\n{r.text[-6000:]}"
    return [row.strip() for row in found[-1]["rows"]]


def after(r, title, label):
    """Stripped text of the row right after the row equal to label on screen(r, title)."""
    rows = screen(r, title)
    assert label in rows, f"label {label!r} not on screen {title!r}: {rows}"
    j = rows.index(label)
    assert j + 1 < len(rows), f"label {label!r} is the last row of {title!r}"
    return rows[j + 1]


def num(s):
    """Parse a TI display number: '⁻1/36', '1ᴇ⁻5', '.25', '2'."""
    t = str(s).strip().replace("⁻", "-").replace("ᴇ", "e").replace(" ", "")
    if "/" in t:
        a, b = t.split("/")
        return float(Fraction(a) / Fraction(b))
    return float(t)
