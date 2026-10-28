# STA 431 midterm TI-84 Plus CE helper

Run **`prgmSTA431`** after transferring the nine TI-BASIC programs. This is a menu-driven program suite, not a TI Flash application.

## Choose a menu

- **ENCYCLOPEDIA:** compact formulas, recognition cues, worked examples, and proof outlines, with Freund as the primary reference.
- **CALCULATORS:** guided counting, probability, and random-variable computations. Start with **WHICH TOOL? HINTS** when you do not know which formula applies.
- **HELP + NOTATION:** navigation keys and symbols used on the calculator.

The one-page `EXAM_MENU_CARD.pdf` maps the STA 431 Homework 1–3 questions to menu paths. `INSTALL_AND_DEVICE_TEST.md` gives transfer instructions and checks to run on your own TI-84 Plus CE before the exam.

## What it covers

The suite targets the common and STA 431 questions in Homeworks 1–3: counting and binomial coefficients; event algebra, conditional probability, total probability and Bayes; discrete PMFs/CDFs; continuous PDFs/CDFs and transformations. It also includes Freund Chapter 3 joint, marginal, conditional, and independence concepts, with joint numerical tools where the input form fits.

The program helps set up and check computations. It does not replace written proofs, event notation, sketches, or a derivation of the support and integration limits. Typed-function integration and differentiation are numerical; verify any claimed exact form from mathematics.

## Files

- `calculator_files/STA_REF1.8xg`, `STA_REF2.8xg`, `STA_CALC.8xg`: three optional groups. A single TI group cannot hold the whole suite.
- `calculator_files/*.8xp`: all nine individual programs; send these if group transfer does not expose every program.
- `EXAM_MENU_CARD.pdf` and `.md`: quick menu map.
- `INSTALL_AND_DEVICE_TEST.md`: installation and physical-device test checklist.
- `source_code/`: TI-BASIC sources, content JSON, build specification, and Python requirements.
- `SHA256SUMS.txt`: checksums for package contents.

The source is validated by tokenization, static lints, a TI-BASIC simulator, and homework-style regression tests. **Physical CE behavior remains to be checked on your calculator.** The programs use calculator variables `A`–`Z`, `θ`, and `Str1`–`Str9`; back up existing work before installing. Leave tools through BACK.
