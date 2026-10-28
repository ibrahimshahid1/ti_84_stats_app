#!/usr/bin/env python3
# PLAN DEVIATIONS / EXTRA FIXES (P1)
# * M2CONT gate row reads "NOT CONVERGED - RAISE N" (the plan wrote "NOT CONVERGED: RAISE N"): a colon
#   inside a string is a lint WARN (SPEC policy), and the DoD needs 0 warnings.
# * (superseded in fix round 1, see below) M2MGF Richardson flag compared Richardson vs h=.005.
# * STAM2 HOW TO ENTER: "ON ERR CHOOSE 1 QUIT" (no colons), "FRACTIONS 1/2 = DIVIDE KEY" (the ÷ glyph
#   has no string token), LEFT on page 1 also returns to the HELP menu (content.py pager behaviour).
#   STAM2 tokenizes to ~1.9 KB (budget 2,000).
# * tisim snapshots gained a "stack" field (prgm call chain), used by test_menu_tree to key menus.
# * test_cov_mgf "negative values" case now types 1-10000X² (1+200X fails the new M(.001) check first).
# * Encyclopedia/HW map text that named the old launcher items (GENERAL SOLVERS, DISCRETE + JOINT,
#   EXAM ASSISTANT, PRACTICE + HW) now names the P1 items (SOLVERS, DISCRETE TABLE, HELP > FIND MY
#   SOLVER, HOMEWORK PRACTICE). Preset intro text advises N=8 (START_HERE: "use 8; raise it until
#   CHANGE is 0").
# * build_package also fails on linter WARN lines (DoD item 4), not only on non-zero exit codes.
# * tests/test_transfer_general.py and tests/test_cov_mgf.py were also migrated to text menu choices
#   (the plan listed only the other test files), so no test hard-codes a BACK position.
# * tisim text menu choice raises SIM:ACTION on an ambiguous exact or prefix match (not only on none).
# * QUIT no longer prints "MIDTERM II DONE": STAM2 ends with ClrHome and "" (blank screen, no Done).
# * Before the first P1 build, the two hand-made files of the v1 package (HOMEWORK_WALKTHROUGH.pdf,
#   PREVIEW.png; old menus + STA 631 extras) were moved to ../output/_superseded_v1/package_v1_extras/
#   instead of being deleted by the from-scratch package rebuild.
# FIX ROUND 1 (verifier issues; all also in PROGRESS.md "## P1"):
# * Finite bounds (PLAN 4.4 |v|<1E5): M2CONT 1D bounds, DOUBLE INTEGRAL x bounds and the evaluated y
#   limits at every node, and M2SLICE given value/bounds re-prompt with "BOUNDS MUST BE FINITE" /
#   "FINITE VALUES ONLY" + a cutoff hint instead of overflowing or returning an exact-looking 0.
#   DOUBLE INTEGRAL "UPPER MUST EXCEED LOWER" now re-asks the bounds (Lbl J2), not the whole model.
# * M2CONT gate row is Str0: "NOT CONVERGED - RAISE N", "N=100 IS MAX - USE DECIMAL" (at the cap), or
#   "CHANGE<1ᴇ⁻6 - USE DECIMAL" (both changes below 1E-6 relative; a quartic+ outer integrand never
#   meets 1E-9). Extra row "I=0 - CHECK q AND BOUNDS". DOUBLE INTEGRAL menu gains "NEW N" (Goto J1);
#   the N prompt gets ClrHome + a header.
# * M2MGF TYPE MGF NUMERIC: D1/D2 at h=.01,.005,.0025; reports (16R(.005)-R(.01))/15 (the plan said
#   R(.01,.005); this is the next Richardson level, error O(h^6), shown as clean 6/48/12 for
#   (1-2t)^-3). The warning now tests that value's estimated error |R(.005)-final| > 1E-6*|final| +
#   1E-8 (the old test measured the error of the unreported h=.005 value). Check screen
#   "NUMERIC STEP CHECK" shows the h=.005 and Richardson values; texts "RELATIVE ERROR EST <1ᴇ⁻6" /
#   "WARNING STEP-SIZE CHANGE" + "TRY M(X/10), SCALE 10a". ʟM2MV has 7 cells, ʟM2MD 11.
# * M(.001) guard kept (it also keeps h=.01 off a pole: a mean-free test would let 1/(1-100t) reach
#   M(.01)=1/0); message "M(.001) IS NOT NEAR 1" ... "(M(0) MUST BE 1)" ... "TYPE M(X/10), SCALE 10a".
# * EVAL Mz AT t: ClrHome + header before the prompt; Mx(0)=1 is used when G=3 and |a*t|<1E-12.
# * STAM2 HOW TO ENTER page 1: header "KEYS     ENTER=NEXT    1/2", "X=X,T,θ,n(FUNC) Y=ALPHA 1",
#   "⁻3 = (-) KEY  1/2 = DIVIDE", "(NOT IN DENSITY+INTEGRAL)" under the ᴇ99 row, "CLEAR OR LEFT=HELP
#   MENU". LIMITS row "Finite rows ≤30; combos≤3" (the plan's build-fix text) became "TABLE ROWS ≤30"
#   and "LINEAR COMBOS ≤3 VARIABLES" (uppercase, unambiguous).
# * Preset intro: "START WITH EVEN N=8" / "RAISE N IF NOT CONVERGED" (was "USE EVEN N=8 OR MORE").
# * test_menu_tree types canned inputs (CANNED table) so menus behind inputs are explored; asserts
#   every Menu( line is reached, INIT unchanged on every run and no ʟM2* list once back in STAM2.
# * START_HERE device checks use Freund/mock/made-up data, no homework answers.
"""P1 repository-wide checks (PLAN.md section 5): both linters on every program with zero errors and
zero warnings, the STA 431-only scan (Appendix F), the program list, prgm references, and the memory
budget (section 3.1).
"""
from pathlib import Path
import re
import unittest

from m2test import ROOT, SRC
import tibuild
import tilint
import build_package

SCAN_PATTERNS = ['631', 'OPTIONAL 6', 'REIMBURS', '24X*(1-X-Y)', '(20-X)', '1-abs(X)', 'abs(X)<1/2']
PRGM = b'\x5f'


def scan_files():
    files = sorted(SRC.glob('*.txt')) + sorted((ROOT / 'content').glob('*.json'))
    files += sorted((ROOT / 'tools').glob('write_*.py')) + [ROOT / 'START_HERE.md']
    files += [p for p in sorted((ROOT / 'tests').glob('*.py')) if p.name != Path(__file__).name]
    return files


def prgm_refs(name, text):
    toks = tibuild.token_list(tibuild.clean_source(text))
    refs = set()
    for j, t in enumerate(toks):
        if t.bits == PRGM:
            s = ''
            for u in toks[j + 1:]:
                c = tilint.NAMECH.get(u.bits)
                if c is None:
                    break
                s += c
            refs.add(s)
    return refs


class LintAll(unittest.TestCase):
    def test_tibuild_lint_every_program_clean(self):
        for path in sorted(SRC.glob('*.txt')):
            with self.subTest(program=path.stem):
                name, text, lmap = tibuild.read_program(str(path), with_map=True)
                self.assertEqual(tibuild.lint_program(name, text, lmap), [])

    def test_tilint_every_program_clean(self):
        for path in sorted(SRC.glob('*.txt')):
            with self.subTest(program=path.stem):
                self.assertEqual(tilint.lint_file(str(path)), [])

    def test_tilint_configured_for_midterm2(self):
        self.assertEqual(tilint.FORMATTER, 'M2FMT')
        self.assertEqual(tilint.MAIN_PROGRAM, 'STAM2')
        warn = tilint.lint_source('TX', '1→W\nprgmM2FMT\nDisp Q\nReturn')
        self.assertTrue(any('reads Q after prgmM2FMT' in w for w in warn), warn)

    def test_tibuild_reports_original_line_numbers(self):
        text = '// comment\n\nDisp "A<=B"\nReturn\n'
        msgs = tibuild.lint_program('TX', tibuild.clean_source(text), tibuild.line_map_of(text))
        self.assertTrue(msgs and msgs[0].startswith('ERROR TX:3:'), msgs)

    def test_no_sta631_material_anywhere(self):
        hits = []
        for path in scan_files():
            low = path.read_text(encoding='utf-8').lower()
            for pat in SCAN_PATTERNS:
                if pat.lower() in low:
                    hits.append(f'{path.relative_to(ROOT)}: {pat}')
        self.assertEqual(hits, [])

    def test_program_list_matches_src(self):
        stems = sorted(p.stem for p in SRC.glob('*.txt'))
        order = build_package.program_order()
        self.assertEqual(order[0], 'STAM2')
        self.assertEqual(sorted(order), stems)
        self.assertEqual(order[1:], sorted(order[1:]))
        for s in stems:
            self.assertRegex(s, r'^[A-Z][A-Z0-9]{0,7}$')
        # generated content programs exist for every content JSON
        import json
        for doc in (ROOT / 'content').glob('*.json'):
            self.assertIn(json.loads(doc.read_text())['program'], stems)
        # START_HERE names every program that the student must transfer
        start = (ROOT / 'START_HERE.md').read_text()
        for s in stems:
            self.assertRegex(start, r'\b' + s + r'\b', f'START_HERE does not mention {s}')
        self.assertIn(f'{len(stems)} programs', start)

    def test_every_prgm_reference_exists(self):
        stems = {p.stem for p in SRC.glob('*.txt')}
        for path in sorted(SRC.glob('*.txt')):
            refs = prgm_refs(path.stem, path.read_text(encoding='utf-8'))
            with self.subTest(program=path.stem):
                self.assertEqual(sorted(refs - stems), [])
                self.assertNotIn(path.stem, refs, 'a program must not call itself')

    def test_no_midterm1_names_reused(self):
        mid1 = {'STA431', 'STAE1', 'STAE2', 'STAE3', 'STAHNT', 'STACNT', 'STAPRB', 'STARV', 'STAFMT'}
        self.assertFalse(mid1 & {p.stem for p in SRC.glob('*.txt')})

    def test_memory_budget(self):
        est = build_package.memory_estimate()
        sizes = build_package.tokenized_sizes()
        print(f'\nmemory estimate {est} bytes (limit {build_package.BUDGET_BYTES}); tokenized: {sizes}')
        self.assertLessEqual(est, build_package.BUDGET_BYTES)

    def test_menu_limits_in_source(self):
        # 7 options, title <= 22, option <= 18: tilint enforces; double-check none slipped past.
        for path in sorted(SRC.glob('*.txt')):
            for line in path.read_text(encoding='utf-8').splitlines():
                if line.startswith('Menu('):
                    texts = re.findall(r'"([^"]*)"', line)
                    self.assertLessEqual(len(texts) - 1, 7, line)
                    self.assertLessEqual(len(texts[0]), 22, line)
                    for t in texts[1:]:
                        self.assertLessEqual(len(t), 18, line)


if __name__ == '__main__':
    unittest.main(verbosity=2)
