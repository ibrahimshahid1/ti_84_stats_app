#!/usr/bin/env python3
"""Token-stream simulator tests for the new covariance and MGF modules.

Run: python midterm2_app/tests/test_cov_mgf.py
These tests establish simulated numerical/menu behavior, not physical-device qualification.
"""
import math
from pathlib import Path
import sys
import unittest

import sympy as sp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tisim import Sim
from tilint import lint_file
import tibuild


def m(n):
    return {"menu": n}


def i(value):
    # Numeric negatives use TI's unary-negative token; subtraction inside
    # a typed expression must remain the binary-minus token.
    text = str(value)
    if isinstance(value, (int, float)) and value < 0:
        text = "⁻" + text[1:]
    return {"input": text}


def inputs(*values):
    return [i(v) for v in values]


def number(text):
    text = text.strip().replace("⁻", "-").replace("ᴇ", "e")
    if "/" in text:
        a, b = text.split("/")
        return float(a) / float(b)
    return float(text)


class Modules(unittest.TestCase):
    def run_module(self, program, actions):
        r = Sim(str(ROOT / "src")).run(program, actions=actions, max_steps=500_000)
        self.assertIsNone(r.error, r.text)
        self.assertEqual(r.leaks, 0, r.text)
        self.assertFalse(r.warnings, r.warnings)
        self.assertIn(r.ended_reason, ("end", "return"), r.text)
        private = ("M2MU", "M2VR", "M2CV", "M2CA", "M2CB", "M2CR", "M2MR", "M2MV", "M2MD")
        self.assertFalse(set(private) & set(r.vars["lists"]), r.vars["lists"])
        return r

    def screen(self, r, title):
        for screen in r.screens:
            if screen["event"] == "pause" and screen["rows"][0].strip() == title:
                return [row.strip() for row in screen["rows"]]
        self.fail(f"Missing screen {title!r}\n{r.text}")

    def value(self, r, title, label, expected, delta=1e-6):
        screen = self.screen(r, title)
        k = screen.index(label)
        self.assertAlmostEqual(number(screen[k + 1]), expected, delta=delta)

    def test_static_and_token_roundtrip(self):
        for program in ("M2COV", "M2MGF"):
            p = ROOT / "src" / (program + ".txt")
            self.assertEqual(lint_file(str(p)), [])
            text = tibuild.clean_source(p.read_text())
            self.assertTrue(tibuild.tokenize(text))

    def test_hw5_q5_insurance_variance(self):
        r = self.run_module("M2COV", [m("ONE COMBINATION"), m("VAR/COV ONLY")] + inputs(2, 300, 500, 150, 2, 1.1, 100) + [m("BACK")])
        self.value(r, "COMBINATION U", "VAR(U)", 2465)
        self.assertIn("MEAN NOT PROVIDED", r.text)

    def test_hw5_q6_three_variable_variance(self):
        r = self.run_module("M2COV", [m("ONE COMBINATION"), m("VAR/COV ONLY")] + inputs(3, 4, 9, 2, 1, -1, 0, 3, -2, 1, 0) + [m("BACK")])
        self.value(r, "COMBINATION U", "VAR(U)", 56)

    def test_two_combinations_mean_variance_covariance(self):
        r = self.run_module("M2COV", [m("TWO COMBINATIONS"), m("MEAN+VAR/COV")] + inputs(2, 1, 4, 2, 9, -1, 2, 1, -1, 3, 1, -4) + [m("BACK")])
        self.value(r, "COMBINATION U", "E(U)", 1)
        self.value(r, "COMBINATION U", "VAR(U)", 29)
        self.value(r, "COMBINATION V", "E(V)", 3)
        self.value(r, "COMBINATION V", "VAR(V)", 79)
        self.value(r, "TWO COMBINATIONS", "COV(U,V)", -24)
        self.value(r, "TWO COMBINATIONS", "CORR(U,V)", -24 / math.sqrt(29 * 79))

    def test_one_variable_affine(self):
        r = self.run_module("M2COV", [m("ONE COMBINATION"), m("MEAN+VAR/COV")] + inputs(1, 2, 3, -4, 7) + [m("BACK")])
        self.value(r, "COMBINATION U", "E(U)", -1)
        self.value(r, "COMBINATION U", "VAR(U)", 48)

    def test_zero_variance_correlation_undefined(self):
        r = self.run_module("M2COV", [m("TWO COMBINATIONS"), m("VAR/COV ONLY")] + inputs(2, 0, 1, 0, 1, 0, 0, 1, 0, 0) + [m("BACK")])
        self.value(r, "COMBINATION U", "VAR(U)", 0)
        self.value(r, "COMBINATION V", "VAR(V)", 1)
        self.assertIn("UNDEFINED ZERO VARIANCE", r.text)

    def test_invalid_covariance_matrix_reentry(self):
        r = self.run_module("M2COV", [m("ONE COMBINATION"), m("VAR/COV ONLY")] +
                            inputs(3, 1, 1, 1, .9, .9, -.9,
                                   1, 1, 1, 0, 0, 0, 1, 0, 0, 0) + [m("BACK")])
        self.assertIn("INVALID COVARIANCE DATA", r.text)
        self.value(r, "COMBINATION U", "VAR(U)", 1)

    def test_invalid_variance_reentry(self):
        r = self.run_module("M2COV", [m("ONE COMBINATION"), m("VAR/COV ONLY")] + inputs(2, -1, 4, 1, 4, 0, 1, 1, 0) + [m("BACK")])
        self.assertIn("VARIANCE MUST BE ≥0", r.text)
        self.value(r, "COMBINATION U", "VAR(U)", 5)

    def test_invalid_dimension_reentry(self):
        r = self.run_module("M2COV", [m("ONE COMBINATION"), m("VAR/COV ONLY")] + inputs(4, 1, 2, 3, 0) + [m("BACK")])
        self.assertIn("n MUST BE INTEGER 1 TO 3", r.text)
        self.value(r, "COMBINATION U", "VAR(U)", 18)

    def test_hw5_q4_exact_quadratic_mgf_transform(self):
        r = self.run_module("M2MGF", [m("QUADRATIC LOG MGF")] + inputs(4, 8, .25, -1) + [m("BACK")])
        self.value(r, "ORIGINAL X MOMENTS", "E(X)", 4)
        self.value(r, "ORIGINAL X MOMENTS", "E(X²)", 32)
        self.value(r, "ORIGINAL X MOMENTS", "VAR(X)", 16)
        self.value(r, "Z=aX+b MOMENTS", "E(Z)", 0)
        self.value(r, "Z=aX+b MOMENTS", "VAR(Z)", 1)
        self.assertIn("H=1/2", r.text)

    def test_hw5_q3_exponential_rate(self):
        r = self.run_module("M2MGF", [m("EXPONENTIAL RATE")] + inputs(3, 1, 0) + [m("BACK")])
        self.value(r, "ORIGINAL X MOMENTS", "E(X)", 1 / 3)
        self.value(r, "ORIGINAL X MOMENTS", "E(X²)", 2 / 9)
        self.value(r, "ORIGINAL X MOMENTS", "VAR(X)", 1 / 9)
        self.assertIn("DOMAIN t<3", r.text)

    def test_negative_scale_reverses_domain_and_eval(self):
        r = self.run_module("M2MGF", [m("EXPONENTIAL RATE")] + inputs(2, -2, 3) + [m("EVAL Mz AT t")] + inputs(1) + [m("BACK")])
        self.value(r, "Z=aX+b MOMENTS", "E(Z)", 2)
        self.value(r, "Z=aX+b MOMENTS", "VAR(Z)", 1)
        self.assertIn("DOMAIN t>⁻1", r.text)
        self.assertAlmostEqual(number(self.screen(r, "NUMERIC Mz(t)")[2]), math.exp(3) / 2, delta=1e-7)

    def test_exponential_evaluation_rejects_boundary(self):
        r = self.run_module("M2MGF", [m("EXPONENTIAL RATE")] + inputs(2, -2, 3) + [m("EVAL Mz AT t")] + inputs(-1) + [m("BACK")])
        self.assertIn("OUTSIDE MGF DOMAIN", r.text)

    def test_zero_scale_gives_constant(self):
        r = self.run_module("M2MGF", [m("EXPONENTIAL RATE")] + inputs(2, 0, 7) + [m("BACK")])
        self.value(r, "Z=aX+b MOMENTS", "E(Z)", 7)
        self.value(r, "Z=aX+b MOMENTS", "VAR(Z)", 0)
        self.assertIn("ALL REAL t; Mz=e^(B*t)", r.text)

    def test_generic_exponential_numeric(self):
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("3/(3-X)", 1, 0) + [m("BACK")])
        self.value(r, "APPROX X MOMENTS", "E(X)", 1 / 3, delta=2e-6)
        self.value(r, "APPROX X MOMENTS", "VAR(X)", 1 / 9, delta=2e-6)
        self.assertIn("M(0)=1 IS NOT A PROOF", r.text)
        self.assertIn("RELATIVE ERROR EST <1ᴇ⁻6", r.text)
        self.assertIn("RICHARDSON h=.01 TO .0025", r.text)
        self.assertNotIn("WARNING STEP-SIZE CHANGE", r.text)

    def test_generic_quadratic_numeric(self):
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("𝑒^(4X+8X²)", .25, -1) + [m("BACK")])
        self.value(r, "APPROX X MOMENTS", "E(X)", 4, delta=.002)
        self.value(r, "APPROX Z=aX+b MOMENTS", "VAR(Z)", 1, delta=.001)
        self.assertNotIn("APPROX X MOMENTSTS", r.text)

    def test_generic_step_size_warning(self):
        # Fix round 1: the warning now measures the error of the REPORTED Richardson value. An
        # exponential with mean 20 (1/(1-20t)) is too wide for h=.01: estimated error > 1E-6 relative.
        e1, e2, var = self.sympy_moments(lambda t: 1 / (1 - 20 * t))
        self.assertEqual((e1, var), (20.0, 400.0))
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("1/(1-20X)", 1, 0) + [m("BACK")])
        self.assertIn("WARNING STEP-SIZE CHANGE", r.text)
        self.assertIn("TRY M(X/10), SCALE 10a", r.text)
        self.assertNotIn("RELATIVE ERROR EST <1ᴇ⁻6", r.text)
        # ...and the advice works: M(t/10)=1/(1-2t) with scale 10 gives X's moments without a warning.
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("1/(1-2X)", 10, 0) + [m("BACK")])
        self.assertNotIn("WARNING STEP-SIZE CHANGE", r.text)
        self.value(r, "APPROX Z=aX+b MOMENTS", "E(Z)", e1, delta=1e-5)
        self.value(r, "APPROX Z=aX+b MOMENTS", "VAR(Z)", var, delta=1e-4)

    def test_smooth_mgf_has_no_step_warning(self):
        # e^(100t²) (normal, variance 200): the Richardson value is accurate, so no warning (P1 used
        # to warn here because it compared against the cruder h=.005 value).
        e1, e2, var = self.sympy_moments(lambda t: sp.exp(100 * t ** 2))
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("𝑒^(100X²)", 1, 0) + [m("BACK")])
        self.assertNotIn("WARNING STEP-SIZE CHANGE", r.text)
        self.value(r, "APPROX X MOMENTS", "E(X)", e1, delta=1e-8)
        self.value(r, "APPROX X MOMENTS", "VAR(X)", var, delta=1e-5)

    def test_generic_invalid_m0(self):
        # M(.001)=2.001 is not within .05 of 1 (M itself is never evaluated at 0).
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("2+X", 1, 0) + [m("BACK")])
        self.assertIn("M(0) MUST BE 1", r.text)
        self.assertIn("M(.001) IS NOT NEAR 1", r.text)

    def test_large_mean_message_and_rescale(self):
        # Fix round 1: 1/(1-50t) is a valid MGF (exponential, mean 50) but M(.001)=1.0526; the message
        # must not just say M(0) is wrong, it must offer the rescale M(t/10) with scale 10a.
        e1, e2, var = self.sympy_moments(lambda t: 1 / (1 - 50 * t))
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("1/(1-50X)", 1, 0) + [m("BACK")])
        self.assertIn("IF IT IS OK, THE MEAN IS", r.text)
        self.assertIn("TYPE M(X/10), SCALE 10a", r.text)
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("1/(1-5X)", 10, 0) + [m("BACK")])
        self.value(r, "APPROX Z=aX+b MOMENTS", "E(Z)", e1, delta=1e-5)
        self.value(r, "APPROX Z=aX+b MOMENTS", "VAR(Z)", var, delta=1e-3)

    def test_generic_negative_values(self):
        # passes the M(.001) check (.99) but M(.01)=0, so the positivity guard must fire
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("1-10000X²", 1, 0) + [m("BACK")])
        self.assertIn("MGF VALUES MUST BE >0", r.text)
        self.assertNotIn("M(0) MUST BE 1", r.text)

    def sympy_moments(self, M):
        t = sp.symbols("t")
        M = M(t)
        e1 = sp.limit(sp.diff(M, t), t, 0)
        e2 = sp.limit(sp.diff(M, t, 2), t, 0)
        return float(e1), float(e2), float(e2 - e1 ** 2)

    def test_p1_typed_mgf_richardson_accuracy(self):
        # (1-2t)^-3 (gamma, mean 6, variance 12): plain h=.005 differences are off by .002/.03;
        # the Richardson values must be within 1e-5 (mean) and 1e-4 (variance) of the sympy limits.
        e1, e2, var = self.sympy_moments(lambda t: (1 - 2 * t) ** -3)
        self.assertEqual((e1, var), (6.0, 12.0))
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("(1-2X)^⁻3", 1, 0) + [m("BACK")])
        self.value(r, "APPROX X MOMENTS", "E(X)", e1, delta=1e-5)
        self.value(r, "APPROX X MOMENTS", "E(X²)", e2, delta=1e-4)
        self.value(r, "APPROX X MOMENTS", "VAR(X)", var, delta=1e-4)
        two = self.screen(r, "NUMERIC STEP CHECK")
        self.assertEqual(two[1], "E(X) h=.005 / RICHARDSON")
        self.assertGreater(abs(number(two[2]) - e1), 1e-3)        # h=.005 alone is worse
        self.assertLess(abs(number(two[3]) - e1), 1e-7)           # the Richardson value is shown too
        self.assertLess(abs(number(two[6]) - e2), 1e-6)
        # Fix round 1: the warning measures the Richardson value's own error, so none here.
        self.assertNotIn("WARNING STEP-SIZE CHANGE", r.text)
        self.assertIn("RELATIVE ERROR EST <1ᴇ⁻6", r.text)

    def test_mock5_q5_gamma_mgf_transformed(self):
        # Mock 5 Q5 style: M(t)=(1-2t)^-2 (E=4, Var=8); Z=-3X+2 has E=-10, Var=72. No warning.
        e1, e2, var = self.sympy_moments(lambda t: (1 - 2 * t) ** -2)
        self.assertEqual((e1, var), (4.0, 8.0))
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("(1-2X)^⁻2", -3, 2) + [m("BACK")])
        self.assertNotIn("WARNING STEP-SIZE CHANGE", r.text)
        self.value(r, "APPROX X MOMENTS", "E(X)", e1, delta=1e-6)
        self.value(r, "APPROX X MOMENTS", "VAR(X)", var, delta=1e-6)
        self.value(r, "APPROX Z=aX+b MOMENTS", "E(Z)", -3 * e1 + 2, delta=1e-6)
        self.value(r, "APPROX Z=aX+b MOMENTS", "VAR(Z)", 9 * var, delta=1e-5)

    def test_eval_typed_mgf_at_zero(self):
        # Fix round 1: EVAL Mz AT t=0 on the uniform MGF used to stop with ERR:DIVIDE BY 0 and leave
        # the M2M lists behind. Mx(0)=1 by definition; t=1/2 must give (e-1)/1 (sympy).
        Mu = lambda t: (sp.exp(2 * t) - 1) / (2 * t)
        self.assertEqual(sp.limit(Mu(sp.symbols("t")), sp.symbols("t"), 0), 1)
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("(𝑒^(2X)-1)/(2X)", 1, 0) +
                            [m("EVAL Mz AT t"), i(0), m("BACK")])
        rows = self.screen(r, "NUMERIC Mz(t)")
        self.assertEqual(rows[2], "1")
        self.assertIn("Mx(0)=1 BY DEFINITION", rows)
        self.assertIn("Mz(t)=e^(b*t)*Mx(a*t)", r.text)                 # header before the prompt
        self.assertAlmostEqual(float(r.var("Y")), 1.0, delta=1e-12)
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("(𝑒^(2X)-1)/(2X)", 1, 0) +
                            [m("EVAL Mz AT t"), i("1/2"), m("BACK")])
        self.assertAlmostEqual(float(r.var("Y")), float(Mu(sp.Rational(1, 2))), delta=1e-9)
        self.assertNotIn("BY DEFINITION", r.text)
        # a=0 makes Mx(a*t)=Mx(0) for every t: Mz(t)=e^(b*t)
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("(𝑒^(2X)-1)/(2X)", 0, 3) +
                            [m("EVAL Mz AT t"), i(1), m("BACK")])
        self.assertAlmostEqual(float(r.var("Y")), math.exp(3), delta=1e-9)

    def test_p1_uniform_mgf_never_evaluated_at_zero(self):
        # uniform(0,2): M(t)=(e^(2t)-1)/(2t) divides by 0 at t=0; the tool must not crash.
        e1, e2, var = self.sympy_moments(lambda t: (sp.exp(2 * t) - 1) / (2 * t))
        self.assertEqual((e1, var), (1.0, float(sp.Rational(1, 3))))
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("(𝑒^(2X)-1)/(2X)", 1, 0) + [m("BACK")])
        self.value(r, "APPROX X MOMENTS", "E(X)", e1, delta=1e-5)
        self.value(r, "APPROX X MOMENTS", "VAR(X)", var, delta=1e-6)
        self.assertIn("RELATIVE ERROR EST <1ᴇ⁻6", r.text)
        self.assertNotIn("M(0) MUST BE 1", r.text)

    def test_generic_negative_variance(self):
        r = self.run_module("M2MGF", [m("TYPE MGF NUMERIC")] + inputs("𝑒^(2X-X²)", 1, 0) + [m("BACK")])
        self.assertIn("NEGATIVE APPROX VARIANCE", r.text)

    def test_invalid_rate_then_reentry(self):
        r = self.run_module("M2MGF", [m("EXPONENTIAL RATE")] + inputs(0, 2, 1, 0) + [m("BACK")])
        self.assertIn("RATE MUST BE POSITIVE", r.text)
        self.value(r, "ORIGINAL X MOMENTS", "E(X)", .5)

    def test_negative_quadratic_then_reentry(self):
        r = self.run_module("M2MGF", [m("QUADRATIC LOG MGF")] + inputs(0, -1, 0, 1, 1, 0) + [m("BACK")])
        self.assertIn("D MUST BE ≥0", r.text)
        self.value(r, "ORIGINAL X MOMENTS", "VAR(X)", 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
