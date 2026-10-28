#!/usr/bin/env python3
"""Homework-style simulator checks for STARV's joint-distribution tool.

Run with a Python environment containing tivars:
    python tests/test_joint.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from tisim import Sim  # noqa: E402


def menu(number):
    return {"menu": number}


def entered(value):
    return {"input": str(value)}


BACK = menu(7)
INITIAL_GRAPHS = {"Y9": "X²", "Y0": "X+1"}


def run_case(name, actions, required, last_value=None, tolerance=1e-5):
    result = Sim(os.path.join(ROOT, "src")).run(
        "STARV", actions=actions, max_steps=6_000_000, init_vars=INITIAL_GRAPHS,
    )
    problems = []
    if result.error is not None:
        problems.append(str(result.error))
    if result.ended_reason != "end":
        problems.append("did not return through BACK: " + str(result.ended_reason))
    if result.leaks:
        problems.append(f"{result.leaks} leaked control frames")
    if result.warnings:
        problems.append("display warnings: " + str(result.warnings[:3]))
    if [key for key in result.vars["lists"] if key.startswith("RV")]:
        problems.append("joint temporary lists remained after BACK")
    for graph, before in INITIAL_GRAPHS.items():
        if result.var(graph) != before:
            problems.append(f"{graph} changed from {before!r} to {result.var(graph)!r}")
    for expected in required:
        if expected not in result.text:
            problems.append(f"missing {expected!r}")
    if last_value is not None and abs(float(result.var("W")) - last_value) > tolerance:
        problems.append(f"last result {result.var('W')} differs from {last_value}")
    if problems:
        print("FAIL", name, " | ".join(problems))
        return False
    print("PASS", name)
    return True


def main():
    checks = []

    # Dependent joint PMF. x-major cells: (0,0)=.1, (0,1)=.2,
    # (1,0)=.3, (1,1)=.4.
    checks.append(run_case(
        "dependent joint PMF, CDF, rectangle, conditional, event",
        [menu(6), menu(1), entered(2), entered(2), menu(1),
         entered(0), entered(1), entered(0), entered(1),
         entered(".1"), entered(".2"), entered(".3"), entered(".4"),
         menu(1), entered(2), entered(2),      # p(1,1)=2/5
         menu(2), entered(0), entered(0),      # F(0,0)=1/10
         menu(3), entered("⁻1"), entered(0), entered("⁻1"), entered(1),
         menu(4), menu(1), entered(2), menu(3),  # p(X|Y=1)
         menu(5), entered("X<Y"),
         menu(6), BACK],
        ["pX(0)=3/10", "pY(1)=3/5", "X,Y DEPENDENT",
         "p(x,y)=2/5", "F(0,0)=1/10", "=3/10",
         "X=0 =1/3", "X=1 =2/3", "P(EVENT)=SUM MATCHES", "=1/5"],
        last_value=0.2,
    ))

    checks.append(run_case(
        "independent counts normalized and conditional",
        [menu(6), menu(1), entered(2), entered(2), menu(2),
         entered(0), entered(1), entered(0), entered(1),
         entered(1), entered(1), entered(1), entered(1),
         menu(4), menu(1), entered(1), menu(3), menu(6), BACK],
        ["TOTAL WEIGHT=4", "pX(0)=1/2", "pY(0)=1/2",
         "X,Y INDEPENDENT", "X=0 =1/2"],
    ))

    checks.append(run_case(
        "zero-probability condition is undefined",
        [menu(6), menu(1), entered(2), entered(2), menu(1),
         entered(0), entered(1), entered(0), entered(1),
         entered(".5"), entered(0), entered(".5"), entered(0),
         menu(4), menu(1), entered(2), menu(3), menu(6), BACK],
        ["CONDITION HAS p=0", "CONDITIONAL UNDEFINED"],
    ))

    checks.append(run_case(
        "uniform square joint PDF, marginals, conditionals and event",
        [menu(6), menu(2), entered(1), entered(0), entered(1),
         entered(0), entered(1), entered(0),
         menu(1), entered(0), entered(".5"), entered(0), entered(".5"),
         menu(2), entered(".5"), entered(".5"),
         menu(3), menu(1), entered(".5"), menu(2), entered(".5"), menu(3),
         menu(4), entered(".5"), entered(".5"),
         menu(5), entered("X<Y"), menu(6), BACK],
        ["AREA=∫∫f=1", "P(RECT)=c*∫∫ f", "=1/4",
         "F(x,y)=∫∫ f TO x,y", "fX(.5)=1", "fY(.5)=1",
         "f(x|y)=1", "f(y|x)=1", "P(EVENT)=∫∫1_EVENT*f"],
        last_value=0.5, tolerance=2e-3,
    ))

    checks.append(run_case(
        "triangular support and unknown normalizing factor",
        [menu(6), menu(2), entered("X+Y<1"), entered(0), entered(1),
         entered(0), entered(1), entered(1),
         menu(5), entered("X+Y<.5"), menu(6), BACK],
        ["JOINT PDF CHECK", "c=1/AREA=", "P(EVENT)=∫∫1_EVENT*f"],
        last_value=0.25, tolerance=2e-3,
    ))

    checks.append(run_case(
        "typed one-variable CDF leaves graph functions unchanged",
        [menu(4), menu(2), entered("1-𝑒^(⁻2X)"), entered(0),
         entered(50), menu(3), entered(1), menu(6), BACK],
        ["P(X>1)=1-F(a)"],
    ))

    checks.append(run_case(
        "transformation tool leaves graph functions unchanged",
        [menu(5), entered("2X"), entered(0), entered(1),
         entered("𝑒^(⁻X)"), menu(2), entered(1), menu(2), BACK],
        ["F_Y(y)=1-F_X(x)", "f_Y(y)="],
    ))

    print(f"\n{sum(checks)}/{len(checks)} joint/state checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
