#!/usr/bin/env python3
"""Numerical joint-slice tests against independent homework calculations."""
from pathlib import Path
import sys, unittest, math
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
def data(direction,q,c,a,lo,hi):return [m(direction)]+[entered(x) for x in [q,c,a,lo,hi]]
INIT={'Y1':'X²+1','Y9':'X+3','L₁':[91,92],'L₂':[71,72]}
class Slice(unittest.TestCase):
 def run_slice(self,actions,program='M2SLICE'):
  r=Sim(str(ROOT/'src')).run(program,actions,max_steps=300000,init_vars=INIT)
  self.assertIsNone(r.error,r.text)
  self.assertIn(r.ended_reason,('end','return'),r.text)
  self.assertEqual(r.leaks,0,r.text)
  self.assertFalse(r.warnings,r.warnings)
  for key,v in INIT.items():self.assertEqual(r.var(key),v,key)
  return r
 def values(self,r,**expected):
  for k,v in expected.items():self.assertAlmostEqual(float(r.var(k)),v,delta=1e-7,msg=k+'\n'+r.text)
 def test_hw4_q2_marginal_and_conditional_moments(self):
  r=self.run_slice(data(1,'2X+Y','1/4','1/2',0,1)+[m(6)])
  self.values(r,M=3/8,E=11/18,F=4/9,H=23/324)
  for t in ['3/8','11/18','23/324']:self.assertIn(t,r.text)
 def test_hw4_q2_conditional_density_at_point(self):
  r=self.run_slice(data(1,'2X+Y','1/4','1/2',0,1)+[m(1),entered('1/2'),m(6)])
  self.values(r,O=1,P=3/8)
 def test_hw4_q2_reverse_marginal(self):
  r=self.run_slice(data(2,'2X+Y','1/4','1/2',0,2)+[m(6)])
  self.values(r,M=1,E=7/6,F=5/3,H=11/36)
 def test_hw5_q7_conditional_moments(self):
  r=self.run_slice(data(1,'X+Y',1,'1/2',0,1)+[m(6)])
  self.values(r,M=1,E=7/12,F=5/12,H=11/144)
 def test_hw5_q7_conditional_interval(self):
  r=self.run_slice(data(1,'X+Y',1,'1/2',0,1)+[m(2),entered('1/2'),entered(1),m(6)])
  self.values(r,O=5/8)
 def test_reimbursement_marginal_conditional_probability(self):
  r=self.run_slice(data(2,'(20-X)/(25X)',1,12,'X/2','X')+[m(2),entered(8),entered(12),m(6)])
  self.values(r,M=4/25,E=9,F=84,H=3,O=2/3)
  self.assertIn('2/3',r.text)
 def test_reimbursement_density_at_point(self):
  r=self.run_slice(data(2,'(20-X)/(25X)',1,12,'X/2','X')+[m(1),entered(8),m(6)])
  self.values(r,O=1/6,P=2/75)
 def test_triangle_given_y_moving_bound(self):
  r=self.run_slice(data(1,'24X*(1-X-Y)',1,'1/4',0,'1-Y')+[m(6)])
  self.values(r,M=27/16,E=3/8,F=27/160,H=9/320)
 def test_triangle_given_x_moving_bound(self):
  r=self.run_slice(data(2,'24X*(1-X-Y)',1,'1/4',0,'1-X')+[m(6)])
  self.values(r,M=27/16,E=1/4,F=3/32,H=1/32)
 def test_clipped_interval(self):
  r=self.run_slice(data(1,'X+Y',1,'1/2',0,1)+[m(2),entered(-1),entered('1/2'),m(6)])
  self.values(r,O=3/8)
 def test_empty_interval(self):
  r=self.run_slice(data(1,'X+Y',1,'1/2',0,1)+[m(2),entered(2),entered(3),m(6)])
  self.values(r,O=0)
 def test_pdf_outside_support_zero(self):
  r=self.run_slice(data(1,'X+Y',1,'1/2',0,1)+[m(1),entered(2),m(6)])
  self.values(r,O=0,P=0)
 def test_new_given_value_recomputes_marginal(self):
  r=self.run_slice(data(1,'X+Y',1,'1/2',0,1)+[m(4),entered('1/4'),entered(0),entered(1),m(6)])
  self.values(r,M=3/4,E=11/18,F=4/9,H=23/324)
 def test_zero_marginal_undefined(self):
  r=self.run_slice(data(1,'X*Y',1,0,0,1)+[m(3)])
  self.assertIn('CONDITION DENSITY IS ZERO',r.text)
 def test_negative_slice_rejected(self):
  r=self.run_slice(data(1,'⁻X',1,'1/2',0,1)+[m(3)])
  self.assertIn('NEGATIVE SAMPLED DENSITY',r.text)
 def test_invalid_multiplier_reentry(self):
  r=self.run_slice([m(1),entered('1'),entered(0),entered('1'),entered(1),entered(0),entered(0),entered(1),m(6)])
  self.assertIn('KNOWN c MUST BE POSITIVE',r.text)
  self.values(r,M=1,E=1/2,H=1/12)
 def test_invalid_bounds_reentry(self):
  r=self.run_slice(data(1,'1',1,0,1,0)+[entered(0),entered(0),entered(1),m(6)])
  self.assertIn('UPPER MUST EXCEED LOWER',r.text)
  self.values(r,M=1,E=1/2,H=1/12)
 def test_parent_menu_entry_and_back(self):
  self.run_slice([m(3),m(3),m(4)],program='M2CONT')
 def test_token_and_static_lints(self):
  p=ROOT/'src'/'M2SLICE.txt'
  self.assertEqual(lint_file(str(p)),[])
  self.assertEqual(tibuild.lint_program('M2SLICE',tibuild.clean_source(p.read_text())),[])
if __name__=='__main__':unittest.main(verbosity=2)
