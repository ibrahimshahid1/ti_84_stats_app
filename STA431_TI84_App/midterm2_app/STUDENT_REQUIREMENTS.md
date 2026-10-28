# Student requirements (mandatory, added before the build)

These come directly from the student and override anything in PLAN.md that conflicts.
Every item must be implemented, tested, and reachable from the SOLVERS menu (and, where
relevant, the HELP finder).

## R1. Joint CDF solver

The student types F(x,y) and its support. The solver must:

- compute rectangle probabilities with
  P(a<X≤b, c<Y≤d) = F(b,d) − F(a,d) − F(b,c) + F(a,c)
- give the marginal CDFs: F_X(x) = F(x, top of Y's support), and the same for Y
  (F_Y(y) = F(top of X's support, y))
- recover the joint PDF f(x,y) = ∂²F/∂x∂y:
  - as an EXACT formula when F is a polynomial
  - as numerical values at points otherwise
- also go the other way: given f, find F(x,y) at a point
- show the formula it used on each result screen so the work can be copied onto the exam

## R2. Support and integration-limits helper

The student picks the support shape from a menu:
rectangle, triangle like 0<y<x<1, region under x+y<1, first quadrant (0,∞)², or custom
linear bounds.

Then the student picks the event:
X<Y, X>Y, X+Y≤k, min(X,Y)≤t, max(X,Y)≤t, X>a and Y>b, or a complement.

The helper must then:

- print the written iterated integral with the correct limits, splitting the region into
  pieces when needed
- say which order of integration it used
- evaluate the probability
- include a "words → math" step, e.g.
  "fails if either fails" → min(X,Y) < t → 1 − P(X>t, Y>t)

## R3. Testing

Simulator regression tests (expected values verified with sympy) for both features on:

- the homework problems that use regions:
  - HW4 Q3 (device fails in first hour): f=(x+y)/8 on (0,2)², P(min(X,Y)<1) = 5/8
  - HW4 Q4 (discrete (x+y)/32): P(X>Y) = 3/32, P(X+Y≤3) = 1/4
  - HW4 Q5 (f=(2x+y)/4 on 0<x<1, 0<y<2): P(X<Y) = 19/24
- at least two joint CDF variants that are NOT from the homework, e.g.:
  - F(x,y) = x²y(x+y)/2 on the unit square
    (f = x(3x+4y)/2; F_X = x²(x+1)/2; F_Y = y(y+1)/2;
    P(1/4<X≤1/2, 1/2<Y≤1) = 25/256)
  - F(x,y) = (1−e^(−x))(1−e^(−2y)) for x,y>0
    (f = 2e^(−x−2y); P(0<X≤1, 0<Y≤1) = (1−e^(−1))(1−e^(−2)) ≈ 0.546572344)

(The values above were checked with sympy; builders must re-verify every expected value
with sympy inside the tests or a committed check script.)

## R4. Encyclopedia

Add pages, each citing the relevant Freund Ch. 3 sections (§5 Multivariate Distributions,
§6 Marginal Distributions; with definition/theorem numbers and printed page numbers):

- deriving f from F (mixed partial ∂²F/∂x∂y) and F from f (double integral up to (x,y))
- the rectangle formula P(a<X≤b, c<Y≤d) = F(b,d) − F(a,d) − F(b,c) + F(a,c)
- sketching the region to choose integration limits (order of integration, splitting a
  region, using a complement)
