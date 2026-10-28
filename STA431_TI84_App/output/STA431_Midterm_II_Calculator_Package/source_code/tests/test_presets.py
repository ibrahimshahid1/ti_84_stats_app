#!/usr/bin/env python3
"""Run all sixteen homework presets through the actual loader and solver menus."""
from pathlib import Path
import math,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from tisim import Sim
from tilint import lint_file
import tibuild

def m(n):return {'menu':n}
def entered(v):
 s=str(v)
 if isinstance(v,(int,float)) and v<0:s='⁻'+s[1:]
 return {'input':s}
INIT={'Y1':'X²+1','Y9':'X+3','L₁':[91,92],'L₂':[71,72]}
class Presets(unittest.TestCase):
 def run_case(self,group,question,solver,expected=None,required=()):
  back={1:6,2:5,3:5,4:4}[group]
  actions=[m(group),m(question)]+solver+[m(back),m(5)]
  r=Sim(str(ROOT/'src')).run('M2RUN',actions,max_steps=7000000,init_vars=INIT)
  self.assertIsNone(r.error,r.text)
  self.assertIn(r.ended_reason,('end','return'),r.text)
  self.assertEqual(r.leaks,0,r.text)
  self.assertFalse(r.warnings,r.warnings)
  for key,v in INIT.items():self.assertEqual(r.var(key),v,key)
  self.assertEqual(r.var('Z'),0,'preset routing flag not cleared')
  self.assertFalse(any(k.startswith('M2') for k in r.vars['lists']),r.vars['lists'])
  for key,target in (expected or {}).items():
   self.assertTrue(math.isclose(float(r.var(key)),target,rel_tol=1e-7,abs_tol=1e-7),key+'\n'+r.text)
  for needle in required:self.assertIn(needle,r.text)
  return r
 def test_hw4_q1_joint_table_conditional_and_independence(self):
  self.run_case(1,1,[m(2),m(6),m(3),entered(2),m(5),m(7),m(7)],
                required=['1/37','17/37','20/37','5/11','6/11','NUMERIC FACTORIZATION FAIL'])
 def test_hw4_q2_joint_normalization(self):
  self.run_case(1,2,[entered(4),m(1),m(4)],{'F':4},['1/4'])
 def test_hw4_q3_survival_region(self):
  self.run_case(1,3,[entered(4),m(4)],{'F':3/8},['FAILURE IS 1-RAW I','3/8'])
 def test_hw4_q4_both_discrete_events(self):
  self.run_case(1,4,[m(3),m(1),entered('X>Y'),m(1),entered('X+Y≤3'),m(3),m(7)],
                {'W':1/4},['3/32','1/4'])
 def test_hw4_q5_variable_bound_probability(self):
  self.run_case(1,5,[entered(4),m(4)],{'F':19/24},['19/24'])
 def test_hw5_q1_pmf_moments(self):
  self.run_case(2,1,[m(1),m(7)],{'E':13/4,'G':227/20,'B':63/80},['1/40','63/80'])
 def test_hw5_q2_symmetric_density_and_transformed_square(self):
  self.run_case(2,2,[m(1),m(3),entered('X²'),m(7)],{'E':1/5,'F':3/35,'G':8/175},['1/5','8/175'])
 def test_hw5_q3_exponential_mgf(self):
  self.run_case(2,3,[m(3)],required=['1/3','2/9','1/9','DOMAIN t<3'])
 def test_hw5_q4_affine_mgf(self):
  self.run_case(2,4,[m(3)],required=['ORIGINAL X MOMENTS','Z=aX+b MOMENTS','H=1/2','DOMAIN ALL REAL t'])
 def test_hw5_q5_claim_variance(self):
  self.run_case(3,1,[m(3)],required=['2465','MEAN NOT PROVIDED'])
 def test_hw5_q6_three_variable_variance(self):
  self.run_case(3,2,[m(3)],required=['56','MEAN NOT PROVIDED'])
 def test_hw5_q7_conditional_moments(self):
  self.run_case(3,3,[m(1),m(7)],{'E':7/12,'F':5/12,'G':11/144},['7/12','11/144'])
 def test_hw5_q8_joint_moments_and_conditional(self):
  self.run_case(3,4,[m(1),m(2),m(4),entered(1),m(7),m(7)],
                {'E':20/9,'G':50/9,'B':50/81},['13/6','14/3','⁻1/36','20/9'])
 def test_631_hw4_q4_triangular_density(self):
  self.run_case(4,1,[entered(4),m(4)],{'F':1},['RAW I=INT q APPROX='])
 def test_631_hw4_q5_reimbursement(self):
  self.run_case(4,2,[m(2),entered(8),entered(12),m(7)],{'W':2/3},['2/3'])
 def test_631_hw5_q8_zero_covariance_reasoning_inputs(self):
  self.run_case(4,3,[m(1),m(4),m(1),entered(3),m(3),m(2),entered('⁻1/2'),entered('1/2'),m(7)],
                {'W':3/4},['1/6','3/4'])
 def test_loader_token_and_structural_lints(self):
  p=ROOT/'src'/'M2RUN.txt'
  self.assertEqual(lint_file(str(p)),[])
  self.assertEqual(tibuild.lint_program('M2RUN',tibuild.clean_source(p.read_text())),[])
if __name__=='__main__':unittest.main(verbosity=2)
