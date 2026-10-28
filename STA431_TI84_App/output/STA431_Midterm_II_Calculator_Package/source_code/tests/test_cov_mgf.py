#!/usr/bin/env python3
"""Token-stream simulator tests for the new covariance and MGF modules.

Run: python midterm2_app/tests/test_cov_mgf.py
These tests establish simulated numerical/menu behavior, not physical-device qualification.
"""
import math
from pathlib import Path
import sys
import unittest

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
        r = self.run_module("M2COV", [m(1), m(1)] + inputs(2, 300, 500, 150, 2, 1.1, 100) + [m(3)])
        self.value(r, "COMBINATION U", "VAR(U)", 2465)
        self.assertIn("MEAN NOT PROVIDED", r.text)

    def test_hw5_q6_three_variable_variance(self):
        r = self.run_module("M2COV", [m(1), m(1)] + inputs(3, 4, 9, 2, 1, -1, 0, 3, -2, 1, 0) + [m(3)])
        self.value(r, "COMBINATION U", "VAR(U)", 56)

    def test_two_combinations_mean_variance_covariance(self):
        r = self.run_module("M2COV", [m(2), m(2)] + inputs(2, 1, 4, 2, 9, -1, 2, 1, -1, 3, 1, -4) + [m(3)])
        self.value(r, "COMBINATION U", "E(U)", 1)
        self.value(r, "COMBINATION U", "VAR(U)", 29)
        self.value(r, "COMBINATION V", "E(V)", 3)
        self.value(r, "COMBINATION V", "VAR(V)", 79)
        self.value(r, "TWO COMBINATIONS", "COV(U,V)", -24)
        self.value(r, "TWO COMBINATIONS", "CORR(U,V)", -24 / math.sqrt(29 * 79))

    def test_one_variable_affine(self):
        r = self.run_module("M2COV", [m(1), m(2)] + inputs(1, 2, 3, -4, 7) + [m(3)])
        self.value(r, "COMBINATION U", "E(U)", -1)
        self.value(r, "COMBINATION U", "VAR(U)", 48)

    def test_zero_variance_correlation_undefined(self):
        r = self.run_module("M2COV", [m(2), m(1)] + inputs(2, 0, 1, 0, 1, 0, 0, 1, 0, 0) + [m(3)])
        self.value(r, "COMBINATION U", "VAR(U)", 0)
        self.value(r, "COMBINATION V", "VAR(V)", 1)
        self.assertIn("UNDEFINED ZERO VARIANCE", r.text)

    def test_invalid_covariance_matrix_reentry(self):
        r = self.run_module("M2COV", [m(1), m(1)] +
                            inputs(3, 1, 1, 1, .9, .9, -.9,
                                   1, 1, 1, 0, 0, 0, 1, 0, 0, 0) + [m(3)])
        self.assertIn("INVALID COVARIANCE DATA", r.text)
        self.value(r, "COMBINATION U", "VAR(U)", 1)

    def test_invalid_variance_reentry(self):
        r = self.run_module("M2COV", [m(1), m(1)] + inputs(2, -1, 4, 1, 4, 0, 1, 1, 0) + [m(3)])
        self.assertIn("VARIANCE MUST BE ≥0", r.text)
        self.value(r, "COMBINATION U", "VAR(U)", 5)

    def test_invalid_dimension_reentry(self):
        r = self.run_module("M2COV", [m(1), m(1)] + inputs(4, 1, 2, 3, 0) + [m(3)])
        self.assertIn("n MUST BE INTEGER 1 TO 3", r.text)
        self.value(r, "COMBINATION U", "VAR(U)", 18)

    def test_hw5_q4_exact_quadratic_mgf_transform(self):
        r = self.run_module("M2MGF", [m(2)] + inputs(4, 8, .25, -1) + [m(3)])
        self.value(r, "ORIGINAL X MOMENTS", "E(X)", 4)
        self.value(r, "ORIGINAL X MOMENTS", "E(X²)", 32)
        self.value(r, "ORIGINAL X MOMENTS", "VAR(X)", 16)
        self.value(r, "Z=aX+b MOMENTS", "E(Z)", 0)
        self.value(r, "Z=aX+b MOMENTS", "VAR(Z)", 1)
        self.assertIn("H=1/2", r.text)

    def test_hw5_q3_exponential_rate(self):
        r = self.run_module("M2MGF", [m(1)] + inputs(3, 1, 0) + [m(3)])
        self.value(r, "ORIGINAL X MOMENTS", "E(X)", 1 / 3)
        self.value(r, "ORIGINAL X MOMENTS", "E(X²)", 2 / 9)
        self.value(r, "ORIGINAL X MOMENTS", "VAR(X)", 1 / 9)
        self.assertIn("DOMAIN t<3", r.text)

    def test_negative_scale_reverses_domain_and_eval(self):
        r = self.run_module("M2MGF", [m(1)] + inputs(2, -2, 3) + [m(1)] + inputs(1) + [m(3)])
        self.value(r, "Z=aX+b MOMENTS", "E(Z)", 2)
        self.value(r, "Z=aX+b MOMENTS", "VAR(Z)", 1)
        self.assertIn("DOMAIN t>⁻1", r.text)
        self.assertAlmostEqual(number(self.screen(r, "NUMERIC Mz(t)")[2]), math.exp(3) / 2, delta=1e-7)

    def test_exponential_evaluation_rejects_boundary(self):
        r = self.run_module("M2MGF", [m(1)] + inputs(2, -2, 3) + [m(1)] + inputs(-1) + [m(3)])
        self.assertIn("OUTSIDE MGF DOMAIN", r.text)

    def test_zero_scale_gives_constant(self):
        r = self.run_module("M2MGF", [m(1)] + inputs(2, 0, 7) + [m(3)])
        self.value(r, "Z=aX+b MOMENTS", "E(Z)", 7)
        self.value(r, "Z=aX+b MOMENTS", "VAR(Z)", 0)
        self.assertIn("ALL REAL t; Mz=e^(B*t)", r.text)

    def test_generic_exponential_numeric(self):
        r = self.run_module("M2MGF", [m(3)] + inputs("3/(3-X)", 1, 0) + [m(3)])
        self.value(r, "APPROX X MOMENTS", "E(X)", 1 / 3, delta=2e-6)
        self.value(r, "APPROX X MOMENTS", "VAR(X)", 1 / 9, delta=2e-6)
        self.assertIn("M(0)=1 IS NOT A PROOF", r.text)
        self.assertIn("AGREE AT .1% SCALE TEST", r.text)

    def test_generic_quadratic_numeric(self):
        r = self.run_module("M2MGF", [m(3)] + inputs("𝑒^(4X+8X²)", .25, -1) + [m(3)])
        self.value(r, "APPROX X MOMENTS", "E(X)", 4, delta=.002)
        self.value(r, "APPROX Z=aX+b MOMENTS", "VAR(Z)", 1, delta=.001)
        self.assertNotIn("APPROX X MOMENTSTS", r.text)

    def test_generic_step_size_warning(self):
        r = self.run_module("M2MGF", [m(3)] + inputs("𝑒^(100X²)", 1, 0) + [m(3)])
        self.assertIn("WARNING STEP-SIZE CHANGE", r.text)

    def test_generic_invalid_m0(self):
        r = self.run_module("M2MGF", [m(3)] + inputs("2+X", 1, 0) + [m(4)])
        self.assertIn("M(0) MUST EQUAL 1", r.text)

    def test_generic_negative_values(self):
        r = self.run_module("M2MGF", [m(3)] + inputs("1+200X", 1, 0) + [m(4)])
        self.assertIn("MGF VALUES MUST BE >0", r.text)

    def test_generic_negative_variance(self):
        r = self.run_module("M2MGF", [m(3)] + inputs("𝑒^(2X-X²)", 1, 0) + [m(4)])
        self.assertIn("NEGATIVE APPROX VARIANCE", r.text)

    def test_invalid_rate_then_reentry(self):
        r = self.run_module("M2MGF", [m(1)] + inputs(0, 2, 1, 0) + [m(3)])
        self.assertIn("RATE MUST BE POSITIVE", r.text)
        self.value(r, "ORIGINAL X MOMENTS", "E(X)", .5)

    def test_negative_quadratic_then_reentry(self):
        r = self.run_module("M2MGF", [m(2)] + inputs(0, -1, 0, 1, 1, 0) + [m(3)])
        self.assertIn("D MUST BE ≥0", r.text)
        self.value(r, "ORIGINAL X MOMENTS", "VAR(X)", 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
