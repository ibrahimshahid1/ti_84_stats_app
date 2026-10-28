from fractions import Fraction as F
import sympy as s
x,y,t=s.symbols('x y t',real=True)
S=[(a,b) for a in range(3) for b in range(3) if a+b<=3]
w={(a,b):F(1+a+2*b) for a,b in S}; total=sum(w.values());p={k:v/total for k,v in w.items()}
cond=sum(v for (a,b),v in p.items() if a+b>=2);event=sum(v for (a,b),v in p.items() if a+b>=2 and b>a)
print('T1',total,event/cond,'EX-2Y',sum(F(a-2*b)*v for(a,b),v in p.items()))
q=3*y
I1=s.integrate(q,(y,0,x/2),(x,0,s.Rational(2,3)))
I2=s.integrate(q,(y,0,1-x),(x,s.Rational(2,3),1))
print('T2',I1,I2,I1+I2,'fX',s.integrate(q,(y,0,x/2)))
q=6*x
I1=s.integrate(q,(y,s.Rational(1,2),1),(x,0,s.Rational(1,2)))
I2=s.integrate(q,(y,x,1),(x,s.Rational(1,2),1))
J1=s.integrate(x*q,(y,s.Rational(1,2),1),(x,0,s.Rational(1,2)))
J2=s.integrate(x*q,(y,x,1),(x,s.Rational(1,2),1))
print('T3',I1,I2,J1,J2,(J1+J2)/(I1+I2))
CDF=(x*x*y+2*x*y*y)/3
rect=CDF.subs({x:s.Rational(3,4),y:s.Rational(2,3)})-CDF.subs({x:s.Rational(1,4),y:s.Rational(2,3)})-CDF.subs({x:s.Rational(3,4),y:s.Rational(1,3)})+CDF.subs({x:s.Rational(1,4),y:s.Rational(1,3)})
f=s.diff(CDF,x,y);fx=s.integrate(f,(y,0,1));fy=s.integrate(f,(x,0,1));print('T4',f,fx,fy,rect,s.factor(f-fx*fy))
Eg=s.integrate(x*x,(x,0,1))+s.integrate(2-x,(x,1,2));Eg2=s.integrate(x**3,(x,0,1))+s.integrate(2-x,(x,1,2));print('T5',Eg,Eg2,40*Eg-5,40**2*(Eg2-Eg**2))
M=(1-3*t)**(-2);mu=s.diff(M,t).subs(t,0);second=s.diff(M,t,2).subs(t,0);print('T6',mu,second,second-mu**2,'Z',2-mu/3,(second-mu**2)/9)
S=s.diag(4,9);B=s.Matrix([[3,2],[6,-1]]);means=s.Matrix([1,-1]);print('T7',B*means,B*S*B.T)
q=s.Rational(3,10)*(x*x+y*y);print('T9',s.integrate(q,(y,0,2),(x,0,1)),s.integrate(q,(y,0,s.Rational(3,2)),(x,0,1)))
q=s.Rational(1,3);print('T10',s.integrate(q,(y,x/3,x),(x,0,3)),s.integrate(q,(y,1,x),(x,1,3)))
print('T11',*[s.diff(s.exp(t**4),t,r).subs(t,0) for r in [1,2,4]])
print('T12',s.integrate(x/(2*s.sqrt(x)),(x,0,1)),s.integrate(x**2/(2*s.sqrt(x)),(x,0,1)))
assert total==29 and event/cond==F(11,23)
assert I1+I2==s.Rational(7,8)
assert rect==s.Rational(1,6)
# Exact model checks across computational cases.
assert sum(p.values())==1
assert s.integrate(3*y,(y,0,x/2),(x,0,2))==1
assert s.integrate(3*y,(y,0,x/2),(x,0,s.Rational(2,3)))+s.integrate(3*y,(y,0,1-x),(x,s.Rational(2,3),1))==s.Rational(1,18)
assert (J1+J2)/(I1+I2)==s.Rational(15,28)
assert Eg==s.Rational(5,6) and Eg2==s.Rational(3,4)
assert 40*Eg-5==s.Rational(85,3) and 1600*(Eg2-Eg**2)==s.Rational(800,9)
assert second-mu**2==18
assert (B*S*B.T)==s.Matrix([[72,54],[54,153]])
assert s.integrate(s.Rational(3,10)*(x*x+y*y),(y,0,s.Rational(3,2)),(x,0,1))==s.Rational(39,80)
assert s.integrate(s.Rational(1,3),(y,1,x),(x,1,3))==s.Rational(2,3)
# Token-stream checks of selected general workflows (no preset routes).
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'midterm2_app/tools'))
from tisim import Sim
m=lambda n:{'menu':n}
e=lambda v:{'input':str(v)}
def run(name,actions,expected):
 r=Sim(str(ROOT/'midterm2_app/src')).run(name,actions,max_steps=500000)
 assert r.error is None,r.error
 assert not r.leaks and not r.warnings,(r.leaks,r.warnings)
 for k,v in expected.items():assert abs(float(r.var(k))-float(v))<1e-6,(name,k,r.var(k),v)
 return r
run('M2DISC',[m(3),e('{0,1,2}'),e('{0,1,2}'),e('(1+X+2Y)*(X+Y≤3)'),m(3),m(2),e('Y>X'),e('X+Y≥2'),m(3),m(7)],{'W':s.Rational(11,23)})
run('M2CONT',[m(1),e('1-abs(X-1)'),e(0),e(0),e(2),m(3),e('40*min(X,1)-5'),m(7)],{'E':s.Rational(85,3),'G':s.Rational(800,9)})
run('M2CONT',[m(2),e('3Y'),e(0),e(0),e('2/3'),e(0),e('X/2'),e(1),e(4),m(4)],{'F':s.Rational(1,27)})
run('M2SLICE',[m(1),e('6X'),e(1),e('1/2'),e(0),e('Y'),m(6)],{'E':s.Rational(1,3)})
run('M2CONT',[m(1),e(1),e(0),e(0),e(1),m(3),e('X²'),m(7)],{'E':s.Rational(1,3),'G':s.Rational(4,45)})
print('PASS exact checks and five token-stream general-solver workflows.')
