#!/usr/bin/env python3
"""
tests/test_tisim.py - self-test of the TI-BASIC simulator (tools/tisim.py) and of the static linter
(tools/tilint.py), a >=300-value sweep of src/STAFMT.txt against an independent Python reference of the
formatter contract (SPEC section 3), and STA431 -> encyclopedia navigation (STAE1-3).

Run:   $PY tests/test_tisim.py [-v]          prints PASS/FAIL lines, exit 1 if anything failed.
"""
import os
import re
import sys
import random
from decimal import Decimal, localcontext, ROUND_HALF_UP
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from tisim import Sim, TIError, fmt_num  # noqa: E402
import tilint  # noqa: E402

VERBOSE = "-v" in sys.argv
NEG, EE = "⁻", "ᴇ"
N_PASS = N_FAIL = 0
FAILS = []


def check(name, cond, detail=""):
    global N_PASS, N_FAIL
    if cond:
        N_PASS += 1
        print(f"PASS {name}")
    else:
        N_FAIL += 1
        FAILS.append(name)
        print(f"FAIL {name}" + (f"  -- {detail}" if detail else ""))
    return cond


_uid = [0]


def run_src(text, actions=(), init=None, max_steps=200_000, extra=None):
    """Run a snippet as a uniquely named in-memory program in a FRESH Sim (src/ also searchable)."""
    _uid[0] += 1
    name = f"TT{_uid[0]:04d}"
    sim = Sim(SRC)
    for k, v in (extra or {}).items():
        sim.add_program(k, v)
    sim.add_program(name, text)
    return sim.run(name, list(actions), max_steps=max_steps, init_vars=init)


def ev(expr, init=None):
    return Sim(SRC).eval(expr, init_vars=init)


def near(a, b, tol=1e-9):
    try:
        return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))
    except (TypeError, ValueError):
        return False


def ok(res):
    return res.error is None and res.leaks == 0


def why(res):
    return f"error={res.error} leaks={res.leaks} ended={res.ended_reason}"


# =========================================================================================== 1. order of ops
def test_order_of_operations():
    X3 = {"X": 3}
    cases = [
        ("⁻2²", -4, None), ("5 nCr 2*2", 20, None), ("2*5 nCr 2", 20, None), ("4 nCr 2 nCr 2", 15, None),
        ("5 nPr 2", 20, None), ("5 nCr 7", 0, None), ("2(3+4)", 14, None), ("6/2(1+2)", 9, None),
        ("1/2X", 1.5, X3), ("2X²", 18, X3), ("⁻X²", -9, X3), ("2^3^2", 64, None), ("3!²", 36, None),
        ("2^⁻1", 0.5, None), ("⁻2^2", -4, None), ("(⁻2)^2", 4, None), ("2+3*4", 14, None),
        ("10-2-3", 5, None), ("12/2/3", 2, None), ("3-⁻2", 5, None), ("1+2=3", 1, None),
        ("3>2+2", 0, None), ("2<3 and 3<2", 0, None), ("1 or 0 xor 1", 0, None), ("not(0)+1", 2, None),
        ("2X(X+1)", 24, X3), ("√(16)+1", 5, None), ("2pi", 6.283185307179586, None),
        ("𝑒^(0)+ln(1)", 1, None), ("abs(⁻3)+int(⁻2.5)", 0, None), ("iPart(⁻2.5)", -2, None),
        ("fPart(⁻2.5)", -0.5, None), ("round(2/3,6)", 0.666667, None), ("remainder(17,5)", 2, None),
        ("max(2,7)-min({4,1,9})", 6, None), ("sum({1,2,3})*dim({5,6})", 12, None),
    ]
    bad = []
    for e, want, init in cases:
        try:
            got = ev(e, init)
            if not near(got, want, 1e-12):
                bad.append(f"{e}={got} (want {want})")
        except TIError as ex:
            bad.append(f"{e}: {ex}")
    check(f"order of operations: {len(cases)} expressions (eval)", not bad, "; ".join(bad))
    # the same inside a PROGRAM (program-mode tokenization)
    r = run_src("⁻2²→A\n5 nCr 2*2→B\n2(3+4)→C\n3→X\n2X²→D\n1/2X→E\n6/2(1+2)→F")
    got = [r.var(v) for v in "ABCDEF"]
    check("order of operations inside a program (⁻2²=-4, 5 nCr 2*2=20, implied mult)",
          ok(r) and got == [-4, 20, 14, 18, 1.5, 9], f"{got} {why(r)}")
    r = run_src("{1,2,3}*2+{1,1,1}→ʟTST\nseq(I²,I,1,4)→ʟTSQ\ncumSum(ʟTSQ)→ʟTCS")
    check("list arithmetic, seq(, cumSum(", ok(r) and r.var("ʟTST") == [3, 5, 7] and r.var("ʟTSQ") ==
          [1, 4, 9, 16] and r.var("ʟTCS") == [1, 5, 14, 30], why(r))


# =========================================================================================== 2. control flow
def test_control_flow():
    src = "If A=1\nThen\n10→B\nElse\n20→B\nEnd"
    r1, r0 = run_src(src, init={"A": 1}), run_src(src, init={"A": 0})
    check("If-Then-Else both branches", ok(r1) and ok(r0) and r1.var("B") == 10 and r0.var("B") == 20,
          f"{r1.var('B')} {r0.var('B')}")
    r = run_src("0→B\nIf 0\n1→B\n2→C\nIf 1:3→D")
    check("one-line If controls exactly one statement", ok(r) and (r.var("B"), r.var("C"), r.var("D")) ==
          (0, 2, 3), why(r))
    r = run_src("0→S\nFor(I,1,5)\nS+I→S\nEnd")
    check("For( sum and final counter (I = last+step)", ok(r) and r.var("S") == 15 and r.var("I") == 6,
          f"S={r.var('S')} I={r.var('I')}")
    r = run_src("For(I,5,1)\n1→Z\nEnd\n0→S\nFor(J,5,1,⁻2)\nS+J→S\nEnd")
    check("For( zero-trip loop and negative step", ok(r) and r.var("Z") == 0 and r.var("I") == 5 and
          r.var("S") == 9 and r.var("J") == -1, f"Z={r.var('Z')} I={r.var('I')} S={r.var('S')} J={r.var('J')}")
    r = run_src("0→N\nWhile N<3\nN+1→N\nEnd\n0→M\nWhile 0\n1→M\nEnd\n0→P\nRepeat 1\nP+1→P\nEnd")
    check("While pre-test / Repeat post-test", ok(r) and (r.var("N"), r.var("M"), r.var("P")) == (3, 0, 1),
          why(r))
    r = run_src("0→C\nFor(I,1,4)\nFor(J,1,I)\nIf remainder(J,2)=0\nThen\nC+1→C\nEnd\nEnd\nEnd")
    check("nested For( with If-Then inside", ok(r) and r.var("C") == 4, f"C={r.var('C')}")
    r = run_src("If 1\nThen\n1→A\nElse\nFor(I,1,3)\n5→A\nEnd\nEnd\nIf 0\nThen\n7→B\nElse\nWhile 0\nEnd\n8→B\nEnd")
    check("Else skipping over nested blocks", ok(r) and r.var("A") == 1 and r.var("B") == 8, why(r))
    r = run_src("0→N\nLbl A\nN+1→N\nIf N<5\nGoto A\n1→A:2→B")
    check("backward Goto loop at depth 0 and ':' separators", ok(r) and r.var("N") == 5 and r.var("B") == 2,
          why(r))
    sub = "A*2→A\nReturn\n99→A"
    r = run_src("3→A\nprgmTSUB1\nA+1→A", extra={"TSUB1": sub})
    check("prgm call shares globals and Return goes back to the caller", ok(r) and r.var("A") == 7,
          f"A={r.var('A')} {why(r)}")
    r = run_src("prgmTSUB2\n5→A", extra={"TSUB2": "1→A\nStop"})
    check("Stop in a subprogram ends everything", r.ended_reason == "stop" and r.var("A") == 1, why(r))
    r = run_src("Lbl A\nGoto A", max_steps=5000)
    check("step limit -> ended_reason max_steps", r.ended_reason == "max_steps", why(r))


# =========================================================================================== 3. Menu flow
MENU_SRC = """0→N
Lbl M
Menu("TEST MENU","ONE",A,"TWO",B,"QUIT",Q)
Lbl A
N+1→N
Goto M
Lbl B
N+10→N
Goto M
Lbl Q
Disp N"""


def test_menu():
    r = run_src(MENU_SRC, [{"menu": 1}, {"menu": 2}, {"menu": 1}, {"menu": 3}])
    menus = [s for s in r.screens if s["event"] == "menu"]
    check("Menu( flow: 1,2,1,3 -> N=12, 4 menu snapshots, no leaks",
          ok(r) and r.var("N") == 12 and len(menus) == 4 and r.ended_reason == "end", why(r))
    m = menus[0] if menus else {"rows": [""] * 10, "menu": {}}
    check("Menu snapshot = title row + numbered items",
          m["rows"][0].rstrip() == "TEST MENU" and m["rows"][1].rstrip() == "1:ONE" and
          m["menu"].get("labels") == ["A", "B", "Q"], str(m["rows"][:4]))
    r = run_src(MENU_SRC, [{"menu": 4}])
    check("Menu choice out of range -> SIM:ACTION error", r.error is not None and r.error.startswith("SIM:"),
          str(r.error))
    r = run_src(MENU_SRC, [{"input": "1"}])
    check("Menu with a non-menu action at the head -> SIM:ACTION error",
          r.error is not None and r.error.startswith("SIM:"), str(r.error))
    r = run_src(MENU_SRC, [{"menu": 1}])
    check("empty action queue at a Menu -> out_of_actions (screen recorded)",
          r.ended_reason == "out_of_actions" and r.error is None and r.screens[-1]["event"] == "menu", why(r))


# =========================================================================================== 4. Input
def test_input():
    src = ('ClrHome\nInput "N?",N\nInput "P?",P\nInput "WORD?",Str1\nInput "L?",ʟTST\nPrompt A\n'
           'Input "E?",E\nInput "I?",I')
    acts = [{"input": "3/16"}, {"input": "⁻1"}, {"input": "HELLO"}, {"input": "{1,2,3}"},
            {"input": "⁻2.5"}, {"input": "2+3*4"}, {"input": 5}]
    r = run_src(src, acts)
    check("Input to reals: '3/16' -> .1875, '⁻1' -> -1, expression, number",
          ok(r) and r.var("N") == 0.1875 and r.var("P") == -1 and r.var("E") == 14 and r.var("I") == 5,
          why(r))
    check("Input to a string var and a named list; Prompt",
          r.var("Str1") == "HELLO" and r.var("ʟTST") == [1, 2, 3] and r.var("A") == -2.5, why(r))
    ins = [s for s in r.screens if s["event"] == "input"]
    check("Input snapshots carry the prompt and echo the prompt on screen",
          len(ins) == 7 and ins[0]["prompt"] == "N?" and ins[0]["rows"][0].startswith("N?"),
          str([s.get("prompt") for s in ins]))
    r = run_src('Input "N?",N', [{"input": "-1"}])
    check("typing '-1' (binary minus) into Input -> ERR:SYNTAX", r.error is not None and
          r.error.startswith("ERR:SYNTAX"), str(r.error))
    r = run_src('Input "N?",N\nInput "M?",M', [{"input": "2"}])
    check("Input with empty queue -> out_of_actions", r.ended_reason == "out_of_actions" and r.var("N") == 2,
          why(r))


# =========================================================================================== 5. screen
def test_screen():
    r = run_src('ClrHome\nOutput(1,24,"ABCDEF")\nOutput(3,1,1/4)\nOutput(10,25,"XYZ")\nPause')
    rows = r.screens[0]["rows"] if r.screens else [""] * 10
    check("Output( wraps to the next row at column 26",
          ok(r) and rows[0][23:26] == "ABC" and rows[1][0:3] == "DEF", str(rows[:2]))
    check("Output( of a number is left-aligned at its position", rows[2][:3] == ".25", repr(rows[2]))
    check("Output( past row 10 col 26 is clipped",
          rows[9][24:26] == "XY" and len(rows) == 10 and all(len(x) == 26 for x in rows), repr(rows[9]))
    check("Output wrap/clip reported in res.warnings",
          any("wraps" in w for w in r.warnings) and any("clipped" in w for w in r.warnings), str(r.warnings))
    r = run_src('ClrHome\nDisp "HI",42\nPause')
    rows = r.screens[0]["rows"]
    check("Disp: strings left-aligned, numbers right-aligned", rows[0].startswith("HI ") and
          rows[1].endswith("42") and rows[1].startswith(" "), str(rows[:2]))
    r = run_src("ClrHome\nFor(I,1,12)\nDisp I\nEnd\nPause")
    rows = r.screens[0]["rows"]
    check("Disp scrolls after 10 lines", rows[0].strip() == "3" and rows[9].strip() == "12", str(rows))
    r = run_src('ClrHome\nDisp "ABCDEFGHIJKLMNOPQRSTUVWXYZ12"\nPause')
    check("Disp string > 26 chars is cut and warned",
          r.screens[0]["rows"][0] == "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and r.warnings, str(r.warnings))
    r = run_src('Disp "A"\nPause\nClrHome\nPause 5')
    p = [s for s in r.screens if s["event"] == "pause"]
    check("Pause snapshots; ClrHome clears; Pause value displayed",
          len(p) == 2 and p[0]["rows"][0].startswith("A") and p[1]["rows"][0].strip() == "5",
          str([s["rows"][0] for s in p]))
    r = run_src("5+5")
    check("program end shows the last bare expression value", r.screens[-1]["rows"][0].strip() == "10",
          repr(r.screens[-1]["rows"][0]))


# =========================================================================================== 6. toString
def test_tostring():
    cases = [("1/3", ".3333333333"), ("2/3", ".6666666667"), ("⁻.5", "⁻.5"), ("1.5ᴇ12", "1.5ᴇ12"),
             (".00012", "1.2ᴇ⁻4"), (".001", ".001"), ("9.99ᴇ⁻4", "9.99ᴇ⁻4"), ("1ᴇ10", "1ᴇ10"),
             ("9999999999", "9999999999"), ("12345678901", "1.23456789ᴇ10"), ("0", "0"), ("100", "100"),
             ("⁻3", "⁻3"), ("1/7", ".1428571429"), ("123.456", "123.456"), ("20/3", "6.666666667"),
             ("69!", "1.711224524ᴇ98"), ("round(2/3,6)", ".666667"), ("⁻1ᴇ⁻12", "⁻1ᴇ⁻12"),
             ("2^40", "1.099511628ᴇ12"), ("1-1ᴇ⁻11", "1"), ("12 nCr 3", "220")]
    bad = []
    for e, want in cases:
        try:
            got = ev(f"toString({e})").text
        except TIError as ex:
            got = str(ex)
        if got != want:
            bad.append(f"toString({e})={got!r} want {want!r}")
    check(f"toString( TI formatting: {len(cases)} values", not bad, "; ".join(bad))
    r = run_src('"P="+toString(3/4)→Str1\nsub(Str1,3,3)→Str2\nlength(Str1)→L\ninString(Str1,"=")→K')
    check("string ops: concatenation, sub(, length(, inString(", ok(r) and r.var("Str1") == "P=.75" and
          r.var("Str2") == ".75" and r.var("L") == 5 and r.var("K") == 2, why(r))
    check("fmt_num helper matches toString", fmt_num(Decimal("-0.25")) == "⁻.25", fmt_num(Decimal("-0.25")))


# =========================================================================================== 7. fnInt / nDeriv
def test_calculus():
    cases = [("fnInt(3/256*(16-X²),X,⁻4,⁻2)", 0.15625, 1e-10),
             ("fnInt(3/256*(16-X²),X,1,3)", 0.2734375, 1e-10),
             ("fnInt(X²,X,0,3)", 9, 1e-10), ("fnInt(𝑒^(⁻X),X,0,50)", 1.0, 1e-10),
             ("fnInt(1/X,X,1,𝑒^(1))", 1.0, 1e-10), ("fnInt(√(X),X,0,4)", 16 / 3, 1e-8),
             ("1-fnInt(2X,X,0,𝑒^(⁻1))", 0.8646647167633873, 1e-10),
             ("nDeriv(X³,X,2)", 12.000001, 1e-12),
             ("round(nDeriv(1-𝑒^(⁻2X),X,1),6)", 0.270671, 0)]
    bad = []
    for e, want, tol in cases:
        try:
            got = ev(e)
            if not near(got, want, tol if tol else 1e-15):
                bad.append(f"{e}={got} want {want}")
        except TIError as ex:
            bad.append(f"{e}: {ex}")
    check(f"fnInt( / nDeriv( ({len(cases)} cases)", not bad, "; ".join(bad))
    r = run_src('"2X"→Str1\nStr1→Y₉\nfnInt(Y₉,X,0,1)→A\nY₉(3)→B\n"𝑒^(⁻X)"→Str2\nStr2→Y₀\n'
                'abs(nDeriv(Y₀,X,1))*Y₉(𝑒^(⁻1))→C\nFnOff 9,0')
    check("Y₉/Y₀ from strings: fnInt(Y₉..), Y₉(3), f_Y = f_X(h(y))|h'(y)| (SPEC RV>E y=1 -> .270671)",
          ok(r) and near(r.var("A"), 1) and r.var("B") == 6 and round(r.var("C"), 6) == 0.270671,
          f"A={r.var('A')} B={r.var('B')} C={r.var('C')} {why(r)}")


# =========================================================================================== 8. leaks
def test_leaks():
    r = run_src("For(I,1,3)\nGoto A\nEnd\nLbl A\n1→B")
    check("Goto out of a For( loop -> leaks == 1", r.error is None and r.leaks == 1, why(r))
    r = run_src('While 1\nMenu("M","X",A)\nEnd\nLbl A', [{"menu": 1}])
    check("Menu( inside While -> leaks == 1", r.error is None and r.leaks == 1, why(r))
    r = run_src("If 1\nThen\nGoto A\nEnd\nLbl A")
    check("Goto out of If-Then -> leaks == 1", r.error is None and r.leaks == 1, why(r))
    r = run_src("If 1\nGoto A\nDisp 0\nLbl A\nIf 1:Goto B\nLbl B")
    check("one-line If + Goto at depth 0 -> leaks == 0", ok(r), why(r))
    r = run_src("0→S\nFor(I,1,3)\nIf I=2\nGoto A\nS+1→S\nLbl A\nEnd")
    check("Goto to a label inside the SAME loop body is not a leak", ok(r) and r.var("S") == 2 and
          r.var("I") == 4, f"S={r.var('S')} {why(r)}")
    r = run_src("Lbl A\nWhile 1\nGoto A\nEnd", max_steps=100_000)
    check("repeated leaking Goto -> ERR:MEMORY", r.error is not None and r.error.startswith("ERR:MEMORY"),
          why(r))


# =========================================================================================== 9. errors
def test_errors():
    cases = [
        ("-1→A", "ERR:SYNTAX", "binary minus at expression start"),
        ("2*-3→A", "ERR:SYNTAX", "binary minus after *"),
        ("Disp a", "ERR:SYNTAX", "lowercase letter outside a string"),
        ("2b→A", "ERR:SYNTAX", "lowercase letter in an expression"),
        ("Goto Q9", "ERR:LABEL", "missing label"),
        ('Menu("T","X",ZZ)', "ERR:LABEL", "Menu( target missing"),
        ("Disp Str5", "ERR:UNDEFINED", "undefined string"),
        ("Disp ʟNOPE", "ERR:UNDEFINED", "undefined list"),
        ("1/0→A", "ERR:DIVIDE BY 0", "divide by zero"),
        ('Output(11,1,"X")', "ERR:DOMAIN", "Output row 11"),
        ("2.5 nCr 1→A", "ERR:DOMAIN", "non-integer nCr"),
        ("70!→A", "ERR:OVERFLOW", "70!"),
        ("√(⁻1)→A", "ERR:NONREAL ANS", "sqrt of negative"),
        ("(2+3→A", "ERR:SYNTAX", "unclosed parenthesis (strict)"),
        ("Disp 1\nThen\nEnd", "ERR:SYNTAX", "Then without If"),
        ("End", "ERR:SYNTAX", "End without block"),
        ("{1,2}→ʟTA\n5→ʟTA(4)", "ERR:INVALID DIM", "list store beyond dim+1"),
    ]
    for src, want, what in cases:
        r = run_src(src, [{"menu": 1}])
        check(f"error detection: {what} -> {want}", r.error is not None and r.error.startswith(want) and
              r.ended_reason == "error", str(r.error))
    r = run_src("1→A\n// comment\n\nDisp Str5")
    check("error text names program and ORIGINAL source line", r.error is not None and
          re.search(r"at TT\d+ line 4: Disp Str5", r.error) is not None, str(r.error))
    r = run_src("prgmTERR1", extra={"TERR1": "1→A\n1/0→B"})
    check("error inside a called program is located in that program", r.error is not None and
          "at TERR1 line 2" in r.error, str(r.error))
    r = run_src("{1,2}→ʟTA\n5→ʟTA(3)\nPause\nDisp 1")
    check("list store at dim+1 extends; bare Pause gets its trailing space",
          ok(r) and r.var("ʟTA") == [1, 2, 5], why(r))


# =========================================================================================== 10. Sim reuse fix
def test_sim_reuse():
    sim = Sim(SRC)
    sim.add_program("TREUSE", "A+1→A\nDisp A")
    r1 = sim.run("TREUSE", init_vars={"A": 5})
    r2 = sim.run("TREUSE", init_vars={"A": 10})
    check("same Sim, same program, 2nd run uses its own variables (stale-closure fix)",
          r1.var("A") == 6 and r2.var("A") == 11, f"{r1.var('A')} {r2.var('A')}")
    sim.add_program("TREUSE", "A+2→A")
    r3 = sim.run("TREUSE", init_vars={"A": 10})
    check("add_program with an existing name replaces the program", r3.var("A") == 12, str(r3.var("A")))
    a = sim.run("STAFMT", init_vars={"W": "1/3"}).var("Str9")
    b = sim.run("STAFMT", init_vars={"W": "3/4"}).var("Str9")
    check("repeated runs of a src program on one Sim are independent", (a, b) == ("1/3", "3/4"), f"{a} {b}")


# =========================================================================================== 11. STAFMT sweep
def ref_tistr(d):
    """Independent TI Normal/Float display of a Decimal (10 significant digits)."""
    d = Decimal(d)
    if d == 0:
        return "0"
    sign = NEG if d < 0 else ""
    with localcontext() as c:
        c.prec, c.rounding = 10, ROUND_HALF_UP
        a = +abs(d)
    if Decimal("0.001") <= a < Decimal("1e10"):
        s = format(a, "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        if s.startswith("0."):
            s = s[1:]
        return sign + s
    e = a.adjusted()
    ms = format(a.scaleb(-e), "f")
    if "." in ms:
        ms = ms.rstrip("0").rstrip(".")
    return sign + ms + EE + (NEG + str(-e) if e < 0 else str(e))


def ref_str8(W):
    """Str8 contract: round(W,6) displayed; W itself when |W|<1E-4 or |W|>=1E10."""
    W = Decimal(W)
    if Decimal("1e-4") <= abs(W) < Decimal("1e10"):
        with localcontext() as c:
            c.prec = 60
            return ref_tistr(W.quantize(Decimal("1e-6"), rounding=ROUND_HALF_UP))
    return ref_tistr(W)


def exact_text(F):
    s = ref_tistr(Decimal(abs(F.numerator)))
    if F < 0:
        s = NEG + s
    return s if F.denominator == 1 else s + "/" + str(F.denominator)


def ref_expected(W, exact):
    """Formatter CONTRACT by construction (SPEC section 3): returns (set of accepted Str9, Str8).
    exact = the value W is meant to represent (Fraction), or None for irrational / non-representable values.
      * exact with reduced denominator <= 9999: Str9 = "N/D" (or the integer).  For |W| >= 1000 the
        decimal is accepted too (14-digit arithmetic cannot certify N/D there), but never another fraction
      * otherwise Str9 = Str8 (decimal) - a fraction that is not the value must never be shown
      * every nonzero W remains nonzero in Str9, including tiny probabilities"""
    str8 = ref_str8(W)
    ok9 = {str8}
    if exact is not None and exact.denominator <= 9999:
        ok9 = {exact_text(exact)}
        if abs(W) >= 1000:
            ok9.add(str8)
    return ok9, str8


def ti_div(p, q):
    with localcontext() as c:
        c.prec, c.rounding = 14, ROUND_HALF_UP
        return Decimal(p) / Decimal(q)


def typed(n):
    return (NEG + str(-n)) if n < 0 else str(n)


def lit_frac(s):
    return Fraction(Decimal(s.replace(NEG, "-").replace(EE, "E")))


def sweep_values():
    """[(typed W, exact Fraction or None, group)]; group 'core' = the app's domain (0, 1E-4<=|W|<50,
    integers), 'edge' = large non-integers (|W|>=50) and tiny non-zero values (|W|<1E-4)."""
    vals, seen = [], set()

    def add(text, exact):
        try:
            mag = abs(float(exact)) if exact is not None else abs(float(ev(text)))
        except TIError:
            mag = 1.0
        integer = exact is not None and exact.denominator == 1
        core = integer or mag == 0 or 1e-4 <= mag < 50
        vals.append((text, exact, "core" if core else "edge"))

    for q in range(1, 13):
        for p in range(-2 * q, 2 * q + 1):
            if (p, q) not in seen:
                seen.add((p, q))
                add(f"{typed(p)}/{q}", Fraction(p, q))
    rnd = random.Random(431)
    for _ in range(160):
        q = rnd.choice([rnd.randint(13, 99), rnd.randint(100, 999), rnd.randint(1000, 9999)])
        p = rnd.randint(-3 * q, 3 * q)
        add(f"{typed(p)}/{q}", Fraction(p, q))
    for p, q in [(147, 10000), (2162, 54145), (1, 10007), (12345, 10001), (9999, 10000), (1, 20000),
                 (3, 20000), (7, 100000), (22, 7), (355, 113), (104348, 33215), (1, 9999), (9998, 9999),
                 (1710, 1909), (95, 294), (100, 143), (175, 2584), (15, 34), (35, 128), (19, 27), (5, 32),
                 (9979200, 1), (612360, 1), (123456789, 7), (1, 3000), (2, 30001), (4999, 9998),
                 (20000, 3), (12345, 7), (98765, 4321), (1000000, 9999)]:
        add(f"{p}/{q}", Fraction(p, q))
    for e in ["√(2)", "√(3)/2", "pi", "pi/4", "𝑒^(⁻2)", "2𝑒^(⁻1)", "ln(2)", "1-𝑒^(⁻2)", "⁻√(5)",
              "1/3+1ᴇ⁻9", "1/3+2ᴇ⁻10", "√(2)*100", "pi*1000", "𝑒^(5)", "ln(12345)*10"]:
        add(e, None)
    for k in range(2, 200, 5):                   # irrational values 1..1000 (SD, E[X], e^x ...)
        if int(k ** 0.5) ** 2 != k:
            add(f"√({k})", None)
    for k in range(1, 49, 2):
        add(f"𝑒^({k}/7)", None)
        add(f"ln({k + 1})*{k}", None)
    for e, exact in [("1/3+1ᴇ⁻12", Fraction(1, 3)), (".27343749999", Fraction(35, 128)),
                     (".2734375000001", Fraction(35, 128)), ("1/7+3ᴇ⁻11", Fraction(1, 7)),
                     ("1ᴇ⁻15", None)]:
        add(e, exact)                           # numeric-noise versions of exact values
    for e in ["3ᴇ⁻11", "1ᴇ⁻11", "5ᴇ⁻12", "1ᴇ⁻5", "5ᴇ⁻5", "1.5ᴇ⁻4", "9.99ᴇ⁻5", "1ᴇ⁻4", "1ᴇ10",
              "12345678901", "9999999999", "123456.789", "⁻98765.4321", "0", "5000000.00005", "2.5ᴇ15",
              ".999999999999", "⁻.0005", "1/1024", "1/4096", "3/8192", "1234.5", "⁻64.125", "51.2"]:
        add(e, lit_frac(e) if "/" not in e else Fraction(e.replace(NEG, "-")))
    for _ in range(40):                          # random 6-decimal values in the E[X]/Var range
        e = f"{rnd.randint(50, 99999)}.{rnd.randint(0, 999999):06d}"
        add(e, lit_frac(e))
    add("1ᴇ12/7", None)
    return vals


SPEC_FACTS = [  # (W typed, Str9, Str8 or tuple of accepted Str8)
    ("147/10000", ".0147", ".0147"), ("2162/54145", ".03993", ".03993"),
    ("1710/1909", "1710/1909", ".895757"), ("95/294", "95/294", ".323129"),
    ("100/143", "100/143", ".699301"), ("175/2584", "175/2584", ".067724"),
    ("15/34", "15/34", ".441176"), ("35/128", "35/128", (".273438", ".273437")),
    ("9979200", "9979200", "9979200"), ("612360", "612360", "612360"), ("⁻1/2", "⁻1/2", "⁻.5"),
    ("0", "0", "0"), ("𝑒^(⁻2)", ".135335", ".135335"), ("19/27", "19/27", ".703704"),
    ("17/100", "17/100", ".17"), ("3/25", "3/25", ".12"),
]

FORMAT_REGRESSIONS = [
    ("√(2)*100", "141.421356"),
    ("pi*1000", "3141.592654"),
    ("123456.789", "123456.789"),
    ("3ᴇ⁻11", "3ᴇ⁻11"),
    ("1ᴇ⁻15", "1ᴇ⁻15"),
    ("⁻1ᴇ⁻15", "⁻1ᴇ⁻15"),
    ("1/3", "1/3"),
    ("⁻355/113", "⁻355/113"),
]


def sweep(sim, vals):
    """-> dict: errors, wrong_w, exact (fractions/integers not shown exactly), spurious (non-fractions shown
    as a fraction or 0), str8 (decimal form wrong)"""
    out = {"errors": [], "wrong_w": [], "exact": [], "spurious": [], "str8": []}
    for text, exact, _group in vals:
        r = sim.run("STAFMT", init_vars={"W": text}, max_steps=20_000)
        if r.error or r.leaks:
            out["errors"].append(f"W={text}: {why(r)}")
            continue
        W = r.raw_vars["reals"]["W"]
        if exact is not None and re.fullmatch(r"⁻?\d+/\d+", text):
            if W != ti_div(exact.numerator, exact.denominator):
                out["wrong_w"].append(f"{text}: W={W}")
        got9, got8 = r.var("Str9"), r.var("Str8")
        ok9, want8 = ref_expected(W, exact)
        if got8 != want8:
            out["str8"].append(f"W={text}: Str8 {got8!r} want {want8!r}")
        if got9 not in ok9:
            kind = "exact" if exact is not None and exact.denominator <= 9999 else "spurious"
            out[kind].append(f"W={text}: Str9 {got9!r} want {'|'.join(sorted(ok9))!r}")
    return out


def test_stafmt():
    path = os.path.join(SRC, "STAFMT.txt")
    if not os.path.exists(path):
        check("STAFMT sweep", False, "src/STAFMT.txt missing")
        return
    sim = Sim(SRC)       # one Sim for the whole sweep (exercises the reuse fix)
    vals = sweep_values()
    n_ex = sum(1 for _, e, _ in vals if e is not None and e.denominator <= 9999)
    res = sweep(sim, vals)
    check(f"STAFMT sweep runs cleanly on {len(vals)} values (no error, no leak)", not res["errors"],
          "; ".join(res["errors"][:5]))
    check("STAFMT sweep: W unchanged and equal to the 14-digit quotient", not res["wrong_w"],
          "; ".join(res["wrong_w"][:5]))
    check(f"STAFMT sweep: Str8 = round(W,6) display for all {len(vals)} values", not res["str8"],
          " | ".join(res["str8"][:6]))
    check(f"STAFMT sweep: {n_ex} fractions (D<=9999) / integers shown exactly in Str9", not res["exact"],
          " | ".join(res["exact"][:6]))
    check(f"STAFMT sweep: {len(vals) - n_ex} non-fractions (irrational, D>9999, tiny) never shown as a "
          f"fraction or 0", not res["spurious"],
          f"STAFMT BUG ({len(res['spurious'])}): " + " | ".join(res["spurious"][:6]))
    bad_regressions = []
    for entered, expected in FORMAT_REGRESSIONS:
        r = sim.run("STAFMT", init_vars={"W": entered})
        if r.error or r.var("Str9") != expected:
            bad_regressions.append(f"W={entered}: Str9={r.var('Str9')!r}; expected {expected!r}")
    check("STAFMT regression: large answers and tiny nonzero values", not bad_regressions,
          "; ".join(bad_regressions))
    bad = []
    for text, s9, s8 in SPEC_FACTS:
        r = sim.run("STAFMT", init_vars={"W": text})
        g9, g8 = r.var("Str9"), r.var("Str8")
        if g9 != s9 or (g8 not in s8 if isinstance(s8, tuple) else g8 != s8):
            bad.append(f"W={text}: got ({g9},{g8}) want ({s9},{s8})")
    check(f"STAFMT known facts from SPEC/oracles ({len(SPEC_FACTS)})", not bad, "; ".join(bad))
    keep = {"A": 1.25, "P": 2, "X": 3, "Y": 4, "Z": 5, "K": 6, "θ": 7, "Str1": "KEEP", "Str7": "SEVEN"}
    r = sim.run("STAFMT", init_vars=dict(keep, W="⁻355/113", Q=9, V=9))
    reals = r.raw_vars["reals"]
    changed = {k for k in reals if k not in keep and k != "W"}
    untouched = all(float(reals[k]) == float(v) for k, v in keep.items() if not k.startswith("Str"))
    check("STAFMT leaves W and caller vars (A-P,X-Z,K,θ,Str1-7) alone; scratch only Q-V",
          untouched and float(reals["W"]) == float(ti_div(-355, 113)) and changed <= set("QRSTUV") and
          r.var("Str1") == "KEEP" and r.var("Str7") == "SEVEN" and r.var("Str9") == "⁻355/113",
          f"changed={sorted(changed)} Str9={r.var('Str9')}")


# =========================================================================================== 12. navigation
def m(n):
    return {"menu": n}


def last_menu(sim, actions):
    r = sim.run("STA431", actions, max_steps=500_000)
    s = r.screens[-1] if r.screens else {}
    if r.ended_reason != "out_of_actions" or s.get("event") != "menu":
        raise AssertionError(f"expected to stop at a menu after {actions}: {why(r)}")
    return s["menu"]["items"]


PAGE_RE = re.compile(r"^(.*?)\s+(\d)/(\d)\s*$")


def pages_seen(res):
    """[(title, p, n)] for every getkey snapshot; a header without "p/n" is a single-page topic (1/1)."""
    out = []
    for s in res.screens:
        if s["event"] == "getkey":
            mm = PAGE_RE.match(s["rows"][0])
            if mm:
                out.append((mm.group(1).strip(), int(mm.group(2)), int(mm.group(3))))
            else:
                out.append((s["rows"][0].strip(), 1, 1))
    return out


def test_navigation():
    if not os.path.exists(os.path.join(SRC, "STA431.txt")):
        check("STA431 navigation", False, "src/STA431.txt missing")
        return
    sim = Sim(SRC)
    main = last_menu(sim, [])
    check("STA431 main menu items", main == ["ENCYCLOPEDIA", "CALCULATORS", "WHICH TOOL? HINTS",
                                             "HELP + NOTATION", "QUIT"], str(main))
    enc = last_menu(sim, [m(1)])
    check("ENCYCLOPEDIA menu items", enc == ["CH1 COUNTING", "CH2 PROBABILITY", "CH3 RANDOM VARS", "BACK"],
          str(enc))
    r = sim.run("STA431", [m(5)])
    check("QUIT ends STA431 cleanly", ok(r) and r.ended_reason == "end", why(r))
    # HELP pages: RIGHT -> page 2, LEFT -> page 1, CLEAR -> main menu
    r = sim.run("STA431", [m(4), {"key": 26}, {"key": 24}, {"key": 45}, m(5)])
    heads = [s["rows"][0][:10] for s in r.screens if s["event"] == "getkey"]
    check("HELP + NOTATION: page 2 with RIGHT, back with LEFT, CLEAR to main, QUIT",
          ok(r) and heads == ["HOW TO USE", "NOTATION  ", "HOW TO USE"] and r.ended_reason == "end",
          f"{heads} {why(r)}")
    pagers = [("STAE1", [m(1), m(1)], [m(4), m(5)]), ("STAE2", [m(1), m(2)], [m(4), m(5)]),
              ("STAE3", [m(1), m(3)], [m(4), m(5)]), ("STAHNT", [m(3)], [m(5)])]   # (program, entry, exit)
    for prog, entry, exit_ in pagers:
        if prog == "STAHNT" and not os.path.exists(os.path.join(SRC, "STAHNT.txt")):
            continue                            # hints are optional for this harness test
        if not os.path.exists(os.path.join(SRC, prog + ".txt")):
            check(f"{prog} navigation", False, f"src/{prog}.txt missing")
            continue
        try:
            secs = last_menu(sim, entry)
            back_ch = secs.index("BACK") + 1
            acts, n_topics, multi = list(entry), 0, None
            for si in range(1, back_ch):
                tops = last_menu(sim, entry + [m(si)])
                back_s = tops.index("BACK") + 1
                acts.append(m(si))
                for ti in range(1, back_s):
                    acts.append(m(ti))          # open topic; default ENTER pages through to the section menu
                    n_topics += 1
                acts.append(m(back_s))
            acts += [m(back_ch)] + exit_        # chapter BACK (Return) -> back out -> QUIT
        except (AssertionError, ValueError) as ex:
            check(f"{prog}: discover menus", False, str(ex))
            continue
        r = sim.run("STA431", acts, max_steps=2_000_000)
        pg = pages_seen(r)
        firsts = [x for x in pg if x[1] == 1]
        complete = True
        by_topic, cur = [], []
        for x in pg:
            if x[1] == 1 and cur:
                by_topic.append(cur)
                cur = []
            cur.append(x)
        if cur:
            by_topic.append(cur)
        for t in by_topic:
            n = t[0][2]
            if [x[1] for x in t] != list(range(1, n + 1)) or any(x[2] != n for x in t):
                complete = False
            if n >= 3 and multi is None:
                multi = len(by_topic)
        check(f"{prog}: every topic of every section paged 1..n with ENTER, BACK, QUIT "
              f"({n_topics} topics, {len(pg)} pages)",
              ok(r) and r.ended_reason == "end" and len(firsts) == n_topics and complete,
              f"{why(r)} topics_seen={len(firsts)}/{n_topics} complete={complete}")
        with open(os.path.join(SRC, prog + ".txt"), encoding="utf-8") as f:
            code_lines = {i for i, ln in enumerate(f.read().splitlines(), 1)
                          if ln.strip() and not ln.strip().startswith("//")}
        missing = sorted(code_lines - set(r.coverage.get(prog, [])))
        check(f"{prog}: no display warnings (Output wrap/clip) and every line of the program ran",
              not r.warnings and not missing,
              "; ".join(r.warnings[:3]) + (f" unexecuted lines: {missing[:10]}" if missing else ""))
        # keys on one topic: RIGHT/LEFT paging, key 0 polling, CLEAR back to the section menu
        tops = last_menu(sim, entry + [m(1)])
        r0 = sim.run("STA431", entry + [m(1), m(1)], max_steps=500_000)
        n = (pages_seen(r0) or [("", 1, 1)])[0][2]
        # p1 (key 0 = no key, keeps polling) RIGHT p2 [RIGHT p3 LEFT p2] LEFT p1 LEFT -> section menu
        if n == 1:
            keys, want = [{"key": 0}, {"key": 24}], [1, 1]
        else:
            keys = ([{"key": 0}, {"key": 26}] + ([{"key": 26}, {"key": 24}] if n >= 3 else []) +
                    [{"key": 24}, {"key": 24}])
            want = [1, 2] + ([3, 2] if n >= 3 else []) + [1, 1]   # key-0 polls are not snapshotted
        acts = entry + [m(1), m(1)] + keys + [m(1), {"key": 45}, m(tops.index("BACK") + 1), m(back_ch)] + exit_
        r = sim.run("STA431", acts, max_steps=500_000)
        seq = [x[1] for x in pages_seen(r)]
        check(f"{prog}: RIGHT/LEFT paging, getKey polling, LEFT on p1 and CLEAR return to the section menu",
              ok(r) and r.ended_reason == "end" and seq == want, f"pages={seq} want={want} {why(r)}")
    # calculators: into each module and straight BACK (navigation only; skipped if not written yet)
    for prog, item in (("STACNT", "COUNTING"), ("STAPRB", "PROBABILITY"), ("STARV", "RANDOM VARIABLES")):
        if not os.path.exists(os.path.join(SRC, prog + ".txt")):
            continue
        try:
            cm = last_menu(sim, [m(2)])
            mod = last_menu(sim, [m(2), m(cm.index(item) + 1)])
            r = sim.run("STA431", [m(2), m(cm.index(item) + 1), m(mod.index("BACK") + 1),
                                   m(cm.index("BACK") + 1), m(5)])
            check(f"CALCULATORS > {item} ({prog}) > BACK > BACK > QUIT", ok(r) and r.ended_reason == "end",
                  why(r))
        except (AssertionError, ValueError) as ex:
            check(f"CALCULATORS > {item} ({prog}) > BACK", False, str(ex))


# =========================================================================================== 13. tilint
def test_tilint():
    for nm in ("STA431", "STAFMT", "STAE1", "STAE2", "STAE3", "STAHNT"):
        p = os.path.join(SRC, nm + ".txt")
        if os.path.exists(p):
            msgs = tilint.lint_file(p)
            errs = [x for x in msgs if x.startswith("ERROR")]
            check(f"tilint {nm}: 0 errors", not errs, "; ".join(errs[:3]))
    fixtures = [
        ("Lbl A\nLbl A\nReturn", "duplicate label"),
        ("Goto B\nReturn", "does not exist"),
        ("If A\nThen\nGoto A\nEnd\nLbl A\nReturn", "inside an open block"),
        ("For(I,1,2)\nIf I=2\nGoto A\nEnd\nLbl A\nReturn", "inside an open block"),
        ('While 1\nMenu("T","X",A)\nEnd\nLbl A\nReturn', "inside an open block"),
        ("For(I,1,2)\nElse\nEnd\nReturn", "Else outside"),
        ("End\nReturn", "End without"),
        ("While 1\nReturn", "never closed"),
        ('Lbl A\nMenu("T","1",A,"2",A,"3",A,"4",A,"5",A,"6",A,"7",A,"8",A)\nReturn', "options (max 7)"),
        ('Lbl A\nMenu("A TITLE THAT IS TOO LONG","X",A)\nReturn', "title"),
        ('Lbl A\nMenu("T","OPTION TEXT TOO LONG",A)\nReturn', "option"),
        ('Output(11,1,"X")\nReturn', "row 11"),
        ('Output(1,27,"X")\nReturn', "column 27"),
        ('Output(1,20,"12345678")\nReturn', "would wrap"),
        ('Disp "ABCDEFGHIJKLMNOPQRSTUVWXYZ1"\nReturn', "Disp literal"),
        ('Input "ABCDEFGHIJKLMNOPQ",A\nReturn', "Input prompt"),
        ("5→Q\nprgmSTAFMT\nDisp Q\nReturn", "reads Q after prgmSTAFMT"),
        ("For(S,1,3)\nS→W\nprgmSTAFMT\nEnd\nReturn", "loop counter S"),
        ("Goto A\nWhile 1\nLbl A\nEnd\nReturn", "INTO"),
    ]
    missed = []
    for src, needle in fixtures:
        if not any(needle in x for x in tilint.lint_source("TFIX", src)):
            missed.append(needle)
    check(f"tilint flags {len(fixtures)} bad fixtures", not missed, "missed: " + ", ".join(missed))
    clean = ("Lbl M\nMenu(\"T\",\"A\",A,\"B\",B)\nLbl A\nIf K=45:Goto M\nIf K=1\nGoto M\nRepeat Ans:getKey:End\n"
             "For(I,1,2)\nIf I=1\nThen\nDisp I\nElse\nDisp 0\nEnd\nEnd\n.5→W\nprgmSTAFMT\n1→Q\nDisp Q\n"
             "Output(1,1,\"P(A)=\"+Str9)\nLbl B\nReturn")
    msgs = tilint.lint_source("TCLEAN", clean)
    check("tilint: legal patterns (one-line If Goto, Repeat Ans:getKey:End, If-Then-Else) are clean",
          not msgs, "; ".join(msgs))


# =========================================================================================== main
def main():
    tests = [test_order_of_operations, test_control_flow, test_menu, test_input, test_screen, test_tostring,
             test_calculus, test_leaks, test_errors, test_sim_reuse, test_stafmt, test_navigation,
             test_tilint]
    for t in tests:
        if VERBOSE:
            print(f"--- {t.__name__}")
        try:
            t()
        except Exception as ex:  # a crashing test is a failure, keep going
            import traceback
            check(f"{t.__name__} crashed", False, f"{type(ex).__name__}: {ex}")
            if VERBOSE:
                traceback.print_exc()
    print(f"\n{N_PASS} passed, {N_FAIL} failed")
    if FAILS:
        print("FAILED: " + "; ".join(FAILS))
    return 1 if N_FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
