# STA 431 Midterm II calculator suite

Start with **PRGM > STAM2 > ENTER** after transferring all 14 programs.
This is a TI-BASIC suite for the TI-84 Plus CE. It runs from PRGM, not APPS.
It follows the Midterm I suite's menu and encyclopedia style, with separate program names,
and it covers STA 431 material only.

## Transfer

1. Open TI Connect CE on your computer and connect your calculator by USB.
2. Open Calculator Explorer. Drag **all 14 `.8xp` files** from `calculator_files` onto the
   connected calculator. Send them as programs; do not send the Python or text source files.
3. Archive the Midterm I programs first (see **Memory** below), then run STAM2 from PRGM.
   Keep all 14 programs together, because STAM2 calls the helper programs.
4. Run the device checks below before the exam.

Official TI Connect CE software: https://education.ti.com/en/products/computer-software/ti-connect-ce-sw

The 14 programs: STAM2 (launcher), M2DISC (finite tables), M2JNT (joint densities: support,
events and written limits), M2GL (integration library used by M2JNT), M2PLY (polynomial and
text library used by M2JNT), M2CONT (densities and numeric integrals), M2SLICE (joint
conditional slices), M2MGF (MGFs), M2COV (linear combinations), M2ENC (encyclopedia), M2EXAM
(FIND MY SOLVER question finder), M2HW (homework walkthroughs), M2RUN (homework practice data)
and M2FMT (number formatting).

## Memory

The Midterm I suite takes about 139 KB and this suite about 85 KB, but the CE has only about
154 KB of user RAM. Archive the Midterm I programs (STA431, STAE1, STAE2, STAE3, STAHNT, STACNT,
STAPRB, STARV, STAFMT) so they move to archive memory:

1. Press **2nd MEM** (above +), choose **2:Mem Mgmt/Del**, then **7:Prgm**.
2. Move to a Midterm I program and press **ENTER**: a `*` appears next to it, which means it is
   archived. ENTER again toggles it back.
3. Keep every M2... program and STAM2 **unstarred** (in RAM). STAM2 runs its helpers with
   `prgmNAME`, and archived programs cannot be run that way.

To use Midterm I again, unstar its programs and star the Midterm II ones. Press-to-Test mode
disables all programs, so do not start an exam session in Press-to-Test if you need the suite.

## Modes

STAM2 sets **Float**, **Normal** and **Real** when it starts, so fractions, decimals and error
checks behave as the programs expect. It does not change any other setting. Keep the graph mode
on **FUNCTION** (MODE screen): only then does the X,T,θ,n key type X (in PAR, POL or SEQ mode it
types T, θ or n). HOW TO ENTER shows this as `X=X,T,θ,n(FUNC)`.

## Main menu

`STA431 MIDTERM II`: ENCYCLOPEDIA, SOLVERS, HELP, HOMEWORK PRACTICE, QUIT.

| Menu | Item | What it does |
|---|---|---|
| ENCYCLOPEDIA | (topic menus) | Definitions, method choice, derivation outlines, support rules, formulas and cautions, with Freund citations. Keys: ENTER next page, LEFT previous, CLEAR topic menu. |
| SOLVERS | DISCRETE TABLE | Finite PMFs and joint tables: manual rows or FORMULA/GRID entry, raw weights, c, means, variances, covariance, correlation, marginals, conditionals, events, functions, raw and central product moments. Up to 30 rows; each (x,y) pair distinct. |
| SOLVERS | JOINT DENSITY | A joint PDF f = c·q(x,y): type q, pick the support (rectangle, the two triangles, x+y<k, the quadrant, custom linear bounds or a curved region), and it prints the total and c. EVENTS + LIMITS then gives any event's probability with the words → math step, the written iterated integral (c, q, the order, every piece's limits and value), both orders of integration, complements and P(A\|B). Exact fractions for a polynomial q on a straight-edged finite support. `ᴇ99` means infinity. See **Joint densities** below. |
| SOLVERS | DENSITY+INTEGRAL | Finite-bound densities and conditional slices: mean and variance, interval probability, E[g(X)], raw/central moments; DOUBLE INTEGRAL with explicit bounds and outer Simpson quadrature (NEW N reruns the same region with another N); JOINT SLICE for numeric marginal and conditional values. Every bound must be finite (see **Finite bounds** below). |
| SOLVERS | MGF TOOLS | Exponential-rate and quadratic-log MGF templates with Z=aX+b; numeric moments for a typed M(t); transformed MGF values. |
| SOLVERS | LINEAR COMBOS | One or two linear combinations of up to 3 variables, means optional, with covariance and correlation. |
| HELP | FIND MY SOLVER | Describe the given data and what is asked; it shows the recipe and opens the matching solver. |
| HELP | HOW TO ENTER | Two pages: the keys (X in FUNC mode, Y = ALPHA 1, TEST menu, `𝑒^(`, `√(`, the (-) key, fractions, lists, `ᴇ99` for infinity, which only JOINT DENSITY accepts in this version, what to do on an error) and Freund notation (g(x), h(y), f(x\|y), w(y\|x), μ'r, μr, σXY, ρ). ENTER goes to the next page; CLEAR or LEFT on page 1 goes back to HELP. |
| HELP | LIMITS + CAVEATS | What still needs your own reasoning, and the size limits: table rows ≤ 30, linear combinations of ≤ 3 variables, finite bounds in DENSITY+INTEGRAL. |
| HOMEWORK PRACTICE | WALKTHROUGHS | The STA 431 Homework 4 and 5 problems: model and input strategy. |
| HOMEWORK PRACTICE | LOAD PRACTICE DATA | Loads a homework problem's data into a solver (13 presets). The solver computes every number; no answers are stored. |
| QUIT | | Clears the screen and ends. |

Use BACK to return through the menus. Enter fractions with the divide key (for example 1/2),
the calculator's X and Y variables in expressions (X is the X,T,θ,n key; Y is ALPHA 1), and the
(-) key for a negative number. Use the real `𝑒^(` (2nd LN) and the comparison tokens from
2nd MATH (TEST). A is the optional fixed parameter in a conditional slice. If the calculator shows
an error, choose 1:Quit, then fix the expression or bounds and start again.

## Practice data: HOMEWORK PRACTICE > LOAD PRACTICE DATA

Choose the homework group and question. All 13 STA 431 problem models (HW4 Q1 to Q5, HW5 Q1 to
Q8) are supplied as input presets. The general solvers compute the results; the loader stores no
answers. HW4 Q2, Q3 and Q5 load the density and its rectangle into JOINT DENSITY: you land on
its menu with the model summary already shown, so pick EVENTS + LIMITS and the event (MIN/MAX VS t
for Q3, X<Y for Q5). For a changed exam problem, enter your own data in SOLVERS instead of loading a
preset.

## Fastest table entry: FORMULA/GRID

For Homework 4 Q1, choose SOLVERS > DISCRETE TABLE > FORMULA/GRID. Enter x values `{1,2}`,
y values `{1,2,3}`, and the expression `X+Y²`. The program generates all 6 pairs and normalizes
their weights. For Homework 5 Q8 use `{1,2,3}` for both lists with `X+Y`. For a one-variable
formula use the y list `{0}`; for example the x list `{1,2,3,4}` with `X²+X` gives Homework 5 Q1.
For a support that is not a full grid, either multiply by a 0/1 support mask where the formula is
defined, or enter manual rows and list only the allowed pairs. Do not evaluate an undefined
expression and hope a zero mask will repair it.

## Joint densities: SOLVERS > JOINT DENSITY

1. **NEW MODEL.** Type the shape q(X,Y) (leave out an unknown constant c; X is the X,T,θ,n key,
   Y is ALPHA 1). Then pick the support:
   * `RECT a<X<b,c<Y<d` asks for a, b, c, d;
   * `TRI a<Y<X<b` and `TRI a<X<Y<b` ask for the two ends;
   * `X,Y>0 AND X+Y<k` asks for k; `QUADRANT X,Y>0` asks nothing;
   * `CUSTOM BOUNDS`: `X OUTER, Y(X)` (a<x<b with lower and upper y typed as lines in X, for example
     `X/2` and `1+X/2`), `Y OUTER, X(Y)` (the same with the letters swapped), or `CURVED (NUMERIC)`
     (any formulas in X, for example `0` and `X²`).
   Type `ᴇ99` (2nd , 9 9) for an infinite end and `⁻ᴇ99` for minus infinity; every finite number must
   be below 1E5 in size. The summary screen shows q, the support as an outer and an inner range
   (`0<x<1` / `0<y<x`), TOTAL ∫∫q, c = 1/TOTAL (or `q IS ALREADY A PDF`), and `EXACT (POLYNOMIAL)`
   or `NUMERIC, 2 PASSES AGREE`. The model is kept until you choose NEW MODEL or BACK.
2. **EVENTS + LIMITS.** `X<Y OR X>Y`, `X+Y≤k OR X+Y≥k`, `MIN/MAX VS t` (min(X,Y)≤t is "fails if
   either fails", max(X,Y)≤t "fails only if both fail"), `X>a AND Y>b`, `MORE EVENTS` (aX+bY≤c,
   |X-Y|≤k or >k, the joint CDF X≤s AND Y≤t, a rectangle, a<X<b only, and `COMPLEMENT OF…`), and
   `P(A|B)` (pick A, then the given event B). Three kinds of screen follow, in this order:
   * `EVENT SETUP`: the words → math step, for example `FAILS IF EITHER FAILS`, `=> min(X,Y)≤1`,
     `=1-P(X>t,Y>t)`.
   * `LIMITS`: the integral to copy, `P=∫∫ c*q(x,y) dy dx`, then `c=`, `q=` and
     `ORDER dy dx (x OUTER)`, then one piece per strip: `x FROM 0 TO 1/2`, ` y FROM 0 TO x`,
     ` PIECE=1/8`. Add the pieces to get the probability. A region that changes its upper or lower
     edge is split into pieces automatically.
   * `RESULT`: the probability with the complement arithmetic (`=1-3/8`, `=5/8`) and the label
     EXACT, `NUMERIC, 2 PASSES AGREE`, or `APPROX - NOT CONVERGED` with the change between passes.
3. **EVENT RESULT menu.** `REVERSE ORDER` integrates the same event dx dy (y outer) and prints those
   limits; the probability must agree. `COMPLEMENT 1-P` prints `P(NOT A)=1-P(A)` for the last event.
   `NEW EVENT` keeps the model.
4. **Complements and conditional events.** `COMPLEMENT OF…` (in MORE EVENTS) makes the next event
   A' (Freund's notation for "not A"): SETUP shows `NOT A => A'` and `P(A')=1-P(A)`, LIMITS shows
   the limits of A, and RESULT shows `P(A')=1-P(A)=1-…`. `P(A|B)` integrates the regions A AND B and
   B (and A when B is a complement) and shows `P(A AND B)`, `P(B)` and their ratio; P(B)=0 gives
   `P(B)=0 - UNDEFINED`. A condition on a VALUE (given X=x) is a slice, not an event.
5. **Exact and numeric.** A polynomial q on a finite support with straight edges is integrated
   exactly (fractions). Anything else (an exponential q, an infinite support, a curved region)
   is integrated numerically twice with finer panels; a fraction appears only when both passes
   agree to 1E-8, and an infinite end is cut where q has fallen below 1E-13 of its peak
   (`TAIL MAY BE HEAVY` if that never happens before 4096). A polynomial q on an infinite support is
   refused, and a negative q shows `q<0 SOMEWHERE` / `NOT A VALID PDF`. On the calculator a numeric
   event takes about 10 to 40 seconds (`WORKING k/n` counts the strips).
6. **Curved supports** offer one event, `CURVED SUB-REGION`: a<x<b with lower and upper y formulas
   in X, clipped to the support.

FORMULAS, MOMENTS + COV, GIVEN A VALUE and INDEP + CDF arrive with the next update; for now they show
`COMING IN THIS VERSION` and return to the menu.

## Full tables and joint slices

SOLVERS > DISCRETE TABLE > (your data) > MARG/CONDITIONAL > MARGINAL TABLES prints every marginal
value at once. INDEPENDENCE also shows a violating pair and the two probability values when the
factorization fails. Use their exact comparison in written work.

SOLVERS > DENSITY+INTEGRAL > JOINT SLICE handles X GIVEN Y or Y GIVEN X. Enter a joint shape
q(X,Y), its known positive multiplier c (use 1 if q is already the joint PDF), the given value,
and the remaining variable's slice limits. It reports the numeric marginal density value and the
conditional moments. PDF AT POINT and INTERVAL PROB answer further conditional questions; NEW
GIVEN VALUE reuses the model. A marginal density value is not P(Y=y), and this version does not
give a symbolic marginal-density formula.

## Device checks

These use Freund examples, mock-exam models and small made-up tables (not homework answers). Each
expected value can be checked by hand.

1. **Discrete mean and variance.** SOLVERS > DISCRETE TABLE > UNIVARIATE PMF; 3 rows, x and
   weight = (0,1), (1,2), (2,1). The raw total is 4 and c = 1/4; MOMENTS gives E[X] 1,
   E[X^2] 3/2, VAR(X) 1/2.
2. **Conditional slice, Freund Ex20.** SOLVERS > DENSITY+INTEGRAL > 1D PDF OR SLICE. q(X) =
   `2/3*(X+2A)` (f(x,y) = 2/3(x+2y) with y = A), fixed A = 1/2, lower 0, upper 1. MEAN+VARIANCE
   gives 5/9, 7/18, 13/162.
3. **Exact double integral, Freund Ch4 Ex16.** SOLVERS > DENSITY+INTEGRAL > DOUBLE INTEGRAL.
   q = 2, A 0, x from 0 to 1, y lower 0, y upper `1-X`, g `X*Y`, N 8. RAW I is 1 and RAW J
   (E(XY)) is 1/12 at N 8 and at N 16, with CHANGE 0 and no NOT CONVERGED row.
4. **Convergence warning.** Same tool: q = `6X`, x 0 to 1, y lower `X`, y upper 1, g `X*Y`, N 4.
   RAW J shows decimals (.398438, then .399902) and `NOT CONVERGED - RAISE N`. Choose NEW N and
   type 32: RAW J is .4 at N 32 and N 64, CHANGE IN J is about 3.6E-7 and the row reads
   `CHANGE<1ᴇ⁻6 - USE DECIMAL`. This outer integrand is quartic, so CHANGE never becomes exactly 0.
5. **Finite bounds.** SOLVERS > DENSITY+INTEGRAL > 1D PDF OR SLICE with q = `𝑒^(⁻X)`, A 0,
   lower 0, upper `ᴇ99`. The program must show `BOUNDS MUST BE FINITE` and ask again; type 0 and
   20. MEAN+VARIANCE then gives mean 1 (and 1.999999, .999999: rerun with upper 40 to see 2 and 1).
6. **Three variables.** SOLVERS > LINEAR COMBOS > ONE COMBINATION > VAR/COV ONLY; n 3; variances
   2, 3, 4; covariances 12 = 1, 13 = 0, 23 = -1; coefficients 1, 2, -1; offset 0. VAR(U) is
   2 + 4(3) + 4 + 2(2)(1) + 2(-2)(-1) = 26; no mean is reported because none was supplied.
7. **MGF transformation.** SOLVERS > MGF TOOLS > QUADRATIC LOG MGF; C 1, D 2 (normal, mean 1,
   variance 4); scale 3, shift -1. Original mean 1, variance 4; Z = 3X - 1 has mean 2, variance
   36 and the transformed quadratic coefficient H = 18.
8. **Typed MGF, uniform(0,2).** SOLVERS > MGF TOOLS > TYPE MGF NUMERIC with
   `(𝑒^(2X)-1)/(2X)`, scale 1, shift 0. It must not stop with an error. The check screen ends with
   `RELATIVE ERROR EST <1ᴇ⁻6`; E(X) is 1 and VAR(X) is .333333. Then EVAL Mz AT t with t = 0
   shows 1 and `Mx(0)=1 BY DEFINITION`. For Mock 5 Q5's (1-2t)^-2 (type `(1-2X)^⁻2`, scale -3,
   shift 2) it gives E(X) 4, VAR(X) 8, E(Z) -10, VAR(Z) 72.
9. **Joint table and conditional.** SOLVERS > DISCRETE TABLE > FORMULA/GRID; x values `{0,1}`,
   y values `{0,1}`, q `X+Y+1` (weights 1, 2, 2, 3). MOMENTS: both means 5/8, E[XY] 3/8,
   covariance -1/64. MARG/CONDITIONAL > Y GIVEN X with X = 1 gives P(Y=0|X=1) 2/5,
   P(Y=1|X=1) 3/5 and conditional mean 3/5.
10. **Joint density, Mock Midterm II Q2.** SOLVERS > JOINT DENSITY > NEW MODEL, q = `X`, support
   TRI a<Y<X<b with a 0, b 1: TOTAL ∫∫q=1/3 and c=3. EVENTS + LIMITS > X+Y≤k OR X+Y≥k > X+Y≤k with
   k 1: two pieces, `x FROM 0 TO 1/2` / ` y FROM 0 TO x` / ` PIECE=1/8` and `x FROM 1/2 TO 1` /
   ` y FROM 0 TO 1-x` / ` PIECE=1/4`, so P(X+Y≤1)=3/8. REVERSE ORDER shows one piece
   `y FROM 0 TO 1/2` / ` x FROM y TO 1-y` and 3/8 again.
11. **Series and parallel, Mock 4 Q5.** q = `2/3*(X+2Y)` on RECT 0, 1, 0, 1. MIN/MAX VS t >
   min(X,Y)≤t with t = 1/2: SETUP shows `FAILS IF EITHER FAILS` and `=1-P(X>t,Y>t)`; RESULT
   `=1-3/8`, `=5/8`. max(X,Y)≤t with t = 1/2 gives 1/8. COMPLEMENT 1-P after the min event gives 3/8.
12. **Numeric quadrant.** q = `2𝑒^(⁻X-2Y)` (2nd LN for 𝑒^(), QUADRANT X,Y>0: TOTAL ∫∫q=1 and
   `NUMERIC, 2 PASSES AGREE`. X<Y OR X>Y > X>Y gives 2/3 in both orders (limits `x FROM 0 TO INF` /
   ` y FROM 0 TO x`, then `y FROM 0 TO INF` / ` x FROM y TO INF`); X+Y≤k with k 1 gives .399576.
13. **Complement and conditional, Mock 4 Q4 / Q3.** q = `X+2Y` on RECT 0, 2, 0, 1 (c=1/4): MORE
   EVENTS > COMPLEMENT OF… > X+Y≤k with k 1 shows `P(A')=1-P(A)`, `=1-1/8`, `=7/8`. For q = `X*Y` on
   TRI a<X<Y<b with 0, 1 (c=8): P(A|B) with A = a<X<b ONLY 0, 1/2 and B = aX+bY≤c with a 0, b -1,
   c -1/2 (that is Y≥1/2) gives P(A AND B)=3/8, P(B)=15/16 and P(A|B)=2/5.

## What the numeric tools mean

For a full unnormalized density q, the tool divides moments by its total mass. For a conditional
slice this automatically divides by the correct slice mass. For double integrals, RAW I means
integral(q) and RAW J means integral(q*g). **A normalized PDF integrated over an event gives its
probability as RAW I.** Use NORMALIZE FULL S only when the entered region is the whole support of
the model you mean to normalize.

The DOUBLE INTEGRAL runs N and 2N. When the two results differ by more than 1E-9 (relative), every
RAW I, RAW J and NORMALIZE value is shown as a decimal, never a fraction, with one of these rows:

* `NOT CONVERGED - RAISE N`: choose NEW N in the DOUBLE INTEGRAL menu (it keeps the region) and
  try 16, 32, ... until the row changes or disappears.
* `CHANGE<1ᴇ⁻6 - USE DECIMAL`: N and 2N already agree to better than 1E-6; report the 6-place
  decimal. This is normal when the outer integrand is of degree 4 or more (for example E(XY) on a
  triangle): Simpson's rule is exact only up to degree 3, so CHANGE never becomes exactly 0.
* `N=100 IS MAX - USE DECIMAL`: N cannot go higher (N ≤ 100); report the decimal and say it is a
  numerical approximation.

Start with N = 8. The run time grows with N: N = 100 evaluates about 300 inner integrals and can
take minutes on the calculator. `I=0 - CHECK q AND BOUNDS` appears when RAW I is exactly 0.
Agreement of two resolutions is a convergence check, not a proof of accuracy.

**JOINT DENSITY** runs every non-polynomial (or infinite, or curved) integral twice, with 5 and
then 7 graded panels in each direction. Matching results within 1E-8 print a fraction; otherwise
the result is a decimal with `APPROX - NOT CONVERGED` and the change. A kink inside the region (for
example a curved sub-region whose bound switches from one curve to another) is the usual reason.

**Finite bounds.** This version's DENSITY+INTEGRAL tools (1D PDF OR SLICE, DOUBLE INTEGRAL, JOINT
SLICE) need finite bounds with |bound| < 1E5, including curved y limits at every x. Typing `ᴇ99`
(or any huge number) shows `BOUNDS MUST BE FINITE` and asks again. For an infinite end, type a
cutoff T where q is essentially 0 (for `𝑒^(⁻X)` about 20 in DOUBLE INTEGRAL, 40 in the 1-D tools),
then rerun with 2T: if the answer does not change, the cutoff is large enough.

TYPE MGF NUMERIC never evaluates M at t = 0 (an MGF like the uniform's divides by t there), and
EVAL Mz AT t uses Mx(0) = 1 when a·t = 0. It first checks that M(.001) is within .05 of 1. It
uses central differences at h = .01, .005 and .0025 and reports the Richardson extrapolation of
the three (it cancels the h² and h⁴ error terms). The check screen shows the plain h = .005 value
next to the Richardson value. `RELATIVE ERROR EST <1ᴇ⁻6` means the estimated error of the reported
value is below 1E-6 (relative); otherwise it shows `WARNING STEP-SIZE CHANGE`. Both the warning
and a failed M(.001) check usually mean a large mean or spread (for example an exponential with
mean 20 or more): type M(t/10) instead, for example `1/(1-2X)` for 1/(1-20t), and multiply the
scale a by 10, so the Z=aX+b screen shows the moments of the original X. Use the exact
exponential and quadratic templates when they fit. These checks cannot prove MGF existence,
domain or uniqueness; those explanations are in the encyclopedia. The programs do not do symbolic
differentiation or integration.

## State and validation

Programs use the letters A to Z, θ, strings and private lists whose names start with M2. The
lists L1 to L6 and the Y= equations are left alone; private lists are removed when a solver is
left through BACK. Do not rely on stored letters or strings after running a tool. The Midterm I
programs (STA431, STAE1 to STAE3, STAHNT, STACNT, STAPRB, STARV, STAFMT) are not replaced.

A malformed expression, an undefined operation or an overflow can still produce a calculator
error. TI-BASIC has no general error handler. If it happens, choose 1:Quit, correct the
expression or bounds, and restart.

The source is tokenized for the TI-84 Plus CE and checked by two linters (0 errors, 0 warnings),
a token-stream simulator, homework regressions with sympy-computed targets, a full menu-tree walk
from STAM2, and reference-page navigation checks. This is off-device verification, not a
physical-calculator qualification. Test the transferred programs with the cases above.

## Rebuild

Inside `source_code`, install `requirements.txt` into a Python environment, then run
`python3 tools/build_package.py /path/to/new/package`. It regenerates the generated programs,
runs both linters and every test, rebuilds the 14 `.8xp` files, checks the memory budget
(118,000 bytes) and writes the package and its .zip. `python3 tools/play.py` drives the suite key
by key in the simulator (for example `play.py add S m:SOLVERS m:BACK m:QUIT`).
