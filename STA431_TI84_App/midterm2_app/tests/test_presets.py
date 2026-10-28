#!/usr/bin/env python3
"""Run all thirteen STA 431 homework presets through the real loader and solver menus.

Menus are chosen by item TEXT (m('BACK')), never by position. Every expected value is computed
here with fractions.Fraction or sympy, not copied from a run of the app.
"""
from fractions import Fraction as Fr
import math
import unittest

import sympy as sp

from m2test import ROOT, m, i, run
from tilint import lint_file
import tibuild

x, y, t = sp.symbols('x y t')


def fs(v):
    """Fraction -> the text M2FMT prints ('⁻1/36', '13/4', '2')."""
    v = Fr(v)
    s = str(abs(v.numerator)) if v.denominator == 1 else f"{abs(v.numerator)}/{v.denominator}"
    return ("⁻" if v < 0 else "") + s


def F(e):
    """sympy Rational -> Fraction."""
    e = sp.nsimplify(e)
    return Fr(int(sp.numer(e)), int(sp.denom(e)))


def pmf(weights):
    tot = sum(weights.values())
    return {k: Fr(w) / tot for k, w in weights.items()}, Fr(tot)


HW4 = 'HW4 COMMON +431'
HW5A = 'HW5 Q1 TO Q4'
HW5B = 'HW5 Q5 TO Q8'


class Presets(unittest.TestCase):
    def run_case(self, group, question, solver, expected=None, required=()):
        actions = [m(group), m(question)] + solver + [m('BACK'), m('BACK')]
        r = run('M2RUN', actions, max_steps=7_000_000)
        self.assertEqual(r.var('Z'), 0, 'preset routing flag not cleared')
        for key, target in (expected or {}).items():
            self.assertTrue(math.isclose(float(r.var(key)), float(target), rel_tol=1e-7, abs_tol=1e-7),
                            f"{key}={r.var(key)} expected {target}\n{r.text[-3000:]}")
        for needle in required:
            self.assertIn(needle, r.text)
        return r

    def test_main_menu_lists_only_sta431_groups(self):
        r = run('M2RUN', [m('BACK')])
        items = r.screens[0]['menu']['items']
        self.assertEqual(items, [HW4, HW5A, HW5B, 'BACK'])

    def test_hw4_q1_joint_table_conditional_and_independence(self):
        p, tot = pmf({(a, b): a + b * b for a in (1, 2) for b in (1, 2, 3)})
        px = {a: sum(v for (u, _), v in p.items() if u == a) for a in (1, 2)}
        hy2 = sum(v for (_, w), v in p.items() if w == 2)
        cond = [p[(1, 2)] / hy2, p[(2, 2)] / hy2]
        self.assertEqual(tot, 37)
        self.run_case(HW4, 'Q1 JOINT PMF',
                      [m('MARG/CONDITIONAL'), m('MARGINAL TABLES'), m('X GIVEN Y'), i(2),
                       m('INDEPENDENCE'), m('BACK'), m('BACK')],
                      required=[fs(1 / tot), fs(px[1]), fs(px[2]), fs(cond[0]), fs(cond[1]),
                                'NUMERIC FACTORIZATION FAIL'])

    def test_hw4_q2_joint_normalization(self):
        # P2: JOINT DENSITY (Z=99) normalizes the typed shape 2X+Y on the preloaded rectangle.
        total = F(sp.integrate(2 * x + y, (y, 0, 2), (x, 0, 1)))
        r = self.run_case(HW4, 'Q2 JOINT PDF', [m('BACK')], {'M': 1 / total},
                          ['TOTAL ∫∫q=' + fs(total), 'c=' + fs(1 / total), 'EXACT (POLYNOMIAL)'])
        self.assertFalse([s for s in r.screens if s['event'] == 'input'])      # no prompts at Z=99

    def test_hw4_q3_series_lifetime(self):
        # The device fails if either component fails: P(min(X,Y)≤1) = 1 - P(X>1,Y>1).
        surv = F(sp.integrate((x + y) / 8, (y, 1, 2), (x, 1, 2)))
        self.run_case(HW4, 'Q3 SERIES LIFETIME', [m('EVENTS + LIMITS'), m('MIN/MAX'), m('min(X,Y)≤t'), i(1),
                                                  m('BACK'), m('BACK')],
                      {'A': 1 - surv}, ['FAILS IF EITHER FAILS', '=1-P(X>t,Y>t)', '=1-' + fs(surv),
                                        '=' + fs(1 - surv)])

    def test_hw4_q4_both_discrete_events(self):
        p, _ = pmf({(a, b): a + b for a in (1, 2) for b in (1, 2, 3, 4)})
        gt = sum(v for (a, b), v in p.items() if a > b)
        le3 = sum(v for (a, b), v in p.items() if a + b <= 3)
        self.run_case(HW4, 'Q4 PMF EVENTS',
                      [m('EVENT PROB'), m('P(EVENT)'), i('X>Y'), m('P(EVENT)'), i('X+Y≤3'),
                       m('BACK'), m('BACK')],
                      {'W': le3}, [fs(gt), fs(le3)])

    def test_hw4_q5_variable_bound_probability(self):
        target = F(sp.integrate((2 * x + y) / 4, (y, x, 2), (x, 0, 1)))
        self.run_case(HW4, 'Q5 X LESS Y', [m('EVENTS + LIMITS'), m('X<Y OR X>Y'), m('X<Y'), m('REVERSE ORDER'),
                                           m('BACK'), m('BACK')],
                      {'A': target}, ['P(X<Y)=' + fs(target), 'y FROM x TO 2', 'x FROM 0 TO y'])

    def test_hw5_q1_pmf_moments(self):
        p, tot = pmf({a: a * a + a for a in (1, 2, 3, 4)})
        e1 = sum(a * v for a, v in p.items())
        e2 = sum(a * a * v for a, v in p.items())
        self.run_case(HW5A, 'Q1 PMF MOMENTS', [m('MOMENTS'), m('BACK')],
                      {'E': e1, 'G': e2, 'B': e2 - e1 * e1}, [fs(1 / tot), fs(e2 - e1 * e1)])

    def test_hw5_q2_symmetric_density_and_transformed_square(self):
        f = sp.Rational(3, 4) * (1 - x**2)
        e2 = F(sp.integrate(x**2 * f, (x, -1, 1)))
        e4 = F(sp.integrate(x**4 * f, (x, -1, 1)))
        self.run_case(HW5A, 'Q2 PDF AND SQUARE',
                      [m('MEAN+VARIANCE'), m('FUNCTION g(X)'), i('X²'), m('BACK')],
                      {'E': e2, 'F': e4, 'G': e4 - e2 * e2}, [fs(e2), fs(e4 - e2 * e2)])

    def test_hw5_q3_exponential_mgf(self):
        M = 3 / (3 - t)
        e1 = F(sp.diff(M, t).subs(t, 0))
        e2 = F(sp.diff(M, t, 2).subs(t, 0))
        self.run_case(HW5A, 'Q3 EXPONENTIAL MGF', [m('BACK')],
                      required=[fs(e1), fs(e2), fs(e2 - e1 * e1), 'DOMAIN t<3'])

    def test_hw5_q4_affine_mgf(self):
        Mz = sp.exp(-t) * sp.exp(4 * (t / 4) + 8 * (t / 4)**2)
        half = F(sp.diff(sp.log(Mz), t, 2).subs(t, 0) / 2)
        self.run_case(HW5A, 'Q4 AFFINE MGF', [m('BACK')],
                      required=['ORIGINAL X MOMENTS', 'Z=aX+b MOMENTS', 'H=' + fs(half), 'DOMAIN ALL REAL t'])

    def test_hw5_q5_claim_variance(self):
        a, b = Fr(2), Fr(11, 10)
        var = a * a * 300 + b * b * 500 + 2 * a * b * 150
        self.run_case(HW5B, 'Q5 CLAIM VARIANCE', [m('BACK')], required=[fs(var), 'MEAN NOT PROVIDED'])

    def test_hw5_q6_three_variable_variance(self):
        cv = [[4, 1, -1], [1, 9, 0], [-1, 0, 2]]
        a = [3, -2, 1]
        var = sum(a[r] * a[c] * cv[r][c] for r in range(3) for c in range(3))
        self.run_case(HW5B, 'Q6 THREE VARIABLES', [m('BACK')], required=[fs(var), 'MEAN NOT PROVIDED'])

    def test_hw5_q7_conditional_moments(self):
        # LEAN-B: the preset loads q=X+Y on the unit square into JOINT DENSITY (Z=99)
        joint = x + y
        f = joint.subs(y, sp.Rational(1, 2)) / sp.integrate(joint, (x, 0, 1)).subs(y, sp.Rational(1, 2))
        e1 = F(sp.integrate(x * f, (x, 0, 1)))
        e2 = F(sp.integrate(x**2 * f, (x, 0, 1)))
        self.run_case(HW5B, 'Q7 CONDITIONAL',
                      [m('GIVEN A VALUE'), m('GIVEN Y=y'), i('1/2'), m('BACK'), m('BACK'), m('BACK')],
                      {'A': e1}, [fs(e1), fs(e2), fs(e2 - e1 * e1), '=1/2+x'])

    def test_hw5_q8_joint_moments_and_conditional(self):
        p, _ = pmf({(a, b): a + b for a in (1, 2, 3) for b in (1, 2, 3)})
        ex = sum(a * v for (a, _), v in p.items())
        exy = sum(a * b * v for (a, b), v in p.items())
        cov = exy - ex * ex
        g1 = sum(v for (a, _), v in p.items() if a == 1)
        ey = sum(b * v for (a, b), v in p.items() if a == 1) / g1
        ey2 = sum(b * b * v for (a, b), v in p.items() if a == 1) / g1
        self.run_case(HW5B, 'Q8 JOINT MOMENTS',
                      [m('MOMENTS'), m('MARG/CONDITIONAL'), m('Y GIVEN X'), i(1), m('BACK'), m('BACK')],
                      {'E': ey, 'G': ey2, 'B': ey2 - ey * ey},
                      [fs(ex), fs(exy), fs(cov), fs(ey)])

    def test_loader_token_and_structural_lints(self):
        p = ROOT / 'src' / 'M2RUN.txt'
        self.assertEqual(lint_file(str(p)), [])
        self.assertEqual(tibuild.lint_program('M2RUN', tibuild.clean_source(p.read_text())), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
