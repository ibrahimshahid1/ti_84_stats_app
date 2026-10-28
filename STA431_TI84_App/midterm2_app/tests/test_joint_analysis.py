#!/usr/bin/env python3
# PLAN DEVIATIONS / EXTRA FIXES (LEAN-B, reduced PLAN 7 P3; also in PROGRESS.md "## LEAN-B")
# * The analysis code lives in a NEW helper program M2JAN (M2JNT was at 12.3 KB). M2JNT's top-menu
#   items FORMULAS / MOMENTS + COV / GIVEN A VALUE / INDEP + CDF build the support strips in both
#   orders (RG with the silent return code C=7, no integration) into ʟM2JX (x outer) / ʟM2JY (y
#   outer), then call prgmM2JAN with the item in H. M2JAN returns H=5 for "F(s,t) AT A POINT", which
#   M2JNT answers with its own EVENTS > X≤s AND Y≤t engine (pieces shown). M2JAN's lists are ʟM2N*
#   (deleted on every return); M2JNT's BACK also deletes ʟM2JX/ʟM2JY.
# * The marginal/conditional/E(.|.) formulas are computed by M2JAN itself (strip integration of the
#   RECOVER2 table, synthetic division for common factors) instead of new M2PLY modes 5-7; POLY2STR
#   (M2PLY θ=4, LEAN-A) prints the 2-D numerators. Adjacent identical pieces are not merged (the
#   region engine already merges strips with the same limit lines).
# * Formula screens show ratios as (N)/(D), e.g. (1)/(x), (2x)/(y²); a denominator 1 is omitted.
#   Pieces read "FOR a<x<b" / "y FROM l TO u" (marginals, E formulas) or "AND l<y<u" (conditional
#   supports); no colons (TI strings). Menu item "E[g(X,Y)]"; its screen title is "E(g(X,Y))".
# * MOMENTS + COV has MEANS VARS COV ρ and E[g(X,Y)] (no PRODUCT MOMENT r,s or VAR(aX+bY+c) items:
#   budget mode). ρ shows a fraction, else ±√(p/q) when ρ² is a fraction, plus the decimal.
#   E[g] is EXACT when q and g are polynomials with 2*deg(g)+deg(q) ≤ 12 (total degrees), else
#   NUMERIC (2 passes).
# * GIVEN A VALUE: GIVEN X=x / GIVEN Y=y, then the slice menu P(a<Y<b | X=x) / NEW VALUE / BACK
#   (no E[g(Y)] GIVEN item). The curved support allows GIVEN X=x only. Outside the support the screen
#   says "h(3)=0", "OUTSIDE THE SUPPORT", "CONDITIONAL UNDEFINED".
# * INDEP + CDF: INDEPENDENCE TEST, F(s,t) AT A POINT, F(x,y) FORMULA (A4). Non-product supports
#   give a witness from the 3x3 grid (1/4,1/2,3/4 of the bounding box; .5,1,2 from the finite end of
#   an infinite side): f(x*,y*)=0 BUT g(x*)h(y*)=v. Product supports: rank-1 coefficient test
#   (polynomial) or the grid with numeric marginals ("NUMERIC EVIDENCE", tolerance 1ᴇ⁻7). A curved
#   support is reported DEPENDENT without a witness.
# * M2SLICE and M2CONT's DOUBLE INTEGRAL are NOT retired (budget mode); the HW5 Q7 preset and the
#   M2EXAM GIVEN VALUE / MOMENT / MARGINAL FORMULA routes now open M2JNT.
# * Extra fixes: test_joint_events' P2 stub test now checks the four analysis menus;
#   test_exam_assistant's conditional-slice case runs JOINT DENSITY > GIVEN A VALUE; test_presets'
#   HW5 Q7 case runs GIVEN Y=y; test_menu_tree has CANNED inputs for M2JAN and lists the module.
"""LEAN-B acceptance tests for JOINT DENSITY > FORMULAS, MOMENTS + COV, GIVEN A VALUE and
INDEP + CDF (helper program M2JAN). Every expected value is computed here with sympy, never copied
from a run of the app. Formula strings on the screens are parsed back into sympy and compared
symbolically (and a few are also asserted verbatim)."""
import math
import re
import unittest

import sympy as sp
from sympy.parsing.sympy_parser import (implicit_multiplication_application, parse_expr,
                                        standard_transformations)

from m2test import m, i, run, num
import build_package

x, y = sp.symbols('x y')
R = sp.Rational
BACK = m('BACK')
TRANS = standard_transformations + (implicit_multiplication_application,)


def P(s):
    """Parse a TI screen formula such as 3/2-3/2y², (2x)/(y²), 1/4x²y+1/8xy² into sympy."""
    s = s.replace('⁻', '-').replace('²', '**2').replace('³', '**3').replace('^', '**')
    return parse_expr(s, local_dict={'x': x, 'y': y}, transformations=TRANS)


def same(a, b):
    return sp.simplify(sp.nsimplify(a) - sp.nsimplify(b)) == 0


def fs(v):
    v = sp.nsimplify(v)
    p, q = sp.fraction(v)
    s = str(abs(p)) if q == 1 else f"{abs(p)}/{q}"
    return ("⁻" if v < 0 else "") + s


def lines(r, title):
    """Logical lines of the LAST run of pages titled `title` (rows of 26 characters are joined
    with the next row, which is how the pager wraps a long line)."""
    runs, cur, prev = [], None, None
    for s in r.screens:
        if s['event'] != 'pause':
            prev = None
            continue
        t = s['rows'][0].strip()
        if t == title:
            if prev != title:
                cur = []
                runs.append(cur)
            cur.extend(row.rstrip() for row in s['rows'][1:] if row.strip())
        prev = t
    assert runs, f'no screen titled {title!r}\n{r.text[-4000:]}'
    out, buf = [], ''
    for row in runs[-1]:
        buf += row.strip() if buf else row.strip()
        if len(row) < 26:
            out.append(buf)
            buf = ''
    if buf:
        out.append(buf)
    return out


def value(r, title, label):
    """Text after `label` on the LAST logical line of `title` that starts with it (header lines
    such as g(x)=fX(x) come first, the result last)."""
    for ln in reversed(lines(r, title)):
        if ln.startswith(label):
            return ln[len(label):]
    raise AssertionError(f'{label!r} not on {title!r}: {lines(r, title)}')


def model(q, support, *vals):
    return [m('NEW MODEL'), i(q), m(support), *[i(v) for v in vals]]


def joint(actions, **kw):
    return run('M2JNT', actions + [BACK], **kw)


def marg(f, lo, hi, var):
    return sp.integrate(f, (var, lo, hi))


class Formulas(unittest.TestCase):
    def test_hw4_q2_marginal_and_conditional(self):
        q = 2 * x + y
        c = 1 / sp.integrate(q, (x, 0, 1), (y, 0, 2))
        f = c * q
        h = marg(f, 0, 1, x)
        g = marg(f, 0, 2, y)
        self.assertEqual(c, R(1, 4))
        r = joint(model('2X+Y', 'RECT', 0, 1, 0, 2) +
                  [m('FORMULAS'), m('g(x)'), m('h(y)'), m('f(x|y)'), m('w(y|x)'), BACK])
        self.assertIn('c=' + fs(c), r.text)
        hl = lines(r, 'h(y) MARGINAL')
        self.assertIn('=∫f(x,y) dx', hl)
        self.assertIn('FOR 0<y<2', hl)
        self.assertIn('x FROM 0 TO 1', hl)
        self.assertTrue(same(P(value(r, 'h(y) MARGINAL', 'h(y)=')), h))
        self.assertEqual(value(r, 'h(y) MARGINAL', 'h(y)='), '1/4+1/4y')
        self.assertEqual(value(r, 'h(y) MARGINAL', 'CHECK ∫h dy='), fs(sp.integrate(h, (y, 0, 2))))
        self.assertTrue(same(P(value(r, 'g(x) MARGINAL', 'g(x)=')), g))
        self.assertEqual(value(r, 'f(x|y) CONDITIONAL', 'f(x|y)='), '(2x+y)/(1+y)')
        self.assertTrue(same(P(value(r, 'f(x|y) CONDITIONAL', 'f(x|y)=')), f / h))
        self.assertIn('AND 0<x<1', lines(r, 'f(x|y) CONDITIONAL'))
        self.assertTrue(same(P(value(r, 'w(y|x) CONDITIONAL', 'w(y|x)=')), f / g))

    def test_triangle_q_x_non_homework(self):
        # q = x on 0<y<x<1 (Mock II Q2 model): g=3x², h=3/2-3/2y², w=1/x, E(Y|X=x)=x/2
        q = x
        c = 1 / sp.integrate(q, (y, 0, x), (x, 0, 1))
        f = c * q
        g = marg(f, 0, x, y)
        h = marg(f, y, 1, x)
        ey = sp.integrate(y * f, (y, 0, x)) / g
        r = joint(model('X', 'TRI a<Y<X<b', 0, 1) +
                  [m('FORMULAS'), m('g(x)'), m('h(y)'), m('w(y|x)'), m('E(Y|X=x)'), m('E(X|Y=y)'), BACK])
        self.assertEqual(value(r, 'g(x) MARGINAL', 'g(x)='), '3x²')
        self.assertTrue(same(P(value(r, 'g(x) MARGINAL', 'g(x)=')), g))
        self.assertIn('y FROM 0 TO x', lines(r, 'g(x) MARGINAL'))
        self.assertEqual(value(r, 'h(y) MARGINAL', 'h(y)='), '3/2-3/2y²')
        self.assertTrue(same(P(value(r, 'h(y) MARGINAL', 'h(y)=')), h))
        self.assertIn('x FROM y TO 1', lines(r, 'h(y) MARGINAL'))
        self.assertTrue(same(P(value(r, 'w(y|x) CONDITIONAL', 'w(y|x)=')), f / g))
        self.assertIn('AND 0<y<x', lines(r, 'w(y|x) CONDITIONAL'))
        self.assertTrue(same(P(value(r, 'E(Y|X=x) FORMULA', 'E(Y|X=x)=')), ey))
        ex = sp.integrate(x * f, (x, y, 1)) / h
        self.assertTrue(same(P(value(r, 'E(X|Y=y) FORMULA', 'E(X|Y=y)=')), ex))

    def test_triangle_q_xy_non_homework(self):
        # q = xy on 0<x<y<1 (Mock 4 Q3 model): c=8, g=4x-4x³, h=4y³, f(x|y)=2x/y²
        q = x * y
        c = 1 / sp.integrate(q, (x, 0, y), (y, 0, 1))
        self.assertEqual(c, 8)
        f = c * q
        g = marg(f, x, 1, y)
        h = marg(f, 0, y, x)
        r = joint(model('X*Y', 'TRI a<X<Y<b', 0, 1) +
                  [m('FORMULAS'), m('g(x)'), m('h(y)'), m('f(x|y)'), m('E(Y|X=x)'), BACK])
        self.assertIn('c=8', r.text)
        self.assertTrue(same(P(value(r, 'g(x) MARGINAL', 'g(x)=')), g))
        self.assertTrue(same(P(value(r, 'h(y) MARGINAL', 'h(y)=')), h))
        self.assertEqual(value(r, 'f(x|y) CONDITIONAL', 'f(x|y)='), '(2x)/(y²)')
        self.assertTrue(same(P(value(r, 'f(x|y) CONDITIONAL', 'f(x|y)=')), f / h))
        ey = sp.integrate(y * f, (y, x, 1)) / g
        shown = value(r, 'E(Y|X=x) FORMULA', 'E(Y|X=x)=')
        self.assertTrue(same(P(shown), ey))
        self.assertTrue(shown.endswith('/(1+x)'), shown)     # the factors x and (1-x) cancelled

    def test_sum_bounded_support(self):
        # q = x on x,y>0, x+y<2: h(y) integrates x FROM 0 TO 2-y
        q = x
        c = 1 / sp.integrate(q, (y, 0, 2 - x), (x, 0, 2))
        h = marg(c * q, 0, 2 - y, x)
        r = joint(model('X', 'X,Y>0 AND X+Y<k', 2) + [m('FORMULAS'), m('h(y)'), BACK])
        self.assertIn('x FROM 0 TO 2-y', lines(r, 'h(y) MARGINAL'))
        self.assertTrue(same(P(value(r, 'h(y) MARGINAL', 'h(y)=')), h))

    def test_formulas_refuse_a_numeric_model(self):
        r = joint(model('2𝑒^(⁻X-2Y)', 'QUADRANT') + [m('FORMULAS')], max_steps=5_000_000)
        self.assertIn('FORMULAS NEED A', r.text)
        self.assertIn('USE GIVEN A VALUE', r.text)

    def test_formula_step_budget(self):
        base = joint(model('X*Y', 'TRI a<X<Y<b', 0, 1)).steps
        for item in ['g(x)', 'f(x|y)', 'E(Y|X=x)']:
            r = joint(model('X*Y', 'TRI a<X<Y<b', 0, 1) + [m('FORMULAS'), m(item), BACK])
            self.assertLess(r.steps - base, 6_000, item)


class Given(unittest.TestCase):
    def test_hw5_q7_given_y(self):
        q = x + y
        h = marg(q, 0, 1, x)
        y0 = R(1, 2)
        fc = (q / h).subs(y, y0)
        e1 = sp.integrate(x * fc, (x, 0, 1))
        e2 = sp.integrate(x**2 * fc, (x, 0, 1))
        self.assertEqual((e1, e2 - e1**2), (R(7, 12), R(11, 144)))
        r = joint(model('X+Y', 'RECT', 0, 1, 0, 1) +
                  [m('FORMULAS'), m('h(y)'), BACK, m('GIVEN A VALUE'), m('GIVEN Y=y'), i('1/2'), BACK, BACK])
        self.assertEqual(value(r, 'h(y) MARGINAL', 'h(y)='), '1/2+y')
        self.assertTrue(same(P(value(r, 'h(y) MARGINAL', 'h(y)=')), h))
        L = lines(r, 'GIVEN Y=1/2')
        self.assertIn('h(1/2)=∫f(x,1/2) dx', L)
        self.assertIn('h(1/2)=' + fs(h.subs(y, y0)), L)
        self.assertIn('f(x|1/2)=f(x,1/2)/h(1/2)', L)
        self.assertTrue(same(P(L[L.index('f(x|1/2)=f(x,1/2)/h(1/2)') + 1][1:]), fc))
        self.assertIn('FOR 0<x<1', L)
        self.assertEqual(value(r, 'GIVEN Y=1/2', 'E(X|Y=1/2)='), fs(e1))
        self.assertEqual(value(r, 'GIVEN Y=1/2', 'E(X²|Y=1/2)='), fs(e2))
        self.assertEqual(value(r, 'GIVEN Y=1/2', 'Var(X|Y=1/2)='), fs(e2 - e1**2))
        self.assertAlmostEqual(float(r.var('A')), float(e1), delta=1e-12)

    def test_freund_ex20_given_and_interval_non_homework(self):
        # q = 2/3(x+2y) on the unit square, given Y=1/2: E=5/9, Var=13/162, P(X≤1/2|Y=1/2)=5/12
        f = R(2, 3) * (x + 2 * y)
        fc = (f / marg(f, 0, 1, x)).subs(y, R(1, 2))
        e1 = sp.integrate(x * fc, (x, 0, 1))
        var = sp.integrate(x**2 * fc, (x, 0, 1)) - e1**2
        p = sp.integrate(fc, (x, 0, R(1, 2)))
        r = joint(model('2/3*(X+2Y)', 'RECT', 0, 1, 0, 1) +
                  [m('GIVEN A VALUE'), m('GIVEN Y=y'), i('1/2'), m('P(a<X<b'), i('⁻ᴇ99'), i('1/2'),
                   BACK, BACK])
        self.assertEqual(value(r, 'GIVEN Y=1/2', 'E(X|Y=1/2)='), fs(e1))
        self.assertEqual(value(r, 'GIVEN Y=1/2', 'Var(X|Y=1/2)='), fs(var))
        L = lines(r, 'CONDITIONAL PROB')
        self.assertIn('P(-INF<X<1/2 | Y=1/2)', L)
        self.assertIn('x FROM 0 TO 1/2', L)
        self.assertEqual(value(r, 'CONDITIONAL PROB', 'P='), fs(p))
        self.assertAlmostEqual(float(r.var('A')), float(p), delta=1e-12)

    def test_given_x_on_triangle_and_outside_support(self):
        # q = xy on 0<x<y<1, given Y=3/4: P(X<1/2 | Y=3/4) = 4/9 (Mock 4 Q3); given X=2: undefined
        f = 8 * x * y
        fc = (f / marg(f, 0, y, x)).subs(y, R(3, 4))
        p = sp.integrate(fc, (x, 0, R(1, 2)))
        r = joint(model('X*Y', 'TRI a<X<Y<b', 0, 1) +
                  [m('GIVEN A VALUE'), m('GIVEN Y=y'), i('3/4'), m('P(a<X<b'), i(0), i('1/2'), BACK,
                   m('GIVEN X=x'), i(2), BACK])
        self.assertEqual(value(r, 'CONDITIONAL PROB', 'P='), fs(p))
        self.assertIn('x FROM 0 TO 3/4', lines(r, 'GIVEN Y=3/4'))
        self.assertIn('OUTSIDE THE SUPPORT', r.text)
        self.assertIn('CONDITIONAL UNDEFINED', r.text)

    def test_numeric_given_value(self):
        q = x * sp.exp(-x * (1 + y))
        h1 = sp.integrate(q.subs(y, 1), (x, 0, sp.oo))
        e1 = sp.integrate(x * q.subs(y, 1), (x, 0, sp.oo)) / h1
        p = sp.integrate(q.subs(y, 1), (x, 1, sp.oo)) / h1
        r = joint(model('X𝑒^(⁻X(1+Y))', 'QUADRANT') +
                  [m('GIVEN A VALUE'), m('GIVEN Y=y'), i(1), m('P(a<X<b'), i(1), i('ᴇ99'), BACK, BACK],
                  max_steps=6_000_000)
        self.assertAlmostEqual(num(value(r, 'GIVEN Y=1', 'h(1)=')), float(h1), delta=1e-7)
        self.assertAlmostEqual(num(value(r, 'GIVEN Y=1', 'E(X|Y=1)=')), float(e1), delta=1e-7)
        self.assertAlmostEqual(float(r.var('A')), float(p), delta=1e-7)
        self.assertIn('NUMERIC, 2 PASSES AGREE', r.text)

    def test_given_step_budget(self):
        base = joint(model('X+Y', 'RECT', 0, 1, 0, 1)).steps
        r = joint(model('X+Y', 'RECT', 0, 1, 0, 1) + [m('GIVEN A VALUE'), m('GIVEN Y=y'), i('1/2'), BACK, BACK])
        self.assertLess(r.steps - base, 2_500)


class Moments(unittest.TestCase):
    def test_x_plus_y_unit_square(self):
        f = x + y
        E = lambda g: sp.integrate(g * f, (x, 0, 1), (y, 0, 1))
        ex, ey, exy = E(x), E(y), E(x * y)
        vx, vy = E(x**2) - ex**2, E(y**2) - ey**2
        cov = exy - ex * ey
        rho = cov / sp.sqrt(vx * vy)
        self.assertEqual((ex, cov), (R(7, 12), R(-1, 144)))
        g = x * y
        eg, eg2 = E(g), E(g**2)
        r = joint(model('X+Y', 'RECT', 0, 1, 0, 1) +
                  [m('MOMENTS + COV'), m('MEANS VARS COV ρ'), m('E[g(X,Y)]'), i('X*Y'), BACK])
        t = 'MOMENTS'
        for label, v in [('E(X)=', ex), ('E(Y)=', ey), ('E(X²)=', E(x**2)), ('E(Y²)=', E(y**2)),
                         ('E(XY)=', exy)]:
            self.assertEqual(value(r, t, label), fs(v), label)
        L = lines(r, t)
        self.assertEqual(L[L.index('Var(X)=E(X²)-E(X)²') + 1], '=' + fs(vx))
        self.assertEqual(L[L.index('Var(Y)=E(Y²)-E(Y)²') + 1], '=' + fs(vy))
        j = L.index('Cov=E(XY)-E(X)E(Y)')
        self.assertEqual(L[j + 1], f'={fs(exy)}-({fs(ex)})({fs(ey)})')
        self.assertEqual(L[j + 2], '=' + fs(cov))
        self.assertEqual(L[L.index('ρ=Cov/(SD(X)SD(Y))') + 1], '=' + fs(rho))
        self.assertIn('EXACT (POLYNOMIAL)', L)
        self.assertEqual(value(r, 'E(g(X,Y))', 'E(g)='), fs(eg))
        self.assertEqual(value(r, 'E(g(X,Y))', 'E(g²)='), fs(eg2))
        G = lines(r, 'E(g(X,Y))')
        self.assertEqual(G[G.index('Var(g)=E(g²)-E(g)²') + 1], '=' + fs(eg2 - eg**2))

    def test_triangle_rho_sqrt_form_non_homework(self):
        # q = 1 on 0<x<y<1 (Mock 6 Q2): Cov=1/36, rho=1/2;  q = x on 0<y<x<1: rho irrational -> √ form
        f = 3 * x
        E = lambda g: sp.integrate(g * f, (y, 0, x), (x, 0, 1))
        cov = E(x * y) - E(x) * E(y)
        rho2 = cov**2 / ((E(x**2) - E(x)**2) * (E(y**2) - E(y)**2))
        self.assertFalse(sp.sqrt(rho2).is_rational)
        r = joint(model('X', 'TRI a<Y<X<b', 0, 1) + [m('MOMENTS + COV'), m('MEANS VARS COV ρ'), BACK])
        L = lines(r, 'MOMENTS')
        self.assertIn('=' + fs(cov), L)
        self.assertEqual(L[L.index('ρ=Cov/(SD(X)SD(Y))') + 1], '=√(' + fs(rho2) + ')')
        self.assertAlmostEqual(num(L[L.index('ρ=Cov/(SD(X)SD(Y))') + 2][1:]), float(sp.sqrt(rho2)), delta=1e-6)
        self.assertAlmostEqual(float(r.var('A')), float(cov), delta=1e-12)

    def test_numeric_quadrant_moments_and_budget(self):
        f = 2 * sp.exp(-x - 2 * y)
        E = lambda g: sp.integrate(g * f, (x, 0, sp.oo), (y, 0, sp.oo))
        ex, ey = E(x), E(y)
        cov = E(x * y) - ex * ey
        r = joint(model('2𝑒^(⁻X-2Y)', 'QUADRANT') + [m('MOMENTS + COV'), m('MEANS VARS COV ρ'), BACK],
                  max_steps=6_000_000)
        base = joint(model('2𝑒^(⁻X-2Y)', 'QUADRANT'), max_steps=6_000_000).steps
        self.assertLess(r.steps - base, 120_000)
        self.assertAlmostEqual(num(value(r, 'MOMENTS', 'E(X)=')), float(ex), delta=1e-7)
        self.assertAlmostEqual(num(value(r, 'MOMENTS', 'E(Y)=')), float(ey), delta=1e-7)
        self.assertAlmostEqual(float(r.var('A')), float(cov), delta=1e-7)
        self.assertIn('NUMERIC, 2 PASSES AGREE', r.text)

    def test_exact_moment_budget(self):
        base = joint(model('X+Y', 'RECT', 0, 1, 0, 1)).steps
        r = joint(model('X+Y', 'RECT', 0, 1, 0, 1) + [m('MOMENTS + COV'), m('MEANS VARS COV ρ'), BACK])
        self.assertLess(r.steps - base, 3_000)


class IndepCdf(unittest.TestCase):
    def test_4xy_independent(self):
        f = 4 * x * y
        g, h = marg(f, 0, 1, y), marg(f, 0, 1, x)
        self.assertEqual(sp.simplify(f - g * h), 0)
        r = joint(model('4X*Y', 'RECT', 0, 1, 0, 1) + [m('INDEP + CDF'), m('INDEPENDENCE TEST'), BACK])
        L = lines(r, 'INDEPENDENCE')
        self.assertIn('=> INDEPENDENT', L)
        self.assertTrue(same(P(value(r, 'INDEPENDENCE', 'g(x)=')), g))
        self.assertTrue(same(P(value(r, 'INDEPENDENCE', 'h(y)=')), h))

    def check_witness(self, r, f, g, h, outside):
        L = lines(r, 'INDEPENDENCE')
        self.assertIn('=> DEPENDENT', L)
        fl = next(ln for ln in L if re.match(r'f\([⁻0-9./]+,[⁻0-9./]+\)=', ln))
        pt, fv = fl[2:].split(')=')
        a, b = (sp.Rational(v.replace('⁻', '-')) for v in pt.split(','))
        ghl = next(ln for ln in L if ln.startswith('BUT g('))
        gv = ghl.split(')=')[-1]
        self.assertEqual(sp.Rational(fv.replace('⁻', '-')), 0 if outside else f.subs({x: a, y: b}))
        self.assertEqual(sp.Rational(gv.replace('⁻', '-')), (g.subs(x, a) * h.subs(y, b)))
        self.assertNotEqual(sp.Rational(fv.replace('⁻', '-')), sp.Rational(gv.replace('⁻', '-')))

    def test_x_plus_y_dependent_with_witness(self):
        f = x + y
        r = joint(model('X+Y', 'RECT', 0, 1, 0, 1) + [m('INDEP + CDF'), m('INDEPENDENCE TEST'), BACK])
        self.assertIn('SUPPORT IS A PRODUCT SET', r.text)
        self.check_witness(r, f, marg(f, 0, 1, y), marg(f, 0, 1, x), outside=False)

    def test_triangle_dependent_because_of_the_support(self):
        f = 3 * x
        r = joint(model('X', 'TRI a<Y<X<b', 0, 1) + [m('INDEP + CDF'), m('INDEPENDENCE TEST'), BACK])
        self.assertIn('SUPPORT IS NOT A PRODUCT', r.text)
        self.check_witness(r, f, marg(f, 0, x, y), marg(f, y, 1, x), outside=True)

    def test_numeric_independent_evidence(self):
        r = joint(model('2𝑒^(⁻X-2Y)', 'QUADRANT') + [m('INDEP + CDF'), m('INDEPENDENCE TEST'), BACK],
                  max_steps=6_000_000)
        L = lines(r, 'INDEPENDENCE')
        self.assertIn('(NUMERIC EVIDENCE)', L)
        self.assertIn('=> INDEPENDENT', L)

    def test_a4_f_at_a_point_through_the_event_engine(self):
        for q, b, d, s, t in [((x + y) / 8, 2, 2, 1, 1), ((2 * x + y) / 4, 1, 2, R(1, 2), 1)]:
            target = sp.integrate(q, (x, 0, s), (y, 0, t))
            self.assertEqual(target, R(1, 8))
            typed = '(X+Y)/8' if b == 2 else '(2X+Y)/4'
            r = joint(model(typed, 'RECT', 0, b, 0, d) +
                      [m('INDEP + CDF'), m('F(s,t) AT A POINT'), i(s), i(t), BACK])
            self.assertIn('JOINT CDF F(s,t)', r.text)
            self.assertAlmostEqual(float(r.var('A')), float(target), delta=1e-12)
            self.assertIn('=' + fs(target), r.text)
            self.assertIn('LIMITS', r.text)

    def test_a4_f_formula_hw4_q5_and_freund_ex16(self):
        u, v = sp.symbols('u v')
        for typed, q, b, d in [('(2X+Y)/4', (2 * u + v) / 4, 1, 2), ('X+Y', u + v, 1, 1)]:
            F = sp.integrate(q, (u, 0, x), (v, 0, y))
            r = joint(model(typed, 'RECT', 0, b, 0, d) + [m('INDEP + CDF'), m('F(x,y) FORMULA'), BACK])
            L = lines(r, 'F(x,y) FORMULA')
            interior = L[L.index(f'FOR 0<x<{b}, 0<y<{d}') + 1]
            self.assertTrue(interior.startswith('F='), L)
            self.assertTrue(same(P(interior[2:]), F), L)
            j = L.index(f'y≥{d}, F=F(x,{d})')
            self.assertTrue(same(P(L[j + 1][1:]), F.subs(y, d)))
            j = L.index(f'x≥{b}, F=F({b},y)')
            self.assertTrue(same(P(L[j + 1][1:]), F.subs(x, b)))
        self.assertEqual(interior, 'F=1/2x²y+1/2xy²')       # Freund Ex16

    def test_f_formula_needs_a_rectangle(self):
        r = joint(model('X', 'TRI a<Y<X<b', 0, 1) + [m('INDEP + CDF'), m('F(x,y) FORMULA'), BACK])
        self.assertIn('F FORMULA NEEDS A', r.text)


class Memory(unittest.TestCase):
    def test_program_caps(self):
        sizes = build_package.tokenized_sizes()
        self.assertLessEqual(sizes['M2JNT'], 13_800)
        self.assertLessEqual(sizes['M2JAN'], 13_000)
        self.assertLessEqual(build_package.memory_estimate(), build_package.BUDGET_BYTES)
        self.assertIn('M2JAN', build_package.program_order())


if __name__ == '__main__':
    unittest.main(verbosity=2)
