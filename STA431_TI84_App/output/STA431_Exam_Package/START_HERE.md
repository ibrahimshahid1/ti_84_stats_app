# STA 431 midterm TI-84 Plus CE helper

Run **`prgmSTA431`** after transferring the nine TI-BASIC programs. This is one menu-driven suite from the user's perspective: `STA431` opens the menus and calls the other eight programs as needed. It is not a TI Flash application.

## Choose a menu

- **ENCYCLOPEDIA:** compact formulas, recognition cues, worked examples, and proof outlines, with Freund as the primary reference.
- **CALCULATORS:** guided counting, probability, and random-variable computations. Start with **WHICH TOOL? HINTS** when you do not know which formula applies.
- **HELP + NOTATION:** navigation keys and symbols used on the calculator.

The one-page `EXAM_MENU_CARD.pdf` maps the STA 431 Homework 1–3 questions to menu paths. `INSTALL_AND_DEVICE_TEST.md` gives transfer instructions and checks to run on your own TI-84 Plus CE before the exam.

## What it covers

The suite targets the common and STA 431 questions in Homeworks 1–3: counting and binomial coefficients; event algebra, conditional probability, total probability and Bayes; discrete PMFs/CDFs; continuous PDFs/CDFs and transformations. It also includes Freund Chapter 3 joint, marginal, conditional, and independence concepts, with joint numerical tools where the input form fits.

The program helps set up and check computations. It does not replace written proofs, event notation, sketches, or a derivation of the support and integration limits. Typed-function integration and differentiation are numerical; verify any claimed exact form from mathematics.

## Files

- `calculator_files/1_TRANSFER_ALL_NINE_PROGRAMS/`: select all nine `.8xp` files and drag them to TI Connect CE together. This is the recommended transfer method.
- `calculator_files/2_OPTIONAL_THREE_GROUPS/`: three `.8xg` files containing the same nine programs, split because the full suite cannot fit in one group with this package format. Use this only as an alternative to the individual files; do not send both sets.
- `EXAM_MENU_CARD.pdf` and `.md`: quick menu map.
- `INSTALL_AND_DEVICE_TEST.md`: installation and physical-device test checklist.
- `source_code/`: TI-BASIC sources, content JSON, build specification, and Python requirements.
- `SHA256SUMS.txt`: checksums for package contents.

The source is validated by tokenization, static lints, a TI-BASIC simulator, and homework-style regression tests. **Physical CE behavior remains to be checked on your calculator.** The programs use calculator variables `A`–`Z`, `θ`, and `Str1`–`Str9`; back up existing work before installing. Leave tools through BACK.
