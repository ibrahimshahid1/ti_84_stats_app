"""Independent symbolic checks for the original STA431 practice bank.

Run with SymPy installed. In the authoring environment it is available under
/tmp/sta431_mathdeps. This file does not generate or change deliverables.
"""
from pathlib import Path
import sys
sys.path.insert(0, '/tmp/sta431_mathdeps')
import sympy as s

x, y, t = s.symbols('x y t', real=True)
Q = s.Rational
checks = []

def check(label, actual, expected):
    assert s.simplify(actual - expected) == 0, (label, actual, expected)
    checks.append(label)

def triangle(g):
    return s.integrate(s.integrate(2*g, (y, 0, x)), (x, 0, 1))

# A: normalization, marginals, and event limits.
check('A1 normalizer', sum(a+2*b for a in (1,2) for b in (0,1,2)), 21)
check('A2 normalizer', s.integrate(s.integrate(x+2*y,(x,0,2)),(y,0,1)), 4)
check('A3 event', s.integrate(s.integrate(2,(y,0,x/2)),(x,0,1)), Q(1,2))
check('A4 normalizer', s.integrate(s.integrate((x+y)/27,(x,0,3)),(y,0,3)),1)
check('A4 event', 1-s.integrate(s.integrate((x+y)/27,(x,1,3)),(y,1,3)),Q(11,27))
check('A5 event', sum(Q(a+b,21) for a in (1,2) for b in (1,2,3) if a+b<=4),Q(16,21))
check('A6 event', s.integrate(s.integrate(Q(2,3)*(2*x+y),(x,0,y)),(y,0,1)),Q(4,9))
check('A7 normalizer',s.integrate(s.integrate(x,(x,0,1)),(y,0,2)),1)
check('A7 event',s.integrate(s.integrate(x,(x,Q(1,2),1)),(y,Q(1,2),Q(3,2))),Q(3,8))
check('A10 normalizer',s.integrate(s.integrate(Q(3,2),(y,x*x,1)),(x,0,1)),1)
check('A10 event',s.integrate(s.integrate(Q(3,2),(x,0,s.sqrt(y))),(y,0,Q(1,4))),Q(1,8))

# B: discrete and transformed expectations.
check('B1 normalizer',sum(a*a+1 for a in range(4)),18)
check('B1 expectation',sum(Q(a*(a*a+1),18) for a in range(4)),Q(7,3))
check('B2 inverse',s.integrate(3*x,(x,0,1)),Q(3,2))
check('B3 absolute',2*s.integrate(x*(1-x),(x,0,1)),Q(1,3))
check('B3 second',2*s.integrate(x*x*(1-x),(x,0,1)),Q(1,6))
probs = [(0,Q(1,4)),(1,Q(1,2)),(2,Q(1,4))]
ey = sum(a*a*p for a,p in probs)
check('B4 expectation',ey,Q(3,2))
check('B4 variance',sum(a**4*p for a,p in probs)-ey**2,Q(9,4))
check('B5 square',s.integrate((1-x)**2*2*x,(x,0,1)),Q(1,6))
check('B5 logarithm',s.integrate(s.log(x)*2*x,(x,0,1)),-Q(1,2))
check('B6 profit',100-20*(Q(3,10)+3*Q(1,5)),82)
check('B7 direct',Q(5+2+24+16,10),Q(47,10))
check('B9 inverse',s.integrate(x**-3,(x,1,s.oo)),Q(1,2))
check('B10 indicator',s.integrate(2*x,(x,Q(1,2),1)),Q(3,4))
check('B10 truncated',s.integrate(2*x*x,(x,Q(1,2),1)),Q(7,12))

# C: distinguish raw from central powers and transformed moments.
moments = [sum(Q(a**(r+1),6) for a in (1,2,3)) for r in (1,2,3)]
check('C1 first',moments[0],Q(7,3))
check('C1 second',moments[1],6)
check('C1 third',moments[2],Q(49,3))
check('C1 central third',sum(Q(a,6)*(a-Q(7,3))**3 for a in (1,2,3)),-Q(7,27))
check('C2 variance',s.integrate(4*x**3*(x-Q(4,5))**2,(x,0,1)),Q(2,75))
check('C2 central third',s.integrate(4*x**3*(x-Q(4,5))**3,(x,0,1)),-Q(4,875))
check('C3 central fourth',107-4*2*26+6*4*7-3*16,19)
check('C5 variance',s.integrate((x*x-Q(4,3))**2/4,(x,-2,2)),Q(64,45))
check('C7 mean',s.integrate(2*x**-2,(x,1,s.oo)),2)
assert s.integrate(2/x,(x,1,s.oo)) is s.oo
check('C8 fourth',sum(Q(a**4,5) for a in (-2,-1,0,1,2)),Q(34,5))
check('C10 variance of square',s.integrate(Q(3,2)*x*x*(x*x-Q(3,5))**2,(x,-1,1)),Q(12,175))

# D: MGF derivatives, transformations, and domain interior values.
for label,m,mean,var in [
    ('D1',5/(5-t),Q(1,5),Q(1,25)),
    ('D2',s.exp(-t)/4+Q(1,2)+s.exp(2*t)/4,Q(1,4),Q(19,16)),
    ('D3',s.exp(t*t/2),0,1),
    ('D4',(1-2*t)**-3,6,12),
    ('D6',4/((1-t)*(4-t)),Q(5,4),Q(17,16)),
    ('D8',s.exp(3*t)/(1+2*t),1,4),
    ('D9',s.exp(2*t-t*t),2,-2),
]:
    m1=s.diff(m,t).subs(t,0)
    m2=s.diff(m,t,2).subs(t,0)
    check(label+' mean',m1,mean)
    check(label+' variance',m2-m1*m1,var)
check('D5 MGF mean',s.limit(s.diff((s.exp(2*t)-1)/(2*t),t),t,0),1)
check('D5 MGF second',s.limit(s.diff((s.exp(2*t)-1)/(2*t),t,2),t,0),Q(4,3))

# E: products, correlation, and moment consistency.
table=[(0,0,Q(2,10)),(0,1,Q(3,10)),(1,0,Q(1,10)),(1,1,Q(4,10))]
ex=sum(a*p for a,b,p in table); ey=sum(b*p for a,b,p in table)
cov=sum(a*b*p for a,b,p in table)-ex*ey
check('E1 covariance',cov,Q(1,20))
check('E1 correlation',cov/s.sqrt(ex*(1-ex)*ey*(1-ey)),1/s.sqrt(21))
check('E2 product',s.integrate(s.integrate(x*y*4*x*y,(x,0,1)),(y,0,1)),Q(4,9))
check('E3 mean X',triangle(x),Q(2,3))
check('E3 mean Y',triangle(y),Q(1,3))
check('E3 product',triangle(x*y),Q(1,4))
check('E3 covariance',triangle(x*y)-triangle(x)*triangle(y),Q(1,36))
check('E3 variance X',triangle(x*x)-triangle(x)**2,Q(1,18))
check('E3 variance Y',triangle(y*y)-triangle(y)**2,Q(1,18))

# F: covariance matrix multiplication is independent of hand expansion.
S=s.Matrix([[1,Q(1,2),-1],[Q(1,2),4,1],[-1,1,9]])
assert all(S[:k,:k].det()>0 for k in (1,2,3))
a=s.Matrix([2,-1,3])
check('F3 variance',(a.T*S*a)[0],69)
S2=s.Matrix([[2,-1],[-1,5]])
a=s.Matrix([1,2]); b=s.Matrix([3,-1])
check('F4 variance U',(a.T*S2*a)[0],18)
check('F4 variance V',(b.T*S2*b)[0],29)
check('F4 covariance',(a.T*S2*b)[0],-9)
check('F6 variance',s.integrate((2*x+x*x-Q(1,3))**2/2,(x,-1,1)),Q(64,45))
check('F9 variance',Q(2,5)**2*25+Q(3,5)**2*16+2*Q(2,5)*Q(3,5)*10,Q(364,25))
a=s.Matrix([1,1,0]); b=s.Matrix([0,1,-1])
check('F10 variance U',(a.T*S*a)[0],6)
check('F10 variance V',(b.T*S*b)[0],11)
check('F10 covariance',(a.T*S*b)[0],Q(9,2))

# G: normalization and exact conditional central-moment integrals.
check('G1 normalizer',sum(a+b for a in (1,2) for b in (0,1,2)),15)
check('G1 variance',sum(Q(1+b,6)*(b-Q(4,3))**2 for b in (0,1,2)),Q(5,9))
conditional=(2*x+Q(1,2))/Q(3,2)
check('G2 mean',s.integrate(x*conditional,(x,0,1)),Q(11,18))
check('G2 variance',s.integrate((x-Q(11,18))**2*conditional,(x,0,1)),Q(23,324))
check('G3 variance at point',Q(4,5)**2/12,Q(4,75))
check('G5 total variance',Q(1,2)-Q(1,3)+Q(1,12),Q(1,4))
check('G6 tower',s.integrate((1+y)/2*2*(1-y),(y,0,1)),Q(2,3))
check('G7 variance',Q(4,3)/12+Q(1,3)/4,Q(7,36))
check('G8 normalization',s.integrate(s.integrate(3,(y,0,x*x)),(x,0,1)),1)
check('G9 event conditional',s.integrate(s.integrate(2*y,(y,0,x)),(x,Q(1,2),1))/Q(3,4),Q(7,18))
check('G10 variance',3*Q(3,2)+4*Q(1,4),Q(11,2))

# Ensure exactly ten top-level items in each question and solution subsection.
for fn in ('practice_questions.tex','practice_solutions.tex'):
    content=Path(__file__).with_name(fn).read_text()
    blocks=content.split('\\begin{enumerate}')[1:]
    assert len(blocks)==7, (fn,len(blocks))
    for idx,block in enumerate(blocks):
        count=block.split('\\end{enumerate}')[0].count('\\item ')
        assert count==10, (fn,idx,count)
print(f'{len(checks)} symbolic checks passed; 70 questions and 70 matching solution items confirmed.')
