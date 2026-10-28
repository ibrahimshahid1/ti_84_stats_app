# STA 431 Midterm Menu Card

**TI-84 Plus CE | Freund Chapters 1-3 | Homework 1-3**

Start with `PRGM` > `STA431`. `CALC` means **CALCULATORS**, `ENC` means **ENCYCLOPEDIA**, and `RV` means **RANDOM VARIABLES**. Use the calculator's `(-)` key to enter `-1` for an unknown value. Press `ENTER` to advance on encyclopedia pages; use `BACK` to exit calculator tools.

Menu numbers in the paths below refer to options on each screen. The app checks computations and supplies method cues; write the algebraic proofs and graph sketches in your own solution.

## Homework 1 | Counting

| Q | Menu path | Cue / rule |
|---|---|---|
| 1. Pascal identity + story proof | `ENC > CH1 > BINOMIAL COEFFS > PASCAL IDENTITY` | C(n,r) = C(n-1,r-1)+C(n-1,r). Algebra: common denominator. Story: fix one item. |
| 2. Two binomial-sum proofs | `ENC > CH1 > BINOMIAL COEFFS > SUM IDENTITIES` | Differentiate (1+x)^n at x=1; integrate it from 0 to 1. Results: n·2^(n-1); (2^(n+1)-1)/(n+1). |
| 3. x³y²z² term coefficient | `CALC > COUNT > 6` | Enter (2,3), (-1,2), (3,2). Rule: 7!/(3!2!2!) × 2³(-1)²3². |
| 4. PROBABILITY arrangements | `CALC > COUNT > 2` | Enter word; choose LETTER BLOCK B for adjacent B's. Total 11!/(2!2!); block 10!/2!. |
| 5. Three distinct committees | `CALC > COUNT > 3 > 1` | Sizes 3,4,5; LABELED=1. Rule: 12!/(3!4!5!). |
| 6. T/F exam: 15 right, 2 hard | `CALC > COUNT > 4` | A=5 hard, B=15 other, K=15; hard min=max 2. C(5,2)C(15,13). |
| 7. Delegation: at least 2 each | `CALC > COUNT > 4` | A=8 math, B=6 stats, K=5; min 2 each. Sum C(8,i)C(6,5-i), i=2,3. |
| 8. Grades: exact A and F | `CALC > COUNT > 3 > 2` | N=10; exact counts 3 A and 1 F; remaining 6 choose among B,C,D (3). |

## Homework 2 | Probability

| Q | Menu path | Cue / rule |
|---|---|---|
| 1. Translate event statements | `ENC > CH2 > SETS & EVENTS > ENGLISH ► SETS` | Only A = A∩B'∩C'; exactly one = union of the three only-regions. |
| 2. Union + conditionals | `CALC > PROB > 1` | A=.55, B=.35, union=.70; unknowns=(-)1. Intersection=A+B-union; P(A\|B)=intersection/B. |
| 3. Graduate/faculty 2×2 | `CALC > PROB > 2` | Rows grad/faculty, cols female/male. Enter grad-female=40, row totals 70/50, female=65, N=120; rest=(-)1. |
| 4. Journal acceptance | `CALC > PROB > 3` | Priors .5,.3,.2; accept rates .15,.25,.10. Bayes posterior = prior×rate / total. |
| 5. Die selects an urn | `CALC > PROB > 3` | Cases A/B: priors 1/3,2/3; red likelihoods 3/7,5/7. Use total probability + Bayes. |
| 6. Spam + urgent | `CALC > PROB > 3` | Cases spam/not: priors .6,.4; urgent likelihoods .4,.05. |
| 7. Weekend only / none | `CALC > PROB > 5 > 3` | A=Digital, B=Print, C=Weekend. Enter pairs, triple, N=1000. C-only=C-AC-BC+ABC; none=N-(A+B+C-AB-AC-BC+ABC). |

## Homework 3 | Random Variables

| Q | Menu path | Cue / rule |
|---|---|---|
| 1. Maximum of two balls | `CALC > RV > 2 > MAXIMUM > WITHOUT` | N=5, k=2. p(z)=(z-1)/C(5,2); F(z)=C(z,2)/C(5,2). Sketch spikes + right-continuous steps. |
| 2. Two-interval PDF to CDF | `CALC > RV > 3 > PDF` | Two pieces: (0,2) and (4,6), each constant 1/4. Integrate each; CDF stays flat on (2,4). |
| 3. Given CDF: interval + tail | `CALC > RV > 3 > CDF` | One piece (-2,2), F(x)=1/2+x/4. Use F(b)-F(a) and 1-F(a). |
| 4. Train polynomial PDF | `CALC > RV > 3 > PDF` | One piece (-4,4): c0=3/16, c2=-3/256. Integrate intervals; P(X=-1)=0. |
| 5. Normalize cy², then CDF | `CALC > RV > 3 > PDF` | Piece (0,3): UNKNOWN c=YES, c2=1. c=1/9, F(y)=y³/27; tail=1-F(2). |
| 6. Exponential CDF to PDF | `ENC > CH3 > CONTINUOUS RVs > PDF ◄► CDF; CALC > RV > 4` | F=1-e^(-2x), x>0. Symbolically f=F'=2e^(-2x); tail P(X>1)=e^(-2). Use [0,50] for numeric check. |

## Core rules

- Counting: ordered picks use `nPr`; unordered picks use `nCr`. Distinct labeled groups of sizes n_i use `n! / product(n_i!)`.
- Probability: `P(A union B)=P(A)+P(B)-P(A and B)`; Bayes = prior × likelihood / total evidence.
- Discrete RV: `F(x)=sum_{t<=x} p(t)`. Continuous RV: `P(a<X<b)=F(b)-F(a)`, `f=F'`, and `P(X=a)=0`.
- Freund Chapter 3 joint distributions: `CALC > RV > 6` opens `JOINT X,Y`. Choose `DISCRETE PMF` for a joint table or `CONTINUOUS PDF` for a density on a rectangular support. The tool checks joint CDFs, marginals, conditionals, and independence. This extends beyond the assigned STA 431 Homework 1-3 questions.

Source mapping: STA431_631_Homework_1.pdf, STA431_631_Homework_2.pdf, STA431_631_Homework_3.pdf (common and STA 431-only questions).
