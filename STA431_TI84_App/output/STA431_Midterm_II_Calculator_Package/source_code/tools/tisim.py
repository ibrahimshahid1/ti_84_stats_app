#!/usr/bin/env python3
"""
tisim.py - off-device TI-84 Plus CE TI-BASIC simulator (token-stream interpreter).

Programs are loaded from <src_dir>/NAME.txt, cleaned with tibuild.clean_source, tokenized with
tibuild.tokenize (tivars "smart" mode, exactly what the .8xp contains) and decoded back into tivars
TIToken objects.  The interpreter works on the TOKEN STREAM, so tokenization mistakes behave like on the
calculator: a lowercase letter outside a string is a text token (ERR:SYNTAX), "-1" at the start of an
expression is a binary minus (ERR:SYNTAX), "Pause" without its trailing space is P*a*u*s*e, etc.

Numbers are 14-significant-digit decimals (like the TI's BCD floats); display/toString use TI Normal/Float
formatting (max 10 digits, ".5", "⁻3", "1.5ᴇ12", "1ᴇ⁻4").

-------------------------------------------------------------------------------------------------------
PYTHON API
-------------------------------------------------------------------------------------------------------
    import sys; sys.path.insert(0, "<ROOT>/tools")
    from tisim import Sim, TIError

    sim = Sim("src")                     # or Sim(["tmpdir", "src"])  (searched in order)
    sim.add_program("TDRV", "1/7→W\\nprgmSTAFMT")   # optional in-memory program (source text)
    res = sim.run("STACNT",
                  actions=[{"menu": 1}, {"input": "5"}, {"input": "2"}],
                  max_steps=2_000_000,
                  init_vars={"W": 0.25, "Str1": "ABC", "ʟRVX": [1, 2], "Y9": "X²"})   # optional

  Actions (consumed in order):
    {"menu": n}      answer the next Menu( with item n (1-based). Error if the next action is not a menu
                     action or n is out of range.
    {"menu": "TEXT"} answer the next Menu( with the item whose stripped text equals TEXT exactly; if none
                     does, the ONE item whose stripped text starts with TEXT. No match, or several
                     exact/prefix matches, raises SIM:ACTION listing the menu's items. Prefer text in tests
                     ({"menu": "BACK"}) so menus can grow without breaking hard-coded positions.
    {"input": "txt"} answer the next Input/Prompt. txt is what the user TYPES, tokenized like keypresses
                     (tivars expression mode): "3/16", "⁻1" (negation key!), "{1,2,3}", "1-𝑒^(⁻2X)",
                     "5ᴇ⁻3", "pi". Real vars: typed text is evaluated (so "-1" is ERR:SYNTAX, like the TI).
                     List vars: must evaluate to a list. String vars: the typed tokens are stored as text.
                     Numbers are accepted too: {"input": 5}.
    {"key": code}    returned by the next getKey (105 ENTER, 45 CLEAR, 24 LEFT, 26 RIGHT, 25 UP, 34 DOWN;
                     {"key": 0} = no key pressed this poll).
    getKey when the head action is NOT a key action returns 105 (ENTER) without consuming it.
    getKey / Menu / Input with an EMPTY queue -> run stops, ended_reason "out_of_actions"
    (a snapshot of the screen waiting for that action is still recorded).
    Pause does not consume actions: it records a snapshot and continues (ENTER pressed).

  Result object:
    res.screens      list of snapshots (dicts):
                       "event": "pause" | "menu" | "input" | "getkey" | "end" | "error" | "out_of_actions"
                       "rows":  10 strings of exactly 26 chars (what the home screen shows; for "menu"
                                it is the menu screen: title row + "1:ITEM" rows)
                       "program", "line": where it happened (line = line number in src/NAME.txt)
                       "stack": program names on the prgm call stack, outermost first
                       "menu":  {"title", "items", "labels"}            (event == "menu")
                       "prompt", "var"                                   (event == "input")
                       "key"                                             (event == "getkey")
                       "response": what the action queue answered (menu choice / typed text / key)
    res.text         all snapshots rendered as boxed 26x10 screens with event labels (grep this)
    res.vars         final variables with floats:  {"reals": {"A": 1.5, ...}, "strings": {"Str9": "3/4"},
                       "lists": {"CNA": [..], "L₁": [..]}, "equations": {"Y9": "X²"}, "Ans": ...}
                     named lists are keyed WITHOUT the ʟ; built-in lists as "L₁".."L₆".
    res.var(name)    convenience: res.var("A"), res.var("Str9"), res.var("ʟCNA"), res.var("Y9")
    res.raw_vars     same structure as vars but with exact Decimal values
    res.leaks        number of block frames (If-Then/For/While/Repeat) abandoned by Goto/Menu( (must be 0)
    res.error        None or e.g. "ERR:DOMAIN at STACNT line 57: <source line> -- <detail>"
                     simulator/action problems start with "SIM:" (e.g. "SIM:ACTION ...")
    res.ended_reason "return" | "stop" | "end" | "out_of_actions" | "error" | "max_steps"
    res.warnings     list of display-policy warnings (Disp string > 26, Output wraps/clipped, ...)
    res.steps        statements executed;   res.coverage  {program: sorted list of executed lines}
    res.screen(i)    snapshot i rendered as text; res.find("TEXT") -> indices of snapshots containing TEXT
    res.all_text_rows() -> every row of every snapshot (list of str)

  Other helpers:
    fmt_num(Decimal) -> TI display string;   Sim(...).eval("5 nCr 2*2") -> value (Decimal/list/str)

-------------------------------------------------------------------------------------------------------
CLI
-------------------------------------------------------------------------------------------------------
    $PY tools/tisim.py run src STACNT --actions '[{"menu":1},{"input":"5"}]' [--max-steps N] [--vars]
    $PY tools/tisim.py eval "5 nCr 2*2"          (evaluate one expression, prints TI-formatted value)

-------------------------------------------------------------------------------------------------------
FAITHFULNESS NOTES / LIMITATIONS
-------------------------------------------------------------------------------------------------------
 * If without Then controls exactly one statement; For( evaluates bounds/step once, runs 0 times if
   start>end, var ends at last+step; While pre-test, Repeat post-test; End pops the innermost frame;
   skipping counts Then/For(/While/Repeat vs End; Goto searches labels from the top (ERR:LABEL).
 * Goto/Menu( out of open blocks leaves the frames on the stack (like the TI: a later End may use them)
   and counts them in res.leaks; >2000 open frames -> ERR:MEMORY.
 * Stricter than the calculator on purpose: closing ) and " are REQUIRED (SPEC rule 8).
 * Factorial: integers 0..69 and half-integers (like the TI); 70! -> ERR:OVERFLOW; others ERR:DOMAIN.
 * fnInt uses adaptive Gauss-Kronrod (7/15) to ~1e-10 relative (more accurate than the TI's 1e-5 default);
   nDeriv symmetric difference with h=1ᴇ⁻3 in TI decimal arithmetic.
 * Unsupported (raise SIM:UNSUPPORTED): graphing/drawing commands, matrices, complex numbers, Fix/Sci
   modes, stat commands, Send/Get, Asm.  Mode tokens Normal/Float/Radian/Func/FnOn/FnOff/... are no-ops.
 * Menu( renders as title row + "n:ITEM" rows in the snapshot; the home screen is left unchanged.
 * At program end (not Stop/Return/error) the TI shows "Done" or the value of a final bare expression;
   the "end" snapshot reproduces that.
 * One Sim may be run many times: every run() gets fresh variables/screen, and compiled statements are
   rebuilt per run (they used to capture the first run's interpreter -> stale variables; fixed).
   add_program(name, text) always replaces an earlier program of that name (cache dropped).
"""
import json
import math
import os
import random
import sys
from collections import deque
from decimal import (Context, Decimal, DivisionByZero, InvalidOperation, Overflow, ROUND_FLOOR,
                     ROUND_HALF_UP, ROUND_DOWN, localcontext)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tibuild  # noqa: E402

from tivars.models import TI_84PCE  # noqa: E402
from tivars.tokenizer import decode, encode  # noqa: E402

TOKENS = TI_84PCE.tokens.bytes      # bits -> TIToken
TRIE = TI_84PCE.tokens.tries[None]

ROWS, COLS = 10, 26
MAX_FRAMES = 2000
MAX_CALL_DEPTH = 60

# ------------------------------------------------------------------------------------ numbers
CTX = Context(prec=14, rounding=ROUND_HALF_UP, Emax=99, Emin=-99,
              traps=[Overflow, DivisionByZero, InvalidOperation])
FMT10 = Context(prec=10, rounding=ROUND_HALF_UP, Emax=999, Emin=-999)
WIDE = Context(prec=40, rounding=ROUND_HALF_UP, Emax=999, Emin=-999)
ZERO = Decimal(0)
ONE = Decimal(1)
PI = CTX.create_decimal("3.1415926535898")
EE = CTX.create_decimal("2.7182818284590")


def D(x):
    """Python number -> 14-digit Decimal."""
    if isinstance(x, Decimal):
        return CTX.plus(x)
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            raise TIError("OVERFLOW", "non-finite value")
        return CTX.create_decimal_from_float(x)
    return CTX.create_decimal(x)


def _fixed(d):
    s = format(d.normalize(WIDE), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    return s or "0"


def fmt_num(x):
    """TI-84 Normal/Float display format (also used by toString)."""
    if x == 0:
        return "0"
    neg = x < 0
    a = abs(x)
    r10 = FMT10.plus(a)
    e = r10.adjusted()
    if e >= 10 or e < -3:
        m = r10.scaleb(-e, WIDE)
        s = _fixed(m) + "ᴇ" + (("⁻" + str(-e)) if e < 0 else str(e))
    else:
        places = 10 - (e + 1) if e >= 0 else 10
        v = a.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP, context=WIDE)
        s = _fixed(v)
    return ("⁻" if neg else "") + s


# ------------------------------------------------------------------------------------ errors
class TIError(Exception):
    """A calculator error (kind = 'SYNTAX', 'DOMAIN', ...) or a simulator problem (sim=True)."""

    def __init__(self, kind, detail="", sim=False):
        super().__init__(kind, detail)
        self.kind = kind
        self.detail = detail
        self.sim = sim

    @property
    def label(self):
        return ("SIM:" if self.sim else "ERR:") + self.kind

    def __str__(self):
        return self.label + (f" ({self.detail})" if self.detail else "")


class _Stop(Exception):
    pass


class _Return(Exception):
    pass


class _OutOfActions(Exception):
    pass


class _MaxSteps(Exception):
    pass


# ------------------------------------------------------------------------------------ token bits
def B(h):
    return bytes.fromhex(h)


NEWLINE, COLON, QUOTE, STORE, COMMA = B("3f"), B("3e"), B("2a"), B("04"), B("2b")
LPAREN, RPAREN, LBRACE, RBRACE = B("10"), B("11"), B("08"), B("09")
NEG, SUB, ADD, MUL, DIV, POW = B("b0"), B("71"), B("70"), B("82"), B("83"), B("f0")
EXP_E, DOT = B("3b"), B("3a")
NCR, NPR = B("95"), B("94")
AND, OR, XOR = B("40"), B("3c"), B("3d")
EQ, LT, GT, LE, GE, NE = B("6a"), B("6b"), B("6c"), B("6d"), B("6e"), B("6f")
SQ, CUBE, INV, FACT = B("0d"), B("0f"), B("0c"), B("2d")
ANS, PI_T, E_T, GETKEY, RAND = B("72"), B("ac"), B("bb31"), B("ad"), B("ab")
LIST_L = B("eb")
THETA = B("5b")

IF, THEN, ELSE, WHILE, REPEAT, FOR, END = (B(h) for h in ("ce", "cf", "d0", "d1", "d2", "d3", "d4"))
RETURN, LBL, GOTO, PAUSE, STOP = (B(h) for h in ("d5", "d6", "d7", "d8", "d9"))
INPUT, PROMPT, DISP, OUTPUT, CLRHOME = (B(h) for h in ("dc", "dd", "de", "e0", "e1"))
FILL, SORTA, SORTD, MENU, PRGM = B("e2"), B("e3"), B("e4"), B("e6"), B("5f")
DELVAR, CLRLIST, FNON, FNOFF = B("bb54"), B("fa"), B("96"), B("97")
DIM = B("b5")

OPENERS = {THEN, WHILE, REPEAT, FOR}
DIGITS = {bytes([0x30 + i]): str(i) for i in range(10)}
LETTERS = {bytes([0x41 + i]): chr(0x41 + i) for i in range(26)}
LETTERS[THETA] = "θ"
NAME_CHARS = dict(LETTERS)
NAME_CHARS.update(DIGITS)
STRVARS = {B("aa0%d" % i): "Str%d" % ((i + 1) % 10) for i in range(10)}
YVARS = {B("5e1%d" % i): "Y%d" % ((i + 1) % 10) for i in range(10)}
BUILTIN_LISTS = {B("5d0%d" % i): "L" + "₁₂₃₄₅₆"[i] for i in range(6)}
LOWER_TOKENS = {bytes([0xBB, b]) for b in range(0xB0, 0xCB)}
STAT_LOOKALIKES = tibuild.LOOKALIKE_LOWER
NOOP_CMDS = {B(h) for h in ("66", "69", "64", "65", "76", "bb4d", "75", "74", "85", "ea", "7e09",
                            "7e0b", "7e0d", "fb", "e9", "bb50", "bb51")}
KEY_NAMES = {105: "ENTER", 45: "CLEAR", 24: "LEFT", 26: "RIGHT", 25: "UP", 34: "DOWN", 0: "none"}


def tok(bits):
    return TOKENS[bits]


def tdisp(t):
    d = t.display
    return "'" if d == "\\'" else d


# ------------------------------------------------------------------------------------ strings
class TIStr:
    """A TI string: a sequence of tokens (length( counts tokens, sub( slices tokens)."""
    __slots__ = ("toks",)

    def __init__(self, toks):
        self.toks = tuple(toks)

    @property
    def text(self):
        return "".join(tdisp(t) for t in self.toks)

    def key(self):
        return tuple(t.bits for t in self.toks)

    def __eq__(self, other):
        return isinstance(other, TIStr) and self.key() == other.key()

    def __hash__(self):
        return hash(self.key())

    def __repr__(self):
        return f"TIStr({self.text!r})"


_CHAR_TOK = {"⁻": NEG, "ᴇ": EXP_E, ".": DOT, "{": LBRACE, "}": RBRACE, ",": COMMA, " ": B("29")}
for _b, _c in DIGITS.items():
    _CHAR_TOK[_c] = _b


def str_from_plain(text):
    """Text made only of number-format chars -> TIStr (used by toString)."""
    return TIStr(tok(_CHAR_TOK[c]) for c in text)


def str_from_text(text):
    """Arbitrary text -> TIStr tokenized as string contents (minimal munch)."""
    if not text:
        return TIStr(())
    data, _ = encode(text, trie=TRIE, mode="string")
    return TIStr(decode(data)[0])


def split_upper_words(toks):
    """Keypresses never produce multi-letter UPPERCASE tokens (RED, LEFT, AUTO...) - split them."""
    out = []
    for t in toks:
        d = t.display
        if len(d) > 1 and d.isalpha() and d.isupper() and all("A" <= c <= "Z" for c in d):
            out.extend(tok(bytes([ord(c)])) for c in d)
        else:
            out.append(t)
    return out


def typed_tokens(text):
    """What the user types at an Input prompt -> tokens (expression-mode tokenization)."""
    text = str(text)
    if text == "":
        return []
    try:
        data, _ = encode(text, trie=TRIE, mode="smart")
    except ValueError as e:
        raise TIError("ACTION", f"cannot type {text!r}: {e}", sim=True)
    toks, _ = decode(data)
    return split_upper_words(toks)


def value_text(v):
    if isinstance(v, Decimal):
        return fmt_num(v)
    if isinstance(v, list):
        return "{" + " ".join(fmt_num(x) for x in v) + "}"
    if isinstance(v, TIStr):
        return v.text
    return str(v)


def describe_token(t):
    b = t.bits
    d = tdisp(t)
    if b in LOWER_TOKENS:
        return f"lowercase letter '{d}' outside a string (lowercase is text only)"
    if b in STAT_LOOKALIKES:
        return f"statistics variable '{d}' (looks like a lowercase letter)"
    if b == SUB:
        return "binary minus '-' where an operand is expected (use negation '⁻')"
    if b == NEWLINE:
        return "end of line"
    return f"unexpected token '{d}'"


# ------------------------------------------------------------------------------------ programs
class Stmt:
    __slots__ = ("toks", "bits", "kind", "line", "src", "idx", "cache")

    def __init__(self, toks, line, src, idx):
        self.toks = toks
        self.bits = [t.bits for t in toks]
        self.kind = self.bits[0] if toks else None
        self.line = line
        self.src = src
        self.idx = idx
        self.cache = None


def split_statements(toks, line_map, src_lines):
    """Split a token list into statements at ':' and newlines (not inside strings)."""
    stmts, cur, line_no, in_str = [], [], 0, False

    def flush():
        ln = line_map[line_no] if line_no < len(line_map) else line_no + 1
        src = src_lines[ln - 1].strip() if 0 < ln <= len(src_lines) else ""
        stmts.append(Stmt(list(cur), ln, src, len(stmts)))
        cur.clear()

    for t in toks:
        b = t.bits
        if b == NEWLINE:
            flush()
            line_no += 1
            in_str = False
            continue
        if in_str:
            if b == QUOTE or b == STORE:
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


class Program:
    def __init__(self, name, source_text, path=None):
        self.name = name
        self.path = path
        src_lines = source_text.splitlines()
        line_map = [i + 1 for i, raw in enumerate(src_lines)
                    if raw.strip() and not raw.strip().startswith("//")]
        clean = tibuild.clean_source(source_text)
        self.load_error = None
        try:
            toks = tibuild.token_list(clean)
        except ValueError as e:
            toks = []
            self.load_error = TIError("SYNTAX", f"tokenization failed: {e}")
        self.stmts = split_statements(toks, line_map, src_lines)
        self.labels = {}
        for st in self.stmts:
            if st.kind == LBL:
                nm = label_name(st.toks[1:])
                if nm and nm not in self.labels:
                    self.labels[nm] = st.idx
        # static block ancestors (for leak accounting)
        self.parents = []
        stack = []
        for st in self.stmts:
            self.parents.append(tuple(stack))
            if st.kind in OPENERS:
                stack.append(st.idx)
            elif st.kind == END and stack:
                stack.pop()


def label_name(toks):
    s = ""
    for t in toks:
        c = NAME_CHARS.get(t.bits)
        if c is None:
            return None
        s += c
    return s if 1 <= len(s) <= 2 else None


# ------------------------------------------------------------------------------------ screen
class Screen:
    def __init__(self):
        self.clear()

    def clear(self):
        self.rows = [[" "] * COLS for _ in range(ROWS)]
        self.cur = 0          # row index of the next Disp line

    def scroll(self):
        self.rows.pop(0)
        self.rows.append([" "] * COLS)

    def newline_row(self):
        if self.cur >= ROWS:
            self.scroll()
            self.cur = ROWS - 1
        r = self.cur
        self.cur += 1
        return r

    def put_line(self, text, right=False):
        """Disp one item: returns True if text had to be truncated."""
        r = self.newline_row()
        trunc = len(text) > COLS
        if trunc:
            text = text[:COLS - 1] + "…" if right else text[:COLS]
        self.rows[r] = [" "] * COLS
        start = COLS - len(text) if right else 0
        for i, ch in enumerate(text):
            self.rows[r][start + i] = ch
        return trunc

    def write_at(self, r, c, text):
        """Output( semantics: write from (r,c) (0-based), wrapping; returns (wrapped, clipped)."""
        wrapped = clipped = False
        for ch in text:
            if c >= COLS:
                c = 0
                r += 1
                wrapped = True
            if r >= ROWS:
                clipped = True
                break
            self.rows[r][c] = ch
            c += 1
        return wrapped, clipped

    def write_flow(self, text):
        """Input prompt / typed text: write at cursor row, wrapping onto following rows."""
        r = self.newline_row()
        self.rows[r] = [" "] * COLS
        c = 0
        for ch in text:
            if c >= COLS:
                r = self.newline_row()
                self.rows[r] = [" "] * COLS
                c = 0
            self.rows[r][c] = ch
            c += 1
        return r, c

    def snapshot(self):
        return ["".join(r) for r in self.rows]


def menu_rows(title, items):
    rows = [title[:COLS].ljust(COLS)]
    for i, it in enumerate(items, 1):
        rows.append(f"{i}:{it}"[:COLS].ljust(COLS))
    while len(rows) < ROWS:
        rows.append(" " * COLS)
    return rows[:ROWS]


# ------------------------------------------------------------------------------------ math helpers
def is_int(x):
    return x == x.to_integral_value()


def need_real(v, what="value"):
    if isinstance(v, Decimal):
        return v
    raise TIError("DATA TYPE", f"{what} must be a real number, got {type_name(v)}")


def need_list(v, what="value"):
    if isinstance(v, list):
        return v
    raise TIError("DATA TYPE", f"{what} must be a list, got {type_name(v)}")


def need_str(v, what="value"):
    if isinstance(v, TIStr):
        return v
    raise TIError("DATA TYPE", f"{what} must be a string, got {type_name(v)}")


def need_int(v, what="value"):
    v = need_real(v, what)
    if not is_int(v):
        raise TIError("DOMAIN", f"{what} must be an integer, got {fmt_num(v)}")
    return int(v)


def type_name(v):
    return {Decimal: "real", list: "list", TIStr: "string"}.get(type(v), type(v).__name__)


def elem1(f, v):
    if isinstance(v, Decimal):
        return f(v)
    if isinstance(v, list):
        return [f(x) for x in v]
    raise TIError("DATA TYPE", f"expected number or list, got {type_name(v)}")


def elem2(f, a, b):
    ta, tb = type(a), type(b)
    if ta is Decimal and tb is Decimal:
        return f(a, b)
    if ta is list and tb is list:
        if len(a) != len(b):
            raise TIError("DIM MISMATCH", f"lists of dim {len(a)} and {len(b)}")
        return [f(x, y) for x, y in zip(a, b)]
    if ta is list and tb is Decimal:
        return [f(x, b) for x in a]
    if ta is Decimal and tb is list:
        return [f(a, y) for y in b]
    raise TIError("DATA TYPE", f"cannot combine {type_name(a)} and {type_name(b)}")


def f_add(a, b):
    if isinstance(a, TIStr) or isinstance(b, TIStr):
        if isinstance(a, TIStr) and isinstance(b, TIStr):
            return TIStr(a.toks + b.toks)
        raise TIError("DATA TYPE", "string + non-string")
    return elem2(lambda x, y: x + y, a, b)


def f_sub(a, b):
    return elem2(lambda x, y: x - y, a, b)


def f_mul(a, b):
    return elem2(lambda x, y: x * y, a, b)


def _div(x, y):
    if y == 0:
        raise TIError("DIVIDE BY 0")
    return x / y


def f_div(a, b):
    return elem2(_div, a, b)


def _odd_root_exponent(y):
    """If y == p/q with q odd (q<=999), return (p, q); else None."""
    for q in range(1, 1000, 2):
        p = y * q
        pr = p.to_integral_value()
        if abs(p - pr) <= Decimal("1e-11") * q:
            return int(pr), q
    return None


def _pow(x, y):
    if x == 0:
        if y > 0:
            return ZERO
        if y == 0:
            raise TIError("DOMAIN", "0^0")
        raise TIError("DIVIDE BY 0", "0^negative")
    if is_int(y):
        n = int(y)
        if abs(n) > 100000:
            r = Decimal(abs(x)).ln(WIDE) * n
            if r > 231:
                raise TIError("OVERFLOW")
            if r < -231:
                return ZERO
        return CTX.power(x, n)
    if x < 0:
        pq = _odd_root_exponent(y)
        if pq is None:
            raise TIError("NONREAL ANS", f"({fmt_num(x)})^{fmt_num(y)}")
        p, q = pq
        mag = CTX.power(-x, y)
        return -mag if p % 2 else mag
    return CTX.power(x, y)


def f_pow(a, b):
    return elem2(_pow, a, b)


def _fact(x):
    if is_int(x):
        if x < 0:
            raise TIError("DOMAIN", f"{fmt_num(x)}!")
        if x > 69:
            raise TIError("OVERFLOW", f"{fmt_num(x)}! (69! is the largest)")
        return D(math.factorial(int(x)))
    if is_int(x * 2) and x >= Decimal("-0.5"):
        if x > 69:
            raise TIError("OVERFLOW", f"{fmt_num(x)}!")
        return D(math.gamma(float(x) + 1.0))
    raise TIError("DOMAIN", f"{fmt_num(x)}! (factorial needs an integer)")


def _comb_like(n, r, perm):
    if not is_int(n) or not is_int(r):
        raise TIError("DOMAIN", "nCr/nPr need integers")
    n, r = int(n), int(r)
    if n < 0 or r < 0:
        raise TIError("DOMAIN", "nCr/nPr need non-negative integers")
    if r > n:
        return ZERO
    k = min(r, n - r)
    if (k > 3000 or n > 10 ** 7) and not perm:
        lg = math.lgamma(n + 1) - math.lgamma(r + 1) - math.lgamma(n - r + 1)
        if lg > 230.3:
            raise TIError("OVERFLOW")
    if perm and (r > 3000 or n > 10 ** 7):
        lg = math.lgamma(n + 1) - math.lgamma(n - r + 1)
        if lg > 230.3:
            raise TIError("OVERFLOW")
    v = math.perm(n, r) if perm else math.comb(n, r)
    return D(v)


def f_ncr(a, b):
    return elem2(lambda x, y: _comb_like(x, y, False), a, b)


def f_npr(a, b):
    return elem2(lambda x, y: _comb_like(x, y, True), a, b)


def _cmp(op):
    def f(a, b):
        if isinstance(a, TIStr) or isinstance(b, TIStr):
            if op in ("=", "≠") and isinstance(a, TIStr) and isinstance(b, TIStr):
                eq = a == b
                return ONE if (eq if op == "=" else not eq) else ZERO
            raise TIError("DATA TYPE", f"string comparison with '{op}'")
        fn = {"=": lambda x, y: x == y, "≠": lambda x, y: x != y, "<": lambda x, y: x < y,
              ">": lambda x, y: x > y, "≤": lambda x, y: x <= y, "≥": lambda x, y: x >= y}[op]
        return elem2(lambda x, y: ONE if fn(x, y) else ZERO, a, b)
    return f


def truth(v, what="condition"):
    if isinstance(v, Decimal):
        return v != 0
    raise TIError("DATA TYPE", f"{what} must be a real number, got {type_name(v)}")


def _sqrt(x):
    if x < 0:
        raise TIError("NONREAL ANS", f"√({fmt_num(x)})")
    return x.sqrt(CTX)


def _ln(x):
    if x < 0:
        raise TIError("NONREAL ANS", f"ln({fmt_num(x)})")
    if x == 0:
        raise TIError("DOMAIN", "ln(0)")
    return x.ln(CTX)


def _log(x):
    if x < 0:
        raise TIError("NONREAL ANS", f"log({fmt_num(x)})")
    if x == 0:
        raise TIError("DOMAIN", "log(0)")
    return x.log10(CTX)


def _exp(x):
    if x > 230:
        raise TIError("OVERFLOW")
    if x < -230:
        return ZERO
    return x.exp(CTX)


def _tenpow(x):
    return _pow(Decimal(10), x)


def _round(x, d=9):
    if d < 0 or d > 9:
        raise TIError("DOMAIN", "round( digits must be 0-9")
    if x == 0:
        return x
    if x.adjusted() + d + 1 > 14:
        return x
    return x.quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP, context=WIDE)


def _int(x):
    return x.to_integral_value(rounding=ROUND_FLOOR)


def _ipart(x):
    return x.to_integral_value(rounding=ROUND_DOWN)


def _fpart(x):
    return x - _ipart(x)


def _trig(fn):
    return lambda x: D(fn(float(x)))


# ------------------------------------------------------------------------------------ parser
class Parser:
    """Recursive-descent TI expression parser producing closures (fn() -> value)."""

    def __init__(self, it, toks, start=0, end=None):
        self.it = it
        self.t = toks
        self.b = [x.bits for x in toks]
        self.i = start
        self.n = len(toks) if end is None else end

    # --- token helpers
    def peek(self, k=0):
        j = self.i + k
        return self.b[j] if j < self.n else None

    def next(self):
        b = self.b[self.i]
        self.i += 1
        return b

    def at_end(self):
        return self.i >= self.n

    def fail(self, msg=None):
        if msg is None:
            msg = describe_token(self.t[self.i]) if self.i < self.n else "unexpected end of expression"
        raise TIError("SYNTAX", msg)

    def expect(self, bits, what):
        if self.peek() != bits:
            self.fail(f"expected {what}" + (f", found '{tdisp(self.t[self.i])}'" if not self.at_end() else
                                            " (missing closing token)"))
        self.i += 1

    def done(self):
        if not self.at_end():
            self.fail()

    # --- grammar
    def expr(self):
        return self.p_or()

    def p_or(self):
        left = self.p_and()
        while self.peek() in (OR, XOR):
            op = self.next()
            right = self.p_and()
            if op == OR:
                left = (lambda l, r: lambda: elem2(lambda x, y: ONE if (x != 0 or y != 0) else ZERO,
                                                   l(), r()))(left, right)
            else:
                left = (lambda l, r: lambda: elem2(lambda x, y: ONE if ((x != 0) != (y != 0)) else ZERO,
                                                   l(), r()))(left, right)
        return left

    def p_and(self):
        left = self.p_rel()
        while self.peek() == AND:
            self.next()
            right = self.p_rel()
            left = (lambda l, r: lambda: elem2(lambda x, y: ONE if (x != 0 and y != 0) else ZERO,
                                               l(), r()))(left, right)
        return left

    REL = {EQ: "=", NE: "≠", LT: "<", GT: ">", LE: "≤", GE: "≥"}

    def p_rel(self):
        left = self.p_add()
        while self.peek() in self.REL:
            f = _cmp(self.REL[self.next()])
            right = self.p_add()
            left = (lambda l, r, f: lambda: f(l(), r()))(left, right, f)
        return left

    def p_add(self):
        left = self.p_mul()
        while self.peek() in (ADD, SUB):
            op = self.next()
            right = self.p_mul()
            f = f_add if op == ADD else f_sub
            left = (lambda l, r, f: lambda: f(l(), r()))(left, right, f)
        return left

    def p_mul(self):
        left = self.p_ncr()
        while True:
            p = self.peek()
            if p in (MUL, DIV):
                self.next()
                right = self.p_ncr()
                f = f_mul if p == MUL else f_div
            elif p is not None and self.starts_operand(p):
                right = self.p_ncr()          # implied multiplication
                f = f_mul
            else:
                return left
            left = (lambda l, r, f: lambda: f(l(), r()))(left, right, f)

    def p_ncr(self):
        left = self.p_neg()
        while self.peek() in (NCR, NPR):
            op = self.next()
            right = self.p_neg()
            f = f_ncr if op == NCR else f_npr
            left = (lambda l, r, f: lambda: f(l(), r()))(left, right, f)
        return left

    def p_neg(self):
        if self.peek() == NEG:
            self.next()
            inner = self.p_neg()
            return lambda: elem1(lambda x: -x, inner())
        return self.p_pow()

    def p_pow_rhs(self):
        if self.peek() == NEG:
            self.next()
            inner = self.p_pow_rhs()
            return lambda: elem1(lambda x: -x, inner())
        return self.p_post()

    def p_pow(self):
        left = self.p_post()
        while self.peek() == POW:
            self.next()
            right = self.p_pow_rhs()
            left = (lambda l, r: lambda: f_pow(l(), r()))(left, right)
        return left

    POSTFIX = {SQ: lambda v: elem1(lambda x: x * x, v),
               CUBE: lambda v: elem1(lambda x: x * x * x, v),
               INV: lambda v: elem1(lambda x: _div(ONE, x), v),
               FACT: lambda v: elem1(_fact, v)}

    def p_post(self):
        a = self.p_atom()
        while self.peek() in self.POSTFIX:
            f = self.POSTFIX[self.next()]
            a = (lambda a, f: lambda: f(a()))(a, f)
        return a

    def starts_operand(self, b):
        return (b in DIGITS or b in (DOT, EXP_E, LPAREN, LBRACE, QUOTE, PI_T, E_T, ANS, GETKEY, RAND,
                                     NEG, LIST_L)
                or b in LETTERS or b in STRVARS or b in YVARS or b in BUILTIN_LISTS or b in FUNCS)

    # --- atoms
    def p_atom(self):
        if self.at_end():
            self.fail("expression expected")
        b = self.peek()
        it = self.it
        if b in DIGITS or b == DOT or b == EXP_E:
            v = self.number()
            return lambda: v
        if b in LETTERS:
            self.next()
            name = LETTERS[b]
            reals = it.reals
            return lambda: reals.get(name, ZERO)
        if b == ANS:
            self.next()
            return lambda: it.ans
        if b == PI_T:
            self.next()
            return lambda: PI
        if b == E_T:
            self.next()
            return lambda: EE
        if b == GETKEY:
            self.next()
            return it.getkey
        if b == RAND:
            self.next()
            return lambda: D(it.rng.random())
        if b in STRVARS:
            self.next()
            name = STRVARS[b]
            return lambda: it.get_str(name)
        if b == QUOTE:
            s = self.string_literal()
            return lambda: s
        if b == LBRACE:
            return self.list_literal()
        if b == LIST_L or b in BUILTIN_LISTS:
            name = self.list_name()
            if self.peek() == LPAREN:
                self.next()
                idx = self.expr()
                self.expect(RPAREN, "')' after list index")
                return lambda: it.list_elem(name, idx())
            return lambda: list(it.get_list(name))
        if b in YVARS:
            self.next()
            name = YVARS[b]
            if self.peek() == LPAREN:
                self.next()
                arg = self.expr()
                self.expect(RPAREN, "')'")
                return lambda: it.eval_yvar(name, arg())
            return lambda: it.eval_yvar(name, None)
        if b == LPAREN:
            self.next()
            inner = self.expr()
            self.expect(RPAREN, "')'")
            return inner
        if b in FUNCS:
            self.next()
            return FUNCS[b](self)
        self.fail()

    def number(self):
        s = ""
        while self.peek() in DIGITS or self.peek() == DOT:
            s += "." if self.next() == DOT else DIGITS[self.b[self.i - 1]]
        if s.count(".") > 1 or s == ".":
            self.fail(f"malformed number '{s}'")
        if self.peek() == EXP_E:
            self.next()
            e = ""
            if self.peek() == NEG:
                self.next()
                e = "-"
            if self.peek() not in DIGITS:
                self.fail("digits expected after ᴇ")
            while self.peek() in DIGITS:
                e += DIGITS[self.next()]
            if len(e.lstrip("-")) > 2:
                self.fail("exponent too long")
            s = (s or "1") + "E" + e
        try:
            return CTX.create_decimal(s)
        except Overflow:
            raise TIError("OVERFLOW", s)

    def string_literal(self):
        self.expect(QUOTE, '"')
        start = self.i
        while not self.at_end() and self.peek() != QUOTE and self.peek() != STORE:
            self.i += 1
        toks = self.t[start:self.i]
        if self.peek() != QUOTE:
            self.fail('unclosed string literal (missing closing ")')
        self.i += 1
        return TIStr(toks)

    def list_literal(self):
        self.expect(LBRACE, "{")
        items = [self.expr()]
        while self.peek() == COMMA:
            self.next()
            items.append(self.expr())
        self.expect(RBRACE, "'}'")

        def f():
            out = []
            for g in items:
                out.append(need_real(g(), "list element"))
            return out
        return f

    def list_name(self):
        b = self.next()
        if b in BUILTIN_LISTS:
            return BUILTIN_LISTS[b]
        name = ""
        while self.peek() in NAME_CHARS and len(name) < 5:
            c = NAME_CHARS[self.peek()]
            if not name and c.isdigit():
                break
            name += c
            self.i += 1
        if not name:
            self.fail("list name expected after ʟ")
        return name

    def args(self, lo, hi, fname):
        """Parse comma-separated args up to ')'. Returns list of closures."""
        out = []
        if self.peek() == RPAREN:
            self.fail(f"{fname} needs arguments")
        out.append(self.expr())
        while self.peek() == COMMA:
            self.next()
            out.append(self.expr())
        self.expect(RPAREN, f"')' to close {fname}")
        if not (lo <= len(out) <= hi):
            raise TIError("ARGUMENT", f"{fname} takes {lo}-{hi} arguments, got {len(out)}")
        return out

    def var_arg(self, fname):
        b = self.peek()
        if b not in LETTERS:
            self.fail(f"{fname} needs a real variable name here")
        self.next()
        return LETTERS[b]

    # --- store target (after →)
    def target(self):
        b = self.peek()
        if b is None:
            self.fail("store target expected after →")
        if b in LETTERS:
            self.next()
            return ("real", LETTERS[b], None)
        if b in STRVARS:
            self.next()
            return ("str", STRVARS[b], None)
        if b in YVARS:
            self.next()
            return ("yvar", YVARS[b], None)
        if b == LIST_L or b in BUILTIN_LISTS:
            name = self.list_name()
            if self.peek() == LPAREN:
                self.next()
                idx = self.expr()
                self.expect(RPAREN, "')' after list index")
                return ("elem", name, idx)
            return ("list", name, None)
        if b == DIM:
            self.next()
            if not (self.peek() == LIST_L or self.peek() in BUILTIN_LISTS):
                self.fail("dim( store target must be a list")
            name = self.list_name()
            self.expect(RPAREN, "')' after dim(")
            return ("dim", name, None)
        if b == ANS:
            self.fail("cannot store to Ans")
        self.fail(f"invalid store target: {describe_token(self.t[self.i])}")


# ------------------------------------------------------------------------------------ functions
def _fn_simple(f, name, lo=1, hi=1):
    def build(p):
        a = p.args(lo, hi, name)
        if len(a) == 1:
            g = a[0]
            return lambda: elem1(f, g())
        return lambda: f(*[x() for x in a])
    return build


def _fn_round(p):
    a = p.args(1, 2, "round(")
    if len(a) == 1:
        g = a[0]
        return lambda: elem1(_round, g())
    g, h = a
    return lambda: elem1(lambda x: _round(x, need_int(h(), "round( digits")), g())


def _minmax(pick):
    def build(p):
        a = p.args(1, 2, "max(" if pick is max else "min(")

        def f():
            if len(a) == 1:
                v = need_list(a[0](), "single argument")
                if not v:
                    raise TIError("INVALID DIM", "empty list")
                return pick(v)
            return elem2(lambda x, y: pick(x, y), a[0](), a[1]())
        return f
    return build


def _fn_sum(p):
    a = p.args(1, 3, "sum(")

    def f():
        v = need_list(a[0](), "sum( argument")
        s_i = need_int(a[1](), "start") if len(a) > 1 else 1
        e_i = need_int(a[2](), "end") if len(a) > 2 else len(v)
        if s_i < 1 or e_i > len(v) or (len(a) > 1 and s_i > len(v)):
            raise TIError("INVALID DIM", "sum( range")
        tot = ZERO
        for x in v[s_i - 1:e_i]:
            tot = tot + x
        return tot
    return f


def _fn_prod(p):
    a = p.args(1, 1, "prod(")

    def f():
        tot = ONE
        for x in need_list(a[0](), "prod( argument"):
            tot = tot * x
        return tot
    return f


def _fn_mean(p):
    a = p.args(1, 1, "mean(")

    def f():
        v = need_list(a[0]())
        if not v:
            raise TIError("INVALID DIM", "empty list")
        tot = ZERO
        for x in v:
            tot += x
        return tot / len(v)
    return f


def _fn_median(p):
    a = p.args(1, 1, "median(")

    def f():
        v = sorted(need_list(a[0]()))
        if not v:
            raise TIError("INVALID DIM", "empty list")
        n = len(v)
        return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
    return f


def _fn_dim(p):
    a = p.args(1, 1, "dim(")

    def f():
        v = a[0]()
        if isinstance(v, list):
            return D(len(v))
        raise TIError("DATA TYPE", "dim( needs a list (use length( for strings)")
    return f


def _fn_cumsum(p):
    a = p.args(1, 1, "cumSum(")

    def f():
        out, tot = [], ZERO
        for x in need_list(a[0](), "cumSum( argument"):
            tot = tot + x
            out.append(tot)
        return out
    return f


def _fn_dlist(p):
    a = p.args(1, 1, "ΔList(")

    def f():
        v = need_list(a[0]())
        if len(v) < 2:
            raise TIError("INVALID DIM", "ΔList( needs dim ≥ 2")
        return [v[i + 1] - v[i] for i in range(len(v) - 1)]
    return f


def _fn_augment(p):
    a = p.args(2, 2, "augment(")
    return lambda: need_list(a[0](), "augment( arg 1") + need_list(a[1](), "augment( arg 2")


def _fn_seq(p):
    ex = p.expr()
    p.expect(COMMA, "',' in seq(")
    var = p.var_arg("seq(")
    rest = []
    while p.peek() == COMMA:
        p.next()
        rest.append(p.expr())
    p.expect(RPAREN, "')' to close seq(")
    if len(rest) not in (2, 3):
        raise TIError("ARGUMENT", "seq(expr,var,begin,end[,step])")
    it = p.it

    def f():
        a = need_real(rest[0](), "seq( begin")
        b = need_real(rest[1](), "seq( end")
        st = need_real(rest[2](), "seq( step") if len(rest) == 3 else ONE
        if st == 0:
            raise TIError("DOMAIN", "seq( step 0")
        n = int(_int((b - a) / st)) + 1
        if n < 0:
            n = 0
        if n > 999:
            raise TIError("INVALID DIM", "seq( would have more than 999 elements")
        saved = it.reals.get(var, ZERO)
        out = []
        try:
            for k in range(n):
                it.reals[var] = a + st * k
                out.append(need_real(ex(), "seq( element"))
        finally:
            it.reals[var] = saved
        return out
    return f


def _gk15(f, a, b):
    xgk = (0.991455371120812639206854697526329, 0.949107912342758524526189684047851,
           0.864864423359769072789712788640926, 0.741531185599394439863864773280788,
           0.586087235467691130294144845693013, 0.405845151377397166906606412076961,
           0.207784955007898467600689403773245, 0.0)
    wgk = (0.022935322010529224963732008058970, 0.063092092629978553290700663189204,
           0.104790010322250183839876322541518, 0.140653259715525918745189590510238,
           0.169004726639267902826583426598550, 0.190350578064785409913256402421014,
           0.204432940075298892414161999234649, 0.209482141084727828012999174891714)
    wg = (0.129484966168869693270611432679082, 0.279705391489276667901467771423780,
          0.381830050505118944950369775488975, 0.417959183673469387755102040816327)
    c, h = (a + b) / 2, (b - a) / 2
    fc = f(c)
    rk = fc * wgk[7]
    rg = fc * wg[3]
    for j in range(7):
        dx = h * xgk[j]
        f1, f2 = f(c - dx), f(c + dx)
        rk += wgk[j] * (f1 + f2)
        if j % 2 == 1:
            rg += wg[j // 2] * (f1 + f2)
    return rk * h, abs((rk - rg) * h)


def integrate(f, a, b, rel=1e-10, absol=1e-13, max_evals=200000):
    if a == b:
        return 0.0
    sign = 1.0
    if a > b:
        a, b, sign = b, a, -1.0
    # start with 8 panels so narrow features are not missed
    n0 = 8
    edges = [a + (b - a) * k / n0 for k in range(n0 + 1)]
    work = []
    total, err = 0.0, 0.0
    for k in range(n0):
        r, e = _gk15(f, edges[k], edges[k + 1])
        work.append((e, edges[k], edges[k + 1], r))
        total += r
        err += e
    evals = 15 * n0
    while err > max(absol, rel * abs(total)):
        if evals > max_evals:
            raise TIError("TOL NOT MET", "fnInt did not converge")
        work.sort(key=lambda w: w[0])
        e, lo, hi, r = work.pop()
        mid = (lo + hi) / 2
        r1, e1 = _gk15(f, lo, mid)
        r2, e2 = _gk15(f, mid, hi)
        evals += 30
        total += r1 + r2 - r
        err += e1 + e2 - e
        work.append((e1, lo, mid, r1))
        work.append((e2, mid, hi, r2))
        if hi - lo < 1e-12 * max(1.0, abs(lo)):
            break
    total = sum(w[3] for w in work)
    return sign * total


def _fn_fnint(p):
    ex = p.expr()
    p.expect(COMMA, "',' in fnInt(")
    var = p.var_arg("fnInt(")
    rest = []
    while p.peek() == COMMA:
        p.next()
        rest.append(p.expr())
    p.expect(RPAREN, "')' to close fnInt(")
    if len(rest) not in (2, 3):
        raise TIError("ARGUMENT", "fnInt(expr,var,lower,upper[,tol])")
    it = p.it

    def f():
        a = float(need_real(rest[0](), "fnInt( lower"))
        b = float(need_real(rest[1](), "fnInt( upper"))
        saved = it.reals.get(var, ZERO)

        def g(x):
            it.reals[var] = D(x)
            return float(need_real(ex(), "fnInt( integrand"))
        try:
            r = integrate(g, a, b)
        finally:
            it.reals[var] = saved
        return D(r)
    return f


def _fn_nderiv(p):
    ex = p.expr()
    p.expect(COMMA, "',' in nDeriv(")
    var = p.var_arg("nDeriv(")
    rest = []
    while p.peek() == COMMA:
        p.next()
        rest.append(p.expr())
    p.expect(RPAREN, "')' to close nDeriv(")
    if len(rest) not in (1, 2):
        raise TIError("ARGUMENT", "nDeriv(expr,var,value[,h])")
    it = p.it

    def f():
        x = need_real(rest[0](), "nDeriv( value")
        h = need_real(rest[1](), "nDeriv( h") if len(rest) == 2 else Decimal("0.001")
        if h == 0:
            raise TIError("DOMAIN", "nDeriv( h=0")
        saved = it.reals.get(var, ZERO)
        try:
            it.reals[var] = x + h
            f1 = need_real(ex(), "nDeriv( expression")
            it.reals[var] = x - h
            f2 = need_real(ex(), "nDeriv( expression")
        finally:
            it.reals[var] = saved
        return (f1 - f2) / (2 * h)
    return f


def _fn_sub(p):
    a = p.args(3, 3, "sub(")

    def f():
        s = need_str(a[0](), "sub( arg 1")
        st = need_int(a[1](), "sub( start")
        ln = need_int(a[2](), "sub( length")
        n = len(s.toks)
        if st < 1 or ln < 1 or st + ln - 1 > n:
            raise TIError("INVALID DIM", f"sub( start {st} length {ln} of a {n}-token string")
        return TIStr(s.toks[st - 1:st - 1 + ln])
    return f


def _fn_length(p):
    a = p.args(1, 1, "length(")
    return lambda: D(len(need_str(a[0](), "length( argument").toks))


def _fn_instring(p):
    a = p.args(2, 3, "inString(")

    def f():
        s = need_str(a[0](), "inString( arg 1").key()
        t = need_str(a[1](), "inString( arg 2").key()
        st = need_int(a[2](), "inString( start") if len(a) == 3 else 1
        if st < 1:
            raise TIError("DOMAIN", "inString( start < 1")
        if not t:
            return ZERO
        for i in range(st - 1, len(s) - len(t) + 1):
            if s[i:i + len(t)] == t:
                return D(i + 1)
        return ZERO
    return f


def _fn_expr(p):
    a = p.args(1, 1, "expr(")
    it = p.it
    return lambda: it.eval_tokens(need_str(a[0](), "expr( argument").toks, "expr(")


def _fn_tostring(p):
    a = p.args(1, 1, "toString(")

    def f():
        v = a[0]()
        if isinstance(v, Decimal):
            return str_from_plain(fmt_num(v))
        if isinstance(v, list):
            return str_from_plain("{" + ",".join(fmt_num(x) for x in v) + "}")
        return v
    return f


def _fn_eval(p):
    a = p.args(1, 1, "eval(")
    return lambda: a[0]()


def _fn_not(p):
    a = p.args(1, 1, "not(")
    g = a[0]
    return lambda: elem1(lambda x: ONE if x == 0 else ZERO, g())


def _gcdlcm(is_gcd):
    def build(p):
        a = p.args(2, 2, "gcd(" if is_gcd else "lcm(")

        def one(x, y):
            if not is_int(x) or not is_int(y) or x < 0 or y < 0:
                raise TIError("DOMAIN", "gcd(/lcm( need non-negative integers")
            x, y = int(x), int(y)
            return D(math.gcd(x, y) if is_gcd else (x * y // math.gcd(x, y) if x and y else 0))
        return lambda: elem2(one, a[0](), a[1]())
    return build


def _fn_remainder(p):
    a = p.args(2, 2, "remainder(")

    def one(x, y):
        if not is_int(x) or not is_int(y):
            raise TIError("DOMAIN", "remainder( needs integers")
        if y == 0:
            return x
        return D(int(x) % int(y)) if x >= 0 and y > 0 else D(math.fmod(int(x), int(y)))
    return lambda: elem2(one, a[0](), a[1]())


def _fn_randint(p):
    a = p.args(2, 3, "randInt(")
    it = p.it

    def f():
        lo = need_int(a[0]())
        hi = need_int(a[1]())
        if lo > hi:
            lo, hi = hi, lo
        if len(a) == 3:
            return [D(it.rng.randint(lo, hi)) for _ in range(need_int(a[2]()))]
        return D(it.rng.randint(lo, hi))
    return f


def _fn_logbase(p):
    a = p.args(2, 2, "logBASE(")
    return lambda: elem2(lambda x, b: _div(_ln(x), _ln(b)), a[0](), a[1]())


FUNCS = {
    B("b2"): _fn_simple(abs, "abs("),
    B("b1"): _fn_simple(_int, "int("),
    B("b9"): _fn_simple(_ipart, "iPart("),
    B("ba"): _fn_simple(_fpart, "fPart("),
    B("bc"): _fn_simple(_sqrt, "√("),
    B("be"): _fn_simple(_ln, "ln("),
    B("bf"): _fn_simple(_exp, "𝑒^("),
    B("c0"): _fn_simple(_log, "log("),
    B("c1"): _fn_simple(_tenpow, "₁₀^("),
    B("c2"): _fn_simple(_trig(math.sin), "sin("),
    B("c4"): _fn_simple(_trig(math.cos), "cos("),
    B("c6"): _fn_simple(_trig(math.tan), "tan("),
    B("b8"): _fn_not,
    B("12"): _fn_round,
    B("19"): _minmax(max),
    B("1a"): _minmax(min),
    B("b6"): _fn_sum,
    B("b7"): _fn_prod,
    B("21"): _fn_mean,
    B("1f"): _fn_median,
    B("b5"): _fn_dim,
    B("bb29"): _fn_cumsum,
    B("bb2c"): _fn_dlist,
    B("14"): _fn_augment,
    B("23"): _fn_seq,
    B("24"): _fn_fnint,
    B("25"): _fn_nderiv,
    B("bb0c"): _fn_sub,
    B("bb2b"): _fn_length,
    B("bb0f"): _fn_instring,
    B("bb2a"): _fn_expr,
    B("ef97"): _fn_tostring,
    B("ef98"): _fn_eval,
    B("bb09"): _gcdlcm(True),
    B("bb08"): _gcdlcm(False),
    B("ef32"): _fn_remainder,
    B("bb0a"): _fn_randint,
    B("ef34"): _fn_logbase,
}


# ------------------------------------------------------------------------------------ frames
class Frame:
    __slots__ = ("kind", "opener", "var", "end", "step", "cond", "leaked")

    def __init__(self, kind, opener, var=None, end=None, step=None, cond=None):
        self.kind, self.opener, self.var, self.end, self.step, self.cond = kind, opener, var, end, step, cond
        self.leaked = False


# ------------------------------------------------------------------------------------ interpreter
class Interp:
    def __init__(self, sim, actions, max_steps, seed=0):
        self.sim = sim
        self.actions = deque(actions or [])
        self.max_steps = max_steps
        self.steps = 0
        self.reals = {}
        self.strs = {}
        self.lists = {n: [] for n in BUILTIN_LISTS.values()}
        self.yvars = {}
        self.ans = ZERO
        self.screen = Screen()
        self.snaps = []
        self.leaks = 0
        self.warnings = []
        self._warned = set()
        self.coverage = {}
        self.rng = random.Random(seed)
        self.call_stack = []      # [(Program, stmt)]
        self.parse_cache = {}     # token-bits tuple -> closure (Y-vars, expr(, typed input)
        self.last_was_expr = False
        self.last_value = None

    # --- context
    def where(self):
        if not self.call_stack:
            return ("?", 0, "")
        prog, st = self.call_stack[-1]
        return (prog.name, st.line if st else 0, st.src if st else "")

    def warn(self, msg):
        name, line, _ = self.where()
        m = f"{name} line {line}: {msg}"
        if m not in self._warned:
            self._warned.add(m)
            self.warnings.append(m)

    def snap(self, event, rows=None, **extra):
        name, line, _ = self.where()
        s = {"event": event, "rows": rows if rows is not None else self.screen.snapshot(),
             "program": name, "line": line, "step": self.steps,
             "stack": [p.name for p, _ in self.call_stack if p is not None]}
        s.update(extra)
        self.snaps.append(s)
        return s

    # --- variables
    def get_str(self, name):
        if name not in self.strs:
            raise TIError("UNDEFINED", f"{name} is undefined")
        return self.strs[name]

    def get_list(self, name):
        if name not in self.lists:
            raise TIError("UNDEFINED", f"list {self.lname(name)} is undefined")
        return self.lists[name]

    @staticmethod
    def lname(name):
        return name if name.startswith("L") and name[1:] in "₁₂₃₄₅₆" and len(name) == 2 else "ʟ" + name

    def list_elem(self, name, idx):
        lst = self.get_list(name)
        i = need_real(idx, "list index")
        if not is_int(i):
            raise TIError("DOMAIN", f"list index {fmt_num(i)} is not an integer")
        i = int(i)
        if i < 1 or i > len(lst):
            raise TIError("INVALID DIM", f"{self.lname(name)}({i}) but dim is {len(lst)}")
        return lst[i - 1]

    def eval_tokens(self, toks, what):
        key = tuple(t.bits for t in toks)
        fn = self.parse_cache.get(key)
        if fn is None:
            if not toks:
                raise TIError("SYNTAX", f"{what} of an empty string")
            p = Parser(self, list(toks))
            fn = p.expr()
            p.done()
            self.parse_cache[key] = fn
        return fn()

    def eval_yvar(self, name, arg):
        eq = self.yvars.get(name)
        if eq is None or not eq.toks:
            raise TIError("UNDEFINED", f"{name} is empty")
        if len(self.call_stack) > 200:
            raise TIError("MEMORY", "Y-var recursion")
        if arg is None:
            return self.eval_tokens(eq.toks, name)
        saved = self.reals.get("X", ZERO)
        self.reals["X"] = need_real(arg, f"{name}( argument")
        try:
            return self.eval_tokens(eq.toks, name)
        finally:
            self.reals["X"] = saved

    def store(self, target, value):
        kind, name, idx = target
        if kind == "real":
            self.reals[name] = need_real(value, f"value stored to {name}")
        elif kind == "str":
            self.strs[name] = need_str(value, f"value stored to {name}")
        elif kind == "yvar":
            self.yvars[name] = need_str(value, f"value stored to {name} (store a string)")
        elif kind == "list":
            v = need_list(value, f"value stored to {self.lname(name)}")
            if len(v) > 999:
                raise TIError("INVALID DIM", "list longer than 999")
            self.lists[name] = list(v)
        elif kind == "elem":
            v = need_real(value, f"value stored to {self.lname(name)}(i)")
            i = need_real(idx(), "list index")
            if not is_int(i):
                raise TIError("DOMAIN", f"list index {fmt_num(i)} is not an integer")
            i = int(i)
            lst = self.lists.get(name)
            n = len(lst) if lst is not None else 0
            if i < 1 or i > n + 1 or i > 999:
                raise TIError("INVALID DIM", f"store to {self.lname(name)}({i}) but dim is {n}"
                              + (" (undefined)" if lst is None else ""))
            if lst is None:
                lst = self.lists[name] = []
            if i == n + 1:
                lst.append(v)
            else:
                lst[i - 1] = v
        elif kind == "dim":
            n = need_int(value, "dim")
            if n < 0 or n > 999:
                raise TIError("INVALID DIM", f"dim {n}")
            lst = self.lists.get(name, [])
            self.lists[name] = (lst + [ZERO] * n)[:n]

    def delvar(self, target):
        kind, name, _ = target
        if kind == "real":
            self.reals.pop(name, None)
        elif kind == "str":
            self.strs.pop(name, None)
        elif kind == "yvar":
            self.yvars.pop(name, None)
        elif kind == "list":
            if name in BUILTIN_LISTS.values():
                self.lists[name] = []
            else:
                self.lists.pop(name, None)
        else:
            raise TIError("SYNTAX", "DelVar needs a variable name")

    # --- actions
    def take(self, kind):
        if not self.actions:
            raise _OutOfActions()
        a = self.actions[0]
        if not isinstance(a, dict) or kind not in a:
            raise TIError("ACTION", f"program wants a {kind!r} action but the next action is {a!r}", sim=True)
        self.actions.popleft()
        return a[kind]

    def getkey(self):
        if self.actions and isinstance(self.actions[0], dict) and "key" in self.actions[0]:
            code = self.actions.popleft()["key"]
            code = int(code)
            if code:
                self.snap("getkey", key=code, response=f"key {code} ({KEY_NAMES.get(code, '?')})")
            return D(code)
        if not self.actions:
            self.snap("getkey", key=None)
            raise _OutOfActions()
        self.snap("getkey", key=105, response="key 105 (ENTER, default)")
        return D(105)

    # --- program execution
    def load(self, name):
        return self.sim.program(name)

    def jump(self, prog, stack, label):
        if label not in prog.labels:
            raise TIError("LABEL", f"label {label} not found in {prog.name}")
        t = prog.labels[label]
        anc = set(prog.parents[t])
        for f in stack:
            if not f.leaked and f.opener not in anc:
                f.leaked = True
                self.leaks += 1
        return t

    def skip_block(self, prog, i, stop_at_else):
        """From statement i, find the matching End (or Else at depth 0). Returns its index or len."""
        depth = 0
        stmts = prog.stmts
        n = len(stmts)
        while i < n:
            k = stmts[i].kind
            self.tick()
            if k in OPENERS:
                depth += 1
            elif k == END:
                if depth == 0:
                    return i
                depth -= 1
            elif k == ELSE and depth == 0 and stop_at_else:
                return i
            i += 1
        self.warn("block has no matching End (skipped to end of program)")
        return n

    def tick(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise _MaxSteps()

    def run_program(self, name):
        if len(self.call_stack) >= MAX_CALL_DEPTH:
            raise TIError("MEMORY", "too many nested prgm calls")
        prog = self.load(name)
        self.call_stack.append((prog, None))
        try:
            if prog.load_error:
                raise prog.load_error
            self.exec_body(prog)
        except _Return:
            pass
        # Pop only on normal completion / Return.  Errors (and Stop, out-of-actions, max-steps) abort the
        # whole run, so the frame is kept: Sim.run() then reports WHERE it happened ("ERR:X at NAME line N")
        # instead of "? line 0" (bug fixed: the old finally-pop lost the location).
        self.call_stack.pop()

    def compiled(self, st):
        # st.cache = (owner Interp, closure | TIError).  Compiled closures capture the Interp that built
        # them, and Program objects are cached per Sim, so a later Sim.run() (new Interp) must recompile;
        # otherwise it would read/write the PREVIOUS run's variables (stale-state bug, fixed here).
        c = st.cache
        if c is None or c[0] is not self:
            try:
                val = self.compile(st)
            except TIError as e:
                st.cache = (self, e)
                raise
            st.cache = (self, val)
            return val
        c = c[1]
        if isinstance(c, TIError):
            raise c
        return c

    def exec_body(self, prog):
        stmts = prog.stmts
        n = len(stmts)
        stack = []
        pc = 0
        cov = self.coverage.setdefault(prog.name, set())
        top = len(self.call_stack) - 1
        while pc < n:
            st = stmts[pc]
            self.call_stack[top] = (prog, st)
            self.tick()
            cov.add(st.line)
            k = st.kind
            if k is None:
                pc += 1
                continue
            if k == IF:
                cond = self.compiled(st)
                c = truth(cond(), "If condition")
                nxt = stmts[pc + 1] if pc + 1 < n else None
                self.last_was_expr = False
                if nxt is not None and nxt.kind == THEN:
                    if len(nxt.toks) != 1:
                        raise_at(self, prog, nxt, TIError("SYNTAX", "Then must be alone on its line"))
                    if c:
                        stack.append(Frame("if", pc + 1))
                        pc += 2
                    else:
                        j = self.skip_block(prog, pc + 2, True)
                        if j < n and stmts[j].kind == ELSE:
                            stack.append(Frame("if", pc + 1))
                        pc = j + 1
                else:
                    pc += 1 if c else 2
                continue
            if k == END:
                if len(st.toks) != 1:
                    raise TIError("SYNTAX", "End must be alone")
                if not stack:
                    raise TIError("SYNTAX", "End without an open If-Then/For/While/Repeat")
                f = stack[-1]
                if f.kind == "if":
                    stack.pop()
                    pc += 1
                elif f.kind == "for":
                    v = need_real(self.reals.get(f.var, ZERO), "For( variable") + f.step
                    self.reals[f.var] = v
                    if (f.step > 0 and v <= f.end) or (f.step < 0 and v >= f.end) or f.step == 0:
                        pc = f.opener + 1
                    else:
                        stack.pop()
                        pc += 1
                elif f.kind == "while":
                    stack.pop()
                    pc = f.opener
                else:  # repeat
                    if truth(f.cond(), "Repeat condition"):
                        stack.pop()
                        pc += 1
                    else:
                        pc = f.opener + 1
                continue
            if k == ELSE:
                # reached Else while executing the Then part: skip to End (which pops the If frame)
                pc = self.skip_block(prog, pc + 1, False)
                continue
            if k == THEN:
                raise TIError("SYNTAX", "Then without If on the previous line")
            if k == FOR:
                var, a, b, s = self.compiled(st)
                a, b = need_real(a(), "For( start"), need_real(b(), "For( end")
                s = need_real(s(), "For( step") if s else ONE
                self.reals[var] = a
                if (s > 0 and a > b) or (s < 0 and a < b):
                    pc = self.skip_block(prog, pc + 1, False) + 1
                else:
                    stack.append(Frame("for", pc, var=var, end=b, step=s))
                    self._check_frames(stack)
                    pc += 1
                continue
            if k == WHILE:
                cond = self.compiled(st)
                if truth(cond(), "While condition"):
                    stack.append(Frame("while", pc))
                    self._check_frames(stack)
                    pc += 1
                else:
                    pc = self.skip_block(prog, pc + 1, False) + 1
                continue
            if k == REPEAT:
                cond = self.compiled(st)
                stack.append(Frame("repeat", pc, cond=cond))
                self._check_frames(stack)
                pc += 1
                continue
            if k == GOTO:
                label = self.compiled(st)
                pc = self.jump(prog, stack, label)
                continue
            if k == LBL:
                self.compiled(st)
                pc += 1
                continue
            if k == MENU:
                pc = self.do_menu(prog, stack, st)
                continue
            if k == RETURN:
                raise _Return()
            if k == STOP:
                raise _Stop()
            if k == PRGM:
                name = self.compiled(st)
                self.run_program(name)
                self.last_was_expr = False
                pc += 1
                continue
            self.exec_simple(st)
            pc += 1

    def _check_frames(self, stack):
        if len(stack) > MAX_FRAMES:
            raise TIError("MEMORY", f"{len(stack)} open blocks (Goto/Menu out of loops leaks memory)")

    # --- compile statements (parse once, cached per statement)
    def compile(self, st):
        k = st.kind
        toks = st.toks
        if k in (IF, WHILE, REPEAT):
            p = Parser(self, toks, 1)
            if p.at_end():
                p.fail("condition expected")
            c = p.expr()
            p.done()
            return c
        if k == FOR:
            p = Parser(self, toks, 1)
            var = p.var_arg("For(")
            p.expect(COMMA, "',' in For(")
            a = p.expr()
            p.expect(COMMA, "',' in For(")
            b = p.expr()
            s = None
            if p.peek() == COMMA:
                p.next()
                s = p.expr()
            p.expect(RPAREN, "')' to close For(")
            p.done()
            return (var, a, b, s)
        if k in (GOTO, LBL):
            nm = label_name(toks[1:])
            if nm is None:
                raise TIError("SYNTAX", "label must be 1-2 chars from A-Z, 0-9, θ")
            return nm
        if k == PRGM:
            name = "".join(NAME_CHARS.get(t.bits, "?") for t in toks[1:])
            if not tibuild.NAME_RE.match(name):
                raise TIError("SYNTAX", f"bad program name {name!r}")
            return name
        if k == MENU:
            p = Parser(self, toks, 1)
            title = p.expr()
            items = []
            while p.peek() == COMMA:
                p.next()
                txt = p.expr()
                p.expect(COMMA, "',' before Menu( label")
                start = p.i
                while not p.at_end() and p.peek() in NAME_CHARS:
                    p.i += 1
                nm = label_name(toks[start:p.i])
                if nm is None:
                    p.fail("Menu( label must be 1-2 chars from A-Z, 0-9, θ")
                items.append((txt, nm))
            p.expect(RPAREN, "')' to close Menu(")
            p.done()
            if not items:
                raise TIError("ARGUMENT", "Menu( with no options")
            if len(items) > 7:
                raise TIError("ARGUMENT", "Menu( with more than 7 options")
            return (title, items)
        if k in (DISP, PAUSE):
            p = Parser(self, toks, 1)
            args = []
            if not p.at_end():
                args.append(p.expr())
                while p.peek() == COMMA:
                    p.next()
                    args.append(p.expr())
            p.done()
            if k == PAUSE and len(args) > 2:
                raise TIError("ARGUMENT", "Pause [value[,time]]")
            return args
        if k == OUTPUT:
            p = Parser(self, toks, 1)
            a = p.args(3, 3, "Output(")
            p.done()
            return a
        if k == INPUT:
            p = Parser(self, toks, 1)
            if p.at_end():
                raise TIError("UNSUPPORTED", "Input with no arguments (graph cursor)", True)
            prompt = None
            if p.peek() == QUOTE or p.peek() in STRVARS:
                if p.peek() == QUOTE:
                    s = p.string_literal()
                    prompt = (lambda s: lambda: s)(s)
                else:
                    nm = STRVARS[p.next()]
                    prompt = (lambda nm: lambda: self.get_str(nm))(nm)
                if p.at_end():
                    raise TIError("UNSUPPORTED", "Input \"text\" with no variable", True)
                p.expect(COMMA, "',' after Input prompt")
            tgt = self.input_target(p)
            p.done()
            return (prompt, tgt)
        if k == PROMPT:
            p = Parser(self, toks, 1)
            tgts = [self.input_target(p)]
            while p.peek() == COMMA:
                p.next()
                tgts.append(self.input_target(p))
            p.done()
            return tgts
        if k == DELVAR:
            p = Parser(self, toks, 1)
            t = p.target()
            if t[0] in ("elem", "dim"):
                p.fail("DelVar needs a variable name")
            p.done()
            return t
        if k in (SORTA, SORTD):
            p = Parser(self, toks, 1)
            names = [p.list_name() if (p.peek() == LIST_L or p.peek() in BUILTIN_LISTS) else p.fail(
                "SortA(/SortD( need list names")]
            while p.peek() == COMMA:
                p.next()
                if not (p.peek() == LIST_L or p.peek() in BUILTIN_LISTS):
                    p.fail("SortA(/SortD( need list names")
                names.append(p.list_name())
            p.expect(RPAREN, "')' to close SortA(")
            p.done()
            return names
        if k == CLRLIST:
            p = Parser(self, toks, 1)
            names = [p.list_name()]
            while p.peek() == COMMA:
                p.next()
                names.append(p.list_name())
            p.done()
            return names
        if k == FILL:
            p = Parser(self, toks, 1)
            v = p.expr()
            p.expect(COMMA, "',' in Fill(")
            nm = p.list_name()
            p.expect(RPAREN, "')' to close Fill(")
            p.done()
            return (v, nm)
        if k in (CLRHOME, RETURN, STOP, THEN, ELSE, END):
            if len(toks) != 1:
                Parser(self, toks, 1).fail()
            return True
        if k in NOOP_CMDS or k in (FNON, FNOFF) or k == B("ef96"):
            return True
        if k in (B("73"), B("67"), B("68")):
            raise TIError("UNSUPPORTED", f"'{tdisp(toks[0])}' display mode", True)
        # expression statement, optionally with →target
        store_at = None
        for j, b in enumerate(st.bits):
            if b == STORE:
                store_at = j
                break
        if store_at is None:
            p = Parser(self, toks)
            if not p.starts_operand(p.peek()):
                d = tdisp(toks[0])
                if d.endswith("(") or d.endswith(" ") or len(d) > 1 and d not in ("Ans",):
                    raise TIError("UNSUPPORTED", f"command '{d}'", True)
            e = p.expr()
            p.done()
            return ("expr", e, None)
        p = Parser(self, toks, 0, store_at)
        if p.at_end():
            p.fail("value expected before →")
        e = p.expr()
        p.done()
        p2 = Parser(self, toks, store_at + 1)
        tgt = p2.target()
        p2.done()
        return ("store", e, tgt)

    def input_target(self, p):
        b = p.peek()
        if b in LETTERS:
            p.next()
            return ("real", LETTERS[b], None)
        if b in STRVARS:
            p.next()
            return ("str", STRVARS[b], None)
        if b == LIST_L or b in BUILTIN_LISTS:
            return ("list", p.list_name(), None)
        if b is None:
            p.fail("variable expected")
        p.fail(f"cannot Input into {describe_token(p.t[p.i])}")

    # --- simple statements
    def exec_simple(self, st):
        k = st.kind
        c = self.compiled(st)
        if k == DISP:
            self.last_was_expr = False
            for a in c:
                self.disp_value(a())
            return
        if k == PAUSE:
            self.last_was_expr = False
            if c:
                self.disp_value(c[0]())
            self.snap("pause", response="ENTER")
            return
        if k == OUTPUT:
            self.last_was_expr = False
            r = need_int(c[0](), "Output( row")
            col = need_int(c[1](), "Output( column")
            if not (1 <= r <= ROWS) or not (1 <= col <= COLS):
                raise TIError("DOMAIN", f"Output({r},{col},...) outside 10x26 screen")
            v = c[2]()
            text = value_text(v)
            wrapped, clipped = self.screen.write_at(r - 1, col - 1, text)
            if clipped:
                self.warn(f"Output text clipped at screen end: {text!r}")
            elif wrapped:
                self.warn(f"Output text wraps to next row: {text!r} at ({r},{col})")
            return
        if k == CLRHOME:
            self.screen.clear()
            return
        if k == INPUT:
            prompt, tgt = c
            if prompt is None:
                ptext = "?"
            else:
                ptext = need_str(prompt(), "Input prompt").text
            self.do_input(ptext, tgt)
            return
        if k == PROMPT:
            for tgt in c:
                nm = tgt[1] if tgt[0] != "list" else self.lname(tgt[1])
                self.do_input(nm + "=?", tgt)
            return
        if k == DELVAR:
            self.delvar(c)
            return
        if k in (SORTA, SORTD):
            lists = [self.get_list(nm) for nm in c]
            n = len(lists[0])
            if any(len(l) != n for l in lists):
                raise TIError("DIM MISMATCH", "SortA( lists of different dims")
            order = sorted(range(n), key=lambda i: lists[0][i], reverse=(k == SORTD))
            for nm, l in zip(c, lists):
                self.lists[nm] = [l[i] for i in order]
            return
        if k == CLRLIST:
            for nm in c:
                self.lists[nm] = []
            return
        if k == FILL:
            v = need_real(c[0](), "Fill( value")
            lst = self.get_list(c[1])
            self.lists[c[1]] = [v] * len(lst)
            return
        if c is True:
            return
        kind, e, tgt = c
        v = e()
        if kind == "store":
            self.store(tgt, v)
        self.ans = v
        self.last_was_expr = (kind == "expr")
        self.last_value = v

    def disp_value(self, v):
        if isinstance(v, TIStr):
            text = v.text
            if self.screen.put_line(text, right=False):
                self.warn(f"Disp string longer than 26 chars was cut: {text!r}")
        else:
            text = value_text(v)
            if self.screen.put_line(text, right=True):
                self.warn(f"Disp value longer than 26 chars: {text!r}")

    def do_input(self, ptext, tgt):
        r, c = self.screen.write_flow(ptext)
        vname = tgt[1] if tgt[0] != "list" else self.lname(tgt[1])
        s = self.snap("input", prompt=ptext, var=vname)
        typed = self.take("input")
        typed = typed if isinstance(typed, str) else (fmt_num(D(typed)) if isinstance(typed, (int, float))
                                                      else str(typed))
        typed = typed.replace("-", "-")
        s["response"] = f"typed {typed!r} into {vname}"
        toks = typed_tokens(typed)
        # echo typed text on the screen after the prompt
        text = "".join(tdisp(t) for t in toks)
        row = self.screen.cur - 1
        col = c
        for ch in text:
            if col >= COLS:
                row = self.screen.newline_row()
                self.screen.rows[row] = [" "] * COLS
                col = 0
            self.screen.rows[row][col] = ch
            col += 1
        if tgt[0] == "str":
            self.strs[tgt[1]] = TIStr(toks)
            return
        if not toks:
            raise TIError("SYNTAX", f"empty input for {vname}")
        p = Parser(self, toks)
        e = p.expr()
        p.done()
        v = e()
        if tgt[0] == "real":
            self.reals[tgt[1]] = need_real(v, f"input for {vname}")
        else:
            self.lists[tgt[1]] = list(need_list(v, f"input for {vname}"))

    def do_menu(self, prog, stack, st):
        title_f, items = self.compiled(st)
        title = need_str(title_f(), "Menu( title").text
        texts = [need_str(t(), "Menu( option").text for t, _ in items]
        labels = [nm for _, nm in items]
        s = self.snap("menu", rows=menu_rows(title, texts),
                      menu={"title": title, "items": texts, "labels": labels})
        n = self.take("menu")
        if isinstance(n, str) and not n.strip().isdigit():
            n = self.menu_index(title, texts, n)
        try:
            n = int(n)
        except (TypeError, ValueError):
            raise TIError("ACTION", f"menu choice must be an integer or item text, got {n!r}", sim=True)
        if not 1 <= n <= len(items):
            raise TIError("ACTION", f"menu choice {n} out of range 1..{len(items)} for {title!r}", sim=True)
        s["response"] = f"chose {n}: {texts[n - 1]} (label {labels[n - 1]})"
        self.last_was_expr = False
        return self.jump(prog, stack, labels[n - 1])


    @staticmethod
    def menu_index(title, texts, want):
        """1-based index of the item whose stripped text equals want, else of the unique item that starts
        with want. Raises SIM:ACTION (listing the items) when there is no match or the match is ambiguous."""
        items = [t.strip() for t in texts]
        listing = ", ".join(f"{k}={t}" for k, t in enumerate(items, 1))
        exact = [k for k, t in enumerate(items, 1) if t == want]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise TIError("ACTION", f"menu text {want!r} matches several items of {title!r}: {listing}", sim=True)
        pref = [k for k, t in enumerate(items, 1) if want and t.startswith(want)]
        if len(pref) == 1:
            return pref[0]
        what = "is ambiguous in" if pref else "matches no item of"
        raise TIError("ACTION", f"menu text {want!r} {what} {title!r}: {listing}", sim=True)


def raise_at(it, prog, st, err):
    it.call_stack[-1] = (prog, st)
    raise err


# ------------------------------------------------------------------------------------ results
class Result:
    def __init__(self, it, ended_reason, error):
        self.screens = it.snaps
        self.leaks = it.leaks
        self.error = error
        self.ended_reason = ended_reason
        self.warnings = it.warnings
        self.steps = it.steps
        self.coverage = {k: sorted(v) for k, v in it.coverage.items()}
        self.raw_vars = {
            "reals": dict(it.reals),
            "strings": {k: v.text for k, v in it.strs.items()},
            "lists": {k: list(v) for k, v in it.lists.items()},
            "equations": {k: v.text for k, v in it.yvars.items()},
            "Ans": it.ans,
        }

        def conv(v):
            if isinstance(v, Decimal):
                return float(v)
            if isinstance(v, list):
                return [float(x) for x in v]
            if isinstance(v, TIStr):
                return v.text
            return v
        self.vars = {
            "reals": {k: float(v) for k, v in it.reals.items()},
            "strings": dict(self.raw_vars["strings"]),
            "lists": {k: [float(x) for x in v] for k, v in it.lists.items()},
            "equations": dict(self.raw_vars["equations"]),
            "Ans": conv(it.ans),
        }
        self.text = "\n".join(render_snapshot(i, s) for i, s in enumerate(self.screens))
        tail = f"== ended: {ended_reason}; leaks={self.leaks}; steps={self.steps}"
        if error:
            tail += f"\n== error: {error}"
        for w in self.warnings:
            tail += f"\n== warning: {w}"
        self.text += ("\n" if self.text else "") + tail

    def var(self, name):
        """res.var('A') / res.var('Str9') / res.var('ʟCNA') / res.var('L₁') / res.var('Y9')."""
        v = self.vars
        if name.startswith("Str"):
            return v["strings"].get(name)
        if name.startswith("ʟ"):
            return v["lists"].get(name[1:])
        if name in v["lists"]:
            return v["lists"][name]
        if name.startswith("Y") and len(name) == 2:
            return v["equations"].get(name)
        if name == "Ans":
            return v["Ans"]
        return v["reals"].get(name, 0.0)

    def screen(self, i):
        return render_snapshot(i, self.screens[i])

    def find(self, text):
        return [i for i, s in enumerate(self.screens) if any(text in r for r in s["rows"])]

    def all_text_rows(self):
        return [r for s in self.screens for r in s["rows"]]

    def __repr__(self):
        return f"<Result {self.ended_reason} error={self.error!r} leaks={self.leaks} screens={len(self.screens)}>"


def render_snapshot(i, s):
    head = f"#{i} {s['event'].upper()}  [{s.get('program')} line {s.get('line')}, step {s.get('step')}]"
    if s["event"] == "menu":
        m = s["menu"]
        head += f"  menu {m['title']!r}: " + ", ".join(f"{k}={t}" for k, t in enumerate(m["items"], 1))
    if s["event"] == "input":
        head += f"  prompt {s.get('prompt')!r} -> {s.get('var')}"
    out = [head, "+" + "-" * COLS + "+"]
    out += ["|" + r + "|" for r in s["rows"]]
    out.append("+" + "-" * COLS + "+")
    if s.get("response"):
        out.append(f">> {s['response']}")
    if s.get("error"):
        out.append(f">> {s['error']}")
    return "\n".join(out)


# ------------------------------------------------------------------------------------ Sim
class Sim:
    def __init__(self, src_dir="src"):
        self.dirs = [src_dir] if isinstance(src_dir, str) else list(src_dir)
        self.extra = {}
        self._cache = {}

    def add_program(self, name, source_text):
        """Register/replace an in-memory program. Re-adding a name REPLACES the old source and drops the
        cached Program, so the next run uses the new text (also shadows a src/NAME.txt of that name)."""
        self.extra[name] = source_text
        self._cache.pop(name, None)

    def program(self, name):
        if name in self._cache:
            prog, mtime = self._cache[name]
            if prog.path is None or os.path.getmtime(prog.path) == mtime:
                return prog
        if name in self.extra:
            prog = Program(name, self.extra[name])
            self._cache[name] = (prog, None)
            return prog
        for d in self.dirs:
            path = os.path.join(d, name + ".txt")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    prog = Program(name, f.read(), path)
                self._cache[name] = (prog, os.path.getmtime(path))
                return prog
        raise TIError("UNDEFINED", f"prgm{name} not found in {self.dirs}")

    def run(self, name, actions=(), max_steps=2_000_000, init_vars=None, seed=0):
        it = Interp(self, actions, max_steps, seed)
        ended, error = "end", None
        with localcontext(CTX):
            try:
                if init_vars:
                    self._init_vars(it, init_vars)
                it.call_stack.append((None, None))  # placeholder so errors in loading have context
                it.call_stack.pop()
                it.run_program(name)
                ended = "end"
                self._final_display(it)
                it.snap("end")
            except _Return:
                ended = "return"
                it.snap("end")
            except _Stop:
                ended = "stop"
                it.snap("end")
            except _OutOfActions:
                ended = "out_of_actions"
                if it.snaps:
                    it.snaps[-1]["response"] = "(no more actions: stopped here)"
            except _MaxSteps:
                ended = "max_steps"
                error = f"SIM:MAX_STEPS exceeded ({max_steps}) at {self._loc(it)}"
                it.snap("error", error=error)
            except TIError as e:
                ended = "error"
                error = self._errtext(it, e)
                it.snap("error", error=error)
            except (ZeroDivisionError,) as e:
                ended = "error"
                error = self._errtext(it, TIError("DIVIDE BY 0", str(e)))
                it.snap("error", error=error)
            except Overflow as e:
                ended = "error"
                error = self._errtext(it, TIError("OVERFLOW", str(e)))
                it.snap("error", error=error)
            except InvalidOperation as e:
                ended = "error"
                error = self._errtext(it, TIError("DOMAIN", str(e)))
                it.snap("error", error=error)
            except RecursionError:
                ended = "error"
                error = self._errtext(it, TIError("MEMORY", "recursion too deep"))
                it.snap("error", error=error)
        return Result(it, ended, error)

    @staticmethod
    def _loc(it):
        name, line, src = it.where()
        return f"{name} line {line}: {src}"

    def _errtext(self, it, e):
        name, line, src = it.where()
        return f"{e.label} at {name} line {line}: {src}" + (f" -- {e.detail}" if e.detail else "")

    @staticmethod
    def _final_display(it):
        # the TI home screen shows "Done" or the value of a final bare expression
        if it.last_was_expr and it.last_value is not None:
            it.disp_value(it.last_value)
        else:
            it.screen.put_line("Done", right=True)

    def _init_vars(self, it, init):
        for k, v in init.items():
            if k.startswith("Str"):
                it.strs[k] = v if isinstance(v, TIStr) else str_from_text(str(v))
            elif k.startswith("ʟ"):
                it.lists[k[1:]] = [D(x) for x in v]
            elif k in it.lists or (k.startswith("L") and k[1:] in "₁₂₃₄₅₆" and len(k) == 2):
                it.lists[k] = [D(x) for x in v]
            elif k.startswith("Y") and len(k) == 2:
                it.yvars[k] = typed_str(v)
            elif k == "Ans":
                it.ans = D(v) if not isinstance(v, (list, str)) else v
            else:
                it.reals[k] = D(v) if not isinstance(v, str) else it_eval_text(it, v)

    def eval(self, text, init_vars=None):
        """Evaluate one typed expression (expression-mode tokens). Returns Decimal / list / TIStr."""
        it = Interp(self, [], 1_000_000)
        with localcontext(CTX):
            if init_vars:
                self._init_vars(it, init_vars)
            return it_eval_text(it, text)


def typed_str(v):
    return v if isinstance(v, TIStr) else TIStr(typed_tokens(str(v)))


def it_eval_text(it, text):
    toks = typed_tokens(text)
    if not toks:
        raise TIError("SYNTAX", "empty expression")
    p = Parser(it, toks)
    e = p.expr()
    p.done()
    return e()


# ------------------------------------------------------------------------------------ CLI
def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="TI-84 Plus CE TI-BASIC simulator")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="run a program")
    r.add_argument("src")
    r.add_argument("name")
    r.add_argument("--actions", default="[]", help="JSON list of actions")
    r.add_argument("--max-steps", type=int, default=2_000_000)
    r.add_argument("--vars", action="store_true", help="print final variables")
    r.add_argument("--init", default=None, help="JSON dict of initial variables")
    e = sub.add_parser("eval", help="evaluate an expression")
    e.add_argument("expr")
    a = ap.parse_args(argv[1:])
    if a.cmd == "run":
        sim = Sim(a.src.split(os.pathsep))
        res = sim.run(a.name, json.loads(a.actions), max_steps=a.max_steps,
                      init_vars=json.loads(a.init) if a.init else None)
        print(res.text)
        if a.vars:
            print(json.dumps(res.vars, ensure_ascii=False, indent=1))
        return 1 if res.error else 0
    if a.cmd == "eval":
        try:
            v = Sim([]).eval(a.expr)
        except TIError as ex:
            print(ex)
            return 1
        print(value_text(v))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
