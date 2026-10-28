#!/usr/bin/env python3
"""gen_oracles.py - independent answer key for the STA 431/631 TI-84 helper.

Recomputes, from scratch and in exact arithmetic (fractions / sympy / mpmath at 40 digits):
  * every oracle case of SPEC.md section 4 (the SPEC numbers are only used for comparison),
  * 2-3 extra edge cases per calculator tool,
  * the Homework 1-3 answers (numeric ones; proofs are outlined in cases.md).
and predicts the STAFMT display (Str9 exact form, Str8 6-decimal form) of every value.

Writes oracles.json (machine-readable) and cases.md (human-readable).
Run:  $PY oracles/gen_oracles.py
"""
import itertools
import json
import os
import re
import sys
from fractions import Fraction as Fr
from math import comb, factorial, perm, prod
from collections import Counter, OrderedDict
from decimal import Decimal

import mpmath
import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tifmt import stafmt, stafmt_robust, ti_str, to_dec  # noqa: E402

mpmath.mp.dps = 40

CASES = []
DISCREPANCIES = []   # (id, text)
FRAGILE = []         # (id, name, text)


# ----------------------------------------------------------------------------------------
# value helpers
class Irr:
    """An irrational / numeric value: symbolic text + high-precision value.
    ti_value = what the calculator computes (e.g. nDeriv approximation) if different."""
    def __init__(self, text, value, ti_value=None, numeric=True):
        self.text = text
        self.value = mpmath.mpf(value)
        self.ti_value = mpmath.mpf(ti_value) if ti_value is not None else self.value
        self.numeric = numeric


def exact_str(v):
    if isinstance(v, bool):
        return "YES" if v else "NO"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, Fr):
        return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    if isinstance(v, Irr):
        return v.text
    return str(v)


def dec_of(v):
    if isinstance(v, bool) or isinstance(v, str):
        return None
    if isinstance(v, (int, Fr)):
        return float(round(Fr(v).numerator / Fr(v).denominator, 12)) if not isinstance(v, int) else v
    if isinstance(v, Irr):
        return float(mpmath.nstr(v.value, 15))
    return None


def display_of(cid, name, v, numeric_tool=False):
    """[Str9, Str8] as STAFMT shows the value; flags fragile displays."""
    if isinstance(v, bool) or isinstance(v, str):
        return None
    if isinstance(v, Irr):
        x = v.ti_value
        rel = Decimal("1e-11") if v.numeric else Decimal("1e-13")
    else:
        x = Fr(v)
        rel = Decimal("1e-11") if numeric_tool else Decimal("1e-13")
    base, stable, outs = stafmt_robust(x, rel)
    if not stable:
        FRAGILE.append((cid, name, f"display not stable under relative error {rel}: "
                        + " / ".join(f"[{a}, {b}]" for a, b in outs)))
    return list(base)


def parse_num(s):
    s = s.strip().replace("⁻", "-").replace("−", "-")
    try:
        if s.startswith("."):
            s = "0" + s
        if s.startswith("-."):
            s = "-0" + s[1:]
        return Fr(s)
    except (ValueError, ZeroDivisionError):
        return None


def compare_spec(cid, name, mine, spec_s, disp):
    """spec_s = the value exactly as written in SPEC.md section 4."""
    if isinstance(mine, bool) or isinstance(mine, str):
        ok = str(spec_s).upper() == exact_str(mine).upper()
        if not ok:
            DISCREPANCIES.append((cid, f"{name}: SPEC says {spec_s!r}, oracle computes {exact_str(mine)!r}"))
        return ok
    sv = parse_num(spec_s)
    mine_val = Fr(mine) if not isinstance(mine, Irr) else None
    is_dec = ("/" not in spec_s) and ("." in spec_s)
    if mine_val is not None and sv is not None and sv == mine_val:
        ok = True
    elif is_dec and disp is not None and disp[1].replace("⁻", "-") == spec_s.replace("⁻", "-"):
        ok = True   # SPEC gave the 6-decimal display
    elif is_dec and isinstance(mine, Irr):
        nd = len(spec_s.split(".")[1])
        ok = abs(float(mine.ti_value) - float(sv)) <= 0.51 * 10 ** (-nd)
    else:
        ok = False
    if not ok:
        DISCREPANCIES.append((cid, f"{name}: SPEC says {spec_s}, oracle computes {exact_str(mine)}"
                              f" (display {disp})"))
        return False
    # display check: SPEC gives a fraction but STAFMT would not show that fraction
    if "/" in spec_s and disp is not None:
        want = spec_s.replace("-", "⁻")
        if disp[0] != want:
            DISCREPANCIES.append((cid, f"{name}: SPEC writes {spec_s} but STAFMT cannot show that "
                                  f"fraction (reduced denominator > 9999) -> calculator shows "
                                  f"Str9={disp[0]!r}, Str8={disp[1]!r}. Tests must expect {disp[0]!r}."))
    return True


def add(cid, program, tool, kind, desc, inputs, expected, spec=None, notes=None,
        numeric_tool=False, tool_name=None):
    exp_s, decs, disp = OrderedDict(), OrderedDict(), OrderedDict()
    for k, v in expected.items():
        exp_s[k] = exact_str(v)
        d = dec_of(v)
        if d is not None:
            decs[k] = d
        ds = display_of(cid, k, v, numeric_tool)
        if ds is not None:
            disp[k] = ds
    spec_cmp = None
    if spec:
        spec_cmp = OrderedDict()
        for k, sval in spec.items():
            if k not in expected:
                DISCREPANCIES.append((cid, f"internal: spec key {k} not computed"))
                continue
            ok = compare_spec(cid, k, expected[k], sval, disp.get(k))
            spec_cmp[k] = {"spec": sval, "match": ok}
    entry = OrderedDict(id=cid, program=program, tool=tool, tool_name=tool_name or TOOL_NAMES.get((program, tool), ""),
                        kind=kind, inputs_description=desc, inputs=inputs, expected=exp_s,
                        decimal=decs, display=disp)
    if spec_cmp is not None:
        entry["spec_check"] = spec_cmp
    if notes:
        entry["notes"] = notes
    CASES.append(entry)
    return entry


TOOL_NAMES = {
    ("STACNT", "A"): "n!, nPr, nCr", ("STACNT", "B"): "WORD ARRANGEMENTS",
    ("STACNT", "C"): "GROUPS/MULTINOMIAL", ("STACNT", "D"): "2-GROUP SELECTION",
    ("STACNT", "E"): "STARS AND BARS", ("STACNT", "F"): "TERM COEFFICIENT",
    ("STAPRB", "A"): "TWO EVENTS A,B", ("STAPRB", "B"): "2x2 TABLE", ("STAPRB", "C"): "TOTAL PROB/BAYES",
    ("STAPRB", "D"): "SENS/SPEC TEST", ("STAPRB", "E"): "VENN 2-3 SETS", ("STAPRB", "F"): "URN DRAWS",
    ("STARV", "A"): "PMF TABLE + CDF", ("STARV", "B"): "MAX/MIN/SUM DRAWS", ("STARV", "C"): "POLY PDF/CDF",
    ("STARV", "D"): "ANY f(x) OR F(x)", ("STARV", "E"): "TRANSFORM Y=g(X)",
}

# ========================================================================================
# STACNT
# ========================================================================================


def cnt_a(N, R):
    out = OrderedDict()
    out["n!"] = factorial(N) if N <= 69 else "TOO BIG"
    out["r!"] = factorial(R) if R <= 69 else "TOO BIG"
    out["nPr"] = perm(N, R) if R <= N else 0
    out["nCr"] = comb(N, R) if R <= N else 0
    out["n^r"] = N ** R                       # python: 0**0 == 1 (number of maps from empty set)
    # multisets of size R from N types (brute-force check for small values)
    ms = comb(N + R - 1, R) if N >= 1 else (1 if R == 0 else 0)
    if N <= 6 and R <= 6:
        bf = sum(1 for _ in itertools.combinations_with_replacement(range(N), R))
        assert bf == ms, (N, R, bf, ms)
    out["C(n+r-1,r)"] = ms
    return out


def word_counts(w):
    c = Counter(w)
    n = len(w)
    total = factorial(n) // prod(factorial(k) for k in c.values())
    return n, c, total


def cnt_b(word, letter=None):
    n, c, total = word_counts(word)
    out = OrderedDict()
    out["n"] = n
    rep = "  ".join(f"{ch} x{k}" for ch, k in sorted(c.items(), key=lambda t: word.index(t[0])) if k > 1)
    out["repeated"] = rep if rep else "(none)"
    out["total"] = total
    if letter is not None:
        k = c.get(letter, 0)
        if k == 0:
            out["block"] = "REJECT (letter not in word)"
        else:
            block = factorial(n - k + 1) // prod(factorial(v) for ch, v in c.items() if ch != letter)
            # brute-force check for short words
            if n <= 9:
                perms = set(itertools.permutations(word))
                bf = sum(1 for p in perms if letter * k in "".join(p))
                assert bf == block, (word, letter, bf, block)
                assert len(perms) == total
            out["block"] = block
            out["not together"] = total - block
    return out


def cnt_c1(sizes):
    n = sum(sizes)
    lab = factorial(n) // prod(factorial(s) for s in sizes)
    m = Counter(sizes)
    unl = lab // prod(factorial(v) for v in m.values())
    return OrderedDict([("n", n), ("labeled", lab), ("unlabeled", unl)])


def cnt_c2(N, counts, F):
    out = OrderedDict()
    if sum(counts) > N:
        out["result"] = "REJECT (sum of counts > N)"
        return out
    r = N - sum(counts)
    mult = factorial(N) // (prod(factorial(c) for c in counts) * factorial(r))
    out["r"] = r
    out["multinomial"] = mult
    out["F^r"] = F ** r
    out["total"] = mult * F ** r
    return out


def cnt_d(A, B, K, mn1, mx1, mn2, mx2):
    # brute force over i = number chosen from G1
    terms = []
    for i in range(0, K + 1):
        j = K - i
        if i > A or j > B:
            continue
        if not (mn1 <= i <= mx1 and mn2 <= j <= mx2):
            continue
        terms.append((i, comb(A, i), comb(B, j)))
    # SPEC range formula, for cross-check
    lo = max(mn1, K - min(mx2, B), 0)
    hi = min(mx1, A, K - mn2, K)
    spec_terms = [(i, comb(A, i), comb(B, K - i)) for i in range(lo, hi + 1)]
    assert [t for t in spec_terms if t[1] * t[2] > 0 or True] == spec_terms
    total = sum(a * b for _, a, b in terms)
    assert total == sum(a * b for _, a, b in spec_terms), (A, B, K, terms, spec_terms)
    out = OrderedDict()
    out["i range"] = f"{lo}..{hi}" if lo <= hi else f"empty ({lo}>{hi})"
    for i, a, b in terms:
        out[f"i={i}"] = f"{a}*{b}={a*b}"
    out["total"] = total
    denom = comb(A + B, K)
    out["C(A+B,K)"] = denom
    out["P"] = Fr(total, denom) if denom else "undef (K>A+B, C(A+B,K)=0)"
    return out


def cnt_e(n, k, mins):
    np_ = n - sum(mins)
    out = OrderedDict()
    out["n'"] = np_
    if np_ < 0:
        out["ways"] = 0
    else:
        out["ways"] = comb(np_ + k - 1, k - 1)
        out["shown"] = f"C({np_ + k - 1},{k - 1})={out['ways']}"
    # brute force
    if n <= 16 and k <= 4:
        bf = sum(1 for xs in itertools.product(range(n + 1), repeat=k)
                 if sum(xs) == n and all(x >= m for x, m in zip(xs, mins)))
        assert bf == out["ways"], (n, k, mins, bf)
    return out


def cnt_f(terms):
    n = sum(e for _, e in terms)
    mult = factorial(n) // prod(factorial(e) for _, e in terms)
    pr = prod((a ** e if not (a == 0 and e == 0) else 1) for a, e in terms)
    # sympy cross-check
    xs = sp.symbols(f"x0:{len(terms)}")
    poly = sp.expand(sum(a * x for (a, _), x in zip(terms, xs)) ** n)
    mono = prod(x ** e for (_, e), x in zip(terms, xs))
    coeff = sp.Poly(poly, *xs).coeff_monomial(mono) if poly != 0 else 0
    assert coeff == mult * pr, (terms, coeff, mult * pr)
    return OrderedDict([("n", n), ("multinomial", mult), ("product", pr), ("coefficient", mult * pr)])


def build_stacnt():
    P = "STACNT"
    # ---- A
    add("CNT-A-S1", P, "A", "spec", "N=5, R=2", {"N": 5, "R": 2}, cnt_a(5, 2),
        spec={"n!": "120", "r!": "2", "nPr": "20", "nCr": "10", "n^r": "25", "C(n+r-1,r)": "15"})
    add("CNT-A-S2", P, "A", "spec", "N=12, R=3", {"N": 12, "R": 3}, cnt_a(12, 3),
        spec={"n!": "479001600", "r!": "6", "nPr": "1320", "nCr": "220", "n^r": "1728", "C(n+r-1,r)": "364"})
    add("CNT-A-E1", P, "A", "edge", "r>n: N=3, R=5", {"N": 3, "R": 5}, cnt_a(3, 5),
        notes="nPr=nCr=0 when r>n (SPEC rule 15). Multisets C(7,5)=21 still valid.")
    add("CNT-A-E2", P, "A", "edge", "N=0, R=0", {"N": 0, "R": 0}, cnt_a(0, 0),
        notes="Real TI-84: 0^0 gives ERR:DOMAIN and (-1) nCr 0 gives ERR:DOMAIN; the tool must special-case "
              "n^r=1 when r=0 and C(n+r-1,r)=1 when n=0,r=0 (0 when n=0,r>0).")
    add("CNT-A-E3", P, "A", "edge", "N=70, R=2 (n! too big)", {"N": 70, "R": 2}, cnt_a(70, 2),
        notes="n! must show TOO BIG (70! overflows 1E100). nPr=4830, nCr=2415 are still computable.")
    add("CNT-A-E4", P, "A", "edge", "N=2.5, R=1 (non-integer)", {"N": 2.5, "R": 1},
        OrderedDict([("result", "REJECT (N,R must be non-negative integers)")]))
    # ---- B
    add("CNT-B-S1", P, "B", "spec", "WORD=PROBABILITY, letter B (block / not together)",
        {"word": "PROBABILITY", "letter": "B"}, cnt_b("PROBABILITY", "B"),
        spec={"n": "11", "total": "9979200", "block": "1814400", "not together": "8164800"})
    add("CNT-B-S2", P, "B", "spec", "WORD=MISSISSIPPI, letter S", {"word": "MISSISSIPPI", "letter": "S"},
        cnt_b("MISSISSIPPI", "S"), spec={"total": "34650", "block": "840"})
    add("CNT-B-S3", P, "B", "spec", "WORD=STATISTICS", {"word": "STATISTICS"}, cnt_b("STATISTICS"),
        spec={"total": "50400"})
    add("CNT-B-E1", P, "B", "edge", "WORD=BOOKKEEPER, letter E", {"word": "BOOKKEEPER", "letter": "E"},
        cnt_b("BOOKKEEPER", "E"))
    add("CNT-B-E2", P, "B", "edge", "WORD=AAB, letter B (a single letter: block = total)",
        {"word": "AAB", "letter": "B"}, cnt_b("AAB", "B"),
        notes="k=1: block formula (n-1+1)!/prod = total, not-together = 0.")
    add("CNT-B-E3", P, "B", "edge", "WORD=AAB, letter A", {"word": "AAB", "letter": "A"}, cnt_b("AAB", "A"))
    add("CNT-B-E4", P, "B", "edge", "WORD=MATH, letter Z (not in word)", {"word": "MATH", "letter": "Z"},
        cnt_b("MATH", "Z"),
        notes="Letter absent: naive formula would give (n+1)!/prod = 120; tool should reject or say 0 copies.")
    # ---- C
    add("CNT-C-S1", P, "C", "spec", "C1 split sizes 3,4,5 (labeled)", {"mode": "C1", "sizes": [3, 4, 5]},
        cnt_c1([3, 4, 5]), spec={"labeled": "27720"})
    add("CNT-C-S2", P, "C", "spec", "C1 split sizes 2,2,2", {"mode": "C1", "sizes": [2, 2, 2]},
        cnt_c1([2, 2, 2]), spec={"labeled": "90", "unlabeled": "15"})
    add("CNT-C-S3", P, "C", "spec", "C1 split sizes 4,4,2", {"mode": "C1", "sizes": [4, 4, 2]},
        cnt_c1([4, 4, 2]), spec={"labeled": "3150", "unlabeled": "1575"})
    add("CNT-C-S4", P, "C", "spec", "C2 N=10, exact counts 3,1, F=3 free choices",
        {"mode": "C2", "N": 10, "counts": [3, 1], "F": 3}, cnt_c2(10, [3, 1], 3),
        spec={"multinomial": "840", "F^r": "729", "total": "612360"})
    add("CNT-C-S5", P, "C", "spec", "C2 N=5, exact count 2, F=4", {"mode": "C2", "N": 5, "counts": [2], "F": 4},
        cnt_c2(5, [2], 4), spec={"multinomial": "10", "F^r": "64", "total": "640"})
    add("CNT-C-E1", P, "C", "edge", "C1 sizes 1,1,1", {"mode": "C1", "sizes": [1, 1, 1]}, cnt_c1([1, 1, 1]))
    add("CNT-C-E2", P, "C", "edge", "C1 sizes 2,2,2,2 (8 people into 4 pairs)", {"mode": "C1", "sizes": [2, 2, 2, 2]},
        cnt_c1([2, 2, 2, 2]))
    add("CNT-C-E3", P, "C", "edge", "C2 N=4, counts 2,2, F=0 (r=0 -> F^0=1)", {"mode": "C2", "N": 4, "counts": [2, 2], "F": 0},
        cnt_c2(4, [2, 2], 0), notes="0^0 must be 1 here (TI gives ERR:DOMAIN for 0^0; guard r=0).")
    add("CNT-C-E4", P, "C", "edge", "C2 N=5, counts 3,3 (sum > N)", {"mode": "C2", "N": 5, "counts": [3, 3], "F": 2},
        cnt_c2(5, [3, 3], 2))
    # ---- D
    add("CNT-D-S1", P, "D", "spec", "A=8 (G1), B=6 (G2), K=5, G1 at least 2, G1 at most 99, G2 at least 2, G2 at most 99",
        {"A": 8, "B": 6, "K": 5, "G1min": 2, "G1max": 99, "G2min": 2, "G2max": 99}, cnt_d(8, 6, 5, 2, 99, 2, 99),
        spec={"i=2": "28*20=560", "i=3": "56*15=840", "total": "1400", "P": "100/143"})
    add("CNT-D-S2", P, "D", "spec", "A=5, B=15, K=15, G1 exactly 2 (min=max=2), G2 min 0 max 99",
        {"A": 5, "B": 15, "K": 15, "G1min": 2, "G1max": 2, "G2min": 0, "G2max": 99}, cnt_d(5, 15, 15, 2, 2, 0, 99),
        spec={"i=2": "10*105=1050", "total": "1050", "P": "175/2584"})
    add("CNT-D-E1", P, "D", "edge", "A=8, B=6, K=5, no constraints (0,99,0,99)",
        {"A": 8, "B": 6, "K": 5, "G1min": 0, "G1max": 99, "G2min": 0, "G2max": 99}, cnt_d(8, 6, 5, 0, 99, 0, 99),
        notes="Vandermonde check: total = C(14,5) = 2002, P = 1.")
    add("CNT-D-E2", P, "D", "edge", "A=8, B=6, K=5, G1 at least 4, G2 at least 2 (impossible)",
        {"A": 8, "B": 6, "K": 5, "G1min": 4, "G1max": 99, "G2min": 2, "G2max": 99}, cnt_d(8, 6, 5, 4, 99, 2, 99),
        notes="Empty i range -> total 0, P = 0 (no terms listed).")
    add("CNT-D-E3", P, "D", "edge", "A=3, B=2, K=6 (K > A+B)",
        {"A": 3, "B": 2, "K": 6, "G1min": 0, "G1max": 99, "G2min": 0, "G2max": 99}, cnt_d(3, 2, 6, 0, 99, 0, 99),
        notes="C(5,6)=0 -> division by zero if not guarded.")
    add("CNT-D-E4", P, "D", "edge", "A=8, B=6, K=5, G1 at most 1 (G2 at least 0, at most 99)",
        {"A": 8, "B": 6, "K": 5, "G1min": 0, "G1max": 1, "G2min": 0, "G2max": 99}, cnt_d(8, 6, 5, 0, 1, 0, 99))
    # ---- E
    add("CNT-E-S1", P, "E", "spec", "n=15, k=4, same min 1", {"n": 15, "k": 4, "mins": [1, 1, 1, 1]},
        cnt_e(15, 4, [1, 1, 1, 1]), spec={"ways": "364", "shown": "C(14,3)=364"})
    add("CNT-E-S2", P, "E", "spec", "n=15, k=4, mins 3,1,1,1", {"n": 15, "k": 4, "mins": [3, 1, 1, 1]},
        cnt_e(15, 4, [3, 1, 1, 1]), spec={"ways": "220"})
    add("CNT-E-S3", P, "E", "spec", "n=10, k=3, min 0", {"n": 10, "k": 3, "mins": [0, 0, 0]},
        cnt_e(10, 3, [0, 0, 0]), spec={"ways": "66"})
    add("CNT-E-E1", P, "E", "edge", "n=3, k=4, min 1 each (n'<0)", {"n": 3, "k": 4, "mins": [1, 1, 1, 1]},
        cnt_e(3, 4, [1, 1, 1, 1]), notes="n'=-1 -> 0 ways (do not call nCr with negative args).")
    add("CNT-E-E2", P, "E", "edge", "n=4, k=4, min 1 each (n'=0)", {"n": 4, "k": 4, "mins": [1, 1, 1, 1]},
        cnt_e(4, 4, [1, 1, 1, 1]))
    add("CNT-E-E3", P, "E", "edge", "n=7, k=1, min 0", {"n": 7, "k": 1, "mins": [0]}, cnt_e(7, 1, [0]))
    # ---- F
    add("CNT-F-S1", P, "F", "spec", "(2x-y+3z)^7, x^3 y^2 z^2: terms (2,3),(-1,2),(3,2)",
        {"terms": [[2, 3], [-1, 2], [3, 2]]}, cnt_f([(2, 3), (-1, 2), (3, 2)]),
        spec={"n": "7", "multinomial": "210", "product": "72", "coefficient": "15120"})
    add("CNT-F-S2", P, "F", "spec", "(x+2)^5 coefficient of x^3: terms (1,3),(2,2)",
        {"terms": [[1, 3], [2, 2]]}, cnt_f([(1, 3), (2, 2)]),
        spec={"multinomial": "10", "product": "4", "coefficient": "40"})
    add("CNT-F-S3", P, "F", "spec", "(3x-2y)^4 x^2 y^2: terms (3,2),(-2,2)",
        {"terms": [[3, 2], [-2, 2]]}, cnt_f([(3, 2), (-2, 2)]),
        spec={"multinomial": "6", "product": "36", "coefficient": "216"})
    add("CNT-F-E1", P, "F", "edge", "(x-2)^5 coefficient of x^2: terms (1,2),(-2,3)",
        {"terms": [[1, 2], [-2, 3]]}, cnt_f([(1, 2), (-2, 3)]), notes="Negative result shown as ⁻80.")
    add("CNT-F-E2", P, "F", "edge", "(x+0y)^3 coefficient of x^3 y^0: terms (1,3),(0,0)",
        {"terms": [[1, 3], [0, 0]]}, cnt_f([(1, 3), (0, 0)]), notes="0^0 must count as 1 (TI: ERR:DOMAIN).")
    add("CNT-F-E3", P, "F", "edge", "(2a+b-c)^6, a^2 b^1 c^3: terms (2,2),(1,1),(-1,3)",
        {"terms": [[2, 2], [1, 1], [-1, 3]]}, cnt_f([(2, 2), (1, 1), (-1, 3)]))


# ========================================================================================
# STAPRB
# ========================================================================================
a_, b_, i_ = sp.symbols("a b i", real=True)


def prb_a_solve(known, rel="none"):
    """known: dict with keys among A,B,I,U,C,D,N (Fractions). Solve for (A,B,I) with sympy."""
    eqs = []
    for k, v in known.items():
        v = sp.Rational(v.numerator, v.denominator)
        if k == "A":
            eqs.append(a_ - v)
        elif k == "B":
            eqs.append(b_ - v)
        elif k == "I":
            eqs.append(i_ - v)
        elif k == "U":
            eqs.append(a_ + b_ - i_ - v)
        elif k == "N":
            eqs.append(1 - (a_ + b_ - i_) - v)
        elif k == "C":   # P(A|B) = I/B
            eqs.append(i_ - v * b_)
        elif k == "D":   # P(B|A) = I/A
            eqs.append(i_ - v * a_)
    if rel == "indep":
        eqs.append(i_ - a_ * b_)
    elif rel == "excl":
        eqs.append(i_)
    sols = sp.solve(eqs, [a_, b_, i_], dict=True)
    good = []
    for s in sols:
        if len(s) < 3 or any(not s[x].is_number for x in (a_, b_, i_)):
            continue
        vals = [Fr(str(s[x])) for x in (a_, b_, i_)]
        if all(0 <= t <= 1 for t in vals) and vals[0] > 0 and vals[1] > 0 or all(0 <= t <= 1 for t in vals):
            good.append(tuple(vals))
    good = sorted(set(good))
    if len(good) != 1:
        return None
    return good[0]


def prb_a_outputs(A, B, I):
    U = A + B - I
    o = OrderedDict()
    o["P(A)"] = A
    o["P(B)"] = B
    o["P(AnB)"] = I
    o["P(AuB)"] = U
    o["P(A')"] = 1 - A
    o["P(B')"] = 1 - B
    o["P(A'nB')"] = 1 - U
    o["P(AnB')"] = A - I
    o["P(A'nB)"] = B - I
    o["P(A|B)"] = I / B if B else "undef"
    o["P(B|A)"] = I / A if A else "undef"
    o["P(A|B')"] = (A - I) / (1 - B) if B != 1 else "undef"
    o["P(B|A')"] = (B - I) / (1 - A) if A != 1 else "undef"
    o["P(A'|B)"] = (B - I) / B if B else "undef"
    o["P(B'|A)"] = (A - I) / A if A else "undef"
    o["P(exactly one)"] = A + B - 2 * I
    o["P(A)P(B)"] = A * B
    o["independent?"] = (A * B == I)
    o["mutually exclusive?"] = (I == 0)
    warn = []
    for nm, v in (("P(A)", A), ("P(B)", B), ("P(AnB)", I), ("P(AuB)", U)):
        if v < 0 or v > 1:
            warn.append(f"{nm} outside [0,1]")
    if I > min(A, B):
        warn.append("P(AnB) > min(P(A),P(B))")
    if U > 1:
        warn.append("P(AuB) > 1")
    o["warnings"] = "; ".join(warn) if warn else "none"
    return o


def prb_a(known, rel="none"):
    sol = prb_a_solve(known, rel)
    if sol is None:
        return OrderedDict([("result", "NOT ENOUGH INFO")])
    return prb_a_outputs(*sol)


def prb_b(cells):
    """cells: dict with keys R1C1,R1C2,R1,R2C1,R2C2,R2,C1,C2,N -> Fraction or None (unknown)."""
    names = ["R1C1", "R1C2", "R1", "R2C1", "R2C2", "R2", "C1", "C2", "N"]
    sy = {n: sp.Symbol(n) for n in names}
    eqs = [sy["R1C1"] + sy["R1C2"] - sy["R1"], sy["R2C1"] + sy["R2C2"] - sy["R2"],
           sy["R1C1"] + sy["R2C1"] - sy["C1"], sy["R1C2"] + sy["R2C2"] - sy["C2"],
           sy["R1"] + sy["R2"] - sy["N"], sy["C1"] + sy["C2"] - sy["N"]]
    subs = {sy[n]: sp.Rational(v.numerator, v.denominator) for n, v in cells.items() if v is not None}
    eqs2 = [e.subs(subs) for e in eqs]
    unknown = [sy[n] for n in names if cells.get(n) is None]
    out = OrderedDict()
    sol = sp.solve([e for e in eqs2 if e != 0], unknown, dict=True) if unknown else [{}]
    if not sol:
        out["result"] = "INCONSISTENT TOTALS (warn)"
        return out
    s = sol[0]
    full = {}
    for n in names:
        if cells.get(n) is not None:
            full[n] = cells[n]
        elif sy[n] in s and s[sy[n]].is_number:
            full[n] = Fr(str(s[sy[n]]))
        else:
            full[n] = None
    for n in names:
        out[n] = full[n] if full[n] is not None else "unknown"
    if any(v is None for v in full.values()):
        out["result"] = "NOT ENOUGH INFO (some cells stay unknown)"
        return out
    Nn = full["N"]
    j = {k: full[k] / Nn for k in ("R1C1", "R1C2", "R2C1", "R2C2", "R1", "R2", "C1", "C2")}
    out["P(R1nC1)"] = j["R1C1"]
    out["P(R1nC2)"] = j["R1C2"]
    out["P(R2nC1)"] = j["R2C1"]
    out["P(R2nC2)"] = j["R2C2"]
    out["P(R1)"] = j["R1"]
    out["P(R2)"] = j["R2"]
    out["P(C1)"] = j["C1"]
    out["P(C2)"] = j["C2"]
    for r in ("R1", "R2"):
        for c in ("C1", "C2"):
            out[f"P({r}|{c})"] = full[r + c] / full[c] if full[c] else "undef"
    for c in ("C1", "C2"):
        for r in ("R1", "R2"):
            out[f"P({c}|{r})"] = full[r + c] / full[r] if full[r] else "undef"
    out["P(R1)P(C1)"] = j["R1"] * j["C1"]
    out["independent?"] = (j["R1"] * j["C1"] == j["R1C1"])
    # consistency of given data
    ok = all(e.subs({sy[n]: sp.Rational(full[n].numerator, full[n].denominator) for n in names}) == 0 for e in eqs)
    out["totals consistent?"] = ok
    return out


def prb_c(priors, liks):
    notes = []
    tot = sum(priors)
    rescaled = (tot != 1)
    pri = [p / tot for p in priors]
    lk = [l / 100 if l > 1 else l for l in liks]
    if any(l > 1 for l in liks):
        notes.append("likelihood > 1 treated as percent")
    terms = [l * p for l, p in zip(lk, pri)]
    PA = sum(terms)
    o = OrderedDict()
    o["rescaled?"] = rescaled
    for idx, p in enumerate(pri, 1):
        o[f"P(B{idx})"] = p
    for idx, t in enumerate(terms, 1):
        o[f"P(A|B{idx})P(B{idx})"] = t
    o["P(A)"] = PA
    for idx, t in enumerate(terms, 1):
        o[f"P(B{idx}|A)"] = t / PA if PA else "undef"
    o["P(A')"] = 1 - PA
    for idx, (l, p) in enumerate(zip(lk, pri), 1):
        o[f"P(B{idx}|A')"] = (1 - l) * p / (1 - PA) if PA != 1 else "undef"
    return o


def prb_d(p, sens, spec, result, followups=()):
    pc = lambda v: v / 100 if v > 1 else v  # noqa: E731
    p, sens, spec = pc(p), pc(sens), pc(spec)
    o = OrderedDict()
    Ppos = sens * p + (1 - spec) * (1 - p)
    Pneg = 1 - Ppos
    o["P(+)"] = Ppos
    o["P(-)"] = Pneg
    o["PPV=P(D|+)"] = sens * p / Ppos if Ppos else "undef"
    o["NPV=P(D'|-)"] = spec * (1 - p) / Pneg if Pneg else "undef"
    o["P(D|-)"] = (1 - sens) * p / Pneg if Pneg else "undef"
    post = o["PPV=P(D|+)"] if result == "+" else o["P(D|-)"]
    o["posterior (chosen result)"] = post
    for n, (s2, sp2, r2) in enumerate(followups, 2):
        s2, sp2 = pc(s2), pc(sp2)
        prior = post
        Pp = s2 * prior + (1 - sp2) * (1 - prior)
        Pn = 1 - Pp
        o[f"test{n} P(+)"] = Pp
        o[f"test{n} P(-)"] = Pn
        if r2 == "+":
            post = s2 * prior / Pp if Pp else "undef"
        else:
            post = (1 - s2) * prior / Pn if Pn else "undef"
        o[f"UPDATED P(D) after test{n}"] = post
    return o


def prb_e3(a, b, c, ab, ac, bc, abc, N):
    o = OrderedDict()
    o["A only"] = a - ab - ac + abc
    o["B only"] = b - ab - bc + abc
    o["C only"] = c - ac - bc + abc
    o["AnB only"] = ab - abc
    o["AnC only"] = ac - abc
    o["BnC only"] = bc - abc
    o["all 3"] = abc
    un = a + b + c - ab - ac - bc + abc
    o["union"] = un
    o["none"] = (N - un) if N is not None else "n/a (N unknown)"
    o["exactly 1"] = o["A only"] + o["B only"] + o["C only"]
    o["exactly 2"] = o["AnB only"] + o["AnC only"] + o["BnC only"]
    o["at least 2"] = o["exactly 2"] + abc
    regs = [o[k] for k in ("A only", "B only", "C only", "AnB only", "AnC only", "BnC only", "all 3")]
    if N is not None:
        regs.append(o["none"])
    o["negative region warning?"] = any(r < 0 for r in regs)
    return o


def prb_e2(a, b, ab, N):
    o = OrderedDict()
    o["A only"] = a - ab
    o["B only"] = b - ab
    o["union"] = a + b - ab
    o["neither"] = (N - (a + b - ab)) if N is not None else "n/a (N unknown)"
    o["exactly one"] = a + b - 2 * ab
    return o


def hyper(N, K, n, k):
    if n > N or n < 0:
        return None
    return Fr(comb(K, k) * comb(N - K, n - k), comb(N, n)) if 0 <= k <= n else Fr(0)


def binom(n, p, k):
    return Fr(comb(n, k)) * p ** k * (1 - p) ** (n - k) if 0 <= k <= n else Fr(0)


def prb_f(N, K, n, k):
    o = OrderedDict()
    if n <= N:
        pk = hyper(N, K, n, k)
        ge = sum((hyper(N, K, n, j) for j in range(max(k, 0), n + 1)), Fr(0))
        le = sum((hyper(N, K, n, j) for j in range(0, min(k, n) + 1)), Fr(0))
        # brute-force enumeration check for small urns
        if N <= 9:
            balls = [1] * K + [0] * (N - K)
            draws = list(itertools.permutations(range(N), n))
            cnt = sum(1 for d in draws if sum(balls[x] for x in d) == k)
            assert Fr(cnt, len(draws)) == pk
        o["w/o P(X=k)"] = pk
        o["w/o P(X>=k)"] = ge
        o["w/o P(X<=k)"] = le
    else:
        o["w/o"] = "n/a (n > N: cannot draw without replacement)"
    p = Fr(K, N)
    o["with P(X=k)"] = binom(n, p, k)
    o["with P(X>=k)"] = sum((binom(n, p, j) for j in range(max(k, 0), n + 1)), Fr(0))
    o["with P(X<=k)"] = sum((binom(n, p, j) for j in range(0, min(k, n) + 1)), Fr(0))
    if 0 <= k <= n:
        if n <= N:
            o["specific order w/o"] = o["w/o P(X=k)"] / comb(n, k)
            # direct product check: first k successes then n-k failures
            direct = prod(Fr(K - t, N - t) for t in range(k)) * prod(Fr(N - K - t, N - k - t) for t in range(n - k)) \
                if k <= K and n - k <= N - K else Fr(0)
            assert direct == o["specific order w/o"], (direct, o["specific order w/o"])
        o["specific order with"] = o["with P(X=k)"] / comb(n, k)
    else:
        o["specific order"] = "undef (k>n: C(n,k)=0, guard the division)"
    return o


def build_staprb():
    P = "STAPRB"
    F = Fr
    # ---- A
    add("PRB-A-S1", P, "A", "spec", "P(A)=.55, P(B)=.35, P(AuB)=.7, others unknown; NO EXTRA INFO",
        {"A": ".55", "B": ".35", "AnB": -1, "AuB": ".7", "A|B": -1, "B|A": -1, "neither": -1, "relation": "NO EXTRA INFO"},
        prb_a({"A": F(55, 100), "B": F(35, 100), "U": F(7, 10)}),
        spec={"P(AnB)": "1/5", "P(A|B)": "4/7", "P(B|A)": "4/11", "P(B|A')": "1/3", "P(A|B')": "7/13",
              "P(A'nB')": "3/10", "P(AnB')": "7/20", "P(A'nB)": "3/20", "P(exactly one)": "1/2",
              "independent?": "NO", "P(A)P(B)": ".1925"})
    add("PRB-A-S2", P, "A", "spec", "P(A)=.3, P(B)=.4, INDEPENDENT",
        {"A": ".3", "B": ".4", "relation": "INDEPENDENT"}, prb_a({"A": F(3, 10), "B": F(4, 10)}, "indep"),
        spec={"P(AnB)": "3/25", "P(AuB)": "29/50"})
    add("PRB-A-S3", P, "A", "spec", "P(AnB)=.1, P(A|B)=.25, P(B|A)=.5; NO EXTRA INFO",
        {"AnB": ".1", "A|B": ".25", "B|A": ".5", "relation": "NO EXTRA INFO"},
        prb_a({"I": F(1, 10), "C": F(1, 4), "D": F(1, 2)}),
        spec={"P(B)": "2/5", "P(A)": "1/5", "P(AuB)": "1/2"})
    add("PRB-A-E1", P, "A", "edge", "P(A)=.3, P(B)=.4, MUTUALLY EXCL.",
        {"A": ".3", "B": ".4", "relation": "MUTUALLY EXCL."}, prb_a({"A": F(3, 10), "B": F(2, 5)}, "excl"),
        notes="Disjoint => NOT independent (P(A)P(B)=.12 ≠ 0).")
    add("PRB-A-E2", P, "A", "edge", "P(A)=0, P(B)=.5, P(AuB)=.5 (zero-probability conditioning)",
        {"A": "0", "B": ".5", "AuB": ".5"}, prb_a({"A": F(0), "B": F(1, 2), "U": F(1, 2)}),
        notes="P(B|A), P(B'|A) must show undef (condition has probability 0). A=0 counts as independent.")
    add("PRB-A-E3", P, "A", "edge", "P(A)=.5, P(AuB)=.8, P(A|B)=.25 (uses B=(U-A)/(1-C))",
        {"A": ".5", "AuB": ".8", "A|B": ".25"}, prb_a({"A": F(1, 2), "U": F(4, 5), "C": F(1, 4)}))
    add("PRB-A-E4", P, "A", "edge", "P(AuB)=.5, P(A|B)=.25, P(B|A)=.5 (uses I=U/(1/C+1/D-1))",
        {"AuB": ".5", "A|B": ".25", "B|A": ".5"}, prb_a({"U": F(1, 2), "C": F(1, 4), "D": F(1, 2)}))
    add("PRB-A-E5", P, "A", "edge", "P(A)=.5 only", {"A": ".5"}, prb_a({"A": F(1, 2)}))
    add("PRB-A-E6", P, "A", "edge", "P(NEITHER)=.3, P(A)=.55, P(B)=.35", {"A": ".55", "B": ".35", "neither": ".3"},
        prb_a({"A": F(55, 100), "B": F(35, 100), "N": F(3, 10)}), notes="Same results as PRB-A-S1.")
    add("PRB-A-E7", P, "A", "edge", "P(A)=.3, P(B)=.4, P(AnB)=.5 (invalid data)", {"A": ".3", "B": ".4", "AnB": ".5"},
        prb_a_outputs(F(3, 10), F(2, 5), F(1, 2)),
        notes="Validity warning expected: P(AnB) > min(P(A),P(B)); A only / B only negative.")
    # ---- B
    add("PRB-B-S1", P, "B", "spec", "R1C1=40, R1 total=70, R2 total=50, C1 total=65, N=120, others unknown "
        "(HW2 Q3: R1=grad, R2=faculty, C1=female, C2=male)",
        {"R1C1": 40, "R1C2": -1, "R1": 70, "R2C1": -1, "R2C2": -1, "R2": 50, "C1": 65, "C2": -1, "N": 120},
        prb_b({"R1C1": F(40), "R1": F(70), "R2": F(50), "C1": F(65), "N": F(120),
               "R1C2": None, "R2C1": None, "R2C2": None, "C2": None}),
        spec={"R1C2": "30", "R2C1": "25", "R2C2": "25", "C2": "55", "P(R2nC2)": "5/24", "P(R1|C1)": "8/13",
              "P(C1|R1)": "4/7", "independent?": "NO"})
    add("PRB-B-E1", P, "B", "edge", "probabilities: R1C1=.2, R1 total=.5, C1 total=.4, N=1, others unknown",
        {"R1C1": ".2", "R1": ".5", "C1": ".4", "N": "1"},
        prb_b({"R1C1": F(1, 5), "R1": F(1, 2), "C1": F(2, 5), "N": F(1),
               "R1C2": None, "R2C1": None, "R2C2": None, "R2": None, "C2": None}),
        notes="Independent: P(R1)P(C1) = .2 = P(R1nC1).")
    add("PRB-B-E2", P, "B", "edge", "R1C1=10, R1C2=20, R1 total=40 (inconsistent), rest unknown",
        {"R1C1": 10, "R1C2": 20, "R1": 40},
        prb_b({"R1C1": F(10), "R1C2": F(20), "R1": F(40),
               "R2C1": None, "R2C2": None, "R2": None, "C1": None, "C2": None, "N": None}),
        notes="Must warn: 10+20 ≠ 40.")
    add("PRB-B-E3", P, "B", "edge", "only R1C1=10 and N=100 known", {"R1C1": 10, "N": 100},
        prb_b({"R1C1": F(10), "N": F(100),
               "R1C2": None, "R1": None, "R2C1": None, "R2C2": None, "R2": None, "C1": None, "C2": None}))
    # ---- C
    add("PRB-C-S1", P, "C", "spec", "k=3, priors .5,.3,.2, likelihoods .15,.25,.10 (HW2 Q4)",
        {"priors": [".5", ".3", ".2"], "liks": [".15", ".25", ".10"]},
        prb_c([F(1, 2), F(3, 10), F(1, 5)], [F(15, 100), F(25, 100), F(10, 100)]),
        spec={"P(A)": "17/100", "P(B1|A)": "15/34", "P(B2|A)": "15/34", "P(B3|A)": "2/17", "P(A')": "83/100",
              "P(B1|A')": "85/166"})
    add("PRB-C-S2", P, "C", "spec", "k=2, priors 2,4 (rescaled), likelihoods 3/7,5/7 (HW2 Q5)",
        {"priors": ["2", "4"], "liks": ["3/7", "5/7"]}, prb_c([F(2), F(4)], [F(3, 7), F(5, 7)]),
        spec={"P(B1)": "1/3", "P(B2)": "2/3", "P(A)": "13/21", "P(B1|A)": "3/13", "P(B2|A)": "10/13"})
    add("PRB-C-S3", P, "C", "spec", "k=2, priors .6,.4, likelihoods .4,.05 (HW2 431 Q6)",
        {"priors": [".6", ".4"], "liks": [".4", ".05"]}, prb_c([F(3, 5), F(2, 5)], [F(2, 5), F(1, 20)]),
        spec={"P(A)": "13/50", "P(B1|A)": "12/13"})
    add("PRB-C-E1", P, "C", "edge", "percent everywhere: priors 50,30,20; likelihoods 15,25,10",
        {"priors": ["50", "30", "20"], "liks": ["15", "25", "10"]},
        prb_c([F(50), F(30), F(20)], [F(15), F(25), F(10)]), notes="Same answers as PRB-C-S1; rescale note shown.")
    add("PRB-C-E2", P, "C", "edge", "priors .5,.5; likelihoods 1, 0", {"priors": [".5", ".5"], "liks": ["1", "0"]},
        prb_c([F(1, 2), F(1, 2)], [F(1), F(0)]),
        notes="likelihood exactly 1 is NOT percent (only >1).")
    add("PRB-C-E3", P, "C", "edge", "priors .5,.5; likelihoods 0, 0 (P(A)=0)", {"priors": [".5", ".5"], "liks": ["0", "0"]},
        prb_c([F(1, 2), F(1, 2)], [F(0), F(0)]), notes="Posteriors given A undefined (division by P(A)=0).")
    add("PRB-C-E4", P, "C", "edge", "counts 1,1,1 as priors; likelihoods 20,50,80 (percent)",
        {"priors": ["1", "1", "1"], "liks": ["20", "50", "80"]}, prb_c([F(1), F(1), F(1)], [F(20), F(50), F(80)]))
    # ---- D
    add("PRB-D-S1", P, "D", "spec", "p=.005, sens=.95, spec=.99, result +; then ANOTHER TEST sens .90, spec .95, + "
        "(HW2 631 Q7)", {"p": ".005", "sens": ".95", "spec": ".99", "result": "+",
                         "next": [{"sens": ".90", "spec": ".95", "result": "+"}]},
        prb_d(F(5, 1000), F(95, 100), F(99, 100), "+", [(F(9, 10), F(95, 100), "+")]),
        spec={"P(+)": "147/10000", "PPV=P(D|+)": "95/294", "UPDATED P(D) after test2": "1710/1909"},
        notes="Prevalence 0.5% must be typed .005 (typing .5 is read as 50%, since only values >1 are percent).")
    add("PRB-D-E1", P, "D", "edge", "percent inputs p=.005, sens=95, spec=99, result -",
        {"p": ".005", "sens": "95", "spec": "99", "result": "-"}, prb_d(F(5, 1000), F(95), F(99), "-"))
    add("PRB-D-E2", P, "D", "edge", "p=.005, sens .95, spec .99, +; then second test sens .9, spec .95, result -",
        {"p": ".005", "sens": ".95", "spec": ".99", "result": "+", "next": [{"sens": ".9", "spec": ".95", "result": "-"}]},
        prb_d(F(5, 1000), F(95, 100), F(99, 100), "+", [(F(9, 10), F(95, 100), "-")]))
    add("PRB-D-E3", P, "D", "edge", "p=.2, sens=0, spec=1, result + (P(+)=0)", {"p": ".2", "sens": "0", "spec": "1", "result": "+"},
        prb_d(F(1, 5), F(0), F(1), "+"), notes="PPV undefined: zero-probability conditioning must not crash.")
    add("PRB-D-E4", P, "D", "edge", "p=0, sens .9, spec .95, result +", {"p": "0", "sens": ".9", "spec": ".95", "result": "+"},
        prb_d(F(0), F(9, 10), F(95, 100), "+"))
    # ---- E
    add("PRB-E-S1", P, "E", "spec", "3 SETS: n(A)=400,n(B)=500,n(C)=600,n(AnB)=200,n(AnC)=150,n(BnC)=250,"
        "n(AnBnC)=100,N=1000 (HW2 431 Q7: A=Digital,B=Print,C=Weekend)",
        {"mode": 3, "values": [400, 500, 600, 200, 150, 250, 100, 1000]},
        prb_e3(400, 500, 600, 200, 150, 250, 100, 1000),
        spec={"A only": "150", "B only": "150", "C only": "300", "AnB only": "100", "AnC only": "50", "BnC only": "150",
              "all 3": "100", "union": "1000", "none": "0", "exactly 1": "600", "exactly 2": "300", "at least 2": "400"})
    add("PRB-E-S2", P, "E", "spec", "2 SETS: P(A)=.5, P(B)=.4, P(AnB)=.2, N=1",
        {"mode": 2, "values": [".5", ".4", ".2", "1"]}, prb_e2(F(1, 2), F(2, 5), F(1, 5), F(1)),
        spec={"A only": ".3", "B only": ".2", "union": ".7", "neither": ".3", "exactly one": ".5"})
    add("PRB-E-E1", P, "E", "edge", "3 SETS with N unknown: 400,500,600,200,150,250,100,N=-1",
        {"mode": 3, "values": [400, 500, 600, 200, 150, 250, 100, -1]}, prb_e3(400, 500, 600, 200, 150, 250, 100, None))
    add("PRB-E-E2", P, "E", "edge", "3 SETS inconsistent: 10,10,10,8,8,8,1,N=30",
        {"mode": 3, "values": [10, 10, 10, 8, 8, 8, 1, 30]}, prb_e3(10, 10, 10, 8, 8, 8, 1, 30),
        notes="Must warn: some regions negative.")
    add("PRB-E-E3", P, "E", "edge", "2 SETS disjoint counts: 30,20,0,N=100", {"mode": 2, "values": [30, 20, 0, 100]},
        prb_e2(30, 20, 0, 100))
    # ---- F
    add("PRB-F-S1", P, "F", "spec", "N=7, K=3, n=2, k=1", {"N": 7, "K": 3, "n": 2, "k": 1}, prb_f(7, 3, 2, 1),
        spec={"w/o P(X=k)": "4/7", "w/o P(X>=k)": "5/7", "w/o P(X<=k)": "6/7", "with P(X=k)": "24/49",
              "with P(X>=k)": "33/49", "with P(X<=k)": "40/49", "specific order w/o": "2/7",
              "specific order with": "12/49"})
    add("PRB-F-S2", P, "F", "spec", "N=52, K=4, n=5, k=2 (two aces in a poker hand)", {"N": 52, "K": 4, "n": 5, "k": 2},
        prb_f(52, 4, 5, 2), spec={"w/o P(X=k)": ".03993"},
        notes="Exact value 2162/54145 has denominator > 9999, so the calculator shows only .03993.")
    add("PRB-F-E1", P, "F", "edge", "N=7, K=3, n=2, k=3 (k>n)", {"N": 7, "K": 3, "n": 2, "k": 3}, prb_f(7, 3, 2, 3))
    add("PRB-F-E2", P, "F", "edge", "N=10, K=4, n=3, k=0", {"N": 10, "K": 4, "n": 3, "k": 0}, prb_f(10, 4, 3, 0))
    add("PRB-F-E3", P, "F", "edge", "N=3, K=1, n=5, k=1 (n>N)", {"N": 3, "K": 1, "n": 5, "k": 1}, prb_f(3, 1, 5, 1),
        notes="Without replacement impossible (C(3,5)=0: guard division); with replacement fine.")


# ========================================================================================
# STARV
# ========================================================================================


def rv_a(xs, ps, mode="p", query=None, Fat=None):
    pairs = sorted(zip(xs, ps))
    xs = [x for x, _ in pairs]
    vals = [v for _, v in pairs]
    if mode == "p":
        p = vals
    elif mode == "w":
        tot = sum(vals)
        p = [v / tot for v in vals]
    else:   # CDF values
        p = [vals[0]] + [vals[t] - vals[t - 1] for t in range(1, len(vals))]
    Fv = list(itertools.accumulate(p))
    o = OrderedDict()
    for x, pi, Fi in zip(xs, p, Fv):
        o[f"p({exact_str(x)})"] = pi
    for x, pi, Fi in zip(xs, p, Fv):
        o[f"F({exact_str(x)})"] = Fi
    o["sum p"] = sum(p)
    o["warn sum≠1?"] = (sum(p) != 1)
    o["warn negative p?"] = any(v < 0 for v in p)
    E = sum(x * pi for x, pi in zip(xs, p))
    E2 = sum(x * x * pi for x, pi in zip(xs, p))
    o["E[X]"] = E
    o["E[X^2]"] = E2
    V = E2 - E * E
    o["Var(X)"] = V
    sd = sp.sqrt(sp.Rational(V.numerator, V.denominator))
    o["SD(X)"] = Fr(str(sd)) if sd.is_rational else Irr(str(sd), mpmath.sqrt(mpmath.mpf(V.numerator) / V.denominator), numeric=False)
    if query:
        a, b = query
        o[f"P({exact_str(a)}<=X<={exact_str(b)})"] = sum((pi for x, pi in zip(xs, p) if a <= x <= b), Fr(0))
        o[f"P({exact_str(a)}<X<={exact_str(b)})"] = sum((pi for x, pi in zip(xs, p) if a < x <= b), Fr(0))
        o[f"P({exact_str(a)}<=X<{exact_str(b)})"] = sum((pi for x, pi in zip(xs, p) if a <= x < b), Fr(0))
        o[f"P({exact_str(a)}<X<{exact_str(b)})"] = sum((pi for x, pi in zip(xs, p) if a < x < b), Fr(0))
    for t in (Fat or []):
        o[f"F({exact_str(t)}) query"] = sum((pi for x, pi in zip(xs, p) if x <= t), Fr(0))
    return o


def rv_b(stat, N, k, repl):
    pool = range(1, N + 1)
    if repl:
        draws = list(itertools.product(pool, repeat=k))
    else:
        draws = list(itertools.permutations(pool, k))
    f = {"max": max, "min": min, "sum": sum, "diff": lambda d: abs(d[0] - d[1])}[stat]
    c = Counter(f(d) for d in draws)
    tot = len(draws)
    o = OrderedDict()
    if tot == 0:
        o["result"] = "invalid (k > N without replacement: C(N,k)=0)"
        return o
    zs = sorted(c)
    # formula cross-check
    for z in zs:
        pz = Fr(c[z], tot)
        if stat == "max":
            fz = Fr(comb(z - 1, k - 1), comb(N, k)) if not repl else Fr(z ** k - (z - 1) ** k, N ** k)
            assert fz == pz
        if stat == "min":
            fz = Fr(comb(N - z, k - 1), comb(N, k)) if not repl else Fr((N - z + 1) ** k - (N - z) ** k, N ** k)
            assert fz == pz
    Fc = Fr(0)
    for z in zs:
        o[f"p({z})"] = Fr(c[z], tot)
    for z in zs:
        Fc += Fr(c[z], tot)
        o[f"F({z})"] = Fc
    return o


x = sp.Symbol("x", real=True)


def rv_c(mode, pieces, unknown_c=False, queries=()):
    """pieces: list of (lo, hi, [C0,C1,C2,C3]) with Fractions. mode 'pdf' or 'cdf'."""
    o = OrderedDict()
    R = lambda f: sp.Rational(f.numerator, f.denominator) if isinstance(f, Fr) else sp.Rational(f)  # noqa: E731
    polys = [(R(lo), R(hi), sum(R(cf) * x ** j for j, cf in enumerate(cs))) for lo, hi, cs in pieces]
    if mode == "pdf":
        area = sum(sp.integrate(p, (x, lo, hi)) for lo, hi, p in polys)
        o["area"] = Fr(str(area))
        if unknown_c:
            if area == 0:
                o["c"] = "undef (area 0)"
                return o
            c = 1 / area
            o["c"] = Fr(str(c))
            polys = [(lo, hi, sp.expand(c * p)) for lo, hi, p in polys]
        else:
            o["warn area≠1?"] = (area != 1)
        neg = False
        for lo, hi, p in polys:
            for t in range(11):
                xv = lo + (hi - lo) * sp.Rational(t, 10)
                if p.subs(x, xv) < 0:
                    neg = True
        o["warn f<0?"] = neg
        # CDF pieces
        Fprev = sp.Integer(0)
        cdf_pieces = []
        prev_hi = None
        for n, (lo, hi, p) in enumerate(polys, 1):
            G = sp.integrate(p, x)  # no constant: C0 x + C1 x^2/2 + ...
            K = Fprev - G.subs(x, lo)
            Fp = sp.expand(K + G)
            cdf_pieces.append((lo, hi, Fp))
            if prev_hi is not None and lo > prev_hi:
                o[f"F on gap {exact_str(Fr(str(prev_hi)))}<=x<={exact_str(Fr(str(lo)))}"] = Fr(str(Fprev))
            poly = sp.Poly(Fp, x)
            o[f"F piece{n} ({exact_str(Fr(str(lo)))}<x<{exact_str(Fr(str(hi)))}) const"] = Fr(str(poly.coeff_monomial(1)))
            for j in range(1, 5):
                cj = poly.coeff_monomial(x ** j)
                if cj != 0:
                    o[f"F piece{n} x^{j}" if j > 1 else f"F piece{n} x"] = Fr(str(cj))
            Fprev = Fp.subs(x, hi)
            prev_hi = hi
        o["F after last piece"] = Fr(str(sp.Integer(1) if abs(Fprev - 1) == 0 else Fprev))

        def Fx(t):
            t = R(t)
            if t <= cdf_pieces[0][0]:
                return sp.Integer(0)
            for n, (lo, hi, Fp) in enumerate(cdf_pieces):
                if lo <= t <= hi:
                    return Fp.subs(x, t)
                if n + 1 < len(cdf_pieces) and hi < t < cdf_pieces[n + 1][0]:
                    return Fp.subs(x, hi)
            return cdf_pieces[-1][2].subs(x, cdf_pieces[-1][1])
    else:  # cdf mode: pieces are F itself
        cdf_pieces = polys
        for n, (lo, hi, Fp) in enumerate(cdf_pieces, 1):
            d = sp.Poly(sp.diff(Fp, x), x)
            o[f"f piece{n} const"] = Fr(str(d.coeff_monomial(1)))
            for j in range(1, 3):
                cj = d.coeff_monomial(x ** j)
                if cj != 0:
                    o[f"f piece{n} x^{j}" if j > 1 else f"f piece{n} x"] = Fr(str(cj))
        F_lo = cdf_pieces[0][2].subs(x, cdf_pieces[0][0])
        F_hi = cdf_pieces[-1][2].subs(x, cdf_pieces[-1][1])
        o["F(lo1)"] = Fr(str(F_lo))
        o["F(hi_m)"] = Fr(str(F_hi))
        o["warn jump (F(lo1)≠0 or F(hi_m)≠1)?"] = (F_lo != 0 or F_hi != 1)

        def Fx(t):
            t = R(t)
            if t < cdf_pieces[0][0]:
                return sp.Integer(0)
            if t >= cdf_pieces[-1][1]:
                return sp.Integer(1)
            for n, (lo, hi, Fp) in enumerate(cdf_pieces):
                if lo <= t < hi:
                    return Fp.subs(x, t)
                if n + 1 < len(cdf_pieces) and hi <= t < cdf_pieces[n + 1][0]:
                    return Fp.subs(x, hi)
            return sp.Integer(1)
    for q in queries:
        kind = q[0]
        if kind == "between":
            a, b = q[1], q[2]
            o[f"P({exact_str(a)}<X<{exact_str(b)})"] = Fr(str(Fx(b) - Fx(a)))
        elif kind == "F":
            o[f"F({exact_str(q[1])})"] = Fr(str(Fx(q[1])))
        elif kind == "gt":
            o[f"P(X>{exact_str(q[1])})"] = Fr(str(1 - Fx(q[1])))
        elif kind == "eq":
            o[f"P(X={exact_str(q[1])})"] = "0 (continuous X)"
    return o


def nderiv(f, t, h=mpmath.mpf("0.001")):
    return (f(t + h) - f(t - h)) / (2 * h)


def build_starv():
    P = "STARV"
    F = Fr
    # ---- A
    add("RV-A-S1", P, "A", "spec", "p(x) VALUES: x=2,3,4,5 p=.1,.2,.3,.4; query a=3,b=4; F(3.5)",
        {"mode": "p(x) VALUES", "x": [2, 3, 4, 5], "p": [".1", ".2", ".3", ".4"], "a": 3, "b": 4, "Fx": "3.5"},
        rv_a([2, 3, 4, 5], [F(1, 10), F(2, 10), F(3, 10), F(4, 10)], "p", (3, 4), [F(7, 2)]),
        spec={"F(2)": "1/10", "F(3)": "3/10", "F(4)": "3/5", "F(5)": "1", "E[X]": "4", "Var(X)": "1",
              "P(3<=X<=4)": "1/2", "P(3<X<=4)": "3/10", "P(3<=X<4)": "1/5", "P(3<X<4)": "0", "F(7/2) query": "3/10"})
    add("RV-A-S2", P, "A", "spec", "CDF VALUES F(x): x=2,3,4,5 F=.1,.3,.6,1",
        {"mode": "CDF VALUES F(x)", "x": [2, 3, 4, 5], "F": [".1", ".3", ".6", "1"]},
        rv_a([2, 3, 4, 5], [F(1, 10), F(3, 10), F(6, 10), F(1)], "F"),
        spec={"p(2)": ".1", "p(3)": ".2", "p(4)": ".3", "p(5)": ".4"})
    add("RV-A-S3", P, "A", "spec", "WEIGHTS/COUNTS: x=2,3,4,5 weights 1,2,3,4",
        {"mode": "WEIGHTS/COUNTS", "x": [2, 3, 4, 5], "w": [1, 2, 3, 4]},
        rv_a([2, 3, 4, 5], [F(1), F(2), F(3), F(4)], "w"),
        spec={"p(2)": ".1", "p(3)": ".2", "p(4)": ".3", "p(5)": ".4"})
    add("RV-A-E1", P, "A", "edge", "p(x) VALUES unsorted: x=5,2,4,3 p=.4,.1,.3,.2; F(1), F(10)",
        {"mode": "p(x) VALUES", "x": [5, 2, 4, 3], "p": [".4", ".1", ".3", ".2"], "Fx": [1, 10]},
        rv_a([5, 2, 4, 3], [F(4, 10), F(1, 10), F(3, 10), F(2, 10)], "p", None, [F(1), F(10)]),
        notes="Must sort by x; F below support = 0, above = 1.")
    add("RV-A-E2", P, "A", "edge", "p(x) VALUES: x=-1,0,1 p=1/4,1/2,1/4 (irrational SD)",
        {"mode": "p(x) VALUES", "x": [-1, 0, 1], "p": ["1/4", "1/2", "1/4"]},
        rv_a([-1, 0, 1], [F(1, 4), F(1, 2), F(1, 4)], "p"))
    add("RV-A-E3", P, "A", "edge", "p(x) VALUES not summing to 1: x=1,2,3 p=.1,.2,.3",
        {"mode": "p(x) VALUES", "x": [1, 2, 3], "p": [".1", ".2", ".3"]},
        rv_a([1, 2, 3], [F(1, 10), F(2, 10), F(3, 10)], "p"), notes="Warn: sum of p = .6 ≠ 1.")
    add("RV-A-E4", P, "A", "edge", "x=.1,.2,.3 p=1/3 each; query a=.2, b=.3 (tolerant comparisons)",
        {"mode": "p(x) VALUES", "x": [".1", ".2", ".3"], "p": ["1/3", "1/3", "1/3"], "a": ".2", "b": ".3"},
        rv_a([F(1, 10), F(2, 10), F(3, 10)], [F(1, 3)] * 3, "p", (F(1, 5), F(3, 10))))
    # ---- B
    add("RV-B-S1", P, "B", "spec", "MAXIMUM, N=5, k=2, WITHOUT (HW3 Q1)", {"stat": "MAXIMUM", "N": 5, "k": 2, "repl": "WITHOUT"},
        rv_b("max", 5, 2, False),
        spec={"p(2)": "1/10", "p(3)": "1/5", "p(4)": "3/10", "p(5)": "2/5", "F(2)": "1/10", "F(3)": "3/10",
              "F(4)": "3/5", "F(5)": "1"})
    r = rv_b("max", 6, 2, True)
    add("RV-B-S2", P, "B", "spec", "MAXIMUM, N=6, k=2, WITH", {"stat": "MAXIMUM", "N": 6, "k": 2, "repl": "WITH"}, r,
        spec={f"p({z})": exact_str(Fr(2 * z - 1, 36)) for z in range(1, 7)})
    add("RV-B-S3", P, "B", "spec", "SUM (2 DRAWS), N=6, WITH", {"stat": "SUM", "N": 6, "k": 2, "repl": "WITH"},
        rv_b("sum", 6, 2, True), spec={"p(7)": "1/6"})
    add("RV-B-S4", P, "B", "spec", "MINIMUM, N=5, k=2, WITHOUT", {"stat": "MINIMUM", "N": 5, "k": 2, "repl": "WITHOUT"},
        rv_b("min", 5, 2, False), spec={"p(1)": "2/5", "p(2)": "3/10", "p(3)": "1/5", "p(4)": "1/10"})
    add("RV-B-S5", P, "B", "spec", "|DIFF| (2 DRAWS), N=5, WITHOUT", {"stat": "|DIFF|", "N": 5, "k": 2, "repl": "WITHOUT"},
        rv_b("diff", 5, 2, False), spec={"p(1)": "2/5", "p(2)": "3/10", "p(3)": "1/5", "p(4)": "1/10"})
    add("RV-B-E1", P, "B", "edge", "MAXIMUM, N=4, k=4, WITHOUT (k=N)", {"stat": "MAXIMUM", "N": 4, "k": 4, "repl": "WITHOUT"},
        rv_b("max", 4, 4, False))
    add("RV-B-E2", P, "B", "edge", "MINIMUM, N=4, k=3, WITHOUT", {"stat": "MINIMUM", "N": 4, "k": 3, "repl": "WITHOUT"},
        rv_b("min", 4, 3, False))
    add("RV-B-E3", P, "B", "edge", "MAXIMUM, N=4, k=3, WITH", {"stat": "MAXIMUM", "N": 4, "k": 3, "repl": "WITH"},
        rv_b("max", 4, 3, True))
    add("RV-B-E4", P, "B", "edge", "SUM (2 DRAWS), N=4, WITHOUT", {"stat": "SUM", "N": 4, "k": 2, "repl": "WITHOUT"},
        rv_b("sum", 4, 2, False))
    add("RV-B-E5", P, "B", "edge", "|DIFF| (2 DRAWS), N=4, WITH (d=0 possible)", {"stat": "|DIFF|", "N": 4, "k": 2, "repl": "WITH"},
        rv_b("diff", 4, 2, True))
    add("RV-B-E6", P, "B", "edge", "MAXIMUM, N=3, k=4, WITHOUT (k>N)", {"stat": "MAXIMUM", "N": 3, "k": 4, "repl": "WITHOUT"},
        rv_b("max", 3, 4, False), notes="C(3,4)=0: must reject, not divide by zero.")
    add("RV-B-E7", P, "B", "edge", "MINIMUM, N=6, k=2, WITH", {"stat": "MINIMUM", "N": 6, "k": 2, "repl": "WITH"},
        rv_b("min", 6, 2, True))
    # ---- C
    q = F(1, 4)
    add("RV-C-S1", P, "C", "spec", "PDF, c known; pieces (0,2) deg0 C0=1/4 and (4,6) deg0 C0=1/4 (HW3 Q2); "
        "queries P(1<X<5), F(3)",
        {"mode": "PDF", "unknown_c": 0, "pieces": [[0, 2, ["1/4"]], [4, 6, ["1/4"]]], "queries": ["P(1<X<5)", "F(3)"]},
        rv_c("pdf", [(F(0), F(2), [q]), (F(4), F(6), [q])], False, [("between", 1, 5), ("F", 3)]),
        spec={"area": "1", "F piece1 (0<x<2) x": "1/4", "F on gap 2<=x<=4": "1/2", "F piece2 (4<x<6) const": "-1/2",
              "F piece2 x": "1/4", "P(1<X<5)": "1/2", "F(3)": "1/2"})
    add("RV-C-S2", P, "C", "spec", "PDF, c known; piece (-4,4) deg2 C0=3/16, C1=0, C2=-3/256 (HW3 Q4); "
        "queries F(-2), P(1<X<3), P(X=-1)",
        {"mode": "PDF", "unknown_c": 0, "pieces": [[-4, 4, ["3/16", "0", "-3/256"]]],
         "queries": ["P(-4<X<-2)", "F(-2)", "P(1<X<3)", "P(X=-1)"]},
        rv_c("pdf", [(F(-4), F(4), [F(3, 16), F(0), F(-3, 256)])], False,
             [("between", -4, -2), ("F", -2), ("between", 1, 3), ("eq", -1)]),
        spec={"F piece1 (-4<x<4) const": "1/2", "F piece1 x": "3/16", "F piece1 x^3": "-1/256",
              "P(-4<X<-2)": "5/32", "F(-2)": "5/32", "P(1<X<3)": "35/128"})
    add("RV-C-S3", P, "C", "spec", "PDF, UNKNOWN c; piece (0,3) deg2 C0=0,C1=0,C2=1 (HW3 431 Q5); query P(X>2)",
        {"mode": "PDF", "unknown_c": 1, "pieces": [[0, 3, ["0", "0", "1"]]], "queries": ["P(X>2)"]},
        rv_c("pdf", [(F(0), F(3), [F(0), F(0), F(1)])], True, [("gt", 2)]),
        spec={"c": "1/9", "F piece1 x^3": "1/27", "P(X>2)": "19/27"})
    add("RV-C-S4", P, "C", "spec", "CDF mode; piece (-2,2) deg1 C0=1/2, C1=1/4 (HW3 Q3); queries P(-1<X<1), P(X>.5)",
        {"mode": "CDF", "pieces": [[-2, 2, ["1/2", "1/4"]]], "queries": ["P(-1<X<1)", "P(X>.5)"]},
        rv_c("cdf", [(F(-2), F(2), [F(1, 2), F(1, 4)])], False, [("between", -1, 1), ("gt", F(1, 2))]),
        spec={"f piece1 const": "1/4", "P(-1<X<1)": "1/2", "P(1/2<X<1)" if False else "P(X>1/2)": "3/8"})
    add("RV-C-E1", P, "C", "edge", "CDF mode with a jump at the left end: piece (0,1) deg1 C0=1/2, C1=1/2; "
        "queries P(-1<X<.5), P(X>.5)",
        {"mode": "CDF", "pieces": [[0, 1, ["1/2", "1/2"]]], "queries": ["P(-1<X<.5)", "P(X>.5)", "P(X=0)"]},
        rv_c("cdf", [(F(0), F(1), [F(1, 2), F(1, 2)])], False, [("between", -1, F(1, 2)), ("gt", F(1, 2)), ("eq", 0)]),
        notes="Must warn F(lo1)=1/2 ≠ 0 (jump of 1/2 at x=0: X is not continuous there, true P(X=0)=1/2 even "
              "though the P(X=a) query prints '0 (continuous X)').")
    add("RV-C-E2", P, "C", "edge", "PDF, UNKNOWN c; triangle pieces (0,1) deg1 C1=1 and (1,2) deg1 C0=2, C1=-1; "
        "query P(.5<X<1.5), F(1)",
        {"mode": "PDF", "unknown_c": 1, "pieces": [[0, 1, ["0", "1"]], [1, 2, ["2", "-1"]]],
         "queries": ["P(.5<X<1.5)", "F(1)"]},
        rv_c("pdf", [(F(0), F(1), [F(0), F(1)]), (F(1), F(2), [F(2), F(-1)])], True,
             [("between", F(1, 2), F(3, 2)), ("F", 1)]))
    add("RV-C-E3", P, "C", "edge", "PDF, c known; piece (1,3) deg0 C0=1/2 (support not starting at 0); F(0), F(2), F(4)",
        {"mode": "PDF", "unknown_c": 0, "pieces": [[1, 3, ["1/2"]]], "queries": ["F(0)", "F(2)", "F(4)"]},
        rv_c("pdf", [(F(1), F(3), [F(1, 2)])], False, [("F", 0), ("F", 2), ("F", 4)]))
    add("RV-C-E4", P, "C", "edge", "PDF, c known; piece (0,2) deg1 C0=1, C1=-1 (f<0 on (1,2), area 0)",
        {"mode": "PDF", "unknown_c": 0, "pieces": [[0, 2, ["1", "-1"]]]},
        rv_c("pdf", [(F(0), F(2), [F(1), F(-1)])], False), notes="Must warn area≠1 and f<0.")
    add("RV-C-E5", P, "C", "edge", "PDF, UNKNOWN c; piece (0,2) deg1 C0=1, C1=-1 (area 0 -> c undefined)",
        {"mode": "PDF", "unknown_c": 1, "pieces": [[0, 2, ["1", "-1"]]]},
        rv_c("pdf", [(F(0), F(2), [F(1), F(-1)])], True), notes="Guard division by zero area.")

    # ---- D (numeric)
    e = mpmath.e
    Fexp = lambda t: 1 - mpmath.exp(-2 * t)  # noqa: E731
    add("RV-D-S1", P, "D", "spec", "CDF F(X)=\"1-𝑒^(⁻2X)\" on [0,50); P(X>1), f(1)=F'(1) (HW3 431 Q6)",
        {"mode": "CDF", "F": "1-𝑒^(⁻2X)", "lo": 0, "hi": 50, "queries": ["P(X>1)", "f(1)"]},
        OrderedDict([("F(0)", F(0)),
                     ("F(50)", Irr("1-exp(-100)", 1 - mpmath.exp(-100))),
                     ("P(X>1)", Irr("exp(-2)", mpmath.exp(-2))),
                     ("f(1) exact", Irr("2*exp(-2)", 2 * mpmath.exp(-2), numeric=False)),
                     ("f(1)", Irr("2*exp(-2) [nDeriv h=.001]", 2 * mpmath.exp(-2), nderiv(Fexp, mpmath.mpf(1))))]),
        spec={"P(X>1)": ".135335", "f(1)": ".270671"}, numeric_tool=True,
        notes="F(50) = 1-e^-100 = 1 to 14 digits, so no F(hi)≠1 warning should fire.")
    fq = lambda t: mpmath.mpf(3) / 256 * (16 - t ** 2)  # noqa: E731
    add("RV-D-S2", P, "D", "spec", "PDF f(X)=\"3/256(16-X²)\" on (-4,4), c known; P(-4<X<-2), P(1<X<3) (HW3 Q4)",
        {"mode": "PDF", "f": "3/256(16-X²)", "lo": -4, "hi": 4, "unknown_c": 0, "queries": ["P(-4<X<-2)", "P(1<X<3)"]},
        OrderedDict([("area", Irr("1", mpmath.quad(fq, [-4, 4]))),
                     ("P(-4<X<-2)", Irr("5/32", mpmath.quad(fq, [-4, -2]))),
                     ("P(1<X<3)", Irr("35/128", mpmath.quad(fq, [1, 3])))]),
        spec={"P(-4<X<-2)": ".15625", "P(1<X<3)": ".273438"}, numeric_tool=True,
        notes="Typed with implied multiplication: 3/256(16-X²) = (3/256)*(16-X²) (left-to-right). "
              "P(1<X<3)=35/128=.2734375 exactly is a rounding TIE at 6 places: Str8 is .273438 only if fnInt "
              "returns >= .2734375; a result 1E-13 low gives .273437. Str9 = 35/128 is robust -> assert Str9.")
    fx2 = lambda t: t ** 2  # noqa: E731
    add("RV-D-S3", P, "D", "spec", "PDF f(X)=\"X²\" on (0,3), UNKNOWN c; P(X>2) (HW3 431 Q5)",
        {"mode": "PDF", "f": "X²", "lo": 0, "hi": 3, "unknown_c": 1, "queries": ["P(X>2)"]},
        OrderedDict([("area", Irr("9", mpmath.quad(fx2, [0, 3]))),
                     ("c", Irr("1/9", 1 / mpmath.quad(fx2, [0, 3]))),
                     ("P(X>2)", Irr("19/27", mpmath.quad(fx2, [2, 3]) / 9))]),
        spec={"c": ".111111", "P(X>2)": ".703704"}, numeric_tool=True)
    f2e = lambda t: 2 * mpmath.exp(-2 * t)  # noqa: E731
    add("RV-D-E1", P, "D", "edge", "PDF \"2𝑒^(⁻2X)\" on (0,50), c known; P(X>1), P(0<X<.5)",
        {"mode": "PDF", "f": "2𝑒^(⁻2X)", "lo": 0, "hi": 50, "unknown_c": 0, "queries": ["P(X>1)", "P(0<X<.5)"]},
        OrderedDict([("area", Irr("1-exp(-100)", 1 - mpmath.exp(-100))),
                     ("P(X>1)", Irr("exp(-2)-exp(-100)", mpmath.exp(-2) - mpmath.exp(-100))),
                     ("P(0<X<.5)", Irr("1-exp(-1)", 1 - mpmath.exp(-1)))]), numeric_tool=True)
    add("RV-D-E2", P, "D", "edge", "PDF \"X²\" on (0,3), UNKNOWN c; P(4<X<5) (interval outside support)",
        {"mode": "PDF", "f": "X²", "lo": 0, "hi": 3, "unknown_c": 1, "queries": ["P(4<X<5)"]},
        OrderedDict([("c", Irr("1/9", mpmath.mpf(1) / 9)), ("P(4<X<5)", F(0))]), numeric_tool=True,
        notes="Clipped interval [max(a,lo),min(b,hi)] = [4,3] is empty -> 0 (do not call fnInt backwards: "
              "fnInt(…,4,3) would give a NEGATIVE value).")
    add("RV-D-E3", P, "D", "edge", "CDF \"X/2\" on [0,1); P(X>.5), f(.5)",
        {"mode": "CDF", "F": "X/2", "lo": 0, "hi": 1, "queries": ["P(X>.5)", "f(.5)"]},
        OrderedDict([("F(lo)", F(0)), ("F(hi)", F(1, 2)), ("warn F(hi)≠1?", True),
                     ("P(X>.5)", F(3, 4)), ("f(.5)", F(1, 2))]), numeric_tool=True,
        notes="Warn F(hi)=1/2≠1 (jump of 1/2 at x=1 by the tool's convention F=1 for t>=hi).")
    add("RV-D-E4", P, "D", "edge", "CDF \"(X+2)/4\" on [-2,2) (HW3 Q3 numerically); P(-1<X<1), P(X>.5)",
        {"mode": "CDF", "F": "(X+2)/4", "lo": -2, "hi": 2, "queries": ["P(-1<X<=1)", "P(X>.5)", "f(0)"]},
        OrderedDict([("P(-1<X<=1)", F(1, 2)), ("P(X>.5)", F(3, 8)), ("f(0)", F(1, 4))]), numeric_tool=True)

    # ---- E
    h = lambda t: mpmath.exp(-t)  # noqa: E731
    def trans(fX, lo, hi, hfun, incr, y):
        xv = hfun(y)
        xc = min(max(xv, lo), hi)
        FX = mpmath.quad(fX, [lo, xc]) if xc > lo else mpmath.mpf(0)
        FY = FX if incr else 1 - FX
        inside = lo < xv < hi
        fY_exact = fX(xv) * abs(mpmath.diff(hfun, y)) if inside else mpmath.mpf(0)
        fY_nd = fX(xv) * abs(nderiv(hfun, y)) if inside else mpmath.mpf(0)
        return xv, FX, FY, fY_exact, fY_nd
    fX = lambda t: 2 * t  # noqa: E731
    for cid, y, kind, spec in (("RV-E-S1", 1, "spec", {"x=h(y)": ".367879", "F_Y(y)": ".864665", "f_Y(y)": ".270671"}),
                               ("RV-E-S2", F(1, 2), "spec", {"F_Y(y)": ".632121", "f_Y(y)": ".735759"}),
                               ("RV-E-E1", 3, "edge", None),
                               ("RV-E-E2", -1, "edge", None)):
        yv = mpmath.mpf(y.numerator) / y.denominator if isinstance(y, Fr) else mpmath.mpf(y)
        xv, FX, FY, fe, fn = trans(fX, 0, 1, h, False, yv)
        ys = exact_str(y)
        exp_ = OrderedDict([("x=h(y)", Irr(f"exp(-{ys})", xv)),
                            ("F_X(x)", Irr(f"min(1,exp(-2*{ys}))", FX)),
                            ("F_Y(y)", Irr(f"1-exp(-2*{ys})" if yv > 0 else "0", FY) if yv > 0 else F(0)),
                            ("f_Y(y) exact", Irr(f"2*exp(-2*{ys})", fe, numeric=False) if yv > 0 else F(0)),
                            ("f_Y(y)", Irr(f"2*exp(-2*{ys}) [via nDeriv]", fe, fn) if yv > 0 else F(0))])
        add(cid, P, "E", kind, f"f_X=\"2X\" on (0,1), h(y)=\"𝑒^(⁻X)\" (Y=-lnX), DECREASING; y={ys} (HW3 631 Q5)",
            {"fX": "2X", "lo": 0, "hi": 1, "h": "𝑒^(⁻X)", "g": "DECREASING", "y": ys}, exp_, spec=spec,
            numeric_tool=True,
            notes=("y<0 is outside the support of Y: x=e>1 is clipped to hi, F_X=1, F_Y=0, f_Y=0."
                   if yv < 0 else "Exact: F_Y(y)=1-e^(-2y), f_Y(y)=2e^(-2y) for y>0 (Exponential, rate 2)."))
    # PIT demo: f_X=2X on (0,1), U=F_X(X)=X^2 increasing, h(u)=sqrt(u)
    sq = lambda t: mpmath.sqrt(t)  # noqa: E731
    xv, FX, FY, fe, fn = trans(fX, 0, 1, sq, True, mpmath.mpf("0.3"))
    add("RV-E-E3", P, "E", "edge", "PIT check: f_X=\"2X\" on (0,1), g=F_X (U=X²) INCREASING, h(u)=\"√(X)\"; y=.3",
        {"fX": "2X", "lo": 0, "hi": 1, "h": "√(X)", "g": "INCREASING", "y": ".3"},
        OrderedDict([("x=h(y)", Irr("sqrt(3/10)", xv)), ("F_X(x)", Irr("3/10", FX)), ("F_Y(y)", Irr("3/10", FY)),
                     ("f_Y(y) exact", F(1)), ("f_Y(y)", Irr("1 [via nDeriv]", fe, fn))]), numeric_tool=True,
        notes="Probability integral transform: F_U(u)=u, f_U=1. nDeriv(√(X),X,.3) has O(h²) error, so the "
              "calculator shows f_Y=1.000001 (not 1).")
    fU = lambda t: mpmath.mpf(1)  # noqa: E731
    xv, FX, FY, fe, fn = trans(fU, 0, 1, sq, True, mpmath.mpf("0.25"))
    add("RV-E-E4", P, "E", "edge", "f_X=\"1\" on (0,1) (uniform), Y=X² INCREASING, h(y)=\"√(X)\"; y=.25",
        {"fX": "1", "lo": 0, "hi": 1, "h": "√(X)", "g": "INCREASING", "y": ".25"},
        OrderedDict([("x=h(y)", Irr("1/2", xv)), ("F_Y(y)", Irr("1/2", FY)), ("f_Y(y) exact", F(1)),
                     ("f_Y(y)", Irr("1/(2*sqrt(y)) = 1 [via nDeriv]", fe, fn))]), numeric_tool=True,
        notes="Typing \"1\" as f_X: Y₉ = 1 is a constant; fnInt handles it.")


# ========================================================================================
# Homework answer key (numeric parts as oracle entries; proofs in cases.md)
# ========================================================================================


def build_hw():
    F = Fr
    H = lambda cid, prog, tool, desc, exp_, notes=None, numeric_tool=False: add(  # noqa: E731
        cid, prog, tool, "hw", desc, {}, exp_, notes=notes, numeric_tool=numeric_tool)
    # HW1
    H("HW1-Q2a-check", "PROOF", "", "HW1 Q2(a) numeric sanity: sum r*C(n,r) = n*2^(n-1), n=1..12",
      OrderedDict((f"n={n}", sum(r * comb(n, r) for r in range(1, n + 1))) for n in (4, 5, 10)),
      notes="n*2^(n-1): 32, 80, 5120")
    for n in range(1, 13):
        assert sum(r * comb(n, r) for r in range(1, n + 1)) == n * 2 ** (n - 1)
        assert sum(Fr(comb(n, r), r + 1) for r in range(n + 1)) == Fr(2 ** (n + 1) - 1, n + 1)
        for r in range(1, n):
            assert comb(n, r) == comb(n - 1, r - 1) + comb(n - 1, r)
    H("HW1-Q2b-check", "PROOF", "", "HW1 Q2(b) numeric sanity: sum C(n,r)/(r+1) = (2^(n+1)-1)/(n+1)",
      OrderedDict((f"n={n}", sum(Fr(comb(n, r), r + 1) for r in range(n + 1))) for n in (4, 5, 10)),
      notes="31/5, 21/2, 2047/11")
    H("HW1-Q3", "STACNT", "F", "HW1 Q3: coefficient of x^3 y^2 z^2 in (2x-y+3z)^7",
      OrderedDict([("coefficient", cnt_f([(2, 3), (-1, 2), (3, 2)])["coefficient"])]))
    b = cnt_b("PROBABILITY", "B")
    H("HW1-Q4", "STACNT", "B", "HW1 Q4: PROBABILITY (a) distinct permutations (b) BB adjacent",
      OrderedDict([("(a)", b["total"]), ("(b)", b["block"])]))
    H("HW1-Q5", "STACNT", "C", "HW1 Q5: 12 faculty into distinct committees of 3,4,5",
      OrderedDict([("ways", cnt_c1([3, 4, 5])["labeled"])]))
    H("HW1-Q6", "STACNT", "D", "HW1 Q6: 20 T/F questions, 5 difficult; exactly 15 correct incl. exactly 2 difficult",
      OrderedDict([("ways", comb(5, 2) * comb(15, 13))]),
      notes="C(5,2)*C(15,13) = 10*105; a T/F answer sheet is determined by which questions are correct.")
    H("HW1-431-Q7", "STACNT", "D", "HW1 431 Q7: 5 from 8 math + 6 stat, >=2 of each",
      OrderedDict([("ways", cnt_d(8, 6, 5, 2, 99, 2, 99)["total"]),
                   ("check via complement", comb(14, 5) - (comb(6, 5) + 8 * comb(6, 4) + comb(8, 4) * 6 + comb(8, 5)))]))
    H("HW1-431-Q8", "STACNT", "C", "HW1 431 Q8: grades A-F to 10 students, exactly 3 A and exactly 1 F",
      OrderedDict([("ways", comb(10, 3) * comb(7, 1) * 3 ** 6)]), notes="C(10,3)*C(7,1)*3^6 = 120*7*729")
    H("HW1-631-Q8", "STACNT", "E", "HW1 631 Q8: 15 identical clusters to 4 labs (a) each >=1 (b) lab1 >=3, others >=1",
      OrderedDict([("(a)", comb(14, 3)), ("(b)", comb(12, 3)), ("change", comb(14, 3) - comb(12, 3))]))
    # HW2
    o = prb_a_outputs(F(55, 100), F(35, 100), F(1, 5))
    H("HW2-Q2", "STAPRB", "A", "HW2 Q2: P(X)=.55, P(Y)=.35, P(XuY)=.70",
      OrderedDict([("(a) P(XnY)", o["P(AnB)"]), ("(b) P(X|Y)", o["P(A|B)"]), ("(c) P(Y|X^c)", o["P(B|A')"])]))
    H("HW2-Q3", "STAPRB", "B", "HW2 Q3: 120 people, 70 grad/50 faculty, 40 female grads, 65 females",
      OrderedDict([("(a) P(male faculty)", F(25, 120)), ("(b) P(grad|female)", F(40, 65))]))
    c = prb_c([F(1, 2), F(3, 10), F(1, 5)], [F(15, 100), F(25, 100), F(1, 10)])
    H("HW2-Q4", "STAPRB", "C", "HW2 Q4: journal fields 50/30/20%, acceptance 15/25/10%",
      OrderedDict([("(a) P(accept)", c["P(A)"]), ("(b) P(Methodology|accept)", c["P(B1|A)"])]))
    c = prb_c([F(1, 3), F(2, 3)], [F(3, 7), F(5, 7)])
    H("HW2-Q5", "STAPRB", "C", "HW2 Q5: die 1-2 -> urn A (3R,4B), 3-6 -> urn B (5R,2B)",
      OrderedDict([("(a) P(red)", c["P(A)"]), ("(b) P(die 1or2|red)", c["P(B1|A)"])]))
    c = prb_c([F(3, 5), F(2, 5)], [F(2, 5), F(1, 20)])
    H("HW2-431-Q6", "STAPRB", "C", "HW2 431 Q6: 60% spam; 'urgent' in 40% spam, 5% non-spam",
      OrderedDict([("(a) P(urgent)", c["P(A)"]), ("(b) P(spam|urgent)", c["P(B1|A)"])]))
    v = prb_e3(400, 500, 600, 200, 150, 250, 100, 1000)
    H("HW2-431-Q7", "STAPRB", "E", "HW2 431 Q7: Digital 400, Print 500, Weekend 600, DP 200, PW 250, DW 150, all 100, N=1000",
      OrderedDict([("Weekend only", v["C only"]), ("none", v["none"])]))
    d = prb_d(F(5, 1000), F(95, 100), F(99, 100), "+", [(F(9, 10), F(95, 100), "+")])
    H("HW2-631-Q7", "STAPRB", "D", "HW2 631 Q7: incidence .5%, sens 95%, spec 99%; then physician sens 90%, spec 95%",
      OrderedDict([("(a) P(event|flag)", d["PPV=P(D|+)"]), ("(b) P(event|flag, physician +)", d["UPDATED P(D) after test2"])]))
    # HW3
    r = rv_b("max", 5, 2, False)
    H("HW3-Q1", "STARV", "B", "HW3 Q1: Z = max of 2 balls from 1..5 without replacement",
      OrderedDict(list(r.items())), notes="p(z)=(z-1)/10 for z=2..5; F(z)=C(floor z,2)/10 for 2<=z<5, 0 for z<2, 1 for z>=5.")
    H("HW3-Q2", "STARV", "C", "HW3 Q2: f=1/4 on (0,2) and (4,6): CDF",
      OrderedDict([("F(x), x<=0", F(0)), ("F(x), 0<x<2", "x/4"), ("F(x), 2<=x<4", F(1, 2)),
                   ("F(x), 4<=x<6", "(x-2)/4 = -1/2 + x/4"), ("F(x), x>=6", F(1))]))
    H("HW3-Q3", "STARV", "C", "HW3 Q3: F(x)=(x+2)/4 on [-2,2)",
      OrderedDict([("P(-1<X<1)", F(1, 2)), ("P(X>0.5)", F(3, 8))]))
    H("HW3-Q4", "STARV", "C", "HW3 Q4: f=3/256(16-x^2) on (-4,4)",
      OrderedDict([("(a) P(X<=-2)", F(5, 32)), ("(b) P(1<=X<=3)", F(35, 128)), ("(c) P(X=-1)", F(0))]))
    H("HW3-431-Q5", "STARV", "C", "HW3 431 Q5: f(y)=c y^2 on (0,3)",
      OrderedDict([("(a) c", F(1, 9)), ("(b) F(y), 0<y<3", "y^3/27 (0 for y<=0, 1 for y>=3)"), ("(c) P(Y>2)", F(19, 27))]))
    H("HW3-431-Q6", "STARV", "D", "HW3 431 Q6: F(x)=1-e^(-2x), x>0",
      OrderedDict([("(a) f(x)", "2e^(-2x) for x>0, 0 for x<0"), ("(b) P(X>1)", Irr("exp(-2)", mpmath.exp(-2), numeric=False))]))
    H("HW3-631-Q5", "STARV", "E", "HW3 631 Q5: f_X=2x on (0,1), Y=-ln X",
      OrderedDict([("(a) F_Y(y)", "1-e^(-2y) for y>0; 0 for y<=0"), ("(b) f_Y(y)", "2e^(-2y) for y>0; 0 for y<=0"),
                   ("F_Y(1)", Irr("1-exp(-2)", 1 - mpmath.exp(-2), numeric=False)),
                   ("f_Y(1)", Irr("2*exp(-2)", 2 * mpmath.exp(-2), numeric=False))]))
    H("HW3-631-Q6", "PROOF", "", "HW3 631 Q6: U=F_X(X)",
      OrderedDict([("F_U(u)", "0 for u<=0; u for 0<u<1; 1 for u>=1"), ("f_U(u)", "1 on (0,1), 0 elsewhere")]))


# ========================================================================================
# cases.md
# ========================================================================================
HW_TEXT = r"""
## Homework answer key (computed independently, exact)

Display column = what STAFMT shows: `Str9` (exact form) / `Str8` (6-decimal form).

### HW 1 (Counting)

**Q1 Pascal's identity** C(n,r) = C(n-1,r-1) + C(n-1,r), 1 <= r <= n-1.
* Algebraic: C(n-1,r-1) + C(n-1,r) = (n-1)!/((r-1)!(n-r)!) + (n-1)!/(r!(n-1-r)!)
  = (n-1)!/(r!(n-r)!) * [ r + (n-r) ] = n!/(r!(n-r)!) = C(n,r)
  (common denominator r!(n-r)!: multiply the 1st term by r/r and the 2nd by (n-r)/(n-r)).
* Story: count r-member committees from n people. Fix one person, Pat. Committees containing Pat: choose the
  other r-1 from n-1 -> C(n-1,r-1). Committees without Pat: all r from the other n-1 -> C(n-1,r). The two cases
  are disjoint and cover everything, so the counts add to C(n,r).

**Q2 Binomial sums** start from (1+x)^n = sum_{r=0}^n C(n,r) x^r.
* (a) Differentiate: n(1+x)^(n-1) = sum_{r=1}^n r C(n,r) x^(r-1). Put x = 1: sum r C(n,r) = n 2^(n-1).
  (check n=4: 4+12+12+4 = 32 = 4*8.)
* (b) Integrate from 0 to 1: LHS = [(1+x)^(n+1)/(n+1)]_0^1 = (2^(n+1)-1)/(n+1);
  RHS = sum C(n,r) * integral_0^1 x^r dx = sum C(n,r)/(r+1). (check n=4: 1+2+2+1+1/5 = 31/5 = (32-1)/5.)
  Alternative: C(n,r)/(r+1) = C(n+1,r+1)/(n+1), and sum_{r=0}^n C(n+1,r+1) = 2^(n+1) - 1.
* (x = 1 in the plain expansion gives sum C(n,r) = 2^n; x = -1 gives sum (-1)^r C(n,r) = 0.)

| Q | Answer | Display |
|---|---|---|
| Q3 coeff of x³y²z² in (2x−y+3z)^7 | 7!/(3!2!2!) · 2³(−1)²3² = 210 · 72 = **15120** | 15120 |
| Q4(a) PROBABILITY permutations | 11!/(2!2!) = **9979200** (B×2, I×2) | 9979200 |
| Q4(b) the two B's adjacent | glue BB: 10!/2! = **1814400** | 1814400 |
| Q5 committees 3,4,5 (distinct) | 12!/(3!4!5!) = **27720** | 27720 |
| Q6 exactly 15 correct, exactly 2 of 5 difficult | C(5,2)·C(15,13) = 10·105 = **1050** | 1050 |
| 431 Q7 ≥2 math & ≥2 stat, 5 of 8+6 | C(8,2)C(6,3)+C(8,3)C(6,2) = 560+840 = **1400** (complement: 2002−602) | 1400 |
| 431 Q8 grades, exactly 3 A, exactly 1 F | C(10,3)·C(7,1)·3^6 = 120·7·729 = **612360** | 612360 |
| 631 Q8(a) 15 clusters, 4 labs, each ≥1 | y_i=x_i−1, Σy=11: C(14,3) = **364** | 364 |
| 631 Q8(b) lab 1 ≥3, others ≥1 | Σy = 15−6 = 9: C(12,3) = **220** (144 fewer) | 220 |

**631 Q7 Vandermonde (story proof)** sum_{k=0}^r C(m,k) C(n,r-k) = C(m+n,r).
Count r-person committees from a group of m men and n women (m+n people): C(m+n,r) ways. Split by k = number of
men on the committee: choose the k men (C(m,k)) and the r-k women (C(n,r-k)). The cases k = 0..r are disjoint and
exhaustive (C(a,b) = 0 when b > a), so summing over k gives the same total.

### HW 2 (Probability)

**Q1 set expressions**
* (a) only A: A ∩ B' ∩ C'
* (b) exactly one: (A∩B'∩C') ∪ (A'∩B∩C') ∪ (A'∩B'∩C)
* (c) at least one: A ∪ B ∪ C   ( = (A'∩B'∩C')' )
* (d) A and B but not C: A ∩ B ∩ C'

| Q | Answer | Display |
|---|---|---|
| Q2(a) P(X∩Y) | .55+.35−.70 = **1/5** | 1/5 / .2 |
| Q2(b) P(X\|Y) | .20/.35 = **4/7** ≈ .571429 | 4/7 / .571429 |
| Q2(c) P(Y\|X^c) | (.35−.20)/(1−.55) = .15/.45 = **1/3** ≈ .333333 | 1/3 / .333333 |
| Q3(a) P(male faculty) | table: faculty male = 50−25 = 25 → 25/120 = **5/24** ≈ .208333 | 5/24 / .208333 |
| Q3(b) P(grad \| female) | 40/65 = **8/13** ≈ .615385 | 8/13 / .615385 |
| Q4(a) P(accepted) | .5(.15)+.3(.25)+.2(.10) = **.17** = 17/100 | 17/100 / .17 |
| Q4(b) P(Methodology \| accepted) | .075/.17 = **15/34** ≈ .441176 | 15/34 / .441176 |
| Q5(a) P(red) | (1/3)(3/7)+(2/3)(5/7) = **13/21** ≈ .619048 | 13/21 / .619048 |
| Q5(b) P(die 1 or 2 \| red) | (1/7)/(13/21) = **3/13** ≈ .230769 | 3/13 / .230769 |
| 431 Q6(a) P(urgent) | .6(.4)+.4(.05) = **.26** = 13/50 | 13/50 / .26 |
| 431 Q6(b) P(spam \| urgent) | .24/.26 = **12/13** ≈ .923077 | 12/13 / .923077 |
| 431 Q7 Weekend only / none | 600−150−250+100 = **300**; union = 1000 → none = **0** | 300 ; 0 |
| 631 Q7(a) P(event \| flagged) | .95(.005)/[.95(.005)+.01(.995)] = .00475/.0147 = **95/294** ≈ .323129 | 95/294 / .323129 |
| 631 Q7(b) after physician + | prior 95/294: .9(95/294)/[.9(95/294)+.05(199/294)] = 85.5/95.45 = **1710/1909** ≈ .895757 | 1710/1909 / .895757 |

**631 Q6(a)** P(A|B) > P(A) ⇔ P(A∩B)/P(B) > P(A) ⇔ P(A∩B) > P(A)P(B) (multiply by P(B) > 0)
⇔ P(A∩B)/P(A) > P(B) (divide by P(A) > 0) ⇔ P(B|A) > P(B). (Every step is reversible; symmetric in A, B.)

**631 Q6(b) Multiplication rule** P(A1∩…∩An) = P(A1)P(A2|A1)…P(An|A1∩…∩A_{n-1}), assuming
P(A1∩…∩A_{n-1}) > 0 (then every earlier intersection, being a superset, also has positive probability).
* Base n = 2: P(A1∩A2) = P(A1)P(A2|A1) is the definition of conditional probability.
* Step: assume it for n-1 events. Let B = A1∩…∩A_{n-1}. By the definition, P(B∩An) = P(B)P(An|B).
  Replace P(B) by the (n-1)-event product (induction hypothesis) → the n-event product. ∎

### HW 3 (Random variables)

**Q1** Z = max of 2 balls from {1,…,5} without replacement; C(5,2) = 10 equally likely pairs; P(Z=z) = C(z−1,1)/10.

| z | 2 | 3 | 4 | 5 |
|---|---|---|---|---|
| p(z) | 1/10 | 2/10 = 1/5 | 3/10 | 4/10 = 2/5 |
| F(z) | 1/10 | 3/10 | 6/10 = 3/5 | 1 |

CDF: F(z) = 0 (z<2); 1/10 (2≤z<3); 3/10 (3≤z<4); 3/5 (4≤z<5); 1 (z≥5)  [= C(⌊z⌋,2)/10 on 2≤z<5].
Sketch: PMF = spikes of heights .1,.2,.3,.4 at 2..5; CDF = right-continuous staircase (solid dot at the left end of
each step, jump p(z) at z). E[Z] = 4, Var(Z) = 1.

**Q2** F(x) = 0 for x ≤ 0; x/4 for 0 < x < 2; 1/2 for 2 ≤ x < 4; (x−2)/4 = −1/2 + x/4 for 4 ≤ x < 6; 1 for x ≥ 6.
Sketch: pdf = two flat blocks of height 1/4; CDF = ramp to 1/2, flat, ramp to 1 (continuous, no jumps).

**Q3** P(−1<X<1) = F(1) − F(−1) = 3/4 − 1/4 = **1/2**; P(X>0.5) = 1 − F(.5) = 1 − 5/8 = **3/8** (= .375).

**Q4** F(x) = 1/2 + 3x/16 − x³/256 on (−4,4).
(a) at least 2 min early: P(X ≤ −2) = F(−2) = **5/32** = .15625;
(b) 1 to 3 min late: F(3) − F(1) = 351/512 − 169/256 … = **35/128** ≈ .273438 (exactly .2734375);
(c) exactly 1 min early: P(X = −1) = **0** (continuous X).

**431 Q5** c·∫₀³ y² dy = 9c = 1 → **c = 1/9** (.111111); F(y) = 0 (y ≤ 0), **y³/27** (0 < y < 3), 1 (y ≥ 3);
P(Y > 2) = 1 − 8/27 = **19/27** ≈ .703704.

**431 Q6** f(x) = F'(x) = **2e^(−2x)** for x > 0 (0 for x < 0); P(X > 1) = 1 − F(1) = **e^(−2)** ≈ .135335.

**631 Q5** Y = −ln X maps (0,1) onto (0,∞), decreasing. For y > 0:
F_Y(y) = P(−ln X ≤ y) = P(X ≥ e^(−y)) = 1 − F_X(e^(−y)) = 1 − (e^(−y))² = **1 − e^(−2y)**; F_Y(y) = 0 for y ≤ 0.
f_Y(y) = **2e^(−2y)** for y > 0 (Exponential, rate 2). Check with the monotone formula: h(y) = e^(−y),
|h'(y)| = e^(−y), f_X(h(y))|h'(y)| = 2e^(−y)·e^(−y). Numbers: F_Y(1) = .864665, f_Y(1) = .270671.

**631 Q6 Probability integral transform** F_X continuous and strictly increasing ⇒ F_X^(−1) exists on (0,1) and
U = F_X(X) ∈ (0,1). For 0 < u < 1: F_U(u) = P(F_X(X) ≤ u) = P(X ≤ F_X^(−1)(u)) (F_X increasing)
= F_X(F_X^(−1)(u)) = u. F_U(u) = 0 for u ≤ 0 and 1 for u ≥ 1. Differentiating, f_U(u) = 1 on (0,1), 0 elsewhere:
U ~ Uniform(0,1). ∎
"""


def md_escape(s):
    return str(s).replace("|", "\\|")


def write_md(path):
    L = []
    L.append("# Oracle cases — STA 431/631 TI-84 helper")
    L.append("")
    L.append("Generated by `oracles/gen_oracles.py` (exact arithmetic: Python fractions, sympy; numeric tools: "
             "mpmath 40 digits). Every SPEC §4 case was recomputed from scratch and compared with SPEC; "
             "edge cases and the homework key were added. Display = STAFMT output predicted by "
             "`oracles/tifmt.py` (a line-by-line emulation of src/STAFMT.txt with 14-digit arithmetic): "
             "`Str9` exact form (integer or N/D with D ≤ 9999) / `Str8` 6-decimal form; negatives show `⁻`; "
             "values < .001 show in scientific form (`2.54ᴇ⁻4`).")
    L.append("")
    L.append("## Discrepancies vs SPEC.md")
    L.append("")
    if DISCREPANCIES:
        for cid, t in DISCREPANCIES:
            L.append(f"* **{cid}** — {t}")
    else:
        L.append("* none")
    L.append("")
    L.append("## Fragile displays (value sits on a rounding / fraction-detection boundary)")
    L.append("")
    if FRAGILE:
        for cid, nm, t in FRAGILE:
            L.append(f"* **{cid}** `{nm}` — {t}")
    else:
        L.append("* none")
    L.append("")
    cur = None
    for c in CASES:
        if c["kind"] == "hw":
            continue
        key = (c["program"], c["tool"])
        if key != cur:
            cur = key
            L.append(f"## {c['program']} {c['tool']}. {c['tool_name']}")
            L.append("")
        L.append(f"### {c['id']} ({c['kind']}) — {md_escape(c['inputs_description'])}")
        L.append("")
        L.append("| value | exact | Str9 | Str8 | SPEC |")
        L.append("|---|---|---|---|---|")
        for k, v in c["expected"].items():
            d = c["display"].get(k, ["", ""])
            sc = c.get("spec_check", {}).get(k)
            scs = "" if sc is None else (f"{sc['spec']} ✓" if sc["match"] else f"{sc['spec']} ✗")
            L.append(f"| {md_escape(k)} | {md_escape(v)} | {md_escape(d[0])} | {md_escape(d[1])} | {md_escape(scs)} |")
        if c.get("notes"):
            L.append("")
            L.append(f"_Note:_ {c['notes']}")
        L.append("")
    L.append(HW_TEXT)
    L.append("")
    L.append("### HW numeric entries in oracles.json (kind = \"hw\")")
    L.append("")
    L.append("| id | value | exact | Str9 | Str8 |")
    L.append("|---|---|---|---|---|")
    for c in CASES:
        if c["kind"] != "hw":
            continue
        for k, v in c["expected"].items():
            d = c["display"].get(k, ["", ""])
            L.append(f"| {c['id']} | {md_escape(k)} | {md_escape(v)} | {md_escape(d[0])} | {md_escape(d[1])} |")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def main():
    build_stacnt()
    build_staprb()
    build_starv()
    build_hw()
    meta = OrderedDict(
        generated_by="oracles/gen_oracles.py",
        conventions={
            "expected": "exact value as string: integer, 'p/q', symbolic text for irrational (exp(-2)), "
                        "'YES'/'NO' for checks, or a message string",
            "decimal": "float value (12+ significant digits)",
            "display": "[Str9, Str8] that STAFMT produces for the value the calculator computes "
                       "(for nDeriv values: the nDeriv approximation, h=1E-3)",
            "inputs": "structured inputs; -1 means 'unknown' where the tool supports it",
            "kind": "spec (SPEC.md section 4 case) | edge (extra edge case) | hw (homework answer)",
        },
        discrepancies=[{"id": a, "text": b} for a, b in DISCREPANCIES],
        fragile=[{"id": a, "name": b, "text": c} for a, b, c in FRAGILE],
    )
    out = {"meta": meta, "cases": CASES}
    with open(os.path.join(HERE, "oracles.json"), "w", encoding="utf-8") as fh:
        json.dump(CASES, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "oracles_meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    write_md(os.path.join(HERE, "cases.md"))
    print(f"{len(CASES)} cases; {sum(1 for c in CASES if c['kind']=='spec')} spec, "
          f"{sum(1 for c in CASES if c['kind']=='edge')} edge, {sum(1 for c in CASES if c['kind']=='hw')} hw")
    print("DISCREPANCIES:")
    for a, b in DISCREPANCIES:
        print(" ", a, "|", b)
    print("FRAGILE:")
    for a, b, c in FRAGILE:
        print(" ", a, b, "|", c)


if __name__ == "__main__":
    main()
