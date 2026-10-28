#!/usr/bin/env python3
"""
content.py - encyclopedia / hint content (JSON) -> TI-BASIC menu+pager program.

JSON schema (one file per program, e.g. content/STAE1.json):
{
  "program": "STAE1",                  # program name, A-Z0-9, <=8 chars
  "title":   "CH1 COUNTING",           # top menu title (<=22 chars)
  "sections": [                        # 1..6 sections
    {
      "menu":  "BASICS",               # item text in the top menu (<=18 chars); ignored if only 1 section
      "title": "COUNTING BASICS",      # title of this section's topic menu (<=22 chars)
      "topics": [                      # 1..6 topics per section
        {
          "menu":  "MULT PRINCIPLE",   # item text in the section menu (<=18 chars)
          "title": "MULT PRINCIPLE",   # page header (<=20 chars); page counter "2/3" is added
          "pages": [                   # 1..6 pages
            ["line 1", "... up to 9 lines, each <=26 display chars ..."]
          ]
        }
      ]
    }
  ]
}
If there is exactly ONE section, the top menu lists its topics directly.

Screen layout per page: row 1 = header (title + "p/n"), rows 2-10 = the page's lines.
Keys while reading: ENTER/any key = next page (last page -> back to menu),
LEFT = previous page (page 1 -> menu), CLEAR = back to menu.

Allowed characters: see ALLOWED below. Write pi as "π" (mapped to the Greek glyph).
Square root only as "√(". No colon, no double quote, no "->", "<=", ">=", "!=", "|L", "|E", "|>" ("=>" is fine).

CLI:
  python content.py check   content/STAE1.json [...]    # validate
  python content.py gen     content/STAE1.json src/     # write src/STAE1.txt (validates first)
  python content.py preview content/STAE1.json          # print every screen as a 26x10 box
  python content.py stats   content/*.json              # sizes / page counts
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tibuild  # noqa: E402

W, H = 26, 10
MAX_MENU_ITEM, MAX_MENU_TITLE, MAX_PAGE_TITLE = 18, 22, 20
MAX_SECTIONS, MAX_TOPICS, MAX_PAGES, MAX_LINES = 6, 6, 6, 9

ALLOWED = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 "
    "()[]{},.!?+-*/=<>^|'%&#@;_"
    "≤≥≠²³πΣσμλθ√∫₀₁₂₃₄₅₆₇₈₉►◄↑↓×…αβγδΔερτχΦΩ"
)
BANNED_SEQS = ["->", "<=", ">=", "!=", "|L", "|E", "|>"]

LABEL_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789θ"


def two_char_labels():
    for a in LABEL_CHARS[:26]:          # first char a letter
        for b in LABEL_CHARS:
            yield a + b


def check_text(where, s, maxlen, errs):
    if not isinstance(s, str):
        errs.append(f"{where}: not a string")
        return
    if len(s) > maxlen:
        errs.append(f"{where}: {len(s)} chars > {maxlen}: {s!r}")
    bad = sorted({c for c in s if c not in ALLOWED})
    if bad:
        errs.append(f"{where}: disallowed chars {bad} in {s!r}")
    for seq in BANNED_SEQS:
        if seq in s:
            errs.append(f"{where}: banned sequence {seq!r} in {s!r}")
    if "√" in s and s.count("√") != s.count("√("):
        errs.append(f"{where}: '√' must be written '√(' in {s!r}")


def validate(doc):
    errs = []
    prog = doc.get("program", "")
    if not tibuild.NAME_RE.match(prog or ""):
        errs.append(f"program: invalid name {prog!r}")
    check_text("title", doc.get("title", ""), MAX_MENU_TITLE, errs)
    secs = doc.get("sections", [])
    if not (1 <= len(secs) <= MAX_SECTIONS):
        errs.append(f"sections: need 1..{MAX_SECTIONS}, got {len(secs)}")
    for i, sec in enumerate(secs, 1):
        w = f"section {i}"
        if len(secs) > 1:
            check_text(f"{w}.menu", sec.get("menu", ""), MAX_MENU_ITEM, errs)
        check_text(f"{w}.title", sec.get("title", ""), MAX_MENU_TITLE, errs)
        tops = sec.get("topics", [])
        if not (1 <= len(tops) <= MAX_TOPICS):
            errs.append(f"{w}: need 1..{MAX_TOPICS} topics, got {len(tops)}")
        for j, top in enumerate(tops, 1):
            wt = f"{w} topic {j} ({top.get('menu', '?')})"
            check_text(f"{wt}.menu", top.get("menu", ""), MAX_MENU_ITEM, errs)
            check_text(f"{wt}.title", top.get("title", ""), MAX_PAGE_TITLE, errs)
            pages = top.get("pages", [])
            if not (1 <= len(pages) <= MAX_PAGES):
                errs.append(f"{wt}: need 1..{MAX_PAGES} pages, got {len(pages)}")
            for k, page in enumerate(pages, 1):
                if not isinstance(page, list) or not (1 <= len(page) <= MAX_LINES):
                    errs.append(f"{wt} page {k}: need 1..{MAX_LINES} lines")
                    continue
                for li, line in enumerate(page, 1):
                    check_text(f"{wt} p{k} L{li}", line, W, errs)
    if errs:
        return errs
    # tokenization round-trip of generated program
    src = generate(doc)
    for m in tibuild.lint_program(prog, tibuild.clean_source(src)):
        if m.startswith("ERROR"):
            errs.append(m)
    return errs


def ti_str(s):
    return s.replace("π", "|π")


def header(title, p, n):
    ind = f"{p}/{n}" if n > 1 else ""
    return title.ljust(W - len(ind)) + ind if ind else title


def generate(doc):
    labels = two_char_labels()
    L = []
    secs = doc["sections"]
    multi = len(secs) > 1
    L.append(f"// {doc['program']} - generated by tools/content.py from content JSON; do not hand-edit")
    L.append("Lbl M")
    # assign page labels first
    plan = []
    for si, sec in enumerate(secs, 1):
        tplan = []
        for top in sec["topics"]:
            tplan.append([next(labels) for _ in top["pages"]])
        plan.append(tplan)
    if multi:
        items = ",".join(f"\"{ti_str(s['menu'])}\",{si}" for si, s in enumerate(secs, 1))
        L.append(f"Menu(\"{ti_str(doc['title'])}\",{items},\"BACK\",Z)")
    for si, sec in enumerate(secs, 1):
        menu_lbl = str(si) if multi else "M"
        back = "M" if multi else "Z"
        title = sec["title"] if multi else doc["title"]
        if multi:
            L.append(f"Lbl {si}")
        items = ",".join(f"\"{ti_str(t['menu'])}\",{plan[si-1][ti][0]}"
                         for ti, t in enumerate(sec["topics"]))
        L.append(f"Menu(\"{ti_str(title)}\",{items},\"BACK\",{back})")
        for ti, top in enumerate(sec["topics"]):
            labs = plan[si - 1][ti]
            n = len(top["pages"])
            for pi, page in enumerate(top["pages"]):
                L.append(f"Lbl {labs[pi]}")
                L.append("ClrHome")
                L.append(f"Output(1,1,\"{ti_str(header(top['title'], pi + 1, n))}\")")
                for r, line in enumerate(page, 2):
                    if line.strip():
                        L.append(f"Output({r},1,\"{ti_str(line)}\")")
                L.append("Repeat Ans:getKey:End")
                L.append("Ans→K")
                L.append(f"If K=45:Goto {menu_lbl}")
                L.append(f"If K=24:Goto {labs[pi-1] if pi > 0 else menu_lbl}")
                if pi == n - 1:
                    L.append(f"Goto {menu_lbl}")
    L.append("Lbl Z")
    L.append("ClrHome")
    L.append("Return")
    return "\n".join(L) + "\n"


def preview(doc):
    out = []
    for sec in doc["sections"]:
        out.append(f"=== SECTION: {sec.get('menu', '')} / {sec['title']}")
        for top in sec["topics"]:
            n = len(top["pages"])
            for pi, page in enumerate(top["pages"]):
                rows = [header(top["title"], pi + 1, n)] + page
                rows += [""] * (H - len(rows))
                out.append("+" + "-" * W + "+   [" + top["menu"] + "]")
                for r in rows:
                    out.append("|" + r.ljust(W) + "|")
                out.append("+" + "-" * W + "+")
    return "\n".join(out)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, paths = argv[1], argv[2:]
    if cmd == "check":
        bad = 0
        for p in paths:
            errs = validate(load(p))
            for e in errs:
                print(f"{p}: {e}")
            print(f"{p}: {'OK' if not errs else str(len(errs)) + ' errors'}")
            bad += bool(errs)
        return 1 if bad else 0
    if cmd == "gen":
        src, outdir = paths[0], paths[1]
        doc = load(src)
        errs = validate(doc)
        if errs:
            for e in errs:
                print(e)
            return 1
        dest = os.path.join(outdir, doc["program"] + ".txt")
        with open(dest, "w", encoding="utf-8") as f:
            f.write(generate(doc))
        size = len(tibuild.tokenize(tibuild.clean_source(generate(doc))))
        print(f"wrote {dest} ({size} bytes tokenized)")
        return 0
    if cmd == "preview":
        for p in paths:
            print(preview(load(p)))
        return 0
    if cmd == "stats":
        for p in paths:
            d = load(p)
            np = sum(len(t["pages"]) for s in d["sections"] for t in s["topics"])
            nt = sum(len(s["topics"]) for s in d["sections"])
            size = len(tibuild.tokenize(tibuild.clean_source(generate(d))))
            print(f"{p}: {len(d['sections'])} sections, {nt} topics, {np} pages, {size} bytes")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
