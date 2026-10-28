#!/usr/bin/env python3
"""M2CDF (SOLVERS > CDF OF X AND Y) acceptance tests: R1, R3 and PLAN 0A A3 (LEAN-A build).

Every expected value is computed here with sympy / fractions.Fraction, never copied from an app run.

# PLAN DEVIATIONS / EXTRA FIXES
# * Reduced P4 (budget): no EXP PAIR TEMPLATE item, no M2ONE; M2CONT stays.
# * M2PLY gains mode 4 POLY2STR (planned for P3) for the exact f=d²F/dxdy formula.
# * M2JNT: Z=97 entry (NEW MODEL, then straight to X≤s AND Y≤t) for F FROM A PDF f.
# * After the F FROM A PDF f handoff the F model is cleared (M2JNT reuses Str1/Str2); the next
#   F item asks for F again.
# * Result rows use generic labels: F(x,y)=v for each clipped corner, then P(...)=v; the tail and
#   min/max formulas name FX(a)=F(a,d) and FY(b)=F(top of x,b) with the support ends substituted.
"""
from fractions import Fraction as Fr
import math
import unittest

import sympy as sp

from m2test import m, i, run, num

x, y = sp.symbols('x y')
R = sp.Rational
BACK = m('BACK')


def fs(v):
    v = Fr(v)
    s = str(abs(v.numerator)) if v.denominator == 1 else f"{abs(v.numerator)}/{v.denominator}"
    return ("⁻" if v < 0 else "") + s


def F_(e):
    e = sp.nsimplify(sp.simplify(e))
    return Fr(int(sp.numer(e)), int(sp.denom(e)))


def rows(r, title):
    """Stripped non-empty rows (title excluded) of every pause page titled `title`, in order."""
    out = []
    for s in r.screens:
        if s['event'] == 'pause' and s['rows'][0].strip() == title:
            out.extend(row.strip() for row in s['rows'][1:] if row.strip())
    return out


def new_f(F, a, b, c, d):
    return [m('NEW F(X,Y)'), i(F), i(a), i(b), i(c), i(d)]


def cdf(actions, **kw):
    return run('M2CDF', actions + [BACK], **kw)


def corner(Fs, s, t, a, b, c, d):
    """Clipped CDF value: 0 left of / below the support, else F(min(s,b), min(t,d))."""
    if s <= a or t <= c:
        return sp.Integer(0)
    return sp.simplify(Fs.subs({x: min(s, b), y: min(t, d)}))


class PolyCDF(unittest.TestCase):
    """Polynomial F on a finite box: exact fractions and formula strings."""

    def full(self, Fs, typed, box, rect, tail, t):
        a, b, c, d = box
        r = cdf(new_f(typed, *box)
                + [m('RECTANGLE PROB'), m('a<X≤b,c<Y≤d'), *[i(v) for v in rect],
                   m('X>a AND Y>b'), i(tail[0]), i(tail[1]), m('MIN/MAX ≤ t'), i(t), BACK,
                   m('MARGINAL CDFs'), i(t), i(t), m('PDF f FROM F')])
        G = lambda s, u: corner(Fs, s, u, a, b, c, d)                       # noqa: E731
        chk = rows(r, 'CHECK F')
        self.assertIn('F(a,c)=0 MUST BE 0', chk)
        self.assertIn('F(b,d)=1 MUST BE 1', chk)
        self.assertIn('f≥0 AT 9 TEST POINTS', chk)
        self.assertIn('EXACT (POLYNOMIAL)', chk)
        # rectangle rule
        p1, p2, q1, q2 = rect
        want = F_(G(p2, q2) - G(p1, q2) - G(p2, q1) + G(p1, q1))
        rr = rows(r, 'RECTANGLE RULE')
        self.assertEqual(rr[:3], ['P(a<X≤b,c<Y≤d)', '=F(b,d)-F(a,d)', '-F(b,c)+F(a,c)'])
        self.assertIn(f'F({fs(p2)},{fs(q2)})={fs(F_(G(p2, q2)))}', rr)
        self.assertIn('P=' + fs(want), rr)
        # both exceed
        s0, t0 = tail
        tail_want = F_(1 - G(s0, d) - G(b, t0) + G(s0, t0))
        be = rows(r, 'BOTH EXCEED')
        self.assertEqual(be[0], 'P(X>a,Y>b)=1-FX(a)')
        self.assertIn(f'FX(a)=F(a,{fs(d)})', be)
        self.assertIn(f'FY(b)=F({fs(b)},b)', be)
        self.assertIn('P(X>a,Y>b)=' + fs(tail_want), be)
        # min / max
        mx, mn = F_(G(t, t)), F_(G(t, d) + G(b, t) - G(t, t))
        mm = rows(r, 'MIN/MAX')
        self.assertEqual(mm[0], 'P(max≤t)=F(t,t)')
        for row in ['ONLY IF BOTH = max≤t', 'FAILS IF EITHER FAILS', 'P(max≤t)=' + fs(mx),
                    'P(min≤t)=' + fs(mn)]:
            self.assertIn(row, mm)
        self.assertAlmostEqual(r.var('P'), float(mx), delta=1e-9)
        self.assertAlmostEqual(r.var('M'), float(mn), delta=1e-9)
        # marginals (formula strings) and f = d²F/dxdy
        mg = rows(r, 'MARGINAL CDFs')
        self.assertEqual(mg[0], f'FX(x)=F(x,{fs(d)})')
        pdf = rows(r, 'PDF f FROM F')
        self.assertEqual(pdf[0], 'f=d²F/dxdy')
        return dict(rect=want, tail=tail_want, max=mx, min=mn, marg=mg, pdf=pdf,
                    FX=sp.expand(Fs.subs(y, d)), FY=sp.expand(Fs.subs(x, b)), f=sp.expand(sp.diff(Fs, x, y)))

    def test_r3_variant_unit_square(self):
        Fs = x**2 * y * (x + y) / 2
        res = self.full(Fs, 'X²*Y*(X+Y)/2', (0, 1, 0, 1), (R(1, 4), R(1, 2), R(1, 2), 1),
                        (R(1, 2), R(1, 2)), R(1, 2))
        self.assertEqual(res['rect'], Fr(25, 256))
        self.assertEqual((res['tail'], res['max'], res['min']), (Fr(1, 2), Fr(1, 16), Fr(1, 2)))
        self.assertEqual(sp.expand(res['f'] - x * (3 * x + 4 * y) / 2), 0)
        self.assertEqual(sp.expand(res['FX'] - x**2 * (x + 1) / 2), 0)
        self.assertEqual(sp.expand(res['FY'] - y * (y + 1) / 2), 0)
        self.assertIn('FX(x)=1/2x²+1/2x³', res['marg'])
        self.assertIn('FY(y)=1/2y+1/2y²', res['marg'])
        self.assertIn('f(x,y)=3/2x²+2xy', res['pdf'])

    def test_hw4_q3_device_fails(self):
        Fs = x * y * (x + y) / 16
        self.assertEqual(sp.expand(sp.diff(Fs, x, y) - (x + y) / 8), 0)
        res = self.full(Fs, 'X*Y*(X+Y)/16', (0, 2, 0, 2), (0, 1, 0, 1), (1, 1), 1)
        self.assertEqual(res['rect'], Fr(1, 8))                                 # F(1,1)
        self.assertEqual(F_(res['FX'].subs(x, 1)), Fr(3, 8))
        self.assertEqual((res['tail'], res['min']), (Fr(3, 8), Fr(5, 8)))
        self.assertIn('FX(x)=1/4x+1/8x²', res['marg'])                          # x(x+2)/8
        self.assertIn('F(1,2)=3/8', res['marg'])                                # FX(1)
        self.assertIn('F(2,1)=3/8', res['marg'])                                # FY(1)
        self.assertIn('f(x,y)=1/8x+1/8y', res['pdf'])

    def test_hw4_q5(self):
        Fs = x**2 * y / 4 + x * y**2 / 8
        self.assertEqual(sp.expand(sp.diff(Fs, x, y) - (2 * x + y) / 4), 0)
        res = self.full(Fs, 'X²*Y/4+X*Y²/8', (0, 1, 0, 2), (0, R(1, 2), 0, 1), (R(1, 2), 1), R(1, 2))
        self.assertEqual(res['rect'], Fr(1, 8))                                 # F(1/2,1)
        self.assertEqual(sp.expand(res['FX'] - x * (x + 1) / 2), 0)
        self.assertEqual(sp.expand(res['FY'] - y * (y + 2) / 8), 0)
        self.assertIn('FX(x)=1/2x+1/2x²', res['marg'])
        self.assertIn('FY(y)=1/4y+1/8y²', res['marg'])
        self.assertIn('f(x,y)=1/2x+1/4y', res['pdf'])

    def test_freund_ex16_and_clipping(self):
        # Freund Ex16 F=xy(x+y)/2: f=x+y; P(1/2<X≤1,1/2<Y≤1)=3/8; corners beyond S are clipped
        Fs = x * y * (x + y) / 2
        r = cdf(new_f('X*Y*(X+Y)/2', 0, 1, 0, 1) + [m('RECTANGLE PROB'), m('a<X≤b,c<Y≤d'),
                i('1/2'), i('ᴇ99'), i('1/2'), i(3), BACK, m('PDF f FROM F')])
        want = F_(1 - 2 * Fs.subs({x: R(1, 2), y: 1}) + Fs.subs({x: R(1, 2), y: R(1, 2)}))
        self.assertEqual(want, Fr(3, 8))
        rr = rows(r, 'RECTANGLE RULE')
        self.assertIn('F(INF,3)=1', rr)
        self.assertIn('P=3/8', rr)
        self.assertIn('f(x,y)=x+y', rows(r, 'PDF f FROM F'))


class NumericCDF(unittest.TestCase):
    def test_exponential_pair(self):
        Fs = (1 - sp.exp(-x)) * (1 - sp.exp(-2 * y))
        f = sp.diff(Fs, x, y)
        self.assertEqual(sp.simplify(f - 2 * sp.exp(-x - 2 * y)), 0)
        FX = sp.limit(Fs, y, sp.oo)
        FY = sp.limit(Fs, x, sp.oo)
        F11 = float(Fs.subs({x: 1, y: 1}))
        tail = float(1 - FX.subs(x, 1) - FY.subs(y, 1) + Fs.subs({x: 1, y: 1}))
        pmin = float(FX.subs(x, 1) + FY.subs(y, 1) - Fs.subs({x: 1, y: 1}))
        self.assertAlmostEqual(F11, 0.546572343960, delta=1e-11)
        self.assertAlmostEqual(pmin, 1 - math.exp(-3), delta=1e-12)
        self.assertAlmostEqual(tail, math.exp(-3), delta=1e-12)
        typed = '(1-𝑒^(⁻X))*(1-𝑒^(⁻2Y))'
        base = new_f(typed, 0, 'ᴇ99', 0, 'ᴇ99')
        r = cdf(base + [m('RECTANGLE PROB'), m('a<X≤b,c<Y≤d'), i(0), i(1), i(0), i(1), BACK])
        self.assertIn('NUMERIC (NOT POLYNOMIAL)', rows(r, 'CHECK F'))
        self.assertIn('F(b,d)=1 MUST BE 1', rows(r, 'CHECK F'))
        self.assertAlmostEqual(r.var('M'), F11, delta=1e-9)
        r = cdf(base + [m('RECTANGLE PROB'), m('X>a AND Y>b'), i(1), i(1), BACK])
        self.assertIn('FX(a)=F(a,INF)', rows(r, 'BOTH EXCEED'))
        self.assertAlmostEqual(r.var('M'), tail, delta=1e-9)
        r = cdf(base + [m('RECTANGLE PROB'), m('MIN/MAX ≤ t'), i(1), BACK])
        self.assertAlmostEqual(r.var('M'), pmin, delta=1e-9)
        self.assertAlmostEqual(r.var('P'), F11, delta=1e-9)
        r = cdf(base + [m('MARGINAL CDFs'), i(1), i(1)])
        mg = rows(r, 'MARGINAL CDFs')
        self.assertEqual(mg[:2], ['FX(x)=F(x,INF)', 'FY(y)=F(INF,y)'])
        self.assertAlmostEqual(num(mg[2].split('=')[1]), float(FX.subs(x, 1)), delta=1e-9)
        r = cdf(base + [m('PDF f FROM F'), i(1), i(1)])
        pdf = rows(r, 'PDF f FROM F')
        self.assertEqual(pdf[0], 'f=d²F/dxdy')
        self.assertIn('f=(4D(h/2)-D(h))/3', pdf)
        self.assertAlmostEqual(r.var('M'), float(f.subs({x: 1, y: 1})), delta=1e-6)

    def test_non_homework_numeric_pdf_point(self):
        # F=(1-e^(-3x))(1-e^(-y/2)): f(1/2,2)=3/2 e^(-3/2-1)
        Fs = (1 - sp.exp(-3 * x)) * (1 - sp.exp(-y / 2))
        want = float(sp.diff(Fs, x, y).subs({x: R(1, 2), y: 2}))
        r = cdf(new_f('(1-𝑒^(⁻3X))*(1-𝑒^(⁻Y/2))', 0, 'ᴇ99', 0, 'ᴇ99')
                + [m('PDF f FROM F'), i('1/2'), i(2)])
        self.assertAlmostEqual(r.var('M'), want, delta=1e-6)
        # a point closer than .01 to the edge re-prompts
        r = cdf(new_f('(1-𝑒^(⁻3X))*(1-𝑒^(⁻Y/2))', 0, 'ᴇ99', 0, 'ᴇ99')
                + [m('PDF f FROM F'), i('.005'), i(1), i(1), i(1)])
        self.assertIn('POINT MUST BE .01', r.text)


class FromPdf(unittest.TestCase):
    def handoff(self, q, box, s, t):
        r = cdf([m('F FROM A PDF f'), i(q), m('RECT'), *[i(v) for v in box], i(s), i(t), BACK, BACK])
        self.assertIn('=∫∫ f OVER x≤s,y≤t IN S', rows(r, 'F FROM A PDF f'))
        return r

    def test_hw4_q3_and_q5_through_joint_density(self):
        q3 = (x + y) / 8
        want = F_(sp.integrate(q3, (x, 0, 1), (y, 0, 1)))
        self.assertEqual(want, Fr(1, 8))
        r = self.handoff('(X+Y)/8', (0, 2, 0, 2), 1, 1)
        self.assertIn('P(X≤1,Y≤1)=' + fs(want), rows(r, 'RESULT'))
        self.assertIn('x FROM 0 TO 1', rows(r, 'LIMITS'))
        q5 = (2 * x + y) / 4
        want = F_(sp.integrate(q5, (x, 0, R(1, 2)), (y, 0, 1)))
        self.assertEqual(want, Fr(1, 8))
        self.assertEqual(sp.expand(sp.integrate(q5.subs({x: sp.Symbol('u'), y: sp.Symbol('v')}),
                                                (sp.Symbol('u'), 0, x), (sp.Symbol('v'), 0, y))
                                   - (x**2 * y / 4 + x * y**2 / 8)), 0)
        r = self.handoff('(2X+Y)/4', (0, 1, 0, 2), R(1, 2), 1)
        self.assertIn('P(X≤1/2,Y≤1)=1/8', rows(r, 'RESULT'))

    def test_model_cleared_after_handoff(self):
        r = cdf([m('NEW F(X,Y)'), i('X*Y'), i(0), i(1), i(0), i(1), m('F FROM A PDF f'), i('X+Y'), m('RECT'),
                 i(0), i(1), i(0), i(1), i('1/2'), i('1/2'), BACK, BACK,
                 m('RECTANGLE PROB'), i('X*Y'), i(0), i(1), i(0), i(1), m('a<X≤b,c<Y≤d'),
                 i(0), i('1/2'), i(0), i('1/2'), BACK])
        self.assertIn('P(X≤1/2,Y≤1/2)=' + fs(F_(sp.integrate(x + y, (x, 0, R(1, 2)), (y, 0, R(1, 2))))),
                      rows(r, 'RESULT'))
        self.assertIn('P=1/4', rows(r, 'RECTANGLE RULE'))


class Routes(unittest.TestCase):
    def test_finder_routes_joint_cdf_questions(self):
        r = run('M2EXAM', [m('PROOF OR FORMULA'), m('JOINT CDF GIVEN'), BACK, BACK, BACK], init={'Z': 5})
        self.assertIn('SOLVERS>CDF OF X AND Y', r.text)
        self.assertTrue(any(s['event'] == 'menu' and s['menu']['title'] == 'JOINT CDF'
                            and s['stack'] == ['M2EXAM', 'M2CDF'] for s in r.screens))


class Encyclopedia(unittest.TestCase):
    def test_r4_pages(self):
        import json
        from m2test import ROOT
        doc = json.loads((ROOT / 'content' / 'M2ENC.json').read_text())
        tops = {t['menu']: t for sec in doc['sections'] for t in sec['topics']}
        cdf = [' '.join(p) for p in tops['JOINT CDF F']['pages']]
        lim = [' '.join(p) for p in tops['SKETCH + LIMITS']['pages']]
        self.assertIn('f=d²F/dxdy', cdf[1])
        self.assertIn('F FROM f', cdf[0])
        self.assertIn('F(b,d)-F(a,d)-F(b,c) +F(a,c)', cdf[2])
        for page in cdf + lim[:3]:
            self.assertRegex(page, r'Freund|Guide')
            self.assertRegex(page, r'TOOL SOLV>(CDF|JOINT DENSITY)')
        self.assertIn('Split', lim[1])
        self.assertIn("1-P(A')", lim[2])
        # the worked examples are textbook ones: Ex16 rectangle and Guide Ex4.3 P(X+Y<1)
        F = x * y * (x + y) / 2
        self.assertEqual(F_(F.subs({x: 1, y: 1}) - 2 * F.subs({x: R(1, 2), y: 1}) + F.subs({x: R(1, 2), y: R(1, 2)})),
                         Fr(3, 8))
        self.assertEqual(sp.integrate(6 * x, (y, x, 1 - x), (x, 0, R(1, 2))), R(1, 4))
        self.assertIn('3/8', cdf[2])
        self.assertIn('1/4', lim[1])


class Guards(unittest.TestCase):
    def test_rejections_and_preload(self):
        r = cdf([m('NEW F(X,Y)'), i('X*T'), i('X*Y'), i(1), i(0), i(0), i(1), i(0), i(1), i(0), i(1),
                 m('MARGINAL CDFs'), i('1/2'), i('1/2')])
        self.assertIn('F MAY USE ONLY X AND Y', r.text)
        self.assertIn('UPPER BELOW LOWER', r.text)
        self.assertIn('FX(x)=x', rows(r, 'MARGINAL CDFs'))
        r = cdf([m('NEW F(X,Y)'), i('X+Y'), i(0), i(1), i(0), i(1)])          # not a CDF
        self.assertIn('CHECK F AND ITS SUPPORT', rows(r, 'CHECK F'))
        r = cdf([m('NEW F(X,Y)'), i('X*Y'), i(0), i(200000), i(0), i(1), i(0), i(1), i(0), i(1)])
        self.assertIn('ABS(BOUND)<1ᴇ5', r.text)
        # Z=99 preload: Str1 and ʟM2FM, no prompts
        r = run('M2CDF', [m('PDF f FROM F'), BACK], init={'Z': 99, 'Str1': 'X*Y*(X+Y)/2', 'ʟM2FM': [0, 1, 0, 1]})
        self.assertIn('f(x,y)=x+y', rows(r, 'PDF f FROM F'))
        self.assertEqual(r.var('Z'), 0)

    def test_steps(self):
        r = cdf(new_f('X²*Y*(X+Y)/2', 0, 1, 0, 1) + [m('RECTANGLE PROB'), m('a<X≤b,c<Y≤d'),
                i('1/4'), i('1/2'), i('1/2'), i(1), BACK])
        self.assertLess(r.steps, 6000)


if __name__ == '__main__':
    unittest.main(verbosity=1)
