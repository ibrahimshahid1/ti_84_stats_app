from pathlib import Path
import sys,json,math
sys.path.insert(0,'midterm2_app/tools')
from tisim import Sim
M=lambda n:{'menu':n}
I=lambda v:{'input':str(v)}
def grid(xs,ys,q):return [M(3),I(xs),I(ys),I(q)]
def one(q,a,lo,hi):return [M(1),I(q),I(a),I(lo),I(hi)]
def two(q,xl,xu,yl,yu,g='1',n=4):return [M(2),I(q),I(0),I(xl),I(xu),I(yl),I(yu),I(g),I(n)]
cases=[
('HW4 Q1 all marginal and conditional requests','M2DISC',grid('{1,2}','{1,2,3}','X+Y²')+[M(2),M(1),I(1),M(1),I(2),M(2),I(1),M(2),I(2),M(2),I(3),M(3),I(2),M(5),M(7),M(7)],['1/37','17/37','20/37','5/37','11/37','21/37','5/11','6/11','FACTORIZATION FAIL']),
('HW4 Q2 normalization','M2CONT',two('2X+Y',0,1,0,2)+[M(1),M(4)],['1/4']),
('HW4 Q2 numerical marginal at y1','M2CONT',one('(2X+A)/4',1,0,1)+[M(2),I(0),I('.5'),M(7)],['3/8']),
('HW4 Q3 survivor region','M2CONT',two('(X+Y)/8',1,2,1,2)+[M(4)],['3/8']),
('HW4 Q4 both events','M2DISC',grid('{1,2}','{1,2,3,4}','X+Y')+[M(3),M(1),I('X>Y'),M(1),I('X+Y≤3'),M(3),M(7)],['3/32','1/4']),
('HW4 Q5 event region','M2CONT',two('(2X+Y)/4',0,1,'X',2)+[M(4)],['19/24']),
('HW4 631Q4 normalization triangle','M2CONT',two('24X*(1-X-Y)',0,1,0,'1-X')+[M(4)],['RAW I=INT q APPROX=']),
('HW4 631Q4 fX at .5','M2CONT',one('24A*(1-A-X)','.5',0,'.5')+[M(7)],['1.5']),
('HW4 631Q4 fY at .5','M2CONT',one('24X*(1-X-A)','.5',0,'.5')+[M(7)],['.5']),
('HW4 631Q5 reimbursement','M2CONT',one('1',0,6,12)+[M(2),I(8),I(12),M(7)],['2/3']),
]
cases += [
('HW4 Q2 joint-slice marginal/pdf/interval','M2SLICE',[M(1),I('2X+Y'),I('1/4'),I(1),I(0),I(1),M(1),I('.5'),M(2),I(0),I('.5'),M(6)],['1/2','3/8','CONDITIONAL PDF=']),
('HW4 631 Q4 fX joint-slice','M2SLICE',[M(2),I('24X*(1-X-Y)'),I(1),I('.5'),I(0),I('1-X'),M(6)],['3/2']),
('HW4 631 Q4 fY joint-slice','M2SLICE',[M(1),I('24X*(1-X-Y)'),I(1),I('.5'),I(0),I('1-Y'),M(6)],['1/2']),
('HW4 631 Q5 joint-slice reimbursement','M2SLICE',[M(2),I('(20-X)/(25X)'),I(1),I(12),I('X/2'),I('X'),M(1),I(8),M(2),I(8),I(12),M(6)],['4/25','1/6','2/3']),
]
cases.append(('HW4 Q1 complete marginal tables','M2DISC',grid('{1,2}','{1,2,3}','X+Y²')+[M(2),M(6),M(7),M(7)],['17/37','20/37','5/37','11/37','21/37']))
results=[]
for name,prog,acts,needles in cases:
 r=Sim('midterm2_app/src').run(prog,acts,max_steps=7000000)
 assert r.error is None,(name,r.error,r.text)
 assert r.leaks==0,(name,r.leaks)
 assert not r.warnings,(name,r.warnings)
 assert r.ended_reason=='end',(name,r.ended_reason,r.text[-800:])
 for needle in needles:assert needle in r.text,(name,needle,r.text)
 results.append({'case':name,'status':'pass','screens':len(r.screens),'text':r.text})
 print('PASS',name)
Path('tmp/pdfs/hw4_walkthrough_traces.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
