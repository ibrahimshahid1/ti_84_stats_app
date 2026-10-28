# STA 431/631 TI-84 Plus CE Helper — Build Spec (single source of truth)

Goal: a TI-BASIC app for the **TI-84 Plus CE** that helps a student solve STA 431/631
Midterm-I questions like Homeworks 1–3. Two halves:
1. **Encyclopedia** — short, concise topic pages (formula → how to use → HW-style example → traps → refs).
2. **Calculators** — guided solvers for each HW question type, plus "Which tool?" hints.

Primary text: **Freund's Mathematical Statistics with Applications, 8th ed. (Miller & Miller)**.
Supplements: Bertsekas & Tsitsiklis, Feller Vol. I, Wasserman *All of Statistics*, Ross *A First Course*.

Root: `$ROOT = /Users/ibrahimshahid/Downloads/academic_texts/stats_texts/STA431_TI84_App/dev`
Python: install `requirements.txt` into a Python virtual environment, then use that environment's `python` for the commands below. The temporary Claude Python path from the original build is not part of the package.

```
$ROOT/SPEC.md            this file
$ROOT/src/*.txt          TI-BASIC sources; file stem = program name
$ROOT/content/*.json     encyclopedia + hint content (generated into src/ by tools/content.py)
$ROOT/tools/tibuild.py   lint + compile to .8xp   ($PY tools/tibuild.py lint src/X.txt ; build src out)
$ROOT/tools/content.py   content JSON check/gen/preview
$ROOT/tools/tisim.py     TI-BASIC simulator (written by the harness agent)
$ROOT/tools/tilint.py    static structure linter (written by the harness agent)
$ROOT/tests/             test scripts (test_<PROGRAM>.py)
$ROOT/oracles/           exact expected answers (oracles.json, cases.md)
$ROOT/notes/hw1.txt hw2.txt hw3.txt   homework text
$ROOT/out/               built .8xp files
```
Textbook text dumps (page markers `=== PAGE n ===`, n = PDF page):
`/private/tmp/claude-501/-Users-ibrahimshahid-Downloads-academic-texts-stats-texts/81983d3b-00eb-4485-955e-2286225a6c88/scratchpad/books/freund.txt bertsekas.txt feller.txt wasserman.txt ross.txt` (Casella is image-only).

---------------------------------------------------------------------------------------------------
## 1. Programs and menu map (FIXED — do not rename)

| Program | Role | Author |
|---|---|---|
| `STA431` | main launcher (done: src/STA431.txt) | — |
| `STAFMT` | number formatter subroutine (done: src/STAFMT.txt) | — |
| `STAE1` | Encyclopedia Ch1 Counting | generated from content/STAE1.json |
| `STAE2` | Encyclopedia Ch2 Probability | generated from content/STAE2.json |
| `STAE3` | Encyclopedia Ch3 Random variables (+631 transforms) | generated from content/STAE3.json |
| `STAHNT` | "Which tool?" hints, keyword glossary, formula sheet, proof recipes | generated from content/STAHNT.json |
| `STACNT` | Counting calculators | hand-written src/STACNT.txt |
| `STAPRB` | Probability calculators | hand-written src/STAPRB.txt |
| `STARV` | Random-variable calculators | hand-written src/STARV.txt |

Main menu (STA431): ENCYCLOPEDIA → {CH1 COUNTING, CH2 PROBABILITY, CH3 RANDOM VARS};
CALCULATORS → {WHICH TOOL? HINTS, COUNTING, PROBABILITY, RANDOM VARIABLES}; WHICH TOOL? HINTS; HELP + NOTATION; QUIT.
Subprograms are called with `prgmNAME` and must end with `Return` (never `Stop`) so control returns to STA431.

Calculator menus (FIXED text and order — hint pages refer to them as e.g. "CALC>COUNT>2"):
```
STACNT  Menu("COUNTING TOOLS","n!, nPr, nCr",A,"WORD ARRANGEMENTS",B,"GROUPS/MULTINOMIAL",C,"2-GROUP SELECTION",D,"STARS AND BARS",E,"TERM COEFFICIENT",F,"BACK",Z)
STAPRB  Menu("PROBABILITY TOOLS","TWO EVENTS A,B",A,"2x2 TABLE",B,"TOTAL PROB/BAYES",C,"SENS/SPEC TEST",D,"VENN 2-3 SETS",E,"URN DRAWS",F,"BACK",Z)
STARV   Menu("RANDOM VARIABLES","PMF TABLE + CDF",A,"MAX/MIN/SUM DRAWS",B,"POLY PDF/CDF",C,"ANY f(x) OR F(x)",D,"TRANSFORM Y=g(X)",E,"JOINT X,Y",J,"BACK",Z)
```
Tool paths used in hint text: `CALC>COUNT>1..6`, `CALC>PROB>1..6`, `CALC>RV>1..6` (numbers = menu position).

---------------------------------------------------------------------------------------------------
## 2. Device facts (TI-84 Plus CE, OS ≥ 5.2)

* Home screen: **26 columns × 10 rows** (large font). `Output(row,col,…)` row 1–10, col 1–26; long text wraps to
  the next row, text past row 10 col 26 is lost. `Disp` writes at the Disp cursor and scrolls; strings are
  left-aligned, numbers right-aligned; a string longer than 26 chars is cut off — keep Disp strings ≤ 26.
* `Menu(`: title + **at most 7 options**; keep title ≤ 22 chars, option text ≤ 18 chars; labels are 1–2 chars
  from A–Z, 0–9, θ. Labels are local to a program.
* `Input "PROMPT",VAR` — prompt ≤ 16 chars so there is room to type. Works for real vars, lists, strings (Str0–9).
* `toString(`, `eval(` need OS 5.2+ (fine). `Pause` waits for ENTER. `getKey` codes: ENTER 105, CLEAR 45,
  LEFT 24, RIGHT 26, UP 25, DOWN 34.
* CE OS 5.3 or later can execute TI-BASIC programs from archive; OS 5.2 or earlier requires programs in RAM. All nine programs together are large relative to CE RAM, so check free memory and test the final package on the physical calculator.

---------------------------------------------------------------------------------------------------
## 3. TI-BASIC source rules (MUST follow — the linter enforces most of these)

Source files are plain UTF-8 text. `tools/tibuild.py` strips indentation, drops blank lines and lines starting
with `//` (use these for comments), and re-adds the trailing space to bare `Pause`/`Disp`/`FnOff`/… lines.
Run `$PY tools/tibuild.py lint src/NAME.txt` after every edit; it must report 0 errors.

1. **Negation vs minus**: unary minus is `⁻` (U+207B). `-` is binary subtraction only. `⁻Q→Q`, `1ᴇ⁻9`, `max(⁻1,A)`.
   `-1` at the start of an expression is a syntax error on the calculator.
2. Scientific notation uses `ᴇ` (U+1D07): `1ᴇ⁻9`, `1ᴇ10`.
3. Store arrow is `→`. It terminates a string literal, so never put `→` (or `->`) inside quotes.
4. `nCr`/`nPr` must be written with surrounding spaces: `A nCr B`, `N nPr R`. Factorial `N!`.
5. Commands keep their trailing space: `Disp "X"`, `Input "N?",N`, `If A=1`, `While K<5`, `Repeat K`, `Lbl AA`,
   `Goto AA`, `DelVar ʟCNA`, `FnOff 9`. `Pause` may be written bare.
6. Lowercase letters are only legal **inside strings**. Outside strings they tokenize as text chars → ERR:SYNTAX.
7. Exponential is `𝑒^(`, natural log `ln(`, square root `√(`, π constant `pi` (outside strings), `|π` inside strings.
   Squared `²`, cubed `³`. Integration `fnInt(expr,X,a,b)`, derivative `nDeriv(expr,X,a)`.
8. Always close parentheses and quotes (the calculator tolerates omission; our tools do not).
9. **Never `Goto` or `Menu(` from inside an open `If…Then`, `For(`, `While`, `Repeat` block** — each such jump
   leaks memory and eventually gives ERR:MEMORY. A single-line `If cond` followed by `Goto X` (no `Then`) at block
   depth 0 is fine. Put every `Menu(` at block depth 0.
10. `If cond` without `Then` controls exactly one following statement.
11. `For(I,A,B)` runs 0 times if A>B. After the loop I = last value + step.
12. Lists: 1-based. Create with `N→dim(ʟNAME)` after `DelVar ʟNAME` (new elements are 0), or `seq(`.
    Storing to element dim+1 extends the list; beyond that → ERR:INVALID DIM. Named lists: `ʟ` + 1–5 chars
    (A–Z, 0–9, θ; first a letter). Use module prefixes: STACNT `ʟCN…`, STAPRB `ʟPR…`, STARV `ʟRV…`.
    Delete them on BACK (`DelVar ʟCNA` etc., one per line). Do NOT use L₁–L₆ or matrices (user data).
13. Strings: avoid the empty literal `""` except as the very last line of STA431. Use `sub(`, `length(`,
    `inString(`, `+` concatenation, `toString(`, `expr(`. String `=` comparison is allowed.
14. No colon `:` inside strings (policy). Separate statements with newlines; `:` only in the
    `Repeat Ans:getKey:End` idiom and `If cond:Goto X`.
15. Guard division by zero and domain errors (nCr with r>n → treat as 0; n! only for integer 0 ≤ n ≤ 69).
16. Prefer explicit `*`. (Implied multiplication is legal but avoid it in our code.)
17. Before `Input` prompts use `ClrHome` then `Disp` for header lines (Output does not move the Disp cursor, so
    Input would overwrite an Output header). For result screens use `ClrHome`, `Output(`, then `Pause`.
18. Every string shown must be ≤ 26 − col + 1 chars. Allowed display chars in strings: A–Z a–z 0–9 space
    ( ) [ ] { } , . ! ? + - * / = < > ^ | ' % & # @ ; _ ≤ ≥ ≠ ² ³ Σ σ μ λ θ √( ∫ ₀–₉ ► ◄ ↑ ↓ × … α β γ δ Δ ε ρ τ χ Φ Ω
    and `|π`. The linter round-trips every string literal and errors if it would display differently.

### Shared conventions for calculator modules
* **Formatter**: set `W` then `prgmSTAFMT`. Result: `Str9` = integer or a near-rational fraction candidate (`N/D` with D ≤ 9999), else
  decimal; `Str8` = decimal rounded to 6 places. A numeric value alone cannot prove an exact fraction.
  W is not modified. **STAFMT clobbers Q,R,S,T,U,V** — never
  keep live data in Q–W, Str8, Str9 across a `prgmSTAFMT` call. Display as `Output(r,1,"P(A)="+Str9)`; for key
  answers also show the decimal when it differs: `If Str9≠Str8` → another Output of `Str8`.
* Variables a module may use freely: A–P, X–Z, θ, K, Str1–Str7, its own named lists. (K is also used by the
  encyclopedia pager; that's fine.) STARV evaluates typed expressions from strings without replacing
  the user's Y₉ and Y₀ graph functions. Real and string variables are shared calculator state, so back them up before transfer.
* **Unknown values**: in tools that accept partial information, a **negative entry means unknown**. Tell the
  user "(-)1=UNKNOWN" (the (-) key) on the intro screen.
* Percent convenience: where a probability is expected and the user types a value > 1 (and ≤ 100), treat it as
  percent (÷100) and show a note — only where the SPEC says so.
* Each tool: (1) intro "USE WHEN" screen (≤ 10 rows, `Pause`), (2) inputs, (3) result screen(s) with the
  formula and plugged-in numbers where it fits, each followed by `Pause`, (4) return to the module menu
  (label M). Tools with follow-ups use a `Menu(` (at depth 0) for the choice.
* Module skeleton:
```
Lbl M
Menu("COUNTING TOOLS",…,"BACK",Z)
Lbl A
…tool A…
Goto M
…
Lbl Z
DelVar ʟCNA
ClrHome
Return
```

---------------------------------------------------------------------------------------------------
## 4. Calculator tool specifications (behavior + oracle test cases)

All oracle numbers below must be reproduced exactly (fractions via STAFMT). "→" in this section means "gives".

### STACNT — COUNTING TOOLS
**A. n!, nPr, nCr** — inputs N, R (non-negative integers; reject others with a message). Show n!, r!, nPr, nCr,
n^r (ordered, with repetition), C(n+r−1,r) (unordered, with repetition); n! shows "TOO BIG" if n>69; nPr=nCr=0
if r>n. Intro: order matters→nPr; not→nCr; with replacement ordered→n^r; multiset→C(n+r−1,r).
Tests: N=5,R=2 → 120, 2, 20, 10, 25, 15. N=12,R=3 → 479001600, 6, 1320, 220, 1728, 364.

**B. WORD ARRANGEMENTS** — `Input "WORD?",Str1` (intro says: use ALPHA / A-LOCK). n = length. Count each
distinct character; list repeated letters with counts (e.g. "B x2  I x2"); total = n!/Π k_i!. Then
`Menu("WORD OPTIONS","LETTER BLOCK",…,"NOT ALL TOGETHER",…,"BACK",M)`: ask `Input "LETTER?",Str2`; block
(all copies of that letter adjacent) = (n−k+1)!/Π_{j≠letter} k_j!; not-all-together = total − block.
Tests: PROBABILITY → n=11, 9979200; block B → 1814400; not together → 8164800.
MISSISSIPPI → 34650; block S → 840. STATISTICS → 50400.

**C. GROUPS/MULTINOMIAL** — `Menu("GROUPS","SPLIT INTO GROUPS",…,"EXACT COUNTS+FREE",…,"BACK",M)`.
C1 split: number of groups k, sizes n_i; n=Σn_i; labeled count n!/Πn_i!; ask "GROUPS LABELED? 1=Y 0=N"; if
unlabeled divide by Π(m_s!) where m_s = how many groups share size s; show both.
Tests: 3,4,5 labeled → 27720. 2,2,2 → 90 labeled, 15 unlabeled. 4,4,2 unlabeled → 3150 labeled, 1575 unlabeled.
C2 exact counts + free: N objects, M categories with exact counts c_i, remaining r=N−Σc objects each choose
among F other categories: N!/(c_1!…c_M! r!) · F^r (show both factors). Reject Σc > N.
Tests: N=10, counts 3,1, F=3 → 840 × 729 = 612360. N=5, count 2, F=4 → 10 × 64 = 640.

**D. 2-GROUP SELECTION** — sizes A (G1), B (G2), choose K; "G1 AT LEAST?", "G1 AT MOST?" (99=any),
"G2 AT LEAST?", "G2 AT MOST?" (99=any). i (from G1) ranges over
max(minG1, K−min(maxG2,B), 0) … min(maxG1, A, K−minG2, K). Show each term "i=2 28*20=560" (paginate), total, and
probability total/C(A+B,K). Intro mentions T/F exams: "#correct = choose which questions are correct".
Tests: A=8,B=6,K=5, min 2 each, max 99 → terms 560, 840; total 1400; P = 100/143 (.699301).
A=5,B=15,K=15, G1 exactly 2 (min=max=2), G2 min 0 max 99 → 10*105=1050; P = 175/2584 (.067724).

**E. STARS AND BARS** — n identical items, k distinct bins, lower bounds ("SAME MIN ALL? 1=Y 0=N"; then one
min or each bin's min). n' = n − Σmin; if n'<0 → 0; ways = C(n'+k−1, k−1); display "C(14,3)=364".
Tests: n=15,k=4,min 1 each → 364. mins 3,1,1,1 → 220. n=10,k=3,min 0 → 66.

**F. TERM COEFFICIENT** — number of terms k (2–6); each term's coefficient a_i and exponent e_i; n=Σe_i shown
("CHECK n = POWER!"); multinomial n!/Πe_i!, product Πa_i^e_i, coefficient = product of both (0^0 = 1).
Tests: (2x−y+3z)^7, x³y²z² → 210, 72, 15120. (x+2)^5 coeff of x³ (terms (1,3),(2,2)) → 10, 4, 40.
(3x−2y)^4 x²y² → 6, 36, 216.

### STAPRB — PROBABILITY TOOLS
**A. TWO EVENTS A,B** — inputs (negative = unknown): P(A), P(B), P(AnB), P(AuB), P(A|B), P(B|A), P(NEITHER).
Then `Menu("A AND B ARE…","NO EXTRA INFO",…,"INDEPENDENT",…,"MUTUALLY EXCL.",…)`. Solve iteratively (≤ 12 passes)
until P(A), P(B), P(AnB) known, using: U=1−N; N=1−U; I=A+B−U; U=A+B−I; B=U−A+I; A=U−B+I; I=B·C; I=A·D;
B=I/C; A=I/D; C=I/B; D=I/A; indep: I=A·B, A=C, B=D, A=I/B, B=I/A; exclusive: I=0;
B=(U−A)/(1−C) (from A,U,C); A=(U−B)/(1−D); I=U/(1/C+1/D−1). (C=P(A|B), D=P(B|A), U=union, I=intersection,
N=neither.) If still missing → "NOT ENOUGH INFO" + list knowns. Results: screen 1 P(A),P(B),P(AnB),P(AuB),
P(A'),P(B'),P(A'nB') neither, P(AnB') A only, P(A'nB) B only; screen 2 P(A|B),P(B|A),P(A|B'),P(B|A'),P(A'|B),
P(B'|A), P(exactly one)=A+B−2I ("undef" when the condition has probability 0); screen 3 checks: independent?
(show P(A)P(B) vs P(AnB)), mutually exclusive?, validity warnings (value outside [0,1], I>min(A,B), U>1).
Tests: A=.55,B=.35,U=.7 → I=1/5, P(A|B)=4/7, P(B|A)=4/11, P(B|A')=1/3, P(A|B')=7/13, neither 3/10, A only 7/20,
B only 3/20, exactly one 1/2, independent NO (.1925). A=.3,B=.4,indep → I=.12 (3/25), U=.58 (29/50).
I=.1, P(A|B)=.25, P(B|A)=.5 → B=2/5, A=1/5, U=1/2.

**B. 2x2 TABLE** — rows R1,R2 × columns C1,C2 with totals; inputs R1C1, R1C2, R1 TOTAL, R2C1, R2C2, R2 TOTAL,
C1 TOTAL, C2 TOTAL, GRAND TOTAL (negative = unknown); fill by row/column sums repeatedly (a line with exactly
one unknown gets solved). Screens: the completed table; joint P(RinCj) and marginals; P(Ri|Cj) and P(Cj|Ri);
independence check (P(R1nC1) vs P(R1)P(C1)); warn if totals inconsistent. Works for counts or probabilities.
Test: R1C1=40, R1 total 70, R2 total 50, C1 total 65, N=120, others unknown → R1C2=30, R2C1=25, R2C2=25,
C2=55; P(R2nC2)=5/24; P(R1|C1)=8/13; P(C1|R1)=4/7; not independent.

**C. TOTAL PROB/BAYES** — k cases (2–9), for each prior P(Bi) and likelihood P(A|Bi). If priors don't sum to
1, rescale (so counts/percents work) and say so; a likelihood > 1 is treated as percent. Screens: each term
P(A|Bi)P(Bi) and P(A) = Σ; posteriors P(Bi|A); P(A') and P(Bi|A').
Tests: priors .5,.3,.2; lik .15,.25,.10 → P(A)=17/100, P(B1|A)=15/34 (.441176), P(B2|A)=15/34, P(B3|A)=2/17,
P(A')=83/100, P(B1|A')=85/166. Priors 2,4 (scaled to 1/3,2/3), lik 3/7,5/7 → P(A)=13/21, P(B1|A)=3/13,
P(B2|A)=10/13. Priors .6,.4, lik .4,.05 → P(A)=13/50, P(B1|A)=12/13.

**D. SENS/SPEC TEST** — prevalence p, sensitivity, specificity (percent allowed); `Menu("TEST RESULT?","POSITIVE (+)",…,"NEGATIVE (-)",…)`.
Show P(+)=sens·p+(1−spec)(1−p), P(−), PPV=P(D|+), NPV=P(D'|−), P(D|−), and highlight the posterior for the
chosen result. Then `Menu("NEXT?","ANOTHER TEST",…,"DONE",M)`: another test uses the posterior as the new prior
(ask new sens/spec/result) → "UPDATED P(D)=".
Tests: p=.005, sens=.95, spec=.99, + → P(+)=147/10000, PPV=95/294 (.323129); then sens .90, spec .95, + →
posterior 1710/1909 (.895757).

**E. VENN 2-3 SETS** — `Menu("VENN","2 SETS",…,"3 SETS",…,"BACK",M)`; counts or probabilities; total N may be
unknown (negative). 3 sets inputs: n(A), n(B), n(C), n(AnB), n(AnC), n(BnC), n(AnBnC), N. Show regions: A only,
B only, C only, AnB only, AnC only, BnC only, all 3, none (if N known); union (≥1), exactly 1, exactly 2, at
least 2. Warn if any region < 0. 2 sets: n(A), n(B), n(AnB), N → A only, B only, union, neither, exactly one.
Tests: 400,500,600,200,150,250,100,1000 (A=Digital,B=Print,C=Weekend; AnB=200, AnC=150, BnC=250) →
A only 150, B only 150, C only 300, AnB only 100, AnC only 50, BnC only 150, all 100, union 1000, none 0,
exactly 1 600, exactly 2 300, at least 2 400. 2 sets .5,.4,.2,1 → .3,.2,.7,.3, exactly one .5.

**F. URN DRAWS** — N total, K successes, n draws, target k. Screen 1 WITHOUT replacement (hypergeometric):
P(X=k)=C(K,k)C(N−K,n−k)/C(N,n), P(X≥k), P(X≤k); screen 2 WITH replacement (binomial, p=K/N): same three;
screen 3 one specific order (e.g. first k successes then failures) = P(X=k)/C(n,k) for each case.
Tests: N=7,K=3,n=2,k=1 → w/o: 4/7, ≥: 5/7, ≤: 6/7; with: 24/49, 33/49, 40/49; specific order w/o 2/7, with 12/49.
N=52,K=4,n=5,k=2 → w/o P(X=2)=2162/54145 (.03993).

### STARV — RANDOM VARIABLES
**A. PMF TABLE + CDF** — `Menu("YOU HAVE…","p(x) VALUES",…,"WEIGHTS/COUNTS",…,"CDF VALUES F(x)",…)`; number of
values n (1–20); each x_i and p_i (or weight, or F(x_i)). Sort by x (SortA(ʟx,ʟp)). Check p ≥ 0, Σp = 1
(warn), CDF nondecreasing ending at 1 (warn). Table screens "x  p(x)  F(x)" (≤ 8 rows/screen). Then E[X],
Var(X)=E[X²]−E[X]², SD. Then `Menu("QUERY","P(a≤X≤b) ETC",…,"F(x) AT A POINT",…,"DONE",M)`: P(a≤X≤b),
P(a<X≤b), P(a≤X<b), P(a<X<b) (tolerant comparisons), F(x) = Σ_{x_i≤x} p_i.
Tests: x=2,3,4,5 p=.1,.2,.3,.4 → F=1/10,3/10,3/5,1; E=4; Var=1; a=3,b=4 → 1/2, 3/10, 1/5, 0; F(3.5)=3/10.
CDF mode F=.1,.3,.6,1 → p=.1,.2,.3,.4. Weights 1,2,3,4 → same p.

**B. MAX/MIN/SUM DRAWS** — `Menu("STATISTIC","MAXIMUM",…,"MINIMUM",…,"SUM (2 DRAWS)",…,"|DIFF| (2 DRAWS)",…)`;
N (values 1..N), draws k (2 fixed for sum/diff), `Menu("REPLACEMENT?","WITHOUT",…,"WITH",…)`.
Max w/o: C(z−1,k−1)/C(N,k), z=k..N. Max with: (z^k−(z−1)^k)/N^k. Min w/o: C(N−z,k−1)/C(N,k), z=1..N−k+1.
Min with: ((N−z+1)^k−(N−z)^k)/N^k. Sum/diff: enumerate ordered pairs (i≠j if without). Show the formula
line, table z | p(z) | F(z), and a sketch note (PMF = spikes; CDF = right-continuous steps, jump p(z) at z).
Tests: N=5,k=2,max,w/o → z=2..5: 1/10,1/5,3/10,2/5; F 1/10,3/10,3/5,1. N=6,k=2,max,with → p(z)=(2z−1)/36.
Sum N=6 with → p(7)=1/6. Min N=5,k=2,w/o → 2/5,3/10,1/5,1/10. |diff| N=5 w/o → d=1..4: 2/5,3/10,1/5,1/10.

**C. POLY PDF/CDF** (exact polynomial pieces) — `Menu("INPUT IS…","PDF f(x)",…,"CDF F(x)",…)`; number of pieces
m (1–3); each piece: LO, HI, degree (0–3), coefficients C0 (const), C1 (x), C2 (x²), C3 (x³) up to the degree.
PDF mode first asks "UNKNOWN CONST c? 1=Y 0=N" (then the user enters f without c; c = 1/area; all
coefficients scaled). Area = Σ[G_i(hi)−G_i(lo)], G_i = C0x + C1x²/2 + C2x³/3 + C3x⁴/4. Warn if area≠1 (when c
known) or f<0 somewhere (sample ~11 points per piece). CDF formula: before first piece F=0; on piece i
F = K_i + C0x + (C1/2)x² + (C2/3)x³ + (C3/4)x⁴ with K_i = F(lo_i) − G_i(lo_i) (F continuous, constant across
gaps); after last piece F=1. Display each region with coefficients via STAFMT (only non-zero terms), e.g.
"4<x<6: F=" / "  -1/2 + (1/4)x". CDF mode: pieces are F itself; f = F' = C1 + 2C2x + 3C3x²; warn if F(lo_1)≠0 or
F(hi_m)≠1 (jump) or F decreasing. Then `Menu("QUERY","P(a<X<b)",…,"F(x) AT A POINT",…,"P(X>a)",…,"P(X=a)",…,"BACK",M)`;
P(X=a) → "0 (continuous X)".
Tests: PDF pieces (0,2) C0=1/4 and (4,6) C0=1/4 → area 1; F: 0<x<2 (1/4)x; 2≤x≤4 1/2; 4<x<6 −1/2+(1/4)x;
P(1<X<5)=1/2; F(3)=1/2. PDF (−4,4) C0=3/16, C2=−3/256 → K=1/2, x:3/16, x³:−1/256; P(−4<X<−2)=F(−2)=5/32;
P(1<X<3)=35/128. PDF unknown c, (0,3), degree 2, C2=1 → c=1/9, F=(1/27)x³, P(X>2)=19/27.
CDF (−2,2) degree 1, C0=1/2, C1=1/4 → f=1/4; P(−1<X<1)=1/2; P(X>.5)=3/8.

**D. ANY f(x) OR F(x)** (numeric) — `Menu("INPUT IS…","PDF f(x)",…,"CDF F(x)",…)`; `Input "f(X)=",Str1` (typed
with the X,T,θ,n key); LOW/HIGH end of support (use a big number such as 50 for ∞); PDF mode asks unknown c.
`Str1→Str7`; area = fnInt(expr(Str7),X,lo,hi); probabilities by fnInt over [max(a,lo),min(b,hi)] (0 if empty) times c.
CDF mode: F(t)=0 for t<lo, expr(Str7) on [lo,hi), 1 for t≥hi; P(a<X≤b)=F(b)−F(a); P(X>a)=1−F(a); f(x)=nDeriv(expr(Str7),X,x).
Query menu as in C plus (CDF mode) "f(x)=F'(x) AT PT". Warn if F(lo)≠0 or F(hi)≠1. Show 6-decimal values
(Str8) and a fraction candidate when STAFMT finds one. This tool does not overwrite Y₉ or Y₀.
Tests: CDF "1-𝑒^(⁻2X)" on [0,50): P(X>1)=.135335, f(1)=.270671. PDF "3/256(16-X²)" on (−4,4): P(−4<X<−2)=.15625,
P(1<X<3)=.273438. PDF "X²" on (0,3) unknown c → c=.111111 (1/9), P(X>2)=.703704.

**E. TRANSFORM Y=g(X)** — two intro screens: CDF method (F_Y(y)=P(g(X)≤y) → solve for X → F_X(…) or
1−F_X(…) → differentiate), monotone shortcut f_Y(y)=f_X(h(y))|h'(y)| with h=g^-1, support of Y, and the
probability-integral transform U=F(X) ⇒ F_U(u)=u. Then a numeric checker: f_X in Str7, support LOW/HIGH,
inverse h(y) typed in terms of X in Str6, `Menu("g IS…","INCREASING",…,"DECREASING",…)`, then loop: y value →
x=h(y), F_X(x)=fnInt(expr(Str7),X,lo,clip(x)), F_Y = F_X(x) (incr) or 1−F_X(x) (decr), f_Y = f_X(x)·|nDeriv(expr(Str6),X,y)| (0
outside support). `Menu("AGAIN?","ANOTHER y",…,"BACK",M)`.
Tests: f_X="2X" on (0,1), h="𝑒^(⁻X)", decreasing: y=1 → x=.367879, F_Y=.864665, f_Y=.270671;
y=.5 → F_Y=.632121, f_Y=.735759.

**J. JOINT X,Y** (Freund Ch3 §§5–7) — submenu `DISCRETE PMF` / `CONTINUOUS PDF`.
Discrete mode accepts up to four distinct x values and four distinct y values, followed by all
`p(X=x,Y=y)` cells or nonnegative weights. Weight mode normalizes by the total; probability mode requires
the cells to sum to 1. It displays both marginals, checks `p(x,y)=pX(x)pY(y)` for every cell, and offers
joint-cell, joint-CDF, rectangle, conditional-PMF, and event-predicate queries. Conditioning on a
zero-probability value is reported as undefined.
Continuous mode accepts a typed `f(X,Y)` on rectangular support. It uses nested `fnInt` with
`expr(Str7)` for the total area, optional normalizing constant, rectangle probabilities, `F(x,y)`,
marginal densities, conditional densities, and event predicates. Nonrectangular support can be represented
by multiplying by an indicator such as `(X+Y<1)`; outputs are numeric checks and may be slow or
approximate near discontinuous boundaries. Exact support limits and symbolic proofs remain the
student's work. Tests: a dependent 2×2 PMF `(.1,.2;.3,.4)`, equal-cell independent weights, a
zero-probability condition, uniform `f=1` on the unit square, and a normalized triangular support.

---------------------------------------------------------------------------------------------------
## 5. Content specs (encyclopedia + hints) — tools/content.py format

Screen = header row (topic title + "p/n") + up to **9 body lines of ≤ 26 chars**. Menu items ≤ 18 chars,
page titles ≤ 20, menu titles ≤ 22, ≤ 6 sections, ≤ 6 topics/section, ≤ 6 pages/topic (aim 2–3).
Run `$PY tools/content.py check content/X.json` (must be OK) and `preview` to eyeball.

Style ("short, concise, usable mid-exam"):
* Page 1: the key formula(s) + when to use (recognition cues/keywords).
* Page 2: steps or a worked mini-example in the style of HW1–3 (numbers checked!).
* Page 3 (optional): traps / variations + refs line, e.g. "Freund Ch2 Thm 7; Bert 1.3".
* Point to the matching calculator: "TOOL CALC>PROB>3".
* Notation: `u` union, `n` intersection, `'` complement (A'), `|` given, `C(n,r)`, `nPr`, `Σ`, `∫`, `F(x)`,
  `f(x)`, `x²`, `x^k`, `e^(-2x)`, `√(x)`. Use lowercase freely inside text; menus in UPPERCASE.
* Freund numbering is per chapter (e.g. "Freund Ch1 Thm 3", "Ch2 Def 5", "Ch3 Ex 12"). Cite what you verified.
  Supplement tags: "Bert 1.4" (Bertsekas section numbers as printed in OUR pdf: 1.1 sets, 1.2 models,
  1.3 conditional, 1.4 total prob & Bayes, 1.5 independence, 1.6 counting, 2.1–2.2 RVs/PMFs, 3.1 PDFs,
  3.2 CDFs, 3.6 derived distributions), "Feller II.4", "Wass 1.7", "Ross 3.3".

Textbook page map (PDF page numbers = `=== PAGE n ===` markers):
* Freund: Ch1 Introduction p6–25 (§2 Combinatorial Methods p7, §3 Binomial Coefficients p16);
  Ch2 Probability p26–65 (§2 sample spaces 27, §3 events 29, §4 probability 33, §5 rules 37,
  §6 conditional 42, §7 independent 47, §8 Bayes 50); Ch3 Probability Distributions & Densities p66–103
  (§1 RVs 66, §2 distributions 69, §3 continuous RVs 78, §4 densities 79, §5 joint distributions 87,
  §6 marginal distributions 97, §7 conditional distributions 100); Ch7 Functions of RVs p212–222
  (distribution-function technique 212, transformation technique 216); Ch5 hypergeometric p160.
* Bertsekas: 1.1 p9, 1.2 p12, 1.3 p22, 1.4 p31, 1.5 p37, 1.6 p47; 2.1 p57, 2.2 p59; 3.1 p101, 3.2 p110, 3.6 p139.
* Feller Ch II Elements of Combinatorial Analysis ≈ PDF p46–80 (§4 subpopulations/partitions, §5 occupancy,
  binomial coefficient identities near the end).
* Wasserman: 1.5 Independent events p26, 1.6 Conditional probability p28, 1.7 Bayes right after;
  Ch2 RVs from ≈p37 (2.2 distribution functions ≈p40), 2.11 Transformations p58. (grep to confirm)

### Topic lists
**STAE1 "CH1 COUNTING"** — S1 "COUNTING RULES": MULT PRINCIPLE, PERMUTATIONS, COMBINATIONS (incl. "at least" by
cases/complement), REPEATED LETTERS (glue trick, not-adjacent), PARTITIONS/MULTI (labeled vs unlabeled groups,
grades example), STARS AND BARS (631; lower bounds). S2 "BINOMIAL COEFFS": BINOMIAL COEFF (def, symmetry,
Pascal's triangle), PASCAL IDENTITY (algebraic proof + story proof), BINOMIAL THEOREM, SUM IDENTITIES
(x=1, x=−1, differentiate, integrate — HW1 Q2 full proof outlines), MULTINOMIAL THM (HW1 Q3), VANDERMONDE (631 story proof).
**STAE2 "CH2 PROBABILITY"** — S1 "SETS & EVENTS": SAMPLE SPACE/EVENT, SET OPERATIONS, ENGLISH -> SETS (HW2 Q1),
DE MORGAN LAWS. S2 "PROBABILITY RULES": AXIOMS, BASIC RULES, INCL-EXCL 2 SETS, INCL-EXCL 3 SETS, CLASSICAL
/COUNTING. S3 "CONDITIONAL PROB": DEFINITION, MULTIPLICATION RULE, INDEPENDENCE (vs disjoint; mutual),
2x2 TABLES. S4 "TOTAL PROB & BAYES": TOTAL PROBABILITY, BAYES THEOREM, BAYES EXAMPLES, SENS/SPEC TESTS.
S5 "STA 631 PROOFS": P(A|B)>P(A) PROOF, MULT RULE PROOF (induction), INDEP COMPLEMENTS.
**STAE3 "CH3 RANDOM VARS"** — S1 "DISCRETE RVs": RANDOM VARIABLE, PMF, DISCRETE CDF, PMF OF MAX/MIN (HW3 Q1),
SKETCH PMF/CDF. S2 "CONTINUOUS RVs": PDF BASICS, P(X=a)=0, FIND CONSTANT c, BUILD CDF PIECEWISE (HW3 Q2),
CDF -> PROBS (HW3 Q3), PDF <-> CDF (HW3 Q4, Q6). S3 "JOINT / MARGINAL": joint PMF/PDF/CDF,
marginal and conditional laws, independence, and mixed-distribution cautions from Freund Ch3 §§4–7.
S4 "STA 631 EXTRAS": CDF METHOD Y=g(X), MONOTONE FORMULA, PROB INTEGRAL XFORM, COMMON CDFs
(uniform, exponential). S5 "CALCULUS HELP": INTEGRALS, DERIVATIVES, TI-84 fnInt/nDeriv
(MATH menu keystrokes; nCr/nPr/! in MATH>PRB).
**STAHNT "WHICH TOOL?"** — S1 "HOW MANY WAYS?": ORDER MATTERS?, REPEATED ITEMS, SPLIT INTO GROUPS,
AT LEAST/EXACTLY, IDENTICAL ITEMS, COEFF IN EXPANSION. S2 "PROBABILITY Qs": AND/OR/NOT, GIVEN/IF/AMONG,
TWO-STAGE SOURCE, REVERSE (WHICH ONE), TABLE OF COUNTS, OVERLAPPING GROUPS. S3 "RANDOM VAR Qs": PMF OF
MAX/MIN/SUM, FIND CONSTANT c, PDF -> CDF, CDF -> PROBS, CDF -> PDF, EXACTLY x (CONT.). S4 "PROOF Qs": PASCAL,
BINOMIAL SUMS, VANDERMONDE, MULT RULE (n), P(A|B)>P(A), TRANSFORM/PIT. S5 "KEYWORD -> TOOL": COUNTING WORDS,
PROBABILITY WORDS, RV WORDS. S6 "FORMULAS+STRATEGY": FORMULAS COUNT, FORMULAS PROB, FORMULAS RV, CHECKLIST,
COMMON TRAPS. Every hint page ends with the tool path (e.g. "TOOL CALC>COUNT>2") and/or encyclopedia path
("SEE ENC>CH1>COUNTING RULES").

---------------------------------------------------------------------------------------------------
## 6. Simulator requirements (tools/tisim.py) — written by the harness agent

Purpose: run our TI-BASIC programs off-device to test logic. It must load a program from `src/NAME.txt`,
clean it with `tibuild.clean_source`, tokenize with `tibuild.tokenize`, decode with tivars, and interpret the
**token stream** (so tokenization mistakes surface as errors, exactly like the calculator).

Python API:
```python
from tisim import Sim, TIError
sim = Sim(src_dir)                                  # finds NAME.txt files
res = sim.run("STACNT", actions=[{"menu":1},{"input":"5"},{"input":"2"}], max_steps=2_000_000)
res.screens      # list of snapshots; each = {"event": "pause"|"menu"|"input"|"getkey"|"end"|"error",
                 #   "rows": [10 strings of 26 chars], "menu": {...} when event=="menu", "prompt": ...}
res.text         # all snapshots rendered as text (for grep/assert)
res.vars         # final variables: reals, strings, lists, equations
res.leaks        # number of block frames abandoned by Goto/Menu (must be 0)
res.error        # None or "ERR:DOMAIN at STACNT line 57: ..." (programs must not error)
res.ended_reason # "return" | "stop" | "end" | "out_of_actions" | "error" | "max_steps"
```
CLI: `$PY tools/tisim.py run src STACNT --actions '[{"menu":1},{"input":"5"}]'` prints the snapshots.

Action queue semantics: `Menu(` consumes the next `{"menu": n}` (1-based; error if the head is not a menu
action or n is out of range); `Input`/`Prompt` consume `{"input": "text"}` — text is what the user types
(tokenize it with tivars in *expression* mode; `"3/16"`, `"⁻1"`, `"{1,2}"`, `"1-𝑒^(⁻2X)"`, or letters for a
string var); `getKey` returns the head `{"key": code}` if present, otherwise 105 (ENTER); `Pause` snapshots and
continues. When a program needs an action and the queue is empty → stop with ended_reason "out_of_actions".

Must implement faithfully: statements `:`/newline; If/Then/Else/End, For(/While/Repeat/End, Lbl/Goto (label
search from top; ERR:LABEL), Menu(, Return (return to caller or end), Stop, prgmNAME calls (shared globals),
Disp (multi-arg; strings left, numbers right-aligned; scrolling), Output( (wrap, clip), ClrHome, Pause [val],
Input/Prompt, DelVar, FnOff/FnOn (no-op), Normal/Float (no-op), store `→` to reals, lists, list elements
(extend by one allowed), `→dim(`, strings, Y-vars (store a string), getKey. Expressions with the TI order of
operations: (1) prefix functions, (2) postfix ² ³ ⁻¹ !, (3) ^, (4) negation ⁻, (5) nPr nCr, (6) * / and implied
multiplication (left-to-right), (7) + −, (8) relations = ≠ < > ≤ ≥ (return 1/0; also string =/≠),
(9) and, (10) or xor. A leading binary minus is ERR:SYNTAX. Functions: abs int iPart fPart round(x[,d])
max min (2 args or list) sum dim cumSum seq( augment( SortA( SortD( sub( length( inString( expr( toString(
ln log 𝑒^( ₁₀^( √( remainder( gcd( lcm( not( fnInt( nDeriv( and Y₀–Y₉ evaluation (Y₉ and Y₉(v)); list literals,
elementwise list arithmetic; Ans; π; real vars default 0; undefined lists/strings → ERR:UNDEFINED.
Numbers print TI-style (10 significant digits, no leading zero ".5", negative "⁻", scientific "1.5ᴇ12"
outside [1ᴇ⁻3, 1ᴇ10)); toString( uses the same format. nCr/nPr with r>n → 0; non-integer → ERR:DOMAIN.
Leak tracking: a Goto/Menu that leaves open blocks increments `leaks`. Step limit → "max_steps".
fnInt: adaptive Gauss–Kronrod or Simpson to ~1e-10 relative; nDeriv: symmetric difference, h=1ᴇ⁻3.

tools/tilint.py (static): labels unique & every Goto/Menu target exists; blocks balanced; Else only inside a
Then block; Goto/Menu( inside an open block → ERROR; Menu ≤ 7 options, title ≤ 22, items ≤ 18; Output row/col in
range and literal fits; Disp literal ≤ 26; Input prompt literal ≤ 16; formatter misuse (reading Q–V right after
prgmSTAFMT as if they held caller data) → WARN. CLI: `$PY tools/tilint.py src/STACNT.txt`.
