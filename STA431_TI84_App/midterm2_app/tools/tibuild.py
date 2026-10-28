#!/usr/bin/env python3
"""
tibuild.py - compile TI-BASIC source text (.txt) into TI-84 Plus CE programs (.8xp)
and run tokenization lints that catch the classic "looks right, is wrong" bugs.

Source conventions (see SPEC.md):
  * leading indentation is stripped (TI-BASIC has none)
  * blank lines and lines whose first non-space chars are // are dropped
  * a line that is exactly a command that needs a trailing space (Pause, Disp, ...)
    gets the space re-added, because "Pause" without it tokenizes as P+a+u+s+e
  * file stem = program name (e.g. src/STACNT.txt -> STACNT.8xp, prgmSTACNT)

CLI:
  python tibuild.py lint  <src_dir | file.txt ...>     # lint only
  python tibuild.py build <src_dir> <out_dir>          # lint + write .8xp (+ group)
  python tibuild.py clean <file.txt>                   # print cleaned source

Python API (used by the simulator / tests):
  clean_source(text) -> str
  tokenize(clean_text) -> bytes
  token_list(clean_text) -> list[TIToken]
  lint_program(name, clean_text) -> list[str]   (messages prefixed ERROR/WARN)
"""
import os
import re
import sys

from tivars.models import TI_84PCE
from tivars.tokenizer import decode, encode
from tivars.types import TIProgram

TRIE = TI_84PCE.tokens.tries[None]

# Commands whose token text ends in a space; a bare line "Pause" must become "Pause "
TRAILING_SPACE_CMDS = [
    "Pause", "Disp", "Input", "Prompt", "If", "While", "Repeat", "Lbl", "Goto",
    "DelVar", "FnOff", "FnOn", "ClrList", "Fix", "Wait", "SetUpEditor", "Archive",
    "UnArchive", "PlotsOff", "PlotsOn",
]

NAME_RE = re.compile(r"^[A-Zθ][A-Z0-9θ]{0,7}$")


def clean_source(text: str) -> str:
    out = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("//"):
            continue
        if s in TRAILING_SPACE_CMDS:
            s += " "
        out.append(s)
    return "\n".join(out)


def tokenize(clean_text: str) -> bytes:
    data, _ = encode(clean_text, trie=TRIE, mode="smart")
    return data


def token_list(clean_text: str):
    toks, _ = decode(tokenize(clean_text))
    return toks


def disp(tok) -> str:
    d = tok.display
    if d == "\\'":
        d = "'"
    return d


def detok(toks) -> str:
    return "".join(disp(t) for t in toks)


# ---------------------------------------------------------------- lints
LOWER_TOKENS = {bytes([0xBB, b]) for b in range(0xB0, 0xCB)}  # a..z as text chars
# stat / sequence variable tokens that *display* as lowercase letters
LOOKALIKE_LOWER = {bytes.fromhex(h) for h in (
    "5e80", "5e81", "5e82",            # u v w
    "6202", "6212", "6216", "6217", "6218", "6219", "621a", "6222", "6223",
    "6224", "6234",                    # n r a b c d e p z t s (stat vars)
)}
SUB = b"\x71"   # binary minus
NEG = b"\xb0"   # negation
# tokens after which a '-' (binary minus) cannot be binary -> must be negation
OPENERS = {b"\x10", b"\x2b", b"\x08", b"\x06", b"\x6a", b"\x6b", b"\x6c", b"\x6d",
           b"\x6e", b"\x6f", b"\x70", b"\x71", b"\x82", b"\x83", b"\xf0", b"\x3b",
           b"\x40", b"\x3c", b"\x3d", b"\x04", b"\x3e", b"\x3f", b"\xce", b"\xd1",
           b"\xd2", b"\xde", b"\xd8", b"\x95", b"\x94", b"\xb0"}
FUNC_OPEN_SUFFIX = "("


def split_lines(toks):
    line, lines = [], []
    for t in toks:
        if t.bits == b"\x3f":
            lines.append(line)
            line = []
        else:
            line.append(t)
    lines.append(line)
    return lines


def lint_program(name: str, clean_text: str):
    msgs = []
    if not NAME_RE.match(name):
        msgs.append(f"ERROR {name}: invalid program name (A-Z first, <=8 chars A-Z0-9)")
    try:
        data = tokenize(clean_text)
    except ValueError as e:
        return [f"ERROR {name}: tokenization failed: {e}"]
    toks, _ = decode(data)
    src_lines = clean_text.split("\n")
    tok_lines = split_lines(toks)
    if len(src_lines) != len(tok_lines):
        msgs.append(f"WARN {name}: line count mismatch src={len(src_lines)} tok={len(tok_lines)}")
    for ln, (src, tl) in enumerate(zip(src_lines, tok_lines), start=1):
        in_str = False
        str_toks = []
        prev = None
        for t in tl:
            b = t.bits
            if b == b"\x2a":  # quote
                if in_str:
                    in_str = False
                    str_toks = []
                else:
                    in_str = True
                    str_toks = []
                prev = t
                continue
            if in_str:
                if b == b"\x04":
                    msgs.append(f"ERROR {name}:{ln}: store arrow inside string (did you write '->'?): {src}")
                    in_str = False
                elif b == b"\x3e":
                    msgs.append(f"WARN {name}:{ln}: colon inside string (policy: avoid): {src}")
                str_toks.append(t)
                prev = t
                continue
            # outside strings
            if b in LOWER_TOKENS or b in LOOKALIKE_LOWER:
                msgs.append(f"ERROR {name}:{ln}: lowercase letter token '{disp(t)}' outside a string "
                            f"(command mis-tokenized? missing trailing space?): {src}")
            if b == SUB and (prev is None or prev.bits in OPENERS or disp(prev).endswith(FUNC_OPEN_SUFFIX)):
                msgs.append(f"ERROR {name}:{ln}: binary minus '-' where negation '⁻' is required: {src}")
            prev = t
        if in_str and not src.rstrip().endswith('"'):
            msgs.append(f"WARN {name}:{ln}: string not closed on this line: {src}")
        # string content round trip: every "..." literal in source must decode to identical text
        for m in re.finditer(r'"([^"]*)"', src):
            lit = m.group(1)
            if "→" in lit:
                continue  # already reported
            try:
                b2, _ = encode('"' + lit + '"', trie=TRIE, mode="smart")
                t2, _ = decode(b2)
                back = detok(t2)[1:-1]
            except ValueError as e:
                msgs.append(f"ERROR {name}:{ln}: cannot tokenize string {lit!r}: {e}")
                continue
            want = lit.replace("|π", "π")
            if back != want:
                msgs.append(f"ERROR {name}:{ln}: string {lit!r} would display as {back!r}")
    return msgs


def display_len(s: str) -> int:
    return len(s.replace("|π", "π"))


# ---------------------------------------------------------------- build
def read_program(path):
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path, encoding="utf-8") as f:
        return name, clean_source(f.read())


def iter_sources(args):
    for a in args:
        if os.path.isdir(a):
            for fn in sorted(os.listdir(a)):
                if fn.endswith(".txt"):
                    yield os.path.join(a, fn)
        else:
            yield a


def build(src_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    errors = 0
    built = []
    for path in iter_sources([src_dir]):
        name, text = read_program(path)
        msgs = lint_program(name, text)
        for m in msgs:
            print(m)
        if any(m.startswith("ERROR") for m in msgs):
            errors += 1
            continue
        prog = TIProgram(name=name)
        prog.load_string(text, model=TI_84PCE)
        dest = os.path.join(out_dir, name + ".8xp")
        prog.save(dest)
        built.append((name, len(prog.data), dest))
    for name, size, dest in built:
        print(f"built {name:9s} {size:6d} bytes -> {dest}")
    print(f"total program bytes: {sum(s for _, s, _ in built)}")
    return errors


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "lint":
        n_err = 0
        for path in iter_sources(argv[2:]):
            name, text = read_program(path)
            msgs = lint_program(name, text)
            for m in msgs:
                print(m)
            n_err += sum(m.startswith("ERROR") for m in msgs)
            print(f"{name}: {len(tokenize(text)) if not n_err else '?'} bytes, "
                  f"{sum(m.startswith('ERROR') for m in msgs)} errors, "
                  f"{sum(m.startswith('WARN') for m in msgs)} warnings")
        return 1 if n_err else 0
    if cmd == "build":
        return 1 if build(argv[2], argv[3]) else 0
    if cmd == "clean":
        print(read_program(argv[2])[1])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
