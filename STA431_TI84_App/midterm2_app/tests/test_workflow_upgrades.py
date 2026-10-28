#!/usr/bin/env python3
"""End-user workflow checks: full marginal tables, a usable dependence witness, quick loading,
and launcher round trips through the P1 main menu (chosen by item text, never by position)."""
from fractions import Fraction
import unittest

from m2test import m, i, run, screen, num


def grid(xs, ys, q):
    return [m('FORMULA/GRID'), i(xs), i(ys), i(q)]


def hw4q1():
    w = {(a, b): Fraction(a + b * b) for a in (1, 2) for b in (1, 2, 3)}
    tot = sum(w.values())
    return {k: v / tot for k, v in w.items()}


def fs(v):
    v = Fraction(v)
    s = str(abs(v.numerator)) if v.denominator == 1 else f"{abs(v.numerator)}/{v.denominator}"
    return ("⁻" if v < 0 else "") + s


HW5Q6_COV = [[4, 1, -1], [1, 9, 0], [-1, 0, 2]]
HW5Q6_A = [3, -2, 1]
HW5Q6_VAR = sum(HW5Q6_A[r] * HW5Q6_A[c] * HW5Q6_COV[r][c] for r in range(3) for c in range(3))


class Workflows(unittest.TestCase):
    def test_hw4_q1_full_marginal_tables(self):
        p = hw4q1()
        r = run('M2DISC', grid('{1,2}', '{1,2,3}', 'X+Y²') +
                [m('MARG/CONDITIONAL'), m('MARGINAL TABLES'), m('BACK'), m('BACK')])
        xs = '\n'.join(screen(r, 'X MARGINAL TABLE'))
        ys = '\n'.join(screen(r, 'Y MARGINAL TABLE'))
        for a in (1, 2):
            self.assertIn(f"{a} | {fs(sum(v for (u, _), v in p.items() if u == a))}", xs)
        for b in (1, 2, 3):
            self.assertIn(f"{b} | {fs(sum(v for (_, w), v in p.items() if w == b))}", ys)

    def test_marginals_aggregate_unsorted_repeated_coordinates(self):
        rows = [(2, 2, 4), (1, 1, 1), (2, 1, 2), (1, 2, 3)]
        actions = [m('JOINT X,Y'), i(4)]
        for row in rows:
            actions.extend(i(v) for v in row)
        r = run('M2DISC', actions + [m('MARG/CONDITIONAL'), m('MARGINAL TABLES'), m('BACK'), m('BACK')])
        tot = sum(Fraction(w) for *_, w in rows)
        gx = {a: sum(Fraction(w) for u, _, w in rows if u == a) / tot for a in (1, 2)}
        hy = {b: sum(Fraction(w) for _, v, w in rows if v == b) / tot for b in (1, 2)}
        xs, ys = screen(r, 'X MARGINAL TABLE'), screen(r, 'Y MARGINAL TABLE')
        for a, v in gx.items():
            self.assertEqual(sum(f"{a} | {fs(v)}" in s for s in xs), 1)
        for b, v in hy.items():
            self.assertEqual(sum(f"{b} | {fs(v)}" in s for s in ys), 1)

    def test_univariate_grid_suppresses_dummy_y_pages(self):
        w = {a: Fraction(a * a + a) for a in (1, 2, 3, 4)}
        tot = sum(w.values())
        mean = sum(a * v for a, v in w.items()) / tot
        var = sum(a * a * v for a, v in w.items()) / tot - mean ** 2
        r = run('M2DISC', grid('{1,2,3,4}', '{0}', 'X²+X') +
                [m('MOMENTS'), m('MARG/CONDITIONAL'), m('MARGINAL TABLES'), m('BACK'), m('BACK')])
        self.assertIn(fs(mean), r.text)
        self.assertIn(fs(var), r.text)
        self.assertNotIn('Y MOMENTS', r.text)
        self.assertNotIn('Y MARGINAL TABLE', r.text)
        self.assertNotIn('E[XY]', r.text)

    def test_dependence_witness_is_a_valid_exact_counterexample(self):
        r = run('M2DISC', grid('{1,2}', '{1,2,3}', 'X+Y²') +
                [m('MARG/CONDITIONAL'), m('INDEPENDENCE'), m('BACK'), m('BACK')])
        rows = screen(r, 'COUNTEREXAMPLE PAIR')
        a, b = num(rows[1]), num(rows[2])
        joint, product = num(rows[4]), num(rows[6])
        p = hw4q1()
        gx = sum(v for (u, _), v in p.items() if u == a)
        hy = sum(v for (_, w), v in p.items() if w == b)
        self.assertAlmostEqual(joint, float(p[(int(a), int(b))]), delta=1e-9)
        self.assertAlmostEqual(product, float(gx * hy), delta=1e-9)
        self.assertGreater(abs(joint - product), 1e-6)
        self.assertIn('NUMERIC FACTORIZATION FAIL', r.text)

    def test_independence_match_has_no_false_witness(self):
        r = run('M2DISC', grid('{0,1}', '{0,1}', '1') +
                [m('MARG/CONDITIONAL'), m('INDEPENDENCE'), m('BACK'), m('BACK')])
        self.assertIn('NUMERIC MATCH TO 1E-9', r.text)
        self.assertNotIn('COUNTEREXAMPLE PAIR', r.text)

    def test_main_launcher_quicksolve_and_return(self):
        r = run('STAM2', [m('HOMEWORK PRACTICE'), m('LOAD PRACTICE DATA'), m('HW5 Q5 TO Q8'),
                          m('Q6 THREE VARIABLES'), m('BACK'), m('BACK'), m('BACK'), m('BACK'), m('QUIT')])
        rows = screen(r, 'COMBINATION U')
        self.assertEqual(num(rows[rows.index('VAR(U)') + 1]), HW5Q6_VAR)
        self.assertFalse(any(s['event'] == 'input' for s in r.screens),
                         'quick load requested redundant numeric input')
        self.assertIn('PRACTICE EXAMPLES ONLY', r.text)
        end = r.screens[-1]
        self.assertEqual(end['event'], 'end')
        self.assertTrue(all(not row.strip() for row in end['rows']), end['rows'])   # no "Done"

    def test_quicksolve_removes_eleven_manual_covariance_inputs(self):
        typed = [3, 4, 9, 2, 1, -1, 0] + HW5Q6_A + [0]
        manual = run('M2COV', [m('ONE COMBINATION'), m('VAR/COV ONLY')] + [i(v) for v in typed] + [m('BACK')])
        quick = run('M2RUN', [m('HW5 Q5 TO Q8'), m('Q6 THREE VARIABLES'), m('BACK'), m('BACK'), m('BACK')])
        self.assertEqual(sum(s['event'] == 'input' for s in manual.screens), 11)
        self.assertEqual(sum(s['event'] == 'input' for s in quick.screens), 0)
        for r in (manual, quick):
            rows = screen(r, 'COMBINATION U')
            self.assertEqual(num(rows[rows.index('VAR(U)') + 1]), HW5Q6_VAR)

    def test_main_launcher_joint_slice_and_return(self):
        # HW5 Q7 data: f=x+y on the unit square, given Y=1/2 -> f(x|1/2)=x+1/2.
        e1 = Fraction(1, 3) + Fraction(1, 4)                 # integral of x(x+1/2) over 0..1
        e2 = Fraction(1, 4) + Fraction(1, 6)                 # integral of x²(x+1/2)
        actions = [m('SOLVERS'), m('DENSITY+INTEGRAL'), m('JOINT SLICE'), m('X GIVEN Y')]
        actions += [i(v) for v in ['X+Y', 1, '1/2', 0, 1]]
        actions += [m('BACK'), m('BACK'), m('BACK'), m('QUIT')]
        r = run('STAM2', actions)
        rows = screen(r, 'NUMERIC JOINT SLICE')
        self.assertAlmostEqual(num(rows[rows.index('CONDITIONAL MEAN') + 1]), float(e1), delta=1e-9)
        self.assertAlmostEqual(num(rows[rows.index('CONDITIONAL VARIANCE') + 1]), float(e2 - e1 * e1), delta=1e-9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
