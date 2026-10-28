#!/usr/bin/env python3
"""Build the one-page STA 431 exam menu card (PDF plus editable Markdown).

Run from any directory with the bundled Python runtime or an environment with
reportlab installed: python dev/tools/make_menu_card.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "EXAM_MENU_CARD.pdf"
MD = ROOT / "EXAM_MENU_CARD.md"
FONT_DIRS = [
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/"
    "libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/"
    "fonts/truetype",
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/local/share/fonts/dejavu"),
]
FONT_DIR = next(
    (p for p in FONT_DIRS if (p / "DejaVuSansCondensed.ttf").exists()
     and (p / "DejaVuSansCondensed-Bold.ttf").exists()),
    None,
)
if FONT_DIR is None:
    raise RuntimeError("DejaVu Sans Condensed fonts are required to build the menu card")
pdfmetrics.registerFont(TTFont("DVC", str(FONT_DIR / "DejaVuSansCondensed.ttf")))
pdfmetrics.registerFont(TTFont("DVC-Bold", str(FONT_DIR / "DejaVuSansCondensed-Bold.ttf")))


@dataclass(frozen=True)
class Row:
    number: str
    title: str
    path: str
    note: str


SECTIONS = [
    (
        "HOMEWORK 1 | COUNTING",
        colors.HexColor("#0B776C"),
        colors.HexColor("#EFF9F6"),
        [
            Row("1", "Pascal identity + story proof", "ENC > CH1 > BINOMIAL COEFFS > PASCAL IDENTITY", "C(n,r) = C(n-1,r-1)+C(n-1,r). Algebra: common denominator. Story: fix one item."),
            Row("2", "Two binomial-sum proofs", "ENC > CH1 > BINOMIAL COEFFS > SUM IDENTITIES", "Differentiate (1+x)^n at x=1; integrate it from 0 to 1. Results: n·2^(n-1); (2^(n+1)-1)/(n+1)."),
            Row("3", "x³y²z² term coefficient", "CALC > COUNT > 6", "Enter (2,3), (-1,2), (3,2). Rule: 7!/(3!2!2!) × 2³(-1)²3²."),
            Row("4", "PROBABILITY arrangements", "CALC > COUNT > 2", "Enter word; choose LETTER BLOCK B for adjacent B's. Total 11!/(2!2!); block 10!/2!."),
            Row("5", "Three distinct committees", "CALC > COUNT > 3 > 1", "Sizes 3,4,5; LABELED=1. Rule: 12!/(3!4!5!)."),
            Row("6", "T/F exam: 15 right, 2 hard", "CALC > COUNT > 4", "A=5 hard, B=15 other, K=15; hard min=max 2. C(5,2)C(15,13)."),
            Row("7", "Delegation: at least 2 each", "CALC > COUNT > 4", "A=8 math, B=6 stats, K=5; min 2 each. Sum C(8,i)C(6,5-i), i=2,3."),
            Row("8", "Grades: exact A and F", "CALC > COUNT > 3 > 2", "N=10; exact counts 3 A and 1 F; remaining 6 choose among B,C,D (3)."),
        ],
    ),
    (
        "HOMEWORK 2 | PROBABILITY",
        colors.HexColor("#B76A20"),
        colors.HexColor("#FEF7ED"),
        [
            Row("1", "Translate event statements", "ENC > CH2 > SETS & EVENTS > ENGLISH ► SETS", "Only A = A∩B'∩C'; exactly one = union of the three only-regions."),
            Row("2", "Union + conditionals", "CALC > PROB > 1", "A=.55, B=.35, union=.70; unknowns=(-)1. Intersection=A+B-union; P(A|B)=intersection/B."),
            Row("3", "Graduate/faculty 2×2", "CALC > PROB > 2", "Rows grad/faculty, cols female/male. Enter grad-female=40, row totals 70/50, female=65, N=120; rest=(-)1."),
            Row("4", "Journal acceptance", "CALC > PROB > 3", "Priors .5,.3,.2; accept rates .15,.25,.10. Bayes posterior = prior×rate / total."),
            Row("5", "Die selects an urn", "CALC > PROB > 3", "Cases A/B: priors 1/3,2/3; red likelihoods 3/7,5/7. Use total probability + Bayes."),
            Row("6", "Spam + urgent", "CALC > PROB > 3", "Cases spam/not: priors .6,.4; urgent likelihoods .4,.05."),
            Row("7", "Weekend only / none", "CALC > PROB > 5 > 3", "A=Digital, B=Print, C=Weekend. Enter pairs, triple, N=1000. C-only=C-AC-BC+ABC; none=N-(A+B+C-AB-AC-BC+ABC)."),
        ],
    ),
    (
        "HOMEWORK 3 | RANDOM VARIABLES",
        colors.HexColor("#61569A"),
        colors.HexColor("#F5F2FC"),
        [
            Row("1", "Maximum of two balls", "CALC > RV > 2 > MAXIMUM > WITHOUT", "N=5, k=2. p(z)=(z-1)/C(5,2); F(z)=C(z,2)/C(5,2). Sketch spikes + right-continuous steps."),
            Row("2", "Two-interval PDF to CDF", "CALC > RV > 3 > PDF", "Two pieces: (0,2) and (4,6), each constant 1/4. Integrate each; CDF stays flat on (2,4)."),
            Row("3", "Given CDF: interval + tail", "CALC > RV > 3 > CDF", "One piece (-2,2), F(x)=1/2+x/4. Use F(b)-F(a) and 1-F(a)."),
            Row("4", "Train polynomial PDF", "CALC > RV > 3 > PDF", "One piece (-4,4): c0=3/16, c2=-3/256. Integrate intervals; P(X=-1)=0."),
            Row("5", "Normalize cy², then CDF", "CALC > RV > 3 > PDF", "Piece (0,3): UNKNOWN c=YES, c2=1. c=1/9, F(y)=y³/27; tail=1-F(2)."),
            Row("6", "Exponential CDF to PDF", "ENC > CH3 > CONTINUOUS RVs > PDF ◄► CDF; CALC > RV > 4", "F=1-e^(-2x), x>0. Symbolically f=F'=2e^(-2x); tail P(X>1)=e^(-2). Use [0,50] for numeric check."),
        ],
    ),
]


def write_markdown() -> None:
    lines = [
        "# STA 431 Midterm Menu Card",
        "",
        "**TI-84 Plus CE | Freund Chapters 1-3 | Homework 1-3**",
        "",
        "Start with `PRGM` > `STA431`. `CALC` means **CALCULATORS**, `ENC` means **ENCYCLOPEDIA**, and `RV` means **RANDOM VARIABLES**. Use the calculator's `(-)` key to enter `-1` for an unknown value. Press `ENTER` to advance on encyclopedia pages; use `BACK` to exit calculator tools.",
        "",
        "Menu numbers in the paths below refer to options on each screen. The app checks computations and supplies method cues; write the algebraic proofs and graph sketches in your own solution.",
        "",
    ]
    for heading, _, _, rows in SECTIONS:
        lines += [f"## {heading.title()}", "", "| Q | Menu path | Cue / rule |", "|---|---|---|"]
        for row in rows:
            safe_title = row.title.replace("|", r"\|")
            safe_path = row.path.replace("|", r"\|")
            safe_note = row.note.replace("|", r"\|")
            lines.append(f"| {row.number}. {safe_title} | `{safe_path}` | {safe_note} |")
        lines.append("")
    lines += [
        "## Core rules",
        "",
        "- Counting: ordered picks use `nPr`; unordered picks use `nCr`. Distinct labeled groups of sizes n_i use `n! / product(n_i!)`.",
        "- Probability: `P(A union B)=P(A)+P(B)-P(A and B)`; Bayes = prior × likelihood / total evidence.",
        "- Discrete RV: `F(x)=sum_{t<=x} p(t)`. Continuous RV: `P(a<X<b)=F(b)-F(a)`, `f=F'`, and `P(X=a)=0`.",
        "- Freund Chapter 3 joint distributions: `CALC > RV > 6` opens `JOINT X,Y`. Choose `DISCRETE PMF` for a joint table or `CONTINUOUS PDF` for a density on a rectangular support. The tool checks joint CDFs, marginals, conditionals, and independence. This extends beyond the assigned STA 431 Homework 1-3 questions.",
        "",
        "Source mapping: STA431_631_Homework_1.pdf, STA431_631_Homework_2.pdf, STA431_631_Homework_3.pdf (common and STA 431-only questions).",
        "",
    ]
    MD.write_text("\n".join(lines), encoding="utf-8")


def make_style(name: str, size: float, leading: float, color: colors.Color, bold: bool = False) -> ParagraphStyle:
    return ParagraphStyle(
        name,
        fontName="DVC-Bold" if bold else "DVC",
        fontSize=size,
        leading=leading,
        textColor=color,
        alignment=TA_LEFT,
        spaceAfter=0,
        spaceBefore=0,
    )


TITLE = make_style("title", 9.05, 10.8, colors.HexColor("#182638"), True)
PATH = make_style("path", 7.85, 9.6, colors.HexColor("#305C89"), True)
NOTE = make_style("note", 7.95, 10.0, colors.HexColor("#344354"))


def draw_para(c: canvas.Canvas, txt: str, style: ParagraphStyle, x: float, top: float, width: float) -> float:
    para = Paragraph(escape(txt), style)
    _, height = para.wrap(width, 500)
    para.drawOn(c, x, top - height)
    return height


def write_pdf() -> None:
    width, height = landscape(letter)
    c = canvas.Canvas(str(PDF), pagesize=(width, height))
    c.setTitle("STA 431 Midterm Menu Card")
    c.setAuthor("STA 431 TI-84 Helper")

    navy = colors.HexColor("#182638")
    c.setFillColor(navy)
    c.rect(0, height - 57, width, 57, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("DVC-Bold", 17)
    c.drawString(27, height - 31, "STA 431  /  MIDTERM MENU CARD")
    c.setFont("DVC", 8.5)
    c.setFillColor(colors.HexColor("#DCE9F3"))
    c.drawString(28, height - 45, "TI-84 Plus CE  |  Freund Chapters 1-3  |  Homework 1-3")

    c.setFillColor(colors.HexColor("#ECF2F7"))
    c.roundRect(27, height - 87, width - 54, 23, 5, fill=1, stroke=0)
    c.setFillColor(navy)
    c.setFont("DVC-Bold", 7.8)
    c.drawString(37, height - 77, "START  PRGM > STA431")
    c.setFont("DVC", 7.4)
    c.drawString(166, height - 77, "CALC = CALCULATORS   |   ENC = ENCYCLOPEDIA   |   RV = RANDOM VARIABLES   |   (-)1 = unknown")

    margin = 27
    gap = 10
    col_w = (width - 2 * margin - 2 * gap) / 3
    top = height - 99
    bottom = 49
    for idx, (heading, accent, tint, rows) in enumerate(SECTIONS):
        x = margin + idx * (col_w + gap)
        c.setFillColor(tint)
        c.roundRect(x, bottom, col_w, top - bottom, 7, fill=1, stroke=0)
        c.setFillColor(accent)
        c.roundRect(x, top - 26, col_w, 26, 7, fill=1, stroke=0)
        c.rect(x, top - 26, col_w, 7, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("DVC-Bold", 9)
        c.drawString(x + 11, top - 17, heading)
        y = top - 33
        inner_x = x + 10
        inner_w = col_w - 20
        for row in rows:
            title_h = draw_para(c, f"Q{row.number}  {row.title}", TITLE, inner_x, y, inner_w)
            y -= title_h + 1
            path_h = draw_para(c, row.path, PATH, inner_x, y, inner_w)
            y -= path_h + 1
            note_h = draw_para(c, row.note, NOTE, inner_x, y, inner_w)
            y -= note_h + 8
            if row is not rows[-1]:
                c.setStrokeColor(colors.HexColor("#CDD9E1"))
                c.setLineWidth(.45)
                c.line(inner_x, y + 3.5, inner_x + inner_w, y + 3.5)
        if y < bottom + 6:
            raise RuntimeError(f"{heading} overflows panel by {bottom + 6 - y:.1f} pt")

    c.setFillColor(colors.HexColor("#E7EDF3"))
    c.rect(0, 0, width, 43, fill=1, stroke=0)
    c.setFillColor(navy)
    c.setFont("DVC-Bold", 7.1)
    c.drawString(28, 29, "FAST RULES")
    c.setFont("DVC", 7.05)
    c.drawString(91, 29, "Bayes = prior × likelihood / evidence   |   continuous P(a<X<b)=F(b)-F(a), f=F', P(X=a)=0")
    c.setFont("DVC-Bold", 7.1)
    c.drawString(28, 17, "CH3 JOINT")
    c.setFont("DVC", 7.05)
    c.drawString(91, 17, "CALC > RV > 6 JOINT X,Y: marginals, conditionals, independence. Show proofs and sketches by hand.")
    c.setFont("DVC", 6.4)
    c.drawRightString(width - 27, 5, "Homework 1-3 mapping / 1 page")
    c.save()


if __name__ == "__main__":
    write_markdown()
    write_pdf()
    print(PDF)
    print(MD)
