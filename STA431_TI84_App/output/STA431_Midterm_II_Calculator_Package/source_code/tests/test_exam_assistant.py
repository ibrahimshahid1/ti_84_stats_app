#!/usr/bin/env python3
"""M2EXAM (HELP > FIND MY SOLVER) route tests, including unseen inputs and preset isolation.

Renamed from tests_exam_assistant.py in P1 so build_package's tests/test_*.py glob runs it.
Menus are chosen by item text; the route table is read from the program's own menus.
"""
from fractions import Fraction
import unittest

import sympy as sp

from m2test import ROOT, INIT, m, i, run
from tilint import lint_file
import tibuild

x, y = sp.symbols('x y')
CATEGORIES = ['FINITE PMF/TABLE', 'JOINT PDF', 'ONE-VARIABLE PDF', 'MGF GIVEN', 'MEAN/VAR/COV DATA',
              'PROOF OR FORMULA']


class ExamAssistant(unittest.TestCase):
    def run_assistant(self, actions, z=13):
        r = run('M2EXAM', actions, max_steps=500_000, init={'Z': z})
        for key, value in INIT.items():
            self.assertEqual(r.var(key), value, key)
        self.assertEqual(float(r.var('Z')), 0)
        return r

    def test_all_twenty_seven_guidance_routes_return(self):
        top = run('M2EXAM', [m('BACK')])
        self.assertEqual(top.screens[0]['menu']['items'], CATEGORIES + ['BACK'])
        count = 0
        for category in CATEGORIES:
            menu = run('M2EXAM', [m(category), m('BACK'), m('BACK')])
            topics = [t for t in menu.screens[1]['menu']['items'] if t != 'BACK']
            for target in topics:
                with self.subTest(category=category, target=target):
                    # route page, then the solver's (or encyclopedia's) own menu: BACK, BACK, BACK
                    r = self.run_assistant([m(category), m(target), m('BACK'), m('BACK'), m('BACK')])
                    self.assertTrue(any(s['event'] == 'pause' for s in r.screens))
                    # the route really opened a solver or the encyclopedia (a menu one call deeper)
                    self.assertTrue(any(sc['event'] == 'menu' and len(sc.get('stack', [])) >= 2
                                        for sc in r.screens), r.text[-2000:])
                    count += 1
        self.assertEqual(count, 27)

    def test_changed_finite_model_and_event(self):
        # New support/weights/event, not a homework fixture or preset.
        w = {(a, b): 1 + a * b for a in (0, 2) for b in (1, 3)}
        want = Fraction(sum(v for (a, b), v in w.items() if a + b > 3), sum(w.values()))
        a = [m('FINITE PMF/TABLE'), m('PROBABILITY'), m('FORMULA/GRID'), i('{0,2}'), i('{1,3}'), i('1+X*Y'),
             m('EVENT PROB'), m('P(EVENT)'), i('X+Y>3'), m('BACK'), m('BACK'), m('BACK'), m('BACK')]
        r = self.run_assistant(a, z=1)
        self.assertIn('RAW TOTAL=', r.text)
        self.assertAlmostEqual(float(r.var('W')), float(want), delta=1e-8)
        self.assertNotIn('HW4', r.text)
        self.assertNotIn('HW5', r.text)
        prompts = [s.get('prompt', '') for s in r.screens if s['event'] == 'input']
        self.assertTrue(prompts, 'The general solver must request new data')

    def test_changed_continuous_conditional_slice(self):
        # Uniform triangle 0<Y<X<3 (c=2/9), given X=2: Y|X=2 is uniform(0,2).
        c, a0 = sp.Rational(2, 9), 2
        mass = sp.integrate(1, (y, 0, a0))
        e1 = sp.integrate(y, (y, 0, a0)) / mass
        var = sp.integrate((y - e1) ** 2, (y, 0, a0)) / mass
        # LEAN-B: the GIVEN VALUE route opens JOINT DENSITY > GIVEN A VALUE (exact, c computed)
        a = [m('JOINT PDF'), m('GIVEN VALUE'), m('NEW MODEL'), i('1'), m('TRI a<Y<X<b'), i(0), i(3),
             m('GIVEN A VALUE'), m('GIVEN X=x'), i(a0), m('BACK'), m('BACK'), m('BACK'), m('BACK'), m('BACK')]
        r = self.run_assistant(a)
        self.assertIn('JOINT DENSITY > GIVEN A', r.text)
        self.assertIn('g(2)=' + str(c * mass), r.text)
        self.assertAlmostEqual(float(r.var('A')), float(e1), delta=1e-8)
        self.assertIn('Var(Y|X=2)=' + str(var), r.text)
        self.assertNotIn('HW5', r.text)

    def test_probability_setup_preserves_event_normalization_distinction(self):
        # P2: the route page now opens JOINT DENSITY (c=1/TOTAL, then EVENTS + LIMITS).
        r = self.run_assistant([m('JOINT PDF'), m('NORMALIZE / PROB'), m('BACK'), m('BACK'), m('BACK')])
        self.assertIn('It shows c=1/TOTAL.', r.text)
        self.assertIn('limits, each piece and P.', r.text)
        self.assertTrue(any(s['event'] == 'menu' and s['menu']['title'] == 'JOINT DENSITY' for s in r.screens))

    def test_symbolic_route_explains_numeric_limit(self):
        r = self.run_assistant([m('JOINT PDF'), m('MARGINAL FORMULA'), m('BACK'), m('BACK'), m('BACK')])
        self.assertIn('a marginal formula.', r.text)
        self.assertIn('limits and every piece.', r.text)

    def test_event_conditioning_uses_two_region_integrals(self):
        # New triangle 0<Y<X<3 with q=1. Given X>1, find P(Y<1/2): a ratio of two region integrals,
        # now through JOINT DENSITY > EVENTS + LIMITS > P(A|B) (P2).
        base = sp.integrate(1, (y, 0, x), (x, 1, 3))
        both = sp.integrate(1, (y, 0, sp.Rational(1, 2)), (x, 1, 3))
        a = [m('JOINT PDF'), m('GIVEN INTERVAL'), m('NEW MODEL'), i('1'), m('TRI a<Y<X<b'), i(0), i(3),
             m('EVENTS + LIMITS'), m('P(A|B)'), m('MORE EVENTS'), m('aX+bY≤c'), i(0), i(1), i('1/2'),
             m('MORE EVENTS'), m('a<X<b ONLY'), i(1), i(3), m('BACK'), m('BACK'), m('BACK'), m('BACK')]
        r = self.run_assistant(a, z=17)
        self.assertIn('Given Y>k is an EVENT.', r.text)
        self.assertIn('Its scale cancels.', r.text)
        res = [row.strip() for s in r.screens if s['event'] == 'pause' and s['rows'][0].strip() == 'RESULT'
               for row in s['rows']]
        frac = lambda e: str(sp.nsimplify(e))                                  # noqa: E731
        self.assertIn('P(A AND B)=' + frac(both / sp.Rational(9, 2)), res)     # c = 1/area = 2/9
        self.assertIn('P(B)=' + frac(base / sp.Rational(9, 2)), res)
        self.assertIn('P(A|B)=' + frac(both / base), res)
        self.assertAlmostEqual(float(r.var('A')), float(both / base), delta=1e-9)

    def test_cdf_route_teaches_rectangle_and_density_conversion(self):
        r = self.run_assistant([m('PROOF OR FORMULA'), m('DISTRIBUTION FORM'), m('BACK'), m('BACK'), m('BACK')])
        self.assertIn('+F(b,d)-F(a,d)-F(b,c)', r.text)
        self.assertIn('+F(a,c), for (a,b]x(c,d].', r.text)
        self.assertIn('Differentiate twice for', r.text)

    def test_dependence_wording_is_sta431(self):
        for cat, topic in [('MEAN/VAR/COV DATA', 'ZERO COV PROOF'), ('PROOF OR FORMULA', 'ZERO COV / DEPEND')]:
            r = self.run_assistant([m(cat), m(topic), m('BACK'), m('BACK'), m('BACK')])
            for row in ['To show dependence give', 'one (x,y) with', 'f(x,y)≠g(x)h(y), or show',
                        'the support is not a', 'product set.']:
                self.assertIn(row, r.text)

    def test_preset_flags_do_not_bypass_user_inputs(self):
        for flag in [1, 2, 11, 13, 14, 15, 16, 17, 18]:
            with self.subTest(flag=flag):
                r = self.run_assistant([m('FINITE PMF/TABLE'), m('PROBABILITY'), m('BACK'), m('BACK'), m('BACK')],
                                       z=flag)
                self.assertNotIn('NORMALIZED p=w/SUM(w)', r.text)
                self.assertNotIn('ORIGINAL X MOMENTS', r.text)

    def test_static_and_token_roundtrip(self):
        p = ROOT / 'src/M2EXAM.txt'
        s = tibuild.clean_source(p.read_text())
        self.assertEqual(lint_file(str(p)), [])
        self.assertEqual(tibuild.lint_program('M2EXAM', s), [])
        self.assertTrue(tibuild.tokenize(s))
        self.assertNotIn('prgmM2RUN', s)
        self.assertNotIn('prgmM2HW', s)


if __name__ == '__main__':
    unittest.main(verbosity=2)
