#!/usr/bin/env python3
"""build_package.py - regenerate, lint, test, build and package the STA 431 Midterm II suite.

    python3 tools/build_package.py DEST        (e.g. ../output/STA431_Midterm_II_Calculator_Package)

Steps (PLAN.md section 6):
  1. run every tools/write_*.py (sorted), then tools/content.py gen for every content/*.json
  2. tibuild.py lint src and tilint.py src: any ERROR or WARN fails the build
  3. run every tests/test_*.py; record a check count from "Ran N tests", "PASS N ...", or
     "N/M ... passed" (else 1); a non-zero exit status fails the build
  4. clear out/*.8xp, run tibuild.py build src out, and require one .8xp per program in ORDER
     (ORDER = ['STAM2'] + sorted(the other src stems))
  5. memory budget: the .8xp total must be <= 118,000 bytes (target 112,000)
  6. recreate DEST (only if it is empty or holds VALIDATION.json; otherwise abort), write
     calculator_files/*.8xp, source_code/{src,content,tools,tests}, requirements.txt, START_HERE.md,
     VALIDATION.json/.txt, SHA256SUMS.txt, then DEST.zip next to DEST.
Every tool's own output is printed; a failing step stops the build with that tool's message.
The earlier Midterm I suite (../dev) is never touched.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUDGET_BYTES = 118_000          # hard limit for the .8xp total (PLAN 3.1)
TARGET_BYTES = 112_000          # goal
PER_PROGRAM_OVERHEAD = 100      # estimate used before .8xp files exist (test_lint_all)
MAIN = 'STAM2'


class BuildError(RuntimeError):
    pass


def program_order(src=ROOT / 'src'):
    stems = sorted(p.stem for p in Path(src).glob('*.txt'))
    if MAIN not in stems:
        raise BuildError(f'{MAIN}.txt is missing from {src}')
    return [MAIN] + [s for s in stems if s != MAIN]


def tokenized_sizes(src=ROOT / 'src'):
    sys.path.insert(0, str(ROOT / 'tools'))
    import tibuild
    out = {}
    for name in program_order(src):
        out[name] = len(tibuild.tokenize(tibuild.clean_source((Path(src) / f'{name}.txt').read_text(encoding='utf-8'))))
    return out


def memory_estimate(src=ROOT / 'src'):
    """sum(tokenized) + 100 per program: the pre-build estimate of the .8xp total."""
    sizes = tokenized_sizes(src)
    return sum(sizes.values()) + PER_PROGRAM_OVERHEAD * len(sizes)


def run(*args, label=None):
    """Run a Python tool from ROOT, print its output, and fail with that output on a non-zero exit."""
    cmd = [sys.executable, *map(str, args)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    log = r.stdout + r.stderr
    name = label or ' '.join(Path(str(a)).name for a in args)
    print(f'--- {name}')
    if log:
        print(log, end='' if log.endswith('\n') else '\n')
    if r.returncode != 0:
        raise BuildError(f'{name} failed (exit {r.returncode}):\n{log}')
    return log


def count_checks(log):
    for pat in (r'Ran (\d+) tests?', r'(\d+)/\d+ [^\n]*passed', r'PASS (\d+) '):
        found = re.findall(pat, log)
        if found:
            return int(found[-1])
    return 1


def lint_clean(log, tool):
    bad = [ln for ln in log.splitlines() if ln.startswith(('ERROR', 'WARN'))]
    if bad:
        raise BuildError(f'{tool} reported {len(bad)} problem(s):\n' + '\n'.join(bad))


def safe_recreate(dest):
    if dest.exists():
        if not dest.is_dir():
            raise BuildError(f'{dest} exists and is not a directory')
        if any(dest.iterdir()) and not (dest / 'VALIDATION.json').exists():
            raise BuildError(f'refusing to delete {dest}: it is not empty and has no VALIDATION.json')
        shutil.rmtree(dest)
    dest.mkdir(parents=True)


def main(dest):
    dest = Path(dest).resolve()
    if ROOT in dest.parents or dest == ROOT:
        raise BuildError('DEST must be outside the app folder')
    # 1. generators, then content programs
    for gen in sorted((ROOT / 'tools').glob('write_*.py')):
        run(gen)
    for doc in sorted((ROOT / 'content').glob('*.json')):
        run(ROOT / 'tools/content.py', 'gen', doc, ROOT / 'src', label=f'content.py gen {doc.name}')
    order = program_order()
    # 2. both linters, zero errors and zero warnings
    lint_clean(run(ROOT / 'tools/tibuild.py', 'lint', ROOT / 'src', label='tibuild.py lint src'), 'tibuild lint')
    lint_clean(run(ROOT / 'tools/tilint.py', ROOT / 'src', label='tilint.py src'), 'tilint')
    # 3. every test file
    counts = {}
    for test in sorted((ROOT / 'tests').glob('test_*.py')):
        counts[test.name] = count_checks(run(test))
    # 4. fresh .8xp files
    out = ROOT / 'out'
    out.mkdir(exist_ok=True)
    for old in out.glob('*.8xp'):
        old.unlink()
    run(ROOT / 'tools/tibuild.py', 'build', ROOT / 'src', out, label='tibuild.py build src out')
    missing = [n for n in order if not (out / f'{n}.8xp').exists()]
    extra = sorted(p.stem for p in out.glob('*.8xp') if p.stem not in order)
    if missing or extra:
        raise BuildError(f'out/ mismatch: missing {missing}, unexpected {extra}')
    # 5. memory budget
    sizes = {n: (out / f'{n}.8xp').stat().st_size for n in order}
    total = sum(sizes.values())
    print(f'--- memory: {total} bytes in {len(order)} programs (limit {BUDGET_BYTES}, target {TARGET_BYTES})')
    if total > BUDGET_BYTES:
        raise BuildError(f'.8xp total {total} exceeds the {BUDGET_BYTES}-byte budget')
    # 6. package
    safe_recreate(dest)
    calc = dest / 'calculator_files'
    calc.mkdir()
    for n in order:
        shutil.copy2(out / f'{n}.8xp', calc / f'{n}.8xp')
    source = dest / 'source_code'
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store', '.play')
    for folder in ['src', 'content', 'tools', 'tests']:
        shutil.copytree(ROOT / folder, source / folder, ignore=ignore)
    for name in ['requirements.txt', 'START_HERE.md']:
        shutil.copy2(ROOT / name, source / name)
        shutil.copy2(ROOT / name, dest / name)
    report = {
        'built_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'checks': counts,
        'total_checks': sum(counts.values()),
        'programs': order,
        'program_count': len(order),
        'bytes_8xp': sizes,
        'total_bytes_8xp': total,
        'budget_bytes': BUDGET_BYTES,
        'lint': 'tibuild lint and tilint: 0 errors, 0 warnings',
        'physical_device_tested': False,
    }
    (dest / 'VALIDATION.json').write_text(json.dumps(report, indent=2) + '\n')
    (dest / 'VALIDATION.txt').write_text(
        f'All {len(counts)} simulator test files passed ({sum(counts.values())} checks).\n'
        f'{len(order)} programs, {total} bytes of .8xp files (budget {BUDGET_BYTES}).\n'
        'Token and structure lints: 0 errors, 0 warnings.\n'
        'Tested off-device in the token-stream simulator; physical-calculator execution is untested.\n')
    sums = []
    for f in sorted(dest.rglob('*')):
        if f.is_file() and f.name != 'SHA256SUMS.txt':
            sums.append(hashlib.sha256(f.read_bytes()).hexdigest() + '  ' + str(f.relative_to(dest)))
    (dest / 'SHA256SUMS.txt').write_text('\n'.join(sums) + '\n')
    zip_path = dest.parent / (dest.name + '.zip')
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(dest), 'zip', root_dir=dest.parent, base_dir=dest.name)
    print('PACKAGE READY', dest)
    print('ZIP', zip_path)
    print('PROGRAMS', len(order), 'BYTES', total, 'CHECKS', sum(counts.values()))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 tools/build_package.py DEST')
    try:
        main(Path(sys.argv[1]))
    except BuildError as e:
        print(f'BUILD FAILED: {e}', file=sys.stderr)
        raise SystemExit(1)
