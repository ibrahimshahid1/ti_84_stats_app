#!/usr/bin/env python3
"""
tilint.py - static STRUCTURE linter for our TI-BASIC sources (complements `tibuild.py lint`, which checks
tokenization: lowercase outside strings, binary minus as negation, string round trips, ...).

It cleans the source with tibuild.clean_source, tokenizes it with tibuild.token_list (the exact tokens that go
into the .8xp) and splits statements at newlines and ':' outside strings.  Line numbers in messages are
line numbers of the ORIGINAL src/NAME.txt file (comments and blank lines counted).

Checks (SPEC sections 2, 3 and 6)
  ERROR  duplicate Lbl, invalid label name, Goto / Menu( target label missing
  ERROR  blocks unbalanced: End without an open block, block never closed, Then not directly after If,
         Else outside an If-Then block (or a second Else), If on the last line
  ERROR  Goto or Menu( executed inside an open If-Then / For( / While / Repeat block (leaks memory; SPEC
         rule 9).  A one-line "If cond" + "Goto X" (no Then) at block depth 0 is fine.
  ERROR  Goto from outside a block to a Lbl inside that block (its End would pop a frame that is not there)
  ERROR  Menu(: odd argument layout, > 7 options, title > 22 chars, option text > 18 chars
  ERROR  Output(: literal row not in 1..10 / column not in 1..26; string literal (or the literal parts of a
         "lit"+... concatenation) does not fit in the row from its column (26-col+1 chars, SPEC rule 18)
  ERROR  Disp string literal > 26 chars;  Input prompt literal > 16 chars
  WARN   formatter misuse: after prgmSTAFMT, Q R S T U V are read before being re-assigned (STAFMT clobbers
         them), including reads that happen on the next pass of a loop that contains the call and a For(
         loop whose counter is one of Q..V
  WARN   one-line If controlling a block statement (Then/For/While/Repeat/End/Else/Lbl); Stop (subprograms
         must end with Return); subprogram with no Return; empty string literal "" (SPEC rule 13)

Python API:   lint_source(name, text) -> list[str]     lint_file(path) -> list[str]
CLI:          $PY tools/tilint.py src/STACNT.txt [more files or directories ...]   (exit 1 on any ERROR)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tibuild  # noqa: E402


def B(h):
    return bytes.fromhex(h)


NEWLINE, COLON, QUOTE, STORE, COMMA = B("3f"), B("3e"), B("2a"), B("04"), B("2b")
LPAREN, RPAREN, LBRACE, RBRACE, LBRACK, RBRACK = B("10"), B("11"), B("08"), B("09"), B("06"), B("07")
ADD = B("70")
IF, THEN, ELSE, WHILE, REPEAT, FOR, END = (B(h) for h in ("ce", "cf", "d0", "d1", "d2", "d3", "d4"))
RETURN, LBL, GOTO, PAUSE, STOP = (B(h) for h in ("d5", "d6", "d7", "d8", "d9"))
INPUT, PROMPT, DISP, OUTPUT = B("dc"), B("dd"), B("de"), B("e0")
MENU, PRGM, LIST_L, DELVAR, THETA = B("e6"), B("5f"), B("eb"), B("bb54"), B("5b")
OPENERS = {THEN, WHILE, REPEAT, FOR}
BLOCKISH = {THEN, WHILE, REPEAT, FOR, END, ELSE, LBL}
NAMES = {IF: "If", THEN: "Then", ELSE: "Else", WHILE: "While", REPEAT: "Repeat", FOR: "For(", END: "End"}

LETTER = {bytes([0x41 + i]): chr(0x41 + i) for i in range(26)}
LETTER[THETA] = "θ"
DIGIT = {bytes([0x30 + i]): str(i) for i in range(10)}
NAMECH = dict(LETTER)
NAMECH.update(DIGIT)
FMT_SCRATCH = {B("51"): "Q", B("52"): "R", B("53"): "S", B("54"): "T", B("55"): "U", B("56"): "V"}

ROWS, COLS = 10, 26
MENU_MAX_ITEMS, MENU_TITLE_MAX, MENU_ITEM_MAX = 7, 22, 18
DISP_MAX, INPUT_PROMPT_MAX = 26, 16
FORMATTER = "STAFMT"
MAIN_PROGRAM = "STA431"


# ------------------------------------------------------------------------------------------ parsing
class Stmt:
    __slots__ = ("toks", "bits", "kind", "line", "src", "idx")

    def __init__(self, toks, line, src, idx):
        self.toks = toks
        self.bits = [t.bits for t in toks]
        self.kind = self.bits[0] if toks else None
        self.line = line
        self.src = src
        self.idx = idx


def split_statements(toks, line_map, src_lines):
    """Statements at newline / ':' outside strings. A string ends at '"', '→' or newline (like the TI)."""
    stmts, cur = [], []
    state = {"line": 0}
    in_str = False

    def flush():
        ln_i = state["line"]
        ln = line_map[ln_i] if ln_i < len(line_map) else ln_i + 1
        src = src_lines[ln - 1].strip() if 0 < ln <= len(src_lines) else ""
        stmts.append(Stmt(list(cur), ln, src, len(stmts)))
        cur.clear()

    for t in toks:
        b = t.bits
        if b == NEWLINE:
            flush()
            state["line"] += 1
            in_str = False
            continue
        if in_str:
            if b in (QUOTE, STORE):
                in_str = False
            cur.append(t)
            continue
        if b == QUOTE:
            in_str = True
            cur.append(t)
        elif b == COLON:
            flush()
        else:
            cur.append(t)
    flush()
    return stmts


def label_of(toks):
    """Label name from the tokens after Lbl/Goto (or a Menu( label argument); None if invalid."""
    s = ""
    for t in toks:
        c = NAMECH.get(t.bits)
        if c is None:
            return None
        s += c
    return s if 1 <= len(s) <= 2 else None


def split_args(toks):
    """Split tokens (after an opening 'Cmd(' or 'Cmd ') into top-level comma-separated args.
    A trailing ')' closing the command is dropped."""
    args, cur, depth, in_str = [], [], 0, False
    for t in toks:
        b = t.bits
        if in_str:
            cur.append(t)
            if b in (QUOTE, STORE):
                in_str = False
            continue
        if b == QUOTE:
            in_str = True
            cur.append(t)
            continue
        if b == COMMA and depth == 0:
            args.append(cur)
            cur = []
            continue
        if b in (RPAREN, RBRACE, RBRACK):
            if depth == 0:
                continue  # the command's own closing paren (trailing, or stray)
            depth -= 1
        elif b in (LPAREN, LBRACE, LBRACK) or tibuild.disp(t).endswith("("):
            depth += 1
        cur.append(t)
    args.append(cur)
    return args


def string_literal(arg):
    """If arg is exactly one string literal, return its token list (content), else None."""
    if len(arg) >= 2 and arg[0].bits == QUOTE and arg[-1].bits == QUOTE:
        inner = arg[1:-1]
        if all(t.bits != QUOTE for t in inner):
            return inner
    if len(arg) >= 1 and arg[0].bits == QUOTE and all(t.bits != QUOTE for t in arg[1:]):
        return arg[1:]  # unclosed at end of statement (tibuild lint warns separately)
    return None


def split_plus(arg):
    """Split an argument at top-level '+' (string concatenation pieces)."""
    parts, cur, depth, in_str = [], [], 0, False
    for t in arg:
        b = t.bits
        if in_str:
            cur.append(t)
            if b in (QUOTE, STORE):
                in_str = False
            continue
        if b == QUOTE:
            in_str = True
        elif b in (RPAREN, RBRACE, RBRACK):
            depth -= 1
        elif b in (LPAREN, LBRACE, LBRACK) or tibuild.disp(t).endswith("("):
            depth += 1
        elif b == ADD and depth == 0:
            parts.append(cur)
            cur = []
            continue
        cur.append(t)
    parts.append(cur)
    return parts


def text_of(toks):
    return "".join(tibuild.disp(t) for t in toks)


def literal_parts(arg):
    """(total display length of the string-literal pieces, their texts, all_pieces_literal)."""
    total, texts, all_lit = 0, [], True
    for piece in split_plus(arg):
        lit = string_literal(piece)
        if lit is None:
            all_lit = False
            continue
        s = text_of(lit)
        texts.append(s)
        total += len(s)
    return total, texts, all_lit


def int_literal(arg):
    if arg and all(t.bits in DIGIT for t in arg):
        return int("".join(DIGIT[t.bits] for t in arg))
    return None


# ------------------------------------------------------------------------------------------ linter
class Linter:
    def __init__(self, name, text):
        self.name = name
        self.msgs = []
        src_lines = text.splitlines()
        line_map = [i + 1 for i, raw in enumerate(src_lines)
                    if raw.strip() and not raw.strip().startswith("//")]
        clean = tibuild.clean_source(text)
        try:
            toks = tibuild.token_list(clean)
        except ValueError as e:
            self.err(0, f"tokenization failed: {e}")
            self.stmts = []
            return
        self.stmts = split_statements(toks, line_map, src_lines)

    # --- messages
    def err(self, st, msg):
        self._add("ERROR", st, msg)

    def warn(self, st, msg):
        self._add("WARN", st, msg)

    def _add(self, level, st, msg):
        if isinstance(st, Stmt):
            self.msgs.append(f"{level} {self.name}:{st.line}: {msg}  [{st.src}]")
        else:
            self.msgs.append(f"{level} {self.name}:{st}: {msg}")

    # --- passes
    def run(self):
        if not self.stmts:
            return self.msgs
        self.structure()
        self.labels_and_jumps()
        self.display_checks()
        self.formatter_checks()
        self.policy_checks()

        def line_of(msg):
            mm = re.match(r"\S+ [^:]+:(\d+):", msg)
            return int(mm.group(1)) if mm else 0
        self.msgs.sort(key=line_of)     # stable: keeps pass order within a line
        return self.msgs

    def structure(self):
        """Block balance; records for every statement the tuple of open block openers (static)."""
        stmts = self.stmts
        self.parents = []          # per statement: tuple of indices of enclosing openers
        self.block_end = {}        # opener idx -> End idx
        stack = []                 # [(opener idx, kind bits, has_else)]
        for i, st in enumerate(stmts):
            self.parents.append(tuple(s[0] for s in stack))
            k = st.kind
            if k == IF:
                if i + 1 >= len(stmts):
                    self.err(st, "If on the last statement controls nothing")
                elif stmts[i + 1].kind in BLOCKISH - {THEN}:
                    self.warn(st, f"one-line If controls a block statement "
                                  f"'{text_of(stmts[i + 1].toks[:1]).strip()}'")
                if len(st.toks) == 1:
                    self.err(st, "If without a condition")
            elif k == THEN:
                if i == 0 or stmts[i - 1].kind != IF:
                    self.err(st, "Then must directly follow an If statement")
                if len(st.toks) != 1:
                    self.err(st, "Then must stand alone")
                stack.append([i, THEN, False])
            elif k in (WHILE, REPEAT, FOR):
                stack.append([i, k, False])
            elif k == ELSE:
                if not stack or stack[-1][1] != THEN:
                    inner = NAMES.get(stack[-1][1], "?") if stack else "none"
                    self.err(st, f"Else outside an If-Then block (innermost open block = {inner})")
                elif stack[-1][2]:
                    self.err(st, "second Else in the same If-Then block")
                else:
                    stack[-1][2] = True
                if len(st.toks) != 1:
                    self.err(st, "Else must stand alone")
            elif k == END:
                if len(st.toks) != 1:
                    self.err(st, "End must stand alone")
                if not stack:
                    self.err(st, "End without an open If-Then/For(/While/Repeat block")
                else:
                    self.block_end[stack.pop()[0]] = i
        for opener, kind, _ in stack:
            st = stmts[opener]
            what = "If-Then" if kind == THEN else NAMES[kind]
            self.err(st, f"{what} block opened here is never closed with End")
        self.open_at_eof = [s[0] for s in stack]

    def labels_and_jumps(self):
        stmts = self.stmts
        self.labels = {}
        for st in stmts:
            if st.kind == LBL:
                nm = label_of(st.toks[1:])
                if nm is None:
                    self.err(st, "invalid label name (1-2 chars from A-Z, 0-9, θ)")
                elif nm in self.labels:
                    self.err(st, f"duplicate label {nm} (first at line {stmts[self.labels[nm]].line}; "
                                 f"Goto always finds the first)")
                else:
                    self.labels[nm] = st.idx
        for i, st in enumerate(stmts):
            if st.kind == GOTO:
                nm = label_of(st.toks[1:])
                if nm is None:
                    self.err(st, "invalid Goto label")
                    continue
                self._jump(st, i, nm, "Goto")
            elif st.kind == MENU:
                self.check_menu(st, i)

    def _jump(self, st, i, nm, what):
        if nm not in self.labels:
            self.err(st, f"{what} target label {nm} does not exist")
        open_here = self.parents[i]
        if open_here:
            kinds = ", ".join(self._block_desc(o) for o in open_here)
            self.err(st, f"{what} inside an open block ({kinds}) leaks memory -> ERR:MEMORY "
                         f"(SPEC rule 9: jump only at block depth 0)")
        if nm in self.labels:
            t = self.labels[nm]
            inside = [o for o in self.parents[t] if o not in open_here]
            if inside:
                self.err(st, f"{what} to label {nm} (line {self.stmts[t].line}) jumps INTO a "
                             f"{self._block_desc(inside[-1])} block")

    def _block_desc(self, opener_idx):
        st = self.stmts[opener_idx]
        k = st.kind
        what = "If-Then" if k == THEN else NAMES.get(k, "?")
        return f"{what} line {st.line}"

    def check_menu(self, st, i):
        args = split_args(st.toks[1:])
        if len(args) < 3 or len(args) % 2 == 0:
            self.err(st, f"Menu( needs a title then (text,label) pairs; got {len(args)} arguments")
        title = string_literal(args[0]) if args else None
        if title is not None:
            t = text_of(title)
            if len(t) > MENU_TITLE_MAX:
                self.err(st, f"Menu title {t!r} is {len(t)} chars (max {MENU_TITLE_MAX})")
        pairs = [(args[j], args[j + 1] if j + 1 < len(args) else []) for j in range(1, len(args), 2)]
        if len(pairs) > MENU_MAX_ITEMS:
            self.err(st, f"Menu has {len(pairs)} options (max {MENU_MAX_ITEMS})")
        for text_arg, lab_arg in pairs:
            lit = string_literal(text_arg)
            if lit is not None:
                t = text_of(lit)
                if len(t) > MENU_ITEM_MAX:
                    self.err(st, f"Menu option {t!r} is {len(t)} chars (max {MENU_ITEM_MAX})")
            nm = label_of(lab_arg)
            if nm is None:
                self.err(st, f"Menu option label {text_of(lab_arg)!r} is not a valid label")
                continue
            self._jump(st, i, nm, "Menu(")

    def display_checks(self):
        for st in self.stmts:
            k = st.kind
            if k == OUTPUT:
                args = split_args(st.toks[1:])
                if len(args) != 3:
                    self.err(st, f"Output( needs 3 arguments (row,col,value), got {len(args)}")
                    continue
                r, c = int_literal(args[0]), int_literal(args[1])
                if r is not None and not 1 <= r <= ROWS:
                    self.err(st, f"Output row {r} outside 1..{ROWS}")
                if c is not None and not 1 <= c <= COLS:
                    self.err(st, f"Output column {c} outside 1..{COLS}")
                n, texts, all_lit = literal_parts(args[2])
                if texts and c is not None and 1 <= c <= COLS:
                    room = COLS - c + 1
                    if n > room:
                        what = "string" if all_lit and len(texts) == 1 else "literal text"
                        self.err(st, f"Output {what} is {n} chars but only {room} fit from column {c} "
                                     f"(would wrap)")
            elif k == DISP:
                for a in split_args(st.toks[1:]):
                    n, texts, all_lit = literal_parts(a)
                    if texts and n > DISP_MAX:
                        self.err(st, f"Disp literal text is {n} chars (max {DISP_MAX}; longer is cut off)")
            elif k == INPUT:
                args = split_args(st.toks[1:])
                if len(args) == 2:
                    n, texts, _ = literal_parts(args[0])
                    if texts and n > INPUT_PROMPT_MAX:
                        self.err(st, f"Input prompt is {n} chars (max {INPUT_PROMPT_MAX}, leave room to type)")

    # --- formatter misuse ------------------------------------------------------------------
    @staticmethod
    def scratch_events(st):
        """Ordered ('r'|'w', var) events for the STAFMT scratch vars Q..V in one statement."""
        toks, k = st.toks, st.kind
        if k in (LBL, GOTO, MENU, PRGM, None):
            return []
        outside = []                       # tokens outside strings, list names removed
        in_str = False
        i, n = 0, len(toks)
        while i < n:
            b = toks[i].bits
            if in_str:
                if b == QUOTE:
                    in_str = False
                    i += 1
                    continue
                if b != STORE:
                    i += 1
                    continue
                in_str = False             # '→' ends the string and is itself a store
            if b == QUOTE:
                in_str = True
            elif b == LIST_L:              # ʟNAME: the name letters are not variables
                i += 1
                while i < n and toks[i].bits in NAMECH:
                    i += 1
                continue
            else:
                outside.append(toks[i])
            i += 1
        ev = []
        if k in (INPUT, PROMPT, DELVAR):   # every scratch var named here is assigned
            return [("w", FMT_SCRATCH[t.bits]) for t in outside if t.bits in FMT_SCRATCH]
        m = len(outside)
        j = 0
        if k == FOR and m > 1 and outside[1].bits in FMT_SCRATCH:
            first_write = FMT_SCRATCH[outside[1].bits]
            j = 2
        else:
            first_write = None
        final_write = None
        if m >= 2 and outside[-2].bits == STORE and outside[-1].bits in FMT_SCRATCH:
            final_write = FMT_SCRATCH[outside[-1].bits]
            m -= 2
        if first_write:
            ev.append(("w", first_write))
        for t in outside[j:m]:
            if t.bits in FMT_SCRATCH:
                ev.append(("r", FMT_SCRATCH[t.bits]))
        if final_write:
            ev.append(("w", final_write))
        return ev

    @staticmethod
    def is_fmt_call(st):
        return st.kind == PRGM and label_of_name(st.toks[1:]) == FORMATTER

    def formatter_checks(self):
        stmts = self.stmts
        n = len(stmts)
        for ci, call in enumerate(stmts):
            if not self.is_fmt_call(call):
                continue
            live = set(FMT_SCRATCH.values())      # clobbered by STAFMT and not re-assigned yet
            reported = set()
            loops = [o for o in self.parents[ci] if stmts[o].kind in (FOR, WHILE, REPEAT)]
            loop = loops[-1] if loops else None

            def check(st, note=None):
                for kind, v in self.scratch_events(st):
                    if kind == "w":
                        live.discard(v)
                    elif v in live and v not in reported:
                        reported.add(v)
                        where = f" ({note})" if note else ""
                        self.warn(st, f"reads {v} after prgm{FORMATTER} (line {call.line}){where} before "
                                      f"re-assigning it; STAFMT clobbers Q R S T U V")

            j = ci + 1
            wrap = False
            while j < n and live:
                st = stmts[j]
                k = st.kind
                if k in (LBL, GOTO, MENU, RETURN, STOP, PRGM):
                    break
                if loop is not None and j == self.block_end.get(loop):
                    wrap = True
                    break
                if k == ELSE:                     # Then-part done: execution skips to the End
                    j = self.block_end.get(self.parents[j][-1], n - 1) if self.parents[j] else j
                    j += 1
                    continue
                if k not in (END, THEN):
                    check(st)
                j += 1
            if not (wrap and live):
                continue
            # next pass of the loop that contains the call
            op = stmts[loop]
            note = f"next pass of the loop at line {op.line}"
            if op.kind == FOR and len(op.toks) > 1 and op.toks[1].bits in FMT_SCRATCH:
                v = FMT_SCRATCH[op.toks[1].bits]
                if v in live:
                    self.warn(call, f"prgm{FORMATTER} inside For({v},...) (line {op.line}): STAFMT "
                                    f"clobbers the loop counter {v}")
                    reported.add(v)
            if op.kind in (WHILE, REPEAT):
                check(op, note)
            for j in range(loop + 1, ci):
                st = stmts[j]
                if st.kind in (LBL, GOTO, MENU, RETURN, STOP) or not live:
                    break
                if st.kind not in (END, THEN, ELSE, PRGM):
                    check(st, note)

    # --- policy ------------------------------------------------------------------------------
    def policy_checks(self):
        has_return = False
        for st in self.stmts:
            if st.kind == STOP:
                self.warn(st, "Stop ends everything; subprograms must end with Return (SPEC section 1)")
            if st.kind == RETURN:
                has_return = True
            # empty string literal ""
            for a, b in zip(st.bits, st.bits[1:]):
                if a == QUOTE and b == QUOTE:
                    last = st is self.stmts[-1]
                    if not (self.name == MAIN_PROGRAM and last):
                        self.warn(st, 'empty string literal "" (SPEC rule 13: only as the last line of STA431)')
                    break
        if not has_return and self.name not in (MAIN_PROGRAM,):
            self.warn(len(self.stmts) and self.stmts[-1].line or 0,
                      "no Return statement (subprograms should end with Return)")


def label_of_name(toks):
    """Program name after a prgm token (letters/digits/θ, 1-8 chars)."""
    s = ""
    for t in toks:
        c = NAMECH.get(t.bits)
        if c is None:
            return None
        s += c
    return s if 1 <= len(s) <= 8 else None


# ------------------------------------------------------------------------------------------ API
def lint_source(name, text):
    return Linter(name, text).run()


def lint_file(path):
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path, encoding="utf-8") as f:
        return lint_source(name, f.read())


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    n_err = 0
    for path in tibuild.iter_sources(argv[1:]):
        name = os.path.splitext(os.path.basename(path))[0]
        msgs = lint_file(path)
        for m in msgs:
            print(m)
        e = sum(m.startswith("ERROR") for m in msgs)
        w = sum(m.startswith("WARN") for m in msgs)
        n_err += e
        print(f"{name}: {e} errors, {w} warnings")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
