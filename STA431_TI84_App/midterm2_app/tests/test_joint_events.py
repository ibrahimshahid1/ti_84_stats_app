#!/usr/bin/env python3
# PLAN DEVIATIONS / EXTRA FIXES (P2; also in PROGRESS.md "## P2")
# * Pieces read "x FROM a TO b" / " y FROM l TO u" / " PIECE=v" (the plan wrote "x: a TO b"): a colon
#   ends a TI string (tibuild lint WARN). Messages with a colon are split or use " - ":
#   "BOUNDS MUST BE LINEAR"/"USE CURVED OR SPLIT", "UPPER BELOW LOWER"/"SPLIT THE REGION",
#   "COMING IN THIS VERSION"/"USE EVENTS + LIMITS", "P(B)=0 - UNDEFINED", "q<0 SOMEWHERE"/"NOT A VALID PDF".
# * A1: the complement is written A' (Freund's notation; the CE font has no ᶜ). The menu item is
#   "COMPLEMENT OF…" (the … token: tivars turns "..." into it). The |X-Y| submenu item ">k" reads
#   "|X-Y| >k" ("|>" would tokenize as ►). The curved event item is "CURVED SUB-REGION" (the plan's
#   "THIS REGION (CURVED)" has 20 characters; the menu limit is 18).
# * Geometry: the support (any code) and every event are half-planes; RG takes the vertical strips
#   between consecutive breakpoints (crossings of two edge lines), keeps those with upper>lower at the
#   midpoint and merges neighbours with identical lines. This gives the same strips as clipping the
#   support polygon (Sutherland-Hodgman, Appendix A.5) without storing polygons, in less memory.
#   Strips that lie wholly beyond |x|≥5ᴇ5 are dropped (they sit "at infinity").
# * M2GL: |v|≥5ᴇ5 means infinite (records still store ±1ᴇ6), so derived values such as 1ᴇ6-k stay
#   infinite. EXACT uses GL7×GL7 (plan GL7×GL5; exact to degree 13 in both directions). q and g are
#   rewritten with node-list names (Str6, Str7) and evaluated with one expr( per node set, so M2GL
#   clobbers Str6 (and Str7 when Str5≠"1"), never Str0. The outer-cutoff probe uses interior inner
#   points L+(U-L)·{1/64,1/2,63/64} (or L+{1/64,1,2}) so q is never evaluated on an edge (1/Y at
#   Y=0); an all-zero probe gives a zero-length segment instead of the 4096 heavy-tail cutoff. An
#   inner range that turns negative (clipped curved region) contributes 0.
# * M2GL and M2PLY have a cleanup mode θ=9 (DelVar of their own lists); M2JNT's BACK calls both.
# * M2PLY RECOVER2 screens Str1 with a token whitelist (digits X Y + - * / ( ) ² ³ ^ . ⁻ ᴇ, one-digit
#   exponents, no "/("): function tokens such as 𝑒^( or ln( cannot be written inside a TI string
#   literal (tibuild tokenizes them as letters), so the plan's inString pre-screen is impossible. The
#   same reason makes the curved-event clip use comparisons instead of max( and min(.
# * Custom linear bounds are sampled at X (or Y) = .37, 1.37, 2.37 (plan: 0 and 1, checked at -1 and 2)
#   so a mistyped bound such as 1/X is not evaluated at 0.
# * Summary support text is the outer range then the inner range for every code ("0<x<1" / "0<y<x";
#   the quadrant shows "0<x<INF" / "0<y<INF"). "TOTAL ∫∫q=" and its value share one row.
# * SETUP, LIMITS and RESULT are one paged text shown after the integral (COMPUTING… first); for
#   P(A|B) the SETUP of A is shown when A is picked. The first LIMITS page holds the A2 header and one
#   piece, later pages three pieces; a piece is never split across pages.
# * The curved support needs finite a and b. HW4 Q4 (discrete) complements are checked through M2DISC
#   typed events (X≤Y, X+Y>3); the M2DISC EVENT MENU complement display is P6 (A1).
# * Extra fixes: STAM2 HOW TO ENTER row "(JOINT DENSITY ONLY)" under the ᴇ99 row and LIMITS row
#   "DENSITY+INTEGRAL FINITE"; write_content.py tool routes (CHOOSE A SOLVER, HW4 Q2/Q3/Q5) name JOINT
#   DENSITY; M2EXAM B1/B5/B6 route texts rewritten for M2JNT; test_exam_assistant's event-conditioning
#   case now runs M2JNT P(A|B); test_menu_tree CANNED inputs for M2JNT.
"""P2 acceptance tests for SOLVERS > JOINT DENSITY (M2JNT): NEW MODEL, EVENTS + LIMITS, the
amendment items A1 (complements) and A2 (the written integral), and the step budgets.

Every target is computed here with sympy or fractions.Fraction (PLAN Appendix C lists them), never
copied from a run of the app. Screens are read through their titles (EVENT SETUP, LIMITS, RESULT,
COMPLEMENT, MODEL f=c*q); a title can span several pages, so `rows()` joins them.
"""
from fractions import Fraction as Fr
import math
import random
import unittest

import sympy as sp

from m2test import INIT, SRC, m, i, run, num
from tisim import Sim

x, y = sp.symbols('x y')
R = sp.Rational
BACK = m('BACK')


def fs(v):
    v = Fr(v)
    s = str(abs(v.numerator)) if v.denominator == 1 else f"{abs(v.numerator)}/{v.denominator}"
    return ("⁻" if v < 0 else "") + s


def F(e):
    e = sp.nsimplify(e)
    return Fr(int(sp.numer(e)), int(sp.denom(e)))


def rows(r, title):
    """Stripped rows (title row excluded) of every pause page whose first row is `title`, in order."""
    out = []
    for s in r.screens:
        if s['event'] == 'pause' and s['rows'][0].strip() == title:
            out.extend(row.strip() for row in s['rows'][1:] if row.strip())
    return out


def blocks(r, title):
    """Like rows() but one list per separate run of pages (one per integral / result)."""
    out, cur, prev = [], None, None
    for s in r.screens:
        if s['event'] != 'pause':
            continue
        t = s['rows'][0].strip()
        if t == title:
            body = [row.strip() for row in s['rows'][1:] if row.strip()]
            if prev == title and cur is not None and body and body[0] not in ('P=∫∫ c*q(x,y) dy dx',
                                                                              'P=∫∫ c*q(x,y) dx dy'):
                cur.extend(body)
            else:
                cur = body
                out.append(cur)
        prev = t
    return out


def model(q, support, values=()):
    return [m('NEW MODEL'), i(q), *[m(s) for s in support], *[i(v) for v in values]]


RECT = (['RECT'], )


def rect(q, a, b, c, d):
    return model(q, ['RECT'], [a, b, c, d])


def joint(actions, **kw):
    kw.setdefault('max_steps', 3_000_000)
    return run('M2JNT', actions + [BACK, BACK], **kw)


def ev(*path):
    return [m('EVENTS + LIMITS')] + [m(p) if isinstance(p, str) else p for p in path]


def poly_prob(q, region_strips, c=1):
    """c * ∫∫ q over strips given as (x0, x1, lower(x), upper(x)) sympy expressions."""
    return c * sum(sp.integrate(q, (y, lo, hi), (x, a, b)) for a, b, lo, hi in region_strips)


class Regions(unittest.TestCase):
    """R3: the homework problems that use regions (STA 431 problems only)."""

    def test_hw4_q3_device_fails_in_first_hour(self):
        q = (x + y) / 8
        surv = F(sp.integrate(q, (x, 1, 2), (y, 1, 2)))
        fail = 1 - surv
        self.assertEqual(fail, Fr(5, 8))
        r = joint(rect('(X+Y)/8', 0, 2, 0, 2) + ev('MIN/MAX', 'min(X,Y)≤t', i(1)))
        setup = rows(r, 'EVENT SETUP')
        self.assertIn('FAILS IF EITHER FAILS', setup)
        self.assertIn('=> min(X,Y)≤1', setup)
        self.assertIn('=1-P(X>t,Y>t)', setup)
        res = rows(r, 'RESULT')
        self.assertEqual(res[:4], ['P(min(X,Y)≤1)', '=1-P(X>1,Y>1)', '=1-' + fs(surv), '=' + fs(fail)])
        lim = rows(r, 'LIMITS')
        self.assertIn('x FROM 1 TO 2', lim)
        self.assertIn('y FROM 1 TO 2', lim)
        self.assertIn('PIECE=' + fs(surv), lim)
        self.assertAlmostEqual(r.var('A'), float(fail), delta=1e-9)

    def test_hw4_q5_x_less_y_both_orders(self):
        q = (2 * x + y) / 4
        target = F(sp.integrate(q, (y, x, 2), (x, 0, 1)))
        first = F(sp.integrate(q, (x, 0, y), (y, 0, 1)))
        second = F(sp.integrate(q, (x, 0, 1), (y, 1, 2)))
        self.assertEqual(first + second, target)
        r = joint(rect('(2X+Y)/4', 0, 1, 0, 2) + ev('X<Y OR X>Y', 'X<Y', m('REVERSE ORDER')))
        lim = blocks(r, 'LIMITS')
        self.assertEqual(len(lim), 2)
        dydx, dxdy = lim
        self.assertIn('ORDER dy dx (x OUTER)', dydx)
        i0 = dydx.index('x FROM 0 TO 1')
        self.assertEqual(dydx[i0:i0 + 3], ['x FROM 0 TO 1', 'y FROM x TO 2', 'PIECE=' + fs(target)])
        self.assertIn('ORDER dx dy (y OUTER)', dxdy)
        i1 = dxdy.index('y FROM 0 TO 1')
        self.assertEqual(dxdy[i1:i1 + 6], ['y FROM 0 TO 1', 'x FROM 0 TO y', 'PIECE=' + fs(first),
                                           'y FROM 1 TO 2', 'x FROM 0 TO 1', 'PIECE=' + fs(second)])
        results = blocks(r, 'RESULT')
        self.assertEqual(len(results), 2)
        for res in results:
            self.assertEqual(res[0], 'P(X<Y)=' + fs(target))
            self.assertIn('EXACT (POLYNOMIAL)', res)
        self.assertAlmostEqual(r.var('A'), float(target), delta=1e-9)

    def test_hw4_q2_normalizing_constant(self):
        total = F(sp.integrate(2 * x + y, (y, 0, 2), (x, 0, 1)))
        r = joint(rect('2X+Y', 0, 1, 0, 2))
        summary = rows(r, 'MODEL f=c*q')
        self.assertIn('q=2X+Y', summary)
        self.assertIn('0<x<1', summary)
        self.assertIn('0<y<2', summary)
        self.assertIn('TOTAL ∫∫q=' + fs(total), summary)
        self.assertIn('c=' + fs(1 / total), summary)
        self.assertEqual(1 / total, Fr(1, 4))
        self.assertIn('EXACT (POLYNOMIAL)', summary)
        self.assertAlmostEqual(r.var('M'), 1 / float(total), delta=1e-12)

    def test_hw4_q4_discrete_events_and_complements(self):
        # HW4 Q4 is discrete: M2DISC typed events (A1: the complements are 1-P(A)).
        p = {(a, b): Fr(a + b, 32) for a in (1, 2) for b in (1, 2, 3, 4)}
        gt = sum(v for (a, b), v in p.items() if a > b)
        le3 = sum(v for (a, b), v in p.items() if a + b <= 3)
        self.assertEqual((gt, le3), (Fr(3, 32), Fr(1, 4)))
        acts = [m('FORMULA/GRID'), i('{1,2}'), i('{1,2,3,4}'), i('X+Y'), m('EVENT PROB')]
        for event, want in [('X>Y', gt), ('X+Y≤3', le3), ('X≤Y', 1 - gt), ('X+Y>3', 1 - le3)]:
            r = run('M2DISC', acts + [m('P(EVENT)'), i(event), BACK, BACK, BACK])
            self.assertIn('P(EVENT | GIVEN)=', r.text)
            self.assertAlmostEqual(float(r.var('W')), float(want), delta=1e-12)
            self.assertIn(fs(want), r.text)
        self.assertEqual((1 - gt, 1 - le3), (Fr(29, 32), Fr(3, 4)))


class ExactVariants(unittest.TestCase):
    """Non-homework EXACT checks (fraction on screen and r.var within 1e-9)."""

    def check(self, r, label, value):
        res = rows(r, 'RESULT')
        self.assertTrue(any(row.endswith(fs(value)) for row in res), (label, value, res))
        self.assertAlmostEqual(r.var('A'), float(value), delta=1e-9)

    def test_mock2_q2_triangle_sum_event_both_orders(self):
        c = 1 / F(sp.integrate(x, (y, 0, x), (x, 0, 1)))
        p1 = F(c * sp.integrate(x, (y, 0, x), (x, 0, R(1, 2))))
        p2 = F(c * sp.integrate(x, (y, 0, 1 - x), (x, R(1, 2), 1)))
        rev = F(c * sp.integrate(x, (x, y, 1 - y), (y, 0, R(1, 2))))
        self.assertEqual((c, p1 + p2, rev), (3, Fr(3, 8), Fr(3, 8)))
        r = joint(model('X', ['TRI a<Y<X<b'], [0, 1]) + ev('X+Y≤k OR X+Y≥k', 'X+Y≤k', i(1), m('REVERSE ORDER')))
        self.assertIn('c=3', rows(r, 'MODEL f=c*q'))
        dydx, dxdy = blocks(r, 'LIMITS')
        for blk, order in ((dydx, 'dy dx (x OUTER)'), (dxdy, 'dx dy (y OUTER)')):     # A2
            self.assertEqual(blk[:4], ['P=∫∫ c*q(x,y) ' + order[:5], 'c=3', 'q=X', 'ORDER ' + order])
        k = dydx.index('x FROM 0 TO 1/2')
        self.assertEqual(dydx[k:k + 6], ['x FROM 0 TO 1/2', 'y FROM 0 TO x', 'PIECE=' + fs(p1),
                                         'x FROM 1/2 TO 1', 'y FROM 0 TO 1-x', 'PIECE=' + fs(p2)])
        k = dxdy.index('y FROM 0 TO 1/2')
        self.assertEqual(dxdy[k:k + 3], ['y FROM 0 TO 1/2', 'x FROM y TO 1-y', 'PIECE=' + fs(rev)])
        self.assertNotIn('y FROM 1/2 TO 1', dxdy)                  # one piece only
        self.assertEqual(rows(r, 'EVENT SETUP')[:3], ['TOTAL AT MOST 1', '=> X+Y≤1', 'y≤1-x'])
        self.check(r, 'X+Y≤1', Fr(3, 8))

    def test_mock4_q3_triangle(self):
        c = 1 / F(sp.integrate(x * y, (y, x, 1), (x, 0, 1)))
        p = F(c * sp.integrate(x * y, (y, x, 1 - x), (x, 0, R(1, 2))))
        self.assertEqual((c, p), (8, Fr(1, 6)))
        r = joint(model('X*Y', ['TRI a<X<Y<b'], [0, 1]) + ev('X+Y≤k OR X+Y≥k', 'X+Y≤k', i(1)))
        self.assertIn('c=8', rows(r, 'MODEL f=c*q'))
        self.assertIn('x<y<1', rows(r, 'MODEL f=c*q'))
        self.check(r, 'X+Y≤1', p)

    def test_mock4_q4_rectangle_events(self):
        q = x + 2 * y
        c = 1 / F(sp.integrate(q, (y, 0, 1), (x, 0, 2)))
        p_lt = F(c * sp.integrate(q, (y, x, 1), (x, 0, 1)))
        p_sum = F(c * sp.integrate(q, (y, 0, 1 - x), (x, 0, 1)))
        self.assertEqual((c, p_lt, p_sum), (Fr(1, 4), Fr(5, 24), Fr(1, 8)))
        base = rect('X+2Y', 0, 2, 0, 1)
        r = joint(base + ev('X<Y OR X>Y', 'X<Y'))
        self.assertIn('c=1/4', rows(r, 'MODEL f=c*q'))
        self.check(r, 'X<Y', p_lt)
        r = joint(base + ev('X+Y≤k OR X+Y≥k', 'X+Y≤k', i(1)))
        self.check(r, 'X+Y≤1', p_sum)

    def test_mock4_q5_series_and_parallel(self):
        q = R(2, 3) * (x + 2 * y)
        both_work = F(sp.integrate(q, (x, R(1, 2), 1), (y, R(1, 2), 1)))
        p_min = 1 - both_work
        p_max = F(sp.integrate(q, (x, 0, R(1, 2)), (y, 0, R(1, 2))))
        self.assertEqual((p_min, p_max), (Fr(5, 8), Fr(1, 8)))
        base = rect('2/3*(X+2Y)', 0, 1, 0, 1)
        r = joint(base + ev('MIN/MAX', 'min(X,Y)≤t', i('1/2')))
        self.check(r, 'min', p_min)
        r = joint(base + ev('MIN/MAX', 'max(X,Y)≤t', i('1/2')))
        self.assertIn('=P(X≤t,Y≤t)=F(t,t)', rows(r, 'EVENT SETUP'))
        self.assertIn('FAILS ONLY IF BOTH FAIL', rows(r, 'EVENT SETUP'))
        self.check(r, 'max', p_max)
        r = joint(base + ev('MIN/MAX', 'max(X,Y)>t', i('1/2')))
        self.assertIn('=1-F(t,t)', rows(r, 'EVENT SETUP'))
        self.check(r, 'max>', 1 - p_max)
        r = joint(base + ev('MIN/MAX', 'min(X,Y)>t', i('1/2')))
        self.assertIn('BOTH STILL WORK AT t', rows(r, 'EVENT SETUP'))
        self.check(r, 'min>', both_work)

    def test_meeting_problem(self):
        p = 1 - 2 * F(sp.integrate(1, (y, x + R(1, 4), 1), (x, 0, R(3, 4))))
        self.assertEqual(p, Fr(7, 16))
        r = joint(rect('1', 0, 1, 0, 1) + ev('MORE EVENTS', '|X-Y|≤k OR >k', '|X-Y|≤k', i('1/4')))
        setup = rows(r, 'EVENT SETUP')
        self.assertIn('MEET WITHIN 1/4', setup)
        self.assertIn('x-1/4<y<x+1/4', setup)
        self.check(r, 'meet', p)
        r = joint(rect('1', 0, 1, 0, 1) + ev('MORE EVENTS', '|X-Y|≤k OR >k', '|X-Y| >k', i('1/4')))
        self.assertIn('=1-P(|X-Y|≤1/4)', rows(r, 'EVENT SETUP'))
        self.check(r, 'miss', 1 - p)

    def test_conditional_event(self):
        c = 8
        both = F(c * sp.integrate(x * y, (x, 0, R(1, 2)), (y, R(1, 2), 1)))
        pb = F(c * sp.integrate(x * y, (x, 0, y), (y, R(1, 2), 1)))
        self.assertEqual((both, pb, both / pb), (Fr(3, 8), Fr(15, 16), Fr(2, 5)))
        acts = model('X*Y', ['TRI a<X<Y<b'], [0, 1]) + ev(
            'P(A|B)', 'MORE EVENTS', 'a<X<b ONLY', i(0), i('1/2'),
            'MORE EVENTS', 'aX+bY≤c', i(0), i(-1), i(Fr(-1, 2)), m('COMPLEMENT 1-P'))
        r = joint(acts)
        self.assertIn('GIVEN AN EVENT B', rows(r, 'P(A|B) SETUP'))
        self.assertIn('B IS AN EVENT, NOT X=x', rows(r, 'P(A|B) SETUP'))
        self.assertTrue(rows(r, 'EVENT A SETUP') and rows(r, 'EVENT B SETUP'))
        res = rows(r, 'RESULT')
        self.assertIn('P(A|B)=P(A AND B)/P(B)', res)
        self.assertIn('P(A AND B)=' + fs(both), res)
        self.assertIn('P(B)=' + fs(pb), res)
        self.assertIn('P(A|B)=' + fs(both / pb), res)
        self.assertAlmostEqual(r.var('A'), float(both / pb), delta=1e-9)
        self.assertIn('REGION A AND B', rows(r, 'LIMITS'))
        self.assertIn('REGION B', rows(r, 'LIMITS'))
        comp = rows(r, 'COMPLEMENT')
        self.assertEqual(comp, ['P(NOT A|B)=1-P(A|B)', '=1-' + fs(both / pb), '=' + fs(1 - both / pb)])

    def test_conditional_with_complemented_events(self):
        # Inclusion-exclusion: A = min(X,Y)≤1/2 (built-in complement), B = COMPLEMENT OF X+Y≤1.
        q = x + y
        A_c = lambda X, Y: min(X, Y) <= R(1, 2)                                # noqa: E731
        # exact pieces with sympy: P(B) = 1 - P(X+Y≤1); P(A∩B) = P(B) - P(X>1/2,Y>1/2, X+Y>1)
        p_sum = sp.integrate(q, (y, 0, 1 - x), (x, 0, 1))
        p_b = 1 - p_sum
        both_gt = sp.integrate(q, (y, R(1, 2), 1), (x, R(1, 2), 1))            # X,Y>1/2 implies X+Y>1
        p_ab = p_b - both_gt
        self.assertTrue(A_c(R(1, 4), 1))
        acts = rect('X+Y', 0, 1, 0, 1) + ev('P(A|B)', 'MIN/MAX', 'min(X,Y)≤t', i('1/2'),
                                            'MORE EVENTS', 'COMPLEMENT OF', 'X+Y≤k OR X+Y≥k', 'X+Y≤k', i(1),
                                            m('REVERSE ORDER'))
        r = joint(acts)
        for res in blocks(r, 'RESULT'):
            self.assertIn('B=NOT(X+Y≤1)', res)
            self.assertIn('P(A AND B)=' + fs(F(p_ab)), res)
            self.assertIn('P(B)=' + fs(F(p_b)), res)
            self.assertIn('P(A|B)=' + fs(F(p_ab / p_b)), res)
        self.assertIn('REGION A', rows(r, 'LIMITS'))

    def test_custom_linear_bounds_and_reverse(self):
        c = 1 / F(sp.integrate(1, (y, x / 2, 1 + x / 2), (x, 0, 2)))
        p = F(c * sp.integrate(1, (y, sp.Max(1, x / 2), 1 + x / 2), (x, 0, 2)))
        self.assertEqual((c, p), (Fr(1, 2), Fr(1, 2)))
        acts = model('1', ['CUSTOM BOUNDS', 'X OUTER, Y(X)'], [0, 2, 'X/2', '1+X/2']) + ev(
            'MORE EVENTS', 'aX+bY≤c', i(0), i(-1), i(-1), m('REVERSE ORDER'))
        r = joint(acts)
        summary = rows(r, 'MODEL f=c*q')
        self.assertIn('(1/2)x<y<1+(1/2)x', summary)
        self.assertIn('c=1/2', summary)
        self.assertIn('=> -Y≤-1', rows(r, 'EVENT SETUP'))
        dydx, dxdy = blocks(r, 'LIMITS')
        self.assertIn('y FROM 1 TO 1+(1/2)x', dydx)
        self.assertIn('x FROM -2+2y TO 2', dxdy)
        for res in blocks(r, 'RESULT'):
            self.assertEqual(res[0], 'P(-Y≤-1)=' + fs(p))
        # Y outer: 0<y<1, y<x<2-y (a triangle): c = 1/area = 1, P(X>1) by sympy
        c2 = 1 / F(sp.integrate(1, (x, y, 2 - y), (y, 0, 1)))
        p2 = F(c2 * sp.integrate(1, (x, sp.Max(1, y), 2 - y), (y, 0, 1)))
        acts = model('1', ['CUSTOM BOUNDS', 'Y OUTER, X(Y)'], [0, 1, 'Y', '2-Y']) + ev(
            'MORE EVENTS', 'aX+bY≤c', i(-1), i(0), i(-1))
        r = joint(acts)
        self.assertIn('0<y<1', rows(r, 'MODEL f=c*q'))
        self.assertIn('y<x<2-y', rows(r, 'MODEL f=c*q'))
        self.assertIn('c=' + fs(c2), rows(r, 'MODEL f=c*q'))
        self.check(r, 'X>1', p2)

    def test_more_events_rectangle_cdf_interval(self):
        q = x + y
        r = joint(rect('X+Y', 0, 1, 0, 1) + ev('MORE EVENTS', 'X≤s AND Y≤t', i('1/2'), i('1/2')))
        self.assertIn('JOINT CDF F(s,t)', rows(r, 'EVENT SETUP'))
        self.check(r, 'F(1/2,1/2)', F(sp.integrate(q, (x, 0, R(1, 2)), (y, 0, R(1, 2)))))       # Freund Ex16
        r = joint(rect('3/5*X*(Y+X)', 0, 1, 0, 2) + ev('MORE EVENTS', 'RECTANGLE a,b,c,d', i(0), i('1/2'),
                                                        i(1), i(2)))
        self.check(r, 'Ex15', F(sp.integrate(R(3, 5) * x * (y + x), (x, 0, R(1, 2)), (y, 1, 2))))   # 11/80
        r = joint(rect('X+Y', 0, 1, 0, 1) + ev('MORE EVENTS', 'a<X<b ONLY', i('1/4'), i('3/4')))
        self.assertIn('Y IS FREE', rows(r, 'EVENT SETUP'))
        self.check(r, 'interval', F(sp.integrate(q, (y, 0, 1), (x, R(1, 4), R(3, 4)))))
        r = joint(rect('X+Y', 0, 1, 0, 1) + ev('X>a AND Y>b', i('1/3'), i('1/2')))
        self.check(r, 'both exceed', F(sp.integrate(q, (y, R(1, 2), 1), (x, R(1, 3), 1))))
        r = joint(rect('X+Y', 0, 1, 0, 1) + ev('X+Y≤k OR X+Y≥k', 'X+Y≥k', i('3/2')))
        self.assertIn('TOTAL AT LEAST 3/2', rows(r, 'EVENT SETUP'))
        self.check(r, 'sum≥', F(sp.integrate(q, (y, R(3, 2) - x, 1), (x, R(1, 2), 1))))

    def test_random_supports_and_events_against_python_clipping(self):
        # Independent reference: Sutherland-Hodgman with Fractions + sympy over vertical strips.
        rnd = random.Random(7)
        for case in range(6):
            a, b = 0, rnd.randint(1, 3)
            l0, l1 = Fr(rnd.randint(-2, 1)), Fr(rnd.randint(-2, 2), 2)
            u0 = l0 + rnd.randint(2, 4)
            u1 = l1 + Fr(rnd.randint(-1, 1), 2)
            if u0 + u1 * b <= l0 + l1 * b:
                continue
            ea, eb = rnd.choice([(1, 1), (1, -1), (2, 1), (-1, 3)])
            ec = Fr(rnd.randint(-2, 4), 2)
            poly = [(0, 0, 1), (1, 0, 1), (0, 1, 2)][case % 3]
            qs = {(0, 0, 1): ('1', sp.Integer(1)), (1, 0, 1): ('X+1', x + 1), (0, 1, 2): ('2Y+X²+5', 2 * y + x**2 + 5)}[poly]
            verts = [(Fr(a), l0 + l1 * a), (Fr(b), l0 + l1 * b), (Fr(b), u0 + u1 * b), (Fr(a), u0 + u1 * a)]
            total = polygon_integral(qs[1], verts)
            clipped = clip(verts, (Fr(ea), Fr(eb), ec))
            want = Fr(0) if len(clipped) < 3 else polygon_integral(qs[1], clipped) / total
            acts = model(qs[0], ['CUSTOM BOUNDS', 'X OUTER, Y(X)'],
                         [a, b, lin_text(l0, l1, 'X'), lin_text(u0, u1, 'X')])
            acts += ev('MORE EVENTS', 'aX+bY≤c', i(ea), i(eb), i(ec), m('REVERSE ORDER'))
            r = joint(acts)
            for res in blocks(r, 'RESULT'):
                self.assertTrue(res[0].endswith('=' + fs(want)), (case, res, want))
            self.assertAlmostEqual(r.var('A'), float(want), delta=1e-9)


def lin_text(c0, c1, v):
    parts = []
    if c0:
        parts.append(fs(c0))
    if c1:
        coef = '' if abs(c1) == 1 else fs(abs(c1)) + '*'
        parts.append(('-' if c1 < 0 else ('+' if parts else '')) + coef + v)
    s = ''.join(parts) or '0'
    return s


def clip(poly, hp):
    a, b, c = hp
    out = []
    n = len(poly)
    for k in range(n):
        p, q = poly[k], poly[(k + 1) % n]
        dp, dq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if dp <= 0:
            out.append(p)
        if (dp < 0 < dq) or (dq < 0 < dp):
            t = dp / (dp - dq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    dedup = []
    for v in out:
        if not dedup or dedup[-1] != v:
            dedup.append(v)
    if len(dedup) > 1 and dedup[0] == dedup[-1]:
        dedup.pop()
    return dedup


def polygon_integral(expr, poly):
    """Exact ∫∫ expr over a convex polygon (Fractions) via vertical strips."""
    xs = sorted(set(v[0] for v in poly))
    tot = Fr(0)
    n = len(poly)
    for x0, x1 in zip(xs, xs[1:]):
        mid = (x0 + x1) / 2
        vals = []
        for k in range(n):
            p, q = poly[k], poly[(k + 1) % n]
            if (p[0] - mid) * (q[0] - mid) < 0:
                s = (q[1] - p[1]) / (q[0] - p[0])
                vals.append((p[1] + s * (mid - p[0]), p[1] - s * p[0], s))
        vals.sort()
        (_, lo0, lo1), (_, hi0, hi1) = vals[0], vals[-1]
        Rr = lambda f: sp.Rational(f.numerator, f.denominator)           # noqa: E731
        tot += F(sp.integrate(expr, (y, Rr(lo0) + Rr(lo1) * x, Rr(hi0) + Rr(hi1) * x), (x, Rr(x0), Rr(x1))))
    return tot


class Numeric(unittest.TestCase):
    """Non-homework NUMERIC checks (PLAN 4.5 gate: a fraction only when the 2 passes agree)."""

    def test_exponential_pair_on_quadrant(self):
        f = 2 * sp.exp(-x - 2 * y)
        total = sp.integrate(f, (x, 0, sp.oo), (y, 0, sp.oo))
        p_gt = sp.integrate(f, (y, 0, x), (x, 0, sp.oo))
        p_lt = sp.integrate(f, (y, x, sp.oo), (x, 0, sp.oo))
        p_sum = sp.integrate(f, (y, 0, 1 - x), (x, 0, 1))
        self.assertEqual((total, p_gt, p_lt), (1, R(2, 3), R(1, 3)))
        base = model('2𝑒^(⁻X-2Y)', ['QUADRANT X,Y>0'])
        r = joint(base + ev('X<Y OR X>Y', 'X>Y', m('REVERSE ORDER')))
        summary = rows(r, 'MODEL f=c*q')
        self.assertIn('0<x<INF', summary)
        self.assertIn('NUMERIC, 2 PASSES AGREE', summary)
        self.assertAlmostEqual(r.var('M'), 1, delta=1e-8)      # c = 1/total
        for res in blocks(r, 'RESULT'):
            self.assertEqual(res[0], 'P(X>Y)=2/3')                      # converged fraction
            self.assertIn('NUMERIC, 2 PASSES AGREE', res)
        self.assertAlmostEqual(r.var('A'), 2 / 3, delta=1e-8)
        self.assertIn('x FROM 0 TO INF', rows(r, 'LIMITS'))
        self.assertIn('x FROM y TO INF', rows(r, 'LIMITS'))
        r = joint(base + ev('X<Y OR X>Y', 'X<Y'))
        self.assertAlmostEqual(r.var('A'), 1 / 3, delta=1e-8)
        self.assertIn('P(X<Y)=1/3', rows(r, 'RESULT'))
        r = joint(base + ev('X+Y≤k OR X+Y≥k', 'X+Y≤k', i(1)))
        self.assertAlmostEqual(r.var('A'), float(p_sum), delta=1e-8)
        self.assertAlmostEqual(float(p_sum), 0.399576400894, delta=1e-12)
        self.assertIn('P(X+Y≤1)=.399576', rows(r, 'RESULT'))

    def test_quadrant_meeting_event_far_tail_strip(self):
        # |X-Y|≤1/4 on the quadrant creates a strip beyond 5ᴇ5 that must be dropped, not integrated.
        f = 2 * sp.exp(-x - 2 * y)
        k = R(1, 4)
        want = (sp.integrate(f, (y, 0, x + k), (x, 0, k)) +
                sp.integrate(f, (y, x - k, x + k), (x, k, sp.oo)))
        r = joint(model('2𝑒^(⁻X-2Y)', ['QUADRANT X,Y>0']) + ev('MORE EVENTS', '|X-Y|≤k OR >k', '|X-Y|≤k', i('1/4')))
        self.assertAlmostEqual(r.var('A'), float(want), delta=1e-8)

    def test_exponential_triangle_with_infinite_end(self):
        f = sp.exp(-x)
        total = sp.integrate(f, (y, 0, x), (x, 0, sp.oo))
        p = sp.integrate(f, (y, x / 2, x), (x, 0, sp.oo))
        self.assertEqual((total, p), (1, R(1, 2)))
        r = joint(model('𝑒^(⁻X)', ['TRI a<Y<X<b'], [0, 'ᴇ99']) + ev('MORE EVENTS', 'aX+bY≤c', i(1), i(-2), i(0)))
        self.assertAlmostEqual(r.var('M'), 1, delta=1e-8)      # c = 1/total
        self.assertIn('q IS ALREADY A PDF', rows(r, 'MODEL f=c*q'))
        self.assertIn('0<y<x', rows(r, 'MODEL f=c*q'))
        self.assertIn('P(X-2Y≤0)=1/2', rows(r, 'RESULT'))
        self.assertAlmostEqual(r.var('A'), 0.5, delta=1e-8)

    def test_curved_support_and_sub_region(self):
        total = sp.integrate(3, (y, 0, x**2), (x, 0, 1))
        # sub-region 0<x<1/2, X²/2<y<1, clipped to the support (upper X²): smooth, so it converges
        sub = F(sp.integrate(3, (y, x**2 / 2, x**2), (x, 0, R(1, 2))))
        self.assertEqual((total, sub), (1, Fr(1, 16)))
        acts = model('3', ['CUSTOM BOUNDS', 'CURVED (NUMERIC)'], [0, 1, '0', 'X²'])
        acts += ev('CURVED SUB-REGION', i(0), i('1/2'), i('X²/2'), i('1'), m('COMPLEMENT 1-P'))
        r = joint(acts)
        summary = rows(r, 'MODEL f=c*q')
        self.assertIn('TOTAL ∫∫q=1', summary)
        self.assertIn('y FROM 0', summary)
        self.assertIn('TO X²', summary)
        self.assertIn('NUMERIC, 2 PASSES AGREE', summary)
        lim = rows(r, 'LIMITS')
        for row in ['INSIDE THE SUPPORT', 'x FROM 0 TO 1/2', 'y FROM X²/2', 'TO 1', 'PIECE=1/16']:
            self.assertIn(row, lim)
        self.assertIn('P(SUB-REGION)=1/16', rows(r, 'RESULT'))
        self.assertEqual(rows(r, 'COMPLEMENT')[-2:], ['=1-1/16', '=15/16'])
        self.assertAlmostEqual(r.var('M'), 1, delta=1e-10)
        self.assertAlmostEqual(r.var('A'), float(sub), delta=1e-10)
        # a kink inside the sub-region (min(X²,1/8)) cannot be exact: decimals and the APPROX row
        kink = sp.integrate(3 * sp.Min(x**2, R(1, 8)), (x, 0, R(1, 2)))
        r = joint(model('3', ['CUSTOM BOUNDS', 'CURVED (NUMERIC)'], [0, 1, '0', 'X²']) +
                  ev('CURVED SUB-REGION', i(0), i('1/2'), i('0'), i('1/8')))
        self.assertIn('APPROX - NOT CONVERGED', rows(r, 'RESULT'))
        self.assertAlmostEqual(r.var('A'), float(kink), delta=1e-3)

    def test_heavy_tail_and_negative_q_warnings(self):
        r = joint(model('1/((1+X)²(1+Y)²)', ['QUADRANT X,Y>0']))
        self.assertIn('TAIL MAY BE HEAVY', rows(r, 'MODEL f=c*q'))
        r = joint(rect('X-1/4', 0, 1, 0, 1))
        summary = rows(r, 'MODEL f=c*q')
        self.assertIn('q<0 SOMEWHERE', summary)
        self.assertIn('NOT A VALID PDF', summary)

    def test_long_expression_wraps_without_display_warnings(self):
        q = 'X*Y*𝑒^(⁻X)*𝑒^(⁻Y)*√(1+X²)/√(1+X²)+0*abs(X-Y)'
        r = joint(model(q, ['QUADRANT X,Y>0']))               # run() asserts no display warnings
        summary = rows(r, 'MODEL f=c*q')
        self.assertTrue(summary[0].startswith('q=X*Y*'))
        self.assertAlmostEqual(r.var('M'), 1, delta=1e-7)


class AmendmentA1(unittest.TestCase):
    """A1: COMPLEMENT OF... (7th MORE EVENTS item) and EVENT RESULT > COMPLEMENT 1-P."""

    def test_more_events_menu_has_complement_before_back(self):
        r = joint(rect('1', 0, 1, 0, 1) + ev('MORE EVENTS', BACK, BACK))
        menu = next(s['menu'] for s in r.screens if s['event'] == 'menu' and s['menu']['title'] == 'MORE EVENTS')
        self.assertEqual(menu['items'], ['aX+bY≤c', '|X-Y|≤k OR >k', 'X≤s AND Y≤t', 'RECTANGLE a,b,c,d',
                                         'a<X<b ONLY', 'COMPLEMENT OF…', 'BACK'])

    def test_hw4_q5_complement_of_x_less_y(self):
        q = (2 * x + y) / 4
        p = F(sp.integrate(q, (y, x, 2), (x, 0, 1)))
        self.assertEqual(1 - p, Fr(5, 24))
        r = joint(rect('2X+Y', 0, 1, 0, 2) + ev('MORE EVENTS', 'COMPLEMENT OF', 'X<Y OR X>Y', 'X<Y'))
        setup = rows(r, 'EVENT SETUP')
        k = setup.index("NOT A => A'")
        self.assertEqual(setup[k:k + 3], ["NOT A => A'", "P(A')=1-P(A)", 'A=X<Y'])
        res = rows(r, 'RESULT')
        self.assertEqual(res[:5], ['A=X<Y', 'P(A)=' + fs(p), "P(A')=1-P(A)", '=1-' + fs(p), '=' + fs(1 - p)])
        lim = rows(r, 'LIMITS')
        self.assertIn('P(A)=∫∫ c*q(x,y) dy dx', lim)          # A's limits and pieces are shown
        self.assertIn('y FROM x TO 2', lim)
        self.assertAlmostEqual(r.var('A'), float(1 - p), delta=1e-9)

    def test_mock4_q4_complement_of_sum_event(self):
        q = x + 2 * y
        p = F(sp.integrate(q / 4, (y, 0, 1 - x), (x, 0, 1)))
        self.assertEqual(1 - p, Fr(7, 8))
        r = joint(rect('X+2Y', 0, 2, 0, 1) + ev('MORE EVENTS', 'COMPLEMENT OF', 'X+Y≤k OR X+Y≥k', 'X+Y≤k', i(1)))
        res = rows(r, 'RESULT')
        self.assertIn('=1-' + fs(p), res)
        self.assertIn('=' + fs(1 - p), res)

    def test_complement_1_minus_p_reuses_last_event(self):
        q = (x + y) / 8
        fail = 1 - F(sp.integrate(q, (x, 1, 2), (y, 1, 2)))
        r = joint(rect('(X+Y)/8', 0, 2, 0, 2) + ev('MIN/MAX', 'min(X,Y)≤t', i(1), m('COMPLEMENT 1-P')))
        comp = rows(r, 'COMPLEMENT')
        self.assertEqual(comp, ['A=min(X,Y)≤1', 'P(NOT A)=1-P(A)', '=1-' + fs(fail), '=' + fs(1 - fail)])
        menus = [s['menu']['title'] for s in r.screens if s['event'] == 'menu']
        self.assertEqual(menus.count('EVENT RESULT'), 2)          # back to the result menu
        r = joint(rect('2X+Y', 0, 1, 0, 2) + ev('MORE EVENTS', 'COMPLEMENT OF', 'X<Y OR X>Y', 'X<Y',
                                                m('COMPLEMENT 1-P')))
        p = F(sp.integrate((2 * x + y) / 4, (y, x, 2), (x, 0, 1)))
        self.assertEqual(rows(r, 'COMPLEMENT')[:4], ['A=NOT(X<Y)', 'P(NOT A)=1-P(A)', '=1-' + fs(1 - p), '=' + fs(p)])


class AmendmentA2(unittest.TestCase):
    """A2: the first LIMITS screen shows P=∫∫ c*q dy dx, c=, q= and the order before the pieces."""

    def test_hw4_q5_integrand_lines_both_orders(self):
        r = joint(rect('2X+Y', 0, 1, 0, 2) + ev('X<Y OR X>Y', 'X<Y', m('REVERSE ORDER')))
        first_pages = [s for s in r.screens if s['event'] == 'pause' and s['rows'][0].strip() == 'LIMITS'
                       and 'c=1/4' in [row.strip() for row in s['rows']]]
        self.assertEqual(len(first_pages), 2)
        for page, order in zip(first_pages, ('dy dx (x OUTER)', 'dx dy (y OUTER)')):
            body = [row.strip() for row in page['rows'][1:]]
            self.assertEqual(body[:4], ['P=∫∫ c*q(x,y) ' + order[:5], 'c=1/4', 'q=2X+Y', 'ORDER ' + order])
        dydx = blocks(r, 'LIMITS')[0]
        k = dydx.index('x FROM 0 TO 1')
        self.assertEqual(dydx[k + 1], 'y FROM x TO 2')        # enough to write ∫0^1∫x^2 (1/4)(2x+y) dy dx


class ModelEntry(unittest.TestCase):
    def test_rejections(self):
        # NOT LINEAR (X²) in custom linear bounds -> back to CUSTOM
        r = run('M2JNT', model('1', ['CUSTOM BOUNDS', 'X OUTER, Y(X)'], [0, 1, '0', 'X²']) + [BACK, BACK, BACK],
                allow_lists=False)
        self.assertIn('BOUNDS MUST BE LINEAR', r.text)
        # VARCHECK: 2X+T is refused and q is asked again
        r = run('M2JNT', [m('NEW MODEL'), i('2X+T'), i('2X+Y'), BACK, BACK])
        self.assertIn('q MAY USE ONLY X AND Y', r.text)
        self.assertEqual([s['prompt'] for s in r.screens if s['event'] == 'input'], ['q(X,Y)?', 'q(X,Y)?'])
        # a bound that uses Y in an X-outer custom support
        r = run('M2JNT', model('1', ['CUSTOM BOUNDS', 'X OUTER, Y(X)'], [0, 1, '0', 'Y+1']) + [BACK, BACK, BACK])
        self.assertIn('A BOUND USES A LETTER', r.text)
        # UPPER BELOW LOWER
        r = run('M2JNT', model('1', ['CUSTOM BOUNDS', 'X OUTER, Y(X)'], [0, 2, '0', '1-X']) + [BACK, BACK])
        self.assertIn('UPPER BELOW LOWER', r.text)
        r = run('M2JNT', rect('1', 1, 0, 0, 1) + [BACK, BACK])
        self.assertIn('UPPER BELOW LOWER', r.text)
        # polynomial on the quadrant
        r = run('M2JNT', model('X+Y', ['QUADRANT X,Y>0']) + [BACK, BACK])
        self.assertIn('A POLYNOMIAL CANNOT BE', r.text)
        # a huge finite bound
        r = run('M2JNT', rect('1', 0, 200000, 0, 1) + [BACK, BACK])
        self.assertIn('ABS(BOUND)<1ᴇ5', r.text)
        # total ≤ 0
        r = run('M2JNT', rect('X-1/2', 0, 1, 0, 1) + [i('1'), BACK, BACK, BACK])
        self.assertIn('TOTAL ∫∫q≤0', r.text)

    def test_event_misses_support_gives_zero(self):
        r = joint(rect('X+Y', 0, 1, 0, 1) + ev('X>a AND Y>b', i(2), i(0)))
        self.assertIn('EVENT MISSES SUPPORT', rows(r, 'LIMITS'))
        self.assertIn('P(X>2,Y>0)=0', rows(r, 'RESULT'))
        self.assertEqual(r.var('A'), 0)
        r = joint(rect('X+Y', 0, 1, 0, 1) + ev('MORE EVENTS', 'aX+bY≤c', i(1), i(1), i(10)))
        self.assertIn('P(X+Y≤10)=1', rows(r, 'RESULT'))

    def test_event_number_guard(self):
        r = joint(rect('1', 0, 1, 0, 1) + ev('X+Y≤k OR X+Y≥k', 'X+Y≤k', i('ᴇ99'), BACK))
        self.assertIn('EVENT NUMBERS MUST BE', r.text)
        r = joint(rect('1', 0, 1, 0, 1) + ev('MORE EVENTS', 'aX+bY≤c', i(0), i(0), i(1), BACK))
        self.assertIn('a AND b NOT BOTH 0', r.text)

    def test_top_menu_and_flow(self):
        r = run('M2JNT', [BACK])
        menu = r.screens[0]['menu']
        self.assertEqual(menu['title'], 'JOINT DENSITY')
        self.assertEqual(menu['items'], ['NEW MODEL', 'EVENTS + LIMITS', 'FORMULAS', 'MOMENTS + COV',
                                         'GIVEN A VALUE', 'INDEP + CDF', 'BACK'])
        # no model yet: EVENTS + LIMITS starts NEW MODEL, then goes straight to the EVENT menu
        r = joint([m('EVENTS + LIMITS'), i('X+Y'), m('RECT'), i(0), i(1), i(0), i(1), BACK])
        titles = [s['menu']['title'] for s in r.screens if s['event'] == 'menu']
        self.assertEqual(titles[:4], ['JOINT DENSITY', 'SUPPORT', 'EVENT', 'JOINT DENSITY'])
        # P3 items: a short note, then the top menu again (the model is kept)
        for item in ['FORMULAS', 'MOMENTS + COV', 'GIVEN A VALUE', 'INDEP + CDF']:
            r = joint(rect('X+Y', 0, 1, 0, 1) + [m(item)])
            self.assertIn('COMING IN THIS VERSION', r.text)
        r = joint([m('FORMULAS'), i('X+Y'), m('RECT'), i(0), i(1), i(0), i(1)])
        self.assertIn('COMING IN THIS VERSION', r.text)
        self.assertEqual(r.var('Z'), 0)

    def test_z99_preload_lands_on_the_analysis_menu(self):
        init = {'Z': 99, 'Str1': '(X+Y)/8', 'ʟM2JM': [1, 0, 2, 0, 2]}
        r = run('M2JNT', ev('MIN/MAX', 'min(X,Y)≤t', i(1)) + [BACK, BACK], init=init)
        self.assertFalse([s for s in r.screens if s['event'] == 'input' and s['prompt'] == 'q(X,Y)?'])
        self.assertIn('q=(X+Y)/8', rows(r, 'MODEL f=c*q'))
        first_menu = next(s for s in r.screens if s['event'] == 'menu')
        self.assertEqual(first_menu['menu']['title'], 'JOINT DENSITY')
        self.assertEqual(r.var('Z'), 0)
        self.assertAlmostEqual(r.var('A'), 5 / 8, delta=1e-9)

    def test_back_removes_every_private_list(self):
        r = joint(model('2𝑒^(⁻X-2Y)', ['QUADRANT X,Y>0']) + ev('X<Y OR X>Y', 'X>Y'))
        self.assertEqual(sorted(n for n in r.vars['lists'] if n.startswith('M2')), [])


class StepBudgets(unittest.TestCase):
    """PLAN 7 P2 item 7 (simulator statements)."""

    @staticmethod
    def span(r, first_title, first_item, last_title):
        start = next(s['step'] for s in r.screens if s['event'] == 'menu' and s['menu']['title'] == first_title
                     and s['response'].split(': ', 1)[-1].startswith(first_item))
        end = next(s['step'] for s in r.screens if s['event'] == 'menu' and s['menu']['title'] == last_title
                   and s['step'] > start)
        return end - start

    def test_exact_budgets(self):
        sim = Sim(str(SRC))
        cases = [  # (model actions, event path from the EVENT menu, submenu title, item)
            (rect('(2X+Y)/4', 0, 1, 0, 2), ['X<Y OR X>Y', 'X<Y'], 'X VS Y', 'X<Y'),
            (rect('(X+Y)/8', 0, 2, 0, 2), ['MIN/MAX', 'min(X,Y)≤t', i(1)], 'MIN/MAX', 'min'),
            (model('X', ['TRI a<Y<X<b'], [0, 1]), ['X+Y≤k OR X+Y≥k', 'X+Y≤k', i(1)], 'X+Y VS k', 'X+Y≤k'),
            (rect('1', 0, 1, 0, 1), ['MORE EVENTS', '|X-Y|≤k OR >k', '|X-Y|≤k', i('1/4')], '|X-Y| VS k', '|X-Y|≤k'),
        ]
        for base, path, title, item in cases:
            r = sim.run('M2JNT', base + ev(*path, m('REVERSE ORDER')) + [BACK, BACK], max_steps=3_000_000,
                        init_vars=dict(INIT))
            self.assertIsNone(r.error)
            model_steps = next(s['step'] for s in r.screens if s['event'] == 'menu' and s['menu']['title'] == 'EVENT')
            self.assertLess(model_steps, 3000, base)
            self.assertLess(self.span(r, title, item, 'EVENT RESULT'), 5000, path)
            self.assertLess(self.span(r, 'EVENT RESULT', 'REVERSE', 'EVENT RESULT'), 5000, path)

    def test_numeric_quadrant_budgets(self):
        sim = Sim(str(SRC))
        r = sim.run('M2JNT', model('2𝑒^(⁻X-2Y)', ['QUADRANT X,Y>0']) + ev('X<Y OR X>Y', 'X<Y', m('REVERSE ORDER'))
                    + [BACK, BACK], max_steps=3_000_000, init_vars=dict(INIT))
        self.assertIsNone(r.error)
        model_steps = next(s['step'] for s in r.screens if s['event'] == 'menu' and s['menu']['title'] == 'EVENT')
        self.assertLess(model_steps, 80_000)
        self.assertLess(self.span(r, 'X VS Y', 'X<Y', 'EVENT RESULT'), 80_000)
        self.assertLess(self.span(r, 'EVENT RESULT', 'REVERSE', 'EVENT RESULT'), 80_000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
