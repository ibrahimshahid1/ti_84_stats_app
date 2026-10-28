#!/usr/bin/env python3
"""Generate input presets, not stored answers: all results use the general solvers."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GRID={
 'A1':('HW4 Q1','{1,2}','{1,2,3}','X+Y²',1,'A'),
 'A4':('HW4 Q4','{1,2}','{1,2,3,4}','X+Y',4,'A'),
 'B1':('HW5 Q1','{1,2,3,4}','{0}','X²+X',11,'B'),
 'C4':('HW5 Q8','{1,2,3}','{1,2,3}','X+Y',18,'C')}
# P2: the joint-density presets load q and the support record into M2JNT (Z=99, PLAN 4.3).
JOINT={
 'A2':('HW4 Q2','2X+Y','{1,0,1,0,2}',['RECT 0<x<1, 0<y<2','c IS COMPUTED']),
 'A3':('HW4 Q3','(X+Y)/8','{1,0,2,0,2}',['RECT 0<x<2, 0<y<2','FAILS IF EITHER FAILS','USE EVENTS > MIN/MAX']),
 'A5':('HW4 Q5','(2X+Y)/4','{1,0,1,0,2}',['RECT 0<x<1, 0<y<2','USE EVENTS > X<Y']),
 'C3':('HW5 Q7','X+Y','{1,0,1,0,1}',['UNIT SQUARE','USE GIVEN A VALUE','THEN GIVEN Y=y'])}
ONE={
 'B2':('HW5 Q2','3/4*(1-X²)','0','⁻1','1',12,'B')}
L=['// M2RUN - supplied-homework input presets; general solvers compute every result.',
'Lbl M','Menu("HOMEWORK QUICK SOLVE","HW4 COMMON +431",A,"HW5 Q1 TO Q4",B,"HW5 Q5 TO Q8",C,"BACK",Z)',
'Lbl A','Menu("HW4 LOAD + SOLVE","Q1 JOINT PMF",A1,"Q2 JOINT PDF",A2,"Q3 SERIES LIFETIME",A3,"Q4 PMF EVENTS",A4,"Q5 X LESS Y",A5,"BACK",M)',
'Lbl B','Menu("HW5 LOAD + SOLVE","Q1 PMF MOMENTS",B1,"Q2 PDF AND SQUARE",B2,"Q3 EXPONENTIAL MGF",B3,"Q4 AFFINE MGF",B4,"BACK",M)',
'Lbl C','Menu("HW5 LOAD + SOLVE","Q5 CLAIM VARIANCE",C1,"Q6 THREE VARIABLES",C2,"Q7 CONDITIONAL",C3,"Q8 JOINT MOMENTS",C4,"BACK",M)']
def intro(label,title,lines):
 L.extend(['Lbl '+label,'ClrHome','Disp "'+title+'"']+['Disp "'+x+'"' for x in lines]+['Pause'])
def call(code,prog,back):L.extend([str(code)+'→Z','prgm'+prog,'0→Z','Goto '+back])
for lab,(title,xs,ys,q,code,back) in GRID.items():
 intro(lab,title,['PRELOAD x AND y GRID','q='+q,'GENERAL SOLVER COMPUTES'])
 L.extend([xs+'→ʟM2AX',ys+'→ʟM2AY','"'+q+'"→Str1'])
 call(code,'M2DISC',back)
for lab,(title,q,rec,lines) in JOINT.items():
 intro(lab,title,['PRELOAD JOINT DENSITY','q='+q]+lines)
 L.extend(['"'+q+'"→Str1',rec+'→ʟM2JM'])
 call(99,'M2JNT',lab[0])
for lab,(title,q,a,lo,hi,code,back) in ONE.items():
 intro(lab,title,['PRELOAD 1D DENSITY/SLICE','q='+q,'USE MOMENTS OR INTERVAL'])
 L.extend(['"'+q+'"→Str1',a+'→A',lo+'→B',hi+'→C'])
 call(code,'M2CONT',back)
intro('B3','HW5 Q3',['EXPONENTIAL RATE 3','NO AFFINE CHANGE'])
L.extend(['3→L','1→A','0→B']);call(13,'M2MGF','B')
intro('B4','HW5 Q4',['Mx=e^(4t+8t²)','Z=(X-4)/4'])
L.extend(['4→C','8→D','1/4→A','⁻1→B']);call(14,'M2MGF','B')
for lab,title,n,vr,cv,ca,offset,code in [
 ('C1','HW5 Q5',2,'{300,500,0}','{300,150,0,150,500,0,0,0,0}','{2,1.1,0}',100,15),
 ('C2','HW5 Q6',3,'{4,9,2}','{4,1,⁻1,1,9,0,⁻1,0,2}','{3,⁻2,1}',0,16)]:
 intro(lab,title,['PRELOAD GIVEN VAR/COV','MEANS NOT PROVIDED','OFFSETS INCLUDED'])
 L.extend([str(n)+'→N','1→M','0→E','{0,0,0}→ʟM2MU',vr+'→ʟM2VR',cv+'→ʟM2CV',ca+'→ʟM2CA','{0,0,0}→ʟM2CB',str(offset)+'→C','0→D'])
 call(code,'M2COV','C')
L.extend(['Lbl Z','0→Z','Return'])
(ROOT/'src/M2RUN.txt').write_text('\n'.join(L)+'\n')
print('Generated 13 input presets, no stored answers.')
