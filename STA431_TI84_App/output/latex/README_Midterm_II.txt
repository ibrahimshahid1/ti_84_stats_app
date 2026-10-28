STA 431 MIDTERM II LATEX SOURCES

Two independent local LaTeX projects:
  STA431_Midterm_II_Guide/main.tex
  STA431_Midterm_II_Notesheet/main.tex

Open either project folder in the Codex LaTeX editor, or compile in its own
folder using: latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
A standard TeX Live distribution supplies the used packages.

The guide has 70 pages, with 70 original practice questions (10 per distinct
exam topic), worked solutions, subsection checkpoints, Homework 4-5 keys,
textbook reading references, and a TI-84 Plus CE command companion.
The repeated expectation topic in the request is merged into one topic.
The guide now includes a calculator-first section and a menu map for the separate STAM2 TI-BASIC package.
The sheet is exactly two US Letter landscape pages, with three columns per
side and approximately 8.3-point body type. Print at actual size as a layout
reference for copying by hand with a 0.3 mm pen. Handwriting size affects fit.

The supplied textbook PDFs and assignment PDFs are not copied into this
archive. Their exact sections/pages are cited in the guide. Practice questions
are original models of homework skills, not predictions of the real exam.
STA 631 extensions and total-expectation/variance supplement are marked.
Native calculator commands were checked against official TI documentation;
the STAM2 programs passed 141 token-stream simulator checks. No physical calculator test or device installation is claimed.

VALIDATION
Both projects compiled using the desktop editor and local pdflatex.
All PDF pages were visually reviewed; no overflow warnings remain.
The practice bank passed 81 SymPy checks and 70 question/answer count checks.
The optional verify_practice.py requires SymPy (pip install sympy).

The separate STA431_Homework_4_5_App_Walkthrough project is19pages and covers all16questions and every subpart. The updated app package now has10programs, including input presets and joint slices.
