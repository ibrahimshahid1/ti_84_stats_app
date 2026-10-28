# STA 431 TI-84 Plus CE installation and device check

This package contains nine **TI-BASIC programs**, not a Flash application. Start it with `prgmSTA431` from the calculator's `PRGM` menu. The programs are meant to assist with the STA 431 Homework 1–3 question types and Freund Chapters 1–3; written proofs, mathematical setup, and sketches still require your work.

## Before transferring

1. Confirm that your instructor permits stored calculator programs on the midterm.
2. Back up your calculator with TI Connect CE. The programs use real variables `A`–`Z` and `θ`, strings `Str1`–`Str9`, and temporary named lists. They can replace existing values. Use the app's BACK choices to leave each calculator; pressing ON to interrupt skips normal cleanup.
3. Check the OS under **2nd → MEM → 1:About**. CE OS **5.3 or later** can execute archived TI-BASIC programs. On 5.2 or earlier, programs must be in RAM; the complete suite uses substantial RAM. Keep enough free RAM for calculations and consider updating the OS if needed.

## Transfer

1. Connect the TI-84 Plus CE to a computer, turn it on, and open **TI Connect CE → Calculator Explorer**.
2. Drag all nine `.8xp` files from `calculator_files/` onto the connected calculator and complete the transfer. The three `.8xg` files are an optional grouped alternative; one group cannot hold this entire suite. If grouped transfer does not expose all nine programs, send the individual files.
3. Verify these names appear in the `PRGM` menu: `STA431`, `STAFMT`, `STAE1`, `STAE2`, `STAE3`, `STAHNT`, `STACNT`, `STAPRB`, `STARV`.
4. If your OS is 5.3 or later, you can archive the larger programs to free RAM. Retest them after archiving. On older OS versions, leave them unarchived.

## Five-minute device smoke test

Mark each item after checking it **on the physical calculator**. The automated build and simulator tests do not replace these checks.

- [ ] Run `prgmSTA431`; open ENCYCLOPEDIA → each chapter → a topic, then return with CLEAR/BACK.
- [ ] Open WHICH TOOL? HINTS and return. If `ERR:UNDEFINED` appears, `STAHNT` is missing.
- [ ] Open CALCULATORS → COUNTING → `n!, nPr, nCr`; enter `n=5`, `r=2`. Check `nCr=10`, `nPr=20`, and return with BACK.
- [ ] Open CALCULATORS → PROBABILITY → TOTAL PROB/BAYES. The HW2 journal example should give `P(accept)=17/100` and `P(Methodology|accept)=15/34` when entered with its homework priors and conditional probabilities.
- [ ] Open CALCULATORS → RANDOM VARIABLES → MAX/MIN/SUM DRAWS. For maximum of two balls from 1–5 without replacement, check the PMF at 2, 3, 4, 5 is `1/10, 2/10, 3/10, 4/10`; return with BACK.
- [ ] Open CALCULATORS → RANDOM VARIABLES → JOINT X,Y, enter a small valid joint table, and check both marginals and a conditional probability against a hand calculation.
- [ ] Check typed-function evaluation in RANDOM VARIABLES → ANY f(x) OR F(x): enter `F(X)=1-e^(-2X)` on `[0,50]` and check `P(X>1)≈0.135335`. Confirm any preexisting `Y₀` and `Y₉` definitions remain unchanged afterward.
- [ ] Check JOINT X,Y → CONTINUOUS PDF using `f(X,Y)=1` on `[0,1]×[0,1]`: total area should be 1 and the lower-left half-by-half rectangle should have probability 1/4.
- [ ] Exit to the home screen. Reopen the app and confirm the menus still work and no `ERR:MEMORY`, `ERR:SYNTAX`, or `ERR:UNDEFINED` occurs.

## Use during a problem

Start with WHICH TOOL? when the problem type is unclear. Use the encyclopedia for formulas, assumptions, and proof outlines. Use a calculator menu after you have identified the sample space, support, or conditioning event. For continuous densities, a displayed decimal or fraction from numerical integration is an approximation unless you have independently derived an exact value.

**Official TI references:** [TI Connect CE transfer and backup](https://education.ti.com/html/eguides/graphing/84PlusCE/EN/content/eg_84tic/m_workdevicefile/df_copy_device_files.HTML), [executing archived programs on CE OS 5.3+](https://education.ti.com/html/webhelp/EG_TI84PlusCECode/EN/Subsystems/e-guide_prog_en/Content/M_EnterCommandLine/M_ExeProgram.HTML), [file types](https://education.ti.com/en/customer-support/knowledge-base/ti-83-84-plus-family/product-usage/29430).
