#!/usr/bin/env python3
"""Simulator tests for STACNT (SPEC section 4, tools A-F) + oracle cases from oracles/oracles.json.

Run:  $PY tests/test_STACNT.py [--show ID]   (prints PASS/FAIL per case + total; exit 1 on any failure)

Every case drives the real menus/prompts through the action queue, always leaves through BACK, and checks:
  * the expected values appear on the rendered result screens (exact rows, leading "0." normalized to ".")
  * res.error is None, res.leaks == 0, no display-policy warnings (nothing wrapped/clipped)
  * BACK returns to the caller: the run goes through a driver program "prgmSTACNT" followed by a marker
    statement, the Return line of STACNT is executed, and the marker runs afterwards. (tisim reports a
    Return inside a called program as ended_reason "end" of the driver; running STACNT directly its Return
    also shows as "end" because tisim swallows _Return in run_program. Both are accepted, and the
    "return to caller" property is checked with the marker instead.)
  * all ʟCN… lists are deleted after BACK
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from tisim import Sim  # noqa: E402

SRC = os.path.join(ROOT, "src")
ORACLES = json.load(open(os.path.join(ROOT, "oracles", "oracles.json"), encoding="utf-8"))
ORC = {o["id"]: o for o in ORACLES}

MARK = 4242
_counter = [0]
RETURN_LINE = None
with open(os.path.join(SRC, "STACNT.txt"), encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if line.strip() == "Return":
            RETURN_LINE = i

results = []
SHOW = sys.argv[sys.argv.index("--show") + 1] if "--show" in sys.argv else None


def norm(s):
    return re.sub(r"(?<![0-9])0\.(?=[0-9])", ".", s.rstrip())


def run(actions, direct=False):
    sim = Sim(SRC)
    if direct:
        return sim.run("STACNT", actions=actions, max_steps=3_000_000)
    _counter[0] += 1
    name = "TCN%03d" % _counter[0]
    sim.add_program(name, "prgmSTACNT\n%d→X" % MARK)
    return sim.run(name, actions=actions, max_steps=3_000_000)


def pauses(res):
    return [s for s in res.screens if s["event"] == "pause"]


def screen_with(res, marker):
    """first pause snapshot that has a row containing marker (normalized)"""
    for s in pauses(res):
        if any(norm(marker) in norm(r) for r in s["rows"]):
            return s
    return None


def rows_of(s):
    return [norm(r) for r in s["rows"]] if s else []


class Case:
    def __init__(self, cid):
        self.cid = cid
        self.fails = []

    def check(self, cond, msg):
        if not cond:
            self.fails.append(msg)

    def row(self, res, marker, want, label=None):
        """screen identified by marker must contain the exact row `want`"""
        s = screen_with(res, marker)
        if s is None:
            self.fails.append(f"{label or want}: no screen containing {marker!r}")
            return
        self.check(norm(want) in rows_of(s), f"{label or want}: row {want!r} not on screen {rows_of(s)}")

    def anywhere(self, res, text, label=None):
        ok = any(norm(text) in norm(r) for s in res.screens for r in s["rows"])
        self.check(ok, f"{label or text}: {text!r} not shown anywhere")

    def common(self, res, direct=False):
        self.check(res.error is None, f"error: {res.error}")
        self.check(res.leaks == 0, f"leaks={res.leaks}")
        self.check(not res.warnings, f"display warnings: {res.warnings[:3]}")
        self.check(res.ended_reason in ("return", "end"), f"ended_reason={res.ended_reason}")
        cov = res.coverage.get("STACNT", [])
        self.check(RETURN_LINE in cov, "Return line of STACNT not executed")
        if not direct:
            self.check(res.var("X") == MARK, "control did not come back to the caller after BACK")
        left = [k for k in res.vars.get("lists", {}) if k.startswith("CN")]
        self.check(not left, f"lists not deleted on BACK: {left}")

    def done(self, res=None):
        if SHOW and SHOW == self.cid and res is not None:
            print(res.text)
        results.append((self.cid, not self.fails, self.fails))
        print(("PASS " if not self.fails else "FAIL ") + self.cid + ("" if not self.fails else "  " + " | ".join(self.fails)))


def d9(o, key):
    """Str9 display of an oracle value"""
    disp = o.get("display", {})
    if key in disp:
        return disp[key][0]
    return str(o["expected"][key]).replace("-", "⁻")


def s(v):
    return str(v).replace("-", "⁻")


# ------------------------------------------------------------------------------------------ tool A
def val_after(rows, prefix):
    for r in rows:
        if r.startswith(prefix):
            tail = r[len(prefix):]
            if tail.startswith("TOO BIG"):
                return "TOO BIG"
            tail = tail.split("=")[-1] if "=" in tail else tail
            return tail.split()[0] if tail.split() else ""
    return None


def test_A(cid):
    o = ORC[cid]
    c = Case(cid)
    N, R = o["inputs"]["N"], o["inputs"]["R"]
    exp = o["expected"]
    if "result" in exp:        # reject, then enter a valid pair
        res = run([{"menu": 1}, {"input": str(N)}, {"input": str(R)}, {"input": "5"}, {"input": "2"}, {"menu": 7}])
        c.anywhere(res, "n AND r MUST BE WHOLE")
        c.row(res, "n=5  r=2", "nCr=5!/(2!3!)=10", "valid retry after reject")
        c.common(res)
        c.done(res)
        return
    res = run([{"menu": 1}, {"input": str(N)}, {"input": str(R)}, {"menu": 7}])
    sc = rows_of(screen_with(res, f"n={N}  r={R}"))
    for key, prefix in [("n!", "n! ="), ("r!", "r! ="), ("nPr", "nPr="), ("nCr", "nCr="), ("n^r", "n^r="),
                        ("C(n+r-1,r)", "C(n+r-1,r)=")]:
        want = exp[key]
        got = val_after(sc, prefix)
        c.check(got == want, f"{key}: got {got!r} want {want!r}")
    c.common(res)
    c.done(res)


# ------------------------------------------------------------------------------------------ tool B
def test_B(cid):
    o = ORC[cid]
    c = Case(cid)
    word = o["inputs"]["word"]
    letter = o["inputs"].get("letter")
    exp = o["expected"]
    acts = [{"menu": 2}, {"input": word}]
    if letter:
        acts += [{"menu": 1}, {"input": letter}, {"menu": 2}, {"input": letter}]
    acts += [{"menu": 3}, {"menu": 7}]
    res = run(acts)
    tot = screen_with(res, "TOTAL=n!/(k1!k2!…)")
    rt = rows_of(tot)
    c.check(tot is not None, "no total screen")
    c.check(any(r.startswith("n=" + exp["n"] + " (") for r in rt), f"n row: {rt[1:2]}")
    if exp["repeated"] == "(none)":
        c.check("NO REPEATED LETTERS" in rt, "NO REPEATED LETTERS missing")
    else:
        joined = "".join(r for r in tot["rows"][3:5])
        for item in exp["repeated"].split("  "):
            c.check(item in joined, f"repeated item {item!r} not in {joined!r}")
    c.check("=" + d9(o, "total") in rt, f"total row '={d9(o, 'total')}' missing: {rt}")
    if letter:
        if exp.get("block", "").startswith("REJECT"):
            c.anywhere(res, "LETTER NOT IN WORD")
            c.check(screen_with(res, "AS 1 BLOCK") is None, "block screen shown for absent letter")
        else:
            bl = [s_ for s_ in pauses(res) if any("AS 1 BLOCK" in r for r in s_["rows"])]
            c.check(len(bl) == 2, f"expected 2 block screens, got {len(bl)}")
            if bl:
                c.check("=" + d9(o, "block") in rows_of(bl[0]), f"block {d9(o, 'block')} missing: {rows_of(bl[0])}")
            if len(bl) == 2:
                r2 = rows_of(bl[1])
                c.check("=TOTAL-BLOCK" in r2, "not-together formula missing")
                c.anywhere(res, "ARE NOT ALL TOGETHER?")
                c.check("=" + d9(o, "total") + "-" + d9(o, "block") in r2, "plug-in total-block missing")
                c.check("=" + d9(o, "not together") in r2, f"not together {d9(o, 'not together')} missing: {r2}")
    c.common(res)
    c.done(res)


# ------------------------------------------------------------------------------------------ tool C
def test_C(cid):
    o = ORC[cid]
    c = Case(cid)
    inp, exp = o["inputs"], o["expected"]
    if inp["mode"] == "C1":
        sizes = inp["sizes"]
        labeled = 1 if cid == "CNT-C-S1" else 0
        acts = [{"menu": 3}, {"menu": 1}, {"input": str(len(sizes))}] + [{"input": str(x)} for x in sizes]
        acts += [{"input": str(labeled)}, {"menu": 7}]
        res = run(acts)
        sc = screen_with(res, "LABELED=n!/(n1!…nk!)")
        r = rows_of(sc)
        c.check(sc is not None, "no C1 result screen")
        if sc:
            c.check(r[0].startswith("n=" + exp["n"] + " INTO " + str(len(sizes))), f"n row {r[0]!r}")
            c.check(r[4] == "=" + exp["labeled"], f"labeled row {r[4]!r} want ={exp['labeled']}")
            c.check(r[6] == "=" + exp["unlabeled"], f"unlabeled row {r[6]!r} want ={exp['unlabeled']}")
            ans = exp["labeled"] if labeled else exp["unlabeled"]
            c.check(r[9] == "ANSWER=" + ans, f"answer row {r[9]!r}")
    else:
        counts = inp["counts"]
        acts = [{"menu": 3}, {"menu": 2}, {"input": str(inp["N"])}, {"input": str(len(counts))}]
        acts += [{"input": str(x)} for x in counts]
        if "result" in exp:
            acts += [{"input": "5"}, {"input": "1"}, {"input": "2"}, {"input": "4"}, {"menu": 7}]
            res = run(acts)
            c.anywhere(res, "MORE THAN N - REJECTED")
            c.row(res, "STEP1 N!/(c1!..cM!r!)", "=10*64", "valid retry after reject")
        else:
            acts += [{"input": str(inp["F"])}, {"menu": 7}]
            res = run(acts)
            sc = screen_with(res, "STEP1 N!/(c1!..cM!r!)")
            r = rows_of(sc)
            c.check(sc is not None, "no C2 result screen")
            if sc:
                c.check(("FREE r=" + exp["r"]) in r[0], f"r row {r[0]!r}")
                c.check(r[3] == "=" + exp["multinomial"], f"multinomial row {r[3]!r}")
                c.check(r[5] == "=%s^%s=%s" % (inp["F"], exp["r"], exp["F^r"]), f"F^r row {r[5]!r}")
                c.check(r[7] == "=%s*%s" % (exp["multinomial"], exp["F^r"]), f"product row {r[7]!r}")
                c.check(r[8] == "=" + exp["total"], f"total row {r[8]!r}")
    c.common(res)
    c.done(res)


# ------------------------------------------------------------------------------------------ tool D
def test_D(cid):
    o = ORC[cid]
    c = Case(cid)
    i, exp = o["inputs"], o["expected"]
    acts = [{"menu": 4}] + [{"input": str(i[k])} for k in ("A", "B", "K", "G1min", "G1max", "G2min", "G2max")]
    if i["K"] > i["A"] + i["B"]:
        acts += [{"input": x} for x in ("8", "6", "5", "2", "99", "2", "99")] + [{"menu": 7}]
        res = run(acts)
        c.anywhere(res, "K IS MORE THAN A+B")
        c.row(res, "TOTAL WAYS=Σ TERMS", "=1400", "valid retry after reject")
        c.common(res)
        c.done(res)
        return
    acts += [{"menu": 7}]
    res = run(acts)
    terms = [k for k in exp if k.startswith("i=")]
    for k in terms:
        c.anywhere(res, "%s %s" % (k, exp[k]), k)
    if not terms:
        c.anywhere(res, "NO VALID i  (0 WAYS)")
    tot = screen_with(res, "TOTAL WAYS=Σ TERMS")
    r = rows_of(tot)
    c.check(tot is not None, "no total screen")
    if tot:
        c.check(r[2] == "=" + d9(o, "total"), f"total row {r[2]!r}")
        c.check(r[3] == "ALL=C(A+B,K)=C(%d,%d)" % (i["A"] + i["B"], i["K"]), f"all row {r[3]!r}")
        c.check(r[4] == "=" + d9(o, "C(A+B,K)"), f"C(A+B,K) row {r[4]!r}")
        p9, p8 = o["display"]["P"]
        c.check(r[7] == "P=" + p9, f"P row {r[7]!r} want P={p9}")
        if p9 != p8:
            c.check(r[8] == " =" + p8, f"P decimal row {r[8]!r} want ' ={p8}'")
    c.common(res)
    c.done(res)


# ------------------------------------------------------------------------------------------ tool E
def test_E(cid):
    o = ORC[cid]
    c = Case(cid)
    i, exp = o["inputs"], o["expected"]
    mins = i["mins"]
    acts = [{"menu": 5}, {"input": str(i["n"])}, {"input": str(i["k"])}]
    if len(set(mins)) == 1 and cid != "CNT-E-S3":
        acts += [{"input": "1"}, {"input": str(mins[0])}]
    else:
        acts += [{"input": "0"}] + [{"input": str(m)} for m in mins]
    acts += [{"menu": 7}]
    res = run(acts)
    sc = screen_with(res, "Σ MINS=")
    r = rows_of(sc)
    c.check(sc is not None, "no result screen")
    if sc:
        c.check(r[2].endswith("=" + s(exp["n'"])), f"n' row {r[2]!r}")
        if int(exp["n'"]) < 0:
            c.check("n'<0 SO 0 WAYS" in r, "0 ways message missing")
        else:
            c.check(r[4] == "=" + exp["shown"], f"ways row {r[4]!r} want ={exp['shown']}")
    c.common(res)
    c.done(res)


# ------------------------------------------------------------------------------------------ tool F
def test_F(cid):
    o = ORC[cid]
    c = Case(cid)
    terms = o["inputs"]["terms"]
    acts = [{"menu": 6}, {"input": str(len(terms))}]
    for a, e in terms:
        acts += [{"input": s(a)}, {"input": str(e)}]
    acts += [{"menu": 7}]
    res = run(acts)
    sc = screen_with(res, "COEFF=MULTINOMIAL*PRODUCT")
    r = rows_of(sc)
    c.check(sc is not None, "no result screen")
    if sc:
        c.check(r[0].startswith("n=Σe=" + o["expected"]["n"] + " "), f"n row {r[0]!r}")
        c.check(r[3] == "=" + d9(o, "multinomial"), f"multinomial row {r[3]!r}")
        c.check(r[6] == "=" + d9(o, "product"), f"product row {r[6]!r}")
        c.check(r[8] == "=%s*%s" % (d9(o, "multinomial"), d9(o, "product")), f"plug row {r[8]!r}")
        c.check(r[9] == "=" + d9(o, "coefficient"), f"coefficient row {r[9]!r}")
    c.common(res)
    c.done(res)


# ------------------------------------------------------------------------------------------ extra cases
def extra_cases():
    # BACK straight away, run directly (no driver)
    c = Case("X-BACK-direct")
    res = run([{"menu": 7}], direct=True)
    c.common(res, direct=True)
    c.check(res.screens[0]["event"] == "menu" and res.screens[0]["menu"]["items"] == [
        "n!, nPr, nCr", "WORD ARRANGEMENTS", "GROUPS/MULTINOMIAL", "2-GROUP SELECTION", "STARS AND BARS",
        "TERM COEFFICIENT", "BACK"] and res.screens[0]["menu"]["title"] == "COUNTING TOOLS", "menu text/order")
    c.done(res)

    # all six tools in one session, then BACK: lists from every tool must be deleted
    c = Case("X-ALL-TOOLS-then-BACK")
    acts = [{"menu": 1}, {"input": "5"}, {"input": "2"},
            {"menu": 2}, {"input": "AAB"}, {"menu": 3},
            {"menu": 3}, {"menu": 1}, {"input": "2"}, {"input": "1"}, {"input": "1"}, {"input": "0"},
            {"menu": 4}] + [{"input": x} for x in ("3", "3", "2", "0", "99", "0", "99")] + [
            {"menu": 5}, {"input": "5"}, {"input": "2"}, {"input": "1"}, {"input": "0"},
            {"menu": 6}, {"input": "2"}, {"input": "1"}, {"input": "1"}, {"input": "1"}, {"input": "1"},
            {"menu": 7}]
    res = run(acts)
    c.common(res)
    c.done(res)

    # big numbers: TOO BIG paths, no overflow errors
    c = Case("X-A-big-1000-500")
    res = run([{"menu": 1}, {"input": "1000"}, {"input": "500"}, {"menu": 7}])
    sc = rows_of(screen_with(res, "n=1000  r=500"))
    for p in ("n! =", "r! =", "nPr=", "nCr=", "n^r=", "C(n+r-1,r)="):
        c.check(val_after(sc, p) == "TOO BIG", f"{p} not TOO BIG: {sc}")
    c.common(res)
    c.check(res.steps < 60000, f"too slow: {res.steps} steps")
    c.done(res)

    c = Case("X-A-100-50")
    res = run([{"menu": 1}, {"input": "100"}, {"input": "50"}, {"menu": 7}])
    sc = rows_of(screen_with(res, "n=100  r=50"))
    c.check(val_after(sc, "nCr=") == "1.008913445ᴇ29", f"nCr {val_after(sc, 'nCr=')}")
    c.check(val_after(sc, "nPr=") == "3.068518756ᴇ93", f"nPr {val_after(sc, 'nPr=')}")
    c.check(val_after(sc, "n^r=") == "TOO BIG", "n^r")  # 100^50 = 1E100
    c.common(res)
    c.done(res)

    c = Case("X-A-negative-reject")
    res = run([{"menu": 1}, {"input": "⁻3"}, {"input": "2"}, {"input": "4"}, {"input": "4"}, {"menu": 7}])
    c.anywhere(res, "n AND r MUST BE WHOLE")
    c.row(res, "n=4  r=4", "nCr=4!/(4!)=1")
    c.row(res, "n=4  r=4", "nPr=4!/0!=24")
    c.common(res)
    c.done(res)

    # word with 3+ copies not-together hint; long word
    c = Case("X-B-long-word")
    res = run([{"menu": 2}, {"input": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}, {"menu": 3}, {"menu": 7}])
    c.row(res, "TOTAL=n!/(k1!k2!…)", "=4.032914611ᴇ26")
    c.anywhere(res, "NO REPEATED LETTERS")
    c.common(res)
    c.done(res)

    c = Case("X-B-too-big")
    res = run([{"menu": 2}, {"input": "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 4},
               {"menu": 2}, {"input": "A"}, {"menu": 3}, {"menu": 7}])
    c.row(res, "TOTAL=n!/(k1!k2!…)", "=TOO BIG")
    c.row(res, "AS 1 BLOCK", "=TOO BIG")
    c.anywhere(res, " A x4  B x4  C x4  D x4  E")
    c.anywhere(res, "…")
    c.common(res)
    c.done(res)

    # C1 bad k then bad size
    c = Case("X-C1-reject")
    res = run([{"menu": 3}, {"menu": 1}, {"input": "0"}, {"input": "2"}, {"input": "1.5"}, {"input": "2"},
               {"input": "2"}, {"input": "3"}, {"input": "3"}, {"input": "1"}, {"menu": 7}])
    c.anywhere(res, "k MUST BE 1 TO 30")
    c.anywhere(res, "SIZES MUST BE WHOLE")
    c.row(res, "LABELED=n!/(n1!…nk!)", "ANSWER=20")
    c.common(res)
    c.done(res)

    # C2: F=0 with r>0 -> total 0
    c = Case("X-C2-F0-r2")
    res = run([{"menu": 3}, {"menu": 2}, {"input": "5"}, {"input": "1"}, {"input": "3"}, {"input": "0"}, {"menu": 7}])
    c.row(res, "STEP1 N!/(c1!..cM!r!)", "=0^2=0")
    c.row(res, "STEP1 N!/(c1!..cM!r!)", "=0")
    c.common(res)
    c.done(res)

    # D pagination: 21 terms -> 3 pages, Vandermonde total = C(40,20)
    c = Case("X-D-paginate")
    res = run([{"menu": 4}] + [{"input": x} for x in ("20", "20", "20", "0", "99", "0", "99")] + [{"menu": 7}])
    more = [p for p in pauses(res) if any("ENTER=MORE" in r for r in p["rows"])]
    c.check(len(more) == 2, f"expected 2 ENTER=MORE pages, got {len(more)}")
    c.anywhere(res, "i=10 TERM=3.413477954ᴇ10")
    c.anywhere(res, "i=0 1*1=1")
    c.row(res, "TOTAL WAYS=Σ TERMS", "=1.378465288ᴇ11")
    c.row(res, "TOTAL WAYS=Σ TERMS", "P=1")
    c.common(res)
    c.done(res)

    # E: bad k, then per-bin mins with a negative
    c = Case("X-E-reject")
    res = run([{"menu": 5}, {"input": "5"}, {"input": "0"}, {"input": "5"}, {"input": "2"}, {"input": "0"},
               {"input": "⁻1"}, {"input": "0"}, {"input": "5"}, {"input": "2"}, {"input": "1"}, {"input": "0"},
               {"menu": 7}])
    c.anywhere(res, "n≥0, 1≤k≤50, mins≥0")
    c.row(res, "Σ MINS=", "=C(6,1)=6")
    c.common(res)
    c.done(res)

    # F: zero coefficient with positive exponent -> 0 ; fractional coefficient ; bad k
    c = Case("X-F-zero-coeff")
    res = run([{"menu": 6}, {"input": "7"}, {"input": "2"}, {"input": "0"}, {"input": "2"}, {"input": "3"},
               {"input": "1"}, {"menu": 7}])
    c.anywhere(res, "k MUST BE 2 TO 6")
    c.row(res, "COEFF=MULTINOMIAL*PRODUCT", "=3")
    c.row(res, "COEFF=MULTINOMIAL*PRODUCT", "=0")
    c.common(res)
    c.done(res)

    # ---- TOO BIG / reject paths (no ERR:OVERFLOW, message shown, back to a prompt or the menu)
    c = Case("X-A-n0-r2")
    res = run([{"menu": 1}, {"input": "0"}, {"input": "2"}, {"menu": 7}])
    sc = rows_of(screen_with(res, "n=0  r=2"))
    for p, v in (("nPr=", "0"), ("nCr=", "0"), ("n^r=", "0"), ("C(n+r-1,r)=", "0")):
        c.check(val_after(sc, p) == v, f"{p} {val_after(sc, p)!r} want {v}")
    c.common(res)
    c.done(res)

    c = Case("X-C1-too-big")
    res = run([{"menu": 3}, {"menu": 1}, {"input": "2"}, {"input": "200"}, {"input": "200"}, {"input": "0"},
               {"menu": 7}])
    c.row(res, "LABELED=n!/(n1!…nk!)", "=TOO BIG")
    c.row(res, "LABELED=n!/(n1!…nk!)", "ANSWER=TOO BIG")
    c.common(res)
    c.done(res)

    c = Case("X-C2-reject-and-too-big")
    res = run([{"menu": 3}, {"menu": 2}, {"input": "5"}, {"input": "0"},
               {"input": "500"}, {"input": "1"}, {"input": "250"}, {"input": "1000"}, {"menu": 7}])
    c.anywhere(res, "(1 TO 20 CATEGORIES)")
    sc = screen_with(res, "STEP1 N!/(c1!..cM!r!)")
    r = rows_of(sc)
    c.check(sc is not None and r[3] == "=TOO BIG" and r[5] == "=1000^250=TOO BIG" and r[7] == ""
            and r[8] == "=TOO BIG", f"C2 too big rows {r}")
    c.common(res)
    c.done(res)

    c = Case("X-C2-long-plugin")
    res = run([{"menu": 3}, {"menu": 2}, {"input": "42"}, {"input": "1"}, {"input": "30"}, {"input": "12345678"},
               {"menu": 7}])
    sc = screen_with(res, "STEP1 N!/(c1!..cM!r!)")
    r = rows_of(sc)
    c.check(sc is not None and r[5].startswith("=") and "^" not in r[5] and len(r[5]) <= 26, f"F^r row {r}")
    c.common(res)
    c.done(res)

    c = Case("X-D-reject-and-too-big")
    res = run([{"menu": 4}] + [{"input": x} for x in ("⁻1", "6", "5", "0", "99", "0", "99")]
              + [{"input": x} for x in ("300", "300", "300", "0", "99", "0", "99")] + [{"menu": 7}])
    c.anywhere(res, "(A, B, K AT LEAST 0)")
    c.anywhere(res, "C(A+B,K) TOO BIG")
    c.common(res)
    c.done(res)

    c = Case("X-D-long-header")
    res = run([{"menu": 4}] + [{"input": x} for x in ("123456", "567890", "3", "3", "3", "0", "99")] + [{"menu": 7}])
    c.anywhere(res, "i  C(A,i)*C(B,K-i)")
    c.anywhere(res, "i=3 ")
    c.common(res)
    c.done(res)

    c = Case("X-E-too-big-and-split")
    res = run([{"menu": 5}, {"input": "5000"}, {"input": "50"}, {"input": "1"}, {"input": "0"},
               {"menu": 5}, {"input": "50000"}, {"input": "20"}, {"input": "1"}, {"input": "0"}, {"menu": 7}])
    c.row(res, "n=5000 ITEMS, k=50 BINS", "=C(5049,49)=TOO BIG")
    c.row(res, "n=50000 ITEMS, k=20 BINS", "=C(50019,19)")
    s2 = screen_with(res, "n=50000 ITEMS, k=20 BINS")
    c.check(s2 is not None and rows_of(s2)[5].startswith("=") and "ᴇ" in rows_of(s2)[5], f"split row {rows_of(s2)}")
    c.common(res)
    c.done(res)

    c = Case("X-F-reject-too-big-zero-exps")
    res = run([{"menu": 6}, {"input": "2"}, {"input": "1"}, {"input": "1.5"}, {"input": "1"}, {"input": "1"},
               {"input": "2"}, {"input": "1000"}, {"input": "40"}, {"input": "1"}, {"input": "1"},
               {"menu": 6}, {"input": "2"}, {"input": "5"}, {"input": "0"}, {"input": "7"}, {"input": "0"},
               {"menu": 7}])
    c.anywhere(res, "EXPONENTS MUST BE WHOLE")
    s1 = screen_with(res, "n=Σe=41  CHECK n = POWER!")
    r = rows_of(s1)
    c.check(s1 is not None and r[3] == "=41" and r[6] == "=TOO BIG" and r[9] == "=TOO BIG", f"too big rows {r}")
    s2 = screen_with(res, "n=Σe=0  CHECK n = POWER!")
    r = rows_of(s2)
    c.check(s2 is not None and r[5] == "=1" and r[9] == "=1", f"zero exps rows {r}")
    c.common(res)
    c.done(res)

    # long plug-in texts are shortened with "…" or dropped, never wrapped
    c = Case("X-long-texts")
    res = run([{"menu": 1}, {"input": "123456789"}, {"input": "10"},
               {"menu": 3}, {"menu": 1}, {"input": "12"}] + [{"input": "2"}] * 12 + [{"input": "0"},
              {"menu": 3}, {"menu": 2}, {"input": "40"}, {"input": "10"}] + [{"input": "2"}] * 10 + [{"input": "2"},
              {"menu": 6}, {"input": "6"}] + [{"input": x} for x in ("1", "10", "1", "11", "1", "12", "1", "13", "1", "14", "1", "15")] + [
              {"menu": 6}, {"input": "6"}] + [{"input": x} for x in ("1", "100", "1", "101", "1", "102", "1", "103", "1", "104", "1", "105")] + [
              {"menu": 6}, {"input": "2"}, {"input": "1"}, {"input": "300"}, {"input": "1"}, {"input": "300"},
              {"menu": 6}, {"input": "2"}, {"input": "1"}, {"input": "100"}, {"input": "3"}, {"input": "100"},
              {"menu": 7}])
    sa = rows_of(screen_with(res, "n=123456789  r=10"))
    c.check(any(r.startswith("n^r=") and "^1" not in r for r in sa), f"n^r short form {sa}")
    c.anywhere(res, "SIZES 2,2,2,2,2,2,2,2,2,2…")
    c.anywhere(res, "=24!/(2!2!2!2!2!2!2!2!2!2…")
    c.anywhere(res, "=40!/(2!2!2!2!2!2!2!2!2!2…")
    c.anywhere(res, "=75!/(10!11!12!13!14!15!)")
    c.anywhere(res, "UNLABELED=LABELED/(m!…)")
    st = rows_of(screen_with(res, "n=Σe=600  CHECK n = POWER!"))
    c.anywhere(res, "=615!/(100!101!102!103!10…")
    c.check(st[3:4] == ["=TOO BIG"] and st[8] == "" and st[9] == "=TOO BIG", f"600 rows {st}")
    st = rows_of(screen_with(res, "n=Σe=200  CHECK n = POWER!"))
    c.check(st[3].startswith("=9.05485146") and st[9] == "=TOO BIG", f"200 rows {st}")
    c.common(res)
    c.done(res)

    c = Case("X-F-fraction")
    res = run([{"menu": 6}, {"input": "2"}, {"input": "1/2"}, {"input": "2"}, {"input": "⁻1/3"}, {"input": "1"},
               {"menu": 7}])
    # 3!/(2!1!) * (1/4)*(-1/3) = 3 * -1/12 = -1/4
    c.row(res, "COEFF=MULTINOMIAL*PRODUCT", "=⁻1/12")
    c.row(res, "COEFF=MULTINOMIAL*PRODUCT", "=(1/2)^2*(⁻1/3)^1")
    c.row(res, "COEFF=MULTINOMIAL*PRODUCT", "=⁻1/4  =⁻.25")
    c.common(res)
    c.done(res)


HW_MAP = {  # homework key -> (spec case, expected key in that case, hw key)
    "HW1-Q3": [("CNT-F-S1", "coefficient", "coefficient")],
    "HW1-Q4": [("CNT-B-S1", "total", "(a)"), ("CNT-B-S1", "block", "(b)")],
    "HW1-Q5": [("CNT-C-S1", "labeled", "ways")],
    "HW1-Q6": [("CNT-D-S2", "total", "ways")],
    "HW1-431-Q7": [("CNT-D-S1", "total", "ways")],
    "HW1-431-Q8": [("CNT-C-S4", "total", "ways")],
    "HW1-631-Q8": [("CNT-E-S1", "ways", "(a)"), ("CNT-E-S2", "ways", "(b)")],
}


def hw_cases():
    # the homework answers are produced by the spec-case runs above; check the keys agree
    for hid, maps in HW_MAP.items():
        c = Case(hid)
        h = ORC[hid]
        for sid, skey, hkey in maps:
            c.check(str(ORC[sid]["expected"][skey]) == str(h["expected"][hkey]),
                    f"{hid} {hkey}={h['expected'][hkey]} vs {sid} {skey}={ORC[sid]['expected'][skey]}")
            c.check(any(r[0] == sid and r[1] for r in results), f"covering case {sid} did not pass")
        c.done()


def main():
    ids = [o["id"] for o in ORACLES if o["program"] == "STACNT" and o["kind"] in ("spec", "edge")]
    for cid in ids:
        tool = ORC[cid]["tool"]
        {"A": test_A, "B": test_B, "C": test_C, "D": test_D, "E": test_E, "F": test_F}[tool](cid)
    hw = [o["id"] for o in ORACLES if o["program"] == "STACNT" and o["kind"] == "hw"]
    missing = [h for h in hw if h not in HW_MAP]
    hw_cases()
    extra_cases()
    if missing:
        results.append(("HW-mapping", False, missing))
        print("FAIL HW-mapping  unmapped hw cases: %s" % missing)
    npass = sum(1 for r in results if r[1])
    print("TOTAL: %d/%d passed" % (npass, len(results)))
    sys.exit(0 if npass == len(results) else 1)


if __name__ == "__main__":
    main()
