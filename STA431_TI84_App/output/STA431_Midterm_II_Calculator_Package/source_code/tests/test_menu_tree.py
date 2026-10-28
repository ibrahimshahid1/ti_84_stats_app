#!/usr/bin/env python3
"""Depth-first exploration of every Menu( choice reachable from STAM2 (PLAN.md section 5).

Each path is replayed from a fresh start. At a menu not yet explored with the same prgm call chain,
every item is tried. At an Input prompt the explorer types a canned, valid value from CANNED (fix
round 1: so menus behind inputs, such as the DOUBLE INTEGRAL menu, SLICE OPTIONS and MGF NEXT, are
explored too); a prompt with no canned value is a leaf. A getKey site (a pager) is passed once with
CLEAR. Every run must have no error, no leaked block frames, no display warnings and the user's
INIT variables unchanged; whenever control is back in STAM2 alone (and at QUIT) no ʟM2* list may be
left. Every Menu( line in src must be reached. Also holds the P1 STAM2 route tests (main-menu shape,
HELP > FIND MY SOLVER > BACK, QUIT, HOW TO ENTER keys).
"""
import re
import unittest

from m2test import INIT, SRC, m, i, k, run
from tisim import Sim

MAX_RUNS = 6000
MAX_INPUT_RUN = 30          # more inputs in a row than this (no menu between) = re-prompt loop

# (program, prompt) -> values typed on the 1st, 2nd, ... visit within one path (cycled).
CANNED = {
    ('M2CONT', 'q(X)?'): ['2X'], ('M2CONT', 'FIXED A?'): ['0'],
    ('M2CONT', 'LOWER X?'): ['0'], ('M2CONT', 'UPPER X?'): ['1'],
    ('M2CONT', 'EVENT LOWER?'): ['0'], ('M2CONT', 'EVENT UPPER?'): ['1/2'],
    ('M2CONT', 'g(X)?'): ['X²'], ('M2CONT', 'POWER 0-10?'): ['2'],
    ('M2CONT', 'q(X,Y)?'): ['X+Y'], ('M2CONT', 'LOWER Y(X)?'): ['0'], ('M2CONT', 'UPPER Y(X)?'): ['X'],
    ('M2CONT', 'g(X,Y),1=AREA?'): ['X*Y'], ('M2CONT', 'EVEN N 4-100?'): ['4'],
    ('M2SLICE', 'q(X,Y)?'): ['X+Y'], ('M2SLICE', 'KNOWN c>0?'): ['1'], ('M2SLICE', 'GIVEN VALUE?'): ['1/2'],
    ('M2SLICE', 'LOWER BOUND?'): ['0'], ('M2SLICE', 'UPPER BOUND?'): ['1'],
    ('M2SLICE', 'REMAINING VALUE?'): ['1/2'], ('M2SLICE', 'EVENT LOWER?'): ['0'],
    ('M2SLICE', 'EVENT UPPER?'): ['1/2'],
    ('M2MGF', 'RATE L>0?'): ['2'], ('M2MGF', 'C?'): ['1'], ('M2MGF', 'D≥0?'): ['1'],
    ('M2MGF', 'M(X)?'): ['(𝑒^(2X)-1)/(2X)'], ('M2MGF', 'SCALE a?'): ['1'], ('M2MGF', 'SHIFT b?'): ['0'],
    ('M2MGF', 'EVAL t?'): ['0'],          # the uniform MGF at t=0 used to divide by zero
    ('M2COV', 'n (1-3)?'): ['2'], ('M2COV', 'MEAN?'): ['1'], ('M2COV', 'VARIANCE?'): ['2'],
    ('M2COV', 'COVARIANCE?'): ['1'], ('M2COV', 'a FOR U?'): ['1'], ('M2COV', 'b FOR V?'): ['1'],
    ('M2COV', 'OFFSET c FOR U?'): ['0'], ('M2COV', 'OFFSET d FOR V?'): ['0'],
    ('M2DISC', 'ROWS 1-30?'): ['2'], ('M2DISC', 'x VALUE?'): ['0', '1'], ('M2DISC', 'y VALUE?'): ['0', '1'],
    ('M2DISC', 'RAW WEIGHT?'): ['1', '2'], ('M2DISC', 'x VALUES LIST?'): ['{0,1}'],
    ('M2DISC', 'y VALUES LIST?'): ['{0,1}'], ('M2DISC', 'q(X,Y)?'): ['X+Y+1'],
    ('M2DISC', 'GIVEN Y=?'): ['1'], ('M2DISC', 'GIVEN X=?'): ['1'], ('M2DISC', 'EVENT X,Y?'): ['X<Y'],
    ('M2DISC', 'GIVEN X,Y?'): ['X≥0'], ('M2DISC', 'g(X,Y)?'): ['X*Y'],
    ('M2DISC', 'r POWER 0-10?'): ['1'], ('M2DISC', 's POWER 0-10?'): ['1'],
    # P2 JOINT DENSITY: a polynomial model, so every event is EXACT (the curved support is numeric)
    ('M2JNT', 'q(X,Y)?'): ['X+Y'], ('M2JNT', 'a=LOWER X?'): ['0'], ('M2JNT', 'b=UPPER X?'): ['1'],
    ('M2JNT', 'c=LOWER Y?'): ['0'], ('M2JNT', 'd=UPPER Y?'): ['1'], ('M2JNT', 'a=LOWER END?'): ['0'],
    ('M2JNT', 'b=UPPER END?'): ['1'], ('M2JNT', 'k=SUM BOUND?'): ['1'], ('M2JNT', 'LOWER END?'): ['0'],
    ('M2JNT', 'UPPER END?'): ['1'], ('M2JNT', 'LOWER BOUND?'): ['0'], ('M2JNT', 'UPPER BOUND?'): ['1'],
    ('M2JNT', 'k?'): ['1/2'], ('M2JNT', 't?'): ['1/2'], ('M2JNT', 'a?'): ['1/4'], ('M2JNT', 'b?'): ['3/4'],
    ('M2JNT', 'c?'): ['1'], ('M2JNT', 'd?'): ['1'], ('M2JNT', 's?'): ['1/2'],
}


def menu_sites():
    """(program, line) of every Menu( statement in src (comments skipped)."""
    sites = set()
    for path in sorted(SRC.glob('*.txt')):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if not line.lstrip().startswith('//') and re.search(r'(^|:)Menu\(', line.strip()):
                sites.add((path.stem, n))
    return sites


def explore():
    sim = Sim(str(SRC))
    seen, todo = set(), [[]]
    stats = {'runs': 0, 'menus': 0, 'leaves': 0, 'ends': 0, 'inputs': 0, 'keys': 0, 'home_checks': 0}
    problems, programs_with_menus, menu_keys, uncanned = [], set(), set(), set()
    while todo:
        acts = todo.pop()
        stats['runs'] += 1
        if stats['runs'] > MAX_RUNS:
            problems.append('too many runs: explorer did not terminate')
            break
        r = sim.run('STAM2', acts, max_steps=3_000_000, init_vars=INIT)
        path = ' > '.join(str(a.get('menu', a.get('input', a.get('key')))) for a in acts)
        if r.error or r.leaks or r.warnings:
            problems.append(f'{path}: error={r.error} leaks={r.leaks} warnings={r.warnings}')
            continue
        changed = [key for key, value in INIT.items() if r.var(key) != value]
        if changed:
            problems.append(f'{path}: user variables changed {changed}')
        last = r.screens[-1]
        home = r.ended_reason in ('end', 'return') or last.get('stack') == ['STAM2']
        if home:                                   # every module has returned: its lists are gone
            stats['home_checks'] += 1
            left = sorted(n for n in r.vars['lists'] if n.startswith('M2'))
            if left:
                problems.append(f'{path}: private lists left in STAM2: {left}')
        if r.ended_reason in ('end', 'return'):
            stats['ends'] += 1
            continue
        if r.ended_reason != 'out_of_actions':
            problems.append(f'{path}: ended {r.ended_reason}')
            continue
        site = (tuple(last.get('stack', [])), last['program'], last['line'])
        if last['event'] == 'input':
            values = CANNED.get((last['program'], last['prompt']))
            if values is None:
                uncanned.add((last['program'], last['prompt']))
                stats['leaves'] += 1
                continue
            since = len(acts) - max([j + 1 for j, a in enumerate(acts) if 'menu' in a] or [0])
            if since >= MAX_INPUT_RUN:
                problems.append(f'{path}: {since} inputs in a row (re-prompt loop with canned data?)')
                continue
            visits = sum(1 for s in r.screens[:-1] if s['event'] == 'input' and s['program'] == last['program']
                         and s.get('prompt') == last['prompt'])
            stats['inputs'] += 1
            todo.append(acts + [i(values[visits % len(values)])])
            continue
        if last['event'] == 'getkey':
            if ('key',) + site in seen:
                stats['leaves'] += 1
                continue
            seen.add(('key',) + site)
            stats['keys'] += 1
            todo.append(acts + [k(45)])            # CLEAR leaves every pager
            continue
        if last['event'] != 'menu':
            stats['leaves'] += 1
            continue
        # A menu reached through typed data is keyed by the menu choice that started that data entry
        # too, so e.g. MGF NEXT is explored after EXPONENTIAL RATE and after TYPE MGF NUMERIC.
        menus_done = [s for s in r.screens[:-1] if s['event'] == 'menu']
        j = max([n for n, a in enumerate(acts) if 'menu' in a] or [-1])
        if menus_done and any('input' in a for a in acts[j + 1:]):
            prev = menus_done[-1]
            site += ((prev['program'], prev['line'], prev['menu']['items'][acts[j]['menu'] - 1]),)
        if site in seen:
            continue
        seen.add(site)
        stats['menus'] += 1
        programs_with_menus.add(last['program'])
        menu_keys.add((last['program'], last['line']))
        for n in range(len(last['menu']['items']), 0, -1):
            todo.append(acts + [m(n)])
    return stats, problems, programs_with_menus, menu_keys, uncanned


class MenuTree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stats, cls.problems, cls.programs, cls.menus, cls.uncanned = explore()
        st = cls.stats
        print(f"\nmenu tree: {st['runs']} runs, {st['menus']} distinct menus (by call chain), "
              f"{st['inputs']} canned inputs, {st['keys']} pager exits, {st['leaves']} leaves, "
              f"{st['ends']} clean ends, {st['home_checks']} list checks in STAM2")

    def test_every_path_has_no_error_or_leak(self):
        self.assertEqual(self.problems, [])

    def test_every_menu_site_reached(self):
        # fix round 1: canned inputs carry the explorer past data entry, so no Menu( line is skipped
        self.assertEqual(sorted(menu_sites() - self.menus), [])
        self.assertGreater(self.stats['inputs'], 100)
        self.assertGreater(self.stats['home_checks'], 10)

    def test_every_prompt_has_canned_data(self):
        # A new Input prompt needs a CANNED value, or the menus behind it are never explored.
        self.assertEqual(sorted(self.uncanned), [])

    def test_explorer_reached_every_module(self):
        for prog in ['STAM2', 'M2ENC', 'M2HW', 'M2RUN', 'M2EXAM', 'M2DISC', 'M2CONT', 'M2SLICE',
                     'M2MGF', 'M2COV', 'M2JNT']:
            self.assertIn(prog, self.programs)
        self.assertGreater(self.stats['menus'], 50)
        self.assertGreater(self.stats['ends'], 0)        # QUIT reached

    def test_main_menu_shape(self):
        r = run('STAM2', [m('QUIT')])
        menu = r.screens[0]['menu']
        self.assertEqual(menu['title'], 'STA431 MIDTERM II')
        self.assertEqual(menu['items'], ['ENCYCLOPEDIA', 'SOLVERS', 'HELP', 'HOMEWORK PRACTICE', 'QUIT'])
        subs = {}
        for item in ['SOLVERS', 'HELP', 'HOMEWORK PRACTICE']:
            rr = run('STAM2', [m(item), m('BACK'), m('QUIT')])
            subs[item] = rr.screens[1]['menu']['items']
        self.assertEqual(subs['SOLVERS'], ['DISCRETE TABLE', 'JOINT DENSITY', 'DENSITY+INTEGRAL', 'MGF TOOLS',
                                           'LINEAR COMBOS', 'BACK'])
        self.assertEqual(subs['HELP'], ['FIND MY SOLVER', 'HOW TO ENTER', 'LIMITS + CAVEATS', 'BACK'])
        self.assertEqual(subs['HOMEWORK PRACTICE'], ['WALKTHROUGHS', 'LOAD PRACTICE DATA', 'BACK'])

    def test_mode_lines_first(self):
        lines = [ln.strip() for ln in (SRC / 'STAM2.txt').read_text().splitlines()
                 if ln.strip() and not ln.strip().startswith('//')]
        self.assertEqual(lines[:4], ['Float', 'Normal', 'Real', '0→Z'])
        self.assertEqual(lines[-2:], ['ClrHome', '""'])

    def test_route_help_find_my_solver_back(self):
        r = run('STAM2', [m('HELP'), m('FIND MY SOLVER'), m('BACK'), m('BACK'), m('QUIT')], init={'Z': 5})
        titles = [s['menu']['title'] for s in r.screens if s['event'] == 'menu']
        self.assertEqual(titles, ['STA431 MIDTERM II', 'HELP', 'EXAM GIVEN DATA', 'HELP', 'STA431 MIDTERM II'])
        exam = next(s for s in r.screens if s['event'] == 'menu' and s['menu']['title'] == 'EXAM GIVEN DATA')
        self.assertEqual(exam['stack'], ['STAM2', 'M2EXAM'])
        self.assertEqual(r.var('Z'), 0)

    def test_route_quit_ends_cleanly(self):
        r = run('STAM2', [m('QUIT')])
        self.assertEqual(r.ended_reason, 'end')
        end = r.screens[-1]
        self.assertEqual(end['event'], 'end')
        self.assertTrue(all(not row.strip() for row in end['rows']), end['rows'])   # no "Done"

    def test_route_solvers_joint_density_back(self):
        # P2: SOLVERS > JOINT DENSITY > BACK returns to SOLVERS with every private list deleted
        r = run('STAM2', [m('SOLVERS'), m('JOINT DENSITY'), m('BACK'), m('BACK'), m('QUIT')], init={'Z': 7})
        titles = [s['menu']['title'] for s in r.screens if s['event'] == 'menu']
        self.assertEqual(titles, ['STA431 MIDTERM II', 'SOLVERS', 'JOINT DENSITY', 'SOLVERS', 'STA431 MIDTERM II'])
        jnt = next(s for s in r.screens if s['event'] == 'menu' and s['menu']['title'] == 'JOINT DENSITY')
        self.assertEqual(jnt['stack'], ['STAM2', 'M2JNT'])

    def test_route_solvers_back_quit(self):
        r = run('STAM2', [m('SOLVERS'), m('BACK'), m('QUIT')])
        self.assertEqual([s['menu']['title'] for s in r.screens if s['event'] == 'menu'],
                         ['STA431 MIDTERM II', 'SOLVERS', 'STA431 MIDTERM II'])

    def test_help_pager_keys(self):
        r = run('STAM2', [m('HELP'), m('HOW TO ENTER'), k(105), k(24), k(105), k(105), m('BACK'), m('QUIT')])
        heads = [s['rows'][0].strip() for s in r.screens if s['event'] == 'getkey']
        self.assertEqual(heads, ['KEYS     ENTER=NEXT    1/2', 'NOTATION (FREUND)      2/2',
                                 'KEYS     ENTER=NEXT    1/2', 'NOTATION (FREUND)      2/2'])
        pages = [s for s in r.screens if s['event'] == 'getkey']
        page1, page2 = '\n'.join(pages[0]['rows']), '\n'.join(pages[1]['rows'])
        for needle in ['X,T,θ,n(FUNC)', 'ALPHA 1', '2ND MATH TEST', '𝑒^(', '√(', '(-) KEY', 'DIVIDE',
                       '{ }', 'ᴇ99', '(JOINT DENSITY ONLY)', 'ON ERR CHOOSE 1 QUIT',
                       'CLEAR OR LEFT=HELP MENU']:
            self.assertIn(needle, page1)
        self.assertIn('ENTER=MENU  LEFT=PAGE 1', page2)
        for needle in ['g(x)', 'h(y)', 'f(x|y)', 'w(y|x)', "μ'r", 'μr', 'σXY', 'ρ']:
            self.assertIn(needle, page2)

    def test_help_pager_page1_clear_and_left_go_back(self):
        # fix round 1: CLEAR and LEFT on page 1 are both routes back to the HELP menu
        for key in (45, 24):
            with self.subTest(key=key):
                r = run('STAM2', [m('HELP'), m('HOW TO ENTER'), k(key), m('BACK'), m('QUIT')])
                titles = [s['menu']['title'] for s in r.screens if s['event'] == 'menu']
                self.assertEqual(titles, ['STA431 MIDTERM II', 'HELP', 'HELP', 'STA431 MIDTERM II'])
                self.assertEqual([s['rows'][0].strip() for s in r.screens if s['event'] == 'getkey'],
                                 ['KEYS     ENTER=NEXT    1/2'])

    def test_limits_page_rows(self):
        r = run('STAM2', [m('HELP'), m('LIMITS + CAVEATS'), m('BACK'), m('QUIT')])
        rows = [row.strip() for s in r.screens if s['event'] == 'pause' for row in s['rows']]
        for needle in ['TABLE ROWS ≤30', 'LINEAR COMBOS ≤3 VARIABLES', 'DENSITY+INTEGRAL FINITE']:
            self.assertIn(needle, rows)

    def test_practice_notice_before_presets(self):
        r = run('STAM2', [m('HOMEWORK PRACTICE'), m('LOAD PRACTICE DATA'), m('BACK'), m('BACK'), m('QUIT')])
        i_notice = next(j for j, s in enumerate(r.screens) if 'PRACTICE EXAMPLES ONLY' in '\n'.join(s['rows']))
        i_menu = next(j for j, s in enumerate(r.screens)
                      if s['event'] == 'menu' and s['menu']['title'] == 'HOMEWORK QUICK SOLVE')
        self.assertLess(i_notice, i_menu)


if __name__ == '__main__':
    unittest.main(verbosity=2)
