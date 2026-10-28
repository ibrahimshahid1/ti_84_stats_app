# PLAN.md — STA 431 Midterm II TI-84 Plus CE suite (shared build brief)

Author: prime agent (lead engineer). Audience: the builder agents who implement packages P1 to P8,
**one at a time and in order**. Each builder sees this file, the repo, and its package id. It sees
nothing else, so every rule a builder needs is written here.

---------------------------------------------------------------------------------------------------
## 0. Read this first (every builder)

* APP = `/home/user/ti_84_stats_app/STA431_TI84_App/midterm2_app`. Run every command from APP.
  Python is `python3`, and `tivars`, `mpmath` and `sympy` are installed.
* Implement **only your package** (§7). Earlier packages are already in the repo. Do not start later
  packages. You may make small fixes elsewhere when your acceptance tests need them; list each one at
  the top of your main test file under a comment headed `# PLAN DEVIATIONS / EXTRA FIXES`.
* Never modify `../dev/` (the Midterm I suite, which is frozen),
  `/home/user/ti_84_stats_app/texts/` or `/home/user/ti_84_stats_app/homework/`. Never run
  `git commit` or `git push`.
* **STA 431 ONLY.** The student said: use ONLY the STA 431 problems and do not incorporate the
  "STA 631 Only" problems. No 631 problem, model, preset, test, hint or doc line may exist anywhere.
  `tests/test_lint_all.py` (P1) enforces this.
* **Generated files are never hand-edited.** These are:
  * `content/*.json` and the programs generated from them (`src/M2E4.txt`, `M2E5`, `M2E6`, `M2HLP`,
    `M2HW`, plus `M2ENC` until P7), which come from `tools/write_content.py` and then
    `tools/content.py gen`;
  * `src/M2RUN.txt`, which comes from `tools/write_presets.py`;
  * `src/M2FIND.txt`, which comes from `tools/write_finder.py` (P8).

  Edit the generator and regenerate. `tools/build_package.py` regenerates everything anyway.
* **No stored homework answers.** Presets load the DATA of a problem, and the general solvers
  compute every number. Walkthrough pages show the setup and method but no final numeric answers.
* **Definition of done** for every package:
  1. `for t in tests/test_*.py; do python3 $t || exit 1; done` is green.
  2. `python3 tools/build_package.py ../output/STA431_Midterm_II_Calculator_Package` succeeds. It
     regenerates content, lints, runs every test, builds the .8xp files, checks the memory budget
     and writes the package plus its .zip.
  3. `START_HERE.md` is updated for every change a user can see.
  4. Both linters report 0 errors and 0 warnings.
* Expected values in tests come from **sympy, or exact `fractions.Fraction` arithmetic, computed
  inside the test**. Never take them from a run of the app. Every feature also needs at least one
  NON-homework variant (different numbers or functions); see Appendix C for verified targets.
* If something here proves impossible as written, implement the closest behaviour that meets the
  intent of the acceptance criteria, and document the change under `# PLAN DEVIATIONS`.

---------------------------------------------------------------------------------------------------
## 1. Goal, scope and sources

The student takes STA 431 (Intro to Probability). Midterm II covers Freund (Miller & Miller, *John E.
Freund's Mathematical Statistics with Applications*, 8th ed.) Ch. 3 §5–7 and Ch. 4. The student
does not know TI-BASIC. They want a TI-84 Plus CE program suite, launched from PRGM, in the style
of their Midterm I suite (`../dev/src/STA431.txt`), with this shape:

* ENCYCLOPEDIA: notes for every topic below, organised by the study guide and textbook, with each
  page citing Freund.
* SOLVERS: one solver for every question type. The exam reuses the homework questions with
  different numbers and functions, so adapting a solver to a new question must be EASY, and output
  should be EXACT where TI-BASIC can manage it.
* HELP: the use cases for each solver, plus a click-through finder ("describe the question → the
  suggested solver and recipe").
* HOMEWORK PRACTICE: walkthroughs and load-data presets for the STA 431 problems only.
* QUIT.

**Topic list (the student's words, condensed).**
* Unit 4, multivariate random variables: joint, marginal and conditional distributions; deriving
  one distribution function from another; justifying independence and its properties; computing
  probabilities from the distribution functions you have; converting word problems to notation;
  integration limits.
* Unit 5, Ch. 4 expectation: E[X], E[g(X)] and their properties; moments about the origin (the
  mean) and about the mean (the variance); MGFs (definition, uniqueness, deriving moments,
  transformations).
* Unit 6: product moments (covariance, correlation, and independence vs zero covariance); one and
  two linear combinations; conditional expectation.

**Mandatory student requirements** in `STUDENT_REQUIREMENTS.md` override this plan:
* R1, joint CDF solver → P4 (M2CDF). The "given f, find F at a point" part is delivered through
  M2JNT in P3.
* R2, support and integration-limits helper → P2 (M2JNT EVENTS + LIMITS).
* R3, tests → P2 (region homework problems), P4 (CDF variants) and P6 (HW4 Q4 through the
  discrete event menu).
* R4, encyclopedia pages (f↔F, the rectangle formula, sketching regions) → P7.

**Homework (STA 431 only).** The text is in `../tmp/pdfs/sources/hw4.txt` and `hw5.txt`.
* HW4 Q1, Q2, Q3 (common), plus HW4 Q4 and Q5 (the "STA 431 Only" problems).
* HW5 Q1–Q7 (common), plus HW5 Q8 (the STA 431 version: joint PMF (x+y)/36 on {1,2,3}²).
* Never use HW4's 631 Q4 or Q5, or HW5's 631 Q8.

**Sources.** The pre-extracted text is in `../tmp/pdfs/sources/`.
* `freund.txt` is the full book; page footers are the printed page numbers.
* `freund_ch4.txt` is Ch. 4 with `===PDF PAGE n; PRINTED m===` markers.
* `outline.txt` is the course study guide ("Guide"), keyed to Freund. Units 4–6 are Midterm II,
  with mock exams 4, 5 and 6 and the Mock Midterm II on p. 98.
* `bertsekas.txt` (BT), `wasserman.txt` (W) and `feller.txt` are secondary texts.

Cite Freund Def/Thm/Ex numbers with **printed** page numbers (index in Appendix E).

---------------------------------------------------------------------------------------------------
## 2. State before P1 (summary of four audits)

* There are 11 programs in `src/`: STAM2, M2EXAM, M2DISC, M2CONT, M2SLICE, M2COV, M2MGF, M2ENC
  (generated), M2HW (generated), M2RUN (generated) and M2FMT. All 8 test files pass (162 checks).
* `build_package.py` FAILS because line 60 of `src/STAM2.txt` contains `<=`. The linter calls it
  "STAM2:59" because it counts cleaned lines. M2EXAM.8xp was therefore never built, and `out/` is
  stale (its STAM2.8xp is the old launcher).
* The math in the encyclopedia and the homework map is correct, and all 13 STA 431 targets were
  verified. The numerics are wrong in three places:
  * the DOUBLE INTEGRAL's outer Simpson rule prints wrong but exact-looking fractions on triangles
    (819/2048 for 2/5);
  * it is badly wrong with exponential densities over long cutoffs (.119 for 2/3);
  * the typed-MGF derivatives are off in the 3rd–4th significant digit (Var 11.988 for 12), and a
    uniform MGF crashes it (M is evaluated at 0).
* Coverage gaps:
  * no symbolic marginal or conditional formulas;
  * no infinite supports;
  * only two MGF templates;
  * Cov and ρ of a joint PDF take 5 separate runs;
  * linear combinations are limited to n ≤ 3, with no correlation input;
  * no CDF tools;
  * HELP is not the requested shape.
* STA 631 material is in M2HW, M2RUN, M2CONT (preset codes 21–23), write_content.py,
  write_presets.py, tests and START_HERE.
* Tests choose menus by hard-coded index, so removing the 631 menu items breaks 19 tests.
* Memory: Midterm I takes 139 KB and Midterm II about 68 KB, while CE user RAM is about 154 KB.
  The student must archive Midterm I.

I (the prime agent) verified the new engine design in the simulator myself (see Appendix A):
* coefficient recovery of a typed polynomial q(X,Y) from 25 samples: error ≤ 3e-12, about 370 steps;
* convex-polygon clipping plus vertical-strip Gauss–Legendre integration: exact to 1e-13 for
  polynomials, in both orders of integration, under 1,500 steps per event;
* graded panels with an automatic cutoff on infinite supports: error ≤ 5e-9 on pass 1 and ≤ 1e-10
  on pass 2 for exponential-type densities.

---------------------------------------------------------------------------------------------------
## 3. Final architecture

### 3.1 Programs (final state after P8)

| Program | Role | Source | Package | Budget (tokenized bytes) |
|---|---|---|---|---|
| STAM2  | launcher: main menu, submenus | hand | P1 (menus extended P2,P4,P7,P8) | 2,000 |
| M2FMT  | number formatter (W → Str9 fraction/int, Str8 decimal) | hand (unchanged) | — | 300 |
| M2GL   | **integration kernel** library (GL 7×5 product rule on strips; graded panels; infinite tails) | hand | P2 | 3,000 |
| M2PLY  | **polynomial library**: coefficient recovery, line/poly → string, strip marginals, cancellation | hand | P2 (part 1), P3 (part 2) | 4,000 |
| M2JNT  | **joint density solver**: model + support, EVENTS + LIMITS, FORMULAS, MOMENTS, GIVEN A VALUE, INDEP + CDF | hand | P2, P3 | 12,000 |
| M2CDF  | joint CDF solver (R1) + exponential-pair template | hand | P4 | 4,000 |
| M2ONE  | one-variable density solver (replaces M2CONT) | hand | P4 | 4,000 |
| M2MGF  | MGF library: derive, identify, typed numeric, Z=aX+b, sums | hand (rewrite) | P5 | 7,000 |
| M2COV  | linear combinations hub (n ≤ 4, COV/CORR/indep, pair info, E[poly]) | hand (rewrite) | P6 | 5,000 |
| M2DISC | discrete tables (grid/rows/pairs/univariate, events, CDF, derived pair, formulas) | hand (upgrade) | P6 | 8,000 |
| M2E4   | encyclopedia Unit 4 (multivariate) | generated | P7 | 12,000 |
| M2E5   | encyclopedia Unit 5 (expectation, moments, MGF) | generated | P7 | 12,000 |
| M2E6   | encyclopedia Unit 6 (product moments, combos, conditional E) | generated | P7 | 12,000 |
| M2HLP  | HELP pages: solver use cases, keys, notation, workflow, memory/errors | generated | P7 | 6,000 |
| M2FIND | finder "describe the question → solver + recipe" (replaces M2EXAM) | generated | P8 | 8,000 |
| M2HW   | homework walkthroughs, STA 431 only, no final answers | generated | P8 | 7,000 |
| M2RUN  | load-data presets (HW + Freund examples + Mock Midterm II) | generated | P8 | 4,000 |

The budgets add up to about 110,300 tokenized bytes, plus about 1,300 bytes of .8xp headers, for
roughly 111.6 KB. A program may exceed its own budget by up to 15% as long as the TOTAL stays
≤ 118,000 bytes.

Programs **removed**: M2SLICE and the DOUBLE INTEGRAL in M2CONT (P3), M2CONT itself (P4), M2ENC (P7)
and M2EXAM (P8). None of the new names collides with the Midterm I names (STA431, STAE1-3, STAHNT,
STACNT, STAPRB, STARV, STAFMT).

**Memory budget.** The total of the .8xp file sizes must be ≤ **118,000 bytes**, with a target of
≤ 112,000. That leaves about 35 KB of the CE's roughly 154 KB user RAM for variables.
`tests/test_lint_all.py` enforces it from P1 on, using the estimate
`sum(tokenized) + 100·programs`. Every program must stay in RAM (unarchived), because
subprograms are called with `prgmNAME`, so the Midterm I suite must be archived (START_HERE says
how).

### 3.2 Final menu tree (item texts are FIXED; paths and tests rely on them)

```
STAM2  Menu("STA431 MIDTERM II","ENCYCLOPEDIA","SOLVERS","HELP","HOMEWORK PRACTICE","QUIT")
├ ENCYCLOPEDIA  Menu("ENCYCLOPEDIA","U4 MULTIVARIATE","U5 EXPECT + MGF","U6 PRODUCT + COND","BACK")  → prgmM2E4/M2E5/M2E6
├ SOLVERS       Menu("SOLVERS","DISCRETE TABLE","JOINT DENSITY","CDF OF X AND Y","ONE-VAR DENSITY","MGF TOOLS","LINEAR COMBOS","BACK")
│   DISCRETE TABLE → M2DISC   entry Menu("DISCRETE TABLE","FORMULA ON GRID","TABLE BY ROWS","LIST EACH PAIR","ONE VARIABLE","BACK")
│                             joint tools Menu("TABLE TOOLS","MOMENTS + COV","MARGINALS","CONDITIONALS","EVENTS + CDF","MORE TOOLS","NEW DATA","BACK")
│                             univariate Menu("ONE-VAR TABLE","MOMENTS","PROB + CDF","E[g(X)]","MGF M(t)","SHOW/EDIT TABLE","NEW DATA","BACK")
│   JOINT DENSITY  → M2JNT    Menu("JOINT DENSITY","NEW MODEL","EVENTS + LIMITS","FORMULAS","MOMENTS + COV","GIVEN A VALUE","INDEP + CDF","BACK")
│   CDF OF X AND Y → M2CDF    Menu("JOINT CDF","NEW F(X,Y)","RECTANGLE PROB","MARGINAL CDFs","PDF f FROM F","F FROM A PDF f","EXP PAIR TEMPLATE","BACK")
│   ONE-VAR DENSITY→ M2ONE    Menu("ONE-VAR DENSITY","NEW DENSITY","MOMENTS","PROB + CDF","E[g(X)]","CDF FORMULA","BACK")
│   MGF TOOLS      → M2MGF    Menu("MGF TOOLS","FROM A DENSITY","KNOWN FAMILY","TYPED M(t)","Z=aX+b OF LAST","SUM OF COPIES","BACK")
│   LINEAR COMBOS  → M2COV    Menu("LINEAR COMBOS","ENTER MOMENTS","E + VAR OF U","COV + CORR U,V","PAIR INFO","E[POLY(X)]","BACK")
├ HELP          Menu("HELP","FIND MY SOLVER","HELP PAGES","BACK")  → prgmM2FIND / prgmM2HLP
├ HOMEWORK PRACTICE Menu("HOMEWORK PRACTICE","WALKTHROUGHS","LOAD PRACTICE DATA","BACK") → prgmM2HW / prgmM2RUN
└ QUIT  → ClrHome, then the last line of STAM2 is "" (no "Done")
```
**Interim states.**
* P1: SOLVERS = DISCRETE TABLE, DENSITY+INTEGRAL (M2CONT), MGF TOOLS, LINEAR COMBOS, BACK.
  ENCYCLOPEDIA calls prgmM2ENC directly. HELP = FIND MY SOLVER (prgmM2EXAM), HOW TO ENTER,
  LIMITS + CAVEATS, BACK. HOMEWORK PRACTICE = WALKTHROUGHS (M2HW), LOAD PRACTICE DATA (M2RUN).
* P2: "JOINT DENSITY" is inserted after DISCRETE TABLE.
* P4: "CDF OF X AND Y" is inserted, and "DENSITY+INTEGRAL" becomes "ONE-VAR DENSITY" (M2ONE).
* P7: the ENCYCLOPEDIA submenu is added, and HELP gets "HELP PAGES" (M2HLP) in place of the two
  interim items.
* P8: FIND MY SOLVER calls M2FIND.

**Path codes** (used in encyclopedia TOOL lines, HELP, the finder and walkthroughs). A path is
written like `SOLV>JOINT>EVENTS>MIN`.
* The first token is SOLV, ENC, HELP or PRAC.
* Each later token must be a prefix of the FIRST WORD of exactly one item in the menu reached at
  that level. The prefix is at least 3 characters, or the whole word when the word is shorter, as
  with `F` or `E`. The menu item texts above are chosen so that first words are
  unique within each menu. Keep it that way: `tests/test_paths.py` (P7) checks it.
* Inputs (model entry) between menus are implied. A path is at most 26 characters including the
  `TOOL ` prefix, so use short submenu tokens.

### 3.3 Library call graph

```
M2JNT ──prgmM2GL (θ=1 2D, θ=2 1D)──┐       M2ONE ──prgmM2GL θ=2, prgmM2PLY
      └─prgmM2PLY (θ=1..8)─────────┤       M2CDF ──prgmM2PLY (recover F, strings), prgmM2JNT (Z=97: F from f)
M2DISC ──prgmM2PLY (θ=3,7 marginal formula), prgmM2COV (Z=99 handoff)
every program ──prgmM2FMT (W→Str8/Str9)
```

---------------------------------------------------------------------------------------------------
## 4. Conventions (MUST follow)

### 4.1 TI-BASIC source rules (the linters enforce most of them)
Source files are UTF-8 `.txt` files in `src/`. The file stem is the program name (≤ 8 characters,
A–Z/0–9, starting with a letter). The full rules are in `../dev/SPEC.md` §2–3 (read it). In short:
1. Negation is `⁻`; `-` is binary minus only. The exponent marker is `ᴇ` (`1ᴇ⁻9`, `ᴇ99`). The
   store arrow is `→`.
2. Lowercase letters only inside strings. Use `𝑒^(`, `√(`, `≤ ≥ ≠`, and `nCr` with spaces around it.
3. Never `Goto` or `Menu(` inside an open If-Then, For(, While or Repeat block. Put every `Menu(` at
   block depth 0, and only use the `If cond:Goto L` one-liner at depth 0. A `prgmX` call inside a
   block is fine.
4. Menu( takes at most **7** options (6 + BACK). Title ≤ 22 characters, option ≤ 18, labels of
   1–2 characters. The simulator and tilint both enforce 7, so do not use more.
5. `Input` prompt ≤ 16 characters; `Disp` string ≤ 26; `Output(` text must fit in its row. No colon
   inside strings; no `->`, `<=`, `>=`, `!=` anywhere in strings (use ≤ ≥ ≠).
6. Subprograms end with `Return`, never `Stop`. Use `If cond` without `Then` for a single statement.
7. No `""` literal except as the very last line of STAM2. Do not use L₁–L₆, matrices or Y= variables
   (they are user data). Tests check that they are preserved.
8. Lint after every edit with `python3 tools/tibuild.py lint src` and `python3 tools/tilint.py src`.
   Both must report 0 errors and 0 warnings.
9. Speed: the CE runs TI-BASIC at roughly 1–3 ms per statement, and an `expr(` evaluation costs
   several ms. Prefer whole-list operations (`sum(ʟA*ʟB)`, `seq(`, `augment(`, `SortA(`) to element
   loops. Each package gives step budgets (`res.steps` in the simulator), and tests assert them.

### 4.2 Variables, strings, lists (global CE state is shared by every program)
| Register | Use |
|---|---|
| `W` | M2FMT input (not modified by M2FMT); **clobbered by M2GL and M2PLY** |
| `Q R S T U V` | **clobbered by M2FMT, M2GL and M2PLY**. Never keep live data in Q–W across any `prgmM2FMT`/`prgmM2GL`/`prgmM2PLY` call |
| `I J K O X Y` | loop/eval registers, **clobbered by M2GL and M2PLY** (X,Y are also the expression variables) |
| `θ` | library mode IN / status OUT for M2GL and M2PLY (clobbered by those calls) |
| `Z` | program routing code (§4.3) — each program reads it at entry then sets `0→Z` |
| `A B C D E F G H L M N P` | module-local; survive M2FMT/M2GL/M2PLY calls (the libraries never touch them). Libraries needing more scratch use their own list cells |

So the libraries may use only `I J K O X Y θ Q R S T U V W` and their own lists. The prototypes in
Appendix A use other letters. Rename them when you adopt the code.

| String | Use |
|---|---|
| Str1 | model expression (q(X,Y), q(X), F(X,Y), typed M(X)) |
| Str2, Str3 | secondary expressions (curved bounds, event/given typed text, U(X,Y)/V(X,Y)) |
| Str4 | M2DISC support condition (`"1"` = all) / spare |
| Str5 | kernel multiplier g (`"1"` = none) |
| Str6 | M2PLY input (variable letter `"x"`/`"y"`) |
| Str7 | M2PLY output string |
| Str8, Str9 | M2FMT output (decimal / fraction-or-decimal) |
| Str0 | screen-building scratch |

**Named lists** have the form `ʟ` + 1–5 characters. Each program uses only its own prefix, and it
DelVars every list it created when the user leaves through BACK. Library temporaries (ʟM2K*, ʟM2Q*)
are deleted by the solver that called the library, when that solver exits.
| Prefix | Owner |
|---|---|
| `ʟM2X ʟM2Y ʟM2P ʟM2G ʟM2W ʟM2PR ʟM2AX ʟM2AY ʟM2D*` | M2DISC |
| `ʟM2J*` (e.g. ʟM2JM model, ʟM2JX/ʟM2JY polygon, ʟM2JS strips, ʟM2JE/ʟM2JA/ʟM2JB events, ʟM2JR results) | M2JNT |
| `ʟM2K*` | M2GL: GL7 constants ʟM2KT/ʟM2KW, GL5 constants ʟM2KU/ʟM2KV, strips IN ʟM2KS, options ʟM2KO, results ʟM2KR/ʟM2KP, scratch ʟM2KZ and node lists |
| `ʟM2Q*` | M2PLY (ʟM2QA table, ʟM2QC/ʟM2QN/ʟM2QD 1-D coefficient lists, ʟM2QS args, ʟM2QR roots) |
| `ʟM2O*` | M2ONE | 
| `ʟM2F*` | M2CDF |
| `ʟM2M*` | M2MGF (ʟM2MF family record, ʟM2MX/ʟM2MP finite PMF, ʟM2MD diffs) |
| `ʟM2C* ʟM2MU ʟM2VR` | M2COV (ʟM2MU means, ʟM2VR variances, ʟM2CV N² covariances, ʟM2CF flags, ʟM2CA/ʟM2CB coeffs, ʟM2CR results) |

### 4.3 Program interfaces

**Z routing codes.** `Z=0` is normal entry and shows the program's top menu. **`Z=99`** means the
model is PRELOADED in the documented variables: the program skips the input prompts, validates and
normalises the model, shows its summary screen, then shows the analysis menu. `Z=97` is
M2JNT-only: run NEW MODEL, then go straight to the F(s,t) prompt (used by M2CDF "F FROM A PDF f").
A program must `0→Z` right after reading Z. Old codes (1, 2, 3, 4, 5, 11–18) are retired when a
package migrates that solver's presets to Z=99.

**Z=99 preload layouts** (presets and handoffs write these, then `99→Z:prgmNAME`):
| Program | Preloaded variables |
|---|---|
| M2DISC | `ʟM2AX`, `ʟM2AY` (`{0}` = univariate), `Str1`=q(X,Y), `Str4`=support (`"1"`) — grid mode |
| M2JNT | `Str1`=q(X,Y); `ʟM2JM`=support record (§7 P2); `Str2`,`Str3` only for curved code 8 |
| M2ONE | `Str1`=q(X); `ʟM2OM={a,b}` (±ᴇ99 = ±∞) |
| M2CDF | `Str1`=F(X,Y); `ʟM2FM={a,b,c,d}` |
| M2MGF | `ʟM2MF`=family record (§7 P5); for finite PMF also `ʟM2MX`,`ʟM2MP` |
| M2COV | `N`; `ʟM2MU` (N), `ʟM2VR` (N), `ʟM2CV` (N², row-major), `ʟM2CF={means known 1/0}` |

**M2FMT (unchanged).** Input W. Output Str9 = the integer, or a fraction N/D when D ≤ 9999,
|W| < 1000 and the error < 1E-10; otherwise the decimal. Str8 = the decimal rounded to 6 places.
It clobbers Q–V.

**M2GL integration kernel** (P2). The mode is read from θ. It clobbers I J K O X Y θ, Q–W and
ʟM2K* temporaries. It never calls M2FMT.
* **θ=1 (2-D).** Integrates over the strips in `ʟM2KS`. Each strip is 7 numbers
  `x0,x1,l0,l1,u0,u1,kind`: the outer variable runs over [x0,x1], and the inner variable runs from
  l0+l1·s to u0+u1·s, where s is the outer value. kind 0 = linear limits; kind 1 = curved, where
  the limits are `expr(Str2)` and `expr(Str3)` evaluated at the outer value (X outer only). A
  number with |v| ≥ 1ᴇ6 means infinity (BIG = 1ᴇ6; for example x1=1ᴇ6 or u0=1ᴇ6 with u1=0).
  * Options `ʟM2KO={orient,mode}`.
    * orient: 0 = the outer variable is X; 1 = the outer variable is Y and the inner one is X. The
      strips are then written in (y,x) coordinates.
    * mode: 1 = EXACT (one GL7×GL5 panel per strip, finite strips only); 2 = NUMERIC pass 1; 3 =
      NUMERIC pass 2 (§4.6).
  * Integrand: `expr(Str1)`, times `expr(Str5)` for the g-moments when `Str5≠"1"`.
  * Output `ʟM2KR = {∫q, ∫Xq, ∫Yq, ∫X²q, ∫Y²q, ∫XYq, ∫gq, ∫g²q, min q seen}` in TRUE X,Y
    coordinates whatever the orient, plus `ʟM2KP` = ∫q per strip, for the written pieces.
* **θ=2 (1-D).** Integrates over `ʟM2KS={a,b}`, with ±1ᴇ6 meaning ±∞.
  * `ʟM2KO={var,mode}`: var 0 integrates in X; var 1 integrates in Y with X held at its current
    value (for slices).
  * Output `ʟM2KR={∫q, ∫vq, ∫v²q, ∫v³q, ∫v⁴q, ∫gq, ∫g²q, min q}`, where v is the integration
    variable.
* The kernel is EXACT up to rounding (about 1e-13) for any polynomial q of degree ≤ 4 in each
  variable, together with every built-in moment (r+s ≤ 4) and g of degree ≤ 2 in each variable.
  (For 1-D: q of degree ≤ 4, moments up to v⁴, and g of degree ≤ 4.) GL7 is exact up to degree 13
  and GL5 up to degree 9.

**M2PLY polynomial library** (P2 part 1, P3 part 2). The mode is read from θ; it returns θ=1 for OK
and θ=0 for failure. It clobbers I J K O X Y θ, Q–V and W (it calls M2FMT), plus ʟM2Q* temporaries.
| θ | Name | In → Out |
|---|---|---|
| 1 | RECOVER2 | `Str1`=q(X,Y) → `ʟM2QA` (25 numbers, element `5i+j+1` = coefficient of X^i·Y^j, i,j=0..4). θ=0 if it is not a polynomial of degree ≤4 in each variable; this is checked at 2 off-grid points with relative tolerance 1ᴇ⁻9. Before sampling, use `inString` to pre-screen for the tokens `√(`, `ln(`, `log(`, `𝑒^(`, `^(` and `^.`. Any of them means "not a polynomial" (θ=0) without sampling. This avoids ERR:NONREAL at negative nodes and saves time. Sampling nodes are X,Y ∈ {⁻3/2,⁻1/2,1/2,3/2,5/2}, which avoids 0 and the integers, so 1/X and 1/(1-X) never divide by zero. Coefficients below 1ᴇ⁻11·max are set to zero. Appendix A.3 is validated code. A q(X) without Y gives a table whose j>0 entries are 0. |
| 2 | LINESTR | `ʟM2QS(1)`=l0, `ʟM2QS(2)`=l1, `Str6`=`"x"` or `"y"` → `Str7` like `1-x`, `x/2`→ render as `(1/2)x`, `2`, `INF`, `-INF`. Negative numbers render with `-` (never `⁻`). |
| 3 | POLYSTR | `ʟM2QC` = coefficients for powers 0..n of `Str6` → `Str7`, e.g. `3/2-3/2y²`, `4x-4x³`, `0`. Rules: skip zero terms; coefficient 1/−1 omitted except constant; powers `x`, `x²`, `x³`, `x^4`…; first term no `+`. |
| 4 | POLY2STR | `ʟM2QA` (n×n, n in `ʟM2QS(3)`, element `n·i+j+1`) → `Str7` in x and y, ordered by total degree then by x-power descending, e.g. `1/2x²y+1/2xy²`. (P3) |
| 5 | STRIPMARG | `ʟM2QA` (5×5), strip `ʟM2QS={x0,x1,l0,l1,u0,u1,s}` → `ʟM2QC` = coefficients of ∫_{l0+l1x}^{u0+u1x} y^s·q(x,y) dy as a polynomial in x (length 12). Build powers of the line polynomials by `augment` shifts (`P→u0*augment(P,{0})+u1*augment({0},P)`); never use `^` with a possibly-zero base and exponent 0 (0^0 = ERR:DOMAIN). (P3) |
| 6 | CANCEL | numerator polynomials (`ʟM2QN`, either 1-D length n or 2-D table with column count in `ʟM2QS(4)`) over denominator `ʟM2QD` (1-D, same variable) with candidate roots `ʟM2QR` → cancels every common linear factor (x−r) for r in `ʟM2QR∪{0,1,⁻1}` by synthetic division (zero test 1ᴇ⁻9·scale), then divides all by the lowest-degree nonzero coefficient of `ʟM2QD`. (P3) |
| 7 | RECOVER1S | `ʟM2QS` = 5 samples at the standard nodes {⁻3/2,…,5/2} → `ʟM2QC` (degree ≤ 4 coefficients) using the same inverse-Vandermonde constants. (P3) |
| 8 | VARCHECK | `Str1`, allowed letters in `Str6` (e.g. `"XY"`) → θ=0 if Str1 contains any single-letter variable token A–Z or θ not in Str6. (P2) |

### 4.4 Input conventions (screen hygiene)
* Before every `Input`: `ClrHome`, then at least one `Disp` header that gives an example and any key
  hint. A prompt must never be drawn over an old result screen.
* Expressions use the calculator's variables X and Y (X = the [X,T,θ,n] key; Y = ALPHA 1).
  Comparisons come from 2nd MATH (TEST); `𝑒^(` is 2nd LN; lists use `{ }` (2nd ( 2nd )); negative
  numbers use the (-) key; fractions use the ÷ key (it displays /).
* **Infinity is `ᴇ99`** (2nd , 9 9) and −∞ is `⁻ᴇ99`. Any |value| ≥ 1ᴇ50 typed as a bound means
  ±∞. A finite bound must satisfy |v| < 1ᴇ5.
* Validate inputs and re-prompt with a message; never let a bad input crash. Guards:
  * reject expressions that use variables the tool does not set (M2PLY θ=8): q(X) may use only X;
    q(X,Y) only X and Y; a typed MGF only X (meaning t);
  * reject an upper bound below the lower bound;
  * reject a non-linear bound where linear bounds are required;
  * reject a polynomial q on an infinite support.
* Solvers KEEP the current model between analyses (no re-entry). "NEW …" items replace the model.

### 4.5 Output conventions
* **Freund notation on screens.**
  * Joint: f(x,y). Marginals: g(x) and h(y); the first screen also shows the HW alias, e.g.
    `g(x)=fX(x)`.
  * Conditionals: f(x|y) (=fX|Y) and w(y|x) (=fY|X).
  * Moments: μ, σ², σ, μ'r, μr, μ'r,s, σXY (Cov), ρ. Conditional mean `E(X|y)` and conditional
    variance `Var(X|y)`.
  * MGF: `M(t)`, `MX(t)`.
* **Numbers.** Show every number through M2FMT.
  * Exact results show Str9, and also Str8 on the next row when it differs (Midterm I style).
  * A **fraction is shown only when the result is exact or converged**:
    * results labelled EXACT (polynomial engine, finite sums) always show Str9;
    * NUMERIC results run 2 passes and show Str9 only if `abs(p2-p1)≤1ᴇ⁻8*max(1,abs(p2))`;
      otherwise they show Str8, the label `APPROX`, and `CHANGE=` the difference.
* **√ forms.** For an SD or a ρ that is not rational, compute W² through M2FMT; when that is a
  fraction, show `√(p/q)`, with the sign for ρ.
* **Show work.** Every result screen shows the formula used, with the numbers plugged in where they
  fit. Examples: `Var=9(4)+4(9)+2(3)(-2)(1)`, `P=1-P(X>1,Y>1)`, `F(b,d)-F(a,d)-F(b,c)+F(a,c)`.
  Integral answers are preceded by the written limits (P2).
* **Labels** say what each number is: `E(X|Y=1/2)=`, `h(1/2)=`, `P(X<Y)=`; never just `MEAN=`.

### 4.6 Numeric policy (one rule for every continuous tool; implemented in M2GL)
* **EXACT mode.** Use it when q is a polynomial (M2PLY θ=1 succeeds), every strip is finite and the
  multiplier is a built-in moment (or a g that passes RECOVER2 with degree ≤ 2 in each variable).
  One GL7 (outer) × GL5 (inner) panel per strip. Label: `EXACT (POLYNOMIAL)`.
* **NUMERIC mode** (everything else). Run pass 1 and pass 2 and compare them (§4.5).
  * In each direction, use **graded panels from the lower limit**: m panels whose widths are in the
    ratio 1:2:4:…, so panel k covers `[L+H(2^(k-1)-1), L+H(2^k-1)]` with `H=(T-L)/(2^m-1)`. Pass 1
    uses m=5 and pass 2 m=7. Use GL7 on every panel, in both directions.
  * A finite direction uses T = U.
  * A semi-infinite direction [L,∞) finds a **cutoff T by probing**. Evaluate the probe value at
    `L+2^k` for k=⁻3..12 and keep the running peak. T is the first probe point (k > ⁻3) whose value
    is < 1ᴇ⁻13·peak. If no point qualifies, T = L+4096 and the screen notes `TAIL MAY BE HEAVY`.
    * For the outer direction, the probe value is max|q| at three inner points (L, the midpoint and
      U when the inner range is finite, times (U−L); L, L+1 and L+2 when it is infinite).
    * For an infinite inner direction, the probe runs at each outer node.
  * (−∞,U] mirrors this, probing downward from U. If both ends are infinite, split at 0.
  * Verified accuracy, from Appendix B, includes P(X>Y) for 2e^(−x−2y), x e^(−x(1+y)) on the
    quadrant, 4xy e^(−x²−y²), e^(−x) on 0<y<x, rates 1/5 to 10, e^(x+y) and 1/x. Pass 1 is within
    5e-9 and pass 2 within 4e-10, with the simulator step counts in Appendix B.
  * Show progress in numeric mode with `Output(10,1,"WORKING "+toString(k)+"/"+toString(n))`.
* A polynomial q on an infinite support is an error ("A POLYNOMIAL CANNOT BE A PDF ON AN INFINITE
  REGION").
* q < 0 at any node (`ʟM2KR(9) < ⁻1ᴇ⁻12`) gives the warning `q<0 SOMEWHERE: NOT A VALID PDF`.
* fnInt( and nDeriv( are no longer used anywhere once P4 is finished. The fnInt(expr(…)) risk on
  hardware is removed.

### 4.7 Content authoring (encyclopedia, HELP, walkthroughs)
* The only source is `tools/write_content.py` (authoring), which writes `content/<PROG>.json`.
  `tools/content.py gen` turns that into `src/<PROG>.txt`. content.py limits: ≤ 6 sections, ≤ 6
  topics per section, ≤ 6 pages per topic, ≤ 9 lines per page, 26 display columns, and only the
  allowed characters. Keys while reading: ENTER = next page, LEFT = previous, CLEAR = menu.
* Page style matches Midterm I (`python3 ../dev/tools/content.py preview ../dev/content/STAE3.json`):
  formula, then how to use it, then a worked mini-example (a TEXTBOOK example, never a homework
  answer), then traps, then a citation line (`Freund Def14 p98`) and a `TOOL SOLV>…` path line.
* Write lines by hand when layout matters. Add a helper `pg(*lines)` alongside the existing textwrap
  `t()` helper. Always put a space before a number ("variance 2B", not "variance2B").
* Prefer uppercase for HELP, finder and walkthroughs, because lowercase costs 2 bytes per letter.
  The encyclopedia may be mixed case for readability.

---------------------------------------------------------------------------------------------------
## 5. Testing conventions

* Shared helper module **`tests/m2test.py`** (created in P1; every test imports it):
  ```python
  ROOT, SRC; INIT = {'Y1':'X²+1','Y9':'X+3','L₁':[91,92],'L₂':[71,72]}
  m(x)        # {'menu': x}; x = 1-based int OR item text (exact, else unique prefix) — prefer text
  i(v)        # Input action; negatives use '⁻'; Fraction -> 'p/q'; str passed through
  k(code)     # getKey action (105 ENTER, 45 CLEAR, 24 LEFT)
  run(prog, actions, init=None, max_steps=3_000_000, allow_lists=False, ends=True)
              # asserts: no error, leaks==0, no warnings, ended 'end'/'return' (if ends), INIT preserved,
              # and (unless allow_lists) no ʟM2* list left; returns the Result
  screen(r, title)            # rows (stripped) of the LAST pause screen whose row 1 starts with title
  after(r, title, label)      # text of the row after the row == label on that screen
  num(s)                      # parse '⁻1/36', '1ᴇ⁻5', '.25', '2' → float
  ```
  Text-based menu choice needs the simulator change in P1 (`{"menu": "BACK"}` picks that item).
  **Never hard-code BACK positions.**
* Name tests `tests/test_<area>.py` and use unittest. build_package runs every `tests/test_*.py`
  and requires exit status 0.
* Expected values come from sympy or Fraction, computed in the test (see Appendix C for verified
  values). Compare floats with `abs(actual-expected) ≤ 1e-9` for EXACT results. For NUMERIC
  results, use the tolerance the plan states (typically 1e-7).
* Check both the stored variables (`r.var('E')`) AND the screen text (fractions, labels, written
  limits).
* Step budgets: assert `r.steps < budget` wherever the package states one.
* Driving the UI by hand: `PLAY_DIR=<your scratch dir>/play python3 tools/play.py new S`, then
  `play.py add S m:SOLVERS m:JOINT i:X*Y ...`. Use a scratch PLAY_DIR (your session's scratchpad),
  never the repo.
* Tests added in P1 that everything must keep green:
  * `test_lint_all.py` checks:
    * both linters on every src file, with zero ERROR and zero WARN;
    * the no-631 scan (Appendix F);
    * that the program list equals the stems of `src/*.txt`;
    * that every `prgmNAME` referenced exists in src;
    * the memory budget (§3.1).
  * `test_menu_tree.py`: a depth-first explorer from STAM2 over every Menu( choice. It stops at
    Input/getKey screens and asserts no error and no leaks on any path; QUIT must end cleanly.

---------------------------------------------------------------------------------------------------
## 6. Build and package (`tools/build_package.py`, hardened in P1)

`python3 tools/build_package.py DEST` runs these steps:
1. Run every `tools/write_*.py` in sorted order. Then run `tools/content.py gen` for every
   `content/*.json`.
2. Run `tibuild.py lint src` and `tilint.py src`. On any failure, print the tool's own output.
3. Run every `tests/test_*.py`, recording a count from "Ran N tests", "PASS N", or "N/M … passed"
   (else 1). Exit status 0 is required.
4. Clear `out/*.8xp`. Run `tibuild.py build src out`, and assert that every program in ORDER has an
   .8xp. `ORDER = ['STAM2'] + sorted(other src stems)`.
5. Check the memory budget, failing if the .8xp total exceeds 118,000 bytes.
6. Recreate DEST from scratch: delete it only if it is empty or contains `VALIDATION.json`;
   otherwise abort. Write `calculator_files/*.8xp`, `source_code/{src,content,tools,tests}`,
   `requirements.txt`, `START_HERE.md`, `VALIDATION.json`/`.txt` and `SHA256SUMS.txt`, then write
   `DEST.zip` next to DEST.

The final package lives at `../output/STA431_Midterm_II_Calculator_Package` (+ `.zip`).

---------------------------------------------------------------------------------------------------
## 7. Work packages (implement in order)

### P1 — Foundation: fix the build, remove STA 631, test/build hardening, main-menu shape

**Goal.** A green, buildable, STA 431-only baseline with the requested main-menu shape, robust tests
and the two quick numeric safety fixes.

**Files.**
* src/STAM2.txt, src/M2CONT.txt, src/M2MGF.txt, src/M2EXAM.txt.
* tools/write_content.py, tools/write_presets.py; regenerate content/*.json, src/M2ENC.txt,
  src/M2HW.txt and src/M2RUN.txt.
* tools/tisim.py, tools/play.py, tools/tilint.py, tools/tibuild.py, tools/build_package.py.
* New tests: tests/m2test.py, tests/test_lint_all.py, tests/test_menu_tree.py.
* Edited tests: test_presets.py, test_slice.py, test_disc_cont.py, test_reference_navigation.py,
  test_workflow_upgrades.py, plus tests_exam_assistant.py, which is RENAMED to
  test_exam_assistant.py.
* START_HERE.md, and out/ (refreshed by the build).

**Spec.**
1. **Build fix.** Line 60 of STAM2 becomes `"Finite rows ≤30; combos≤3"` (the ≤ token). In
   `tibuild.py lint`:
   * count errors per file, so later files print their byte size again instead of `?`;
   * report ORIGINAL file line numbers by building a line map in `read_program`, the way tilint's
     `line_map` does.
2. **tilint configuration.** Set `FORMATTER='M2FMT'` and `MAIN_PROGRAM='STAM2'`, so the Q–V clobber
   check runs against M2FMT. Fix any warnings that appear. Update the stale "STAFMT" header comment
   in M2FMT.txt; it is a comment, so behaviour does not change.
3. **STAM2 (P1 shape).**
   * The first lines are `Float`, `Normal`, `Real` (mode safety), then `0→Z`.
   * Main `Menu("STA431 MIDTERM II","ENCYCLOPEDIA",E,"SOLVERS",S,"HELP",H,"HOMEWORK PRACTICE",P,"QUIT",Q)`.
   * ENCYCLOPEDIA → prgmM2ENC.
   * SOLVERS → `Menu("SOLVERS","DISCRETE TABLE",…,"DENSITY+INTEGRAL",…,"MGF TOOLS",…,"LINEAR COMBOS",…,"BACK",M)`.
     Each item does `0→Z`, calls the program, then returns to the SOLVERS menu.
   * HELP → `Menu("HELP","FIND MY SOLVER",…,"HOW TO ENTER",…,"LIMITS + CAVEATS",…,"BACK",M)`.
     * FIND MY SOLVER → `0→Z:prgmM2EXAM`.
     * HOW TO ENTER is a 2-page pager in the Midterm I style (`Repeat Ans:getKey:End`, CLEAR goes
       back, LEFT goes to the previous page). Page 1, KEYS: the X key, Y=ALPHA 1, TEST menu, `𝑒^(`,
       `√(`, the (-) key, ÷ for fractions, `{ }`, `ᴇ99`=∞, and "ON ERR: CHOOSE 1:QUIT". Page 2,
       NOTATION: g(x), h(y), f(x|y), w(y|x), μ'r, μr, σXY, ρ.
     * LIMITS + CAVEATS = the two existing screens, fixed.
   * HOMEWORK PRACTICE → `Menu("HOMEWORK PRACTICE","WALKTHROUGHS",…,"LOAD PRACTICE DATA",…,"BACK",M)`,
     calling M2HW / M2RUN. Keep the "PRACTICE EXAMPLES ONLY" notice before M2RUN.
   * QUIT: `ClrHome` and then `""` as the last line.
4. **STA 631 removal** (the checklist is in Appendix F).
   * In write_content.py, delete the `OPTIONAL 631` section, and replace the `ZERO NOT INDEP` page
     with the Freund Ex17 text in Appendix D.4.
   * In write_presets.py, delete D1, D2 and D3, the "OPTIONAL 631" menu item and `Lbl D` menu, and
     change the print to "Generated 13 input presets".
   * In M2CONT, delete the preset codes 21–23 (lines 4–5).
   * In M2EXAM, reword E3 and F4 to "To show dependence give one (x,y) with f(x,y)≠g(x)h(y), or
     show the support is not a product set". Also fix D3 lines 298-299 to "Two matching moments" /
     "cannot identify the law." and C2 line 213 to "Var(X^2) needs E[X^4].".
   * Regenerate the generated files.
5. **Interim numeric safety fixes.** These are minimal, because P3, P4 and P5 replace the code.
   * M2CONT DOUBLE INTEGRAL: after both passes, set a flag when
     `abs(F-D)>1ᴇ⁻9*max(1,abs(F))` or `abs(G-E)>1ᴇ⁻9*max(1,abs(G))`. When the flag is set, every
     RAW I/RAW J and NORMALIZE value is shown as Str8, with the row `NOT CONVERGED: RAISE N`.
     Change the START_HERE advice from "try 4" to "use 8; raise it until CHANGE is 0".
   * M2MGF TYPE MGF NUMERIC: never evaluate M at 0; use `1→ʟM2MV(1)`.
     * First check that `abs(M(.001)-1)<.05`; otherwise show "M(0) MUST BE 1".
     * Use `D2(h)=(M(h)+M(⁻h)-2)/h²`.
     * Report the Richardson values `(4·D(h/2)−D(h))/3` for D1 and D2 (h=.01, .005).
     * The two-step message compares the Richardson value against the h=.005 value at a relative
       1ᴇ⁻4.
6. **Tests and tools.**
   * tisim.py: in `do_menu`, if the action value is a str, choose the item whose stripped text
     equals it, else the unique item that starts with it. Otherwise raise SIM:ACTION and list the
     items. Document this in the docstring.
   * play.py: accept the key `m:TEXT`.
   * Create `tests/m2test.py` (§5).
   * Migrate every test that indexes BACK or main-menu positions to text choices:
     * test_presets: `[m(group),m(question)]+solver+[m('BACK'),m('BACK')]`;
     * the test_reference_navigation launcher walk;
     * the test_workflow_upgrades STAM2 paths;
     * the test_exam_assistant route table.
   * Replace the 631 test data with non-631 data, computing the expected values with sympy:
     * test_slice reimbursement → Freund Ex20 slice: q=`2/3*(X+2Y)`, c=1, Y=1/2, x 0..1, giving
       M=1, E=5/9, F=7/18, H=13/162; interval x≤1/2 gives 5/12 (Freund Ex24).
     * test_slice triangle → Mock 4 Q3: q=`X*Y`, c=8, given X=1/2, y from 1/2 to 1. sympy gives
       g(1/2)=3/2 and E(Y|X=1/2)=7/9; also check the interval P(Y<3/4|X=1/2)=5/12.
     * test_disc_cont triangle → density `2` on x 0..1, y 0..1−X with g=`X*Y` and N=4. The expected
       values are F=1 and G=1/12 (Freund Ch4 Ex16); Simpson is exact for the cubic.
     * test_exam_assistant: change the flag list to `[1,2,11,13,14,15,16,17,18]`.
   * Add these tests:
     * `test_lint_all.py` (§5);
     * `test_menu_tree.py` (§5);
     * a numeric-gating test: q=`6X`, x 0..1, y `X`..1, g=`X*Y`, N=4. The screen must NOT contain
       `819/2048` and must contain `NOT CONVERGED`;
     * an MGF test: `(1-2X)^⁻3` with a=1, b=0 must give E within 1e-5 of 6 and VAR within 1e-4 of
       12; `(𝑒^(2X)-1)/(2X)` must not crash, with E within 1e-5 of 1 and VAR within 1e-4 of 1/3.
       Compute the sympy limits;
     * a STAM2 route test for HELP>FIND MY SOLVER>BACK, and one for QUIT.
7. **build_package.py.** Rewrite it to §6: `run()` prints the output and fails with the tool's own
   message.
8. **START_HERE.md.**
   * Change the program count/list and the main-menu table to the new shape; remove all 631 text;
     fix the paths you touched to the new menu names (`SOLVERS > DENSITY+INTEGRAL > …`).
   * Add "Memory": archive the Midterm I programs with 2nd MEM > 2:Mem Mgmt/Del > 7:Prgm; ENTER
     toggles `*`; keep every M2/STAM2 program unstarred; Press-to-Test disables programs.
   * Add "Modes": STAM2 sets Float, Normal and Real.
   * Restore the missing spaces between words and digits.

**Acceptance.**
* All tests are green, and the build to `../output/STA431_Midterm_II_Calculator_Package` succeeds
  with M2EXAM.8xp present. `out/` contains exactly one fresh .8xp per src program, and the .zip is
  written.
* The Appendix F grep returns nothing.
* `test_menu_tree` explores every menu with 0 errors and 0 leaks.
* The numeric-gating and MGF tests pass.
* `play.py` session `m:SOLVERS m:BACK m:QUIT` ends cleanly.

---

### P2 — Exact region engine core: M2GL, M2PLY (part 1), M2JNT model + EVENTS + LIMITS (R2)

**Goal.** A joint-density solver where the student types q(X,Y), picks a support from a menu and
picks an event from a menu. The app prints the written iterated integral with the correct limits
(split into pieces, in either order) and the words → math translation, then gives the probability.
It is EXACT for polynomial densities on straight-edged supports and accurate numerically for
exponential and other densities, including infinite supports.

**Files.**
* New: src/M2GL.txt, src/M2PLY.txt (modes 1, 2, 3, 8) and src/M2JNT.txt.
* Changed: src/STAM2.txt (SOLVERS gets "JOINT DENSITY" after DISCRETE TABLE), src/M2EXAM.txt (B1,
  B5 and B6 open M2JNT), tools/write_presets.py (HW4 Q2, Q3 and Q5 go to M2JNT with Z=99) and
  START_HERE.md.
* New tests: tests/test_kernel.py and tests/test_joint_events.py. Update test_presets and
  test_exam_assistant.

**Spec.**
1. **M2GL**, as in §4.3 and §4.6. The validated prototype code is in Appendix A: A.1
   (constants), A.2 (strip decomposition and GL), A.4 (graded and infinite handling, Python
   reference in Appendix B).
   * For θ=1, loop over the strips. In EXACT mode, use 7 outer × 5 inner nodes per strip. Store the
     node values in lists and accumulate the moments with `sum(` list operations.
   * Return ʟM2KR and ʟM2KP. Keep GL7 and GL5 constants as list literals with 14 significant
     digits (Appendix A.1).
2. **M2PLY part 1.** θ=1 RECOVER2 (Appendix A.3, validated), θ=2 LINESTR, θ=3 POLYSTR and θ=8
   VARCHECK.
3. **M2JNT model entry** ("NEW MODEL"). The first time, the item flows automatically from the top
   menu.
   * `ClrHome`, then the Disp lines `f(x,y)=c*q(x,y)`, `TYPE q WITH X AND Y`, `OMIT c IF UNKNOWN`.
     Then `Input "q(X,Y)?",Str1`, followed by VARCHECK with "XY".
   * Then `Menu("SUPPORT","RECT a<X<b,c<Y<d",…,"TRI a<Y<X<b",…,"TRI a<X<Y<b",…,"X,Y>0 AND X+Y<k",…,"QUADRANT X,Y>0",…,"CUSTOM BOUNDS",…,"BACK",…)`.
     * CUSTOM → `Menu("CUSTOM","X OUTER, Y(X)",…,"Y OUTER, X(Y)",…,"CURVED (NUMERIC)",…,"BACK",…)`.
     * Inputs are numbers (ᴇ99 = ∞). Custom linear bounds are typed as strings in X (or Y), then
       parsed into l0,l1 by evaluating at 0 and 1 and checked at ⁻1 and 2. If the check fails, show
       "BOUNDS MUST BE LINEAR: USE CURVED OR SPLIT".
   * Store the **support record `ʟM2JM`**, where ∞ is stored as ±1ᴇ6:
     | code | record | polygon (vertices) |
     |---|---|---|
     | 1 rectangle | {1,a,b,c,d} | (a,c),(b,c),(b,d),(a,d) |
     | 2 triangle a<y<x<b | {2,a,b} | (a,a),(b,a),(b,b) |
     | 3 triangle a<x<y<b | {3,a,b} | (a,a),(b,b),(a,b) |
     | 4 simplex x,y>0, x+y<k | {4,k} | (0,0),(k,0),(0,k) |
     | 5 quadrant | {5} | (0,0),(B,0),(B,B),(0,B), B=1ᴇ6 |
     | 6 x outer, l0+l1x<y<u0+u1x | {6,a,b,l0,l1,u0,u1} | (a,l(a)),(b,l(b)),(b,u(b)),(a,u(a)) with duplicates removed |
     | 7 y outer, l0+l1y<x<u0+u1y | {7,c,d,l0,l1,u0,u1} | (l(c),c),(u(c),c),(u(d),d),(l(d),d) |
     | 8 curved x outer (numeric) | {8,a,b} + Str2/Str3 = lower/upper y(X) | no polygon; one kind-1 strip |
   * Validate that every finite value satisfies |v| < 1ᴇ5, that U ≥ L at both ends ("UPPER BELOW
     LOWER: SPLIT THE REGION"), and that the area is positive.
   * Decide the mode: polynomial if M2PLY θ=1 succeeds AND the support is finite and not curved.
     A polynomial on an infinite support is an error.
   * Compute the total `T=∫∫_S q` with the kernel (EXACT, or 2 NUMERIC passes) and set `c=1/T`.
     Error if T ≤ 0. Warn if `ʟM2KR(9)<0`.
   * **Summary screen**: `MODEL f=c*q`, Str1, a support text such as `0<y<x<1` or
     `x>0,y>0` (built with M2PLY LINESTR), `TOTAL ∫∫q=`, `c=` (or `q IS ALREADY A PDF` when
     |T−1| < 1ᴇ⁻9), and `EXACT (POLYNOMIAL)` or `NUMERIC`.
   * `Z=99` enters here with the preloaded Str1/ʟM2JM (§4.3) and skips the prompts.
4. **Events.** An event is a list of half-planes `a·X+b·Y≤c`, stored as triples in `ʟM2JE`, plus a
   complement flag.
   * P(E) = c·∫∫ over (support polygon clipped by the half-planes) of q. The clipping is
     Sutherland–Hodgman (Appendix A.5 is validated). If the event is a complement, the probability
     is 1 − that.
   * P(A and B) for any complement flags uses inclusion–exclusion with the concatenated half-plane
     lists: P(Cᶜ∩D)=P(D)−P(C∩D), and P(Cᶜ∩Dᶜ)=1−P(C)−P(D)+P(C∩D).
   * If the clipped polygon has fewer than 3 vertices or zero area, P=0 and the screen says
     `EVENT MISSES SUPPORT`.
   * Menus:
     * `Menu("EVENT","X<Y OR X>Y",…,"X+Y≤k OR X+Y≥k",…,"MIN/MAX VS t",…,"X>a AND Y>b",…,"MORE EVENTS",…,"P(A|B)",…,"BACK",…)`.
     * MORE EVENTS = `"aX+bY≤c","|X-Y|≤k OR >k","X≤s AND Y≤t","RECTANGLE a,b,c,d","a<X<b ONLY","BACK"`.
     * MIN/MAX = `"min(X,Y)≤t","min(X,Y)>t","max(X,Y)≤t","max(X,Y)>t","BACK"`.
   * Each event first shows a **SETUP** screen with words → math (table below). Next come the
     **LIMITS** screens: `ORDER dy dx (x OUTER)`, then per piece `x: 0 TO 1/2` / ` y: x TO 1-x` /
     ` PIECE=1/8`, three pieces per screen. These are the vertical strips of the clipped polygon.
     Each strip's lower and upper lines become strings through LINESTR, and each piece value is
     c·ʟM2KP. The **RESULT** screen shows `P(…)=`, the complement arithmetic such as `=1-3/8=5/8`,
     and the EXACT/APPROX label.
   * After the result, `Menu("EVENT RESULT","REVERSE ORDER",…,"NEW EVENT",…,"BACK",…)`. REVERSE
     ORDER transposes the polygon (swap X/Y and the half-plane a↔b), decomposes, integrates with
     orient=1, and prints `ORDER dx dy (y OUTER)` with pieces `y: …` / ` x: …`. The total must
     agree.
   * P(A|B): pick A and then B with the same menus (a slot flag says which is being picked). Show
     `P(A AND B)=`, `P(B)=`, and the ratio. If P(B)=0, show `P(B)=0: UNDEFINED`.
   * For a curved support, the EVENTS menu offers only "THIS REGION (CURVED)". The user types a
     sub-region a<x<b, y between two X-expressions, and the program integrates it numerically.
5. **Words → math table** (SETUP screen text, ≤ 26 characters per line).
   | event | words | math | note |
   |---|---|---|---|
   | X<Y | FIRST BEFORE SECOND | X<Y | |
   | X+Y≤k | TOTAL AT MOST k | X+Y≤k | y≤k-x |
   | min≤t | FAILS IF EITHER FAILS | min(X,Y)≤t | =1-P(X>t,Y>t) |
   | min>t | BOTH STILL WORK AT t | min(X,Y)>t | =P(X>t,Y>t) |
   | max≤t | FAILS ONLY IF BOTH FAIL | max(X,Y)≤t | =P(X≤t,Y≤t)=F(t,t) |
   | max>t | AT LEAST ONE WORKS | max(X,Y)>t | =1-F(t,t) |
   | X>a,Y>b | BOTH EXCEED | X>a AND Y>b | |
   | abs≤k | MEET WITHIN k | abs(X-Y)≤k | x-k<y<x+k |
   | X≤s,Y≤t | JOINT CDF F(s,t) | X≤s AND Y≤t | |
   | P(A|B) | GIVEN AN EVENT B | P(A AND B)/P(B) | not a value X=x |
6. **Top menu**: `Menu("JOINT DENSITY","NEW MODEL",…,"EVENTS + LIMITS",…,"FORMULAS",…,"MOMENTS + COV",…,"GIVEN A VALUE",…,"INDEP + CDF",…,"BACK",Z)`.
   * In P2, FORMULAS, MOMENTS, GIVEN and INDEP show "COMING IN THIS VERSION: USE EVENTS" and
     return. P3 fills them.
   * If an analysis item is chosen with no model, go to NEW MODEL.
   * BACK deletes every ʟM2J*, ʟM2K* and ʟM2Q* list.
7. **Performance budgets** (simulator steps, from the moment the event is chosen):
   * EXACT event: < 5,000.
   * EXACT model entry, recovery included: < 3,000.
   * NUMERIC quadrant event, both passes: < 80,000.
   * NUMERIC model total, quadrant: < 80,000.
8. **Presets.** In write_presets.py, change HW4 Q2 (q=`2X+Y`, {1,0,1,0,2}), HW4 Q3 (`(X+Y)/8`,
   {1,0,2,0,2}) and HW4 Q5 (`(2X+Y)/4`, {1,0,1,0,2}) to `99→Z:prgmM2JNT`, landing on the analysis
   menu.

**Acceptance** (tests compute every target with sympy; the values are in Appendix C):
* R3, regions. HW4 Q3 through MIN/MAX "min(X,Y)≤t" with t=1 on q=`(X+Y)/8`, RECT 0..2 × 0..2:
  the screens show `=1-P(X>t,Y>t)`, `3/8` and `5/8`. HW4 Q5 through X<Y on `(2X+Y)/4`:
  `19/24` in BOTH orders, with dy dx pieces `x: 0 TO 1` / ` y: x TO 2`, and dx dy pieces split at
  y=1 (`y: 0 TO 1` / ` x: 0 TO y` and `y: 1 TO 2` / ` x: 0 TO 1`). HW4 Q2 gives `c=1/4`.
  HW4 Q4 (discrete) is checked through M2DISC typed events: X>Y gives 3/32 and X+Y≤3 gives 1/4.
* Non-HW, EXACT. Each test asserts the fraction on screen and r.var agreement to 1e-9:
  * Mock II Q2 (q=`X`, TRI a<Y<X<b on 0..1): c=3; P(X+Y≤1)=3/8 with the two pieces
    `x: 0 TO 1/2` ` y: 0 TO x` and `x: 1/2 TO 1` ` y: 0 TO 1-x`, and the reverse order as one piece
    `y: 0 TO 1/2` ` x: y TO 1-y`.
  * Mock 4 Q3 (q=`X*Y`, TRI a<X<Y<b): c=8, P(X+Y≤1)=1/6.
  * Mock 4 Q4 (q=`X+2Y`, RECT 0..2 × 0..1): c=1/4, P(X<Y)=5/24, P(X+Y≤1)=1/8.
  * Mock 4 Q5 (q=`2/3*(X+2Y)` on the unit square): P(min≤1/2)=5/8, P(max≤1/2)=1/8.
  * Meeting problem (q=`1`, unit square): P(|X−Y|≤1/4)=7/16.
  * Conditional event: P(X<1/2 | Y>1/2) for q=`X*Y` on TRI a<X<Y<b (0..1) is 2/5. P(A AND B)=3/8
    and P(B)=15/16.
  * Custom linear bounds: q=`1` on 0<x<2, x/2<y<1+x/2 has c=1/2, and P(Y>1)=1/2 by sympy.
  * The "NOT LINEAR" rejection for `X²`; VARCHECK rejecting `2X+T`; the "UPPER BELOW LOWER"
    rejection; the polynomial-on-quadrant rejection; and `EVENT MISSES SUPPORT` → 0.
* Non-HW, NUMERIC:
  * q=`2𝑒^(⁻X-2Y)` on QUADRANT: T within 1e-8 of 1; P(X>Y) within 1e-8 of 2/3, and the screen must
    show the converged fraction `2/3`; P(Y>X) within 1e-8 of 1/3; P(X+Y≤1) within 1e-8 of
    0.399576400894. If the passes disagree by more than the §4.5 gate in the simulator, raise the
    panel counts (for example m=6/8) while keeping within the step budget, and document the change.
  * q=`𝑒^(⁻X)` on TRI a<Y<X<b with b=ᴇ99: T=1 and P(X<2Y)=1/2.
  * Curved: q=`3` on 0<y<x² (code 8, x 0..1): T=1.
* Step budgets as in item 7. test_kernel checks random polynomials of degree ≤4 over random
  triangles against sympy through a driver program (`sim.add_program`): error < 1e-11.
* START_HERE gains a JOINT DENSITY section (support menu, event menu, ᴇ99 for ∞, reading the
  written limits). The finder routes still return.

---

### P3 — M2JNT analysis: FORMULAS, MOMENTS + COV, GIVEN A VALUE, INDEP + CDF; retire M2SLICE and DOUBLE INTEGRAL

**Goal.** For a typed joint density, produce **symbolic** marginal and conditional density formulas
with their supports, E(Y|X=x) as a function, every moment along with Cov and ρ in one pass,
conditional laws at a given value, an exact independence verdict with a witness, and the joint CDF.
Polynomial models get exact output; other models get numeric values.

**Files.**
* Changed: src/M2PLY.txt (θ=4, 5, 6, 7), src/M2JNT.txt, src/M2CONT.txt (delete DOUBLE INTEGRAL and
  JOINT SLICE, keeping 1D), src/M2EXAM.txt (B2, B3 and B4 open M2JNT), tools/write_presets.py
  (HW5 Q7 → M2JNT Z=99 with q=`X+Y`, {1,0,1,0,1}) and START_HERE.md.
* Deleted: src/M2SLICE.txt.
* Tests: new tests/test_joint_analysis.py. Port the non-631 cases of test_slice.py, the
  double-integral cases of test_disc_cont.py and the M2SLICE/M2CONT cases of
  test_transfer_general.py and test_workflow_upgrades.py to M2JNT, then delete the old cases.

**Spec.**
1. **FORMULAS** (polynomial models only; otherwise "FORMULAS NEED A POLYNOMIAL q ON A STRAIGHT-EDGED
   SUPPORT; USE GIVEN A VALUE").
   `Menu("FORMULAS","g(x) MARGINAL",…,"h(y) MARGINAL",…,"w(y|x) CONDITIONAL",…,"f(x|y) CONDITIONAL",…,"E(Y|X=x) FORMULA",…,"E(X|Y=y) FORMULA",…,"BACK",…)`.
   * **g(x).** For each vertical strip, M2PLY θ=5 (s=0) times c gives a polynomial in x. Merge
     adjacent identical pieces. Screen: `g(x)=fX(x)`, then per piece `0<x<1:` / ` 3x²`, then
     `0 ELSEWHERE`, then `CHECK ∫g dx=1`. The check is computed from the pieces' antiderivatives
     and must be 1 within 1e-9.
   * **h(y).** The same with horizontal strips (transposed polygon and transposed table).
   * **w(y|x).** Per vertical strip, numerator = c·q (the 2-D table) and denominator = the g(x)
     piece. Run CANCEL with the candidate roots = all finite vertex coordinates. Screen:
     `w(y|x)=fY|X(y|x)`, `(N)/(D)` (or just N when D=1), `FOR L(x)<y<U(x)`, `AND a<x<b`.
     * Mock II Q2 shows `1/(x)`, with `0<y<x` and `0<x<1`.
     * HW4 Q2 shows `(2x+y)/(1+y)` for f(x|y).
     * HW5 Q7 shows `(2x+2y)/(1+2y)`.
     * Mock 6 Q7 shows `(3x²+3y²)/(1+3y²)`.
   * **f(x|y)** works the same way with horizontal strips.
   * **E(Y|X=x)** = [θ=5 with s=1]/[θ=5 with s=0], per strip, then CANCEL. For example, Mock 6 Q2
     (f=2 on 0<x<y<1) gives `1/2+1/2x`, and Mock 4 Q3 gives `(2/3+2/3x+2/3x²)/(1+x)`.
     **E(X|Y=y)** is analogous.
2. **MOMENTS + COV.** One kernel pass (EXACT) or two (NUMERIC) over the support gives the 6
   moments.
   * Screens: μX, μY, E(X²), E(Y²), σ²X, σ²Y, E(XY)=μ'1,1, σXY=Cov, and ρ with a √ form.
   * `Menu("MOMENTS","MEANS VARS COV ρ",…,"E[g(X,Y)]",…,"PRODUCT MOMENT r,s",…,"VAR(aX+bY+c)",…,"BACK",…)`.
   * **E[g].** Str5 = the typed g. EXACT if q is a polynomial and g passes RECOVER2 with degree ≤ 2
     in each variable; otherwise NUMERIC with 2 passes. Shows E[g], E[g²] and Var(g).
   * **Product moments.** Raw μ'r,s and central μr,s for r,s ∈ 0..4 with r+s ≤ 4. Build
     Str5=`"X^r*Y^s"`, or for central `"(X-A)^r*(Y-B)^s"` with A and B holding the means; omit any
     factor whose power is 0.
   * **Var(aX+bY+c)**: a²σ²X + b²σ²Y + 2abσXY, with the work shown.
3. **GIVEN A VALUE.** `Menu("GIVEN A VALUE","GIVEN X=x",…,"GIVEN Y=y",…,"BACK",…)`, then input the
   value.
   * The slice interval comes from the strip that contains the value. Outside the support, show
     `g(x0)=0: CONDITIONAL UNDEFINED`.
   * The 1-D kernel (var 1 or 0) gives the marginal value g(x0)=c·∫q dy, then E(Y|x0), E(Y²|x0) and
     Var(Y|x0). For a polynomial model, also show the conditional density in y with numbers
     substituted (coefficients b_j=Σ_i a_ij x0^i, through POLYSTR, scaled), for example
     `w(y|1/2)=2/3+4/3y FOR 0<y<1`.
   * Then `Menu("SLICE","P(a<Y<b | X=x0)",…,"E[g(Y)] GIVEN",…,"NEW VALUE",…,"BACK",…)`, with clipping
     to the slice. The density value at a point is shown with the note "DENSITY, NOT A POINT PROB".
4. **INDEP + CDF.** `Menu("INDEP + CDF","INDEPENDENCE TEST",…,"F(s,t) AT A POINT",…,"F(x,y) FORMULA",…,"BACK",…)`.
   * **Independence.**
     * For a non-product support (anything but RECT/QUADRANT, or custom with l1=u1=0), the answer is
       DEPENDENT. Search the 3×3 grid at 1/4, 1/2 and 3/4 of the bounding box for a point outside
       the support where g>0 and h>0, then print `f(x*,y*)=0 BUT g(x*)h(y*)=…>0` and cite Def14 p98.
     * For a product support with a polynomial q, use the rank-1 test on the coefficient table (all
       2×2 minors ≤ 1ᴇ⁻10·max²). If it passes: `INDEPENDENT: f=g(x)h(y) ON A PRODUCT SET`, showing
       g and h. If not, DEPENDENT, with the worst point of an interior 3×3 grid showing f vs g·h.
     * For a numeric model, run the same grid check with numeric marginals and label it
       `NUMERIC EVIDENCE`.
   * **F(s,t)** = P(X≤s and Y≤t) through the event engine, with the pieces shown. (This is R1's
     "given f find F at a point".) `Z=97` enters here after NEW MODEL.
   * **F(x,y) FORMULA.** RECT support and polynomial only. Print the interior polynomial (6×6
     antiderivative table through POLY2STR), the branches F(x,d) for y≥d, F(b,y) for x≥b, 1 when
     both, and 0 when x≤a or y≤c. Freund Ex16: `1/2x²y+1/2xy²`.
5. **Retire the old tools.**
   * Delete M2SLICE.txt. In M2CONT, delete the DOUBLE INTEGRAL (J0–BL), JOINT SLICE and the
     preset hooks for codes 2, 3, 5 and 17. M2CONT's menu becomes the 1-D tools only, until P4.
   * Update STAM2, M2EXAM and every test that referenced the deleted features. HW5 Q7's preset uses
     M2JNT. The workflow tests now use JOINT DENSITY > GIVEN A VALUE.
6. **Budgets.**
   * EXACT FORMULAS screens (any one): < 6,000 steps.
   * EXACT MOMENTS: < 3,000.
   * GIVEN A VALUE, exact: < 2,500.
   * NUMERIC MOMENTS on the quadrant: < 120,000.

**Acceptance** (sympy targets, Appendix C):
* Formulas (asserted as strings):
  * Mock II Q2: g=`3x²` on 0<x<1; h=`3/2-3/2y²` on 0<y<1; w=`1/(x)` (or `1/x`) with `0<y<x`;
    P(Y<1/4|X=1/2)=1/2; DEPENDENT, with a witness whose values match sympy.
  * Mock 4 Q3: g=`4x-4x³`; h=`4y³`; f(x|y)=`(2x)/(y²)`; P(X<1/2|Y=3/4)=4/9.
  * HW4 Q2: h=`1/4+1/4y`; f(x|y) as above.
  * HW5 Q7: h=`1/2+y`; E(X|Y=1/2)=7/12; Var=11/144.
  * Mock 6 Q2: E X=1/3, E Y=2/3, E XY=1/4, Cov=1/36, σ²X=σ²Y=1/18, ρ=1/2, and E(Y|X=x) shown as
    `1/2+1/2x`.
  * Mock 6 Q7: E(X|Y=1/2)=9/14, Var=71/980, with f(x|y) as above.
* Moments:
  * Freund Ch4 Ex16 (q=`2`, simplex k=1): μX=1/3, E XY=1/12, Cov=−1/36.
  * Freund Ex20 (q=`2/3*(X+2Y)`): E(X|Y=1/2)=5/9 and Var=13/162.
  * Exercise 51 (q=`(X+Y)/3`, RECT 0..1 × 0..2): Var(3X+4Y−5)=805/162.
  * μ'2,1 for Mock 6 Q2, checked against sympy.
* Independence: Freund Ex25 (q=`4X*Y`, unit square) gives INDEPENDENT with g=`2x` and h=`2y`.
  q=`X+Y` gives DEPENDENT with a correct witness.
* Freund Ex16 F formula and branches; F(1/2,1/2)=1/8 for x+y.
* Numeric:
  * q=`X*𝑒^(⁻X*(1+Y))` on QUADRANT: given Y=1, h(1)=1/4 within 1e-7, E(X|Y=1)=1 within 1e-7, and
    P(X>1|Y=1)=3e^(−2) within 1e-7.
  * 2e^(−x−2y): μX=1, μY=1/2, Cov≈0 (within 1e-7), independent by numeric evidence.
* The ported old tests pass against M2JNT. M2SLICE no longer exists, and test_lint_all's
  prgm-reference check passes.

---

### P4 — M2CDF (R1, joint CDF solver + exponential pair) and M2ONE (1-D density; replaces M2CONT)

**Files.**
* New: src/M2CDF.txt and src/M2ONE.txt.
* Deleted: src/M2CONT.txt.
* Changed: STAM2 (SOLVERS: DISCRETE TABLE, JOINT DENSITY, CDF OF X AND Y, ONE-VAR DENSITY, MGF
  TOOLS, LINEAR COMBOS, BACK), M2EXAM (C1–C4 → M2ONE, F1 → M2CDF), tools/write_presets.py (HW5 Q2 →
  M2ONE Z=99 with q=`3/4*(1-X²)` and {⁻1,1}) and START_HERE.
* Tests: tests/test_cdf.py and tests/test_one_var.py. Port the remaining M2CONT tests from
  test_disc_cont, test_transfer_general and test_workflow_upgrades to M2ONE.

**M2CDF spec.**
* **NEW F(X,Y).** Disp `TYPE F(X,Y) ON ITS`, `SUPPORT a<x<b,c<y<d`, `ᴇ99 = INFINITY`. Then Input
  Str1 (VARCHECK "XY"), then a, b, c, d.
  * Try RECOVER2 on F; it is a polynomial if that succeeds and the box is finite.
  * Show a validity screen: F(a,c)=0? F(b,d)=1? (using BIG for infinite ends), and f ≥ 0 at a 3×3
    interior grid. Then `Menu("JOINT CDF","NEW F(X,Y)",…,"RECTANGLE PROB",…,"MARGINAL CDFs",…,"PDF f FROM F",…,"F FROM A PDF f",…,"EXP PAIR TEMPLATE",…,"BACK",Z)`.
* **RECTANGLE PROB.** Inputs x1<x2 and y1<y2. Use clipped corners
  F̃(x,y)=0 if x≤a or y≤c, else F(min(x,b),min(y,d)). Show
  `P(x1<X≤x2,y1<Y≤y2)`, `=F(x2,y2)-F(x1,y2)`, `-F(x2,y1)+F(x1,y1)`, the four values and the
  result. Fraction if polynomial; decimal for exponentials. Add the note for integer-valued X,Y:
  use a−1, c−1.
* **MARGINAL CDFs.** FX(x)=F(x,d) and FY(y)=F(b,y) (R1: "top of the other support").
  * Polynomial: print the formula by substituting y=d into the table, then POLYSTR. Example: R3's
    `1/2x²+1/2x³` (= x²(x+1)/2).
  * Otherwise: the value at a typed point plus the text `FX(x)=F(x,INF)` when d is infinite (use
    y=1ᴇ6; underflow gives 0).
* **PDF f FROM F.**
  * Polynomial: an EXACT formula f=∂²F/∂x∂y, with coefficient `a_ij=(i+1)(j+1)b_(i+1,j+1)`, shown
    through POLY2STR. R3 gives `3/2x²+2xy`.
  * Otherwise: NUMERIC at a typed interior point with a Richardson mixed difference:
    D(h)=[F(x+h,y+h)−F(x+h,y−h)−F(x−h,y+h)+F(x−h,y−h)]/(4h²) at h=.01 and .005, then
    (4D(h/2)−D(h))/3. The point must be at least .01 inside the support.
  * Always show the formula `f=d²F/dxdy`.
* **F FROM A PDF f.** One recipe screen ("F(s,t)=∫∫ f over x≤s,y≤t ∩ S"), then `97→Z:prgmM2JNT`.
* **EXP PAIR TEMPLATE.** Inputs a,b>0 for F=(1−e^(−ax))(1−e^(−by)) on x,y>0, or equivalently
  f=ab·e^(−ax−by). Output, each with its formula line and value:
  * f, g(x)=a e^(−ax), h(y)=b e^(−by);
  * INDEPENDENT (F factors);
  * P(X<Y)=a/(a+b) and P(X>Y)=b/(a+b);
  * P(X+Y≤k)=1−(b e^(−ak)−a e^(−bk))/(b−a), or 1−e^(−ak)(1+ak) when a=b;
  * P(min≤t)=1−e^(−(a+b)t) and P(max≤t)=(1−e^(−at))(1−e^(−bt));
  * E X=1/a, Var X=1/a² (and the same for Y), E(XY)=1/(ab), Cov=0.

  Use a `Menu(` to pick which one.
* BACK cleans ʟM2F*, ʟM2Q* and ʟM2K*.

**M2ONE spec** (uses M2GL θ=2 and M2PLY).
* **NEW DENSITY.** Disp `f(x)=c*q(x) ON a<x<b`, `OMIT c IF UNKNOWN`, `ᴇ99 = INFINITY`. Input q(X)
  (VARCHECK "X"), then the lower and upper bounds.
  * A polynomial is detected with RECOVER2 (q(X) has no Y) on a finite support. Compute T and c;
    show the summary.
  * `Z=99` uses Str1 and ʟM2OM.
* **MOMENTS.** c, μ=E(X), μ'2, σ², σ (√ form), μ'3, μ'4, μ3=μ'3−3μμ'2+2μ³, μ4, and α3=μ3/σ³
  (decimal; also a `√` exact form when α3² is rational).
* **PROB + CDF.** `Menu("PROB + CDF","P(a<X<b)",…,"P(X>a)",…,"F(x) AT A POINT",…,"BACK",…)`, clipped
  to the support. Add the note `P(X=a)=0 (CONTINUOUS)`.
* **E[g(X)].** First `Input "KINK AT x?",…`. The Disp header reads `IF g HAS A KINK (max,abs)`,
  `TYPE ITS x, ELSE ᴇ99`. When a kink point inside the support is given, integrate [a,s] and [s,b]
  separately. Show E[g], E[g²] and Var(g). EXACT when q and g are polynomials with deg q + 2·deg g
  ≤ 13 (check deg g ≤ 4); otherwise NUMERIC with 2 passes.
* **CDF FORMULA** (polynomial only). `F(x)=0 FOR x≤a`; `c[Q(x)−Q(a)]` printed through POLYSTR for
  a<x<b; `1 FOR x≥b`.
* No fnInt( anywhere. BACK cleans ʟM2O* and the library lists.

**Acceptance** (sympy; Appendix C):
* R3, CDF.
  * F=`X²*Y*(X+Y)/2` on the unit square: f=`3/2x²+2xy` (i.e. x(3x+4y)/2), FX=`1/2x²+1/2x³`,
    FY=`1/2y+1/2y²`, and P(1/4<X≤1/2, 1/2<Y≤1)=25/256.
  * F=`(1-𝑒^(⁻X))*(1-𝑒^(⁻2Y))` on x,y>0: f(1,1) within 1e-6 of 2e^(−3); P(0<X≤1,0<Y≤1) within
    1e-9 of 0.546572343960.
* Freund:
  * Ex16 F=`X*Y*(X+Y)/2`: f=x+y; P(1/2<X≤1,1/2<Y≤1)=3/8.
  * Ex17: P(1<X<3,1<Y<2) within 1e-9 of 0.07397052298.
  * Mock 4 Q6 through EXP PAIR (a=1, b=2): P(X>Y)=2/3; P(X+Y≤1)=1−2e^(−1)+e^(−2) (1e-10).
  * F FROM A PDF f opens M2JNT and gives F(1/2,1/2)=1/8 for q=`X+Y` on the unit square.
* 1-D:
  * HW5 Q2: μ=0, μ'2=1/5, σ²=1/5; g=`X²` gives E=1/5, E[g²]=3/35 and Var=8/175.
  * Mock 5 Q2 (q=`2(1-X)`): μ=1/3, μ'2=1/6, σ²=1/18, α3=2√2/5 (decimal 0.565685); E[√X]=8/15
    (NUMERIC, converged fraction); CDF formula `2x-x²`.
  * Mock 5 Q9 (q=`2X`): μ3=−1/135 and α3≈−0.565685.
  * Mock 5 Q10: f=`𝑒^(⁻X/2)/2` on (0,ᴇ99) gives P(X>1) within 1e-9 of e^(−1/2) (0.606530659713)
    and E[max(X−1,0)] within 1e-8 of 2e^(−1/2) (1.21306131943), with g=`max(X-1,0)` and kink 1.
  * HW5 Q3: q=`3𝑒^(⁻3X)` on (0,ᴇ99) gives μ=1/3 and μ'2=2/9 as converged fractions.
  * Mock II Q3: q=`4X𝑒^(⁻2X)` gives μ=1 and σ²=1/2.
* The total-variance transfer test, ported, passes on M2ONE. No `fnInt(` remains in any src file;
  test_lint_all asserts this.

---

### P5 — M2MGF library (rewrite)

**Goal.** Derive, identify and transform MGFs, with substituted formulas, domains and derivative
lines a student can copy. This covers HW5 Q3 and Q4 and their exam variants: gamma-type
c·x^n·e^(−λx) (the Mock II Q3 is 30 points), uniform, geometric, finite PMF, and identification of
binomial, Poisson, normal, gamma and exponential.

**Files.** src/M2MGF.txt (rewrite), tools/write_presets.py (HW5 Q3 → family 1 {1,3,0,3}; HW5 Q4 →
family 7 normal {7,4,16}) and START_HERE. Tests: tests/test_mgf.py; replace test_cov_mgf's MGF part
and the MGF tests in test_transfer_general.

**Family record `ʟM2MF`** ("current MGF"):
| Code | Family | Record |
|---|---|---|
| 1 | gamma kernel c·x^n·e^(−λx), x>0 | {1,c,n,λ} |
| 2 | uniform(a,b) | {2,a,b} |
| 3 | finite PMF (ʟM2MX values, ʟM2MP probs) | {3} |
| 4 | geometric c·r^x for x=x0,x0+1,… | {4,c,r,x0} |
| 5 | binomial | {5,n,p} |
| 6 | Poisson | {6,λ} |
| 7 | normal | {7,μ,σ²} |
| 8 | gamma (1−βt)^(−α) | {8,α,β} |
| 9 | exponential λ/(λ−t) | {9,λ} |
| 10 | typed | {10}, Str1 in X (=t) |

**Menus.**
* `Menu("MGF TOOLS","FROM A DENSITY",…,"KNOWN FAMILY",…,"TYPED M(t)",…,"Z=aX+b OF LAST",…,"SUM OF COPIES",…,"BACK",Z)`.
* FROM A DENSITY → `Menu("DENSITY","c*x^n*e^(-Lx)",…,"UNIFORM a<x<b",…,"FINITE PMF",…,"GEOMETRIC c*r^x",…,"BACK",…)`.
* KNOWN FAMILY → `Menu("FAMILY","BINOMIAL",…,"POISSON",…,"NORMAL e^(Ct+Dt²)",…,"GAMMA (1-βt)^-α",…,"EXPONENTIAL",…,"GEOMETRIC p",…,"BACK",…)`.

**Formulas** (each result shows M(t) with numbers substituted, its DOMAIN, E X, E X² and Var X):
* **Gamma kernel.** Allow c unknown (the user types 0; then c=λ^(n+1)/n!). Otherwise check
  c·n!/λ^(n+1)=1 and warn "NOT A PDF" if it fails.
  * M=c·n!/(λ−t)^(n+1) for t<λ.
  * Derivation lines:
    `M(t)=∫0..INF e^(tx)f(x)dx`, `=c∫x^n e^(-(λ-t)x)dx`, `=c·n!/(λ-t)^(n+1)`, `NEEDS t<λ`.
  * M'(t)=K(n+1)/(λ−t)^(n+2) and M''(t)=K(n+1)(n+2)/(λ−t)^(n+3), with K=c·n! and the numbers
    shown.
  * E=(n+1)/λ, E X²=(n+1)(n+2)/λ², Var=(n+1)/λ². Also show the Freund form
    `=(1-t/λ)^-(n+1)`.
* **Uniform.** M=(e^(bt)−e^(at))/((b−a)t) for t≠0, M(0)=1; E=(a+b)/2,
  E X²=(a²+ab+b²)/3, Var=(b−a)²/12.
* **Finite PMF.** Input an x list and a weight list (normalised). M=Σ p e^(x t), printed term by
  term; the moments are exact sums.
* **Geometric c·r^x.** Check c·r^(x0)/(1−r)=1. M=c·r^(x0)·e^(x0 t)/(1−r e^t) for t<ln(1/r). With
  p=1−r: x0=1 gives E=1/p and Var=r/p²; x0=0 gives E=r/p and Var=r/p².
* **Binomial.** (1−p+pe^t)^n for all t; E=np, Var=np(1−p); P(X=k) for a typed k.
* **Poisson.** e^(λ(e^t−1)); E=Var=λ; P(X=k).
* **Normal.** Input C and D of e^(Ct+Dt²): μ=C, σ²=2D (D≥0). For D>0 say "NORMAL BY UNIQUENESS".
* **Gamma (1−βt)^(−α).** E=αβ, Var=αβ², t<1/β.
* **Exponential.** E=1/λ, Var=1/λ².
* **Typed (numeric).** The P1 Richardson code, with M(0)=1 assumed and never evaluated. Show 6
  significant digits, plus `LIKELY p/q` when the h and h/2 Richardson values agree to 1ᴇ⁻7 and
  M2FMT finds a fraction.
* **Z=aX+b OF LAST.** M_Z(t)=e^(bt)·M_X(at), substituted per family. Examples:
  * gamma `e^(-t)*4/(2-3t)²`, with domain t<λ/a (a>0), t>λ/a (a<0), all t (a=0);
  * normal `e^((aμ+b)t+(a²σ²/2)t²)` with simplified numbers;
  * binomial `e^(bt)(1-p+pe^(at))^n`.

  E Z=aμ+b, Var Z=a²σ². The new MGF becomes the current one where its family is closed under
  the transform (normal stays normal). Otherwise the record keeps the base family plus (a,b).
* **SUM OF COPIES.** k iid copies: M^k; family closure: binomial(kn,p), Poisson(kλ), normal(kμ,kσ²),
  gamma(kα,β), exponential → gamma(k,1/λ), and gamma kernel → gamma. E=kμ, Var=kσ².
* Every screen keeps to 26 columns. Put the derivation on its own page.

**Acceptance** (sympy, Appendix C):
* HW5 Q3 preset (data only): `3/(3-t)`, `t<3`, E=1/3, E X²=2/9, Var=1/9.
* HW5 Q4: normal C=4, D=8 → μ=4, σ²=16; Z=(X−4)/4 (a=1/4, b=−1) → the screen shows `e^(1/2t²)`
  (drop a zero linear term), E=0, Var=1, `NORMAL BY UNIQUENESS`.
* Mock II Q3: c=4, n=1, λ=2 → `4/(2-t)²`, t<2, M'=`8/(2-t)³`, E=1, Var=1/2; Y=3X−1 →
  `e^(-t)*4/(2-3t)²`, t<2/3, E=2, Var=9/2.
* Mock 5 Q5: c=1/4, n=1, λ=1/2 → E=4, Var=8. Mock 5 Q4: geometric c=1, r=1/2, x0=1 → the screen
  shows `M(t)=1/2e^t/(1-1/2e^t)` and `t<-ln(r)=.693147`, with E=2 and Var=2. Freund Exercise 34:
  c=2, r=1/3 → E=3/2, E X²=3.
* Mock 5 Q6: binomial(5,.7) P(X=4)=7203/20000; Poisson 3 P(X=0)=e^(−3); normal C=2, D=4.5 →
  μ=2, σ²=9; exponential (1−3t)^(−1) → E=3.
* Mock 5 Q7: gamma α=3, β=2 → E=6, Var=12; Y=3X+2 → E=20, Var=108.
* Freund Ex14: finite PMF {0,1,2,3} with weights {1,3,3,1} → E=3/2, E X²=3. Uniform(0,2): E=1,
  E X²=4/3.
* Typed `(1-2X)^⁻3`: E within 1e-5 of 6, Var within 1e-4 of 12. Typed uniform: no crash.
* Sum of 2 Poisson(3) → Poisson(6).

---

### P6 — M2COV hub (rewrite) and M2DISC upgrades

**M2COV spec.**
* **ENTER MOMENTS.** Disp `VARIABLES ARE X,Y,Z,W`; `Input "HOW MANY 1-4?",N`.
  * `Menu("MEANS","MEANS KNOWN",…,"NO MEANS",…)` and `Menu("SPREAD","VARIANCES",…,"STD DEVIATIONS",…)`.
  * For each variable, input the mean (if known) and the variance or SD.
  * If N>1, `Menu("PAIRS","COVARIANCES",…,"CORRELATIONS",…,"ALL INDEPENDENT",…)`. With
    correlations, Cov=ρσiσj.
  * Validate |ρ| ≤ 1 (+1ᴇ⁻9) and positive semidefiniteness by LDLᵀ elimination with tolerance
    1ᴇ⁻9 ("IMPOSSIBLE: COV MATRIX NOT PSD").
  * Store ʟM2MU, ʟM2VR, ʟM2CV (N², row-major) and ʟM2CF.
  * Then show the hub `Menu("LINEAR COMBOS","ENTER MOMENTS",…,"E + VAR OF U",…,"COV + CORR U,V",…,"PAIR INFO",…,"E[POLY(X)]",…,"BACK",Z)`.
    The moments persist.
* **E + VAR OF U.** Disp `U=c+aX+bY+…`, `TYPE {a,b,…} WITH (-)`. Input the coefficient list
  (dim=N) and the constant c.
  * Show E(U) (or MEAN NOT PROVIDED), Var(U) and SD(U) (√ form).
  * WORK: `Var=Σa²σ²+2Σaaσ` with numbers, for example `9(4)+4(9)+1(2)` and
    `+2(3)(-2)(1)+2(3)(1)(-1)…`, wrapped over rows.
* **COV + CORR U,V.** Two coefficient lists and two constants. Show Cov(U,V), Var U, Var V,
  Corr(U,V) (√ form) and the work.
* **PAIR INFO.** For every i<j: σij, ρij, E(XiXj)=σij+μiμj (if means), and E(Xi²)=σi²+μi².
* **E[POLY(X)].** Pick the variable, or type a mean and variance when none are entered; μ'3 is
  optional. Type g(X), a polynomial of degree ≤ 3. Recover its coefficients by sampling at
  X=0,1,2,3 with a fixed inverse-Vandermonde, then check at X=.37. E[g]=Σc_kμ'_k, where
  μ'2=σ²+μ². Show the substitution.
* `Z=99` preload (§4.3) lands on the hub; it serves presets and the DISC/JNT handoff.

**M2DISC spec** (keep existing behaviour that is not mentioned).
* **Entry menu** = `FORMULA ON GRID` (x list, y list, `SUPPORT? 1=ALL` string Str4, q string), `TABLE
  BY ROWS` (x list, y list, then one probability/weight list per x value), `LIST EACH PAIR`
  (existing manual rows), `ONE VARIABLE` (x list + weight list), and BACK.
  * In FORMULA ON GRID, the weight is evaluated only where the support is true, so nCr never sees an
    invalid argument. Freund Ex12 caplets use `(3 nCr X)(2 nCr Y)(4 nCr (2-X-Y))` with support
    `X+Y≤2`.
  * The cap is **99 rows**. Keep the raw weights in ʟM2W.
* **Joint tools.**
  * MOMENTS + COV: as now, plus ρ with a √ form, plus a work line for E[X] when there are ≤ 4
    distinct x.
  * MARGINALS: `MARGINAL TABLES`; `MARGINAL FORMULA` (grid with Str4="1" only: pX(x)=c·Σ_y q(x,y)
    from 5 samples through M2PLY θ=7 and θ=3, printed with `x IN {…}`); `g(x) OR h(y)`.
  * CONDITIONALS: `X GIVEN Y=y`, `Y GIVEN X=x` and `E[g] GIVEN VALUE`.
    * The table lists EVERY distinct value of the other variable, including zero probabilities.
    * It has the header `x | f(x|y=2)` and the line `h(2)=11/37` (the denominator), followed by
      E, E², Var.
  * EVENTS + CDF: `EVENT MENU`, `TYPE AN EVENT`, `P(A|B) TYPED`, `CDF F(a,b)`.
    * The EVENT MENU uses the same items and words → math screens as M2JNT (X<Y, X+Y≤k, MIN/MAX,
      X>a AND Y>b, |X−Y|≤k, X≤s AND Y≤t, complement).
    * It lists the `PAIRS IN EVENT` with their probabilities, for example `(2,1) 3/32`, then the
      total.
  * MORE TOOLS: `E[g(X,Y)]`, `INDEPENDENCE`, `PRODUCT MOMENTS`, `DERIVED PAIR U,V`,
    `SHOW/EDIT TABLE`, `TO LINEAR COMBOS`.
    * INDEPENDENCE precomputes the distinct-x and distinct-y marginals, so it costs
      O(N·(nx+ny)). The counterexample screen is labelled `x=… y=…`, `f(x,y)=…`, `g(x)h(y)=…`.
    * DERIVED PAIR builds the new rows (U,V) with duplicates merged. It requires integer U,V with
      |U|,|V| ≤ 9999 (key = (U+5ᴇ4)·1ᴇ5+(V+5ᴇ4), `SortA`, then merge in one pass). The table is
      replaced.
    * SHOW/EDIT pages through `k: x y w` and allows EDIT ROW k.
    * TO LINEAR COMBOS writes N=2 and the moments, then calls M2COV with Z=99.
  * Add a "TO LINEAR COMBOS" item to M2JNT's MOMENTS menu as well, using the same handoff.
* **Univariate tools.**
  * MOMENTS: μ, μ'2, σ², σ, μ'3, μ'4, μ3, μ4, α3.
  * PROB + CDF: P(a≤X≤b) with the four endpoint variants, F(a).
  * E[g(X)].
  * MGF M(t): prints `M(t)=` with terms `p·e^(xt)` using fractions, and the value at a typed t.
  * SHOW/EDIT, NEW DATA.
* Presets: the HW4 Q1, Q4, HW5 Q1 and Q8 presets change to `99→Z` with Str4=`"1"`. The old codes
  1, 4, 11 and 18 are removed.

**Acceptance** (sympy/Fraction, Appendix C):
* COV:
  * HW5 Q5 = 2465 and HW5 Q6 = 56, as data-only presets landing on the hub.
  * Mock II Q4: E(3X−2Y+5)=13, Var=108, Cov(X+Y,X−Y)=−5, ρ=−1/2, E(XY)=−5.
  * Mock 6 Q3: E W=−1, Var W=42. Mock 6 Q4: Cov=5, Var U=17, Var V=9, Corr=5√17/51.
  * Mock 6 Q5: Var=945. Mock 6 Q9 (CORR 0.6): Cov=18/5, Cov(2X+3,−4Y+1)=−144/5, Corr=−3/5.
  * Freund Ex18: 17 and 18. Ex19: −76.
  * A 4-variable case built from independent parts (as in the existing transfer test).
  * PSD rejection. E[POLY] Mock 5 Q3: E(3X−2)=4, Var(3X−2)=36 (through U), E(X+1)²=13, E[X(X−1)]=6.
* DISC:
  * Mock II Q1 (grid {1,2,3}×{1,2}, q=`X+Y`): c=1/21, the marginal formula `1/7+2/21x` (i.e.
    (2x+3)/21) for x IN {1,2,3}, w(y|1)=2/5, 3/5, E(Y|X=1)=8/5, P(X>Y)=4/7.
  * Mock 4 Q2 (rows of decimals): P(X>Y)=9/20, P(X=Y)=7/20, F(2,1)=1/4.
  * Mock 6 Q1: E X=3/5, E Y=9/10, E XY=1/2, Cov=−1/25, ρ=−√6/21 (≈−0.116642), E(Y|X=0)=1,
    E(Y|X=1)=5/6.
  * Freund Ex12 caplets (support condition): g=5/12, 1/2, 1/12 and Cov=−7/54.
  * Freund Ch4 Ex17 zero-covariance table: Cov=0 and DEPENDENT with a correct witness.
  * Mock 6 Q6 through DERIVED PAIR (X uniform on {−2..2}, U=X, V=X²): Cov=0 and dependent.
  * Two dice → (max,min): P(U=6)=11/36, P(U=4,V=2)=1/18, 21 rows.
  * A 6×6 grid (36 cells) is accepted.
  * R3: HW4 Q4 through EVENT MENU X>Y = 3/32 with the pair `(2,1)`, and X+Y≤3 = 1/4.
  * The conditional table includes zero rows (Freund Ex23: f(2|1)=0).
* Budgets: INDEPENDENCE on 36 cells < 15,000 steps; DERIVED PAIR on 36 cells < 10,000.

---

### P7 — Encyclopedia (M2E4, M2E5, M2E6 replace M2ENC) and HELP pages (M2HLP)

**Files.**
* tools/write_content.py (author all four programs; the HW part stays until P8 rewrites it).
* content/M2E4.json, M2E5.json, M2E6.json and M2HLP.json (generated).
* src/STAM2.txt: the ENCYCLOPEDIA submenu, and HELP = `FIND MY SOLVER`, `HELP PAGES` (M2HLP),
  BACK. Remove the interim HOW TO ENTER and LIMITS pages, since their content moves into M2HLP.
* Delete content/M2ENC.json and src/M2ENC.txt.
* tests/test_reference_navigation.py: generalise to every content/*.json.
* New tests/test_paths.py, plus tests/m2paths.py (a TREE of menus for path validation).

**Encyclopedia outline.** Each program has ≤ 6 sections, about 16 topics and about 26 pages, within
the §3.1 budget of ≤ 12,000 tokenized bytes each; use uppercase where it saves space. Every topic
ends with a Freund citation line and, where a tool exists, a `TOOL SOLV>…` line. Use textbook
examples, never homework answers. Appendix D contains page text that has already been validated:
use it, but re-validate. Topic menu names must be ≤ 18 characters, and the names below already
are.

* **M2E4 "UNIT 4 MULTIVARIATE"** (Freund Ch3 §5–7; Guide Unit 4)
  * JOINT LAWS:
    * JOINT PMF + PDF (Def6 Thm7 p83, Def8 Thm8 p85, Ex13 p83, Ex15 p85);
    * JOINT CDF (Def7 p84, Def9 p86; App D.2);
    * f FROM F, F FROM f (mixed partial p86, Ex16–17 pp86–88; R4);
    * RECTANGLE RULE (Exercise58 p91, integer endpoints; R4);
    * 3 OR MORE RVS (Ex18 p89, Ex22 p94; App D.9).
  * MARGINALS + CONDS:
    * MARGINALS (Def10 p92, Def11 p93, Ex20–21);
    * CONDITIONALS (Def12 p95, Def13 p96, Ex23–24, P(a<X<b|Y=y));
    * JOINT=MARG×COND (Guide Ex4.5 p37);
    * VALUE VS EVENT.
  * INDEPENDENCE: DEFINITION + PROOF and DEPENDENCE PROOF (Def14 p98, Ex25 p97; App D.3); PROPERTIES.
  * LIMITS + WORDS:
    * REGIONS + LIMITS (sketch first, inner/outer, splitting a region, reverse order, complement
      trick, infinite supports; R4);
    * LIMITS EXAMPLE (App D.5);
    * WORDS TO EVENTS (App D.4b);
    * SERIES, PARALLEL (also the meeting problem |X−Y|≤k).
* **M2E5 "UNIT 5 EXPECT + MGF"** (Freund Ch4 §1–5)
  * EXPECTATION: DEFINITION (Def1 p114), E[g(X)], E[g(X,Y)] (Thm1 p115, Thm4 p119), LINEARITY
    RULES (Thm2–3 p117, Thm5 p120).
  * MOMENTS:
    * RAW + CENTRAL (Def2–5 pp122–123);
    * VARIANCE RULES (Thm6 p124, Thm7 p125);
    * μ3, μ4, SKEWNESS (Exercise25 p130; α3=μ3/σ³).
  * MGF BASICS:
    * DEF + DOMAIN (Def6 p127, Ex13 p128);
    * DERIVE AN MGF (App D.6);
    * INTEGRAL TRICKS (∫x^n e^(−ax)dx=n!/a^(n+1), geometric series, the uniform case).
  * MGF PROPERTIES:
    * MOMENTS FROM M (Maclaurin p128, Thm9 p129, Ex14);
    * R(t)=ln M(t) (Exercise35 p131);
    * Z=aX+b (Thm10 p129–130);
    * SUMS (Ch7 Thm3 p226);
    * UNIQUENESS (Ch7 §5 p227, BT §4.1, W Thm3.33, Exercise36 p131, Ch6 Thm6 p187 normal;
      App D finding M14).
  * MGF TABLE: DISCRETE FAMILIES (binomial, Poisson, geometric) and CONTIN. FAMILIES (uniform,
    exponential/gamma, normal), each with M(t), domain, mean and variance.
* **M2E6 "UNIT 6 PRODUCT + COND"** (Freund Ch4 §6–8)
  * PRODUCT MOMENTS: DEFINITIONS (Def7 p131, Def8–9 p132), COVARIANCE RULES (Thm11 p132,
    Cov(aX+b,cY+d)), WORKED COV EXAMPLE (Ex15–16 p133).
  * CORRELATION: DEF + BOUNDS (Ch14 §2 p395, p396; Ch6 §7 p196; BT §4.5); CORR GIVEN, SCALE.
  * ZERO COV: THEOREM 12 (p134) and ZERO NOT INDEP (Ex17 p135; App D.4).
  * LINEAR COMBOS:
    * ONE COMBINATION (Thm14 p136, Cor3 p137, Ex18 p137 check 17/18);
    * TWO COMBINATIONS (App D.10);
    * X+Y AND X−Y (Exercise53 p140);
    * MATRIX SHORTCUT (warn that matrices are user data).
  * CONDITIONAL EXP:
    * DEFINITION (Def10 p138);
    * RECIPES (discrete and continuous);
    * COND EXAMPLE (App D.8; Ex20 p139);
    * COND VARIANCE (p139);
    * TOTAL LAWS (BT §4.3; "not in Freund" per Guide p52).

**M2HLP "HELP PAGES"** (uppercase-leaning, ≤ 6 KB)
* USE CASES: one topic per solver, 6 topics. Each has USE WHEN / YOU TYPE / YOU GET / PATH / A
  MINI-EXAMPLE (non-HW), for example `JOINT DENSITY: q=X*Y, TRI a<X<Y<b, EVENTS>X+Y≤k`.
* KEYS + ENTRY: keypad, ∞=ᴇ99, (-), lists, ÷, the TEST menu, `𝑒^(`, `abs(` (MATH NUM) and `√(`.
* NOTATION: the Freund notation page, App D.1.
* EXAM WORKFLOW: GIVEN → ASKED → SUPPORT/EVENT → SOLVER → WRITE THE SETUP → CHECK (marginal
  integrates to 1).
* MEMORY + ERRORS:
  * archive Midterm I;
  * on ERR choose 1:QUIT and restart STAM2;
  * numeric integrals on infinite regions can take about 1 minute;
  * what the app cannot do (proofs, curved-support formulas, 3+ variable joint laws).

**Acceptance.**
* Every page validates in content.py. All topics are reachable (the generalised navigation test).
* Each of M2E4, M2E5 and M2E6 is ≤ 12,000 tokenized bytes (+15% allowed) and M2HLP ≤ 6,000; the
  total memory test passes.
* Every topic of M2E4/5/6 contains a `Freund` or `BT`/`W`/`Guide` citation line. The test greps
  each topic's pages.
* test_paths: every `TOOL SOLV>…`/`PATH …` string in content/*.json resolves in tests/m2paths.py
  TREE. TREE matches the real menus: walk each solver in the simulator with a small fixed model per
  solver and compare the menu item texts. First words are unique in every menu in TREE.
* The R4 pages exist with Freund Ch3 citations: f from F and F from f, the rectangle formula, and
  regions/limits (order, splitting, complement). The no-631 scan stays clean.

---

### P8 — Finder (M2FIND), homework walkthroughs (M2HW), presets (M2RUN), docs, final package

**Files.**
* New tools/write_finder.py → src/M2FIND.txt.
* Delete src/M2EXAM.txt and tests/test_exam_assistant.py; replace them with
  tests/test_finder.py.
* tools/write_content.py (rewrite of the HW section) → content/M2HW.json and src/M2HW.txt.
* tools/write_presets.py → src/M2RUN.txt.
* src/STAM2.txt (FIND MY SOLVER → M2FIND).
* START_HERE.md (full rewrite).
* tests/test_presets.py (rewrite), tests/test_homework.py (new).
* ../output: final package. Move the outdated app-walkthrough deliverables that describe the OLD
  menus and contain STA 631 extras into `../output/_superseded_v1/` (do not delete them). These
  are `../output/pdf/STA431_Homework_4_5_App_Walkthrough.pdf`,
  `../output/latex/STA431_Homework_4_5_App_Walkthrough/`,
  `../output/STA431_Midterm_II_Calculator_Preview.png` and the old LaTeX sources zip, if present.
  Leave the study guide and notesheets alone.

**M2FIND** is generated from a TREE in write_finder.py. Menus have ≤ 6 items + BACK. Each leaf has
1–2 pages of ≤ 9 lines (uppercase): a recipe of the formula/steps to WRITE, then `PATH SOLV>…`.
Next comes `Menu("NEXT","OPEN SOLVER",…,"BACK",…)`, which runs `0→Z:prgm<solver>` and then returns
to the leaf's menu. The pager keys are the same as content.py's. The tree:
* JOINT PMF/TABLE:
  * c AND MARGINALS;
  * CONDITIONAL + E(Y|x);
  * P(EVENT) OR F(a,b);
  * MEANS COV ρ E[g];
  * INDEPENDENT?;
  * DERIVED (MAX,MIN,X²).
* JOINT PDF:
  * c OR P(EVENT);
  * MARGINAL/COND FORMULA;
  * GIVEN X=x VALUE;
  * MOMENTS COV ρ;
  * INDEPENDENT?;
  * WORD PROBLEM (either/both fail, meet within k, given an event).
* JOINT CDF F(x,y): RECTANGLE PROB; MARGINAL CDF; PDF FROM F; F FROM f; EXPONENTIAL F.
* ONE VARIABLE: PMF TABLE; PDF MOMENTS; PDF PROB/CDF; E[g(X)]; MGF FROM DENSITY.
* MGF GIVEN:
  * MOMENTS;
  * Z=aX+b;
  * IDENTIFY FAMILY;
  * SUM OF INDEP;
  * DOMAIN/UNIQUENESS (opens the encyclopedia, M2E5).
* MEANS/VARS/COVS:
  * ONE COMBINATION;
  * TWO COMBOS / COV;
  * CORR GIVEN;
  * E[POLY(X)];
  * ZERO COV vs INDEP (opens M2E6).

Budget ≤ 8,000 bytes. Every PATH must resolve (test_paths).

**M2HW** (13 topics: HW4 Q1–Q5; HW5 Q1–Q4; HW5 Q5–Q8; ≤ 2 pages each, ≤ 7 KB). Each topic gives:
* GIVEN in Freund notation;
* ASKED;
* SETUP to write (support, limits, or the formula to sum or integrate);
* APP STEPS (the exact path and what to type, using the current solvers);
* `LOAD PRACTICE DATA > HW…` to see the computed results;
* a CHECK hint.

**NO final numeric answers.** test_homework searches the displayed text of every page in
content/M2HW.json for these final answers. The match is case-insensitive, after removing spaces,
and numeric items only count when no digit or `/` comes directly before or after them:
* `1/37`, `17/37`, `20/37`, `5/11`, `6/11`;
* `(1+y)/4`, `(2x+y)/(1+y)`;
* `5/8`, `3/32`, `19/24`;
* `1/40`, `13/4`, `227/20`, `63/80`, `8/175`, `3/(3-t)`, `2/9`, `e^(t²/2)`;
* `2465`, `56`, `y+1/2`, `1/2+y`, `7/12`, `11/144`;
* `13/6`, `14/3`, `-1/36`, `⁻1/36`, `20/9`.

`1/4` is NOT on the list, because HW4 Q5's given density is f=1/4(2x+y). Intermediate method text
such as "c=1/SUM OF WEIGHTS" is fine.

**M2RUN.** `Menu("PRACTICE DATA","HW4 Q1-Q5",…,"HW5 Q1-Q4",…,"HW5 Q5-Q8",…,"FREUND EXAMPLES",…,"MOCK MIDTERM II",…,"BACK",Z)`.
Each item shows a one-screen GIVEN summary (the data only), then writes the preload variables and
`99→Z:prgm<solver>`.
* The HW items are the 13 STA 431 problems.
* FREUND EXAMPLES:
  * Ch3 Ex13 kxy grid;
  * Ch3 Ex15 3/5x(y+x) rect;
  * Ch3 Ex24 2/3(x+2y);
  * Ch4 Ex15/Ch3 Ex12 caplets (support condition);
  * Ch4 Ex16 density 2 on the simplex;
  * Ch4 Ex17 zero-covariance table (rows);
  * Ch4 Ex18/Ex19 moments for COV;
  * Exercise 51.

  That is more than 6, so use two submenus.
* MOCK MIDTERM II: Q1 grid, Q2 q=`X` TRI, Q3 gamma kernel {1,4,1,2}, Q4 COV moments.

**START_HERE.md**, a full rewrite for a student who does not know TI-BASIC:
* transfer (TI Connect CE, all N .8xp files);
* MEMORY (archive Midterm I, keep the M2 programs in RAM, the free-RAM check, Press-to-Test);
* the first run;
* the main menu and full menu tree with path codes;
* "How to type": X, Y, ᴇ99, (-), lists, ÷, `𝑒^(`, `abs(`, TEST;
* a solver-by-solver "use when", with one non-HW example each;
* the exam workflow;
* EXACT vs NUMERIC (fractions only when converged);
* limitations;
* 8 DEVICE CHECKS with exact keystrokes and expected screens. Use non-HW examples from Appendix C,
  such as Mock II Q2 P(X+Y≤1)=3/8 and the exponential pair 2/3. Also include one numeric
  infinite-support check and a timing note;
* error recovery;
* rebuilding from source.

All counts and paths must match the code; test_paths also scans START_HERE for `SOLV>` paths.

**Acceptance.**
* The full build succeeds; the programs are exactly the §3.1 list (17).
* The total .8xp size is ≤ 118,000 bytes, and the build prints a per-program table.
* test_menu_tree covers the final tree with 0 errors and 0 leaks.
* test_finder: every leaf is reachable, and OPEN SOLVER returns to the leaf's menu.
* test_presets: every preset loads data only. Its solver shows the analysis menu with no Input
  prompt, and the solver's computed results equal the sympy targets for all 13 HW items. Spot-check
  3 FREUND and 2 MOCK items.
* test_homework: no forbidden answer strings; all 13 problems present.
* No 631 strings anywhere. START_HERE paths are valid.
* The package and its zip are written to `../output/STA431_Midterm_II_Calculator_Package`; the
  superseded docs are moved.

---------------------------------------------------------------------------------------------------
## 8. Audit findings: adopted (where) / rejected (why)

| ID | Finding | Decision |
|---|---|---|
| B1 | build fails on STAM2 `<=` | P1 |
| B2 | stale out/ | P1 (build clears and rebuilds out/) |
| B3 | build swallows diagnostics; lint line numbers | P1 |
| D1 | START_HERE contradicts app | P1 partial, every package incremental, P8 full rewrite |
| X1/M04/COV-05 | STA 631 content | P1 (Appendix F), test enforced |
| T1 | tests hard-code menu indices | P1 (text menu choice, m2test) |
| R1 | memory | P1 budget test, P7 HELP page, P8 START_HERE |
| U1 | silent stale Y | P2 VARCHECK in every new tool |
| U2 | re-entry friction | P2/P3 persistent model + one-pass moments; P6 COV hub, DISC edit |
| U3 | HELP shape | P7 (M2HLP) + P8 (M2FIND) |
| U4 | prompts over old screens | convention §4.4, all new/rewritten code |
| U5 | missing labels/context | convention §4.5 |
| U6 | confusing prompts (FIXED A, AREA, EVEN N, X1..X3, braces) | removed with M2CONT/M2SLICE; COV names X,Y,Z,W; list prompts show braces |
| U7 | missing spaces | P1 START_HERE, P7 content, P8 HW |
| U8 | finder drops at top menus | P8: leaves print PATH and open the solver; deep jumps rejected (see below) |
| R2 | slow double integral | superseded by M2GL (P2) |
| R3 | modes | P1 (Float/Normal/Real) |
| R4 | fnInt(expr) on hardware | removed: M2GL replaces fnInt (P2–P4); device checks P8 |
| N1/M03/COV-04 | MGF numeric derivatives | P1 interim Richardson, P5 final |
| M01/M02/COV-08 | Simpson wrong fractions, exponentials | P1 interim gating; P2/P3 replacement engine (exact poly, graded numeric, gating) |
| M05 | notation | §4.5 screens + P7 NOTATION page |
| M06/M07 | citations | P7 (Appendix E index) |
| M08 | F↔f coverage | P3 F formula, P4 M2CDF, P7 pages |
| M09 | independence justification | P3 INDEP test + P7 pages |
| M10 | words/limits | P2 words→math + written limits; P7 pages |
| M11 | MGF derivation | P5 FROM A DENSITY + P7 page |
| M12 | cond. expectation example; 3+ RVs | P7 pages (no trivariate solver, see rejected) |
| M13 | linear-combination forms | P6 show work + P7 pages |
| M14 | uniqueness details | P7 |
| M15 | fnInt tolerance | moot (no fnInt after P4) |
| M16 | M2EXAM wording | P1 |
| M17 | readability of numbers | P7/P8 |
| M18 | conditional table hides zeros | P6 |
| M19 | HW justification details | P8 as method lines only (no final answers) |
| M20 | encyclopedia structure | P7 (unit programs) |
| L1 | tilint configured for Midterm I | P1 |
| L2 | dead code | P1 (631 codes), P6 (univariate menu) |
| L3 | content capacity | P7 (3 unit programs) |
| COV-01 | symbolic marginal/conditional formulas | P3 (critical) |
| COV-02 | infinite supports | P2 kernel + P4 EXP PAIR |
| COV-03 | MGF families | P5 |
| COV-06 | finder not delivered | P1 builds M2EXAM; P8 M2FIND |
| COV-07 | joint moments one pass | P3 |
| COV-09 | linear combos scope | P6 (n≤4, CORR, hub, E(XY), show work) |
| COV-10 | discrete entry | P6 (TABLE BY ROWS, support, cap 99, derived pair) |
| COV-11 | E(Y|X=x) function | P3 |
| COV-12 | moment algebra | P6 E[POLY(X)] |
| COV-13 | CDF conversions | P3 F formula, P4 M2CDF + M2ONE CDF formula |
| COV-14 | discrete marginal formula | P6 |
| COV-15 | keystroke costs | P2–P6 |
| STUDENT R1–R4 | | P4 (+P3 F from f), P2, P2/P4/P6, P7 |

---------------------------------------------------------------------------------------------------
## Appendix A — validated prototype code (simulator-tested by the prime agent)

Rename the lists to the §4.2 prefixes when you adopt this code (ʟGT→ʟM2KT, etc.).

**A.1 Gauss–Legendre constants on [0,1]** (14 significant digits):
```
GL7 nodes   {.025446043828621,.12923440720030,.29707742431130,.5,.70292257568870,.87076559279970,.97455395617138}
GL7 weights {.064742483084435,.13985269574464,.19091502525256,.20897959183673,.19091502525256,.13985269574464,.064742483084435}
GL5 nodes   {.046910077030668,.23076534494716,.5,.76923465505284,.95308992296933}
GL5 weights {.11846344252809,.23931433524968,.28444444444444,.23931433524968,.11846344252809}
```

**A.2 Strip decomposition and EXACT integration over a convex polygon (ʟPX,ʟPY → moments ʟPR)**.
In the simulator, polynomials of degree ≤ 4 in each variable on triangles and rectangles had a
maximum error of 1.3e-13 against sympy, at about 375 steps per strip.
```
ʟPX→ʟPZ
SortA(ʟPZ)
dim(ʟPX)→N
{ʟPZ(1)}→ʟPD
For(I,2,N)
If ʟPZ(I)-ʟPD(dim(ʟPD))>1ᴇ⁻10*(1+abs(ʟPZ(I)))
augment(ʟPD,{ʟPZ(I)})→ʟPD
End
{0,0,0,0,0,0}→ʟPR
For(K,1,dim(ʟPD)-1)
ʟPD(K)→A
ʟPD(K+1)→B
(A+B)/2→M
ᴇ99→C
⁻ᴇ99→D
For(I,1,N)
I+1-N*(I=N)→J
ʟPX(I)→E
ʟPX(J)→F
If (E-M)*(F-M)<0
Then
(ʟPY(J)-ʟPY(I))/(F-E)→G
ʟPY(I)-G*E→H
H+G*M→L
If L<C
Then
L→C
H→ʟPL(1)
G→ʟPL(2)
End
If L>D
Then
L→D
H→ʟPL(3)
G→ʟPL(4)
End
End
End
// strip: x in [A,B], lower y=ʟPL(1)+ʟPL(2)x, upper y=ʟPL(3)+ʟPL(4)x
35→dim(ʟNX)
35→dim(ʟNY)
35→dim(ʟNW)
35→dim(ʟNQ)
0→O
For(I,1,7)
A+(B-A)*ʟGT(I)→X
ʟPL(1)+ʟPL(2)*X→E
ʟPL(3)+ʟPL(4)*X→F
For(J,1,5)
O+1→O
E+(F-E)*ʟGS(J)→Y
X→ʟNX(O)
Y→ʟNY(O)
(B-A)*(F-E)*ʟGW(I)*ʟGV(J)→ʟNW(O)
expr(Str1)→ʟNQ(O)
End
End
ʟNW*ʟNQ→ʟNW
ʟPR+{sum(ʟNW),sum(ʟNW*ʟNX),sum(ʟNW*ʟNY),sum(ʟNW*ʟNX²),sum(ʟNW*ʟNY²),sum(ʟNW*ʟNX*ʟNY)}→ʟPR
End
```
(ʟGT/ʟGW = GL7, ʟGS/ʟGV = GL5. In the kernel, the strips arrive precomputed in ʟM2KS; M2JNT does
the decomposition. Note that `ʟPL` must exist with dim 4 before use.)

**A.3 Coefficient recovery (M2PLY θ=1).** Recovers q(X,Y) with degree ≤ 4 in each variable. Max
coefficient error was 3e-12 (for (1+x)^4(2−y)^3/3), and it correctly rejected 𝑒^(⁻X−2Y), 1/X and
X^5, at about 370 steps.
```
{⁻3/2,⁻1/2,1/2,3/2,5/2}→ʟQN
{⁻5/128,15/32,45/64,⁻5/32,3/128,1/24,⁻9/8,9/8,⁻1/24,0,7/48,1/6,⁻7/8,2/3,⁻5/48,⁻1/6,1/2,⁻1/2,1/6,0,1/24,⁻1/6,1/4,⁻1/6,1/24}→ʟQV
25→dim(ʟQS)
For(I,1,5)
ʟQN(I)→X
For(J,1,5)
ʟQN(J)→Y
expr(Str1)→ʟQS(5I+J-5)
End
End
25→dim(ʟQB)
For(M,1,5)
seq(ʟQV(5M-5+I),I,1,5)→ʟQR
For(J,1,5)
sum(ʟQR*seq(ʟQS(5I+J-5),I,1,5))→ʟQB(5M+J-5)
End
End
25→dim(ʟQA)
For(M,1,5)
seq(ʟQB(5M-5+I),I,1,5)→ʟQR
For(N,1,5)
sum(ʟQR*seq(ʟQV(5N-5+I),I,1,5))→ʟQA(5M+N-5)
End
End
max(abs(ʟQA))→H
ʟQA*(abs(ʟQA)>1ᴇ⁻11*H)→ʟQA
// verify at (.37,.61) and (1.27,-.69): |poly-expr(Str1)| ≤ 1ᴇ⁻9*(1+|poly|) else NOT POLY
```
(ʟQV is the inverse Vandermonde matrix for the nodes, stored row-major. ʟQA(5i+j+1) is the
coefficient of X^i·Y^j. M2PLY may clobber only `I J K O X Y θ Q R S T U V W`, so replace the
prototype's M, N, H, P and S with those registers (for example M→Q, N→R, H→T, P→U, S→V). Never
touch the caller's A–H or L–P.)

**A.4 Numeric graded panels with an automatic cutoff.** Prototype `PINF`, one strip, M = panels:
```
// outer cutoff when B≥1ᴇ6: probe A+2^K, K=⁻3..12; first value <1ᴇ⁻13*peak after K=⁻3 gives C
// panel edges: seq(A+H*(2^I-1),I,0,M)  with H=(C-A)/(2^M-1)
// inner: same for an infinite upper limit at EACH outer node; finite inner → graded edges on [L,U]
```
Simulator results with M=4/6:
* 2e^(−x−2y), y>x (both directions infinite): errors 3.1e-10/3.6e-11, at 6,935/12,221 steps.
* x e^(−x(1+y)) total: 7.8e-10/9.9e-11.
* 4xy e^(−x²−y²): 1.2e-8/1.2e-9.
* Rate 1/5: 1.6e-9. Rate 10: 6.9e-10.

With a single finite inner panel, P(X>Y) had an error of 2.5e-7. That is why §4.6 requires graded
inner panels and the max-of-3 outer probe; with them it is 4.7e-9 (m=5) and 3.7e-12 (m=7) in the
Python reference (Appendix B).

**A.5 Sutherland–Hodgman clipping** (ʟPX,ʟPY by the half-planes in ʟPH, triples aX+bY≤c). Chained
with A.2, it was exact (≤ 2e-14) in both orders on: HW4 Q5 (19/24), HW4 Q3 survival (3/8),
Mock II X+Y<1 (3/8), Mock 4 Q3 (1/6), the meeting problem (7/16), Mock 4 Q4 (5/24) and Mock 4 Q5
(1/8), at ≤ 1,500 steps. For the reverse order, swap X↔Y in the polygon, in each half-plane
(a↔b), and in the evaluation roles.
```
For(H,1,dim(ʟPH)/3)
ʟPH(3H-2)→A
ʟPH(3H-1)→B
ʟPH(3H)→C
dim(ʟPX)→N
If N≥3
Then
1ᴇ⁻12*(1+abs(C)+max(abs(ʟPX))*abs(A)+max(abs(ʟPY))*abs(B))→T
{0}→ʟPU
{0}→ʟPV
0→O
For(I,1,N)
I+1-N*(I=N)→J
A*ʟPX(I)+B*ʟPY(I)-C→D
A*ʟPX(J)+B*ʟPY(J)-C→E
If D≤T
Then
O+1→O
ʟPX(I)→ʟPU(O)
ʟPY(I)→ʟPV(O)
End
If (D>T and E<⁻T) or (D<⁻T and E>T)
Then
D/(D-E)→F
O+1→O
ʟPX(I)+F*(ʟPX(J)-ʟPX(I))→ʟPU(O)
ʟPY(I)+F*(ʟPY(J)-ʟPY(I))→ʟPV(O)
End
End
If O<3
Then
{0}→ʟPX
{0}→ʟPY
Else
seq(ʟPU(I),I,1,O)→ʟPX
seq(ʟPV(I),I,1,O)→ʟPY
End
End
End
```
(Remove consecutive duplicate vertices afterwards. Use registers allowed by §4.2: the prototype
used A–F and T, which is fine inside M2JNT as long as no M2FMT call happens in between.)

## Appendix B — Python reference for the numeric rule (§4.6)
```python
import math, numpy as np
x7,w7=np.polynomial.legendre.leggauss(7); T7=(1+x7)/2; W7=w7/2; BIG=1e6
def probe(h,L,U):
    pk=0.0
    for k in range(-3,13):
        z=L+2.0**k
        if z>=U: break
        v=abs(h(z)); pk=max(pk,v)
        if k>-3 and pk>0 and v<1e-13*pk: return z
    return None
def edges(h,L,U,m):
    T=probe(h,L,U) if U>=BIG else None
    if T is None: T = L+4096 if U>=BIG else U
    H=(T-L)/(2**m-1); return [L+H*(2**i-1) for i in range(m+1)]
def integ(f,A,B,lo,hi,m):            # m=5 pass 1, m=7 pass 2
    def ho(x):
        L,U=lo(x),hi(x); ys=[L,L+1,L+2] if U>=BIG else [L,(L+U)/2,U]
        return max(abs(f(x,y)) for y in ys)*(1 if U>=BIG else max(U-L,1e-300))
    tot=0.0
    for a,b in zip(*(lambda E:(E,E[1:]))(edges(ho,A,B,m))):
        for t,w in zip(T7,W7):
            x=a+(b-a)*t; L,U=lo(x),hi(x); s=0.0
            F=edges(lambda y:f(x,y),L,U,m)
            for c,d in zip(F,F[1:]):
                for tt,ww in zip(T7,W7): s+=(d-c)*ww*f(x,c+(d-c)*tt)
            tot+=(b-a)*w*s
    return tot
```
Errors (pass 1 / pass 2):
* 2e^(−x−2y): P(X>Y) 4.7e-9/3.7e-12; P(Y>X) 7e-11/3e-11; P(X+Y<1) 6e-17/1e-16.
* x e^(−x(1+y)): 3.2e-10/8.2e-11.
* 4xy e^(−x²−y²): 4.2e-9/2.5e-10.
* 2e^(−x−y) on y<x: 1.2e-9/1.5e-11.
* e^(x+y) on the unit square: 0/9e-16.
* 1/x on 0<y<x<1: 0/0.
* Rate 1/5: 2.9e-10/8.6e-11.

## Appendix C — verified targets (sympy/Fraction, prime agent; tests must recompute them)

**Joint PDF**
| Model (q, support) | Targets |
|---|---|
| Mock II Q2: q=x, 0<y<x<1 | c=3; g=3x²; h=3/2(1−y²); w(y\|x)=1/x on 0<y<x; P(X+Y<1)=3/8; P(Y<1/4\|X=1/2)=1/2; dependent |
| Mock 4 Q3: xy, 0<x<y<1 | c=8; g=4x(1−x²); h=4y³; f(x\|y)=2x/y²; P(X+Y<1)=1/6; P(X<1/2\|Y=3/4)=4/9; E(Y\|X=x)=2(x²+x+1)/(3(x+1)) |
| Mock 4 Q4: x+2y, 0<x<2, 0<y<1 | c=1/4; g=(x+1)/4; h=y+1/2; P(X<Y)=5/24; P(X+Y<1)=1/8 |
| Mock 4 Q5: 2/3(x+2y), unit sq | P(min≤1/2)=5/8; P(max≤1/2)=1/8 |
| Meeting: 1, unit sq | P(\|X−Y\|<1/4)=7/16 |
| 2e^(−x−2y), quadrant | P(X>Y)=2/3; P(Y>X)=1/3; P(X+Y<1)=1−2e^(−1)+e^(−2)=0.399576400894; E XY=1/2; P(X<1,Y<1)=0.546572343960 |
| e^(−x), 0<y<x<∞ | total 1; P(X<2Y)=1/2; h(y)=e^(−y) |
| x e^(−x(1+y)), quadrant | total 1; h(1)=1/4; E(X\|Y=1)=1; P(X>1\|Y=1)=3e^(−2) |
| Mock 6 Q2: 2, 0<x<y<1 | EX=1/3; EY=2/3; EXY=1/4; Cov=1/36; VarX=VarY=1/18; ρ=1/2; E(Y\|x)=(1+x)/2 |
| Mock 6 Q7: 3/2(x²+y²), unit sq | h=3y²/2+1/2; f(x\|y)=3(x²+y²)/(3y²+1); E(X\|1/2)=9/14; Var=71/980 |
| Freund Ch4 Ex16: 2, x+y<1 | EX=1/3; EXY=1/12; Cov=−1/36 |
| Freund Ex20/Ex24: 2/3(x+2y) | f(x\|y)=2(x+2y)/(4y+1); at y=1/2: E=5/9, E X²=7/18, Var=13/162; P(X≤1/2\|Y=1/2)=5/12 |
| Exercise 51: (x+y)/3, (0,1)×(0,2) | Var(3X+4Y−5)=805/162 |
| HW5 Q7 (data): x+y | h=y+1/2; f(x\|y)=2(x+y)/(2y+1) |
| Freund Ex16: x+y unit sq | F=xy(x+y)/2; F(1/2,1/2)=1/8 |
| Freund Ch3 Ex15: 3/5x(y+x), (0,1)×(0,2) | P(0<X<1/2,1<Y<2)=11/80 |

**Joint CDF**
| F | Targets |
|---|---|
| x²y(x+y)/2 unit sq (R3) | f=x(3x+4y)/2; FX=x²(x+1)/2; FY=y(y+1)/2; P(1/4<X≤1/2,1/2<Y≤1)=25/256 |
| (1−e^(−x))(1−e^(−2y)) (R3) | f=2e^(−x−2y); P(0<X≤1,0<Y≤1)=0.546572343960 |
| xy(x+y)/2 (Ex16) | P(1/2<X≤1,1/2<Y≤1)=3/8 |
| (1−e^(−x))(1−e^(−y)) (Ex17) | P(1<X<3,1<Y<2)=0.07397052298 |

**One variable**
| f | Targets |
|---|---|
| 3/4(1−x²), (−1,1) (HW5 Q2 data) | μ=0; μ'2=1/5; σ²=1/5; μ'4=3/35; Var(X²)=8/175 |
| 2(1−x), (0,1) (Mock 5 Q2) | μ=1/3; μ'2=1/6; σ²=1/18; μ3=1/135; α3=2√2/5; E√X=8/15; Var(3X+2)=1/2; F=2x−x² |
| 2x (Mock 5 Q9) | μ=2/3; μ'2=1/2; μ'3=2/5; σ²=1/18; μ3=−1/135; α3=−2√2/5≈−0.565685 |
| e^(−x/2)/2 (Mock 5 Q10) | P(X>1)=e^(−1/2); E max(X−1,0)=2e^(−1/2)=1.21306131943 |
| 4x e^(−2x) (Mock II Q3) | μ=1; μ'2=3/2; σ²=1/2 |

**MGF**: HW5 Q3: 3/(3−t), E=1/3, E X²=2/9, Var=1/9 · Mock II Q3: 4/(2−t)², E=1, E X²=3/2, Var=1/2;
Y=3X−1: e^(−t)4/(2−3t)², E=2, Var=9/2 · Mock 5 Q5: (1−2t)^(−2), E=4, Var=8 · Mock 5 Q4: geometric
E=2, E X²=6, Var=2 · Ex34: E=3/2, E X²=3, Var=3/4 · binomial(5,.7) P(4)=7203/20000 · Poisson 3
P(0)=e^(−3) · Mock 5 Q7: E=6, E X²=48, Var=12; Y=3X+2: E=20, Var=108 · Ex14: E=3/2, E X²=3 ·
uniform(0,2): E=1, E X²=4/3.

**COV**: Mock II Q4: E=13, Var=108, Cov(X+Y,X−Y)=−5, ρ=−1/2, E XY=−5 · Mock 6 Q3: −1, 42 · Mock 6 Q4:
5, 17, 9, 5√17/51 · Mock 6 Q5: 945 · Mock 6 Q9: 18/5, −144/5 · Ex18: 17, 18 · Ex19: −76 · Mock 5 Q3:
E(3X−2)=4, Var=36, E(X+1)²=13, E X(X−1)=6.

**DISC**: Mock II Q1: c=1/21, P(X>Y)=4/7, E(Y\|X=1)=8/5 · Mock 4 Q2: P(X>Y)=9/20, P(X=Y)=7/20,
F(2,1)=1/4 · Mock 6 Q1: EX=3/5, EY=9/10, EXY=1/2, Cov=−1/25, ρ=−√6/21, E(Y\|X=0)=1, E(Y\|X=1)=5/6
· caplets: g=5/12,1/2,1/12; EX=2/3, EY=4/9, Cov=−7/54 · Ch4 Ex17: Cov=0, f(0,−1)=1/3 vs 2/9 ·
Mock 6 Q6 (X,X²): Cov=0 · dice max/min: P(U=6)=11/36, P(4,2)=1/18, 21 rows · Ex13 kxy k=1/36.

## Appendix D — encyclopedia page text validated by the math audit (content.validate passed)

Reuse these texts with the `t(menu, *paragraphs)` helper. Re-run validation after any edit. Insert
a space before numbers where the source omits it.

* **D.1 FREUND NOTATION.**
  'Joint f(x,y) is a PMF or a PDF. Marginals g(x), h(y). Conditionals f(x|y)=f(x,y)/h(y) and w(y|x)=f(x,y)/g(x).' /
  'HW writes fX|Y(x|y) for f(x|y) and fY|X(y|x) for w(y|x). Joint CDF F(x,y)=P(X≤x,Y≤y).' /
  "Raw moment μ'r=E(X^r). Mean μ=μ'1. Central μr=E[(X-μ)^r]. Variance σ²=μ2." /
  "Product moments μ'r,s=E(X^r*Y^s), μr,s=E[(X-μX)^r(Y-μY)^s]. Covariance σXY=μ1,1." /
  'MGF MX(t)=E(e^(tX)). Conditional mean μX|y=E(X|y). Conditional variance σ²X|y.' /
  'Freund Ch3 Defs6-14 pp83-98. Ch4 Defs1-10 pp114-138.'
* **D.2 JOINT CDF.**
  'F(x,y)=P(X≤x,Y≤y) for ALL real x,y. Discrete sums f(s,t) over s≤x,t≤y (Def7 p84). Continuous integrates f(s,t) over s≤x,t≤y (Def9 p86).' /
  'f(x,y)=mixed partial d²F/dxdy where it exists (p86). Marginal CDF FX(x)=F(x,inf).' /
  'Ex16 p86. f=x+y on unit square. F=xy(x+y)/2 if 0<x<1,0<y<1. F=y(y+1)/2 if x≥1,0<y<1. F=x(x+1)/2 if 0<x<1,y≥1. F=1 if x≥1,y≥1. F=0 if x≤0 or y≤0.' /
  'Ex17 p87. F=(1-e^(-x))(1-e^(-y)) for x,y>0 gives f=e^(-x-y). P(1<X<3,1<Y<2)=0.074.' /
  'P(a<X≤b,c<Y≤d) = F(b,d) - F(a,d) - F(b,c) + F(a,c). Exercise58 p91.' /
  'Integer X,Y with a≤X≤b, c≤Y≤d use a-1 and c-1 in place of a and c.'
* **D.3 INDEPENDENCE.**
  'Def14 p98. X,Y independent iff f(x,y)=g(x)h(y) for ALL (x,y) in their range. PDFs use densities.' /
  'Equivalent forms. f(x|y)=g(x) whenever h(y)>0 (p98). F(x,y)=FX(x)FY(y) for all x,y.' /
  'PROVE INDEPENDENT. Support is a rectangle or full grid AND f=a(x)b(y). Then g is proportional to a and h to b.' /
  'PROVE DEPENDENT. Give ONE pair with f(x,y)≠g(x)h(y). On a triangle use a point outside the support where g(x)>0 and h(y)>0. For a PDF the failure must hold on a positive-area region.' /
  'Ex25 p97. 4xy on unit square has g=2x, h=2y, f=gh, independent. Ex24 f(x|y) depends on y, dependent.' /
  'Independent => E(XY)=E(X)E(Y), σXY=0 (Thm12 p134). var of a sum = sum of vars (Cor3 p137). MGF of a sum = product (Ch7 Thm3 p226).'
* **D.4 ZERO NOT INDEP** (P1 replaces the old page with this).
  'Thm12 p134. Independent => E(XY)=E(X)E(Y), so σXY=0. The converse is FALSE.' /
  'Ex17 p135. f(-1,-1)=1/6, f(0,-1)=1/3, f(1,-1)=1/6, f(-1,1)=1/6, f(1,1)=1/6, all other pairs 0.' /
  "μX=0, μY=-1/3, μ'1,1=0, so σXY=0-0*(-1/3)=0." /
  'But f(-1,-1)=1/6 while g(-1)h(-1)=(1/3)(2/3)=2/9. One failing pair => dependent.' /
  'Covariance measures only LINEAR association.'
* **D.4b WORDS TO EVENTS.**
  'Name each variable and its units. Then write the event as a set A in the plane.' /
  'at least a => X≥a. at most a => X≤a. more than a => X>a. total under c => X+Y<c. first fails before second => X<Y. within d => abs(X-Y)<d.' /
  'both => intersection. either or at least one => union. not => complement, 1-P.' /
  'Fails if EITHER fails => lifetime min(X,Y). P(min≤t)=1-P(X>t,Y>t). Fails only if BOTH fail => max(X,Y). P(max≤t)=F(t,t).' /
  'Given X=x0 (a value) => use w(y|x0). Given X>a (an event) => P(A and B)/P(B).' /
  'Guide 4.2.4 p35. Freund Ex15 p85, Ex27 p99.'
* **D.5 LIMITS EXAMPLE.**
  'Guide Ex4.3 p36. f=6x on 0<x<y<1. Fixed x => y runs x..1. Fixed y => x runs 0..y.' /
  'g(x)=6x(1-x) on 0<x<1. h(y)=3y² on 0<y<1. Triangle support => dependent.' /
  'P(X+Y<1). Need x<y<1-x, so x<1/2. Integral x 0..1/2, y x..1-x of 6x = 1/4.' /
  'Reverse order. Split where the right edge changes, e.g. on 0<x<1, 0<y<2 the event X<Y needs y 0..1 with x 0..y, plus y 1..2 with x 0..1.' /
  'Check that every marginal integrates to 1. It catches most limit errors.'

  (This version deliberately has no homework answer; the audit's draft quoted HW4 Q5's number.)
* **D.6 DERIVE AN MGF.**
  'Write M(t)=sum or integral of e^(tx)f(x). Combine exponents. State the t values where it converges.' /
  "Ex13 p128. f=e^(-x), x>0. M=integral of e^(-(1-t)x)=1/(1-t) for t<1. μ'r=r!." /
  'Ex14 p129. f=C(3,x)/8, x=0..3. M=(1+e^t)³/8 for all t. Mprime(0)=3/2. Msecond(0)=3.' /
  "Exercise34 p131. f=2(1/3)^x, x=1,2,3,etc. Geometric sum M=2e^t/(3-e^t) needs e^t<3, i.e. t<ln3. μ'1=3/2, μ'2=3." /
  'Exercise36 p131. M(0) must be 1, so t/(1-t) is never an MGF.'
* **D.8 COND EXAMPLE.**
  'Def10 p138. E[u(X)|y]=sum or integral of u(x)f(x|y). μX|y=E(X|y). σ²X|y=E(X²|y)-μ²X|y (p139).' /
  'Ex20 p139. f=2/3(x+2y) on unit square. h(y)=(1+4y)/3. f(x|y)=(2x+4y)/(1+4y).' /
  'At y=1/2, f(x|1/2)=2(x+1)/3 on 0<x<1. E(X|1/2)=5/9. E(X²|1/2)=7/18. σ²X|1/2=13/162.' /
  'Recipe. marginal of GIVEN variable, then conditional law, then E(X|y), E(X²|y), subtract.'
* **D.9 3 OR MORE RVS.**
  'For X1 to Xn, f(x1,..,xn) = P(all Xi=xi). The marginal of X1 sums or integrates out ALL others. A joint marginal keeps several.' /
  'Ex18 p89. f=(x+y)z/63, x=1,2; y=1,2,3; z=1,2. P(X=2,Y+Z≤3)=13/63.' /
  'Ex22 p94. f=(x1+x2)e^(-x3) on 0<x1<1,0<x2<1,x3>0. m(x1,x3)=(x1+1/2)e^(-x3). g(x1)=x1+1/2.' /
  'Independence needs f=f1*f2*..*fn for all points (Def14 p98). Pairwise independence is weaker (Ex22, Exercise81).'
* **D.10 TWO COMBINATIONS.**
  'Thm15 p137. cov(Y1,Y2)=Σ ai*bi*var(Xi) + Σ over i<j of (ai*bj+aj*bi)cov(Xi,Xj).' /
  'Cor4 p138. Independent Xi => cov(Y1,Y2)=Σ ai*bi*var(Xi).' /
  'Ex19 p138 check. U=X+4Y+2Z, V=3X-Y-Z, vars 8,12,18, covs XY1, XZ-3, YZ2 => cov(U,V)=-76.' /
  'var(X+Y)=varX+varY+2cov. var(X-Y)=varX+varY-2cov. cov(X+Y,X-Y)=varX-varY (Exercise53 p140).'
* **Extra lines from the math audit to merge into pages.**
  * MGF UNIQUENESS: 'M(0)=1 is necessary (Exercise36 p131). B>0 => normal mean A var 2B (Ch6 Thm6 p187). Uniqueness Ch7 S5 p227; BT S4.1; W Thm3.33.'
  * ONE COMBINATION: 'Ex18 p137 check. W=3X-Y+2Z, means 2,-3,4, vars 1,5,2, covs XY-2, XZ-1, YZ1 => E(W)=17, var(W)=18.'
  * CONDITIONALS: 'P(a<X<b|Y=y)=integral a..b of f(x|y)dx. Ex24 p96, f(x|1/2)=(2x+2)/3, P(X≤1/2|Y=1/2)=5/12.' and 'Joint = marginal × conditional, f(x,y)=g(x)w(y|x) (Guide Ex4.5 p37).'
  * CORRELATION citation: 'Freund Ch14 S2 p395 (ρ=σXY/(σXσY)), p396 (-1≤ρ≤1); Ch6 S7 p196; BT S4.5'.

## Appendix E — Freund citation index (printed pages; verified against freund.txt / freund_ch4.txt)

**Ch3:**
* Def6/Thm7 p83, Ex12–13 pp82–83;
* Def7 p84; Def8/Thm8 p85, Ex15 p85;
* Def9 p86, the mixed partial p86, Ex16–17 pp86–88;
* Ex18 p89; Exercise58 p91;
* Def10 p92, Ex20; Def11 p93, Ex21 p93; Ex22 p94;
* Def12 p95, Ex23; Def13 p96, Ex24 p96;
* Ex25 p97; Def14 p98, f=f(x|y)h(y) p98; Ex27 p99.

**Ch4:**
* Def1 p114; Thm1 p115; Thm2–3, Cor1–2 p117; Thm4 p119; Thm5 p120;
* Def2–4 p122; Def5 p123; Thm6 p124; Thm7 p125; Exercises 23, 25 p130;
* Def6 p127, Ex13 p128, Maclaurin p128; Thm9 p129, Ex14 p129; Thm10 pp129–130;
  Exercises 33–37, 40 pp130–131;
* Def7 p131; Def8–9, Thm11 p132; Ex15–16 p133; Thm12 p134; Ex17 p135;
* Thm13 p135; Thm14 p136; Cor3 p137, Ex18 p137, Thm15 p137; Cor4 p138, Ex19 p138;
* Def10 p138; μX|y and σ²X|y p139, Ex20 p139; Exercises 46–55 p140.

**Elsewhere:** Ch6 §7 p196 (ρ in the bivariate normal); Ch6 Thm6 p187 (normal MGF); Ch7 Thm3 p226;
Ch7 §5 p227; Ch14 §2 pp395–396.

**Guide:** Unit 4 pp32–42 (Thm4.6 p34, §4.2.4 p35, Ex4.3 p36, Ex4.5 p37, Mock 4 p41); Unit 5
pp43–51 (Mock 5 p50); Unit 6 pp52–61 (Mock 6 p60); Mock Midterm II p98.

**BT** §4.1 (MGF inversion), §4.3 (total laws), §4.5 (correlation). **W** Thm 3.33.

## Appendix F — STA 631 removal checklist (P1) and the scan used by test_lint_all

Locations to clean:
* tools/write_content.py: the `sec('OPTIONAL 631',…)` block, and the `ZERO NOT INDEP` page
  (uniform with Y=X², which mirrors 631 HW5 Q8).
* tools/write_presets.py: the D1, D2 and D3 entries, the "OPTIONAL 631" menu item, `Lbl D`, and
  "Generated 16".
* src/M2CONT.txt lines 4–5 (codes 21, 22, 23).
* src/M2EXAM.txt E3/F4 (the 631 hint wording).
* tests/test_presets.py: the three `test_631_*` tests.
* tests/test_slice.py: the reimbursement and triangle tests.
* tests/test_disc_cont.py: the `24X*(1-X-Y)` case.
* tests/tests_exam_assistant.py: flags 21–23.
* START_HERE.md: "plus 3 marked STA631 extensions" and "All 16 common/431/optional631".
* The regenerated M2HW, M2RUN, M2ENC and content/*.json.

**Scan** (case-insensitive, over src/*.txt, content/*.json, tools/write_*.py, START_HERE.md and
tests/*.py excluding test_lint_all.py itself): `631`, `OPTIONAL 6`, `REIMBURS`, `24X*(1-X-Y)`,
`(20-X)`, `1-abs(X)`, `abs(X)<1/2`. Zero matches are required.
