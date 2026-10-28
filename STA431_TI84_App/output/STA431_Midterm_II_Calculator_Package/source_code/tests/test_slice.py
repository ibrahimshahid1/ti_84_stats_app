#!/usr/bin/env python3
"""Numerical joint-slice tests (M2SLICE) against sympy calculations made in this file.

M2SLICE variables: M = marginal density value (c * slice mass), E = conditional mean,
F = conditional second moment, H = conditional variance, O = interval probability or
conditional density value, P = joint density value at a point.
The continuous slice cases use Freund Ex20/Ex24 and Mock 4 Q3 (STA 431 material only; P1).
"""
import unittest

import sympy as sp

from m2test import ROOT, m, i, run
from tilint import lint_file
import tibuild

x, y = sp.symbols('x y')


def data(direction, q, c, a, lo, hi):
    """direction 'X GIVEN Y' or 'Y GIVEN X', then the six inputs as the student types them."""
    return [m(direction)] + [i(v) for v in (q, c, a, lo, hi)]


def targets(q, c, given, a, lo, hi):
    """sympy marginal value and conditional moments of the slice at given=a (given is x or y)."""
    other = x if given is y else y
    s = q.subs(given, a)
    lo, hi = sp.sympify(lo).subs(given, a), sp.sympify(hi).subs(given, a)
    mass = sp.integrate(s, (other, lo, hi))
    e1 = sp.integrate(other * s, (other, lo, hi)) / mass
    e2 = sp.integrate(other**2 * s, (other, lo, hi)) / mass
    return {'M': c * mass, 'E': e1, 'F': e2, 'H': sp.simplify(e2 - e1**2)}, s, mass, other, lo, hi


def frac_text(v):
    v = sp.nsimplify(v)
    return str(v).replace('-', '⁻')


class Slice(unittest.TestCase):
    def run_slice(self, actions, program='M2SLICE'):
        return run(program, actions, max_steps=300_000)

    def values(self, r, expected, delta=1e-7):
        for k, v in expected.items():
            self.assertAlmostEqual(float(r.var(k)), float(v), delta=delta, msg=k + '\n' + r.text[-3000:])

    def test_hw4_q2_marginal_and_conditional_moments(self):
        exp, *_ = targets(2 * x + y, sp.Rational(1, 4), y, sp.Rational(1, 2), 0, 1)
        r = self.run_slice(data('X GIVEN Y', '2X+Y', '1/4', '1/2', 0, 1) + [m('BACK')])
        self.values(r, exp)
        for v in (exp['M'], exp['E'], exp['H']):
            self.assertIn(frac_text(v), r.text)

    def test_hw4_q2_conditional_density_at_point(self):
        exp, s, mass, other, *_ = targets(2 * x + y, sp.Rational(1, 4), y, sp.Rational(1, 2), 0, 1)
        h = sp.Rational(1, 2)
        r = self.run_slice(data('X GIVEN Y', '2X+Y', '1/4', '1/2', 0, 1) +
                           [m('PDF AT POINT'), i('1/2'), m('BACK')])
        self.values(r, {'O': s.subs(other, h) / mass, 'P': sp.Rational(1, 4) * s.subs(other, h)})

    def test_hw4_q2_reverse_marginal(self):
        exp, *_ = targets(2 * x + y, sp.Rational(1, 4), x, sp.Rational(1, 2), 0, 2)
        r = self.run_slice(data('Y GIVEN X', '2X+Y', '1/4', '1/2', 0, 2) + [m('BACK')])
        self.values(r, exp)

    def test_hw5_q7_conditional_moments(self):
        exp, *_ = targets(x + y, 1, y, sp.Rational(1, 2), 0, 1)
        r = self.run_slice(data('X GIVEN Y', 'X+Y', 1, '1/2', 0, 1) + [m('BACK')])
        self.values(r, exp)

    def test_hw5_q7_conditional_interval(self):
        _, s, mass, other, *_ = targets(x + y, 1, y, sp.Rational(1, 2), 0, 1)
        r = self.run_slice(data('X GIVEN Y', 'X+Y', 1, '1/2', 0, 1) +
                           [m('INTERVAL PROB'), i('1/2'), i(1), m('BACK')])
        self.values(r, {'O': sp.integrate(s, (other, sp.Rational(1, 2), 1)) / mass})

    def test_freund_ex20_slice_moments(self):
        # Freund Ex20 p139: f=2/3(x+2y) on the unit square, given Y=1/2.
        q = sp.Rational(2, 3) * (x + 2 * y)
        exp, *_ = targets(q, 1, y, sp.Rational(1, 2), 0, 1)
        self.assertEqual(exp['M'], 1)
        self.assertEqual((exp['E'], exp['F'], exp['H']),
                         (sp.Rational(5, 9), sp.Rational(7, 18), sp.Rational(13, 162)))
        r = self.run_slice(data('X GIVEN Y', '2/3*(X+2Y)', 1, '1/2', 0, 1) + [m('BACK')])
        self.values(r, exp)
        for v in ('5/9', '7/18', '13/162'):
            self.assertIn(v, r.text)

    def test_freund_ex24_slice_interval(self):
        # Freund Ex24 p96: P(X≤1/2 | Y=1/2) for the same density.
        q = sp.Rational(2, 3) * (x + 2 * y)
        _, s, mass, other, *_ = targets(q, 1, y, sp.Rational(1, 2), 0, 1)
        want = sp.integrate(s, (other, 0, sp.Rational(1, 2))) / mass
        self.assertEqual(want, sp.Rational(5, 12))
        r = self.run_slice(data('X GIVEN Y', '2/3*(X+2Y)', 1, '1/2', 0, 1) +
                           [m('INTERVAL PROB'), i(0), i('1/2'), m('BACK')])
        self.values(r, {'O': want})
        self.assertIn('5/12', r.text)

    def test_mock4_q3_triangle_given_x_moving_bound(self):
        # Mock 4 Q3: f=8xy on 0<x<y<1. Given X=1/2, y runs 1/2..1 (bound = X).
        exp, *_ = targets(x * y, 8, x, sp.Rational(1, 2), x, 1)
        self.assertEqual(exp['M'], sp.Rational(3, 2))
        self.assertEqual(exp['E'], sp.Rational(7, 9))
        r = self.run_slice(data('Y GIVEN X', 'X*Y', 8, '1/2', 'X', 1) + [m('BACK')])
        self.values(r, exp)
        self.assertIn('3/2', r.text)
        self.assertIn('7/9', r.text)

    def test_mock4_q3_triangle_conditional_interval(self):
        _, s, mass, other, *_ = targets(x * y, 8, x, sp.Rational(1, 2), x, 1)
        want = sp.integrate(s, (other, sp.Rational(1, 2), sp.Rational(3, 4))) / mass
        self.assertEqual(want, sp.Rational(5, 12))
        r = self.run_slice(data('Y GIVEN X', 'X*Y', 8, '1/2', 'X', 1) +
                           [m('INTERVAL PROB'), i(0), i('3/4'), m('BACK')])
        self.values(r, {'O': want})

    def test_mock4_q3_triangle_given_y_moving_bound(self):
        # Non-homework variant: same model, given Y=3/4, x runs 0..Y.
        exp, *_ = targets(x * y, 8, y, sp.Rational(3, 4), 0, y)
        r = self.run_slice(data('X GIVEN Y', 'X*Y', 8, '3/4', 0, 'Y') + [m('BACK')])
        self.values(r, exp)

    def test_clipped_interval(self):
        _, s, mass, other, *_ = targets(x + y, 1, y, sp.Rational(1, 2), 0, 1)
        r = self.run_slice(data('X GIVEN Y', 'X+Y', 1, '1/2', 0, 1) +
                           [m('INTERVAL PROB'), i(-1), i('1/2'), m('BACK')])
        self.values(r, {'O': sp.integrate(s, (other, 0, sp.Rational(1, 2))) / mass})

    def test_empty_interval(self):
        r = self.run_slice(data('X GIVEN Y', 'X+Y', 1, '1/2', 0, 1) +
                           [m('INTERVAL PROB'), i(2), i(3), m('BACK')])
        self.values(r, {'O': 0})

    def test_pdf_outside_support_zero(self):
        r = self.run_slice(data('X GIVEN Y', 'X+Y', 1, '1/2', 0, 1) + [m('PDF AT POINT'), i(2), m('BACK')])
        self.values(r, {'O': 0, 'P': 0})

    def test_new_given_value_recomputes_marginal(self):
        exp, *_ = targets(x + y, 1, y, sp.Rational(1, 4), 0, 1)
        r = self.run_slice(data('X GIVEN Y', 'X+Y', 1, '1/2', 0, 1) +
                           [m('NEW GIVEN VALUE'), i('1/4'), i(0), i(1), m('BACK')])
        self.values(r, exp)

    def test_zero_marginal_undefined(self):
        r = self.run_slice(data('X GIVEN Y', 'X*Y', 1, 0, 0, 1) + [m('BACK')])
        self.assertIn('CONDITION DENSITY IS ZERO', r.text)

    def test_negative_slice_rejected(self):
        r = self.run_slice(data('X GIVEN Y', '⁻X', 1, '1/2', 0, 1) + [m('BACK')])
        self.assertIn('NEGATIVE SAMPLED DENSITY', r.text)

    def test_invalid_multiplier_reentry(self):
        r = self.run_slice([m('X GIVEN Y'), i('1'), i(0), i('1'), i(1), i(0), i(0), i(1), m('BACK')])
        self.assertIn('KNOWN c MUST BE POSITIVE', r.text)
        exp, *_ = targets(sp.Integer(1), 1, y, 0, 0, 1)
        self.values(r, {'M': exp['M'], 'E': exp['E'], 'H': exp['H']})

    def test_invalid_bounds_reentry(self):
        r = self.run_slice(data('X GIVEN Y', '1', 1, 0, 1, 0) + [i(0), i(0), i(1), m('BACK')])
        self.assertIn('UPPER MUST EXCEED LOWER', r.text)
        exp, *_ = targets(sp.Integer(1), 1, y, 0, 0, 1)
        self.values(r, {'M': exp['M'], 'E': exp['E'], 'H': exp['H']})

    def test_infinite_bound_rejected_then_cutoff(self):
        # P1 fix round 1: f=x e^(-x(1+y)) on the quadrant (Appendix C), given Y=1. Typing ᴇ99 (the
        # HOW TO ENTER infinity) used to crash with ERR:OVERFLOW; it must re-prompt, and a cutoff of 40
        # must then give h(1)=1/4, E(X|Y=1)=1, E(X²|Y=1)=3/2, Var=1/2 (sympy on (0,oo); tail < 1e-30).
        q = x * sp.exp(-x * (1 + y))
        exp, *_ = targets(q, 1, y, 1, 0, sp.oo)
        self.assertEqual((exp['M'], exp['E'], exp['F'], exp['H']),
                         (sp.Rational(1, 4), 1, sp.Rational(3, 2), sp.Rational(1, 2)))
        r = self.run_slice(data('X GIVEN Y', 'X𝑒^(⁻X(1+Y))', 1, 1, 0, 'ᴇ99') +
                           [i(1), i(0), i(40), m('BACK')])
        self.assertIn('FINITE VALUES ONLY', r.text)
        self.assertIn('NO ᴇ99, ABS MUST BE <1ᴇ5', r.text)
        self.values(r, exp, delta=1e-9)
        for v in ('1/4', '3/2', '1/2'):
            self.assertIn(v, r.text)

    def test_huge_given_value_rejected(self):
        r = self.run_slice(data('X GIVEN Y', 'X+Y²', 1, '2ᴇ5', 0, 1) + [i('1/2'), i(0), i(1), m('BACK')])
        self.assertIn('FINITE VALUES ONLY', r.text)
        exp, *_ = targets(x + y ** 2, 1, y, sp.Rational(1, 2), 0, 1)
        self.values(r, exp)

    def test_parent_menu_entry_and_back(self):
        self.run_slice([m('JOINT SLICE'), m('BACK'), m('BACK')], program='M2CONT')

    def test_token_and_static_lints(self):
        p = ROOT / 'src' / 'M2SLICE.txt'
        self.assertEqual(lint_file(str(p)), [])
        self.assertEqual(tibuild.lint_program('M2SLICE', tibuild.clean_source(p.read_text())), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
