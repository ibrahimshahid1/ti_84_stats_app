#!/usr/bin/env python3
"""P2 library tests: M2GL (integration kernel) and M2PLY part 1 (RECOVER2, LINESTR, POLYSTR,
VARCHECK), driven through small in-memory programs (sim.add_program).

Every expected value is computed here with sympy or fractions.Fraction (never from a run of the app).
* EXACT mode: random polynomials of degree ≤4 in each variable over random triangles, cut into
  vertical (or horizontal) strips by an independent Python decomposition: error < 1e-11.
* NUMERIC mode: PLAN 4.6 / Appendix B targets (pass 1 within 5e-9, pass 2 within 4e-10), heavy tails,
  (-INF,U] and (-INF,INF) ranges, the 1-D mode and the g-moments.
"""
from fractions import Fraction as Fr
import math
import random
import unittest

import sympy as sp

from m2test import INIT, SRC
from tisim import Sim

x, y = sp.symbols('x y')
BIG = 10**6


def ti_num(v):
    """Fraction/int/float -> text for a TI list literal (negation key ⁻, ᴇ exponent)."""
    if isinstance(v, float):
        s = repr(abs(v)).replace('e+0', 'ᴇ').replace('e+', 'ᴇ').replace('e-0', 'ᴇ⁻').replace('e-', 'ᴇ⁻')
    else:
        v = Fr(v)
        s = str(abs(v.numerator)) if v.denominator == 1 else f"{abs(v.numerator)}/{v.denominator}"
    return ('⁻' if v < 0 else '') + s


def ti_poly(coef):
    """{(i,j): Fraction} -> a TI expression string in X and Y."""
    out = ''
    for (i, j), c in sorted(coef.items()):
        if c == 0:
            continue
        mag = ti_num(abs(c))
        term = mag + ''.join(f'*{v}^{p}' for v, p in (('X', i), ('Y', j)) if p)
        if not out:
            out = ('⁻' if c < 0 else '') + term
        else:
            out += ('-' if c < 0 else '+') + term
    return out or '0'


def sp_poly(coef):
    return sum(sp.Rational(c.numerator, c.denominator) * x**i * y**j for (i, j), c in coef.items())


def triangle_strips(pts):
    """Vertical strips (x0,x1,l0,l1,u0,u1,0) of a triangle given as 3 Fraction points."""
    pts = sorted(pts)
    (ax, ay), (bx, by), (cx, cy) = pts

    def line(p, q):
        s = (q[1] - p[1]) / (q[0] - p[0])
        return p[1] - s * p[0], s
    strips = []
    long_ = line(pts[0], pts[2])
    for lo, hi, other in ((pts[0], pts[1], line(pts[0], pts[1]) if bx != ax else None),
                          (pts[1], pts[2], line(pts[1], pts[2]) if cx != bx else None)):
        if hi[0] == lo[0]:
            continue
        mid = (lo[0] + hi[0]) / 2
        v_long = long_[0] + long_[1] * mid
        v_other = other[0] + other[1] * mid
        (l0, l1), (u0, u1) = (long_, other) if v_long < v_other else (other, long_)
        strips.append((lo[0], hi[0], l0, l1, u0, u1, 0))
    return strips


def strip_integral(expr, strips, orient=0):
    """sympy integral of expr(x,y) over strips; orient 1 = strips in (y,x) coordinates."""
    tot = 0
    for x0, x1, l0, l1, u0, u1, _ in strips:
        r = [sp.Rational(v.numerator, v.denominator) if isinstance(v, Fr) else v for v in (x0, x1, l0, l1, u0, u1)]
        if orient == 0:
            tot += sp.integrate(expr, (y, r[2] + r[3] * x, r[4] + r[5] * x), (x, r[0], r[1]))
        else:
            tot += sp.integrate(expr, (x, r[2] + r[3] * y, r[4] + r[5] * y), (y, r[0], r[1]))
    return tot


class Kernel(unittest.TestCase):
    sim = Sim(str(SRC))

    def kernel(self, q, strips, orient=0, mode=1, theta=1, g='1', extra=None):
        flat = [ti_num(v) if not isinstance(v, str) else v for st in strips for v in st]
        src = '{' + ','.join(flat) + '}→ʟM2KS\n' + f'{{{orient},{mode}}}→ʟM2KO\n{theta}→θ\nprgmM2GL\n'
        self.sim.add_program('TKDRV', src)
        init = dict(INIT)
        init.update({'Str1': q, 'Str5': g, 'Str2': '0', 'Str3': '0'})
        init.update(extra or {})
        r = self.sim.run('TKDRV', [], max_steps=400_000, init_vars=init)
        self.assertIsNone(r.error, r.error)
        self.assertEqual(r.leaks, 0)
        self.assertFalse(r.warnings, r.warnings)
        for key, value in INIT.items():
            self.assertEqual(r.var(key), value)
        return r

    def test_exact_random_polynomials_on_random_triangles(self):
        rnd = random.Random(431)
        worst = 0
        for case in range(12):
            coef = {(i, j): Fr(rnd.randint(-9, 9), rnd.randint(1, 5))
                    for i in range(5) for j in range(5) if rnd.random() < .35}
            coef[(rnd.randint(0, 4), rnd.randint(0, 4))] = Fr(rnd.randint(1, 9), rnd.randint(1, 4))
            while True:
                pts = [(Fr(rnd.randint(-8, 8), 4), Fr(rnd.randint(-8, 8), 4)) for _ in range(3)]
                xs = sorted(p[0] for p in pts)
                (a, b), (c, d), (e, f) = pts
                if xs[0] < xs[2] and (c - a) * (f - b) - (d - b) * (e - a) != 0:
                    break
            strips = triangle_strips(pts)
            q = sp_poly(coef)
            orient = case % 2
            if orient:      # same triangle, strips written in (y,x) coordinates
                strips = triangle_strips([(p[1], p[0]) for p in pts])
                if not strips:
                    continue
            r = self.kernel(ti_poly(coef), strips, orient=orient)
            R = r.var('ʟM2KR')
            for idx, w in enumerate([1, x, y, x**2, y**2, x * y]):
                exact = strip_integral(w * q, strips, orient)
                err = abs(R[idx] - float(exact))
                worst = max(worst, err / max(1, abs(float(exact))))
                self.assertLess(err, 1e-11 * max(1, abs(float(exact))), (case, idx, R[idx], exact))
            pieces = r.var('ʟM2KP')
            self.assertAlmostEqual(sum(pieces), R[0], delta=1e-11 * max(1, abs(R[0])))
            self.assertEqual(r.var('θ'), 1)
            self.assertLess(r.steps, 3 * len(ti_poly(coef)) + 450 * len(strips) + 100)
        self.assertLess(worst, 1e-11)

    def test_exact_g_moments_and_min_q(self):
        # q = 1+X*Y on the triangle (0,0),(2,0),(2,1): g = X^2*Y-Y^2 (degree 2 per variable).
        strips = [(0, 2, 0, 0, 0, Fr(1, 2), 0)]
        q = 1 + x * y
        g = x**2 * y - y**2
        r = self.kernel('1+X*Y', strips, g='X^2*Y-Y^2')
        R = r.var('ʟM2KR')
        self.assertAlmostEqual(R[6], float(strip_integral(g * q, strips)), delta=1e-11)
        self.assertAlmostEqual(R[7], float(strip_integral(g**2 * q, strips)), delta=1e-11)
        self.assertGreaterEqual(R[8], 1.0)            # min q seen at the nodes
        r = self.kernel('X-1', strips)
        self.assertLess(r.var('ʟM2KR')[8], 0)         # q<0 is reported, not hidden

    def test_numeric_quadrant_targets(self):
        q = '2𝑒^(⁻X-2Y)'
        cases = [  # strips, exact value, pass-1 / pass-2 tolerance (PLAN 4.6, Appendix B)
            ([(0, BIG, 0, 0, BIG, 0, 0)], 1, 5e-9, 4e-10),
            ([(0, BIG, 0, 0, 0, 1, 0)], Fr(2, 3), 5e-9, 4e-10),
            ([(0, BIG, 0, 1, BIG, 0, 0)], Fr(1, 3), 5e-9, 4e-10),
            ([(0, 1, 0, 0, 1, -1, 0)], 1 - 2 * math.exp(-1) + math.exp(-2), 5e-9, 4e-10),
        ]
        for strips, exact, tol1, tol2 in cases:
            for mode, tol in ((2, tol1), (3, tol2)):
                r = self.kernel(q, strips, mode=mode)
                self.assertAlmostEqual(r.var('ʟM2KR')[0], float(exact), delta=tol, msg=(strips, mode))
                self.assertEqual(r.var('θ'), 1)
                self.assertLess(r.steps, 6000)
        # E(XY)=1/2 for the same density (∫∫ x*y*2e^(-x-2y) over the quadrant).
        exy = sp.integrate(x * y * 2 * sp.exp(-x - 2 * y), (x, 0, sp.oo), (y, 0, sp.oo))
        r = self.kernel(q, [(0, BIG, 0, 0, BIG, 0, 0)], mode=3)
        self.assertAlmostEqual(r.var('ʟM2KR')[5], float(exy), delta=1e-9)

    def test_numeric_other_densities(self):
        # x e^(-x(1+y)) on the quadrant, e^(-x) on 0<y<x<INF, 4xy e^(-x^2-y^2): totals 1.
        for q, strips in [('X*𝑒^(⁻X*(1+Y))', [(0, BIG, 0, 0, BIG, 0, 0)]),
                          ('𝑒^(⁻X)', [(0, BIG, 0, 0, 0, 1, 0)]),
                          ('4X*Y*𝑒^(⁻X²-Y²)', [(0, BIG, 0, 0, BIG, 0, 0)])]:
            for mode, tol in ((2, 5e-8), (3, 5e-9)):
                r = self.kernel(q, strips, mode=mode)
                self.assertAlmostEqual(r.var('ʟM2KR')[0], 1, delta=tol, msg=(q, mode))
        # orient 1: e^(-x) on 0<y<x, outer y from 0 to INF, inner x from y to INF; E(Y)=1/2... total 1
        r = self.kernel('𝑒^(⁻X)', [(0, BIG, 0, 1, BIG, 0, 0)], orient=1, mode=3)
        R = r.var('ʟM2KR')
        self.assertAlmostEqual(R[0], 1, delta=5e-9)
        self.assertAlmostEqual(R[2], 1, delta=5e-8)     # E(Y) = ∫ y e^(-y) dy = 1 (Y ~ Exp(1))
        self.assertAlmostEqual(R[1], 2, delta=5e-8)     # E(X) = 2 (X ~ Gamma(2,1))

    def test_numeric_finite_and_curved(self):
        # e^(X+Y) on the unit square, 1/X on 0<y<x<1 (finite, numeric) and q=3 on 0<y<x² (curved).
        r = self.kernel('𝑒^(X+Y)', [(0, 1, 0, 0, 1, 0, 0)], mode=3)
        self.assertAlmostEqual(r.var('ʟM2KR')[0], (math.e - 1)**2, delta=1e-12)
        r = self.kernel('1/X', [(0, 1, 0, 0, 0, 1, 0)], mode=2)
        self.assertAlmostEqual(r.var('ʟM2KR')[0], 1, delta=1e-12)
        r = self.kernel('3', [(0, 1, 0, 0, 0, 0, 1)], mode=3, extra={'Str2': '0', 'Str3': 'X²'})
        self.assertAlmostEqual(r.var('ʟM2KR')[0], 1, delta=1e-12)
        # an inner range that turns negative contributes 0 (clipped curved sub-regions): 1/8, not
        # the signed ∫(x-1/2)dx=0 (a kink at x=1/2, so only numeric accuracy)
        r = self.kernel('1', [(0, 1, 0, 0, 0, 0, 1)], mode=3, extra={'Str2': '1/2', 'Str3': 'X'})
        self.assertAlmostEqual(r.var('ʟM2KR')[0], float(sp.integrate(x - sp.Rational(1, 2), (x, sp.Rational(1, 2), 1))),
                               delta=1e-4)

    def test_one_dimensional_mode(self):
        # 3/4(1-x^2) on (-1,1): exact moments (HW5 Q2 data); X held, integrate in Y.
        r = self.kernel('3/4*(1-X²)', [(-1, 1)], theta=2)
        R = r.var('ʟM2KR')
        f = sp.Rational(3, 4) * (1 - x**2)
        for k in range(5):
            self.assertAlmostEqual(R[k], float(sp.integrate(x**k * f, (x, -1, 1))), delta=1e-12)
        r = self.kernel('X*Y', [(0, 2)], orient=1, theta=2, g='Y²', extra={'X': 3})
        R = r.var('ʟM2KR')
        self.assertAlmostEqual(R[0], 6, delta=1e-12)                     # ∫0^2 3y dy
        self.assertAlmostEqual(R[5], float(sp.integrate(3 * y**3, (y, 0, 2))), delta=1e-11)
        self.assertAlmostEqual(R[6], float(sp.integrate(3 * y**5, (y, 0, 2))), delta=1e-10)
        self.assertEqual(r.var('X'), 3)                                  # the held value is unchanged
        # semi-infinite and doubly infinite ranges
        r = self.kernel('𝑒^(⁻X)', [(0, BIG)], theta=2, mode=3)
        R = r.var('ʟM2KR')
        for k in range(4):
            self.assertAlmostEqual(R[k], math.factorial(k), delta=1e-8 * math.factorial(k))
        r = self.kernel('𝑒^(X)', [(-BIG, 0)], theta=2, mode=3)
        self.assertAlmostEqual(r.var('ʟM2KR')[0], 1, delta=1e-9)
        self.assertAlmostEqual(r.var('ʟM2KR')[1], -1, delta=1e-8)
        normal = '.39894228040143*𝑒^(⁻X²/2)'
        r = self.kernel(normal, [(-BIG, BIG)], theta=2, mode=3)
        self.assertAlmostEqual(r.var('ʟM2KR')[0], 1, delta=1e-8)
        self.assertAlmostEqual(r.var('ʟM2KR')[2], 1, delta=1e-7)

    def test_heavy_tail_flag(self):
        r = self.kernel('1/(1+X)²', [(0, BIG)], theta=2, mode=3)
        self.assertEqual(r.var('θ'), 2)                  # cutoff 4096 reached: TAIL MAY BE HEAVY
        self.assertTrue(.9 < r.var('ʟM2KR')[0] < 1)     # only a rough value: the caller warns
        r = self.kernel('𝑒^(⁻X)', [(0, BIG)], theta=2, mode=3)
        self.assertEqual(r.var('θ'), 1)

    def test_cleanup_mode_deletes_lists(self):
        src = '{0,1}→ʟM2KS\n{0,1}→ʟM2KO\n2→θ\nprgmM2GL\n9→θ\nprgmM2GL\n1→θ\nprgmM2PLY\n9→θ\nprgmM2PLY\n'
        self.sim.add_program('TKCLN', src)
        init = dict(INIT, Str1='X+Y', Str5='1')
        r = self.sim.run('TKCLN', [], init_vars=init)
        self.assertIsNone(r.error)
        self.assertEqual(sorted(n for n in r.vars['lists'] if n.startswith('M2')), [])


class Poly(unittest.TestCase):
    sim = Sim(str(SRC))

    def ply(self, mode, init):
        self.sim.add_program('TPDRV', f'{mode}→θ\nprgmM2PLY\n')
        start = dict(INIT)
        start.update(init)
        r = self.sim.run('TPDRV', [], max_steps=200_000, init_vars=start)
        self.assertIsNone(r.error, r.error)
        self.assertFalse(r.warnings)
        return r

    def test_recover2_random_and_homework_shapes(self):
        rnd = random.Random(2)
        cases = [{(1, 0): Fr(1, 2), (0, 1): Fr(1, 4)},              # (2X+Y)/4
                 {(1, 1): Fr(1)}, {(0, 0): Fr(3)}]
        for _ in range(6):
            cases.append({(i, j): Fr(rnd.randint(-9, 9), rnd.randint(1, 7))
                          for i in range(5) for j in range(5) if rnd.random() < .4})
        for coef in cases:
            r = self.ply(1, {'Str1': ti_poly(coef)})
            self.assertEqual(r.var('θ'), 1, ti_poly(coef))
            A = r.var('ʟM2QA')
            scale = max([1] + [abs(float(c)) for c in coef.values()])
            for i in range(5):
                for j in range(5):
                    self.assertAlmostEqual(A[5 * i + j], float(coef.get((i, j), 0)), delta=1e-9 * scale)
            self.assertLess(r.steps, 300)
        # typed forms the student uses
        for q, coef in [('(2X+Y)/4', {(1, 0): Fr(1, 2), (0, 1): Fr(1, 4)}),
                        ('2/3*(X+2Y)', {(1, 0): Fr(2, 3), (0, 1): Fr(4, 3)}),
                        ('(1+X)^4(2-Y)^3/3', None)]:
            r = self.ply(1, {'Str1': q})
            self.assertEqual(r.var('θ'), 1, q)
            if coef:
                A = r.var('ʟM2QA')
                for (i, j), c in coef.items():
                    self.assertAlmostEqual(A[5 * i + j], float(c), delta=1e-11)
        expect = sp.Poly(sp.expand((1 + x)**4 * (2 - y)**3 / 3), x, y)
        A = self.ply(1, {'Str1': '(1+X)^4(2-Y)^3/3'}).var('ʟM2QA')
        for (i, j), c in expect.terms():
            self.assertAlmostEqual(A[5 * i + j], float(c), delta=1e-9 * 32)

    def test_recover2_rejects_non_polynomials_without_sampling_errors(self):
        for q in ['𝑒^(⁻X-2Y)', '1/X', 'X^5', 'X^(1/2)', '√(X)', '1/(X-Y)', 'X^2.5', 'ln(X+3)', 'abs(X-Y)',
                  'X*Y^10']:
            r = self.ply(1, {'Str1': q})
            self.assertEqual(r.var('θ'), 0, q)

    def test_linestr(self):
        cases = [((0, 1), 'x'), ((1, -1), '1-x'), ((0, Fr(1, 2)), '(1/2)x'), ((2, 0), '2'), ((0, 0), '0'),
                 ((BIG, 0), 'INF'), ((-BIG, 0), '-INF'), ((-1, 2), '-1+2x'),
                 ((Fr(1, 2), Fr(1, 2)), '1/2+(1/2)x'), ((Fr(-1, 3), Fr(-2, 3)), '-1/3-(2/3)x'),
                 ((Fr(1, 3), 1), '1/3+x'), ((1e-15, 1), 'x'), ((-2, -1), '-2-x')]
        for (l0, l1), want in cases:
            r = self.ply(2, {'ʟM2QS': [float(l0), float(l1)], 'Str6': 'x'})
            self.assertEqual(r.var('Str7'), want, (l0, l1))
        self.assertEqual(self.ply(2, {'ʟM2QS': [0.0, -1.0], 'Str6': 'y'}).var('Str7'), '-y')

    def test_polystr(self):
        cases = [([1.5, 0, -1.5], 'y', '3/2-3/2y²'), ([0, 4, 0, -4], 'x', '4x-4x³'), ([0, 0, 0], 'x', '0'),
                 ([1, -1, 1, 0, 2], 'y', '1-y+y²+2y^4'), ([0, 1], 'x', 'x'), ([-1], 'x', '-1'),
                 ([0, 0, 3], 'x', '3x²')]
        for coefs, var, want in cases:
            self.assertEqual(self.ply(3, {'ʟM2QC': coefs, 'Str6': var}).var('Str7'), want, coefs)

    def test_varcheck(self):
        for q, allowed, ok in [('2X+Y', 'XY', 1), ('2X+T', 'XY', 0), ('X²', 'X', 1), ('Y+1', 'X', 0),
                               ('x+Y', 'XY', 0), ('θ+X', 'XY', 0), ('𝑒^(⁻X)', 'X', 1), ('A*X', 'XY', 0)]:
            r = self.ply(8, {'Str1': q, 'Str6': allowed})
            self.assertEqual(r.var('θ'), ok, q)
            self.assertLess(r.steps, 20)


if __name__ == '__main__':
    unittest.main(verbosity=2)
