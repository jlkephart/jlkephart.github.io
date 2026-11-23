"""Write _build/cv.yml: a copy of _data/cv.yml with PDF-only layout, for RenderCV.

_data/cv.yml holds content only; all PDF formatting is added here:
- Publications and manuscripts under review become numbered one-line citations (RenderCV
  NumberedEntry), with trainee authors underlined (rules in scripts/cvlib.py, shared with the
  website) using Typst's #underline[...], which RenderCV passes through unescaped.
- Most other sections become date-on-the-left plain-text entries (RenderCV OneLineEntry, drawn by
  pdf_templates/classic/entries/OneLineEntry.j2.typ):
  - Education ('PhD/2019  Institution (Field)'), Experience ('2022-present  Position, Organization');
  - Mentoring, with indented lines for thesis, current position and awards;
  - grants in three rows (funder | dates, investigators | total costs, title);
  - Teaching, grouped under institution sub-headings with repeat offerings merged onto one line;
  - the list sections in DATE_LEFT, with optional `group`/`institution` sub-headings.
- "Group: Sub" section names become a group heading printed once plus sub-headings
  (pdf_templates/classic/SectionBeginning.j2.typ); see PDF_GROUPS for sections grouped only here.
- pdf_templates/<theme>/ is copied next to the output; RenderCV looks for <theme>/<template>
  beside its input file before using its built-in templates.

Run validate_cv.py first to catch data errors. Never edit _build/ by hand; it is rebuilt each run.
"""
import os
import re
import shutil
import stat
from pathlib import Path

import yaml

from cvlib import (GROUP_NEXT, GROUP_START, LABEL_GRANT, LABEL_SUBHEAD, PI, RIGHT, SUBLINE,
                   has_star, is_course_code, mentored_people, plain_author, split_course, trainees)

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"


def _clear_readonly(func, path, _exc):  # Windows: copied folders can be read-only
    os.chmod(path, stat.S_IWRITE)
    func(path)


if BUILD.exists():  # start clean: no stale templates or outputs from earlier runs
    shutil.rmtree(BUILD, onexc=_clear_readonly)
BUILD.mkdir()

PUB_SECTIONS = ["Peer-Reviewed Publications", "Manuscripts Under Review"]
GRANT_SECTIONS = ["Active Grants", "Completed Grants"]
DATE_LEFT = ("Editorial and Review Activities", "Presentations", "Honors and Awards",
             "Professional Activities", "Media and Research Dissemination", "Academic Service",
             "Community Service", "Skills and Certifications")
PDF_GROUPS = {  # sections the website reads by these exact names, grouped in the PDF only
    "Peer-Reviewed Publications": "Publications: Peer-Reviewed Publications",
    "Manuscripts Under Review": "Publications: Manuscripts Under Review",
    "Briefs and Outreach": "Publications: Briefs and Outreach",
    "Media and Research Dissemination": "Publications: Media and Research Dissemination",
    "Active Grants": "Research Grant Participation: Active",
    "Completed Grants": "Research Grant Participation: Completed",
}

data = yaml.safe_load((ROOT / "_data" / "cv.yml").read_text(encoding="utf-8"))
S = data["cv"]["sections"]


def sentence(s):
    s = str(s).strip()
    return s if s[-1:] in ".?!" else s + "."


# ---------------------------------------------------------------- publications
def cite_author(a, trainee):
    """'**Kephart JL**' stays bold; trainees are underlined; any star becomes an escaped \\*."""
    name = plain_author(a)
    shown = f"**{name}**" if name == PI else (f"#underline[{name}]" if trainee else name)
    return shown + ("\\*" if has_star(a) else "")


def citation(p, marked):
    """'Authors. Title. Journal. Year. doi:...' as one line."""
    authors = ", ".join(cite_author(a, plain_author(a) in marked) for a in p["authors"])
    parts = [sentence(authors), sentence(p["title"])]
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


people = mentored_people(S)
n_underlined = 0
for sec in PUB_SECTIONS:
    if sec in S:
        cites = []
        for p in S[sec]:
            marked = trainees(p, people) - {PI}
            n_underlined += sum(plain_author(a) in marked for a in p["authors"])
            cites.append({"number": citation(p, marked)})  # newest first; each section restarts at 1
        S[sec] = cites


# ---------------------------------------------------------------- mentoring
def mentee(e):
    """'Name (fellowship). Program: X. With Y. Affiliation. Note.' then indented lines for
    thesis title, current position and awards."""
    head = e["name"] + (f" ({e['fellowship']})" if e.get("fellowship") else "")
    parts = [sentence(head)]
    if e.get("program"):
        parts.append(sentence(f"Program: {e['program']}"))
    if e.get("with"):
        parts.append(sentence(f"With {e['with']}"))
    for key in ("affiliation", "note"):
        if e.get(key):
            parts.append(sentence(e[key]))
    lines = [" ".join(parts)]
    if e.get("thesis"):
        lines.append(f"Thesis title: {sentence(e['thesis'])}")
    if e.get("position"):
        lines.append(f"Current position: {sentence(e['position'])}")
    if e.get("award"):
        lines.append(sentence(e["award"]))
    return {"label": str(e.get("date", "")), "details": SUBLINE.join(lines)}


for sec in [k for k in S if k.startswith("Mentoring")]:
    S[sec] = [mentee(e) for e in S[sec]]


# ---------------------------------------------------------------- grants
def grant(g):
    rows = [g["funder"] + RIGHT + str(g.get("date", "")),
            g["investigators"] + (RIGHT + f"Total costs: {g['total_costs']}" if g.get("total_costs") else ""),
            g["name"]]
    return {"label": LABEL_GRANT, "details": SUBLINE.join(rows)}


for sec in GRANT_SECTIONS:
    if sec in S:
        S[sec] = [grant(g) for g in S[sec]]


# ---------------------------------------------------------------- date-left lists
def year_span(dates):
    """[2026, 2023, '2021-2022'] -> '2021-2023, 2026'. Ranges are expanded before merging; if any
    date is open-ended ('2024-present') or not year-based, the dates are listed as written."""
    years = set()
    for d in dates:
        m = re.fullmatch(r"(\d{4})(?:-(\d{4}))?", str(d).strip())
        if not m:
            return ", ".join(dict.fromkeys(str(x) for x in dates))
        years.update(range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1))
    ys = sorted(years)
    runs, start = [], ys[0]
    for a, b in zip(ys, ys[1:] + [None]):
        if b != a + 1:
            runs.append(str(start) if start == a else f"{start}-{a}")
            start = b
    return ", ".join(runs)


def course_text(name):
    """'Title, EOH 642 (3 credits)' -> 'EOH 642: Title (3 credits)'; also 'Independent Study'.
    Other shapes (e.g. 'Title, Summer Institute (15 hrs)') are printed as written."""
    title, kind, detail = split_course(name)
    return f"{kind}: {title} ({detail})" if is_course_code(kind) else name


def media_text(e):
    """'**Outlet**. Headline. Note. Mon DD. URL' from the structured media fields."""
    parts = [f"**{e['outlet']}**.", sentence(e["name"])]
    if e.get("note"):
        parts.append(sentence(e["note"]))
    if e.get("day"):
        parts.append(sentence(e["day"]))
    if e.get("url"):
        parts.append(e["url"])
    return " ".join(parts)


def date_left(entries, fmt=lambda e: e["name"], merge=False):
    """An optional italic sub-heading per `group` (or `institution`), then date-on-the-left
    entries. merge=True puts repeats of the same item (same name) on one line."""
    if not all(isinstance(e, dict) for e in entries):
        return entries  # plain-text sections (e.g. the journal reviewer list) stay as they are
    groups = {}
    for e in entries:
        key = e.get("group") or e.get("institution") or ""
        groups.setdefault(key, {}).setdefault(e["name"] if merge else id(e), []).append(e)
    out = []
    for heading, items in groups.items():
        if heading:
            out.append({"label": LABEL_SUBHEAD, "details": heading})
        for es in items.values():
            date = year_span([e.get("date", "") for e in es]) if merge else str(es[0].get("date", ""))
            out.append({"label": date, "details": fmt(es[0])})
    return out


for sec in [k for k in S if k.startswith("Teaching")]:
    S[sec] = date_left(S[sec], lambda e: sentence(course_text(e["name"])), merge=True)

if "Education" in S:
    S["Education"] = [{
        "label": f"{e['degree']}/{e.get('end_date', '')}",
        "details": SUBLINE.join([e["institution"] + (f" ({e['area']})" if e.get("area") else "")]
                                + list(e.get("highlights") or [])),
    } for e in S["Education"]]

if "Professional Experience" in S:
    S["Professional Experience"] = [
        {"label": f"{e.get('start_date', '')}-{e.get('end_date', '')}".strip("-"),
         "details": f"{e['position']}, {e['company']}"} for e in S["Professional Experience"]]

for sec in [k for k in S if k.startswith(DATE_LEFT)]:
    S[sec] = date_left(S[sec], media_text if sec == "Media and Research Dissemination" else (lambda e: e["name"]))

# ---------------------------------------------------------------- two heading levels
# RenderCV has one heading level, so cv.yml names grouped sections "Group: Sub". The first section
# of each run of a group becomes "Group ⟫ Sub" and the rest "Group › Sub"; SectionBeginning.j2.typ
# prints the large group heading once, then a smaller sub-heading. Keep a group's sections
# adjacent in cv.yml, or its heading prints again.
renamed, prev = {}, None
for key, entries in S.items():
    group, sep, sub = PDF_GROUPS.get(key, key).partition(": ")
    if sep:
        key = group + (GROUP_NEXT if group == prev else GROUP_START) + sub
        prev = group
    else:
        key, prev = group, None
    renamed[key] = entries
data["cv"]["sections"] = renamed

(BUILD / "cv.yml").write_text(
    yaml.dump(data, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")

for theme_dir in (ROOT / "pdf_templates").iterdir():
    if theme_dir.is_dir():
        shutil.copytree(theme_dir, BUILD / theme_dir.name)

print(f"prepare_pdf: underlined {n_underlined} trainee author entries -> _build/cv.yml (+ template overrides)")
