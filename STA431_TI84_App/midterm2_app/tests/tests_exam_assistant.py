#!/usr/bin/env python3
"""General recognition/router tests, including unseen inputs and preset isolation."""
from pathlib import Path
from fractions import Fraction
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from tisim import Sim
from tilint import lint_file
import tibuild

def m(n):return {'menu':n}
def i(v):
 s=str(v)
 if isinstance(v,(int,float)) and v<0:s='⁻'+s[1:]
 return {'input':s}
INIT={'Y1':'X²+1','Y9':'X+3','L₁':[91,92],'L₂':[71,72],'Z':13}
class ExamAssistant(unittest.TestCase):
 def run_assistant(self,actions,init=None):
  initial=dict(INIT);initial.update(init or {})
  r=Sim(str(ROOT/'src')).run('M2EXAM',actions,max_steps=500000,init_vars=initial)
  self.assertIsNone(r.error,r.text);self.assertEqual(r.leaks,0,r.text)
  self.assertFalse(r.warnings,r.warnings);self.assertIn(r.ended_reason,('end','return'),r.text)
  for k,v in INIT.items():
   if k!='Z':self.assertEqual(r.var(k),v,k)
  self.assertEqual(float(r.var('Z')),0)
  self.assertFalse(any(k.startswith('M2') for k in r.vars['lists']),r.vars['lists'])
  return r
 def test_all_twenty_six_guidance_routes_return(self):
  # category, topic count, helper menu Back, category Back
  paths={1:(5,{1:4,2:4,3:4,4:4,5:4},6),
         2:(6,{1:4,2:3,3:4,4:4,5:7,6:7},7),
         3:(4,{1:4,2:4,3:4,4:7},5),
         4:(3,{1:4,2:4,3:7},4),
         5:(3,{1:3,2:3,3:7},4),
         6:(5,{1:7,2:7,3:7,4:7,5:7},6)}
  count=0
  for category,(n,helperback,back) in paths.items():
   for target in range(1,n+1):
    with self.subTest(category=category,target=target):
     r=self.run_assistant([m(category),m(target),m(helperback[target]),m(back),m(7)])
     self.assertTrue(any(s['event']=='pause' for s in r.screens))
     count+=1
  self.assertEqual(count,26)
 def test_changed_finite_model_and_event(self):
  # New support/weights/event, not a homework fixture or preset.
  a=[m(1),m(1),m(3),i('{0,2}'),i('{1,3}'),i('1+X*Y'),m(3),m(1),i('X+Y>3'),m(3),m(7),m(6),m(7)]
  r=self.run_assistant(a,{'Z':1})
  self.assertIn('RAW TOTAL=',r.text)
  self.assertAlmostEqual(float(r.var('W')),7/12,delta=1e-8)
  self.assertNotIn('HW4',r.text);self.assertNotIn('HW5',r.text)
  prompts=[s.get('prompt','') for s in r.screens if s['event']=='input']
  self.assertTrue(prompts,'The general solver must request new data')
 def test_changed_continuous_conditional_slice(self):
  # Uniform triangle 0<Y<X<3, given X=2; Y|X=2 uniform(0,2).
  a=[m(2),m(2),m(2),i('1'),i('2/9'),i(2),i(0),i('X'),m(6),m(7),m(7)]
  r=self.run_assistant(a,{'Z':17})
  self.assertIn('NUMERIC JOINT SLICE',r.text)
  self.assertAlmostEqual(float(r.var('M')),4/9,delta=1e-8)
  self.assertAlmostEqual(float(r.var('E')),1,delta=1e-8)
  self.assertAlmostEqual(float(r.var('H')),1/3,delta=1e-8)
  self.assertNotIn('HW5',r.text)
 def test_probability_setup_preserves_event_normalization_distinction(self):
  r=self.run_assistant([m(2),m(1),m(4),m(7),m(7)])
  self.assertIn('Full support c=1/RAW I.',r.text)
  self.assertIn('probability is RAW I.',r.text)
 def test_symbolic_route_explains_numeric_limit(self):
  r=self.run_assistant([m(2),m(5),m(7),m(7),m(7)])
  self.assertIn('a marginal formula.',r.text)
  self.assertIn('Give all support branches.',r.text)
 def test_event_conditioning_uses_two_region_integrals(self):
  # New triangle 0<Y<X<3. Given X>1, find P(Y<1/2): ratio 1/4.
  # A point slice at X=1 would give 1/2, so it is a different model.
  a=[m(2),m(3),m(2)]+[i(x) for x in ['1',0,1,3,0,'X','1',4]]
  a+=[m(2)]+[i(x) for x in ['1',0,1,3,0,'1/2','1',4]]+[m(4),m(7),m(7)]
  r=self.run_assistant(a,{'Z':17})
  self.assertIn('Given Y>k is an EVENT.',r.text)
  self.assertIn('Its scale cancels.',r.text)
  raw=[]
  for s in r.screens:
   if s['event']=='pause':
    rows=s.get('rows',[])
    for j,row in enumerate(rows):
     if 'RAW I=INT q APPROX=' in row:raw.append(float(Fraction(rows[j+1].strip())))
  self.assertEqual(len(raw),4,r.text)  # Each run reports base and refined N.
  for actual,expected in zip(raw,[4,4,1,1]):
   self.assertAlmostEqual(actual,expected,delta=1e-8)
  self.assertAlmostEqual(raw[3]/raw[1],1/4,delta=1e-8)
 def test_cdf_route_teaches_rectangle_and_density_conversion(self):
  r=self.run_assistant([m(6),m(1),m(7),m(6),m(7)])
  self.assertIn('+F(b,d)-F(a,d)-F(b,c)',r.text)
  self.assertIn('+F(a,c), for (a,b]x(c,d].',r.text)
  self.assertIn('Differentiate twice for',r.text)
 def test_preset_flags_do_not_bypass_user_inputs(self):
  for flag in [1,2,11,13,14,15,16,17,18,21,22,23]:
   with self.subTest(flag=flag):
    r=self.run_assistant([m(1),m(1),m(4),m(6),m(7)],{'Z':flag})
    self.assertNotIn('NORMALIZED p=w/SUM(w)',r.text)
    self.assertNotIn('ORIGINAL X MOMENTS',r.text)
 def test_static_and_token_roundtrip(self):
  p=ROOT/'src/M2EXAM.txt';s=tibuild.clean_source(p.read_text())
  self.assertEqual(lint_file(str(p)),[])
  self.assertEqual(tibuild.lint_program('M2EXAM',s),[])
  self.assertTrue(tibuild.tokenize(s))
  self.assertNotIn('prgmM2RUN',s)
  self.assertNotIn('prgmM2HW',s)
if __name__=='__main__':unittest.main(verbosity=2)
