"""Write _build/cv.yml: a copy of _data/cv.yml with PDF-only markup, for RenderCV.

- Underlines trainee authors (same rules as the website: scripts/trainees.py) using
  Typst's #underline[...], which RenderCV passes through unescaped.
- Turns Peer-Reviewed Publications and Manuscripts Under Review into numbered,
  one-line citations (RenderCV NumberedEntry). The website still uses the structured fields.
- Turns Mentoring entries' structured fields into plain-text, date-on-the-left entries
  (RenderCV OneLineEntry + our OneLineEntry.j2.typ override), like the Bilal CV format.
- Lays out grants the same way: funder and dates, investigators and total costs, title.
- Groups Teaching entries under institution sub-headings, merging repeat offerings' years,
  and lays out the other list sections (see DATE_LEFT), plus Education and Experience,
  date-left, with `group` or `institution` sub-headings.
- Copies pdf_templates/<theme>/ next to it. RenderCV looks for <theme>/<template> beside
  the input file before using its built-in templates; our SectionBeginning override
  prints the publication key under the Peer-Reviewed Publications heading.

_data/cv.yml stays plain; never edit _build/ by hand.
"""
import re
import shutil
from pathlib import Path

import yaml

from trainees import mentored_people, plain_author, trainees

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
BUILD.mkdir(exist_ok=True)

PUB_SECTIONS = ["Peer-Reviewed Publications", "Manuscripts Under Review"]

data = yaml.safe_load((ROOT / "_data" / "cv.yml").read_text(encoding="utf-8"))
S = data["cv"]["sections"]
people = mentored_people(S)

n = 0
for sec in PUB_SECTIONS:
    for pub in S.get(sec, []):
        marked = trainees(pub, people)
        new = []
        for a in pub["authors"]:
            name = plain_author(a)
            if name in marked and name != "Kephart JL":
                star = "*" in a.replace("**", "")
                a = f"#underline[{name}]" + ("\\*" if star else "")
                n += 1
            new.append(a)
        pub["authors"] = new


def cite_author(a):
    """Keep bold/underline markup; normalize any co-first/co-senior star to an escaped \\*."""
    star = "*" in a.replace("**", "").replace("\\*", "") or "\\*" in a
    a = a.replace("\\*", "")
    a = a[:-1] if a.endswith("*") and not a.endswith("**") else a
    return a.strip() + ("\\*" if star else "")


def sentence(s):
    s = str(s).strip()
    return s if s[-1:] in ".?!" else s + "."


def citation(p):
    """'Authors. Title. Journal. Year. doi:...' as one line, like a standard academic CV."""
    parts = [sentence(", ".join(cite_author(a) for a in p["authors"])), sentence(p["title"])]
    venue = str(p.get("journal", "")).strip()
    if p.get("date"):
        venue = f"{venue}. {p['date']}" if venue else str(p["date"])
    if venue:
        parts.append(sentence(venue))
    if p.get("doi"):
        parts.append(f"doi:[{p['doi']}](https://doi.org/{p['doi']})")
    if p.get("summary"):
        parts.append(sentence(p["summary"]))
    return " ".join(parts)


SUBLINE = " ¶ "  # must match pdf_templates/classic/OneLineEntry.j2.typ


def mentee(e):
    """Bilal-style mentee entry: 'Name (fellowship). Program: X. With Y. Affiliation.' then
    indented lines for thesis title, current position and awards."""
    head = e["name"] + (f" ({e['fellowship']})" if e.get("fellowship") else "")
    parts = [sentence(head)]
    if e.get("program"):
        parts.append(sentence(f"Program: {e['program']}"))
    if e.get("with"):
        parts.append(sentence(f"With {e['with']}"))
    if e.get("affiliation"):
        parts.append(sentence(e["affiliation"]))
    lines = [" ".join(parts)]
    if e.get("thesis"):
        lines.append(f"Thesis title: {sentence(e['thesis'])}")
    if e.get("position"):
        lines.append(f"Current position: {sentence(e['position'])}")
    if e.get("award"):
        lines.append(sentence(e["award"]))
    return {"label": str(e.get("date", "")), "details": SUBLINE.join(lines)}


# Mentoring sections print like Bilal's CV: date on the left, plain text, indented sub-lines.
# They use RenderCV's one-line entry type (unused elsewhere) with our own template.
for sec in [k for k in S if k.startswith("Mentoring")]:
    S[sec] = [mentee(e) for e in S[sec]]

GRANT_SECTIONS = ["Active Grants", "Completed Grants"]
RIGHT = " ¦ "  # right-aligned cell separator; must match OneLineEntry.j2.typ


def grant(g):
    """Bilal-style grant: funder | dates, investigators | total costs, then the title."""
    rows = [g["funder"] + RIGHT + str(g.get("date", "")),
            g["investigators"] + (RIGHT + f"Total costs: {g['total_costs']}" if g.get("total_costs") else ""),
            g["name"]]
    return {"label": "GRANT", "details": SUBLINE.join(rows)}


for sec in GRANT_SECTIONS:
    if sec in S:
        S[sec] = [grant(g) for g in S[sec]]


def year_span(years):
    """[2026, 2023, 2024] -> '2023-2024, 2026' (Bilal style: repeat offerings on one line)."""
    ys = sorted({int(y) for y in years if str(y).isdigit()})
    if not ys:
        return ", ".join(str(y) for y in years)
    runs, start = [], ys[0]
    for a, b in zip(ys, ys[1:] + [None]):
        if b != a + 1:
            runs.append(str(start) if start == a else f"{start}-{a}")
            start = b
    return ", ".join(runs)


def course_text(name):
    """'Healthy Housing & Built Environment, EOH 642 (3 credits)' -> 'EOH 642: Healthy Housing ... (3 credits)'."""
    m = re.match(r"^(.*), ([A-Z]{2,4} \d{3}) \((.+)\)$", name)
    return f"{m.group(2)}: {m.group(1)} ({m.group(3)})" if m else name


def date_left(entries, fmt=lambda n: n, merge=False):
    """Bilal-style list: an optional sub-heading per `group` (or `institution`), then
    date-on-the-left plain entries. merge=True puts repeats of the same item on one line."""
    if not all(isinstance(e, dict) for e in entries):
        return entries  # plain-text sections (e.g. the journal reviewer list) stay as they are
    groups = {}
    for e in entries:
        key = e.get("group") or e.get("institution") or ""
        groups.setdefault(key, {}).setdefault(e["name"] if merge else id(e), []).append(e)
    out = []
    for heading, items in groups.items():
        if heading:
            out.append({"label": "SUBHEAD", "details": heading})
        for es in items.values():
            date = year_span([e.get("date", "") for e in es]) if merge else str(es[0].get("date", ""))
            out.append({"label": date, "details": fmt(es[0]["name"])})
    return out


# Teaching: institution sub-headings, repeat offerings merged onto one line.
for sec in [k for k in S if k.startswith("Teaching")]:
    S[sec] = date_left(S[sec], lambda n: sentence(course_text(n)), merge=True)

# Education and experience, Bilal style: 'PhD/2019  Institution (Field)' and
# '2022-present  Position, Organization'; education highlights become indented lines.
if "Education" in S:
    S["Education"] = [{
        "label": f"{e['degree']}/{e.get('end_date', '')}",
        "details": SUBLINE.join([e["institution"] + (f" ({e['area']})" if e.get("area") else "")]
                                + list(e.get("highlights") or [])),
    } for e in S["Education"]]
EXP = "Academic and Professional Experience"
if EXP in S:
    S[EXP] = [{"label": f"{e.get('start_date', '')}-{e.get('end_date', '')}".strip("-"),
               "details": f"{e['position']}, {e['company']}"} for e in S[EXP]]

# The other list sections use the same date-left layout, with sub-headings from `group`
# (e.g. Intramural/Extramural grant review, Languages/Certifications) or `institution`.
DATE_LEFT = ("Editorial and Review Activities", "Presentations", "Honors and Awards",
             "Professional Activities", "Media and Research Dissemination", "Academic Service",
             "Community Service", "Skills and Certifications")
for sec in [k for k in S if k.startswith(DATE_LEFT)]:
    S[sec] = date_left(S[sec])

# Numbered citation-style entries, newest first (1 = most recent); each section restarts at 1.
for sec in PUB_SECTIONS:
    if sec in S:
        S[sec] = [{"number": citation(p)} for p in S[sec]]

(BUILD / "cv.yml").write_text(
    yaml.dump(data, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")

for theme_dir in (ROOT / "pdf_templates").iterdir():
    if theme_dir.is_dir():
        shutil.copytree(theme_dir, BUILD / theme_dir.name, dirs_exist_ok=True)

print(f"prepare_pdf: underlined {n} trainee author entries -> _build/cv.yml (+ template overrides)")
