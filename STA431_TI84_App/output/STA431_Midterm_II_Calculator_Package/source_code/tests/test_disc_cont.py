#!/usr/bin/env python3
"""Token-stream homework and edge-case regressions for M2DISC and M2CONT.

Off-device numerical/program-flow checks, not a physical CE test. Menus are chosen by item text.
Expected values are computed here: Fraction for finite tables, sympy for densities.
(P1: the triangle case uses Freund Ch4 Ex16, density 2 on x+y<1; STA 431 problems only.)
"""
from fractions import Fraction as Fr
import math

import sympy as sp

from m2test import INIT, SRC, m, i
from tisim import Sim

x, y = sp.symbols('x y')


def disc_rows(rows, joint=True):
    actions = [m('JOINT X,Y' if joint else 'UNIVARIATE PMF'), i(len(rows))]
    for row in rows:
        actions.extend(i(v) for v in row)
    return actions


def grid(xvalues, yvalues, q):
    return [m('FORMULA/GRID'), i(xvalues), i(yvalues), i(q)]


def one_d(q, lo, hi, parameter=0):
    return [m('1D PDF OR SLICE'), i(q), i(parameter), i(lo), i(hi)]


def two_d(q, xlo, xhi, ylo, yhi, g="1", n=4, parameter=0):
    return [m('DOUBLE INTEGRAL'), i(q), i(parameter), i(xlo), i(xhi), i(ylo), i(yhi), i(g), i(n)]


BACK = m('BACK')


# ------------------------------------------------------------------ independent reference values
def table(rows):
    """rows (x,y,w) -> normalized {(x,y): p} with Fraction weights."""
    tot = sum(Fr(w) for _, _, w in rows)
    return {(Fr(a), Fr(b)): Fr(w) / tot for a, b, w in rows}, tot


def ev(p, g):
    return sum(v * g(a, b) for (a, b), v in p.items())


def joint_moments(p):
    ex, ey = ev(p, lambda a, b: a), ev(p, lambda a, b: b)
    ex2, ey2, exy = ev(p, lambda a, b: a * a), ev(p, lambda a, b: b * b), ev(p, lambda a, b: a * b)
    return {"E": ex, "F": ey, "G": ex2, "H": ey2, "J": exy, "B": ex2 - ex * ex, "D": ey2 - ey * ey,
            "C": exy - ex * ey}


def conditional(p, given_index, value, which):
    """Moments of coordinate `which` (0=x,1=y) given coordinate given_index == value."""
    sub = {k: v for k, v in p.items() if k[given_index] == value}
    tot = sum(sub.values())
    m1 = sum(v * k[which] for k, v in sub.items()) / tot
    m2 = sum(v * k[which] ** 2 for k, v in sub.items()) / tot
    return m1, m2, m2 - m1 * m1


def max_factor_gap(p):
    xs = sorted({a for a, _ in p})
    ys = sorted({b for _, b in p})
    gx = {a: sum(v for (u, _), v in p.items() if u == a) for a in xs}
    hy = {b: sum(v for (_, w), v in p.items() if w == b) for b in ys}
    return max(abs(p.get((a, b), Fr(0)) - gx[a] * hy[b]) for a in xs for b in ys)


def fs(v):
    v = Fr(v)
    s = str(abs(v.numerator)) if v.denominator == 1 else f"{abs(v.numerator)}/{v.denominator}"
    return ("⁻" if v < 0 else "") + s


def S(e):
    """sympy exact value -> Fraction."""
    e = sp.nsimplify(e)
    return Fr(int(sp.numer(e)), int(sp.denom(e)))


def integ(q, lo, hi):
    return sp.integrate(q, (x, lo, hi))


def dbl(q, xlo, xhi, ylo, yhi):
    return sp.integrate(q, (y, ylo, yhi), (x, xlo, xhi))


CASES = []


def check(name, program, actions, expected=None, text=(), tolerance=1e-7, absent=()):
    result = Sim(str(SRC)).run(program, actions=actions, init_vars=INIT, max_steps=7_000_000)
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
    for needle in absent:
        if needle in result.text:
            errors.append("must not show " + repr(needle))
    for key, target in (expected or {}).items():
        actual = result.var(key)
        if not isinstance(actual, (float, int)) or not math.isclose(actual, float(target), rel_tol=tolerance,
                                                                     abs_tol=tolerance):
            errors.append(f"{key}={actual}, expected {float(target)}")
    for key, value in INIT.items():
        if result.var(key) != value:
            errors.append(f"user {key} changed to {result.var(key)!r}")
    if any(key.startswith("M2") for key in result.vars["lists"]):
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
    p51, t51 = table([(a, 0, w) for a, w in h51])
    mom51 = joint_moments(p51)
    exp51 = {"A": t51, "E": mom51["E"], "G": mom51["G"], "B": mom51["B"]}
    check("HW5 Q1 normalization and moments", "M2DISC",
          disc_rows(h51, False) + [m('MOMENTS'), BACK], exp51,
          [fs(1 / t51), fs(mom51["E"]), fs(mom51["G"]), fs(mom51["B"])])

    h41 = [(a, b, a + b * b) for a in (1, 2) for b in (1, 2, 3)]
    p41, t41 = table(h41)
    c41 = conditional(p41, 1, 2, 0)                       # X given Y=2
    check("HW4 Q1 formula/grid input", "M2DISC",
          grid("{1,2}", "{1,2,3}", "X+Y²") + [m('MARG/CONDITIONAL'), m('X GIVEN Y'), i(2), BACK, BACK],
          {"E": c41[0], "B": c41[2]},
          [fs(1 / t41), fs(p41[(1, 2)] / (p41[(1, 2)] + p41[(2, 2)])), fs(p41[(2, 2)] / (p41[(1, 2)] + p41[(2, 2)]))])
    check("HW5 Q1 univariate formula/grid input", "M2DISC",
          grid("{1,2,3,4}", "{0}", "X²+X") + [m('MOMENTS'), BACK], exp51, [fs(1 / t51), fs(mom51["B"])])

    h58 = [(a, b, a + b) for a in (1, 2, 3) for b in (1, 2, 3)]
    p58, _ = table(h58)
    mom58 = joint_moments(p58)
    check("HW5 Q8 formula/grid input", "M2DISC",
          grid("{1,2,3}", "{1,2,3}", "X+Y") + [m('MOMENTS'), BACK],
          {"E": mom58["E"], "F": mom58["F"], "J": mom58["J"], "C": mom58["C"]})

    check("grid duplicate-coordinate rejection", "M2DISC",
          grid("{1,1}", "{1,2}", "1") + [BACK], text=["REPEATED (x,y) PAIR"])
    check("grid pair-count guard", "M2DISC",
          grid("{1,2,3,4,5,6}", "{1,2,3,4,5,6}", "1") + [BACK], text=["GRID MUST HAVE 1-30 PAIRS"])
    check("grid negative-weight rejection", "M2DISC",
          grid("{1,2}", "{1}", "⁻X") + [BACK], text=["WEIGHTS MUST BE ≥0"])
    check("grid zero-total rejection", "M2DISC",
          grid("{1,2}", "{1}", "0") + [BACK], text=["WITH POSITIVE TOTAL"])

    gx1 = sum(v for (a, _), v in p41.items() if a == 1)
    hy2 = sum(v for (_, b), v in p41.items() if b == 2)
    check("HW4 Q1 marginal and conditional PMF", "M2DISC",
          disc_rows(h41) + [m('MARG/CONDITIONAL'), m('pX AT x'), i(1), m('pY AT y'), i(2),
                            m('X GIVEN Y'), i(2), BACK, BACK],
          {"E": c41[0], "G": c41[1], "B": c41[2]},
          [fs(1 / t41), fs(gx1), fs(hy2), fs(p41[(1, 2)] / hy2), fs(p41[(2, 2)] / hy2)])

    c58 = conditional(p58, 0, 1, 1)                       # Y given X=1
    check("HW5 Q8 joint and conditional moments", "M2DISC",
          disc_rows(h58) + [m('MOMENTS'), m('MARG/CONDITIONAL'), m('Y GIVEN X'), i(1), BACK, BACK],
          {"E": c58[0], "G": c58[1], "B": c58[2], "C": mom58["C"]},
          [fs(mom58["E"]), fs(mom58["J"]), fs(c58[0])])

    h44 = [(a, b, a + b) for a in (1, 2) for b in (1, 2, 3, 4)]
    p44, _ = table(h44)
    gt44 = ev(p44, lambda a, b: Fr(a > b))
    le44 = ev(p44, lambda a, b: Fr(a + b <= 3))
    check("HW4 Q4 event masks", "M2DISC",
          disc_rows(h44) + [m('EVENT PROB'), m('P(EVENT)'), i("X>Y"), m('P(EVENT)'), i("X+Y≤3"), BACK, BACK],
          {"W": le44}, [fs(gt44), fs(le44)])
    cond_ev = p58[(1, 3)] / sum(v for (a, _), v in p58.items() if a == 1)
    check("joint conditional event mask", "M2DISC",
          disc_rows(h58) + [m('EVENT PROB'), m('P(EVENT|GIVEN)'), i("Y=3"), i("X=1"), BACK, BACK],
          {"W": cond_ev}, [fs(cond_ev)])
    g1, g2 = ev(p51, lambda a, b: a ** 2), ev(p51, lambda a, b: a ** 4)
    check("discrete function square", "M2DISC",
          disc_rows(h51, False) + [m('FUNCTION g(X,Y)'), i("X²"), BACK],
          {"E": g1, "G": g2, "B": g2 - g1 * g1})
    check("raw and central product moments", "M2DISC",
          disc_rows(h58) + [m('PRODUCT MOMENTS'), m('RAW X^r Y^s'), i(1), i(1),
                            m('CENTRAL PRODUCT'), i(1), i(1), BACK, BACK],
          {"W": mom58["C"]}, [fs(mom58["J"])])
    check("zeroth product moment handles zero data", "M2DISC",
          disc_rows([(0, 0, 1), (1, 1, 1)]) + [m('PRODUCT MOMENTS'), m('RAW X^r Y^s'), i(0), i(0), BACK, BACK],
          {"W": 1})
    check("zero-probability conditioning guards", "M2DISC",
          disc_rows([(1, 1, 1), (2, 2, 1)]) +
          [m('MARG/CONDITIONAL'), m('X GIVEN Y'), i(5), BACK, m('EVENT PROB'), m('P(EVENT|GIVEN)'),
           i("X>0"), i("Y=5"), BACK, BACK],
          text=["CONDITIONAL UNDEFINED", "GIVEN EVENT HAS p=0"])
    full = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]
    check("full Cartesian independence check", "M2DISC",
          disc_rows(full) + [m('MARG/CONDITIONAL'), m('INDEPENDENCE'), BACK, BACK],
          {"A": max_factor_gap(table(full)[0])}, ["NUMERIC MATCH TO 1E-9"])
    diag = [(0, 0, 1), (1, 1, 1)]
    check("missing-pair dependence check", "M2DISC",
          disc_rows(diag) + [m('MARG/CONDITIONAL'), m('INDEPENDENCE'), BACK, BACK],
          {"A": max_factor_gap(table(diag)[0])}, ["NUMERIC FACTORIZATION FAIL"])

    # ---------------------------------------------------------------- M2CONT one variable
    q7 = x + sp.Rational(1, 2)
    m7 = [S(integ(x ** r * q7, 0, 1)) for r in range(3)]
    e7, f7 = m7[1] / m7[0], m7[2] / m7[0]
    check("HW5 Q7 continuous conditional slice", "M2CONT",
          one_d("X+A", 0, 1, .5) + [m('MEAN+VARIANCE'), BACK],
          {"D": m7[0], "E": e7, "F": f7, "G": f7 - e7 * e7}, [fs(e7), fs(f7 - e7 * e7)])
    q2 = sp.Rational(3, 4) * (1 - x ** 2)
    e2, e4 = S(integ(x ** 2 * q2, -1, 1)), S(integ(x ** 4 * q2, -1, 1))
    check("HW5 Q2 symmetric density and square", "M2CONT",
          one_d("3/4*(1-X²)", "⁻1", 1) + [m('MEAN+VARIANCE'), m('FUNCTION g(X)'), i("X²"), BACK],
          {"D": S(integ(q2, -1, 1)), "E": e2, "F": e4, "G": e4 - e2 * e2}, [fs(e4 - e2 * e2)])
    check("continuous interval clipped to support", "M2CONT",
          one_d("2X", 0, 1) + [m('INTERVAL PROB'), i("⁻2"), i("1/2"), BACK],
          {"W": S(integ(2 * x, 0, sp.Rational(1, 2)))})
    check("continuous empty interval", "M2CONT",
          one_d("2X", 0, 1) + [m('INTERVAL PROB'), i(2), i(3), BACK], {"W": 0})
    q3 = 3 * x ** 2
    mu3 = S(integ(x * q3, 0, 1))
    raw4, cen2 = S(integ(x ** 4 * q3, 0, 1)), S(integ((x - mu3) ** 2 * q3, 0, 1))
    check("continuous raw and central moments", "M2CONT",
          one_d("3X²", 0, 1) + [m('RAW/CENTRAL MOM'), m('RAW MOMENT'), i(4), m('CENTRAL MOMENT'), i(2),
                                BACK, BACK],
          {"W": cen2}, [fs(raw4), fs(cen2)])

    # ---------------------------------------------------------------- M2CONT double integral
    hw45 = S(dbl((2 * x + y) / 4, 0, 1, x, 2))
    check("HW4 Q5 double integral with variable bound", "M2CONT",
          two_d("(2X+Y)/4", 0, 1, "X", 2) + [BACK], {"D": hw45, "F": hw45}, [fs(hw45), "REFINED N=8"])
    hw43 = S(dbl((x + y) / 8, 1, 2, 1, 2))
    check("HW4 Q3 reliability complement rectangle", "M2CONT",
          two_d("(X+Y)/8", 1, 2, 1, 2) + [BACK], {"F": hw43}, [fs(hw43)])
    tot42, g42 = S(dbl(2 * x + y, 0, 1, 0, 2)), S(dbl((2 * x + y) * x * y, 0, 1, 0, 2))
    check("HW4 Q2 unknown normalization and product moment", "M2CONT",
          two_d("2X+Y", 0, 1, 0, 2, "X*Y") + [m('NORMALIZE FULL S'), BACK],
          {"F": tot42, "G": g42, "W": g42 / tot42}, [fs(1 / tot42), fs(g42 / tot42)])
    # Freund Ch4 Ex16: f=2 on x+y<1 (triangle; y runs 0..1-x). E(XY)=1/12. Simpson is exact (cubic).
    tri_f, tri_g = S(dbl(2, 0, 1, 0, 1 - x)), S(dbl(2 * x * y, 0, 1, 0, 1 - x))
    assert (tri_f, tri_g) == (1, Fr(1, 12))
    check("triangular support skips zero-length endpoint slice", "M2CONT",
          two_d("2", 0, 1, 0, "1-X", "X*Y") + [BACK], {"F": tri_f, "G": tri_g}, [fs(tri_g)])
    check("double-integration refinement comparison", "M2CONT",
          two_d("𝑒^(X+Y)", 0, 1, 0, 1, n=4) + [BACK],
          {"F": float(dbl(sp.exp(x + y), 0, 1, 0, 1))}, ["NOT CONVERGED - RAISE N"], tolerance=2e-6)
    # P1 numeric gating: q=6x on 0<x<y<1 with g=xy. RAW J=E(XY)=2/5, but Simpson N=4 and N=8 differ
    # (the inner integral is quartic), so no exact-looking fraction may be shown (old bug: 819/2048).
    gate_f, gate_g = S(dbl(6 * x, 0, 1, x, 1)), S(dbl(6 * x * x * y, 0, 1, x, 1))
    assert gate_g == Fr(2, 5)
    check("non-converged Simpson shows decimals only", "M2CONT",
          two_d("6X", 0, 1, "X", 1, "X*Y", n=4) + [m('NORMALIZE FULL S'), BACK],
          {"F": gate_f}, ["NOT CONVERGED - RAISE N", "SIMPSON N=4", "REFINED N=8"], tolerance=1e-9,
          absent=["819/2048", "51/128", "2/5"])
    gate = Sim(str(SRC)).run("M2CONT", two_d("6X", 0, 1, "X", 1, "X*Y", n=4) + [BACK], init_vars=INIT)
    assert abs(gate.var("G") - float(gate_g)) < 2e-3 and abs(gate.var("G") - float(gate_g)) > 1e-9
    check("converged Simpson keeps exact fractions", "M2CONT",
          two_d("6X", 0, 1, "X", 1, "X", n=8) + [BACK],
          {"F": gate_f, "G": S(dbl(6 * x * x, 0, 1, x, 1))}, [fs(S(dbl(6 * x * x, 0, 1, x, 1)))],
          absent=["NOT CONVERGED"])
    # P1 fix round 1: the cap N=100 and a change already below 1E-6 get rows that can be followed.
    gate100 = check("quartic outer integrand at N=100 says use the decimal", "M2CONT",
                    two_d("6X", 0, 1, "X", 1, "X*Y", n=100) + [BACK],
                    {"F": gate_f, "G": gate_g}, ["REFINED N=200", "CHANGE<1ᴇ⁻6 - USE DECIMAL"], tolerance=1e-8,
                    absent=["RAISE N", "2/5"])
    assert 0 < abs(gate100.var("G") - gate100.var("E")) < 1e-6
    sq = S(dbl(sp.sqrt(x), 0, 1, 0, 1))
    check("N=100 cap with a large change says it is the max", "M2CONT",
          two_d("√(X)", 0, 1, 0, 1, n=100) + [BACK], {"F": sq}, ["N=100 IS MAX - USE DECIMAL"],
          tolerance=1e-4, absent=["RAISE N", "2/3"])
    check("DOUBLE INTEGRAL menu NEW N reruns with the same region", "M2CONT",
          two_d("6X", 0, 1, "X", 1, "X*Y", n=8) + [m('NEW N'), i(16), BACK],
          {"F": gate_f, "G": gate_g}, ["SIMPSON N=8", "SIMPSON N=16", "REFINED N=32",
                                       "SIMPSON NEEDS AN EVEN N"], tolerance=1e-5)
    check("zero mass region is flagged", "M2CONT",
          two_d("0", 0, 1, 0, 1) + [BACK], {"F": 0}, ["I=0 - CHECK q AND BOUNDS"])
    # P1 fix round 1: ᴇ99 (HOW TO ENTER's infinity) used to give an exact-looking 0 (double integral)
    # or ERR:OVERFLOW (1-D). Infinite or huge bounds are rejected and re-prompted; a cutoff then works.
    # 2e^(-x-2y) on the quadrant: P(X>Y)=2/3, P(Y>X)=1/3 (Appendix C, sympy on (0,oo)).
    q2e = 2 * sp.exp(-x - 2 * y)
    pxy, pyx = sp.integrate(q2e, (y, 0, x), (x, 0, sp.oo)), sp.integrate(q2e, (y, x, sp.oo), (x, 0, sp.oo))
    assert (pxy, pyx) == (sp.Rational(2, 3), sp.Rational(1, 3))
    check("infinite x bound rejected, cutoff 20 gives P(X>Y)", "M2CONT",
          two_d("2𝑒^(⁻X-2Y)", 0, "ᴇ99", 0, "X")[:5] + [i(0), i(20), i(0), i("X"), i(1), i(100), BACK],
          {"F": pxy}, ["BOUNDS MUST BE FINITE", "NO ᴇ99, ABS MUST BE <1ᴇ5", "N=100 IS MAX - USE DECIMAL"],
          tolerance=5e-5, absent=["(A Y LIMIT IS INFINITE)"])
    check("infinite y bound rejected, cutoff 20 gives P(Y>X)", "M2CONT",
          two_d("2𝑒^(⁻X-2Y)", 0, 20, "X", "ᴇ99", n=8) + [i(0), i(20), i("X"), i(20), i(1), i(100), BACK],
          {"F": pyx}, ["BOUNDS MUST BE FINITE", "(A Y LIMIT IS INFINITE)"], tolerance=5e-5)
    qh = sp.exp(-x / 2) / 2                                # Mock 5 Q10 density; mean 2, E X^2 8
    cut = [integ(x ** r * qh, 0, 40) for r in range(3)]   # the cutoff integrals the tool computes
    assert sp.integrate(x * qh, (x, 0, sp.oo)) == 2
    check("1-D infinite upper bound rejected, cutoff 40 works", "M2CONT",
          one_d("𝑒^(⁻X/2)/2", 0, "ᴇ99") + [i(0), i(40), m('MEAN+VARIANCE'), BACK],
          {"D": float(cut[0]), "E": float(cut[1] / cut[0]), "F": float(cut[2] / cut[0])},
          ["BOUNDS MUST BE FINITE", "MEAN APPROX="], tolerance=1e-8)
    check("1-D huge lower bound rejected", "M2CONT",
          one_d("1", "⁻2ᴇ5", 1) + [i(0), i(1), m('MEAN+VARIANCE'), BACK],
          {"D": 1, "E": sp.Rational(1, 2)}, ["BOUNDS MUST BE FINITE"])
    check("reversed moving limits guard", "M2CONT",
          two_d("1", 0, 1, "X", "X-1") + [BACK], text=["Y LIMITS REVERSED"])
    check("negative density guard", "M2CONT",
          one_d("⁻X", 0, 1) + [BACK], text=["INVALID q OR ZERO MASS"])
    check("zero density guard", "M2CONT",
          one_d("0", 0, 1) + [BACK], text=["INVALID q OR ZERO MASS"])
    print(f"\n{sum(CASES)}/{len(CASES)} M2DISC/M2CONT cases passed")
    return 0 if all(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
