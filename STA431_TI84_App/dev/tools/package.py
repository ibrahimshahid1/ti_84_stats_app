#!/usr/bin/env python3
"""
package.py - validate, build, and bundle the complete exam package.

  python package.py <dest_dir>
"""
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import tibuild  # noqa: E402
from tivars.models import TI_84PCE  # noqa: E402
from tivars.types import TIProgram  # noqa: E402
from tivars.types.group import TIGroup  # noqa: E402

ORDER = ["STA431", "STAFMT", "STAE1", "STAE2", "STAE3", "STAHNT", "STACNT", "STAPRB", "STARV"]
GROUPS = [
    ("STA_REF1", "STA4R1", ["STA431", "STAFMT", "STAE1", "STAE2"]),
    ("STA_REF2", "STA4R2", ["STAE3", "STAHNT"]),
    ("STA_CALC", "STA4CALC", ["STACNT", "STAPRB", "STARV"]),
]


def run(cmd):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(f"failed: {' '.join(cmd)}")


def main(dest):
    grouped = [name for _, _, members in GROUPS for name in members]
    if len(grouped) != len(ORDER) or set(grouped) != set(ORDER):
        raise ValueError("group plan must contain each program exactly once")
    py = sys.executable
    for prog in ["STAE1", "STAE2", "STAE3", "STAHNT"]:
        run([py, "tools/content.py", "gen", f"content/{prog}.json", "src/"])
    run([py, "tools/tibuild.py", "lint", "src"])
    if os.path.exists(os.path.join(HERE, "tilint.py")):
        run([py, "tools/tilint.py"] + [f"src/{p}.txt" for p in ORDER])
    for test in ["test_tisim.py", "test_STACNT.py", "test_STAPRB.py", "test_STARV.py", "test_joint.py"]:
        run([py, "tests/" + test])
    run([py, "tools/tibuild.py", "build", "src", "out"])
    calculator_dir = os.path.join(dest, "calculator_files")
    if os.path.isdir(calculator_dir):
        shutil.rmtree(calculator_dir)
    individual_dir = os.path.join(calculator_dir, "1_TRANSFER_ALL_NINE_PROGRAMS")
    group_dir = os.path.join(calculator_dir, "2_OPTIONAL_THREE_GROUPS")
    os.makedirs(individual_dir)
    os.makedirs(group_dir)
    os.makedirs(os.path.join(dest, "source_code"), exist_ok=True)
    os.makedirs(os.path.join(dest, "source_code", "src"), exist_ok=True)
    progs = {}
    total = 0
    for name in ORDER:
        with open(os.path.join(ROOT, "src", name + ".txt"), encoding="utf-8") as f:
            text = tibuild.clean_source(f.read())
        p = TIProgram(name=name)
        p.load_string(text, model=TI_84PCE)
        p.save(os.path.join(individual_dir, name + ".8xp"))
        progs[name] = p
        total += len(p.data)
        shutil.copy(
            os.path.join(ROOT, "src", name + ".txt"),
            os.path.join(dest, "source_code", "src", name + ".txt"),
        )
        print(f"{name:8s} {len(p.data):6d} bytes")
    print(f"TOTAL    {total:6d} bytes")
    for filename, group_name, members in GROUPS:
        g = TIGroup.group([progs[name] for name in members], name=group_name)
        g.save(os.path.join(group_dir, filename + ".8xg"))
        print(f"group {filename:9s} {', '.join(members)}")
    for extra in ["content", "tools", "tests", "oracles"]:
        src = os.path.join(ROOT, extra)
        if os.path.isdir(src):
            shutil.copytree(
                src, os.path.join(dest, "source_code", extra), dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
    for filename in ["SPEC.md", "requirements.txt"]:
        shutil.copy(os.path.join(ROOT, filename), os.path.join(dest, "source_code", filename))
    for filename in ["START_HERE.md", "EXAM_MENU_CARD.md", "EXAM_MENU_CARD.pdf", "INSTALL_AND_DEVICE_TEST.md"]:
        shutil.copy(os.path.join(ROOT, filename), os.path.join(dest, filename))
        shutil.copy(os.path.join(ROOT, filename), os.path.join(dest, "source_code", filename))
    sums = []
    for base, _, files in os.walk(dest):
        for filename in files:
            if filename == "SHA256SUMS.txt":
                continue
            path = os.path.join(base, filename)
            with open(path, "rb") as stream:
                digest = hashlib.sha256(stream.read()).hexdigest()
            sums.append((os.path.relpath(path, dest), digest))
    with open(os.path.join(dest, "SHA256SUMS.txt"), "w", encoding="utf-8") as stream:
        for path, digest in sorted(sums):
            stream.write(f"{digest}  {path}\n")
    print("packaged ->", dest)
    archive = shutil.make_archive(dest, "zip", root_dir=os.path.dirname(dest), base_dir=os.path.basename(dest))
    print("archive ->", archive)


if __name__ == "__main__":
    main(sys.argv[1])
