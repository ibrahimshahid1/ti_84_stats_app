#!/usr/bin/env python3
"""
test_STAPRB.py - simulator tests for src/STAPRB.txt (SPEC section 4, STAPRB tools A-F).

Drives the real menus/prompts through tools/tisim.py and asserts on the rendered screen text.
Covers every SPEC section 4 STAPRB case and every STAPRB oracle case in oracles/oracles.json
(spec + edge + HW cases), plus input-validation paths.  For every run it also asserts:
  res.error is None, res.leaks == 0, no display-policy warnings, BACK ends with ended_reason "return",
  and all ʟPR... lists are deleted after BACK.

Run:  $PY tests/test_STAPRB.py      (prints PASS/FAIL per case + total; exit 1 on any failure)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from tisim import Sim  # noqa: E402

SRC = os.path.join(ROOT, "src")
ORACLES = json.load(open(os.path.join(ROOT, "oracles", "oracles.json")))
OR = {c["id"]: c for c in ORACLES if c["program"] == "STAPRB" or c["id"].startswith("HW2")}

BACK = {"menu": 7}
RESULTS = []
_counter = [0]


def norm(s):
    """normalize: '-' -> '⁻', optional leading 0 before a decimal point removed."""
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


RETURN_LINE = [i for i, l in enumerate(open(os.path.join(SRC, "STAPRB.txt"), encoding="utf-8"), 1)
               if l.strip() == "Return"][0]


def returned(res):
    """BACK must end the module via its Return.  tisim reports a top-level Return as "return" (SPEC 6);
    the current tisim build reports it as "end" (TI shows Done), so accept "end" only when the Return
    line of STAPRB actually executed."""
    if res.ended_reason == "return":
        return True
    return res.ended_reason == "end" and RETURN_LINE in res.coverage.get("STAPRB", [])


def run(actions, max_steps=3_000_000):
    _counter[0] += 1
    sim = Sim(SRC)
    return sim.run("STAPRB", actions=actions, max_steps=max_steps)


class Case:
    def __init__(self, name, res):
        self.name, self.res, self.fails = name, res, []

    def check(self, cond, msg):
        if not cond:
            self.fails.append(msg)

    # ---------------------------------------------------------------- screen helpers
    def rows(self, pred=None):
        out = []
        for sc in self.res.screens:
            if sc["event"] not in ("pause", "end", "out_of_actions", "input", "getkey"):
                continue
            rs = [norm_row(r) for r in sc["rows"]]
            if pred is None or pred(rs):
                out.append(rs)
        return out

    def has(self, text, screens=None):
        text = norm(text) if not isinstance(text, tuple) else text[0]
        for rs in (screens if screens is not None else self.rows()):
            for r in rs:
                if text in r:
                    return True
        return False

    def expect_text(self, text, screens=None, where=""):
        self.check(self.has((norm_row(text),), screens), f"missing text {text!r} {where}")

    def expect_absent(self, text, screens=None, where=""):
        self.check(not self.has((norm_row(text),), screens), f"unexpected text {text!r} {where}")

    def expect_value(self, label, exact, dec=None, screens=None, where=""):
        """row containing label+exact; decimal also on that row when it differs and fits."""
        exact = norm(exact)
        want = label + exact
        found = None
        for rs in (screens if screens is not None else self.rows()):
            for r in rs:
                if want in r:
                    rest = r[r.index(want) + len(want):]
                    # the value must end here (no longer number glued on)
                    if rest[:1] in ("", " "):
                        found = r
                        break
            if found:
                break
        if found is None:
            self.fails.append(f"missing {want!r} {where}")
            return
        if dec is not None:
            d = norm(dec)
            if d != exact and len(label) + len(exact) + len(d) < 26:
                self.check(found.rstrip().endswith(" " + d), f"row {found.rstrip()!r} lacks decimal {d!r} {where}")

    def finish_common(self, expect_return=True):
        r = self.res
        self.check(r.error is None, f"error: {r.error}")
        self.check(r.leaks == 0, f"leaks={r.leaks}")
        self.check(not r.warnings, f"display warnings: {r.warnings[:3]}")
        if expect_return:
            self.check(returned(r), f"ended_reason={r.ended_reason} (BACK/Return not reached)")
            left = [k for k in r.vars["lists"] if k.startswith("PR")]
            self.check(not left, f"lists not deleted after BACK: {left}")

    def report(self):
        ok = not self.fails
        RESULTS.append(ok)
        print(("PASS " if ok else "FAIL ") + self.name)
        for f in self.fails:
            print("     - " + f)
        return ok


def inp(v):
    if isinstance(v, (int, float)):
        v = str(v)
    v = str(v)
    if v.startswith("-"):
        v = "⁻" + v[1:]
    return {"input": v}


def pauses_with(case, header):
    return case.rows(lambda rs: header in rs[0])


# ================================================================= Tool A
A_KEYS = ["A", "B", "AnB", "AuB", "A|B", "B|A", "neither"]
A_LABEL = {
    "P(A)": "P(A)=", "P(B)": "P(B)=", "P(AnB)": "P(AnB)=", "P(AuB)": "P(AuB)=", "P(A')": "P(A')=",
    "P(B')": "P(B')=", "P(A'nB')": "NONE A'nB'=", "P(AnB')": "A ONLY AnB'=", "P(A'nB)": "B ONLY A'nB=",
    "P(A|B)": "P(A|B)=", "P(B|A)": "P(B|A)=", "P(A|B')": "P(A|B')=", "P(B|A')": "P(B|A')=",
    "P(A'|B)": "P(A'|B)=", "P(B'|A)": "P(B'|A)=", "P(exactly one)": "EXACTLY ONE=", "P(A)P(B)": "P(A)P(B)=",
}
REL = {"NO EXTRA INFO": 1, "INDEPENDENT": 2, "MUTUALLY EXCL.": 3}


def tool_a_actions(inputs):
    acts = [{"menu": 1}]
    for k in A_KEYS:
        acts.append(inp(inputs.get(k, -1)))
    acts.append({"menu": REL[inputs.get("relation", "NO EXTRA INFO")]})
    acts.append(BACK)
    return acts


def test_tool_a_oracle(cid):
    c = OR[cid]
    case = Case(f"{cid} {c['inputs_description']}", run(tool_a_actions(c["inputs"])))
    exp = c["expected"]
    if exp.get("result") == "NOT ENOUGH INFO":
        case.expect_text("NOT ENOUGH INFO")
        case.expect_value("P(A)=", "1/2")
        case.expect_absent("RESULTS 1/3")
    else:
        for key, val in exp.items():
            if key in A_LABEL:
                dec = c["display"].get(key, [None, None])[1]
                case.expect_value(A_LABEL[key], val if val != "undef" else "undef", dec, where=f"({key})")
        ind = exp.get("independent?")
        if ind == "YES":
            case.expect_text("=> INDEPENDENT")
        elif ind == "NO":
            case.expect_text("=> NOT INDEPENDENT")
        me = exp.get("mutually exclusive?")
        if me == "YES":
            case.expect_text("MUTUALLY EXCLUSIVE (AnB=0)")
        elif me == "NO":
            case.expect_text("NOT MUTUALLY EXCL")
        w = exp.get("warnings")
        if w == "none":
            case.expect_text("NO WARNINGS")
        elif w:
            case.expect_text("WARN P(AnB)>MIN(P(A),P(B))")
            case.expect_text("WARN A VALUE NOT IN [0,1]")
    case.finish_common()
    return case.report()


def test_tool_a_hw():
    # HW2 Q2: P(X)=.55 P(Y)=.35 P(XuY)=.70 -> (a) 1/5 (b) 4/7 (c) P(Y|X')=1/3
    c = OR["HW2-Q2"]
    case = Case("HW2-Q2 two events (X=A, Y=B)", run(tool_a_actions({"A": ".55", "B": ".35", "AuB": ".70"})))
    case.expect_value("P(AnB)=", c["expected"]["(a) P(XnY)"], ".2")
    case.expect_value("P(A|B)=", c["expected"]["(b) P(X|Y)"], ".571429")
    case.expect_value("P(B|A')=", c["expected"]["(c) P(Y|X^c)"], ".333333")
    case.finish_common()
    return case.report()


def test_tool_a_screens():
    """layout: 3 result screens, each with its header, formula rows present."""
    case = Case("A layout / headers / formula rows", run(tool_a_actions(OR["PRB-A-S1"]["inputs"])))
    for h in ("RESULTS 1/3", "RESULTS 2/3", "RESULTS 3/3"):
        case.check(len(pauses_with(case, h)) == 1, f"screen {h} count != 1")
    case.expect_text("P(X|Y)=P(XnY)/P(Y)")
    case.expect_text("=P(A)+P(B)-2P(AnB)")
    case.expect_value("P(A)P(B)=", "77/400", ".1925")
    case.expect_text("USE WHEN")
    case.expect_text("(-)1=UNKNOWN")
    case.finish_common()
    return case.report()


# ================================================================= Tool B
B_KEYS = ["R1C1", "R1C2", "R1", "R2C1", "R2C2", "R2", "C1", "C2", "N"]


def tool_b_actions(inputs):
    acts = [{"menu": 2}]
    for k in B_KEYS:
        acts.append(inp(inputs.get(k, -1)))
    acts.append(BACK)
    return acts


def table_cells(case):
    scr = pauses_with(case, "2x2 TABLE (FILLED)")
    if not scr:
        return None
    rs = scr[0]
    cells = []
    for r in (rs[2], rs[3], rs[4]):
        cells += [r[4:10].strip(), r[11:17].strip(), r[18:26].strip()]
    return cells


def test_tool_b_oracle(cid):
    c = OR[cid]
    case = Case(f"{cid} {c['inputs_description']}", run(tool_b_actions(c["inputs"])))
    exp = c["expected"]
    cells = table_cells(case)
    case.check(cells is not None, "table screen missing")
    res = exp.get("result", "")
    if cells:
        for i, k in enumerate(B_KEYS):
            if k in exp:
                v = exp[k]
                if v == "unknown":
                    case.check(cells[i] == "?", f"cell {k}: {cells[i]!r} != '?'")
                else:
                    ex, dec = c["display"][k]
                    want = norm(ex) if len(norm(ex)) <= 6 else norm(dec)[:6]
                    case.check(cells[i] == want, f"cell {k}: {cells[i]!r} != {want!r}")
    if "NOT ENOUGH" in res:
        case.expect_text("NOT ENOUGH INFO")
        case.expect_text("? = UNKNOWN")
        case.expect_absent("JOINT + MARGINAL")
    if "INCONSISTENT" in res:
        case.expect_text("WARN TOTALS INCONSISTENT")
    if not res:
        for key, val in exp.items():
            if key.startswith("P("):
                case.expect_value(key + "=", val, c["display"][key][1], where=f"({key})")
        case.expect_text("=> INDEPENDENT" if exp["independent?"] == "YES" else "=> NOT INDEPENDENT")
        if exp.get("totals consistent?") == "YES":
            case.expect_absent("INCONSISTENT")
    case.finish_common()
    return case.report()


def test_tool_b_hw():
    c = OR["HW2-Q3"]
    case = Case("HW2-Q3 2x2 table (R1=grad R2=faculty C1=female C2=male)",
                run(tool_b_actions(OR["PRB-B-S1"]["inputs"])))
    case.expect_value("P(R2nC2)=", c["expected"]["(a) P(male faculty)"], ".208333")
    case.expect_value("P(R1|C1)=", c["expected"]["(b) P(grad|female)"], ".615385")
    case.finish_common()
    return case.report()


def test_tool_b_zero_total():
    case = Case("B validation: complete table with grand total 0",
                run([{"menu": 2}] + [inp(0)] * 9 + [BACK]))
    case.expect_text("GRAND TOTAL MUST BE >0")
    case.finish_common()
    return case.report()


# ================================================================= Tool C
def tool_c_actions(priors, liks):
    acts = [{"menu": 3}, inp(len(priors))]
    for p, l in zip(priors, liks):
        acts += [inp(p), inp(l)]
    acts.append(BACK)
    return acts


def c_label(key):
    if key == "P(A)":
        return "TOTAL P(A)="
    if key == "P(A')":
        return "P(A')=1-P(A)="
    return key + "="


def test_tool_c_oracle(cid):
    c = OR[cid]
    inputs = c["inputs"]
    case = Case(f"{cid} {c['inputs_description']}", run(tool_c_actions(inputs["priors"], inputs["liks"])))
    exp = c["expected"]
    for key, val in exp.items():
        if key.startswith("P("):
            dec = c["display"].get(key, [None, None])[1]
            case.expect_value(c_label(key), val, dec, where=f"({key})")
    if exp.get("rescaled?") == "YES":
        case.expect_text("RESCALED TO SUM 1")
    else:
        case.expect_absent("RESCALED")
    case.finish_common()
    return case.report()


def test_tool_c_hw():
    ok = True
    for hid, src, pairs in [
        ("HW2-Q4", "PRB-C-S1", [("(a) P(accept)", "TOTAL P(A)="), ("(b) P(Methodology|accept)", "P(B1|A)=")]),
        ("HW2-Q5", "PRB-C-S2", [("(a) P(red)", "TOTAL P(A)="), ("(b) P(die 1or2|red)", "P(B1|A)=")]),
        ("HW2-431-Q6", "PRB-C-S3", [("(a) P(urgent)", "TOTAL P(A)="), ("(b) P(spam|urgent)", "P(B1|A)=")]),
    ]:
        c = OR[hid]
        i = OR[src]["inputs"]
        case = Case(f"{hid} total prob/Bayes", run(tool_c_actions(i["priors"], i["liks"])))
        for key, label in pairs:
            case.expect_value(label, c["expected"][key], c["display"][key][1])
        case.finish_common()
        ok &= case.report()
    return ok


def test_tool_c_percent_note_and_k9():
    pri = ["1"] * 9
    lik = ["10", "20", "30", "40", "50", "60", "70", "80", "90"]
    case = Case("C k=9 counts+percent: notes, pagination, P(A)=1/2", run(tool_c_actions(pri, lik)))
    case.expect_text("PRIORS ADDED TO 9")
    case.expect_text("LIKELIHOOD >1 READ AS %")
    case.expect_value("TOTAL P(A)=", "1/2", ".5")
    case.expect_value("P(B9|A)=", "1/5", ".2")
    case.expect_value("P(B9|A')=", "1/45", ".022222")
    case.finish_common()
    return case.report()


def test_tool_c_validation():
    acts = [{"menu": 3}, inp(1), inp(2), inp(".5"), inp(".1"), inp(".5"), inp("150"), inp(2),
            inp(".5"), inp(".1"), inp(".5"), inp(".2"), BACK]
    case = Case("C validation: k=1 rejected, likelihood 150 rejected", run(acts))
    case.expect_text("k MUST BE 2 TO 9")
    case.expect_text("LIKELIHOODS 0 TO 1")
    case.expect_value("TOTAL P(A)=", "3/20", ".15")
    case.finish_common()
    return case.report()


# ================================================================= Tool D
def d_actions(p, sens, spec, result, nxt=()):
    acts = [{"menu": 4}, inp(p), inp(sens), inp(spec), {"menu": 1 if result == "+" else 2}]
    for t in nxt:
        acts += [{"menu": 1}, inp(t["sens"]), inp(t["spec"]), {"menu": 1 if t["result"] == "+" else 2}]
    acts += [{"menu": 2}, BACK]
    return acts


D_LABEL = {"P(+)": "P(+)=", "P(-)": "P(-)=", "PPV=P(D|+)": "PPV P(D|+)=", "NPV=P(D'|-)": "NPV P(D'| -)=",
           "P(D|-)": "P(D| -)="}


def test_tool_d_oracle(cid):
    c = OR[cid]
    i = c["inputs"]
    case = Case(f"{cid} {c['inputs_description']}",
                run(d_actions(i["p"], i["sens"], i["spec"], i["result"], i.get("next", []))))
    disp, exp = c["display"], c["expected"]
    s1 = case.rows(lambda rs: "PRIOR P(D)=" in rs[0])
    first, second = s1[:1], s1[1:2]
    case.check(len(s1) == 1 + len(i.get("next", [])), f"result screens={len(s1)}")
    for key, lab in D_LABEL.items():
        if key in exp:
            if exp[key] == "undef":
                case.expect_value(lab, "undef", screens=first, where=f"({key})")
            else:
                case.expect_value(lab, disp[key][0], disp[key][1], screens=first, where=f"({key})")
    post = exp.get("posterior (chosen result)")
    plab = "POSTERIOR P(D|+)=" if i["result"] == "+" else "POSTERIOR P(D| -)="
    if post == "undef":
        case.expect_value(plab, "undef", screens=first)
    elif post:
        case.expect_value(plab, disp["posterior (chosen result)"][0], screens=first)
        d = norm(disp["posterior (chosen result)"][1])
        if d != norm(disp["posterior (chosen result)"][0]):
            case.expect_text("   =" + d, screens=first)
    if "test2 P(+)" in exp:
        case.expect_value("P(+)=", exp["test2 P(+)"], disp["test2 P(+)"][1], screens=second)
        case.expect_value("P(-)=", exp["test2 P(-)"], disp["test2 P(-)"][1], screens=second)
        u = disp["UPDATED P(D) after test2"]
        case.expect_value("UPDATED P(D)=", u[0], screens=second)
        case.expect_text("   =" + norm(u[1]), screens=second)
    if cid == "PRB-D-E1":
        case.expect_text("(% INPUTS DIVIDED BY 100)")
    case.finish_common()
    return case.report()


def test_tool_d_hw():
    c = OR["HW2-631-Q7"]
    case = Case("HW2-631-Q7 sens/spec two tests (percent inputs)",
                run(d_actions(".005", "95", "99", "+", [{"sens": "90", "spec": "95", "result": "+"}])))
    s1 = case.rows(lambda rs: "PRIOR P(D)=" in rs[0])
    case.expect_value("POSTERIOR P(D|+)=", c["expected"]["(a) P(event|flag)"], screens=s1[:1])
    case.expect_value("UPDATED P(D)=", c["expected"]["(b) P(event|flag, physician +)"], screens=s1[1:2])
    case.expect_text("   =.895757")
    case.finish_common()
    return case.report()


def test_tool_d_undef_next():
    acts = [{"menu": 4}, inp(".2"), inp("0"), inp("1"), {"menu": 1}, {"menu": 1}, BACK]
    case = Case("D posterior undef -> ANOTHER TEST refused cleanly", run(acts))
    case.expect_text("POSTERIOR IS UNDEFINED")
    case.finish_common()
    return case.report()


def test_tool_d_validation():
    acts = [{"menu": 4}, inp("150"), inp(".01"), inp("150"), inp(".9"), inp(".9"), inp(".8"), {"menu": 1},
            {"menu": 2}, BACK]
    case = Case("D validation: p=150 and sens=150 rejected, then sens .9 spec .8", run(acts))
    case.expect_text("p MUST BE 0 TO 1")
    case.expect_text("SENS, SPEC MUST BE")
    case.expect_value("P(+)=", "207/1000", ".207")
    case.finish_common()
    return case.report()


# ================================================================= Tool E
E_LABEL3 = {"A only": "A ONLY=", "B only": "B ONLY=", "C only": "C ONLY=", "AnB only": "AnB ONLY=",
            "AnC only": "AnC ONLY=", "BnC only": "BnC ONLY=", "all 3": "ALL 3=", "union": "UNION (≥1)=",
            "none": "NONE=", "exactly 1": "EXACTLY 1=", "exactly 2": "EXACTLY 2=", "at least 2": "AT LEAST 2="}
E_LABEL2 = {"A only": "A ONLY=", "B only": "B ONLY=", "union": "UNION AuB=", "neither": "NEITHER=",
            "exactly one": "EXACTLY ONE="}


def e_actions(mode, values):
    acts = [{"menu": 5}, {"menu": 1 if mode == 2 else 2}] + [inp(v) for v in values] + [BACK]
    return acts


def test_tool_e_oracle(cid):
    c = OR[cid]
    i = c["inputs"]
    case = Case(f"{cid} {c['inputs_description']}", run(e_actions(i["mode"], i["values"])))
    labels = E_LABEL3 if i["mode"] == 3 else E_LABEL2
    for key, val in c["expected"].items():
        if key not in labels:
            continue
        if val.startswith("n/a"):
            case.expect_text(labels[key] + "? (N UNKNOWN)")
        else:
            case.expect_value(labels[key], val, c["display"][key][1], where=f"({key})")
    w = c["expected"].get("negative region warning?")
    if w == "YES":
        case.expect_text("WARN A REGION IS <0")
    elif w == "NO":
        case.expect_absent("WARN")
        case.expect_text("ALL REGIONS ≥0  OK")
    if i["mode"] == 3 and c["expected"].get("none", "").isdigit():
        case.expect_value("NONE=N-UNION=", c["expected"]["none"])
    case.finish_common()
    return case.report()


def test_tool_e_hw():
    c = OR["HW2-431-Q7"]
    case = Case("HW2-431-Q7 Venn 3 sets (D,P,W)", run(e_actions(3, [400, 500, 600, 200, 150, 250, 100, 1000])))
    case.expect_value("C ONLY=", c["expected"]["Weekend only"])
    case.expect_value("NONE=", c["expected"]["none"])
    case.finish_common()
    return case.report()


def test_tool_e_validation():
    acts = [{"menu": 5}, {"menu": 1}, inp(-1), inp(2), inp(1), inp(5), {"menu": 3}, BACK]
    case = Case("E validation: negative n(A) rejected, BACK from VENN menu", run(acts))
    case.expect_text("ONLY N MAY BE UNKNOWN")
    case.finish_common()
    return case.report()


def test_tool_e_2set_n_unknown():
    case = Case("E 2 sets N unknown -> NEITHER=?", run(e_actions(2, [30, 20, 10, -1])))
    case.expect_text("NEITHER=? (N UNKNOWN)")
    case.expect_value("UNION AuB=", "40")
    case.expect_value("EXACTLY ONE=", "30")
    case.finish_common()
    return case.report()


# ================================================================= Tool F
def f_actions(N, K, n, k):
    return [{"menu": 6}, inp(N), inp(K), inp(n), inp(k), BACK]


def test_tool_f_oracle(cid):
    c = OR[cid]
    i = c["inputs"]
    k = i["k"]
    case = Case(f"{cid} {c['inputs_description']}", run(f_actions(i["N"], i["K"], i["n"], i["k"])))
    wo = pauses_with(case, "WITHOUT REPLACEMENT")
    wi = pauses_with(case, "WITH REPLACEMENT")
    so = pauses_with(case, "ONE SPECIFIC ORDER")
    case.check(len(wo) == 1 and len(wi) == 1 and len(so) == 1, "expected 3 screens (w/o, with, order)")
    disp, exp = c["display"], c["expected"]
    lab = {"P(X=k)": f"P(X={k})=", "P(X>=k)": f"P(X≥{k})=", "P(X<=k)": f"P(X≤{k})="}
    for pre, scr in (("w/o ", wo), ("with ", wi)):
        for q, l in lab.items():
            key = pre + q
            if key in disp:
                case.expect_value(l, disp[key][0], disp[key][1], screens=scr, where=f"({key})")
    if "specific order w/o" in disp:
        case.expect_value("W/O REPL=", disp["specific order w/o"][0], disp["specific order w/o"][1], screens=so)
    if "specific order with" in disp:
        case.expect_value("WITH REPL=", disp["specific order with"][0], disp["specific order with"][1], screens=so)
    if "specific order" in exp:
        case.expect_text("k>n  NO SUCH ORDER", screens=so)
    if "w/o" in exp:
        case.expect_text("n>N  CANNOT DRAW n ITEMS", screens=wo)
        case.expect_text("W/O REPL=n/a (n>N)", screens=so)
    if cid == "PRB-F-S1":
        case.expect_text("=C(3,1)C(4,1)/C(7,2)", screens=wo)
        case.expect_text("BINOMIAL p=K/N=3/7", screens=wi)
    case.finish_common()
    return case.report()


def test_tool_f_validation():
    acts = [{"menu": 6}, inp(0), inp(1), inp(1), inp(1), inp(10), inp(2.5), inp(2), inp(1),
            inp(10), inp(11), inp(2), inp(1), inp(10), inp(4), inp(3), inp(0), BACK]
    case = Case("F validation: N=0, K=2.5, K>N rejected, then N=10 K=4 n=3 k=0", run(acts))
    case.check(sum("WHOLE NUMBERS ONLY" in "".join(rs) for rs in case.rows()) == 3, "expected 3 rejections")
    case.expect_value("P(X=0)=", "1/6", ".166667")
    case.finish_common()
    return case.report()


def test_tool_f_big():
    case = Case("F N=300 K=150 n=300 k=150 (loop size / no overflow)", run(f_actions(300, 150, 300, 150)))
    case.expect_value("P(X=150)=", "1")
    case.check(case.res.steps < 200000, f"steps={case.res.steps}")
    case.finish_common()
    return case.report()


# ================================================================= module-level
def test_menu_back():
    res = run([BACK])
    case = Case("module menu text/order + BACK returns and deletes lists", res)
    m = [s for s in res.screens if s["event"] == "menu"][0]["menu"]
    case.check(m["title"] == "PROBABILITY TOOLS", f"title {m['title']!r}")
    case.check(m["items"] == ["TWO EVENTS A,B", "2x2 TABLE", "TOTAL PROB/BAYES", "SENS/SPEC TEST",
                              "VENN 2-3 SETS", "URN DRAWS", "BACK"], f"items {m['items']}")
    case.finish_common()
    return case.report()


def test_from_launcher():
    sim = Sim(SRC)
    res = sim.run("STA431", actions=[{"menu": 2}, {"menu": 3}, {"menu": 1}] + tool_a_actions(
        OR["PRB-A-S2"]["inputs"])[1:] + [{"menu": 5}, {"menu": 5}])
    case = Case("launched from STA431 > CALCULATORS > PROBABILITY, back to launcher", res)
    case.expect_value("P(AuB)=", "29/50", ".58")
    case.check(res.error is None, f"error {res.error}")
    case.check(res.leaks == 0, f"leaks {res.leaks}")
    case.check(res.ended_reason in ("end", "return"), f"ended {res.ended_reason}")
    left = [k for k in res.vars["lists"] if k.startswith("PR")]
    case.check(not left, f"lists left {left}")
    return case.report()


def test_fuzz_no_errors():
    """deterministic random inputs (incl. invalid / 0 / 1 / percent-like values): no TI error, no leaks,
    no display-policy warnings, BACK always reached."""
    import random
    rnd = random.Random(431)
    vals = ["⁻1", "0", "1", ".5", ".25", ".75", "2", "1.5", ".3", ".999", "50"]
    runs = []
    for _ in range(40):
        ins = {k: rnd.choice(vals) for k in A_KEYS}
        ins["relation"] = rnd.choice(list(REL))
        runs.append(("A", tool_a_actions(ins)))
    for _ in range(20):
        ins = {k: rnd.choice(["⁻1", "0", "10", "20", "30", ".2", ".5", "1"]) for k in B_KEYS}
        runs.append(("B", tool_b_actions(ins)))
    for _ in range(15):
        k = rnd.randint(2, 4)
        pr = ["1"] + [rnd.choice(["0", "1", ".5", "2", "30"]) for _ in range(k - 1)]
        lk = [rnd.choice(["0", "1", ".5", "20", "100"]) for _ in range(k)]
        runs.append(("C", tool_c_actions(pr, lk)))
    for _ in range(15):
        m = rnd.choice([2, 3])
        v = [rnd.choice(["0", "1", "5", ".2", "100"]) for _ in range(7 if m == 3 else 3)]
        runs.append(("E", e_actions(m, v + [rnd.choice(["⁻1", "0", "1", "100"])])))
    for N, K, n, k in [(300, 1, 300, 300), (300, 299, 300, 0), (1, 0, 0, 0), (1, 1, 1, 1), (5, 5, 3, 2),
                       (20, 7, 25, 30)]:
        runs.append(("F", f_actions(N, K, n, k)))
    fails = []
    for tool, acts in runs:
        r = run(acts)
        if r.error or r.leaks or r.warnings or not returned(r):
            fails.append(f"{tool} {acts}: {r.error} leaks={r.leaks} {r.warnings[:1]} {r.ended_reason}")
    case = Case(f"fuzz {len(runs)} random runs of tools A,B,C,E,F: no errors/leaks/warnings", run([BACK]))
    for f in fails[:5]:
        case.fails.append(f)
    case.finish_common()
    return case.report()


def main():
    test_menu_back()
    for cid in ["PRB-A-S1", "PRB-A-S2", "PRB-A-S3", "PRB-A-E1", "PRB-A-E2", "PRB-A-E3", "PRB-A-E4",
                "PRB-A-E5", "PRB-A-E6", "PRB-A-E7"]:
        test_tool_a_oracle(cid)
    test_tool_a_hw()
    test_tool_a_screens()
    for cid in ["PRB-B-S1", "PRB-B-E1", "PRB-B-E2", "PRB-B-E3"]:
        test_tool_b_oracle(cid)
    test_tool_b_hw()
    test_tool_b_zero_total()
    for cid in ["PRB-C-S1", "PRB-C-S2", "PRB-C-S3", "PRB-C-E1", "PRB-C-E2", "PRB-C-E3", "PRB-C-E4"]:
        test_tool_c_oracle(cid)
    test_tool_c_hw()
    test_tool_c_percent_note_and_k9()
    test_tool_c_validation()
    for cid in ["PRB-D-S1", "PRB-D-E1", "PRB-D-E2", "PRB-D-E3", "PRB-D-E4"]:
        test_tool_d_oracle(cid)
    test_tool_d_hw()
    test_tool_d_undef_next()
    test_tool_d_validation()
    for cid in ["PRB-E-S1", "PRB-E-S2", "PRB-E-E1", "PRB-E-E2", "PRB-E-E3"]:
        test_tool_e_oracle(cid)
    test_tool_e_hw()
    test_tool_e_validation()
    test_tool_e_2set_n_unknown()
    for cid in ["PRB-F-S1", "PRB-F-S2", "PRB-F-E1", "PRB-F-E2", "PRB-F-E3"]:
        test_tool_f_oracle(cid)
    test_tool_f_validation()
    test_tool_f_big()
    test_from_launcher()
    test_fuzz_no_errors()
    n, p = len(RESULTS), sum(RESULTS)
    print(f"\nTOTAL {p}/{n} passed")
    sys.exit(0 if p == n else 1)


if __name__ == "__main__":
    main()
