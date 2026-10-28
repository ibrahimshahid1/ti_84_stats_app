# STA 431 Midterm II: exam-day keystroke card (STAM2 suite)

Start with **PRGM > STAM2 > ENTER**. Every route below starts at the main menu
`STA431 MIDTERM II`. Menu items can be picked by number or by arrowing to them. The worked
example under each type is a homework problem. Change the numbers or functions shown in
`«brackets»` for a new question.

Notation: `SOLVERS > JOINT DENSITY` means pick SOLVERS, then JOINT DENSITY. `type «q»` means type
the expression at the prompt and press ENTER. Screens are shown in short form, as `SCREEN: line /
line`. Each pause screen goes on with ENTER.

---

## 0. Entry rules (read once before the exam)

| You want | Press | Pitfall |
|---|---|---|
| X | `X,T,θ,n` (graph MODE must be FUNC) | In PAR/POL/SEQ mode this key types T, θ or n |
| Y | `ALPHA 1` | |
| a negative number, e.g. -1 | the `(-)` key, shown as `⁻1` | The subtraction key `-` at the start of an entry gives ERR:SYNTAX. Choose 1:Quit and start the solver again |
| fraction 1/4 | `1 ÷ 4` | Results come back as exact fractions when possible |
| list {1,2,3} | `2nd (` … `2nd )` with commas | A single number where a list is asked gives ERR:DATA TYPE |
| x², e^( | `x²` key, `2nd LN` | |
| < > ≤ ≥ | `2nd MATH` (TEST) | Use these for discrete EVENT PROB, e.g. `X+Y≤3` |
| infinity | `2nd , 9 9` → `ᴇ99`; minus infinity `(-) 2nd , 9 9` → `⁻ᴇ99` | Only JOINT DENSITY and CDF OF X AND Y accept ᴇ99. DENSITY+INTEGRAL wants a finite cutoff |
| the constant c | **leave it out**: type q only, e.g. `X+Y²` for c(x+y²) | JOINT DENSITY says `q MAY USE ONLY X AND Y`. DISCRETE FORMULA/GRID shows a misleading `WEIGHTS MUST BE ≥0` if you type C |
| a known constant | type it with the brackets: `(1/4)(2X+Y)`, `(2X+Y)/12`, `(6/5)(X+Y²)` | Implicit multiplication works. The app then shows `q IS ALREADY A PDF`, c=1 |

Reading results: `1/2x` on a result screen means (1/2)·x, not 1/(2x). Write it as x/2 on paper.
The app says `EXACT (POLYNOMIAL)` when the answer is an exact fraction. If it says `NUMERIC` or
`APPROX`, report the decimal.

If anything errors: choose **1:Quit**, run STAM2 again, and retype (nothing is lost but the
current entry).

---

## Type 1. Discrete joint PMF given by a formula on a grid
*(c, marginals, conditional PMF, independence, events, E(X), E(Y), E(XY), Cov, E(Y|X=x))*

**Route:** `SOLVERS > DISCRETE TABLE > FORMULA/GRID`

1. `x VALUES LIST?` type `{«x values»}`
2. `y VALUES LIST?` type `{«y values»}`
3. `q(X,Y)?` type `«formula without c»`
4. Screen: `RAW TOTAL= «S»` / `c=1/SUM(w)= «1/S»` → **answer for c**.
5. The `TABLE TOOLS` menu stays open. Pick what is asked:

| Asked | Menu path from TABLE TOOLS | Screen |
|---|---|---|
| marginal PMFs g(x), h(y) | `MARG/CONDITIONAL > MARGINAL TABLES` | `X MARGINAL TABLE` rows `x | g(x)`, then `Y MARGINAL TABLE` |
| f(x\|y₀) (X given Y) | `MARG/CONDITIONAL > X GIVEN Y`, type y₀ | `CONDITIONAL DISTRIBUTION` rows `x | f(x|y₀)`, then `MEAN=` (E(X\|Y=y₀)), `SECOND MOMENT=`, `VARIANCE=` |
| w(y\|x₀) (Y given X) | `MARG/CONDITIONAL > Y GIVEN X`, type x₀ | same layout, rows `y | w(y|x₀)` |
| independent? | `MARG/CONDITIONAL > INDEPENDENCE` | `NUMERIC FACTORIZATION FAIL` = **NOT independent**. Next screen `COUNTEREXAMPLE PAIR`: line 1 = x, line 2 = y, then `JOINT p(x,y)=` and `pX(x)*pY(y)=`. Write "f(x,y) ≠ g(x)h(y) at this pair" |
| P(event) | `EVENT PROB > P(EVENT)`, type the event, e.g. `X>Y`, `X+Y≤3` | The result is labelled `P(EVENT | GIVEN)=` even with no given event. It is the plain P(event) |
| P(A\|B) | `EVENT PROB > P(EVENT|GIVEN)` | |
| E(X), E(Y), Var, E(XY), Cov, ρ | `MOMENTS` | `X MOMENTS`, `Y MOMENTS`, then `E[XY]=`, `COV(X,Y)=`, `CORRELATION=` |
| E[g(X,Y)] | `FUNCTION g(X,Y)` | |

Strict or non-strict matters for a PMF: `X+Y<3` and `X+Y≤3` give different answers.
Use FORMULA/GRID for any full grid of up to 30 pairs. For a support that is not a full grid, use
`JOINT X,Y` and type only the allowed pairs.

**Worked example HW4-1** (c(x+y²), x∈{1,2}, y∈{1,2,3}):
`SOLVERS > DISCRETE TABLE > FORMULA/GRID`, `{1,2}`, `{1,2,3}`, `X+Y²` → c = **1/37**.
`MARG/CONDITIONAL > MARGINAL TABLES` → g: 17/37, 20/37; h: 5/37, 11/37, 21/37.
`INDEPENDENCE` → FAIL, pair (1,3): 10/37 ≠ 357/1369 → dependent.
`X GIVEN Y`, `2` → f(1|2)=5/11, f(2|2)=6/11.
(play.py: `m:SOLVERS "m:DISCRETE TABLE" m:FORMULA/GRID i:{1,2} i:{1,2,3} i:X+Y² m:MARG/CONDITIONAL "m:MARGINAL TABLES" m:INDEPENDENCE "m:X GIVEN Y" i:2`)

**HW4-4** ((x+y)/32 on {1,2}×{1,2,3,4}): grid `{1,2}`, `{1,2,3,4}`, `X+Y` (c = 1/32 shown), then
`EVENT PROB > P(EVENT)` `X>Y` → **3/32**. ENTER returns to EVENT TYPE: `P(EVENT)` `X+Y≤3` → **1/4**.

**HW5-8** ((x+y)/36 on {1,2,3}²): grid `{1,2,3}`, `{1,2,3}`, `X+Y`. `MOMENTS` → E(X)=E(Y)=**13/6**,
E[XY]=**14/3**, COV=**⁻1/36**. `MARG/CONDITIONAL > Y GIVEN X`, `1` → 2/9, 1/3, 4/9; MEAN=**20/9**.

The marginal *formula* (e.g. g(x)=(3x+14)/37) is not printed. Write it by hand from the sum
over y, and check it against the table values.

---

## Type 2. One-variable discrete PMF with a constant c
*(c, E(X), Var(X), E[g(X)])*

**Route:** `SOLVERS > DISCRETE TABLE > FORMULA/GRID`. The y list is `{0}`.

`{«x values»}`, `{0}`, `«formula in X»` → `c=1/SUM(w)`. Then `MOMENTS` → `E[X]=`, `E[X^2]=`, `VAR(X)=`.
`FUNCTION g(X,Y)` with e.g. `1/(X+1)` gives E[g(X)].
(If c is given and there is no formula, use `UNIVARIATE PMF` and type the rows.)

**HW5-1** (c(x²+x), x=1..4): `{1,2,3,4}`, `{0}`, `X²+X` → c=**1/40**; MOMENTS → E[X]=**13/4**,
E[X²]=227/20, VAR=**63/80**.

---

## Type 3. Joint PDF: c, marginal PDF, conditional PDF formula
**Route:** `SOLVERS > JOINT DENSITY > NEW MODEL`

1. `q(X,Y)?` type `«q without c»`.
2. `SUPPORT` menu: pick the shape.
   * `RECT a<X<b,c<Y<d`: type a, b, c, d (x low, x high, y low, y high)
   * `TRI a<Y<X<b` (0<y<x<1 style), `TRI a<X<Y<b`: type the two ends
   * `X,Y>0 AND X+Y<k`: type k. `QUADRANT X,Y>0` (e.g. exponentials) asks nothing
   * `CUSTOM BOUNDS > X OUTER, Y(X)`: a, b, then y-lower and y-upper as lines in X
3. Screen `MODEL f=c*q`: `q=…` / support / `TOTAL ∫∫q=«T»` / `c=«1/T»` → **answer for c**.
4. `FORMULAS` (polynomial q, straight edges):
   * `g(x) MARGINAL`: `FOR a<x<b` / `y FROM … TO …` / `g(x)=…` / `0 ELSEWHERE`
   * `h(y) MARGINAL`: the same with x and y swapped
   * `f(x|y) CONDITIONAL` (X given Y), `w(y|x) CONDITIONAL` (Y given X): `f(x|y)=(N)/(D)` /
     `FOR …` / `AND …` / `ONLY WHERE h(y)>0`
   * `E(Y|X=x) FORMULA`, `E(X|Y=y) FORMULA`
   BACK returns to the JOINT DENSITY menu, and the model stays loaded.

**HW4-2** (c(2x+y), 0<x<1, 0<y<2): `NEW MODEL`, `2X+Y`, `RECT`, `0`,`1`,`0`,`2` → TOTAL 4, c=**1/4**.
`FORMULAS > h(y) MARGINAL` → `h(y)=1/4+1/4y` FOR 0<y<2 → **(1+y)/4**.
`f(x|y) CONDITIONAL` → **(2x+y)/(1+y)**, 0<x<1, for 0<y<2.
(play.py: `m:SOLVERS "m:JOINT DENSITY" "m:NEW MODEL" i:2X+Y m1 i:0 i:1 i:0 i:2 m:FORMULAS "m:h(y) MARGINAL" "m:f(x|y) CONDITIONAL"`)

**HW5-7 (a)(b)** (x+y on the unit square): `X+Y`, RECT `0,1,0,1` → h(y)=**1/2+y**,
f(x|y)=**(2x+2y)/(1+2y)**.

---

## Type 4. Joint PDF: probability of an event (and the written integral)
**Route:** load the model as in Type 3, then `EVENTS + LIMITS` and pick:

| Words in the question | Menu |
|---|---|
| P(X<Y), P(X>Y) ("first before second") | `X<Y OR X>Y` |
| P(X+Y≤k), P(X+Y<k), P(X+Y≥k) | `X+Y≤k OR X+Y≥k`, type k (for a PDF, < and ≤ are the same) |
| "device fails if **either** fails" by time t (series) | `MIN/MAX VS t > min(X,Y)≤t`, type t |
| "fails only when **both** fail" (parallel) | `MIN/MAX VS t > max(X,Y)≤t`, type t |
| P(X>a, Y>b) | `X>a AND Y>b` |
| aX+bY≤c, \|X−Y\|≤k, X≤s AND Y≤t (= F(s,t)), a rectangle, a<X<b only, NOT A | `MORE EVENTS` |
| P(A \| B) for two events | `P(A|B)` |

Three screens follow:
* `EVENT SETUP`: the words → math step (e.g. `FAILS IF EITHER FAILS` / `=> min(X,Y)≤1` / `=1-P(X>1,Y>1)`)
* `LIMITS`: the integral to copy (`c=`, `q=`, `ORDER dy dx`, `x FROM … TO …`, ` y FROM … TO …`,
  ` PIECE=…`). For a min event the pieces are those of the **complement** P(X>t,Y>t), although
  the header says `P(A)=`.
* `RESULT`: e.g. `=1-3/8` / `=5/8` / `.625`.
Then the `EVENT RESULT` menu: `REVERSE ORDER` (the same P, dx dy) for a check, `NEW EVENT` keeps the model.

**HW4-3** ((x+y)/8 on (0,2)², fails if either fails in hour 1):
`NEW MODEL`, `X+Y`, RECT `0,2,0,2` → c=1/8. `EVENTS + LIMITS > MIN/MAX VS t > min(X,Y)≤t`, `1` →
`=1-3/8`, **5/8**.
(play.py: `m:SOLVERS "m:JOINT DENSITY" "m:NEW MODEL" i:X+Y m1 i:0 i:2 i:0 i:2 "m:EVENTS + LIMITS" "m:MIN/MAX VS t" m1 i:1`)

**HW4-5** (P(X<Y), f=(1/4)(2x+y)): `(1/4)(2X+Y)`, RECT `0,1,0,2` (`q IS ALREADY A PDF`) →
`X<Y OR X>Y > X<Y` → limits `x FROM 0 TO 1` / ` y FROM x TO 2`, **19/24**.

Variant check A4 ((2x+y)/12 on (0,2)², t=1/2): min → **19/64**, max → **1/64**.

---

## Type 5. Joint PDF: conditional mean and variance at a given value
**Route:** model loaded → `GIVEN A VALUE > GIVEN Y=y` (for X given Y=y₀) or `GIVEN X=x`, then type the value.

Screen: `h(y₀)=∫f(x,y₀) dx` / `x FROM … TO …` / `h(y₀)=…` / `f(x|y₀)=…` / `FOR …` /
`E(X|Y=y₀)=…` / `E(X²|Y=y₀)=…`, then `Var(X|Y=y₀)=…`. After that, `P(a<X<b | Y=y)` or `NEW VALUE`.

**HW5-7 (c)**: `X+Y`, RECT `0,1,0,1`, `GIVEN A VALUE > GIVEN Y=y`, `1/2` → f(x|1/2)=1/2+x,
E=**7/12**, Var=**11/144**.
(play.py: `... "m:GIVEN A VALUE" m2 i:1/2`)

Variant A10 ((6/5)(x+y²), given X=1/2): `GIVEN X=x`, `1/2` → E(Y|X=1/2)=**3/5**, Var=**2/25**.

Means, variances, Cov and ρ of a joint **PDF**: model loaded → `MOMENTS + COV > MEANS VARS COV ρ`.
`E[g(X,Y)]` takes any g. (Not on the homework, and not exercised in this review.)

---

## Type 6. One-variable continuous PDF: E, Var, and Y = g(X)
**Route:** `SOLVERS > DENSITY+INTEGRAL > 1D PDF OR SLICE`

`q(X)?` `«pdf or shape»` → `FIXED A?` type **0** → `LOWER X?` `«a»` → `UPPER X?` `«b»` (finite only).
Screen `INTEGRAL q=` / `c APPROX=` (c = 1 if the PDF is complete). Then:
* `MEAN+VARIANCE` → `MEAN`, `E[X^2]`, `VAR(X)`
* `FUNCTION g(X)`, type g (e.g. `X²`) → `E[g]` = E(Y), `E[g^2]`, `VAR(g)` = Var(Y)
* `INTERVAL PROB`, `RAW/CENTRAL MOM`

For an infinite end, type a cutoff (e.g. 40 for 𝑒^(⁻X)), then repeat with twice the cutoff. The
answer must not change.

**HW5-2** ((3/4)(1−x²), −1<x<1): `(3/4)(1-X²)`, `0`, `⁻1`, `1` → `MEAN+VARIANCE`: **0**, E[X²]=1/5,
**Var 1/5**. `FUNCTION g(X)`, `X²` → E(Y)=**1/5**, E[g²]=3/35, Var(Y)=**8/175**.
(play.py: `m:SOLVERS m:DENSITY+INTEGRAL m1 i:(3/4)(1-X²) i:0 i:⁻1 i:1 m1 "m:FUNCTION g(X)" i:X²`)

---

## Type 7. MGF of an exponential density L·e^(−Lx), x>0
**Route:** `SOLVERS > MGF TOOLS > EXPONENTIAL RATE`. Type `RATE L>0?` **L** (the number in the
exponent: e^(−3x) → 3, e^(−x/2) → **1/2**, never the mean 2), then `SCALE a?` **1**, `SHIFT b?` **0**.

Screens: `ORIGINAL X MOMENTS` E(X), E(X²), VAR(X) / `DOMAIN t<L`, then `TRANSFORMED MGF`
`Mz(t)=e^(B*t)L/(L-A*t)` with L, A, B / `DOMAIN t<…`.
Write **M(t)=L/(L−t) for t<L** (with L=1/2 that is 1/(1−2t), t<1/2). The app gives L as a
decimal (.5).

**Written derivation (by hand, the app does not do it):** M(t)=∫₀^∞ e^{tx}·L e^{−Lx} dx
= L∫₀^∞ e^{−(L−t)x} dx = L/(L−t), which is finite only when L−t>0, i.e. t<L. Then M'(t)=L/(L−t)²
and M''(t)=2L/(L−t)³. At t=0 these give E(X)=1/L and E(X²)=2/L².

**HW5-3** (3e^(−3x)): `EXPONENTIAL RATE`, `3`, `1`, `0` → E(X)=**1/3**, E(X²)=**2/9**, domain **t<3**.
Variant A7 (½e^(−x/2)): `1/2`, `1`, `0` → **2**, **8**, Var **4**, t<1/2.

For another MGF you derived by hand (gamma, uniform, …), use `TYPE MGF NUMERIC` and type M with X
as t (e.g. `(1-2X)^⁻2`). It gives numeric E and Var.

---

## Type 8. MGF e^(Ct+Dt²) and a linear transform Z=aX+b
**Route:** `SOLVERS > MGF TOOLS > QUADRATIC LOG MGF`: `C?` (the t coefficient), `D?` (the t²
coefficient), `SCALE a?`, `SHIFT b?`.

Convert first: Z=(X−m)/s gives **a=1/s, b=−m/s**. Y=2X−5 gives a=2, b=⁻5.

Screens: `ORIGINAL X MOMENTS` (E(X)=C, VAR=2D), then `Z=aX+b MOMENTS` E(Z), VAR(Z), then
`TRANSFORMED MGF Mz(t)=e^(F*t+H*t²)` with F, H. Write M_Z(t)=e^{bt}M_X(at)=e^{Ft+Ht²}.

**HW5-4** (e^(4t+8t²), Z=(X−4)/4): `QUADRATIC LOG MGF`, `4`, `8`, `1/4`, `⁻1` → E(Z)=**0**,
VAR(Z)=**1**, F=0, H=1/2 → **M_Z(t)=e^(t²/2)**, all real t.

---

## Type 9. Variance of one linear combination (2 or 3 variables)
**Route:** `SOLVERS > LINEAR COMBOS > ONE COMBINATION > VAR/COV ONLY` (use `MEAN+VAR/COV` if
means are given and E(U) is asked).

Order of prompts: `n (1-3)?` → `VARIANCE?` of X1, X2, (X3) → `COVARIANCE?` for (X1,X2), (X1,X3),
(X2,X3) → `a FOR U?` the coefficient of each Xi → `OFFSET c FOR U?`.
Screen `COMBINATION U` / `VAR(U)` / `SD(U)`.

Rewrite the new variables in terms of the old ones first: W=2X+100, V=1.1Y → W+V = 2X + 1.1Y + 100.
Constants go in the offset (they do not change the variance). A negative covariance or
coefficient uses the (-) key.

**HW5-5**: `n` 2, var `300`, `500`, cov `150`, a `2`, `1.1`, offset `100` → VAR(U)=**2465**.
**HW5-6**: `n` 3, var `4`,`9`,`2`, cov `1`,`⁻1`,`0`, a `3`,`⁻2`,`1`, offset `0` → **56**.
(play.py: `m:SOLVERS "m:LINEAR COMBOS" m1 m1 i:3 i:4 i:9 i:2 i:1 i:⁻1 i:0 i:3 i:⁻2 i:1 i:0`)

Formula for the written answer (the app does not print it): Var(ΣaᵢXᵢ+c)=Σaᵢ²Var(Xᵢ)+2Σ_{i<j}aᵢaⱼCov(Xᵢ,Xⱼ).

---

## Type 10. Cov(U,V) of two linear combinations
**Route:** `SOLVERS > LINEAR COMBOS > TWO COMBINATIONS > VAR/COV ONLY`.
Variances and covariances as in Type 9. Then the coefficient prompts **alternate per variable**:
X1 `a FOR U?`, `b FOR V?`; X2 `a`, `b`; X3 `a`, `b`. A variable missing from U or V gets **0**.
Then `OFFSET c FOR U?`, `OFFSET d FOR V?`.
Screens: VAR(U), VAR(V), then `COV(U,V)` and `CORR(U,V)`.

Variant A9(b) (U=X+2Y, V=3X−Z): a,b = `1`,`3` | `2`,`0` | `0`,`⁻1` → COV(U,V)=**26**.

---

## Type 11. Joint CDF F(x,y) given (not on the homework)
`SOLVERS > CDF OF X AND Y > NEW F(X,Y)`: type F and the support a,b,c,d. Then `RECTANGLE PROB`,
`MARGINAL CDFs`, `PDF f FROM F`. For F from a PDF use `JOINT DENSITY > INDEP + CDF > F(x,y) FORMULA`
or `F(s,t) AT A POINT`.

---

## What you must write yourself
* MGF derivations (the integral or sum, and the condition on t), and the M'(0), M''(0) steps.
  See `ENCYCLOPEDIA > MGFS > DEF AND DOMAIN / MOMENT DERIVS / AFFINE AND SUMS`.
* Independence justification: copy the counterexample pair (discrete), or the witness/RANK line
  from `INDEP + CDF > INDEPENDENCE TEST` (continuous).
* Marginal PMF formulas (the app gives the values only).
* The expansion formula of Var(aX+bY+…).
* If you forget a route: `HELP > FIND MY SOLVER` asks what you are given and what is asked.
