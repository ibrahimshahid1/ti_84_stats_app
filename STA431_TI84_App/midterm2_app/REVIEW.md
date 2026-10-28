# STAM2 suite: judge review (student-use evaluation)

Method: I worked as the student would. I used only the main menu (`python3 tools/play.py`,
PLAY_DIR `.../scratchpad/play_judge`), START_HERE.md, HELP > HOW TO ENTER and HELP > FIND MY
SOLVER. I solved one session per problem and graded each part against
`sealed_answer_keys.json` (sets HW and A). No source, test or tool file was changed. The exact
key list of every session can be replayed with `play.py keys <session>` from that PLAY_DIR.

## 1. Scorecard

**Homework: 35/35 parts correct through the app** (2 parts need a written derivation that the
app only states). **Variants (A1, A3, A4, A7, A9, A10): 21/21 parts correct.** No wrong numbers.

| Problem | Part | App route (session keys) | App answer | Key | Verdict |
|---|---|---|---|---|---|
| HW4-1 | a | DISCRETE TABLE > FORMULA/GRID `{1,2}` `{1,2,3}` `X+Y²` (h41) | c=1/37 | 1/37 | correct |
| | b | MARG/CONDITIONAL > MARGINAL TABLES | 17/37, 20/37; 5/37, 11/37, 21/37 | same (+formula) | correct (values only, formula by hand) |
| | c | X GIVEN Y, `2` | 5/11, 6/11 | same | correct |
| | d | INDEPENDENCE | FAIL, pair (1,3): 10/37 vs 357/1369 | dependent | correct (different valid witness) |
| HW4-2 | a | JOINT DENSITY > NEW MODEL `2X+Y` RECT 0,1,0,2 (h42) | c=1/4 | 1/4 | correct |
| | b | FORMULAS > h(y) | 1/4+1/4y, 0<y<2 | (1+y)/4 | correct |
| | c | FORMULAS > f(x\|y) | (2x+y)/(1+y) | same | correct |
| HW4-3 | only | `X+Y` RECT 0,2,0,2 > EVENTS > MIN/MAX > min≤t, `1` (h43) | 5/8 | 5/8 | correct |
| HW4-4 | a | FORMULA/GRID `{1,2}` `{1,2,3,4}` `X+Y` > EVENT PROB > P(EVENT) `X>Y` (h44) | 3/32 | 3/32 | correct |
| | b | P(EVENT) `X+Y≤3` | 1/4 | 1/4 | correct |
| HW4-5 | only | `(1/4)(2X+Y)` RECT 0,1,0,2 > X<Y (h45) | 19/24 | 19/24 | correct |
| HW5-1 | a,b,c | FORMULA/GRID `{1,2,3,4}` `{0}` `X²+X` > MOMENTS (h51) | 1/40, 13/4, 63/80 | same | correct ×3 |
| HW5-2 | a ×2 | DENSITY+INTEGRAL > 1D `(3/4)(1-X²)` A=0, ⁻1, 1 > MEAN+VAR (h52) | 0, 1/5 | 0, 1/5 | correct ×2 |
| | b ×2 | FUNCTION g(X) `X²` | 1/5, 8/175 | 1/5, 8/175 | correct ×2 |
| HW5-3 | a | MGF TOOLS > EXPONENTIAL RATE `3`,`1`,`0` (h53) | L/(L−t), L=3, t<3 | 3/(3−t), t<3 | correct (derivation by hand) |
| | b ×2 | same | 1/3, 2/9 | same | correct ×2 |
| HW5-4 | a | QUADRATIC LOG MGF `4`,`8`,`1/4`,`⁻1` (h54) | e^(Ft+Ht²), F=0, H=1/2 | e^(t²/2) | correct (a, b by hand) |
| | b ×2 | same | 0, 1 | 0, 1 | correct ×2 |
| HW5-5 | only | LINEAR COMBOS > ONE > VAR/COV n=2 (h55) | 2465 | 2465 | correct |
| HW5-6 | only | same, n=3 (h56) | 56 | 56 | correct |
| HW5-7 | a,b | `X+Y` RECT 0,1,0,1 > FORMULAS h(y), f(x\|y) (h57) | 1/2+y; (2x+2y)/(1+2y) | same | correct ×2 |
| | c ×2 | GIVEN A VALUE > GIVEN Y=y `1/2` | 7/12, 11/144 | same | correct ×2 |
| HW5-8 | a,b,c | FORMULA/GRID `{1,2,3}`² `X+Y` > MOMENTS (h58) | 13/6, 13/6, 14/3, ⁻1/36 | same | correct ×3 |
| | d ×2 | Y GIVEN X `1` | 2/9, 1/3, 4/9; 20/9 | same | correct ×2 |
| A1 | a–d | FORMULA/GRID `X²+Y`, MARGINAL TABLES, Y GIVEN X `2`, INDEPENDENCE (a1) | 1/27; 1/3, 2/3; 7/27, 1/3, 11/27; 5/18, 1/3, 7/18; FAIL at (1,3) 4/27 vs 11/81 | same | correct ×4 |
| A3 | a–c | `X+3Y` RECT 0,2,0,1 > FORMULAS (a3) | 1/5; 2/5+6/5y; (1/2x+3/2y)/(1+3y) | 1/5; (2+6y)/5; (x+3y)/(2+6y) | correct ×3 (see F3) |
| | d,e | X<Y; X+Y≤k `1` | 7/30, 2/15 | same | correct ×2 |
| A4 | a,b | `(2X+Y)/12` RECT 0,2,0,2 > min≤t, max≤t `1/2` (a4) | 19/64, 1/64 | same | correct ×2 |
| A7 | a–d | EXPONENTIAL RATE `1/2`,`1`,`0` (a7) | L=.5, t<.5; 2, 8, 4 | 1/(1−2t), t<1/2; 2, 8, 4 | correct ×4 (simplify by hand) |
| A9 | a | ONE COMBINATION n=3, offset 7 (a9a) | 33 | 33 | correct |
| | b | TWO COMBINATIONS (a9b) | 26 | 26 | correct |
| A10 | a–d | `(6/5)(X+Y²)` RECT 0,1,0,1 > g(x), w(y\|x), GIVEN X=x `1/2` (a10) | 2/5+6/5x; (3x+3y²)/(1+3x); 3/5; 2/25 | same | correct ×4 |

Work left to the student, even though every number came from the app: the marginal PMF formula
(HW4-1b, A1b), the MGF derivation integral and the simplification L/(L−t) → 1/(1−2t) (HW5-3a,
A7a), the conversion Z=(X−4)/4 → a=1/4, b=−1 (HW5-4), and rewriting W+V as 2X+1.1Y+100 (HW5-5).

## 2. Confirmed bugs (each reproduced twice)

| # | Severity | Bug | Repro (play.py keys) |
|---|---|---|---|
| B1 | medium (misleading label) | DISCRETE TABLE > EVENT PROB > **P(EVENT)** labels the result `P(EVENT \| GIVEN)=` although no given event was entered. A student copying the screen writes a conditional probability. | `m:SOLVERS "m:DISCRETE TABLE" m:FORMULA/GRID i:{1,2} i:{1,2,3,4} i:X+Y "m:EVENT PROB" m1 i:X>Y` → `P(EVENT | GIVEN)= 3/32` (the same for `X+Y≤3`) |
| B2 | medium (misleading screen) | JOINT DENSITY min(X,Y)≤t: the LIMITS screen is headed `P(A)=∫∫ c*q dy dx`, but its pieces (x 1..2, y 1..2, PIECE=3/8) belong to the complement P(X>t,Y>t). The RESULT then shows `=1-3/8`. Copying LIMITS gives "P(A)=3/8". | `m:SOLVERS "m:JOINT DENSITY" "m:NEW MODEL" i:X+Y m1 i:0 i:2 i:0 i:2 "m:EVENTS + LIMITS" "m:MIN/MAX VS t" m1 i:1` |
| B3 | low (wrong error text) | DISCRETE FORMULA/GRID accepts the letter C in q (as the stored value C=0) and replies `WEIGHTS MUST BE ≥0 / WITH POSITIVE TOTAL`. It does not say "omit c". JOINT DENSITY has the right guard (`q MAY USE ONLY X AND Y`). DENSITY+INTEGRAL 1D also accepts `C(1-X²)` silently: it worked here only because C happened to be non-zero. | `m:SOLVERS "m:DISCRETE TABLE" m:FORMULA/GRID i:{1,2} i:{1,2,3} "i:C(X+Y²)"` |
| B4 | low (cosmetic) | After MARG/CONDITIONAL > MARGINAL TABLES, the next Input prompt (`GIVEN X=?`) is drawn on row 2 over the old Y table, so the screen mixes the prompt with stale rows. | `... m:FORMULA/GRID i:{1,2} i:{1,2,3} i:X²+Y m:MARG/CONDITIONAL "m:MARGINAL TABLES" "m:Y GIVEN X"` (screen #12) |
| B5 | low (doc) | START_HERE says "Drag **all 14 `.8xp` files**" (Transfer step 2) and "rebuilds the 14 `.8xp` files" (Rebuild), but there are 16 programs, and the same file says "all 16 programs". A student who sends 14 files is missing two helpers (M2JAN, M2CDF), and JOINT DENSITY FORMULAS and CDF fail with ERR:UNDEFINED. | START_HERE.md, the Transfer and Rebuild sections |

No wrong numerical result was found.

## 3. Friction points (no bug, but slow or risky on exam day)

* **F1 Independence wording (discrete).** It shows `NUMERIC FACTORIZATION FAIL / WRITE EXACT
  JUSTIFICATION`, not "NOT INDEPENDENT". The counterexample pair prints two unlabelled numbers
  (x, then y) right-aligned.
* **F2 Unlabelled conditional and marginal tables.** `CONDITIONAL DISTRIBUTION` rows are `1 | 5/11`
  with no `x` / `f(x|2)` header, and the given value is not repeated. With X GIVEN Y vs Y GIVEN X
  it is easy to lose track.
* **F3 Ambiguous fraction-coefficient print.** `(1/2x+3/2y)/(1+3y)` and `1/4+1/4y`, where 1/2x
  means (1/2)x. On paper this reads as 1/(2x). An integer-cleared form `(x+3y)/(2+6y)` or `x/2`
  would be safer.
* **F4 MGF templates need hand conversion.** EXPONENTIAL RATE asks `RATE L>0?` without showing
  the pdf form `L𝑒^(-Lx)` on that screen, so e^(−x/2) is easily typed as 2. The output L is a
  decimal (`L=.5`, `DOMAIN t<.5`), and M(t) is never printed as a simplified expression.
  QUADRATIC LOG MGF needs Z=(X−m)/s typed as a=1/s, b=−m/s.
* **F5 LINEAR COMBOS prints only the number.** There is no expansion line such as
  `=a1²V1+a2²V2+2a1a2C12`, which is the written work. TWO COMBINATIONS interleaves `a FOR U?` and
  `b FOR V?` for each variable, and missing variables must be typed as 0 (easy to mis-order).
* **F6 1D tool asks `FIXED A?` every time.** For a plain one-variable pdf the student must know
  to type 0. Its results are labelled `APPROX` even when the answers are exact fractions.
* **F7 No PDF → MGF path.** FIND MY SOLVER > ONE-VARIABLE PDF has no "MGF" item. A pdf that is
  not exponential (e.g. x·e^(−x), or a discrete pmf's MGF) has no route other than "derive it by
  hand, then TYPE MGF NUMERIC".
* **F8 Discrete marginal formula.** Only values are given. HW4-1(b) expects g(x)=(3x+14)/37.

## 4. Prioritized improvements (new-question adaptation first)

| P | Problem | Concrete fix | Helps types | Size |
|---|---|---|---|---|
| 1 | B5: wrong file count in START_HERE can break the install | Replace "14" by "16" in Transfer step 2 and Rebuild. Add a device check that opens each solver once, so a missing helper shows up before the exam | all | XS (doc) |
| 2 | B1: `P(EVENT \| GIVEN)` label on an unconditional event | In M2DISC, print `P(EVENT)=` when the P1 branch was taken (the given flag is already known there) | discrete events (HW4-4, A2) | XS |
| 3 | B2: LIMITS header on complement events | When the event is evaluated through its complement (min≤t, max>t, COMPLEMENT OF), head the LIMITS screen `P(X>t,Y>t)=∫∫…` (the complement's text) instead of `P(A)=` | series/parallel (HW4-3, A4) | S |
| 4 | F3: coefficient fractions print as `1/2x` | In M2PLY POLYSTR / the conditional printer, emit `(1/2)x` or clear denominators: multiply N and D by their LCM, so `(x+3y)/(2+6y)` and `(1+y)/4` | joint PDF formulas (HW4-2, HW5-7, A3, A10) | S |
| 5 | F1/F2: unlabelled discrete outputs | `INDEPENDENCE`: first line `NOT INDEPENDENT` / `INDEPENDENT`, then `x=1 y=3`. `CONDITIONAL DISTRIBUTION`: header `x | f(x|y=2)` (or `y | w(y|x=1)`) and `E(X|Y=2)=` instead of `MEAN=`; MARGINAL TABLES header `x | g(x)` | discrete joint (HW4-1, HW5-8, A1) | S |
| 6 | F4: exponential template entry | On the RATE prompt show `f(x)=L𝑒^(-Lx), x>0` / `𝑒^(-x/2) → L=1/2`. Print L and the domain as fractions (M2FMT). Add a line `Mx(t)=1/(1-t/L)`. In QUADRATIC LOG, accept "Z=(X-m)/s" as an alternative entry (ask m and s, convert to a=1/s, b=−m/s) | MGF (HW5-3, HW5-4, A7, A8) | S |
| 7 | F5: no written expansion for linear combinations | After VAR(U), print `=Σa²Var+2ΣaaCov` with the numbers (e.g. `=4(300)+1.21(500)+2(2)(1.1)(150)`) | Var/Cov combos (HW5-5, HW5-6, A9) | S |
| 8 | B3: letter C in q | Run the M2PLY VARCHECK "X" (1D) / "XY" (grid) in M2DISC FORMULA/GRID and M2CONT 1D, with the JOINT DENSITY message `q MAY USE ONLY X AND Y / OMIT c` | all c-normalising types | S |
| 9 | F7: PDF → MGF | Add `MGF FROM A PDF` in MGF TOOLS: type f(X) and support, then t. It numerically integrates ∫e^{tx}f(x)dx at t and ±small t, and checks a typed closed form. Also add a finder route ONE-VARIABLE PDF > MGF that points to EXPONENTIAL RATE / TYPE MGF and the encyclopedia derivation page | MGF from pdf (HW5-3 variants) | M |
| 10 | F6: 1D slice prompt | Split `1D PDF` (no A prompt) from `CONDITIONAL SLICE` (asks A). Drop `APPROX` when the value printed is a recognised fraction and both passes agree | one-variable PDF (HW5-2, A6) | S |
| 11 | F8: discrete marginal formula | Optional: for FORMULA/GRID, recover g(x) as a polynomial in x when it fits the values (degree ≤ len−1) and print it | HW4-1(b), A1(b) | M |
| 12 | B4: stale prompt overlay | ClrHome before the Input after MARGINAL TABLES (or Disp a blank line) | discrete | XS |

Each fix needs a non-homework test variant with sympy/Fraction targets, following the
definition of done.

## 5. What the app deliberately leaves to the student, and where the encyclopedia helps

| Left to the student | Encyclopedia / help coverage |
|---|---|
| Deriving an MGF (integral or sum) and its domain condition on t; the M'(0), M''(0) steps | ENCYCLOPEDIA > MGFS > DEF AND DOMAIN (definition, M(0)=1, open interval around 0, exponential L/(L−t), t<L), MOMENT DERIVS, AFFINE AND SUMS (e^{bt}M(at)), UNIQUENESS. FIND MY SOLVER > PROOF OR FORMULA > MGF DOMAIN gives the recipe ("write the integral, combine exponents, solve the condition on t"). There is no line-by-line worked derivation for a specific pdf (improvement 9). |
| Independence justification in words | INDEPENDENCE gives the witness pair (discrete) or the RANK/witness lines (continuous INDEP + CDF). FIND MY SOLVER > WRITTEN REASONING > INDEPENDENCE and ZERO COV / DEPEND |
| Translating words to events (series/parallel, "first before second") | EVENT SETUP screens do it, and WRITTEN REASONING > WORDS TO EVENT; JOINT LAWS > SKETCH + LIMITS |
| Sketching the support and writing the iterated integral | LIMITS screens print the limits per piece; REVERSE ORDER for the other order |
| Symbolic marginal/conditional for non-polynomial or curved models | GIVEN A VALUE (numeric) and JOINT SLICE. FORMULAS refuses with a pointer |
| Proofs (e.g. Var(aX+b), Cov properties) | EXPECT + MOMENTS, PRODUCT + CORR, LINEAR COMBOS topics: definitions and Freund citations |
| Algebraic set-up of linear combinations (W=2X+100 → coefficients) | LINEAR COMBOS topic; `OFFSETS HAVE NO VARIANCE` reminder on the result screen |

## 6. Overall

For the homework-style midterm the suite is exam-ready. Every homework and variant number came
out right on the first try, with exact fractions, and with typing only the changed numbers or
functions. The JOINT DENSITY workflow (model → FORMULAS / EVENTS / GIVEN A VALUE) is the
strongest part, because the model stays loaded across sub-questions. The risks are about
presentation, not arithmetic: two misleading labels (B1, B2), formula prints that are ambiguous
on paper (F3), the transfer-count error in START_HERE (B5), and MGF templates that need hand
conversion (F4). Fixes 1–8 are all small. The exam-day card is `EXAM_KEYSTROKES.md`.

## Fixed after this review

- B1: the discrete EVENT PROB result now reads `P(EVENT)=` for an unconditional event; `P(EVENT | GIVEN)=` appears only for a conditional event.
- B5 / improvement 1: START_HERE.md now says to transfer all 16 `.8xp` files.
