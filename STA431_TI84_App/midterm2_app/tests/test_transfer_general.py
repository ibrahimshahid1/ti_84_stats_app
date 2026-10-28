#!/usr/bin/env python3
"""Structural transfer checks: unfamiliar models entered into general solvers.

These tests never invoke M2RUN or use its homework models. Exact finite results
come from Fraction arithmetic, continuous targets from independent integrals,
and covariance targets from an independent-variable construction. Numerical
quadrature/finite-difference tolerances are explicit. This is off-device testing.
"""
from fractions import Fraction as F
from pathlib import Path
import math
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tisim import Sim


def m(n):
    return {"menu": n}


BACK = m("BACK")


def entry(value):
    s = str(value)
    if isinstance(value, (int, float, F)) and value < 0:
        s = "⁻" + s[1:]
    return {"input": s}


def values(*items):
    return [entry(x) for x in items]


def grid(xs, ys, q):
    return [m("FORMULA/GRID")] + values(xs, ys, q)


def rows(data):
    out = [m("JOINT X,Y"), entry(len(data))]
    for row in data:
        out.extend(values(*row))
    return out


def one_d(q, lo, hi):
    return [m("1D PDF OR SLICE")] + values(q, 0, lo, hi)


def double(q, lo, hi, yl, yh, g="1", n=4):
    return [m("DOUBLE INTEGRAL")] + values(q, 0, lo, hi, yl, yh, g, n)


def slice_data(direction, q, c, given, lo, hi):
    return [m({1: "X GIVEN Y", 2: "Y GIVEN X"}[direction])] + values(q, c, given, lo, hi)


def exact_moment(data, g):
    """Independent weighted average of an arbitrary function over finite rows."""
    total = sum(F(w) for x, y, w in data)
    return sum(F(w) * g(F(x), F(y)) for x, y, w in data) / total


def parse_number(s):
    s = s.strip().replace("⁻", "-").replace("ᴇ", "e")
    if "/" in s:
        a, b = s.split("/")
        return float(a) / float(b)
    return float(s)


# The x/y support cannot be described as a Cartesian product.
NONRECT = [(x, y, 1 + x + 2*y)
           for x in range(4) for y in range(3) if x+y <= 3]
INIT = {"Z": 0, "Y1": "X²+7", "Y9": "X+9", "L₁": [81, 82], "L₂": [61, 62]}


class TransferGeneral(unittest.TestCase):
    def run_general(self, program, actions):
        result = Sim(str(ROOT / "src")).run(
            program, actions=actions, init_vars=INIT, max_steps=2_000_000,
        )
        self.assertIsNone(result.error, result.text)
        self.assertIn(result.ended_reason, ("end", "return"), result.text)
        self.assertEqual(result.leaks, 0, result.text)
        self.assertFalse(result.warnings, result.warnings)
        for k, value in INIT.items():
            self.assertEqual(result.var(k), value, f"User state {k} changed")
        self.assertNotIn("HOMEWORK QUICK SOLVE", result.text)
        self.assertNotIn("PRELOAD", result.text)
        return result

    def near_vars(self, result, tolerance=1e-7, **expected):
        for k, value in expected.items():
            self.assertAlmostEqual(float(result.var(k)), float(value),
                                   delta=tolerance, msg=k + "\n" + result.text)

    def screen_value(self, result, title, label, value, tolerance=1e-6):
        screen = next(s for s in result.screens
                      if s["event"] == "pause" and s["rows"][0].strip() == title)
        lines = [x.strip() for x in screen["rows"]]
        self.assertAlmostEqual(parse_number(lines[lines.index(label)+1]),
                               float(value), delta=tolerance)

    def test_nonrectangular_finite_support_raw_rows(self):
        r = self.run_general("M2DISC", rows(NONRECT) + [m("MOMENTS"), BACK])
        ex = exact_moment(NONRECT, lambda x, y: x)
        ey = exact_moment(NONRECT, lambda x, y: y)
        ex2 = exact_moment(NONRECT, lambda x, y: x*x)
        ey2 = exact_moment(NONRECT, lambda x, y: y*y)
        exy = exact_moment(NONRECT, lambda x, y: x*y)
        self.near_vars(r, E=ex, F=ey, G=ex2, H=ey2, J=exy,
                       B=ex2-ex*ex, D=ey2-ey*ey, C=exy-ex*ey)

    def test_masked_grid_and_nonlinear_joint_payoff(self):
        r = self.run_general("M2DISC",
            grid("{0,1,2,3}", "{0,1,2}", "(1+X+2Y)*(X+Y≤3)") +
            [m("FUNCTION g(X,Y)"), entry("2X-Y²"), BACK])
        mean = exact_moment(NONRECT, lambda x, y: 2*x-y*y)
        second = exact_moment(NONRECT, lambda x, y: (2*x-y*y)**2)
        self.near_vars(r, E=mean, G=second, B=second-mean*mean)

    def test_conditioning_event_differs_from_conditioning_at_value(self):
        # On this support, X>=2 contains a row with X=3,Y=0 as well.
        r = self.run_general("M2DISC", rows(NONRECT) +
            [m("EVENT PROB"), m("P(EVENT|GIVEN)"), entry("Y≥1"), entry("X≥2"),
             m("P(EVENT|GIVEN)"), entry("Y≥1"), entry("X=2"), BACK, BACK])
        self.assertIn("5/12", r.text)
        self.assertIn("5/8", r.text)
        self.near_vars(r, W=F(5, 8))
        self.assertNotEqual(F(5, 12), F(5, 8))

    def test_conditional_arbitrary_payoff_via_restricted_weights(self):
        # FUNCTION g uses the loaded model: include the condition in new weights.
        conditional_rows = [row for row in NONRECT if row[0] >= 1]
        r = self.run_general("M2DISC",
            grid("{0,1,2,3}", "{0,1,2}",
                 "(1+X+2Y)*(X+Y≤3)*(X≥1)") +
            [m("FUNCTION g(X,Y)"), entry("X*Y+Y²"), BACK])
        mean = exact_moment(conditional_rows, lambda x, y: x*y+y*y)
        second = exact_moment(conditional_rows, lambda x, y: (x*y+y*y)**2)
        self.near_vars(r, E=mean, G=second, B=second-mean*mean)

    def test_curved_slice_given_x_pdf_and_interval(self):
        # Joint PDF3 on0<x<1,0<y<x^2; Y|X=a is uniform(0,a^2).
        r = self.run_general("M2SLICE",
            slice_data(2, "1", 3, F(3,5), 0, "X²") +
            [m("PDF AT POINT"), entry(F(1,10)), m("INTERVAL PROB"), entry(F(1,5)), entry(F(9,25)), BACK])
        self.near_vars(r, M=F(27,25), E=F(9,50), F=F(27,625),
                       H=F(27,2500), O=F(4,9), P=3)
        self.assertIn("25/9", r.text)

    def test_curved_slice_reverse_requires_square_root_bound(self):
        # GivenY=1/4, x runs1/2..1, NOT0..1.
        r = self.run_general("M2SLICE",
            slice_data(1, "1", 3, F(1,4), "√(Y)", 1) + [BACK])
        self.near_vars(r, M=F(3,2), E=F(3,4), F=F(7,12), H=F(1,48))

    def test_continuous_event_conditioning_curved_region(self):
        # B={X>1/2}; I=P(B)=7/8 and J=E[Y1_B]=93/320.
        # Conditional mean J/I=93/280. A finerN addresses the x^4 outer term.
        r = self.run_general("M2CONT",
            double("3", F(1,2), 1, 0, "X²", "Y", n=16) + [m("NORMALIZE FULL S"), BACK])
        self.near_vars(r, tolerance=2e-7, F=F(7,8), G=F(93,320), W=F(93,280))
        self.assertIn("FULL SUPPORT ONLY", r.text)

    def test_probability_requires_two_regions(self):
        # PDF1 on0<x<2,0<y<x/2. X+Y<=3/2 changes upperboundary atx=1.
        first = self.run_general("M2CONT", double("1", 0, 1, 0, "X/2") + [BACK])
        second = self.run_general("M2CONT", double("1", 1, F(3,2), 0, "3/2-X") + [BACK])
        self.near_vars(first, F=F(1,4))
        self.near_vars(second, F=F(1,8))
        self.assertAlmostEqual(float(first.var("F"))+float(second.var("F")), F(3,8), delta=1e-7)

    def test_generic_mgf_from_three_point_distribution(self):
        # M(t)=.2e^-2t+.5e^t+.3e^4t; mean13/10,var441/100.
        q = "𝑒^(⁻2X)/5+𝑒^(X)/2+3*𝑒^(4X)/10"
        r = self.run_general("M2MGF", [m("TYPE MGF NUMERIC")] + values(q, -2, 3) +
                             [m("EVAL Mz AT t"), entry(F(1,5)), BACK])
        self.screen_value(r, "APPROX X MOMENTS", "E(X)", F(13,10), 1e-4)
        self.screen_value(r, "APPROX X MOMENTS", "VAR(X)", F(441,100), 1e-4)
        self.screen_value(r, "APPROX Z=aX+b MOMENTS", "E(Z)", F(2,5), 2e-4)
        self.screen_value(r, "APPROX Z=aX+b MOMENTS", "VAR(Z)", F(441,25), 5e-4)
        target = math.exp(3/5) * (math.exp(4/5)/5 + math.exp(-2/5)/2 + 3*math.exp(-8/5)/10)
        self.near_vars(r, tolerance=1e-7, Y=target)

    def test_negative_scale_reverses_new_mgf_domain(self):
        # Rate5/2, Z=7/4-3X/2 -> domain t>-5/3.
        r = self.run_general("M2MGF", [m("EXPONENTIAL RATE")] + values(F(5,2), F(-3,2), F(7,4)) +
                             [m("EVAL Mz AT t"), entry(F(1,2)), BACK])
        self.screen_value(r, "Z=aX+b MOMENTS", "E(Z)", F(23,20))
        self.screen_value(r, "Z=aX+b MOMENTS", "VAR(Z)", F(9,25))
        self.assertIn("DOMAIN t>⁻1.666667", r.text)
        self.near_vars(r, Y=10*math.exp(7/8)/13)

    def test_two_combinations_with_three_correlated_inputs(self):
        # Construct X=U,Y=U+V,Z=V+W from independent U,V,W of variances2,3,5.
        # Then a=(1,-1,2) ->V+2W, b=(-2,3,1) ->U+4V+W.
        args = [3, 1, 2, -2, 5, 4, 8, 2, 0, 3,
                1, -2, -1, 3, 2, 1, 7, -5]
        r = self.run_general("M2COV", [m("TWO COMBINATIONS"), m("MEAN+VAR/COV")] + values(*args) + [BACK])
        self.screen_value(r, "COMBINATION U", "E(U)", 18)
        self.screen_value(r, "COMBINATION U", "VAR(U)", 23)
        self.screen_value(r, "COMBINATION V", "E(V)", -9)
        self.screen_value(r, "COMBINATION V", "VAR(V)", 55)
        self.screen_value(r, "TWO COMBINATIONS", "COV(U,V)", 22)
        self.screen_value(r, "TWO COMBINATIONS", "CORR(U,V)", 22/math.sqrt(23*55))

    def test_total_variance_using_conditional_mean_and_variance_functions(self):
        # Y~Uniform(1,3), X|Y=y~Uniform(0,y^2).
        # Var(E[X|Y])=Var(Y^2/2)=61/45, E[Var(X|Y)]=E[Y^4/12]=121/60.
        r = self.run_general("M2CONT", one_d("1", 1, 3) +
            [m("FUNCTION g(X)"), entry("X²/2"), m("FUNCTION g(X)"), entry("X^4/12"), BACK])
        for value in ["13/6", "61/45", "121/60"]:
            self.assertIn(value, r.text)
        self.near_vars(r, E=F(121,60))
        self.assertEqual(F(61,45)+F(121,60), F(607,180))


if __name__ == "__main__":
    unittest.main(verbosity=2)
