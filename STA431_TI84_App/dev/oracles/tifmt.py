"""tifmt.py - emulation of TI-84 Plus CE number display and of the STAFMT subroutine.

Used by gen_oracles.py to predict exactly what a calculator tool shows for a value.

* TI keeps 14 significant digits internally -> all arithmetic here uses a Decimal context
  with prec=14 (ROUND_HALF_EVEN; the difference to TI's rounding never matters here).
* Display / toString( in Normal Float mode: 10 significant digits, trailing zeros removed,
  no leading zero (".5"), negative sign is U+207B, scientific notation (mantissa + U+1D07 +
  exponent) when |x| < 1E-3 or |x| >= 1E10.
* round(x,6) rounds half away from zero.
* STAFMT: continued-fraction convergents of |W| (see src/STAFMT.txt), exact N/D when D<=9999
  and |N/D - |W|| < 1E-10*max(1,|W|).
"""
from decimal import Decimal, Context, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
from fractions import Fraction
import mpmath

NEG = "⁻"   # ⁻
EE = "ᴇ"    # ᴇ

TI = Context(prec=14, rounding=ROUND_HALF_EVEN)


def to_dec(x):
    """Value -> 14-digit Decimal (what the calculator would hold)."""
    if isinstance(x, Decimal):
        return TI.plus(x)
    if isinstance(x, Fraction):
        return TI.divide(Decimal(x.numerator), Decimal(x.denominator))
    if isinstance(x, int):
        return TI.plus(Decimal(x))
    if isinstance(x, mpmath.mpf):
        return TI.plus(Decimal(mpmath.nstr(x, 30, strip_zeros=False)))
    if isinstance(x, float):
        return TI.plus(Decimal(repr(x)))
    # sympy numbers
    try:
        import sympy
        if isinstance(x, sympy.Basic):
            return TI.plus(Decimal(str(sympy.N(x, 30))))
    except ImportError:
        pass
    raise TypeError(type(x))


def ti_str(x):
    """toString( / display of a value in Normal Float mode."""
    d = to_dec(x)
    if d == 0:
        return "0"
    sign = NEG if d < 0 else ""
    a = abs(d)
    with localcontext() as c:
        c.prec = 10
        c.rounding = ROUND_HALF_UP
        a10 = +a  # 10 significant digits
    if Decimal("1e-3") <= a10 < Decimal("1e10"):
        s = format(a10, "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        if s.startswith("0."):
            s = s[1:]
        return sign + s
    # scientific
    exp = a10.adjusted()
    mant = a10.scaleb(-exp)
    ms = format(mant, "f")
    if "." in ms:
        ms = ms.rstrip("0").rstrip(".")
    es = (NEG + str(-exp)) if exp < 0 else str(exp)
    return sign + ms + EE + es


def ti_round(x, places=6):
    d = to_dec(x)
    q = Decimal(1).scaleb(-places)
    return d.quantize(q, rounding=ROUND_HALF_UP)


def stafmt(x):
    """Return (Str9, Str8) exactly as src/STAFMT.txt would produce them."""
    W = to_dec(x)
    aW = abs(W)
    if aW >= Decimal("1e-4") and aW < Decimal("1e10"):
        str8 = ti_str(ti_round(W, 6))
    else:
        str8 = ti_str(W)
    c = TI
    U = aW
    Q, R, S, T = Decimal(1), Decimal(0), Decimal(0), Decimal(1)
    tol = c.multiply(Decimal("1e-10"), max(Decimal(1), aW))
    for _ in range(200):
        V = Decimal(int(U))  # int( = floor for U>=0
        R = c.add(c.multiply(V, Q), R)
        Q = c.add(Q, R)
        R = c.subtract(Q, R)
        Q = c.subtract(Q, R)
        T = c.add(c.multiply(V, S), T)
        S = c.add(S, T)
        T = c.subtract(S, T)
        S = c.subtract(S, T)
        U = c.subtract(U, V)
        if U >= Decimal("1e-9"):
            U = c.divide(Decimal(1), U)
        if S > 9999 or U < Decimal("1e-9") or abs(c.subtract(c.divide(Q, S), aW)) < tol:
            break
    str9 = str8
    if S <= 9999 and abs(c.subtract(c.divide(Q, S), aW)) < tol:
        if W < 0:
            Q = -Q
        str9 = ti_str(Q)
        if S != 1:
            str9 = str9 + "/" + ti_str(S)
    return str9, str8


def stafmt_robust(x, rel=Decimal("1e-11")):
    """Run STAFMT on x and on x*(1 +- rel); report whether the display is stable.
    rel=1e-11 models a numeric (fnInt / nDeriv) result; rel ~ 1e-13 models 14-digit roundoff."""
    base = stafmt(x)
    d = to_dec(x)
    outs = {base}
    for f in (Decimal(1) + rel, Decimal(1) - rel):
        outs.add(stafmt(TI.multiply(d, f)))
    return base, len(outs) == 1, sorted(outs)


if __name__ == "__main__":
    tests = [Fraction(1, 2), Fraction(-1, 2), Fraction(147, 10000), Fraction(2162, 54145),
             Fraction(95, 294), 120, 479001600, Fraction(5, 19706), Fraction(35, 128),
             mpmath.e ** -2, Fraction(1, 9), 87178291200, 0, Fraction(1, 10**11)]
    for t in tests:
        print(t, stafmt(t))
