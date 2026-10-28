#!/usr/bin/env python3
"""
test_STARV.py - simulator tests for src/STARV.txt (tools A-E and J).

Drives the real menus/prompts through tools/tisim.py and asserts on the rendered screen text.
Covers every SPEC section 4 STARV case, every STARV oracle case in oracles/oracles.json (spec + edge + HW3),
and the input-validation paths.  For every run it also asserts:
  res.error is None, res.leaks == 0, no display-policy warnings, BACK ends the module through its Return
  (ended_reason "return"; this tisim build reports a top-level Return as "end", so "end" is accepted only
  when STARV's Return line executed), and all ʟRV... lists are deleted after BACK.

Run:  $PY tests/test_STARV.py      (prints PASS/FAIL per case + total; exit 1 on any failure)
"""
import json
import os
import sys
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from tisim import Sim  # noqa: E402

SRC = os.path.join(ROOT, "src")
ORACLES = json.load(open(os.path.join(ROOT, "oracles", "oracles.json"), encoding="utf-8"))
OR = {c["id"]: c for c in ORACLES if c["program"] == "STARV"}
USED = set()

BACK = {"menu": 7}            # BACK in the STARV main menu
RESULTS = []
RETURN_LINE = [i for i, l in enumerate(open(os.path.join(SRC, "STARV.txt"), encoding="utf-8"), 1)
               if l.strip() == "Return"][0]


def norm(s):
    """'-' -> '⁻' and drop an optional leading 0 before a decimal point."""
    s = str(s).replace("-", "⁻")
    out = []
    for i, ch in enumerate(s):
        if ch == "0" and i + 1 < len(s) and s[i + 1] == "." and (i == 0 or not s[i - 1].isdigit()):
            continue
        out.append(ch)
    return "".join(out)


def norm_row(r):
    out = []
    for i, ch in enumerate(r):
        if ch == "0" and i + 1 < len(r) and r[i + 1] == "." and (i == 0 or not r[i - 1].isdigit()):
            continue
        out.append(ch)
    return "".join(out)


def num(s):
    """TI display text -> Fraction (for table parsing)."""
    s = s.strip().replace("⁻", "-")
    if "/" in s:
        a, b = s.split("/")
        return Fraction(a) / Fraction(b)
    return Fraction(s)


def run(actions, max_steps=3_000_000):
    return Sim(SRC).run("STARV", actions=actions, max_steps=max_steps)


class Case:
    def __init__(self, name, res):
        self.name, self.res, self.fails = name, res, []

    def check(self, cond, msg):
        if not cond:
            self.fails.append(msg)

    def screens(self):
        return [[norm_row(r) for r in sc["rows"]] for sc in self.res.screens
                if sc["event"] in ("pause", "input", "out_of_actions", "end")]

    def has(self, text, screens=None):
        for rs in (screens if screens is not None else self.screens()):
            for r in rs:
                if text in r:
                    return True
        return False

    def text(self, text, where=""):
        self.check(self.has(norm_row(text)), f"missing text {text!r} {where}")

    def absent(self, text, where=""):
        self.check(not self.has(norm_row(text)), f"unexpected text {text!r} {where}")

    def row(self, want, alts=(), where=""):
        """a row that starts with (after stripping) want or one of alts, and ends right after it."""
        cands = [norm_row(want)] + [norm_row(a) for a in alts]
        for rs in self.screens():
            for r in rs:
                rr = r.rstrip()
                for c in cands:
                    if c in rr and (rr.endswith(c) or rr[rr.index(c) + len(c)] == " "):
                        return rr
        self.fails.append(f"missing {want!r} {where}")
        return None

    def value(self, label, exact, dec=None, alts=(), where=""):
        """label+exact on a row; when dec differs from exact, dec must follow on the same row
        (' =dec') or on the next row ('=dec' / ' =dec')."""
        ex = [norm(exact)] + [norm(a) for a in alts]
        for rs in self.screens():
            for i, r in enumerate(rs):
                rr = r.rstrip()
                for e in ex:
                    want = norm_row(label) + e
                    if want in rr:
                        rest = rr[rr.index(want) + len(want):]
                        if rest[:1] not in ("", " "):
                            continue
                        if dec is None or norm(dec) == e:
                            return
                        d = norm(dec)
                        nxt = rs[i + 1].strip() if i + 1 < len(rs) else ""
                        if rest.strip() == "=" + d or nxt == "=" + d:
                            return
        self.fails.append(f"missing {label}{exact} (dec {dec}) {where}")

    def table(self):
        """parse every x | p(x) | F(x) table screen -> {x: (p_text, F_text)}"""
        out = {}
        for rs in self.screens():
            if rs[0][7:9] == "p(" and rs[0][17:19] == "F(":
                for r in rs[1:9]:
                    if r.strip() and not r.startswith("ENTER"):
                        out[num(r[0:6])] = (r[7:16].strip(), r[17:26].strip())
        return out

    def expect_table(self, disp, where=""):
        """disp: oracle display dict with keys 'p(x)' / 'F(x)'"""
        tab = self.table()
        for k, (s9, s8) in disp.items():
            if not (k.startswith("p(") or k.startswith("F(")) or " " in k:
                continue
            x = num(k[2:-1])
            if x not in tab:
                self.fails.append(f"table has no row x={k[2:-1]} {where}")
                continue
            got = tab[x][0 if k[0] == "p" else 1]
            self.check(norm(got) == norm(s9), f"table {k}: got {got!r} want {s9!r} {where}")

    def finish(self, expect_return=True):
        r = self.res
        self.check(r.error is None, f"error: {r.error}")
        self.check(r.leaks == 0, f"leaks={r.leaks}")
        self.check(not r.warnings, f"display warnings: {r.warnings[:3]}")
        if expect_return:
            ok = r.ended_reason == "return" or (r.ended_reason == "end"
                                                and RETURN_LINE in r.coverage.get("STARV", []))
            self.check(ok, f"did not end via Return (ended_reason={r.ended_reason})")
            rv = [k for k in r.vars["lists"] if k.startswith("RV")]
            self.check(not rv, f"lists not deleted after BACK: {rv}")
        RESULTS.append((self.name, not self.fails, self.fails))
        print(("PASS " if not self.fails else "FAIL ") + self.name)
        for f in self.fails:
            print("     - " + f)


def orc(cid):
    USED.add(cid)
    return OR[cid]


def dsp(cid, key):
    return orc(cid)["display"][key]


# ================================================================ tool A
def acts_A(mode, xs, ps, queries=()):
    a = [{"menu": 1}, {"menu": mode}, {"input": str(len(xs))}]
    for x, p in zip(xs, ps):
        a += [{"input": str(x).replace("-", "⁻")}, {"input": str(p).replace("-", "⁻")}]
    for q in queries:
        if q[0] == "P":
            a += [{"menu": 1}, {"input": str(q[1])}, {"input": str(q[2])}]
        else:
            a += [{"menu": 2}, {"input": str(q[1])}]
    return a + [{"menu": 3}, BACK]


def check_moments(c, cid):
    d = orc(cid)["display"]
    c.value("E[X]=Σx*p(x)=", *d["E[X]"])
    c.value("E[X²]=Σx²*p(x)=", *d["E[X^2]"])
    v9, v8 = d["Var(X)"]
    ok = any(r.startswith("=") and r.rstrip().endswith("=" + norm(v9)) and "²" in r
             for rs in c.screens() for r in rs)
    c.check(ok, f"Var row '=E[X²]-(E[X])²={v9}' missing")
    c.value("SD=√(Var)=", d["SD(X)"][0])


def test_A():
    # A-S1 : p(x) values, queries a=3 b=4, F(3.5)
    cid = "RV-A-S1"
    c = Case(cid + " pmf table/moments/queries",
             run(acts_A(1, [2, 3, 4, 5], [".1", ".2", ".3", ".4"], [("P", 3, 4), ("F", 3.5)])))
    d = orc(cid)["display"]
    c.expect_table(d)
    check_moments(c, cid)
    c.text("Σp=1  OK")
    c.absent("CHECKS")
    c.value("P(3≤X≤4)=", *d["P(3<=X<=4)"])
    c.value("P(3<X≤4)=", *d["P(3<X<=4)"])
    c.value("P(3≤X<4)=", *d["P(3<=X<4)"])
    c.value("P(3<X<4)=", *d["P(3<X<4)"])
    c.text("F(3.5)=P(X≤3.5)")
    c.value(" =", *d["F(7/2) query"])
    c.text("P(X>3.5)=1-F(3.5)")
    c.value(" =", "7/10", ".7")
    c.finish()

    # A-S2 : CDF values
    cid = "RV-A-S2"
    c = Case(cid + " CDF values -> p", run(acts_A(3, [2, 3, 4, 5], [".1", ".3", ".6", "1"])))
    c.expect_table(orc(cid)["display"])
    check_moments(c, cid)
    c.absent("CHECKS")
    c.finish()

    # A-S3 : weights
    cid = "RV-A-S3"
    c = Case(cid + " weights -> p", run(acts_A(2, [2, 3, 4, 5], [1, 2, 3, 4])))
    c.expect_table(orc(cid)["display"])
    check_moments(c, cid)
    c.text("Σw=10  SO p=w/Σw")
    c.finish()

    # A-E1 : unsorted input, F below / above support
    cid = "RV-A-E1"
    c = Case(cid + " unsorted x, F(1), F(10)",
             run(acts_A(1, [5, 2, 4, 3], [".4", ".1", ".3", ".2"], [("F", 1), ("F", 10)])))
    d = orc(cid)["display"]
    c.expect_table(d)
    check_moments(c, cid)
    c.text("F(1)=P(X≤1)")
    c.text("F(10)=P(X≤10)")
    scr = c.screens()
    f1 = [s for s in scr if s[0].startswith("F(1)=")]
    f10 = [s for s in scr if s[0].startswith("F(10)=")]
    c.check(f1 and f1[0][1].strip() == "=" + d["F(1) query"][0], f"F(1) screen {f1[:1]}")
    c.check(f10 and f10[0][1].strip() == "=" + d["F(10) query"][0], f"F(10) screen {f10[:1]}")
    c.finish()

    # A-E2 : negative x, irrational SD
    cid = "RV-A-E2"
    c = Case(cid + " x=-1,0,1 (SD irrational)", run(acts_A(1, [-1, 0, 1], ["1/4", "1/2", "1/4"])))
    c.expect_table(orc(cid)["display"])
    check_moments(c, cid)
    c.finish()

    # A-E3 : sum not 1 -> warning
    cid = "RV-A-E3"
    c = Case(cid + " Σp=.6 warning", run(acts_A(1, [1, 2, 3], [".1", ".2", ".3"])))
    c.expect_table(orc(cid)["display"])
    check_moments(c, cid)
    c.text("CHECKS")
    c.text("Σp=3/5  NOT 1 !")
    c.finish()

    # A-E4 : tolerant comparisons at x=.2,.3
    cid = "RV-A-E4"
    c = Case(cid + " decimals x, tolerant a/b",
             run(acts_A(1, [".1", ".2", ".3"], ["1/3", "1/3", "1/3"], [("P", ".2", ".3")])))
    d = orc(cid)["display"]
    c.expect_table(d)
    check_moments(c, cid)
    c.value("P(.2≤X≤.3)=", *d["P(1/5<=X<=3/10)"])
    c.value("P(.2<X≤.3)=", *d["P(1/5<X<=3/10)"])
    c.value("P(.2≤X<.3)=", *d["P(1/5<=X<3/10)"])
    c.value("P(.2<X<.3)=", *d["P(1/5<X<3/10)"])
    c.finish()

    # extra: CDF values decreasing / last F not 1 -> warnings
    c = Case("A cdf decreasing + last F≠1 warnings", run(acts_A(3, [1, 2, 3], [".5", ".3", ".9"])))
    c.text("F DECREASES - NOT A CDF")
    c.text("LAST F=9/10  NOT 1 !")
    c.finish()

    # validation: n out of range, negative weight
    a = [{"menu": 1}, {"menu": 1}, {"input": "25"}, {"input": "1"}, {"input": "7"}, {"input": "1"},
         {"menu": 3}, BACK]
    c = Case("A reject n=25, then n=1", run(a))
    c.text("n MUST BE A WHOLE")
    c.value("E[X]=Σx*p(x)=", "7")
    c.finish()
    a = [{"menu": 1}, {"menu": 2}, {"input": "2"}, {"input": "1"}, {"input": "⁻1"}, {"input": "2"},
         {"input": "3"}, {"input": "2"}, {"input": "1"}, {"input": "1"}, {"input": "1"}, {"input": "2"},
         {"menu": 3}, BACK]
    c = Case("A reject negative weight, repeated x warning", run(a))
    c.text("WEIGHTS MUST BE ≥ 0")
    c.text("REPEATED x - ADD THEIR p")
    c.finish()
    # BACK from the YOU HAVE menu
    c = Case("A menu BACK", run([{"menu": 1}, {"menu": 4}, BACK]))
    c.finish()


# ================================================================ tool B
STAT = {"MAXIMUM": 1, "MINIMUM": 2, "SUM": 3, "|DIFF|": 4}


def acts_B(stat, N, k, repl, extra=()):
    a = [{"menu": 2}, {"menu": STAT[stat]}, {"input": str(N)}]
    if STAT[stat] <= 2:
        a.append({"input": str(k)})
    a.append({"menu": 1 if repl == "WITHOUT" else 2})
    return a + list(extra) + [{"menu": 3}, BACK]


def test_B():
    for cid, formula in [("RV-B-S1", "p(z)=C(z-1,k-1)/C(N,k)"), ("RV-B-S2", "p(z)=(z^k-(z-1)^k)/N^k"),
                         ("RV-B-S3", "p(s)=#(i,j) WITH i+j=s"), ("RV-B-S4", "p(z)=C(N-z,k-1)/C(N,k)"),
                         ("RV-B-S5", "p(d)=#(i,j) WITH |i-j|=d"), ("RV-B-E1", "p(z)=C(z-1,k-1)/C(N,k)"),
                         ("RV-B-E2", "p(z)=C(N-z,k-1)/C(N,k)"), ("RV-B-E3", "p(z)=(z^k-(z-1)^k)/N^k"),
                         ("RV-B-E4", "p(s)=#(i,j) WITH i+j=s"), ("RV-B-E5", "p(d)=#(i,j) WITH |i-j|=d"),
                         ("RV-B-E7", "p(z)=((N-z+1)^k-(N-z)^k)")]:
        o = orc(cid)
        i = o["inputs"]
        c = Case(f"{cid} {i['stat']} N={i['N']} k={i['k']} {i['repl']}",
                 run(acts_B(i["stat"], i["N"], i["k"], i["repl"])))
        c.expect_table(o["display"])
        c.text(formula)
        c.text("CDF SKETCH=RIGHT-CONT.")
        c.text("Σp=1  OK")
        n_rows = len([k for k in o["display"] if k.startswith("p(")])
        c.check(len(c.table()) == n_rows, f"table rows {len(c.table())} != {n_rows}")
        if cid == "RV-B-S2":   # SPEC: p(z)=(2z-1)/36
            tab = c.table()
            for z in range(1, 7):
                c.check(num(tab[Fraction(z)][0]) == Fraction(2 * z - 1, 36), f"p({z}) != (2z-1)/36")
        c.finish()
    # HW3-Q1 = RV-B-S1
    o = orc("HW3-Q1")
    c = Case("HW3-Q1 max of 2 from 5 w/o", run(acts_B("MAXIMUM", 5, 2, "WITHOUT")))
    c.expect_table(o["display"])
    c.text("   =C(z-1,1)/10")
    c.finish()
    # SPEC: sum N=6 with -> p(7)=1/6 (also RV-B-S3); E[sum]=7
    c = Case("B sum N=6 with: p(7)=1/6, E=7",
             run(acts_B("SUM", 6, 2, "WITH")))
    c.check(c.table().get(Fraction(7), ("",))[0] == "1/6", "p(7) != 1/6")
    c.value("E[X]=Σx*p(x)=", "7")
    c.finish()
    # RV-B-E6 k>N without replacement -> reject, then recover with k=2
    orc("RV-B-E6")
    a = [{"menu": 2}, {"menu": 1}, {"input": "3"}, {"input": "4"}, {"menu": 1},
         {"input": "3"}, {"input": "2"}, {"menu": 1}, {"menu": 3}, BACK]
    c = Case("RV-B-E6 max N=3 k=4 w/o rejected", run(a))
    c.text("k>N WITHOUT REPLACEMENT")
    c.text("IS IMPOSSIBLE")
    c.check(c.table().get(Fraction(3), ("",))[0] == "2/3", "recovery N=3 k=2 p(3) != 2/3")
    c.finish()
    # validation: non-integer N
    a = [{"menu": 2}, {"menu": 3}, {"input": "2.5"}, {"menu": 2},
         {"input": "2"}, {"menu": 2}, {"menu": 3}, BACK]
    c = Case("B reject N=2.5", run(a))
    c.text("N AND k MUST BE WHOLE")
    c.finish()
    # big with-replacement case stays fast and formats tiny p
    c = Case("B max N=99 k=50 with (speed, tiny p)", run(acts_B("MAXIMUM", 99, 50, "WITH")))
    c.check(len(c.table()) == 99, "99 rows")
    c.check(c.res.steps < 400000, f"steps {c.res.steps}")
    c.finish()
    c = Case("B menu BACK", run([{"menu": 2}, {"menu": 5}, BACK]))
    c.finish()


# ================================================================ tool C
def acts_C(mode, pieces, unknown_c=0, queries=(), degree=None):
    a = [{"menu": 3}, {"menu": 1 if mode == "PDF" else 2}]
    if mode == "PDF":
        a.append({"input": str(unknown_c)})
    a.append({"input": str(len(pieces))})
    for lo, hi, co in pieces:
        a += [{"input": str(lo).replace("-", "⁻")}, {"input": str(hi).replace("-", "⁻")},
              {"input": str(len(co) - 1)}]
        a += [{"input": str(x).replace("-", "⁻")} for x in co]
    for q in queries:
        if q[0] == "ab":
            a += [{"menu": 1}, {"input": str(q[1]).replace("-", "⁻")}, {"input": str(q[2]).replace("-", "⁻")}]
        elif q[0] == "F":
            a += [{"menu": 2}, {"input": str(q[1]).replace("-", "⁻")}]
        elif q[0] == ">":
            a += [{"menu": 3}, {"input": str(q[1]).replace("-", "⁻")}]
        elif q[0] == "=":
            a += [{"menu": 4}, {"input": str(q[1]).replace("-", "⁻")}]
    return a + [{"menu": 5}, BACK]


def test_C():
    cid = "RV-C-S1"
    d = orc(cid)["display"]
    c = Case(cid + " two flat pieces (HW3 Q2)",
             run(acts_C("PDF", [(0, 2, ["1/4"]), (4, 6, ["1/4"])], 0, [("ab", 1, 5), ("F", 3)])))
    c.text("AREA=Σ∫f dx=1")
    c.text("AREA=1 AND f≥0  OK")
    c.text("x<0  F=0")
    c.text("0<x<2  F=")
    c.row("  (1/4)x")
    c.text("2≤x≤4  F=" + d["F on gap 2<=x<=4"][0])
    c.text("4<x<6  F=")
    c.row("  -1/2 + (1/4)x")
    c.text("x>6  F=" + d["F after last piece"][0])
    c.text("P(1<X<5)=F(b)-F(a)")
    c.text("=F(5)-F(1)")
    c.text("=3/4-1/4")
    c.value("=", *d["P(1<X<5)"])
    c.value("F(3)=", *d["F(3)"])
    c.finish()
    # HW3-Q2 values are the regions of RV-C-S1
    o = orc("HW3-Q2")["display"]
    c2 = Case("HW3-Q2 F by region", c.res)
    c2.text("x<0  F=" + o["F(x), x<=0"][0])
    c2.text("2≤x≤4  F=" + o["F(x), 2<=x<4"][0])
    c2.text("x>6  F=" + o["F(x), x>=6"][0])
    c2.finish()

    cid = "RV-C-S2"
    d = orc(cid)["display"]
    c = Case(cid + " 3/16-3x²/256 on (-4,4) (HW3 Q4)",
             run(acts_C("PDF", [(-4, 4, ["3/16", "0", "-3/256"])], 0,
                        [("ab", -4, -2), ("F", -2), ("ab", 1, 3), ("=", -1)])))
    c.text("AREA=Σ∫f dx=1")
    c.text("⁻4<x<4  F=")
    c.row("  1/2 + (3/16)x")
    c.row("   - (1/256)x³")
    c.value("F(⁻2)=", *d["F(-2)"])
    c.text("P(⁻4<X<⁻2)=F(b)-F(a)")
    c.value("=", *d["P(-4<X<-2)"])
    c.text("P(1<X<3)=F(b)-F(a)")
    c.value("=", "35/128", ".273438", where="(P(1<X<3))")
    c.check(c.has("=.273438") or c.has("=.273437"), "P(1<X<3) decimal .273438/.273437")
    c.text("P(X=⁻1)=0")
    c.text("0 (continuous X)")
    c.finish()
    o = orc("HW3-Q4")["display"]
    c2 = Case("HW3-Q4 (a) F(-2) (b) P(1<=X<=3) (c) P(X=-1)", c.res)
    c2.value("F(⁻2)=", *o["(a) P(X<=-2)"])
    c2.value("=", o["(b) P(1<=X<=3)"][0])
    c2.text("P(X=⁻1)=" + o["(c) P(X=-1)"][0])
    c2.finish()

    cid = "RV-C-S3"
    d = orc(cid)["display"]
    c = Case(cid + " unknown c, x² on (0,3) (HW3 431 Q5)",
             run(acts_C("PDF", [(0, 3, ["0", "0", "1"])], 1, [(">", 2)])))
    c.value("AREA=Σ∫f dx=", *d["area"])
    c.value("c=1/AREA=", *d["c"])
    c.text("(f IS SCALED BY c)")
    c.row("  (1/27)x³")
    c.text("x>3  F=1")
    c.text("=1-F(2)=1-8/27")
    c.value("=", *d["P(X>2)"])
    c.finish()
    o = orc("HW3-431-Q5")["display"]
    c2 = Case("HW3-431-Q5 c and P(Y>2)", c.res)
    c2.value("c=1/AREA=", *o["(a) c"])
    c2.value("=", *o["(c) P(Y>2)"])
    c2.finish()

    cid = "RV-C-S4"
    d = orc(cid)["display"]
    c = Case(cid + " CDF (x+2)/4 on (-2,2) (HW3 Q3)",
             run(acts_C("CDF", [(-2, 2, ["1/2", "1/4"])], queries=[("ab", -1, 1), (">", ".5")])))
    c.value("F(LO)=F(⁻2)=", d["F(lo1)"][0])
    c.value("F(HI)=F(2)=", d["F(hi_m)"][0])
    c.text("F GOES 0 TO 1 SMOOTHLY OK")
    c.absent("WARNING")
    c.text("⁻2<x<2  f=")
    c.row("  " + d["f piece1 const"][0])
    c.text("x>2  f=0")
    c.text("P(⁻1<X<1)=F(b)-F(a)")
    c.value("=", *d["P(-1<X<1)"])
    c.text("=1-F(.5)=1-5/8")
    c.value("=", *d["P(X>1/2)"])
    c.finish()
    o = orc("HW3-Q3")["display"]
    c2 = Case("HW3-Q3 P(-1<X<1), P(X>.5)", c.res)
    c2.value("=", *o["P(-1<X<1)"])
    c2.value("=", *o["P(X>0.5)"])
    c2.finish()

    cid = "RV-C-E1"
    d = orc(cid)["display"]
    c = Case(cid + " CDF jump at left end",
             run(acts_C("CDF", [(0, 1, ["1/2", "1/2"])], queries=[("ab", -1, ".5"), (">", ".5"), ("=", 0)])))
    c.value("F(LO)=F(0)=", d["F(lo1)"][0])
    c.text(" WARNING ≠0 - JUMP AT LO")
    c.row("  1/2")
    c.value("=", *d["P(-1<X<1/2)"])
    c.value("=", *d["P(X>1/2)"])
    c.text("0 (continuous X)")
    c.text("(UNLESS F JUMPS AT a)")
    c.finish()

    cid = "RV-C-E2"
    d = orc(cid)["display"]
    c = Case(cid + " unknown c, triangle",
             run(acts_C("PDF", [(0, 1, ["0", "1"]), (1, 2, ["2", "-1"])], 1, [("ab", ".5", "1.5"), ("F", 1)])))
    c.value("AREA=Σ∫f dx=", d["area"][0])
    c.value("c=1/AREA=", d["c"][0])
    c.row("  (1/2)x²")
    c.row("  -1 + 2x - (1/2)x²")
    c.text("x>2  F=1")
    c.value("=", *d["P(1/2<X<3/2)"])
    c.value("F(1)=", *d["F(1)"])
    c.finish()

    cid = "RV-C-E3"
    d = orc(cid)["display"]
    c = Case(cid + " support (1,3)",
             run(acts_C("PDF", [(1, 3, ["1/2"])], 0, [("F", 0), ("F", 2), ("F", 4)])))
    c.text("x<1  F=0")
    c.row("  -1/2 + (1/2)x")
    c.text("x>3  F=1")
    c.value("F(0)=", *d["F(0)"])
    c.value("F(2)=", *d["F(2)"])
    c.value("F(4)=", *d["F(4)"])
    c.finish()

    cid = "RV-C-E4"
    d = orc(cid)["display"]
    c = Case(cid + " area 0 and f<0 warnings", run(acts_C("PDF", [(0, 2, ["1", "-1"])], 0)))
    c.value("AREA=Σ∫f dx=", d["area"][0])
    c.text("WARNING AREA≠1 !")
    c.text("WARNING f<0 SOMEWHERE !")
    c.row("  x - (1/2)x²")
    c.text("x>2  F=" + d["F after last piece"][0])
    c.finish()

    cid = "RV-C-E5"
    orc(cid)
    a = [{"menu": 3}, {"menu": 1}, {"input": "1"}, {"input": "1"}, {"input": "0"}, {"input": "2"},
         {"input": "1"}, {"input": "1"}, {"input": "⁻1"}, BACK]
    c = Case(cid + " unknown c with area 0 -> c undefined", run(a))
    c.text("AREA=0 SO c=1/AREA IS")
    c.text("UNDEFINED (c UNDEF)")
    c.finish()

    # validation: bad piece count, lo>=hi, overlapping pieces, degree 4, a>b query
    a = [{"menu": 3}, {"menu": 1}, {"input": "0"}, {"input": "4"},
         {"input": "0"}, {"input": "2"},
         {"input": "2"}, {"input": "1"}, {"input": "0"},            # lo>=hi -> re-enter
         {"input": "0"}, {"input": "1"}, {"input": "4"},            # degree 4 -> re-enter
         {"input": "0"}, {"input": "1"}, {"input": "0"}, {"input": "1/2"},
         {"input": ".5"}, {"input": "2"}, {"input": "0"},           # overlaps -> re-enter
         {"input": "1"}, {"input": "2"}, {"input": "0"}, {"input": "1/2"},
         {"menu": 1}, {"input": "2"}, {"input": "1"},               # a>b
         {"menu": 5}, BACK]
    c = Case("C validation (pieces, lo/hi, degree, overlap, a>b)", run(a))
    c.text("PIECES MUST BE 1, 2 OR 3")
    c.text("NEED LO < HI AND")
    c.text("PIECES MUST GO LEFT TO")
    c.text("NEED a ≤ b")
    c.text("AREA=1 AND f≥0  OK")
    c.finish()
    # degree 3 with all terms, 3 pieces: pagination of the region screens
    c = Case("C 3 pieces deg 3 (pagination)",
             run(acts_C("PDF", [(0, 1, ["1", "2", "3", "4"]), (2, 3, ["1", "-2", "3", "-4"]),
                               (4, 5, ["1/3", "1/5", "1/7", "1/9"])], 1, [("F", 10)])))
    c.text("ENTER=MORE")
    c.text("x>5  F=1")
    c.value("F(10)=", "1")
    c.finish()
    c = Case("C menu BACK", run([{"menu": 3}, {"menu": 3}, BACK]))
    c.finish()


# ================================================================ tool D
def acts_D(mode, fx, lo, hi, unknown_c=0, queries=()):
    a = [{"menu": 4}, {"menu": 1 if mode == "PDF" else 2}, {"input": fx},
         {"input": str(lo).replace("-", "⁻")}, {"input": str(hi).replace("-", "⁻")}]
    if mode == "PDF":
        a.append({"input": str(unknown_c)})
    for q in queries:
        if q[0] == "ab":
            a += [{"menu": 1}, {"input": str(q[1]).replace("-", "⁻")}, {"input": str(q[2]).replace("-", "⁻")}]
        elif q[0] == "F":
            a += [{"menu": 2}, {"input": str(q[1]).replace("-", "⁻")}]
        elif q[0] == ">":
            a += [{"menu": 3}, {"input": str(q[1]).replace("-", "⁻")}]
        elif q[0] == "=":
            a += [{"menu": 4}, {"input": str(q[1]).replace("-", "⁻")}]
        elif q[0] == "f":
            a += [{"menu": 5}, {"input": str(q[1]).replace("-", "⁻")}]
    return a + [{"menu": 5 if mode == "PDF" else 6}, BACK]


def test_D():
    cid = "RV-D-S1"
    d = orc(cid)["display"]
    c = Case(cid + " CDF 1-e^(-2X) (HW3 431 Q6)",
             run(acts_D("CDF", "1-𝑒^(⁻2X)", 0, 50, queries=[(">", 1), ("f", 1)])))
    c.value("F(LO)=F(0)=", d["F(0)"][0])
    c.value("F(HI)=F(50)=", d["F(50)"][0])
    c.text("F GOES 0 TO 1  OK")
    c.absent("WARNING")
    c.text("P(X>1)=1-F(a)")
    c.value("=", *d["P(X>1)"])
    c.value("f(1)=", *d["f(1)"])
    c.finish()
    c2 = Case("HW3-431-Q6 (b) P(X>1)", c.res)
    c2.value("=", *orc("HW3-431-Q6")["display"]["(b) P(X>1)"])
    c2.finish()

    cid = "RV-D-S2"
    d = orc(cid)["display"]
    c = Case(cid + " PDF 3/256(16-X²)",
             run(acts_D("PDF", "3/256(16-X²)", -4, 4, 0, [("ab", -4, -2), ("ab", 1, 3), ("=", 0)])))
    c.value("AREA=∫f dx=", d["area"][0])
    c.text("AREA=1  OK")
    c.text("P(⁻4<X<⁻2)")
    c.value("=", *d["P(-4<X<-2)"])
    c.text("P(1<X<3)")
    c.value("=", "35/128")
    c.check(c.has("=.273438") or c.has("=.273437"), "P(1<X<3) decimal .273438/.273437")
    c.text("0 (continuous X)")
    c.finish()

    cid = "RV-D-S3"
    d = orc(cid)["display"]
    c = Case(cid + " PDF X² unknown c", run(acts_D("PDF", "X²", 0, 3, 1, [(">", 2)])))
    c.value("AREA=∫f dx=", d["area"][0])
    c.value("c=1/AREA=", *d["c"])
    c.text("=c*∫f FROM 2 TO 3")
    c.value("=", *d["P(X>2)"])
    c.finish()

    cid = "RV-D-E1"
    d = orc(cid)["display"]
    c = Case(cid + " PDF 2e^(-2X) on (0,50)",
             run(acts_D("PDF", "2𝑒^(⁻2X)", 0, 50, 0, [(">", 1), ("ab", 0, ".5"), ("F", ".5")])))
    c.value("AREA=∫f dx=", d["area"][0])
    c.value("=", *d["P(X>1)"])
    c.value("=", *d["P(0<X<.5)"])
    c.value("F(.5)=", *d["P(0<X<.5)"])
    c.finish()

    cid = "RV-D-E2"
    d = orc(cid)["display"]
    c = Case(cid + " interval outside support", run(acts_D("PDF", "X²", 0, 3, 1, [("ab", 4, 5), (">", 7)])))
    c.value("c=1/AREA=", *d["c"])
    c.text("  (OUTSIDE SUPPORT)")
    c.value("=", *d["P(4<X<5)"])
    c.text("=0 (PAST THE SUPPORT)")
    c.finish()

    cid = "RV-D-E3"
    d = orc(cid)["display"]
    c = Case(cid + " CDF X/2 on [0,1) warns F(hi)≠1",
             run(acts_D("CDF", "X/2", 0, 1, queries=[(">", ".5"), ("f", ".5"), ("f", 2)])))
    c.value("F(HI)=F(1)=", d["F(hi)"][0])
    c.text(" WARNING ≠1 - JUMP AT HI")
    c.value("=", *d["P(X>.5)"])
    c.value("f(.5)=", *d["f(.5)"])
    c.value("f(2)=", "0")
    c.text("(OUTSIDE (LO,HI) => 0)")
    c.finish()

    cid = "RV-D-E4"
    d = orc(cid)["display"]
    c = Case(cid + " CDF (X+2)/4 on [-2,2)",
             run(acts_D("CDF", "(X+2)/4", -2, 2, queries=[("ab", -1, 1), (">", ".5"), ("f", 0), ("F", 5), ("F", -3)])))
    c.text("P(⁻1<X≤1)=F(b)-F(a)")
    c.value("=", *d["P(-1<X<=1)"])
    c.value("=", *d["P(X>.5)"])
    c.value("f(0)=", *d["f(0)"])
    c.value("F(5)=", "1")
    c.value("F(⁻3)=", "0")
    c.finish()

    # validation: lo>=hi, unknown c with zero area, a>b
    a = [{"menu": 4}, {"menu": 1}, {"input": "X"}, {"input": "2"}, {"input": "1"},
         {"input": "X"}, {"input": "⁻1"}, {"input": "1"}, {"input": "1"}, BACK]
    c = Case("D reject lo>=hi, then c undefined (area 0)", run(a))
    c.text("NEED LOW END < HIGH END")
    c.text("UNDEFINED (c UNDEF)")
    c.finish()
    a = acts_D("PDF", "1", 0, 1, 0, [("ab", 1, 0)])
    c = Case("D reject a>b", run(a))
    c.text("NEED a ≤ b")
    c.finish()
    c = Case("D menu BACK", run([{"menu": 4}, {"menu": 3}, BACK]))
    c.finish()


# ================================================================ tool E
def acts_E(fx, lo, hi, h, g, ys):
    a = [{"menu": 5}, {"input": fx}, {"input": str(lo)}, {"input": str(hi)}, {"input": h},
         {"menu": 1 if g == "INCREASING" else 2}]
    for i, y in enumerate(ys):
        a.append({"input": str(y).replace("-", "⁻")})
        a.append({"menu": 1 if i + 1 < len(ys) else 2})
    return a + [BACK]


def test_E():
    for cid in ["RV-E-S1", "RV-E-S2", "RV-E-E1", "RV-E-E2", "RV-E-E3", "RV-E-E4"]:
        o = orc(cid)
        i, d = o["inputs"], o["display"]
        c = Case(f"{cid} fX={i['fX']} h={i['h']} {i['g']} y={i['y']}",
                 run(acts_E(i["fX"], i["lo"], i["hi"], i["h"], i["g"], [i["y"]])))
        c.value("x=h(y)=", d["x=h(y)"][0])
        c.text("F_Y(y)=F_X(x)" if i["g"] == "INCREASING" else "F_Y(y)=1-F_X(x)")
        if "F_X(x)" in d:
            c.text("F_X(x)=∫f_X FROM LO TO x")
            c.value(" =", *d["F_X(x)"])
        c.value(" =", *d["F_Y(y)"])
        c.text("f_Y(y)=f_X(x)*|h'(y)|")
        c.value(" =", *d["f_Y(y)"])
        if cid == "RV-E-E2":
            c.text("x NOT IN SUPPORT => f_Y=0")
        c.finish()
    # SPEC: y=1 then ANOTHER y=.5 in one session
    c = Case("E two y values in one session (SPEC)", run(acts_E("2X", 0, 1, "𝑒^(⁻X)", "DECREASING", [1, ".5"])))
    c.value(" =", ".864665")
    c.value(" =", ".270671")
    c.value(" =", ".632121")
    c.value(" =", ".735759")
    c.text("TRANSFORM Y=g(X)       1/2")
    c.text("MONOTONE SHORTCUT      2/2")
    c.finish()
    c2 = Case("HW3-631-Q5 F_Y(1), f_Y(1)", c.res)
    o = orc("HW3-631-Q5")["display"]
    c2.value(" =", *o["F_Y(1)"])
    c2.value(" =", *o["f_Y(1)"])
    c2.finish()
    a = [{"menu": 5}, {"input": "1"}, {"input": "1"}, {"input": "0"},
         {"input": "1"}, {"input": "0"}, {"input": "1"}, {"input": "X²"}, {"menu": 1},
         {"input": ".5"}, {"menu": 2}, BACK]
    c = Case("E reject lo>=hi then uniform, Y=√X (h=X²)", run(a))
    c.text("NEED LOW END < HIGH END")
    c.value(" =", "1/4", ".25")
    c.finish()


# ================================================================ misc
def test_misc():
    c = Case("main menu BACK immediately", run([BACK]))
    c.check(c.res.screens[0]["menu"]["items"] == ["PMF TABLE + CDF", "MAX/MIN/SUM DRAWS", "POLY PDF/CDF",
                                                  "ANY f(x) OR F(x)", "TRANSFORM Y=g(X)", "JOINT X,Y", "BACK"],
            "main menu text/order")
    c.finish()
    # several tools in one session, then BACK: all lists deleted
    a = acts_A(1, [1, 2], [".5", ".5"])[:-1] + acts_B("MAXIMUM", 3, 2, "WITH")[:-1] + \
        acts_C("PDF", [(0, 1, ["1"])], 0)[:-1] + [BACK]
    c = Case("A+B+C in one session then BACK deletes lists", run(a))
    c.finish()


if __name__ == "__main__":
    test_A()
    test_B()
    test_C()
    test_D()
    test_E()
    test_misc()
    missing = sorted(set(OR) - USED)
    if missing:
        RESULTS.append(("oracle coverage", False, [f"not tested: {missing}"]))
        print("FAIL oracle coverage: " + ", ".join(missing))
    else:
        print(f"PASS oracle coverage ({len(OR)} STARV oracle cases)")
    npass = sum(1 for r in RESULTS if r[1])
    print(f"\n{npass}/{len(RESULTS)} passed")
    sys.exit(0 if npass == len(RESULTS) else 1)
