# STA 431 Midterm II calculator suite

Start with **PRGM > STAM2 > ENTER > ENTER** after transferring all ten programs.
This is a TI-BASIC suite for the TI-84 Plus CE. It runs from PRGM, not APPS.
It uses the earlier suite's menu/encyclopedia design, with separate program names.

## Transfer

1. Open TI Connect CE on your computer and connect your calculator by USB.
2. Open Calculator Explorer. Drag **all ten `.8xp` files** from `calculator_files` onto the connected calculator. Send them as programs; do not send the Python or text source files.
3. On the calculator, open PRGM, choose STAM2, and run it. Keep all ten programs together because STAM2 calls the helper programs.
4. Run the concrete device checks below before the exam. If a program is archived and does not appear in the execution menu, unarchive it through the calculator's memory-management menu.

Official TI Connect CE software: https://education.ti.com/en/products/computer-software/ti-connect-ce-sw

Programs: STAM2 (launcher), M2DISC (finite tables), M2CONT (numeric integrals),
M2COV (linear combinations), M2MGF (MGFs), M2ENC (encyclopedia), M2HW (homework map),
M2RUN (homework input presets), M2SLICE (joint conditional slices),
and M2FMT (number formatting).

## Choose a solver

| Main menu | What it does |
|---|---|
| DISCRETE + JOINT | Finite PMFs/joint tables: manual rows or formula/grid entry, raw weights, c, means, variances, covariance, correlation, marginals, conditionals, events, functions, raw/central product moments. Up to30 rows; each (x,y) pair distinct. |
| DENSITY + INTEGRAL | Nonnegative finite-bound density/conditional slices; mean/variance, interval probability, transformed moments; double integrals using explicit bounds and outer Simpson quadrature; JOINT SLICE for numerical marginal/conditional values. |
| MGF TOOLS | Exponential-rate and quadratic-log-MGF templates with affine transformations; numerical moments for a typed MGF; transformed MGF values. |
| LINEAR COMBOS | One/two combinations of up to3 variables, means optional, including covariance and correlation. |
| ENCYCLOPEDIA | Definitions, method selection, derivation outlines, domain/support rules, formulas and cautions. |
| HOMEWORK MAP | All13 common/STA431 Homework4–5 questions, plus3 marked STA631 extensions, with input suggestions and independently derived targets. The LOAD + SOLVE submenu preloads models into the solvers. |

Encyclopedia keys: ENTER next page; LEFT previous; CLEAR topic menu.
Use BACK to return through solver menus. Enter fractions normally (e.g.1/2),
actual calculator X/Y variables in expressions, and the unary (-) key for a
negative number. Use the genuine `e^(` and comparison tokens, not typed word
approximations. A is the optional fixed parameter in a conditional slice.

## Fastest homework route: LOAD + SOLVE

From the main menu choose HOMEWORK MAP, then LOAD + SOLVE, then the homework
group and question. All16 common/431/optional631 problem models are supplied
as input presets. The same general calculators compute the results; answers
are not stored in the loader. Double-integral presets ask for an even N (try4).
For a changed exam problem, use the manual solvers instead of the original
homework preset.

## Fastest table entry: FORMULA/GRID

For Homework4Q1, choose DISCRETE + JOINT > FORMULA/GRID. Enter x values
`{1,2}`, y values `{1,2,3}`, and the expression `X+Y²`. The program generates
all6 pairs and normalizes their weights. For Homework5Q8 use `{1,2,3}` for
both lists with `X+Y`. For a univariate formula use the y list `{0}`; e.g.
x list `{1,2,3,4}` with `X²+X` gives Homework5Q1.
For a nonrectangular finite support, either multiply by its 0/1 support mask
where the formula is defined, or use manual rows and list only allowed pairs.
Do not evaluate an undefined expression and hope a zero mask will repair it.

## New full-table and joint-slice commands

DISCRETE + JOINT > MARG/CONDITIONAL > MARGINAL TABLES prints all marginal
values at once. INDEPENDENCE now also shows a violating pair and the two
probability values when numerical factorization fails. Use their exact
comparison in written work.

DENSITY + INTEGRAL > JOINT SLICE handles X GIVEN Y or Y GIVEN X. Enter a
joint shape q(X,Y), its known positive multiplier c (use1 if q is already
the joint PDF), the given value, and the remaining variable’s slice limits.
It reports the numerical marginal density and conditional moments. PDF AT
POINT and INTERVAL PROB answer further conditional queries; NEW GIVEN VALUE
reuses the model. A marginal density value is not P(Y=y), and the app does
not return a symbolic marginal-density formula.

## Concrete device checks

1. **Discrete mean/variance, HW5Q1.** UNIVARIATE PMF;4 rows x/weight=(1,2),(2,6),(3,12),(4,20). MOMENTS should give mean13/4, second227/20, variance63/80. Initial total40 and c1/40.
2. **Conditional moments, HW5Q7.** DENSITY + INTEGRAL >1D PDF OR SLICE. q(X)=X+A, fixed A=1/2, lower0, upper1. MEAN+VARIANCE should give7/12,5/12,11/144.
3. **Double integral, HW4Q5.** q=(2X+Y)/4, A0, x0..1, ylowerX, yupper2, g1, N4. RAW I should be approximately19/24 at N4 andN8. Do not normalize this event region to1.
4. **Three variables, HW5Q6.** LINEAR COMBOS >ONE COMBINATION >VAR/COV ONLY; n3; variances4,9,2; covariances12=1,13=-1,23=0; coefficients3,-2,1; offset0. Variance56; mean is not reported because none was supplied.
5. **MGF transformation, HW5Q4.** MGF TOOLS >QUADRATIC LOG MGF; C4,D8; scale1/4,shift-1. Original mean4,variance16; transformed mean0,variance1; transformed quadratic coefficient1/2.
6. **Joint conditional, HW5Q8.** Enter9 rows for x,y in1,2,3 with weight x+y. MOMENTS: both means13/6, product14/3,covariance-1/36. MARG/CONDITIONAL >Y GIVEN X with X1 gives conditional mean20/9.

## What the numerical tools mean

For a full unnormalized density q, the tool divides moments by its total mass.
For a conditional slice, this automatically divides by the correct slice mass.
For double integrals, RAW I means integral(q) and RAW J means integral(q*g).
**A normalized PDF integrated over an event gives its probability as RAW I.**
Use NORMALIZE FULL S only when the entered region is the entire support of the
model you mean to normalize. The two resolutions are a convergence check, not a
rigorous error guarantee. Polynomial homework cases are especially favorable.

Generic MGF derivatives are explicitly approximate and use h=.01 and.005.
The expression must be defined at0 and all four sample points. Use the exact
exponential/quadratic templates for HW5Q3/Q4. These checks cannot prove MGF
existence, domain or uniqueness; those explanations are in the encyclopedia.
The programs do not perform symbolic differentiation or integration.

## State and validation

Programs use scalar A–Z, theta, strings, and private M2 lists. Existing L1–L6 and
Y= equations are left alone; private lists are removed when their module exits
where applicable. Do not depend on previously stored scalar/string values after
running a tool. Existing STA431/STAE/STACNT/STARV programs are not replaced.

Malformed expressions, undefined operations, or extreme overflow can still
produce a native calculator error. TI-BASIC does not provide a general exception
handler. If that happens, quit, correct the expression/bounds, and restart.

The included source is tokenized for TI-84 Plus CE and checked by token/static
lints, a token-stream simulator, homework regressions, and reference-page
navigation checks. This is off-device verification, not a physical-calculator
qualification. Test the actual transferred programs using the cases above.

## Rebuild

Inside `source_code`, install `requirements.txt` into a Python environment, then
run `python tools/build_package.py /path/to/new/package` to regenerate the
programs, run validation, and create a transfer directory. The simulator's
integrator can be more accurate than the CE's default; both remain numerical.
