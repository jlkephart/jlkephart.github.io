"""Convert KephartJ CV .docx into a RenderCV-style YAML (one-time migration)."""
import re, sys, docx, yaml
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.table import Table

SRC, OUT = sys.argv[1], sys.argv[2]
d = docx.Document(SRC)

def clean(s):
    s = s.replace(" ", " ").replace("\t", " ")
    return re.sub(r"\s+", " ", s).strip()

def para_text(p):
    """Return (text, underlined_spans) for a paragraph."""
    text, under = "", []
    for r in p.runs:
        t = r.text.replace("\n", " ")
        if r.underline and t.strip():
            under.append(t.strip())
        text += t
    return text, under

# ---- walk the document into rows: list of (cells, cell_paragraph_lists)
rows = []
for el in d.element.body.iterchildren():
    if el.tag == qn("w:tbl"):
        for r in Table(el, d).rows:
            seen, cells = set(), []
            for c in r.cells:
                if id(c._tc) in seen:
                    continue
                seen.add(id(c._tc))
                cells.append(c)
            vals = [clean(c.text) for c in cells]
            keep = [(v, c) for v, c in zip(vals, cells) if v]
            if keep:
                rows.append(keep)

# ---- group into section -> subsection -> rows
SECTIONS = ["EDUCATION", "ACADEMIC & PROFESSIONAL EXPERIENCE", "PROFESSIONAL ACTIVITIES",
            "EDITORIAL ACTIVITIES", "HONORS AND AWARDS", "PUBLICATIONS",
            "BRIEFS AND OTHER OUTREACH MATERIAL", "RESEARCH GRANT PARTICIPATION", "TEACHING",
            "MENTORING", "PRESENTATIONS", "OTHER ACADEMIC SERVICE",
            "EXTERNAL/COMMUNITY SERVICE", "SKILLS & CERTIFICATIONS"]
tree, sec, sub = {}, None, None
for row in rows:
    first = row[0][0]
    if len(row) == 1 and first in SECTIONS:
        sec, sub = first, None
        tree[sec] = {None: []}
        continue
    if sec is None:
        continue
    if len(row) == 1 and not re.match(r"^\d{4}", first) and sec not in (
            "PUBLICATIONS", "BRIEFS AND OTHER OUTREACH MATERIAL", "RESEARCH GRANT PARTICIPATION") \
            and len(first) < 120:
        sub = first
        tree[sec].setdefault(sub, [])
        continue
    if sec in ("PUBLICATIONS", "RESEARCH GRANT PARTICIPATION") and len(row) == 1 and len(first) < 60 \
            and not first.startswith(("William", "Drexel", "Wellcome", "National", "Lacuna", "Cotswold", "Johns")):
        sub = first
        tree[sec].setdefault(sub, [])
        continue
    tree[sec].setdefault(sub, []).append(row)

def date_text(row):
    if len(row) >= 2:
        return row[0][0], " ".join(v for v, _ in row[1:])
    m = re.match(r"^(\d{4}(?:[-–]\d{2,4}|-[Pp]resent|-present)?)\s+(.*)$", row[0][0])
    return (m.group(1), m.group(2)) if m else ("", row[0][0])

def norm_date(s):
    s = s.replace("–", "-").replace("Present", "present").strip()
    return s

def normal_entries(rs):
    out = []
    for r in rs:
        dt, txt = date_text(r)
        e = {"name": txt}
        if dt:
            e["date"] = norm_date(dt)
        out.append(e)
    return out

cv_sections = {}

# Education
edu = []
for r in tree["EDUCATION"][None]:
    yd, rest = r[0][0], r[1][0]
    year, degree = yd.split(None, 1)
    cell = r[1][1]
    lines = [clean(p.text) for p in cell.paragraphs if clean(p.text)]
    inst = lines[0]
    honors = None
    if ", summa cum laude" in inst:
        inst, honors = inst.replace(", summa cum laude", ""), "Summa cum laude"
    e = {"institution": inst, "area": lines[1] if len(lines) > 1 else "", "degree": degree.strip(),
         "end_date": int(year)}
    if honors:
        e["highlights"] = [honors]
    edu.append(e)
cv_sections["Education"] = edu

# Experience
exp = []
for r in tree["ACADEMIC & PROFESSIONAL EXPERIENCE"][None]:
    dt = norm_date(r[0][0])
    lines = [clean(x).rstrip(",") for x in r[1][1].text.split(chr(10)) if clean(x)]
    pos, org = lines[0], ", ".join(lines[1:]) if len(lines) > 1 else ""
    s, _, e_ = dt.partition("-")
    e = {"position": pos, "company": org, "start_date": int(s)}
    e["end_date"] = (e_ if e_ == "present" else int(e_)) if e_ else int(s)
    exp.append(e)
cv_sections["Professional Experience"] = exp

# Honors
cv_sections["Honors and Awards"] = normal_entries(tree["HONORS AND AWARDS"][None])

# ---- publications
AUTH_END = re.compile(r"((?:\b[A-Z][A-Za-z]?[A-Z]{0,2}|Group|Project|al|Investigators)\*?\.)\s+(?=[A-Z0-9“\"‘'¿])")

def split_cite(c):
    m = AUTH_END.search(c)
    authors, rest = c[:m.end(1)].rstrip("."), c[m.end():]
    return authors, rest

def fix_authors(a):
    out = []
    for x in a:
        if out and re.fullmatch(r"[A-Z]{1,3}", x) and " " not in out[-1]:
            out[-1] += " " + x          # "Jimenez-Ortiz, CM" typo in source
        else:
            out.append(x)
    return out

def parse_pub(text, under, status):
    notes = []
    authors, rest = split_cite(text)
    tm = re.match(r"^(.*?[.?])\s+(.*)$", rest)
    title, rest2 = (tm.group(1).rstrip("."), tm.group(2)) if tm else (rest, "")
    pub = {"title": title,
           "authors": [("**Kephart JL**" + ("\\*" if "*" in a else "")) if a.replace("*", "").strip() == "Kephart JL" else a
                       for a in [x.strip() for x in authors.split(",")] if a]}
    doi = re.search(r"doi:\s*(10\.\S+?)\.?(?:\s|$)", rest2)
    if doi:
        pub["doi"] = doi.group(1).rstrip(".")
    ym = re.search(r"\((?:In press, )?(\d{4})\)", rest2)
    if status == "under_review":
        pub["journal"] = "Under review"
    else:
        jm = re.match(r"^(.*?)(?:\.|\s)\s*\(", rest2) or re.match(r"^(.*?)\.", rest2)
        pub["journal"] = jm.group(1).strip().rstrip(".") if jm else rest2
        if ym:
            pub["date"] = ym.group(1)
        if "In press" in rest2:
            pub["journal"] += " (in press)"
    mentees = sorted({u.strip(" ,.*").replace("Jimenez-Ortiz, CM", "Jimenez-Ortiz CM") for u in under if re.search(r"[A-Z]{1,3}$", u.strip(" ,.*"))})
    if mentees:
        pub["mentees"] = "; ".join(mentees)
    pub["authors"] = fix_authors(pub["authors"])
    if any("*" in a for a in pub["authors"]):
        pub["co_first_or_senior"] = "yes"
    return pub

def pub_groups(cell):
    """Split a cell into entries on blank lines (blank paragraphs OR double line breaks)."""
    lines, cur_t, cur_u = [], "", []
    for p in cell.paragraphs:
        for r in p.runs:
            parts = r.text.split(chr(10))
            for i, part in enumerate(parts):
                if i > 0:
                    lines.append((cur_t, cur_u)); cur_t, cur_u = "", []
                cur_t += part
                if r.underline and part.strip():
                    cur_u.append(part.strip())
        lines.append((cur_t, cur_u)); cur_t, cur_u = "", []
    groups, cur = [], []
    for t, u in lines:
        if not clean(t):
            if cur:
                groups.append(cur); cur = []
            continue
        cur.append((clean(t), u))
    if cur:
        groups.append(cur)
    return groups

pubs = {"under_review": [], "published": []}
for subname, rs in tree["PUBLICATIONS"].items():
    status = "under_review" if subname and "review" in subname.lower() else "published"
    for r in rs:
        for v, cell in r:
            if len(v) < 200:
                continue
            for g in pub_groups(cell):
                main = [x for x in g if not x[0].startswith("-")]
                notes = [x[0].lstrip("- ").rstrip(", ") for x in g if x[0].startswith("-")]
                text = clean(" ".join(x[0] for x in main))
                under = [u for x in main for u in x[1]]
                p = parse_pub(text, under, status)
                if notes:
                    p["summary"] = "; ".join(notes)
                pubs[status].append(p)
cv_sections["Peer-Reviewed Publications"] = pubs["published"]
cv_sections["Manuscripts Under Review"] = pubs["under_review"]

briefs = []
for r in tree["BRIEFS AND OTHER OUTREACH MATERIAL"][None]:
    for v, cell in r:
        for g in pub_groups(cell):
            briefs.append({"bullet": clean(" ".join(x[0] for x in g))})
cv_sections["Briefs and Outreach"] = briefs

# ---- grants
grants = {"Active Grants": [], "Completed Grants": []}
for subname, rs in tree["RESEARCH GRANT PARTICIPATION"].items():
    key = "Active Grants" if subname and "Active" in subname else "Completed Grants"
    for r in rs:
        cell = r[-1][1]
        lines = [clean(p.text) for p in cell.paragraphs if clean(p.text)]
        if not lines:
            continue
        if len(r) == 2 and len(lines) <= 2:   # William Penn row split across two rows
            pass
        joined = " | ".join(lines)
        grants[key].append(joined)
# re-parse each grant from the joined text
def parse_grant(j):
    funder_dates = re.match(r"^(.*?)\s{0,}((?:\d{2}/\d{2}[/-]\d{2,4}|\d{4})\s*[-–]\s*(?:\d{2}/\d{2}/\d{2,4}|\d{4})|\b\d{4}\b)", j)
    out = {}
    m = re.search(r"((?:\d{2}/\d{2}[/-]\d{2,4})\s*[-–]\s*(?:\d{2}/\d{2}/\d{2,4})|\b\d{4}\s*[-–]\s*\d{4}\b|\b(?:19|20)\d{2}\b)", j)
    funder = clean(j[:m.start()]) if m else ""
    out["funder"] = funder.strip(" |")
    out["date"] = m.group(1).replace("–", "-") if m else ""
    rest = j[m.end():] if m else j
    cost = re.search(r"Total costs:\s*(\$[\d,]+)", rest)
    if cost:
        out["total_costs"] = cost.group(1)
        rest = rest.replace(cost.group(0), "")
    parts = [clean(x) for x in rest.split("|") if clean(x)]
    role = parts[0] if parts else ""
    title = " ".join(parts[1:]) if len(parts) > 1 else ""
    out["role"] = role.rstrip(".")
    out["title"] = title
    return out

raw_rows = []
for subname, rs in tree["RESEARCH GRANT PARTICIPATION"].items():
    key = "Active Grants" if subname and "Active" in subname else "Completed Grants"
    buf = []
    for r in rs:
        txt = " | ".join(clean(p.text) for v, c in r for p in c.paragraphs if clean(p.text))
        buf.append(txt)
    # merge the split William Penn row (funder line with no 'Total costs' followed by continuation)
    merged = []
    for t in buf:
        if merged and "Total costs" not in merged[-1] and "Kirschstein" not in merged[-1] \
                and "Pre-doctoral Fellow" not in merged[-1]:
            merged[-1] += " | " + t
        else:
            merged.append(t)
    for t in merged:
        g = parse_grant(t)
        if not g["title"] and ") " in g["role"]:
            g["role"], g["title"] = g["role"].split(") ", 1)
            g["role"] += ")"
        nm = (g["title"] or g["funder"]).strip()
        if nm.startswith("(") and nm.endswith(")"):
            nm = nm[1:-1]
        g["date"] = g["date"].replace("12/01-2022", "12/01/2022").replace("09/23/23", "09/23/2023")
        e = {"name": nm, "date": g["date"],
             "summary": f'{g["funder"]}. {g["role"]}.'.replace("..", ".")}
        if g.get("total_costs"):
            e["highlights"] = [f'Total costs: {g["total_costs"]}']
        grants[key].append(e)
    grants[key] = [x for x in grants[key] if isinstance(x, dict)]
cv_sections.update(grants)

# ---- generic sections (date | text rows, possibly with subsections)
def add_generic(secname, label):
    for subname, rs in tree[secname].items():
        if not rs:
            continue
        title = label if subname is None else f"{label}: {subname}"
        cv_sections[title] = normal_entries(rs)

add_generic("PROFESSIONAL ACTIVITIES", "Professional Activities")
add_generic("EDITORIAL ACTIVITIES", "Editorial and Review Activities")
add_generic("TEACHING", "Teaching")
add_generic("MENTORING", "Mentoring")
add_generic("PRESENTATIONS", "Presentations")
add_generic("OTHER ACADEMIC SERVICE", "Academic Service")
add_generic("EXTERNAL/COMMUNITY SERVICE", "Community Service")
add_generic("SKILLS & CERTIFICATIONS", "Skills and Certifications")

ren = {"Teaching: Dornsife School of Public Health, Drexel University, Philadelphia, PA": "Teaching: Instructor of Record (Drexel University)",
       "Teaching: Johns Hopkins Bloomberg School of Public Health, Baltimore, MD": "Teaching: Teaching Assistantships (Johns Hopkins)",
       "Presentations: Select Media Appearances and Research Dissemination": "Media and Research Dissemination"}
cv_sections = {ren.get(k, k): v for k, v in cv_sections.items()}

# journal reviewer list -> single text entry
for k in list(cv_sections):
    if k.endswith("Journal Reviewer"):
        jr = tree["EDITORIAL ACTIVITIES"]["Peer Review Activities, Journal Reviewer"]
        names = [clean(x) for r in jr for _, c in r for x in c.text.split(chr(10)) if clean(x)]
        cv_sections[k] = [", ".join(names)]

def year_ints(o):
    if isinstance(o, dict):
        return {k: (int(v) if k == "date" and isinstance(v, str) and re.fullmatch(r"\d{4}", v) else year_ints(v))
                for k, v in o.items()}
    if isinstance(o, list):
        return [year_ints(x) for x in o]
    return o
cv_sections = year_ints(cv_sections)

cv = {
    "cv": {
        "name": "Josiah L. Kephart",
        "headline": "PhD, MPH. Assistant Professor, Environmental and Occupational Health, "
                    "Dornsife School of Public Health, Drexel University",
        "location": "Philadelphia, PA",
        "email": "jlk465@drexel.edu",
        "sections": cv_sections,
    },
    "design": {"theme": "classic"},
}

class Dumper(yaml.SafeDumper):
    pass
def str_rep(dumper, s):
    return dumper.represent_scalar("tag:yaml.org,2002:str", s)
Dumper.add_representer(str, str_rep)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("# Single source of truth for the CV and the lab website.\n"
            "# Migrated from KephartJ_CV_2026-09.docx on 2026-11-19. Edit this file, not the .docx.\n"
            "# Publication extras used by the website: `mentees` (underlined trainee authors),\n"
            "# `co_first_or_senior`. Names in **bold** are Kephart JL.\n\n")
    yaml.dump(cv, f, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=110)

# report
for k, v in cv_sections.items():
    print(f"{len(v):3d}  {k}")
