#!/usr/bin/env python3
"""Rebuild, validate, and package STAM2 without changing the earlier STA431 suite."""
from pathlib import Path
import hashlib,shutil,subprocess,sys,json,re
ROOT=Path(__file__).resolve().parents[1]
ORDER=['STAM2','M2EXAM','M2DISC','M2CONT','M2COV','M2MGF','M2ENC','M2HW','M2RUN','M2SLICE','M2FMT']
def run(*args):
 r=subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,check=True,capture_output=True,text=True)
 log=r.stdout+r.stderr
 print(log,end="" if log.endswith("\n") else "\n")
 return log
def main(dest):
 run(ROOT/'tools/write_content.py')
 run(ROOT/'tools/write_presets.py')
 for name in ['M2ENC','M2HW']:run(ROOT/'tools/content.py','gen',ROOT/'content'/f'{name}.json',ROOT/'src')
 run(ROOT/'tools/tibuild.py','lint',ROOT/'src')
 run(ROOT/'tools/tilint.py',ROOT/'src')
 counts={}
 for name in ['test_disc_cont.py','test_cov_mgf.py','test_reference_navigation.py','test_slice.py','test_presets.py','test_workflow_upgrades.py','tests_exam_assistant.py','test_transfer_general.py']:
  log=run(ROOT/'tests'/name)
  found=re.search(r'Ran (\d+) tests',log) or re.search(r'PASS (\d+) reference/menu',log) or re.search(r'(\d+)/(?:\d+) M2DISC/M2CONT cases passed',log)
  if not found:raise RuntimeError('No validation count for '+name)
  counts[name]=int(found.group(1))
 run(ROOT/'tools/tibuild.py','build',ROOT/'src',ROOT/'out')
 dest=dest.resolve();dest.mkdir(parents=True,exist_ok=True)
 calc=dest/'calculator_files';calc.mkdir(exist_ok=True)
 for name in ORDER:shutil.copy2(ROOT/'out'/f'{name}.8xp',calc/f'{name}.8xp')
 source=dest/'source_code';source.mkdir(exist_ok=True)
 for folder in ['src','content','tools','tests']:
  shutil.copytree(ROOT/folder,source/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for name in ['requirements.txt','START_HERE.md']:
  shutil.copy2(ROOT/name,source/name);shutil.copy2(ROOT/name,dest/name)
 report={'checks':counts,'total_checks':sum(counts.values()),'programs':len(ORDER),'physical_device_tested':False}
 (dest/'VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
 (dest/'VALIDATION.txt').write_text('All included simulator checks passed.\n'+str(sum(counts.values()))+' checks; '+str(len(ORDER))+' exported programs.\nToken/static lints passed. Physical-device execution remains untested.\n')
 sums=[]
 for f in sorted(dest.rglob('*')):
  if f.is_file() and f.name!='SHA256SUMS.txt':sums.append(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(dest)))
 (dest/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n')
 print('PACKAGE READY',dest)
 print('PROGRAMS',len(ORDER),'BYTES',sum((calc/f'{n}.8xp').stat().st_size for n in ORDER))
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('Usage: python tools/build_package.py DEST')
 main(Path(sys.argv[1]))
