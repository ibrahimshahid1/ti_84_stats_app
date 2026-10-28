#!/usr/bin/env python3
"""Token-stream homework and edge-case regressions for M2DISC and M2CONT.

These are off-device numerical/program-flow checks, not a physical CE test.
Run using a Python environment with tivars and mpmath.
"""
from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tisim import Sim


def menu(n):
    return {"menu": n}


def entered(value):
    return {"input": str(value)}


INITIAL = {"Y1": "X²+1", "Y9": "X+3", "L₁": [91, 92], "L₂": [71, 72]}


def disc_rows(rows, joint=True):
    actions = [menu(2 if joint else 1), entered(len(rows))]
    for row in rows:
        actions.extend(entered(v) for v in row)
    return actions


def one_d(q, lo, hi, parameter=0):
    return [menu(1), entered(q), entered(parameter), entered(lo), entered(hi)]


def grid(xvalues, yvalues, q):
    return [menu(3), entered(xvalues), entered(yvalues), entered(q)]


def two_d(q, xlo, xhi, ylo, yhi, g="1", n=4, parameter=0):
    return [menu(2), entered(q), entered(parameter), entered(xlo), entered(xhi),
            entered(ylo), entered(yhi), entered(g), entered(n)]


CASES = []


def check(name, program, actions, expected=None, text=(), tolerance=1e-7):
    result = Sim(str(ROOT / "src")).run(
        program, actions=actions, init_vars=INITIAL, max_steps=7_000_000,
    )
    errors = []
    if result.error:
        errors.append(str(result.error))
    if result.ended_reason != "end":
        errors.append("ended=" + result.ended_reason)
    if result.leaks:
        errors.append(f"control leaks={result.leaks}")
    if result.warnings:
        errors.append("display warnings=" + str(result.warnings))
    for needle in text:
        if needle not in result.text:
            errors.append("missing " + repr(needle))
    for key, target in (expected or {}).items():
        actual = result.var(key)
        if not isinstance(actual, (float, int)) or not math.isclose(actual, target, rel_tol=tolerance, abs_tol=tolerance):
            errors.append(f"{key}={actual}, expected {target}")
    for key, value in INITIAL.items():
        if result.var(key) != value:
            errors.append(f"user {key} changed to {result.var(key)!r}")
    if program == "M2DISC" and any(key.startswith("M2") for key in result.vars["lists"]):
        errors.append("owned temporary lists not cleaned on exit")
    CASES.append(not errors)
    print(("PASS " if not errors else "FAIL ") + name)
    if errors:
        print("  " + " | ".join(errors))
        if result.error:
            print(result.text[-1800:])
    return result


def main():
    h51 = [(1, 2), (2, 6), (3, 12), (4, 20)]
    check("HW5 Q1 normalization and moments", "M2DISC",
          disc_rows(h51, False) + [menu(1), menu(7)],
          {"A": 40, "E": 13/4, "G": 227/20, "B": 63/80},
          ["1/40", "13/4", "227/20", "63/80"])
    check("HW4 Q1 formula/grid input", "M2DISC",
          grid("{1,2}", "{1,2,3}", "X+Y²") +
          [menu(2), menu(3), entered(2), menu(7), menu(7)],
          {"E": 17/11, "B": 30/121}, ["1/37", "5/11", "6/11"])
    check("HW5 Q1 univariate formula/grid input", "M2DISC",
          grid("{1,2,3,4}", "{0}", "X²+X") + [menu(1), menu(7)],
          {"A": 40, "E": 13/4, "G": 227/20, "B": 63/80}, ["1/40", "63/80"])
    check("HW5 Q8 formula/grid input", "M2DISC",
          grid("{1,2,3}", "{1,2,3}", "X+Y") + [menu(1), menu(7)],
          {"E": 13/6, "F": 13/6, "J": 14/3, "C": -1/36})
    check("grid duplicate-coordinate rejection", "M2DISC",
          grid("{1,1}", "{1,2}", "1") + [menu(4)],
          text=["REPEATED (x,y) PAIR"])
    check("grid pair-count guard", "M2DISC",
          grid("{1,2,3,4,5,6}", "{1,2,3,4,5,6}", "1") + [menu(4)],
          text=["GRID MUST HAVE 1-30 PAIRS"])
    check("grid negative-weight rejection", "M2DISC",
          grid("{1,2}", "{1}", "⁻X") + [menu(4)],
          text=["WEIGHTS MUST BE ≥0"])
    check("grid zero-total rejection", "M2DISC",
          grid("{1,2}", "{1}", "0") + [menu(4)],
          text=["WITH POSITIVE TOTAL"])
    h41 = [(x, y, x+y*y) for x in (1, 2) for y in (1, 2, 3)]
    check("HW4 Q1 marginal and conditional PMF", "M2DISC",
          disc_rows(h41) + [menu(2), menu(1), entered(1), menu(2), entered(2),
                           menu(3), entered(2), menu(7), menu(7)],
          {"E": 17/11, "G": 29/11, "B": 30/121},
          ["1/37", "17/37", "11/37", "5/11", "6/11"])
    h58 = [(x, y, x+y) for x in (1, 2, 3) for y in (1, 2, 3)]
    check("HW5 Q8 joint and conditional moments", "M2DISC",
          disc_rows(h58) + [menu(1), menu(2), menu(4), entered(1), menu(7), menu(7)],
          {"E": 20/9, "G": 50/9, "B": 50/81, "C": -1/36},
          ["13/6", "14/3", "20/9"])
    h44 = [(x, y, x+y) for x in (1, 2) for y in (1, 2, 3, 4)]
    check("HW4 Q4 event masks", "M2DISC",
          disc_rows(h44) + [menu(3), menu(1), entered("X>Y"), menu(1),
                           entered("X+Y≤3"), menu(3), menu(7)],
          {"W": 1/4}, ["3/32", "1/4"])
    check("joint conditional event mask", "M2DISC",
          disc_rows(h58) + [menu(3), menu(2), entered("Y=3"), entered("X=1"), menu(3), menu(7)],
          {"W": 4/9}, ["4/9"])
    check("discrete function square", "M2DISC",
          disc_rows(h51, False) + [menu(4), entered("X²"), menu(7)],
          {"E": 227/20, "G": 619/4, "B": 10371/400})
    check("raw and central product moments", "M2DISC",
          disc_rows(h58) + [menu(5), menu(1), entered(1), entered(1),
                           menu(2), entered(1), entered(1), menu(3), menu(7)],
          {"W": -1/36}, ["14/3"])
    check("zeroth product moment handles zero data", "M2DISC",
          disc_rows([(0, 0, 1), (1, 1, 1)]) +
          [menu(5), menu(1), entered(0), entered(0), menu(3), menu(7)], {"W": 1})
    check("zero-probability conditioning guards", "M2DISC",
          disc_rows([(1, 1, 1), (2, 2, 1)]) +
          [menu(2), menu(3), entered(5), menu(7), menu(3), menu(2),
           entered("X>0"), entered("Y=5"), menu(3), menu(7)],
          text=["CONDITIONAL UNDEFINED", "GIVEN EVENT HAS p=0"])
    check("full Cartesian independence check", "M2DISC",
          disc_rows([(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]) +
          [menu(2), menu(5), menu(7), menu(7)], {"A": 0}, ["NUMERIC MATCH TO 1E-9"])
    check("missing-pair dependence check", "M2DISC",
          disc_rows([(0, 0, 1), (1, 1, 1)]) +
          [menu(2), menu(5), menu(7), menu(7)], {"A": .25}, ["NUMERIC FACTORIZATION FAIL"])
    check("HW5 Q7 continuous conditional slice", "M2CONT",
          one_d("X+A", 0, 1, .5) + [menu(1), menu(7)],
          {"D": 1, "E": 7/12, "F": 5/12, "G": 11/144},
          ["7/12", "11/144"])
    check("HW5 Q2 symmetric density and square", "M2CONT",
          one_d("3/4*(1-X²)", "⁻1", 1) +
          [menu(1), menu(3), entered("X²"), menu(7)],
          {"D": 1, "E": 1/5, "F": 3/35, "G": 8/175}, ["8/175"])
    check("continuous interval clipped to support", "M2CONT",
          one_d("2X", 0, 1) + [menu(2), entered("⁻2"), entered("1/2"), menu(7)],
          {"W": .25})
    check("continuous empty interval", "M2CONT",
          one_d("2X", 0, 1) + [menu(2), entered(2), entered(3), menu(7)], {"W": 0})
    check("continuous raw and central moments", "M2CONT",
          one_d("3X²", 0, 1) + [menu(4), menu(1), entered(4), menu(2), entered(2),
                                  menu(3), menu(7)],
          {"W": 3/80}, ["3/7", "3/80"])
    check("HW4 Q5 double integral with variable bound", "M2CONT",
          two_d("(2X+Y)/4", 0, 1, "X", 2) + [menu(4)],
          {"D": 19/24, "F": 19/24}, ["19/24", "REFINED N=8"])
    check("HW4 Q3 reliability complement rectangle", "M2CONT",
          two_d("(X+Y)/8", 1, 2, 1, 2) + [menu(4)],
          {"F": 3/8}, ["3/8"])
    check("HW4 Q2 unknown normalization and product moment", "M2CONT",
          two_d("2X+Y", 0, 1, 0, 2, "X*Y") + [menu(1), menu(4)],
          {"F": 4, "G": 8/3, "W": 2/3}, ["1/4", "2/3"])
    check("triangular support skips zero-length endpoint slice", "M2CONT",
          two_d("24X*(1-X-Y)", 0, 1, 0, "1-X") + [menu(4)], {"F": 1})
    check("double-integration refinement comparison", "M2CONT",
          two_d("𝑒^(X+Y)", 0, 1, 0, 1, n=4) + [menu(4)],
          {"F": (math.e-1)**2}, tolerance=2e-6)
    check("reversed moving limits guard", "M2CONT",
          two_d("1", 0, 1, "X", "X-1") + [menu(4)], text=["Y LIMITS REVERSED"])
    check("negative density guard", "M2CONT",
          one_d("⁻X", 0, 1) + [menu(4)], text=["INVALID q OR ZERO MASS"])
    check("zero density guard", "M2CONT",
          one_d("0", 0, 1) + [menu(4)], text=["INVALID q OR ZERO MASS"])
    print(f"\n{sum(CASES)}/{len(CASES)} M2DISC/M2CONT cases passed")
    return 0 if all(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
