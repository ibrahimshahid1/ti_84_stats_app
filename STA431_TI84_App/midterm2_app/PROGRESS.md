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
