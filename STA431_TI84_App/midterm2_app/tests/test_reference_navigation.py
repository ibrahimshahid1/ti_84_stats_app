#!/usr/bin/env python3
"""Verify every generated topic is reachable and its pages fit CE's text screen."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from tisim import Sim
checks=0
for name in ['M2ENC','M2HW']:
 doc=json.loads((ROOT/'content'/f'{name}.json').read_text())
 for si,sec in enumerate(doc['sections'],1):
  for ti,topic in enumerate(sec['topics'],1):
   actions=[{'menu':si},{'menu':ti}]+[{'key':105} for _ in topic['pages']]+[{'menu':len(sec['topics'])+1},{'menu':len(doc['sections'])+1}]
   r=Sim(str(ROOT/'src')).run(name,actions,max_steps=200000)
   assert r.error is None,(name,topic['menu'],r.error)
   assert not r.leaks,(name,topic['menu'],r.leaks)
   assert not r.warnings,(name,topic['menu'],r.warnings)
   assert r.ended_reason in ['end','return'],(name,topic['menu'],r.ended_reason)
   assert topic['title'] in r.text,(name,topic['menu'],'unreachable')
   checks+=1
# Test launch/back from each module menu, all reference modules, and launcher exit.
actions=[{'menu':x} for x in [2,1,4,2,4,3,4,4,3,5,3,7,4,1,5,2,5,3,5,6]]
r=Sim(str(ROOT/'src')).run('STAM2',actions,max_steps=300000,init_vars={'Y1':'X²','Y9':'X+1'})
assert r.error is None,r.error
assert not r.leaks,r.leaks
assert not r.warnings,r.warnings
assert r.ended_reason in ['end','return'],r.ended_reason
assert r.var('Y1')=='X²' and r.var('Y9')=='X+1','graph changed'
checks+=1
print(f'PASS {checks} reference/menu navigation checks; all topic pages reachable and fit.')
