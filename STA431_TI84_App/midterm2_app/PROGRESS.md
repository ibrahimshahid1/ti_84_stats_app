# PROGRESS — STA 431 Midterm II suite (one section per package)

## P1

**Status: done.** Foundation package: the build is fixed and hardened, STA 631 material is gone,
the main menu has the requested shape, tests choose menus by text, and the two interim numeric
safety fixes are in.

### What was built
* **Build fix + tibuild.** STAM2's `<=` string is now `"Finite rows ≤30; combos≤3"`. `tibuild.py lint`
  counts errors per file (later files print their byte size again), prints a `TOTAL:` line, and
  reports ORIGINAL file line numbers (`line_map_of()`, `read_program(path, with_map=True)`,
  `lint_program(name, clean, line_map)`).
* **tilint.** `FORMATTER='M2FMT'`, `MAIN_PROGRAM='STAM2'`; messages name the configured formatter.
  No new warnings appeared. M2FMT's header comment no longer says STAFMT (code unchanged).
* **STAM2 (P1 shape).** `Float`/`Normal`/`Real`/`0→Z` first; main menu ENCYCLOPEDIA, SOLVERS, HELP,
  HOMEWORK PRACTICE, QUIT. SOLVERS = DISCRETE TABLE, DENSITY+INTEGRAL, MGF TOOLS, LINEAR COMBOS,
  BACK (each `0→Z`, call, back to SOLVERS). HELP = FIND MY SOLVER (`0→Z:prgmM2EXAM`), HOW TO ENTER
  (2-page pager: KEYS, NOTATION; ENTER next, LEFT previous/menu, CLEAR menu), LIMITS + CAVEATS
  (the two old screens, fixed and uppercased). HOMEWORK PRACTICE = WALKTHROUGHS (M2HW), LOAD
  PRACTICE DATA (notice screen, then M2RUN). QUIT = `ClrHome` + final `""` (blank screen, no Done).
  STAM2 is 1,874 tokenized bytes (1,950 as .8xp).
* **STA 631 removal (Appendix F).** write_content.py: OPTIONAL 631 section deleted, ZERO NOT INDEP
  page replaced with the Freund Ex17 text (D.4). write_presets.py: D1–D3, the menu item and `Lbl D`
  deleted, prints "Generated 13 input presets". M2CONT: codes 21–23 removed. M2EXAM: E3 and F4
  reworded ("To show dependence give one (x,y) with f(x,y)≠g(x)h(y), or show the support is not a
  product set"), D3 "Two matching moments / cannot identify the law.", C2 "Var(X^2) needs E[X^4].".
  Generated files regenerated. The Appendix F scan is enforced by `tests/test_lint_all.py`.
* **Numeric safety (interim).** M2CONT DOUBLE INTEGRAL: after both passes `P=1` when
  `abs(F-D)>1ᴇ⁻9*max(1,abs(F))` or the same for G/E; then every RAW I/RAW J/NORMALIZE value shows
  Str8 plus the row `NOT CONVERGED - RAISE N`. M2MGF TYPE MGF NUMERIC: never evaluates M(0)
  (`{1,…}→ʟM2MV`), checks `abs(M(.001)-1)<.05` ("M(0) MUST BE 1"), uses D2(h)=(M(h)+M(⁻h)-2)/h²,
  reports Richardson `(4D(h/2)-D(h))/3` for D1 and D2 (h=.01,.005); the warning compares Richardson
  vs the h=.005 value at relative 1ᴇ⁻4 (+1ᴇ⁻8 floor). ʟM2MD now has 7 cells.
* **Tools.** tisim `{"menu": "TEXT"}` = exact stripped item text, else the unique prefix; no match or
  an ambiguous match raises SIM:ACTION listing the items (docstring updated). Snapshots now carry
  `"stack"` (prgm call chain). play.py accepts `m:TEXT` (quote texts with spaces).
* **build_package.py** rewritten to PLAN §6 (runs every write_*.py, content gen, both linters — WARN
  lines also fail —, every tests/test_*.py with counts, clears and rebuilds out/, checks each program
  has an .8xp, memory budget 118,000, safe DEST recreation, VALIDATION.json/.txt, SHA256SUMS, .zip).
  Exposes `program_order()`, `tokenized_sizes()`, `memory_estimate()` (used by test_lint_all).
* **START_HERE.md** rewritten for the P1 menus: 11-program list, main-menu table, Memory (archive
  Midterm I via 2nd MEM > 2:Mem Mgmt/Del > 7:Prgm, ENTER toggles `*`, keep M2*/STAM2 unstarred,
  Press-to-Test disables programs), Modes, N advice "use 8; raise it until CHANGE is 0", new device
  checks (convergence warning, uniform MGF), spaces restored, no 631 text.

### Files
* src: STAM2.txt, M2CONT.txt, M2MGF.txt, M2EXAM.txt, M2FMT.txt (comment only); regenerated
  M2ENC.txt, M2HW.txt, M2RUN.txt; content/M2ENC.json, content/M2HW.json.
* tools: tibuild.py, tilint.py, tisim.py, play.py, build_package.py, write_content.py,
  write_presets.py.
* tests: NEW m2test.py, test_lint_all.py (main P1 file; holds `# PLAN DEVIATIONS / EXTRA FIXES`),
  test_menu_tree.py; RENAMED tests_exam_assistant.py → test_exam_assistant.py (git mv); EDITED
  test_presets.py, test_slice.py, test_disc_cont.py, test_reference_navigation.py,
  test_workflow_upgrades.py, test_cov_mgf.py, test_transfer_general.py.
* START_HERE.md, PROGRESS.md (new), out/ (11 fresh .8xp incl. M2EXAM.8xp).
* ../output/STA431_Midterm_II_Calculator_Package (+ .zip) rebuilt. The v1 package's hand-made
  HOMEWORK_WALKTHROUGH.pdf and PREVIEW.png were moved (not deleted) to
  `../output/_superseded_v1/package_v1_extras/` before the from-scratch rebuild.

### Tests (all expected values from sympy/Fraction inside the tests)
* test_lint_all (10): both linters clean on every program, tilint config + clobber check, original
  line numbers, Appendix F scan, program list vs src stems/START_HERE, prgm references exist, no
  Midterm I names, memory estimate (66,700 ≤ 118,000), menu limits.
* test_menu_tree (9): DFS over every Menu( choice from STAM2 keyed by (call chain, program, line):
  276 runs, 59 distinct menus, 124 input/key leaves, 0 errors/leaks/warnings; main-menu shape;
  Float/Normal/Real first and `""` last; HELP>FIND MY SOLVER>BACK; QUIT (blank, no Done);
  SOLVERS>BACK>QUIT; HOW TO ENTER keys + content; practice notice before presets.
* Numeric gating (test_disc_cont): q=6X, x 0..1, y X..1, g=X*Y, N=4 shows `NOT CONVERGED - RAISE N`
  and never 819/2048 (or 51/128, 2/5); a converged case (g=X, N=8) keeps exact fractions.
* MGF (test_cov_mgf): (1-2X)^⁻3 E within 1e-5 of 6, VAR within 1e-4 of 12 (sympy limits);
  (𝑒^(2X)-1)/(2X) runs, E within 1e-5 of 1, VAR within 1e-4 of 1/3; M(0) and positivity guards.
* Replaced STA 631 data: test_slice → Freund Ex20 (M=1, 5/9, 7/18, 13/162), Ex24 interval 5/12,
  Mock 4 Q3 (g(1/2)=3/2, E(Y|X=1/2)=7/9, P(Y<3/4|X=1/2)=5/12) + a given-Y variant;
  test_disc_cont triangle → density 2 on x+y<1 with g=XY (F=1, G=1/12, Freund Ch4 Ex16);
  test_exam_assistant flags [1,2,11,13,14,15,16,17,18].
* Totals: 10 test files, 182 counted checks, all green; build_package succeeded
  (11 programs, 66,436 .8xp bytes).

### §0A amendment items
* None of A1–A4 is tagged P1 (A1/A2 → P2, A3 → P4, A4 → P3 and P6). Nothing to implement here.

### Deviations (also listed at the top of tests/test_lint_all.py)
* `NOT CONVERGED - RAISE N` instead of `NOT CONVERGED: RAISE N` (colon in a string = lint WARN).
* HOW TO ENTER: `ON ERR CHOOSE 1 QUIT` (no colons) and `FRACTIONS 1/2 = DIVIDE KEY` (÷ has no string
  token); LEFT on page 1 returns to the HELP menu.
* Richardson warning uses `>1ᴇ⁻4*abs(R)+1ᴇ⁻8` (tiny absolute floor for zero means).
* Old-menu names inside the encyclopedia/HW text were updated to the P1 names; preset intro says
  `USE EVEN N=8 OR MORE`.
* test_transfer_general and test_cov_mgf were also migrated to text menus (beyond the plan's list).

### Fix round 1 (independent verifier issues)
All critical, high and medium issues fixed; the low ones too (details at the top of
`tests/test_lint_all.py` under FIX ROUND 1).
* **Infinite bounds (critical/high).** HOW TO ENTER teaches `ᴇ99`, but no P1 tool accepted it: the
  DOUBLE INTEGRAL showed a converged exact 0, 1D PDF and JOINT SLICE crashed (ERR:OVERFLOW). Now
  M2CONT rejects |B|,|C|≥1ᴇ5 for the 1D bounds (Lbl AP, covers presets) and the DOUBLE x bounds,
  checks the evaluated y limits H,J at every node (P=2, fnInt skipped, after the loop
  `If P=2:Goto BY`), and M2SLICE rejects |A|,|B|,|C|≥1ᴇ5. One shared message (`BOUNDS MUST BE
  FINITE` / `NO ᴇ99, ABS MUST BE <1ᴇ5` / cutoff hint / `RERUN AT 2T, SAME = OK`; `(A Y LIMIT IS
  INFINITE)` for y) re-prompts the bounds (1D → A1, DOUBLE → new Lbl J2). Extra row `I=0 - CHECK q
  AND BOUNDS` when RAW I is exactly 0. HOW TO ENTER adds `(NOT IN DENSITY+INTEGRAL)` under the ᴇ99
  row.
* **Gate at the N cap (medium).** The row is now Str0: `NOT CONVERGED - RAISE N`, `N=100 IS MAX -
  USE DECIMAL`, or `CHANGE<1ᴇ⁻6 - USE DECIMAL` (a quartic+ outer integrand, e.g. q=6X, g=XY, never
  meets the 1ᴇ⁻9 test; at N=100 its change is 3.75ᴇ⁻9). DOUBLE INTEGRAL menu gains `NEW N` (keeps
  the region); the N prompt has a ClrHome header (start 8, max 100, time grows with N). START_HERE
  and the preset intro (`START WITH EVEN N=8` / `RAISE N IF NOT CONVERGED`) no longer promise
  CHANGE 0; START_HERE explains the three rows, the cap and the run time.
* **EVAL Mz AT t=0 (high).** `Mx(0)=1` is used when G=3 and |a·t|<1ᴇ⁻12 (row `Mx(0)=1 BY
  DEFINITION`), so the uniform MGF no longer divides by 0; ClrHome + header before the prompt.
* **MGF step warning (medium).** D1/D2 at h=.01, .005, .0025; the reported value is the next
  Richardson level (16R(.005)−R(.01))/15 = (D(.01)−20D(.005)+64D(.0025))/45; the warning fires only
  when its estimated error |R(.005)−final| exceeds 1ᴇ⁻6 relative (+1ᴇ⁻8). (1-2t)^-3 now shows 6,
  48, 12 with `RELATIVE ERROR EST <1ᴇ⁻6`; 1/(1-20t) warns with `TRY M(X/10), SCALE 10a`. The check
  screen (`NUMERIC STEP CHECK`) shows the h=.005 and the Richardson values; "RICH" is spelled out.
* **M(.001) message (low).** Kept the guard (it also keeps M(±.01) off poles; the suggested
  mean-free product test lets 1/(1-100t) through to M(.01)=1/0), reworded: `M(.001) IS NOT NEAR 1`,
  `(M(0) MUST BE 1)`, and the rescale advice `TYPE M(X/10), SCALE 10a` (verified: 1/(1-5X), a=10
  gives E 50, Var 2500).
* **HOW TO ENTER / LIMITS (low).** Page 1 header `KEYS     ENTER=NEXT    1/2`, rows merged
  (`X=X,T,θ,n(FUNC) Y=ALPHA 1`, `⁻3 = (-) KEY  1/2 = DIVIDE`), last row `CLEAR OR LEFT=HELP MENU`;
  START_HERE Modes says to keep FUNCTION graph mode. LIMITS rows `TABLE ROWS ≤30`, `LINEAR COMBOS ≤3
  VARIABLES` replace the mixed-case `Finite rows ≤30; combos≤3`.
* **Tests (low).** test_menu_tree types canned valid inputs (CANNED table keyed by program+prompt;
  every prompt must have one), keys menus reached through typed data by the choice that started the
  entry, passes each pager once with CLEAR, and asserts: every Menu( line in src reached (41/41),
  INIT unchanged on every run, no ʟM2* list whenever control is back in STAM2 alone (39 checks).
  1,738 runs, ~17 s. It catches the old EVAL t=0 crash (checked on a patched copy). New pager tests
  (CLEAR and LEFT on page 1), LIMITS rows.
* **No homework answers in START_HERE (low).** Device checks now use a made-up table, Freund Ex20 and
  Ch4 Ex16, the 6X triangle (gate + NEW N), the ᴇ99 rejection, made-up LINEAR COMBOS and
  normal-MGF data, the uniform and Mock 5 Q5 MGFs, and a made-up X+Y+1 grid. M2HW walkthrough pages
  still print final homework numbers: **P8 must-fix** (rewrite M2HW without answers; §0).
* New/changed tests: test_disc_cont +8 cases (N=100 decimal row, N cap row, NEW N, I=0, infinite x
  and y bounds with cutoff 20 vs sympy 2/3 and 1/3, 1-D ᴇ99 then cutoff 40 vs sympy cutoff
  integrals, huge lower bound); test_slice +2 (ᴇ99 then cutoff 40 vs sympy h(1)=1/4, 1, 3/2, 1/2;
  huge given value); test_cov_mgf +4 and 4 updated (no warning on accurate (1-2t)^-3/uniform/
  e^(100t²), warning + rescale on 1/(1-20t), large-mean message + rescale, Mock 5 Q5 transform,
  EVAL at t=0, 1/2 and a=0); test_menu_tree +4; test_reference_navigation header text.
* DoD after the fix: all 10 test files green (200 counted checks), build_package to
  ../output/STA431_Midterm_II_Calculator_Package succeeded (+ .zip), both linters 0/0, memory
  67,563 .8xp bytes (66,727 tokenized; estimate 67,827 ≤ 118,000). Per program now: STAM2 1906,
  M2CONT 3648, M2MGF 3963, M2RUN 2506, M2SLICE 1933 (others unchanged).
* Not done (out of P1 scope, recorded for later packages): Simpson over a cutoff region is still
  slow to converge (e.g. 2e^(-x-2y) to x=20 needs N=100 for ~1.5e-5); P2's M2GL replaces it with
  graded panels and true infinite tails. P5 replaces the typed-MGF code (fixed h, rescale advice).

### Notes for the next builder (P2)
* Use `tests/m2test.py` (`m('TEXT')`, `i(v)`, `k(code)`, `run(...)`, `screen`, `after`, `num`).
  `run()` asserts no error/leaks/warnings, INIT preserved, and no ʟM2* list left (pass
  `allow_lists=True` while a module is mid-flow). Never hard-code menu positions.
* tisim snapshots have `"stack"`; test_menu_tree keys menus by call chain, so new solvers called
  from STAM2 are explored automatically. Add "JOINT DENSITY" after DISCRETE TABLE in STAM2's
  SOLVERS menu (P2) and update `test_main_menu_shape` in tests/test_menu_tree.py plus the walk in
  tests/test_reference_navigation.py and START_HERE's table/program count (test_lint_all checks
  that START_HERE names every program and says "<N> programs").
* Memory now: 66,436 .8xp bytes / 65,600 tokenized (estimate 66,700). Per program: STAM2 1874,
  M2CONT 3124, M2COV 2355, M2DISC 4526, M2ENC 23528, M2EXAM 13081, M2FMT 290, M2HW 8991,
  M2MGF 3666, M2RUN 2425, M2SLICE 1740 (tokenized). The .8xp header is 76 bytes per program.
* `python3 tools/build_package.py ../output/STA431_Midterm_II_Calculator_Package` takes ~30 s.
* Known leftovers for later packages (not P1 scope): M2HW walkthrough pages still print final
  homework numbers (P8 rewrites M2HW without answers); encyclopedia/HW text still lacks spaces
  before numbers ("enter6 rows") — P7/P8 rewrite those programs; M2CONT/M2SLICE still use fnInt(
  (removed by P3/P4); M2EXAM is replaced by M2FIND in P8.
* tilint's formatter check now runs against M2FMT; keep Q–V dead across `prgmM2FMT` calls.

## P2

**Status: done** (all acceptance items, A1 and A2). One open risk for P3: M2JNT is already 12,283
tokenized bytes (plan budget 12,000 for P2+P3, hard cap +15% = 13,800); see "Notes for P3".

### What was built
* **M2GL** (3,328 B) integration kernel, PLAN 4.3/4.6. θ=1 2-D over strips ʟM2KS (7 numbers each,
  kind 1 = curved via expr(Str2)/expr(Str3) at X=s, finite outer range only), ʟM2KO={orient,mode};
  θ=2 1-D over ʟM2KS={a,b} with ʟM2KO={var,mode}, the other variable held; θ=9 deletes every ʟM2K*.
  Mode 1 EXACT = one GL7×GL7 panel per strip; mode 2/3 NUMERIC = 5/7 graded panels (1:2:4:…) per
  direction with GL7, probed cutoffs for semi-infinite ranges (first probe <1ᴇ⁻13·running peak,
  else 4096 and θ=2 "heavy"), (-∞,U] probed downward, (-∞,∞) split at 0. |v|≥5ᴇ5 = infinite.
  Speed trick: q and g are rewritten once per call with X→(ʟM2KX), Y→(ʟM2KY) into Str6/Str7, so one
  expr( evaluates a whole node list (per outer node in 2-D). OUT ʟM2KR (9 numbers, true X,Y) and
  ʟM2KP (∫q per strip); θ=1 OK / 2 heavy tail. Clobbers I J K O Q–W X Y θ, Str6, Str7 (only when
  Str5≠"1"), ʟM2K*. Never touches Str0, Str8, Str9, A–H, L–P.
* **M2PLY part 1** (1,698 B): θ=1 RECOVER2 (whitelist pre-screen, 25 samples, inverse Vandermonde,
  1ᴇ⁻11 zeroing, 2 off-grid checks; uses Str7 as scratch), θ=2 LINESTR, θ=3 POLYSTR, θ=8 VARCHECK
  (also rejects lowercase letters), θ=9 deletes every ʟM2Q*. θ=8 touches only θ (callers park q in
  Str0/Str7 while checking other strings).
* **M2JNT** (12,283 B): top menu (NEW MODEL, EVENTS + LIMITS, FORMULAS/MOMENTS + COV/GIVEN A
  VALUE/INDEP + CDF = "COMING IN THIS VERSION"/"USE EVENTS + LIMITS", BACK); an analysis item without
  a model runs NEW MODEL first and then continues to it. NEW MODEL: q prompt + VARCHECK "XY", SUPPORT
  menu (7 items) and CUSTOM menu (X OUTER, Y OUTER, CURVED), ᴇ99 = ∞, |finite|<1ᴇ5, linear-bound
  test, UPPER BELOW LOWER, polynomial-on-infinite refusal, total ≤0 refusal, q<0 warning, summary
  screen. Z=99 preload (Str1 + ʟM2JM, Str2/Str3 for code 8) skips the prompts and lands on the menu.
  EVENTS: every menu of PLAN 7 P2 item 4 plus A1's COMPLEMENT OF… (7th MORE EVENTS item); SETUP
  (words → math table), LIMITS (A2 header P=∫∫ c*q(x,y) dy dx, c=, q=, ORDER …, then pieces),
  RESULT (complement arithmetic, EXACT / NUMERIC, 2 PASSES AGREE / APPROX - NOT CONVERGED +
  CHANGE=, TAIL MAY BE HEAVY); EVENT RESULT menu REVERSE ORDER, COMPLEMENT 1-P, NEW EVENT, BACK;
  P(A|B) with inclusion–exclusion for complemented A and/or B; curved support → CURVED SUB-REGION
  (numeric, clipped to the support). BACK deletes ʟM2J* and runs M2GL/M2PLY θ=9.
* **Integration:** STAM2 SOLVERS = DISCRETE TABLE, JOINT DENSITY, DENSITY+INTEGRAL, MGF TOOLS,
  LINEAR COMBOS, BACK (HOW TO ENTER row "(JOINT DENSITY ONLY)", LIMITS row "DENSITY+INTEGRAL
  FINITE"). M2EXAM B1, B5, B6 open M2JNT (texts rewritten). write_presets.py: HW4 Q2/Q3/Q5 →
  `99→Z:prgmM2JNT` with {1,0,1,0,2}/{1,0,2,0,2}/{1,0,1,0,2} (M2CONT's codes 2/3/5 hooks are now
  dead; P3 deletes them). write_content.py tool routes (CHOOSE A SOLVER, HW4 Q2/Q3/Q5) name JOINT
  DENSITY. START_HERE: 14 programs, ~85 KB, JOINT DENSITY table row + "Joint densities" section,
  practice-data note, device checks 10–13 (Mock II Q2, Mock 4 Q5, 2e^(-x-2y) quadrant, Mock 4 Q4/Q3).

### Files
* New: src/M2GL.txt, src/M2PLY.txt, src/M2JNT.txt, tests/test_kernel.py, tests/test_joint_events.py
  (main P2 test file; holds `# PLAN DEVIATIONS / EXTRA FIXES`).
* Changed: src/STAM2.txt, src/M2EXAM.txt, tools/write_presets.py (→ src/M2RUN.txt),
  tools/write_content.py (→ content/*.json, src/M2ENC.txt, src/M2HW.txt), tests/test_presets.py,
  tests/test_exam_assistant.py, tests/test_menu_tree.py, tests/test_reference_navigation.py,
  START_HERE.md, PROGRESS.md; out/ and ../output/STA431_Midterm_II_Calculator_Package (+ .zip).

### Tests (expected values from sympy/Fraction inside the tests)
* test_kernel (13): 12 random degree-≤4 polynomials on random triangles (both orients) vs sympy,
  error < 1e-11 for all 6 moments; g-moments; min q; numeric quadrant targets (pass 1 ≤5e-9, pass 2
  ≤4e-10: total, P(X>Y), P(Y>X), P(X+Y<1), E(XY)); x e^(-x(1+y)), e^(-x) on 0<y<x, 4xy e^(-x²-y²);
  e^(x+y), 1/x, curved 0<y<x², negative inner range → 0; 1-D exact/semi-/doubly-infinite; heavy-tail
  flag; cleanup modes; RECOVER2 (random + typed forms + rejections), LINESTR, POLYSTR, VARCHECK.
* test_joint_events (33): HW4 Q3 (=1-P(X>t,Y>t), 3/8, 5/8), HW4 Q5 (19/24 both orders, pieces
  x 0..1 / y x..2 and y 0..1 / x 0..y + y 1..2 / x 0..1), HW4 Q2 (c=1/4), HW4 Q4 via M2DISC
  (3/32, 1/4, complements 29/32, 3/4); Mock II Q2 (c=3, 3/8, 2 pieces, reverse 1 piece, A2 header
  in both orders), Mock 4 Q3 (8, 1/6), Mock 4 Q4 (1/4, 5/24, 1/8), Mock 4 Q5 (5/8, 1/8 and the other
  two MIN/MAX items), meeting 7/16 and its complement, P(X<1/2|Y>1/2)=2/5 (3/8, 15/16, COMPLEMENT 1-P
  3/5), P(A|B) with a built-in-complement A and a COMPLEMENT OF B (both orders), custom X-outer
  (c=1/2, P(Y>1)=1/2, both orders) and Y-outer supports, rectangle/CDF/interval/both-exceed/X+Y≥k,
  6 random custom supports × random half-plane events vs an independent Python Sutherland–Hodgman +
  sympy reference (both orders); numeric 2e^(-x-2y) (T=1, 2/3 shown as a fraction in both orders,
  1/3, .399576400894), |X-Y|≤1/4 on the quadrant (far-tail strip dropped), e^(-x) on 0<y<x<∞
  (P(X<2Y)=1/2), curved q=3 on 0<y<x² (T=1, sub-region 1/16 and its complement, a kinked sub-region
  shows APPROX), heavy-tail and q<0 warnings, a long q wraps without display warnings; A1 menu
  shape, HW4 Q5 complement 5/24, Mock 4 Q4 complement 7/8, COMPLEMENT 1-P (also after COMPLEMENT
  OF); A2 header lines; rejections (NOT LINEAR X², VARCHECK 2X+T, a Y in an X bound, UPPER BELOW
  LOWER ×2, polynomial on the quadrant, |bound|≥1ᴇ5, total ≤0), EVENT MISSES SUPPORT → 0, event
  number guard; top menu, no-model flow, COMING items, Z=99, list cleanup; step budgets.
* Step counts (simulator): EXACT model entry ≈1,540 (<3,000); EXACT events 1,655 (X<Y), 1,910
  (min≤t), 2,490 (X+Y≤k, 2 pieces), 3,659 (|X-Y|≤k, 3 pieces), reverse ≤3,455 (<5,000); numeric
  quadrant model 8,171 and event 8,430 (<80,000).
* Updated: test_presets (HW4 Q2/Q3/Q5 through M2JNT), test_exam_assistant (B1 text; conditioning case
  via M2JNT P(A|B)), test_menu_tree (SOLVERS shape, CANNED inputs for 19 M2JNT prompts, M2JNT in
  the module list, new SOLVERS > JOINT DENSITY > BACK route; 2,623 runs, 299 menus, every Menu( line
  reached, 0 errors/leaks/warnings, ~37 s), test_reference_navigation (walk includes JOINT DENSITY).
* Totals: 12 test files, 247 counted checks, all green; build_package succeeded (14 programs, 84,854
  .8xp bytes; 83,790 tokenized; limit 118,000); both linters 0 errors / 0 warnings.

### §0A amendment items
* **A1 done**: COMPLEMENT OF… (7 MORE EVENTS items), SETUP `NOT A => A'` / `P(A')=1-P(A)` / `A=…`,
  RESULT `A=…`, `P(A)=…`, `P(A')=1-P(A)`, `=1-…`, `=…` with A's LIMITS shown; EVENT RESULT >
  COMPLEMENT 1-P prints `P(NOT A)=1-P(A)`, `=1-…`, `=…` (or `P(NOT A|B)=1-P(A|B)`). Acceptance values
  5/24, 7/8, 29/32, 3/4 tested. (The M2DISC EVENT MENU complement display remains P6.)
* **A2 done**: first LIMITS page `P=∫∫ c*q(x,y) dy dx` (dx dy), `c=…`, `q=…` (wrapped), `ORDER dy dx
  (x OUTER)` (or dx dy (y OUTER)), then the pieces; asserted on HW4 Q5 (typed 2X+Y, c=1/4) and Mock
  II Q2 in both orders.

### Deviations (also at the top of tests/test_joint_events.py)
* Pieces are `x FROM a TO b` / ` y FROM l TO u` / ` PIECE=v` (a colon ends a TI string); messages
  with colons are split or use " - ". A' instead of Aᶜ (no ᶜ glyph). "COMPLEMENT OF…" (… token),
  "|X-Y| >k" ("|>" tokenizes as ►), "CURVED SUB-REGION" (18-character menu limit).
* Geometry from half-planes and line breakpoints instead of polygon clipping (same strips, less
  code); strips beyond |x|≥5ᴇ5 dropped; adjacent identical strips merged.
* M2GL: 5ᴇ5 infinity threshold; GL7×GL7 EXACT; Str6/Str7 scratch (not Str0); interior probe points;
  zero probes give zero-length segments; negative inner ranges contribute 0. θ=9 cleanup modes.
* RECOVER2 uses a token whitelist (function tokens cannot be written in TI string literals); the
  curved clip uses comparisons instead of max(/min( for the same reason.
* Custom linear bounds sampled at .37, 1.37, 2.37. Summary support text is outer/inner ranges.
* SETUP/LIMITS/RESULT are one paged text shown after computing (A's SETUP right after picking A).
* Curved supports need finite a,b.

### Notes for P3 (and later)
* **Memory.** M2JNT is 12,283 B. P3 must stay ≤13,800 B for M2JNT (plan budget 12,000 +15%), i.e.
  ≤ ~1.5 KB more, which is too little for FORMULAS/MOMENTS/GIVEN/INDEP. Options: put the heavy lifting
  in M2PLY modes 4–7 (planned anyway), keep M2JNT's new code to menus + display, and if needed move
  one analysis area into a new helper program (document it as a deviation; total limit 118,000,
  current estimate 85,258). Compaction ideas not yet done: G1 label building (~350 B), the curved
  event text (~800 B), the custom-bound Disp texts.
* **Calling RG.** Put half-planes in ʟM2JE ({0,0,1} = whole support), the order in P (0 dy dx,
  1 dx dy), a new return code in C, and `Goto RG`. RG fills ʟM2JT={∫∫q, pass2-pass1, misses,
  heavy, min q}, ʟM2KS (strips in (outer,inner) coordinates) and ʟM2KP; RT appends LIMITS text unless
  C=1 or C=6 (add new silent codes there) and RR dispatches on C (codes 1–6 used; add yours before
  the final `Goto VX`). For moments call M2GL yourself on ʟM2KS with Str5=g. The support half-planes
  are in ʟM2JS, the tuple in ʟM2JG={x0,x1,l0,l1,u0,u1} (code 7 transposed: y outer), c in M,
  exact flag ʟM2JC(1), "c is a fraction" ʟM2JC(3).
* **Registers.** A–H, L–P are M2JNT's (meanings in the M2JNT header); M = c and N = support code
  (0 = no model) must survive; P is the order. G doubles as the post-NEW-MODEL route (1 events,
  2 the analysis items → currently F1; P3 should route each item).
* **Text.** Build Str0 = "θ" + sections "TITLEθlineθ...θθ" and `Goto PG` with a return code in D
  (1 ER, 2 NR, 3 EM, 4 RW); PG pages it with 9 rows per page, repeats the title, wraps by display width
  (the whitelist inside PG must contain every 1-character token you print; other tokens count 6),
  and starts a new page before a line beginning with x or y when fewer than 3 rows remain.
* **M2PLY** callers: θ=8 needs the checked string in Str1 (park q in Str0 or Str7); RECOVER2 clobbers
  Str7. Add any new ʟM2Q* names to M2PLY's θ=9 cleanup, and new ʟM2K* names to M2GL's.
* M2CONT still has the dead preset hooks for codes 2, 3, 5 (now unused); P3 deletes them with the
  DOUBLE INTEGRAL. The test_menu_tree CANNED table has the M2JNT prompts; add new ones there.

## LEAN-A

**Status: done** (reduced P4, budget mode: M2CDF only; no EXP PAIR TEMPLATE, no M2ONE; M2CONT stays).
§0A **A3 implemented** (tails + min/max from F, formula line first on every result, HW4 Q3/Q5 and
both R3 variants through M2CDF). R1, R3 (CDF half), R4 pages done.

### What was built
* **src/M2CDF.txt** (new, SOLVERS > CDF OF X AND Y). Top menu `JOINT CDF`: NEW F(X,Y), RECTANGLE
  PROB (submenu `a<X≤b,c<Y≤d`, `X>a AND Y>b`, `MIN/MAX ≤ t`, BACK), MARGINAL CDFs, PDF f FROM F,
  F FROM A PDF f, BACK. An item chosen without a model runs NEW F first, then continues (route G).
  * NEW F: Input `F(X,Y)?` (VARCHECK "XY"), `a=LOWER X?` … `d=UPPER Y?` (ᴇ99 = ∞, |finite|<1ᴇ5,
    a<b and c<d). Str2 = F with X,Y → (ʟM2FX),(ʟM2FY), so one expr( evaluates F on point lists.
    RECOVER2 → E=1 (EXACT) when F is a polynomial on a finite box; ʟM2FA keeps the 5×5 table.
    CHECK F screen: F(a,c) MUST BE 0, F(b,d) MUST BE 1 (+ `CHECK F AND ITS SUPPORT`), f≥0 at a 3×3
    grid (numeric mixed difference), EXACT (POLYNOMIAL) / NUMERIC (NOT POLYNOMIAL).
  * CL (clipped corners): F̃=0 left of/below S, else F(min(x,b),min(y,d)); one `F(x,y)=v` row each.
  * RECTANGLE RULE / BOTH EXCEED / MIN/MAX screens start with the formula (`=F(b,d)-F(a,d)`,
    `P(X>a,Y>b)=1-FX(a)`, `FX(a)=F(a,2)`, `P(max≤t)=F(t,t)`, `ONLY IF BOTH = max≤t`,
    `FAILS IF EITHER FAILS`, `= min≤t =1-P(X>t,Y>t)`), then corner values, then the result.
  * MARGINAL CDFs: `FX(x)=F(x,d)` / `FY(y)=F(b,y)` with ends substituted, POLYSTR formula when
    exact, values at a typed x and y. PDF f FROM F: `f=d²F/dxdy`; exact → POLY2STR of
    a_ij=(i+1)(j+1)b_(i+1,j+1); else Richardson (4D(h/2)-D(h))/3, h=.01, point ≥.01 inside S.
  * F FROM A PDF f: recipe screen, then `97→Z:prgmM2JNT`; afterwards N=0 (F must be re-entered).
  * Pager PG copied from M2JNT (Str0 = "θTITLEθline…θ", wraps at 26 display columns).
* **M2PLY θ=4 POLY2STR** (the planned P3 interface): ʟM2QA n×n, n=ʟM2QS(3) → Str7.
* **M2JNT Z=97**: NEW MODEL, then straight to EVENTS > X≤s AND Y≤t (Lbl GQ sets L=0).
* STAM2 SOLVERS: DISCRETE TABLE, JOINT DENSITY, CDF OF X AND Y, DENSITY+INTEGRAL, MGF TOOLS, LINEAR
  COMBOS, BACK (7). HOW TO ENTER row `(JOINT DENSITY AND CDF)`. M2EXAM WRITTEN REASONING gains
  `JOINT CDF GIVEN` (F6) → recipe page → prgmM2CDF (27 routes).
* Encyclopedia (write_content.py, JOINT LAWS section, `pt()` helper for hand-laid pages): topic
  `JOINT CDF F` (F from f, f from F, rectangle rule, tails/min/max) replaces CDF CONVERSIONS;
  `SKETCH + LIMITS` (sketch/inner-outer, Guide Ex4.3 order + splitting, complement/infinite,
  words) replaces BOUNDS AND WORDS. Each page has a Freund Ch3 (or Guide) citation and a TOOL line.
* START_HERE: 15 programs, ~92 KB, SOLVERS row, `## Joint CDF` section, device check 14.

### M2CDF interface
* Z=0 normal; **Z=99**: Str1=F(X,Y), ʟM2FM={a,b,c,d} (±ᴇ99 = ±∞) preloaded, no prompts.
* Results: M = last probability (P(min≤t) for MIN/MAX, P(X>a,Y>b), rectangle P, numeric f(x,y));
  P = P(max≤t). E = exact flag, N = model loaded.
* Uses ʟM2F* (FM FA FC FD FX FY FZ FV FP FG FW), Str0, Str2, Str6–Str9; BACK deletes ʟM2F* and runs
  M2PLY/M2GL θ=9. Registers A–H, L–P local (G route, F return code of CL/FD/PG).

### Tests
* NEW tests/test_cdf.py (12): R3 polynomial (f, FX, FY, 25/256, 1/2, 1/16, 1/2), HW4 Q3 (1/8, FX(1)
  3/8, 3/8, 5/8, `1/4x+1/8x²`), HW4 Q5 (`1/2x+1/4y`, F(1/2,1)=1/8, FX, FY), Freund Ex16 with an ᴇ99
  corner (3/8, f=x+y), exponential pair (.546572343960, e^-3, 1-e^-3, f(1,1)≈2e^-3), a non-HW
  numeric f point + edge guard, F FROM A PDF f handoffs (1/8 for (X+Y)/8 and (2X+Y)/4), model
  cleared after handoff, finder route, R4 page checks, VARCHECK/UPPER BELOW LOWER/|bound| guards,
  Z=99, step budget. All expected values from sympy/Fraction in the test.
* Updated: test_menu_tree (SOLVERS shape, CANNED M2CDF prompts, M2CDF module, new route test),
  test_reference_navigation (walk + JOINT CDF title), test_exam_assistant (27 routes).
* Totals: 14 test files green (test_cdf 12, test_menu_tree 15 incl. the M2CDF/M2JNT handoff paths);
  build_package succeeded: 15 programs, 92,948 bytes (limit 118,000), 260 checks; both linters
  0 errors / 0 warnings. M2ENC 25,079 B tokenized, M2JNT 12,317 B.

## LEAN-B

**Status: done** (reduced P3, budget mode). §0A **A4 implemented** (F(s,t) through INDEP + CDF for
HW4 Q3's (X+Y)/8 and HW4 Q5's (2X+Y)/4, and the F FORMULA x²y/4+xy²/8). Not done (budget):
retiring M2SLICE / M2CONT DOUBLE INTEGRAL, PRODUCT MOMENT r,s, VAR(aX+bY+c), E[g(Y)] GIVEN.

### What was built
* **src/M2JAN.txt** (new, 11,848 B tokenized): analysis helper called by M2JNT with the item in H.
  * FORMULAS (polynomial q, straight-edged finite support; else "FORMULAS NEED A POLYNOMIAL…USE
    GIVEN A VALUE"): g(x)/h(y) per strip (definition line, Freund Def11 p93, `FOR a<x<b`,
    `y FROM l TO u`, formula, `0 ELSEWHERE`, `CHECK ∫g dx=1`); w(y|x)/f(x|y) (Def13 p96) and
    E(Y|X=x)/E(X|Y=y) (Ch4 Def10 p138) as `(N)/(D)` after cancelling common linear factors
    (candidates 0, ±1, piece ends, where the limits meet; synthetic division), normalised by D's
    lowest coefficient; `ONLY WHERE g(x)>0`.
  * MOMENTS + COV: MEANS VARS COV ρ (E X, E Y, E X², E Y², E XY, Var with formula, Cov with the
    numbers plugged in, ρ as fraction or ±√(p/q) + decimal) and E[g(X,Y)] (E g, E g², Var g).
    One M2GL 2-D pass (EXACT) or two (NUMERIC, §4.5 labels). A = Cov.
  * GIVEN A VALUE: GIVEN X=x / Y=y → marginal value with its integral and limits, "DENSITY, NOT A
    POINT PROB", conditional density formula with the value substituted (polynomial) and its
    support, E, E of the square, Var; slice menu P(a<Y<b | X=x) (clipped, ᴇ99 = ∞) / NEW VALUE.
    Outside the support: `CONDITIONAL UNDEFINED`. M2GL 1-D kernel, exact or 2 passes. A = last
    E(.|.) or conditional P.
  * INDEP + CDF: INDEPENDENCE TEST (non-product support → witness f(x*,y*)=0 BUT g h>0 from a
    3x3 grid; product + polynomial → rank-1 coefficient test with g, h or a worst-grid witness;
    numeric → grid with numeric marginals, NUMERIC EVIDENCE), F(s,t) AT A POINT (returns H=5;
    M2JNT runs EVENTS > X≤s AND Y≤t with pieces), F(x,y) FORMULA (rectangle + polynomial: interior
    6x6 antiderivative table via POLY2STR, F(x,d), F(b,y), 1 / 0 branches, Freund Def9 p86).
* **M2JNT** (12,516 B): top-menu items J1–J4 → route G=11..14 (also after NEW MODEL), F1 builds
  ʟM2JX/ʟM2JY with RG code C=7 (strips only, no integration; curved: one kind-1 strip, ʟM2JY={0}),
  calls prgmM2JAN, then GQ when H=5. BACK deletes ʟM2JX/ʟM2JY. "COMING IN THIS VERSION" removed.
* M2EXAM JOINT PDF routes GIVEN VALUE, MOMENT / COV, MARGINAL FORMULA now open M2JNT with texts
  naming GIVEN A VALUE / MOMENTS + COV / FORMULAS. write_presets.py: HW5 Q7 → `99→Z:prgmM2JNT` with
  q=X+Y, {1,0,1,0,1} (back to the HW5 Q5-Q8 menu). START_HERE: 16 programs, ~105 KB, JOINT DENSITY
  row, Joint densities items 7–10, HW5 Q7 practice-data note, JOINT SLICE pointer, device check 15.

### Tests
* NEW tests/test_joint_analysis.py (23, holds `# PLAN DEVIATIONS / EXTRA FIXES`): HW4 Q2 (c=1/4,
  h=`1/4+1/4y`, f(x|y)=`(2x+y)/(1+y)`, g, w), HW5 Q7 (h=`1/2+y`, E(X|Y=1/2)=7/12, Var=11/144),
  q=X on 0<y<x<1 (g=`3x²`, h=`3/2-3/2y²`, w, E(Y|X=x)=x/2, E(X|Y=y)), q=XY on 0<x<y<1 (c=8, g, h,
  `(2x)/(y²)`, E(Y|X=x) with cancelled factors), X+Y<k marginal, Freund Ex20 given + P(X<1/2|Y=1/2),
  Mock 4 Q3 P(X<1/2|Y=3/4)=4/9 + outside support, numeric x e^(-x(1+y)) given Y=1, X+Y moments
  (E X=7/12, Cov=-1/144, ρ=-1/11, E[XY], E[(XY)²]), √ form of ρ for q=X on the triangle, numeric
  2e^(-x-2y) (E X=1, E Y=1/2, Cov≈0, <120,000 steps), 4XY INDEPENDENT (g=2x, h=2y), X+Y DEPENDENT and
  triangle DEPENDENT witnesses checked against sympy, numeric independence evidence, A4 F(s,t) and
  F formulas (HW4 Q5, Freund Ex16 `1/2x²y+1/2xy²`, branches), refusals, step budgets (formula
  <6,000, given <2,500, exact moments <3,000), per-program caps (M2JNT ≤13,800, M2JAN ≤13,000,
  total ≤118,000). Formula strings are parsed back into sympy and compared symbolically.
* Updated: test_joint_events (stub test → four analysis menus), test_exam_assistant (conditional
  slice via GIVEN A VALUE; route text), test_presets (HW5 Q7 via M2JNT), test_menu_tree (CANNED
  M2JAN prompts, M2JAN module; ~100 s now).
* build_package succeeded: 16 programs, 104,983 bytes (limit 118,000), 283 checks; both linters
  0 errors / 0 warnings.
* Note: tests/test_exam_assistant.py was briefly reverted to HEAD by mistake and restored to the
  LEAN-A state (27 routes) plus the LEAN-B edits; no other LEAN-A file was touched.
