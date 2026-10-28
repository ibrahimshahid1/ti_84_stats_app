#!/usr/bin/env python3
"""Verify every generated topic is reachable and its pages fit the CE text screen, and walk the
launcher (P2: SOLVERS has JOINT DENSITY) through every submenu and module menu (menus chosen by item text)."""
import json

from m2test import ROOT, m, k, run

checks = 0
for name in ['M2ENC', 'M2HW']:
    doc = json.loads((ROOT / 'content' / f'{name}.json').read_text())
    for sec in doc['sections']:
        for topic in sec['topics']:
            actions = [m(sec['menu']), m(topic['menu'])] + [k(105) for _ in topic['pages']] + [m('BACK'), m('BACK')]
            r = run(name, actions, max_steps=200_000)
            assert topic['title'] in r.text, (name, topic['menu'], 'unreachable')
            checks += 1

# Launch/back from every launcher submenu and module menu, the HELP pager keys, and QUIT.
walk = [m('ENCYCLOPEDIA'), m('BACK'),
        m('SOLVERS'),
        m('DISCRETE TABLE'), m('BACK'),
        m('JOINT DENSITY'), m('BACK'),
        m('CDF OF X AND Y'), m('BACK'),
        m('DENSITY+INTEGRAL'), m('BACK'),
        m('MGF TOOLS'), m('BACK'),
        m('LINEAR COMBOS'), m('BACK'),
        m('BACK'),
        m('HELP'),
        m('FIND MY SOLVER'), m('BACK'),
        m('HOW TO ENTER'), k(105), k(24), k(45),          # next page, LEFT back to page 1, CLEAR
        m('HOW TO ENTER'), k(105), k(105),                # both pages, ENTER returns to HELP
        m('LIMITS + CAVEATS'),
        m('BACK'),
        m('HOMEWORK PRACTICE'),
        m('WALKTHROUGHS'), m('BACK'),
        m('LOAD PRACTICE DATA'), m('BACK'),
        m('BACK'),
        m('QUIT')]
r = run('STAM2', walk, max_steps=300_000, init={'Y1': 'X²', 'Y9': 'X+1'})
assert r.var('Y1') == 'X²' and r.var('Y9') == 'X+1', 'graph changed'
titles = [s['menu']['title'] for s in r.screens if s['event'] == 'menu']
for t in ['STA431 MIDTERM II', 'SOLVERS', 'HELP', 'HOMEWORK PRACTICE', 'MIDTERM II REFERENCE',
          'DISCRETE TABLE', 'JOINT DENSITY', 'JOINT CDF', 'CONTINUOUS TOOLS', 'MOMENT GENERATING FN', 'LINEAR COMBINATIONS',
          'EXAM GIVEN DATA', 'HOMEWORK 4 AND 5', 'HOMEWORK QUICK SOLVE']:
    assert t in titles, ('menu never shown', t)
pages = [s['rows'][0].strip() for s in r.screens if s['event'] == 'getkey']
assert pages.count('KEYS     ENTER=NEXT    1/2') == 3 and pages.count('NOTATION (FREUND)      2/2') == 2, pages
assert r.screens[-1]['event'] == 'end' and not any(x.strip() for x in r.screens[-1]['rows'])
checks += 1
print(f'PASS {checks} reference/menu navigation checks; all topic pages reachable and fit.')
