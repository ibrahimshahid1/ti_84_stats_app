#!/usr/bin/env python3
"""End-user workflow checks for tables, a usable dependence witness, and quick loading."""
from pathlib import Path
from fractions import Fraction
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from tisim import Sim

def m(n):return {'menu':n}
def i(v):
 s=str(v)
 if isinstance(v,(int,float)) and v<0:s='⁻'+s[1:]
 return {'input':s}
def grid(x,y,q):return [m(3),i(x),i(y),i(q)]
INIT={'Y1':'X²+1','Y9':'X+3','L₁':[91,92],'L₂':[71,72]}
def number(s):return float(Fraction(s.replace('⁻','-')))
class Workflows(unittest.TestCase):
 def run_program(self,p,actions):
  r=Sim(str(ROOT/'src')).run(p,actions,max_steps=1000000,init_vars=INIT)
  self.assertIsNone(r.error,r.text);self.assertEqual(r.leaks,0,r.text)
  self.assertFalse(r.warnings,r.warnings);self.assertIn(r.ended_reason,('end','return'),r.text)
  for k,v in INIT.items():self.assertEqual(r.var(k),v,k)
  self.assertFalse(any(k.startswith('M2') for k in r.vars['lists']),r.vars['lists'])
  return r
 def pause(self,r,title):
  return next(s for s in r.screens if s['event']=='pause' and s['rows'][0].strip()==title)
 def test_hw4_q1_full_marginal_tables(self):
  r=self.run_program('M2DISC',grid('{1,2}','{1,2,3}','X+Y²')+[m(2),m(6),m(7),m(7)])
  x='\n'.join(self.pause(r,'X MARGINAL TABLE')['rows'])
  y='\n'.join(self.pause(r,'Y MARGINAL TABLE')['rows'])
  for row in ['1 | 17/37','2 | 20/37']:self.assertIn(row,x)
  for row in ['1 | 5/37','2 | 11/37','3 | 21/37']:self.assertIn(row,y)
 def test_marginals_aggregate_unsorted_repeated_coordinates(self):
  actions=[m(2),i(4)]
  for row in [(2,2,4),(1,1,1),(2,1,2),(1,2,3)]:actions.extend(i(v) for v in row)
  r=self.run_program('M2DISC',actions+[m(2),m(6),m(7),m(7)])
  x=self.pause(r,'X MARGINAL TABLE')['rows'];y=self.pause(r,'Y MARGINAL TABLE')['rows']
  for row in ['2 | 3/5','1 | 2/5']:self.assertEqual(sum(row in s for s in x),1)
  for row in ['2 | 7/10','1 | 3/10']:self.assertEqual(sum(row in s for s in y),1)
 def test_univariate_grid_suppresses_dummy_y_pages(self):
  r=self.run_program('M2DISC',grid('{1,2,3,4}','{0}','X²+X')+[m(1),m(2),m(6),m(7),m(7)])
  self.assertIn('13/4',r.text);self.assertIn('63/80',r.text)
  self.assertNotIn('Y MOMENTS',r.text);self.assertNotIn('Y MARGINAL TABLE',r.text)
  self.assertNotIn('E[XY]',r.text)
 def test_dependence_witness_is_a_valid_exact_counterexample(self):
  r=self.run_program('M2DISC',grid('{1,2}','{1,2,3}','X+Y²')+[m(2),m(5),m(7),m(7)])
  rows=[s.strip() for s in self.pause(r,'COUNTEREXAMPLE PAIR')['rows']]
  x,y=number(rows[1]),number(rows[2]);joint=number(rows[4]);product=number(rows[6])
  true_joint=(x+y*y)/37
  true_product=((3*x+14)/37)*((3+2*y*y)/37)
  self.assertAlmostEqual(joint,true_joint,delta=1e-9)
  self.assertAlmostEqual(product,true_product,delta=1e-9)
  self.assertGreater(abs(joint-product),1e-6)
  self.assertIn('NUMERIC FACTORIZATION FAIL',r.text)
 def test_independence_match_has_no_false_witness(self):
  r=self.run_program('M2DISC',grid('{0,1}','{0,1}','1')+[m(2),m(5),m(7),m(7)])
  self.assertIn('NUMERIC MATCH TO 1E-9',r.text)
  self.assertNotIn('COUNTEREXAMPLE PAIR',r.text)
 def test_main_launcher_quicksolve_and_return(self):
  r=self.run_program('STAM2',[m(x) for x in [4,2,3,2,3,5,5,3,6]])
  rows=[s.strip() for s in self.pause(r,'COMBINATION U')['rows']]
  self.assertEqual(number(rows[rows.index('VAR(U)')+1]),56)
  self.assertFalse(any(s['event']=='input' for s in r.screens),'quick load requested redundant numeric input')
  self.assertIn('MIDTERM II DONE',r.text)
 def test_quicksolve_removes_eleven_manual_covariance_inputs(self):
  actions=[m(1),m(1)]+[i(x) for x in [3,4,9,2,1,-1,0,3,-2,1,0]]+[m(3)]
  manual=self.run_program('M2COV',actions)
  quick=self.run_program('M2RUN',[m(3),m(2),m(3),m(5),m(5)])
  self.assertEqual(sum(s['event']=='input' for s in manual.screens),11)
  self.assertEqual(sum(s['event']=='input' for s in quick.screens),0)
  for r in [manual,quick]:
   rows=[s.strip() for s in self.pause(r,'COMBINATION U')['rows']]
   self.assertEqual(number(rows[rows.index('VAR(U)')+1]),56)
 def test_main_launcher_joint_slice_and_return(self):
  actions=[m(2),m(2),m(3),m(1)]+[i(x) for x in ['X+Y',1,'1/2',0,1]]+[m(6),m(4),m(5),m(6)]
  r=self.run_program('STAM2',actions)
  rows=[s.strip() for s in self.pause(r,'NUMERIC JOINT SLICE')['rows']]
  self.assertEqual(number(rows[rows.index('CONDITIONAL MEAN')+1]),7/12)
  self.assertEqual(number(rows[rows.index('CONDITIONAL VARIANCE')+1]),11/144)
if __name__=='__main__':unittest.main(verbosity=2)
