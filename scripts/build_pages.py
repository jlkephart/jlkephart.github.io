"""Generate website page fragments from _data/cv.yml.

Runs as a Quarto pre-render step. Writes Markdown into _generated/, which the
.qmd pages pull in with {{< include >}}. Never edit _generated/ by hand.
"""
import html
import re
from pathlib import Path

import yaml

from trainees import mentored_people, plain_author, trainees

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_generated"
OUT.mkdir(exist_ok=True)

cv = yaml.safe_load((ROOT / "_data" / "cv.yml").read_text(encoding="utf-8"))["cv"]
S = cv["sections"]


def write(name, text):
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def esc(s):
    return html.escape(str(s), quote=False)


# ---------------------------------------------------------------- trainees
PEOPLE = mentored_people(S)  # rules live in scripts/trainees.py (shared with the PDF build)


# ---------------------------------------------------------------- publications
def author_html(authors, mentees):
    out = []
    for a in authors:
        star = "*" in a.replace("**", "")  # ignore the **bold** markup
        plain = plain_author(a)
        s = esc(plain)
        if plain == "Kephart JL":
            s = f"<strong>{s}</strong>"
        elif plain in mentees:
            s = f'<span class="mentee">{s}</span>'
        out.append(s + ("<sup>&ast;</sup>" if star else ""))
    return ", ".join(out)


def pub_html(p):
    title = esc(p["title"])
    doi = p.get("doi")
    link = f"https://doi.org/{doi}" if doi else None
    t = f'<a href="{link}">{title}</a>' if link else title
    venue = esc(p.get("journal", ""))
    year = p.get("date", "")
    meta = f"<em>{venue}</em>" + (f" ({year})" if year else "")
    extra = f'<div class="pub-note">{esc(p["summary"])}</div>' if p.get("summary") else ""
    return (f'<div class="pub"><div class="pub-title">{t}</div>'
            f'<div class="pub-authors">{author_html(p["authors"], trainees(p, PEOPLE))}</div>'
            f'<div class="pub-venue">{meta}</div>{extra}</div>')


published = S.get("Peer-Reviewed Publications", [])
review = S.get("Manuscripts Under Review", [])

lines = [f'<p class="pub-legend"><strong>Kephart JL</strong> &middot; '
         f'<span class="mentee">lab trainee</span> &middot; <sup>&ast;</sup> co-first or co-senior author &middot; '
         f'{len(published)} published, {len(review)} under review</p>']
by_year = {}
for p in published:
    by_year.setdefault(str(p.get("date", "Other")), []).append(p)
for y in sorted(by_year, reverse=True):
    lines.append(f"\n## {y}\n")
    lines += [pub_html(p) for p in by_year[y]]
if review:
    lines.append("\n## Under review\n")
    lines += [pub_html(p) for p in review]
write("publications.md", "\n".join(lines))

recent = "\n".join(pub_html(p) for p in published[:5])
write("recent_publications.md", recent)

# ---------------------------------------------------------------- grants
def grant_html(g):
    # Dollar amounts (the `total_costs` field) stay in the CV PDF only, never on the website.
    meta = ". ".join(x for x in (g.get("funder"), g.get("investigators")) if x) + "."
    return (f'<div class="grant"><div class="grant-title">{esc(g["name"])}</div>'
            f'<div class="grant-meta">{esc(meta)} {esc(g.get("date", ""))}</div></div>')

write("active_grants.md", "\n".join(grant_html(g) for g in S.get("Active Grants", [])))

# ---------------------------------------------------------------- people
# Lab members are Mentoring entries with a `lab_role` (people the PI mentors directly).
# Listed in this order of role, then CV order within a role.
LAB_ROLE_ORDER = ["Postdoctoral fellow", "PhD student", "Graduate research assistant",
                  "MPH advisee", "MPH practicum student", "Undergraduate research assistant"]


def parse_person(entry):
    name = re.split(r"[.,]", entry["name"], maxsplit=1)[0].strip()
    prog = re.sub(r",\s*(Dornsife|Drexel University).*$", "", entry.get("program", "")).strip()
    return name, prog, entry.get("position", "")


lab = [e for sec, es in S.items() if sec.startswith("Mentoring") for e in es if e.get("lab_role")]
lab.sort(key=lambda e: LAB_ROLE_ORDER.index(e["lab_role"]) if e["lab_role"] in LAB_ROLE_ORDER
         else len(LAB_ROLE_ORDER))

current, alumni, seen = [], [], set()
for e in lab:
    name, prog, now = parse_person(e)
    if name in seen:
        continue
    seen.add(name)
    d = str(e.get("date", ""))
    rec = {"name": name, "role": e["lab_role"], "program": prog, "now": now, "date": d}
    (current if "present" in d else alumni).append(rec)

cards = []
for p in current:
    sub = esc(p["program"]) if p["program"] else ""
    cards.append(f'<div class="person"><div class="person-name">{esc(p["name"])}</div>'
                 f'<div class="person-role">{esc(p["role"])}</div>'
                 f'<div class="person-sub">{sub}</div></div>')
write("people_current.md", '<div class="people-grid">\n' + "\n".join(cards) + "\n</div>")

al = []
for p in sorted(alumni, key=lambda x: x["date"], reverse=True):
    bits = [p["role"]] + ([p["program"]] if p["program"] else []) + [p["date"]]
    tail = f" &rarr; {esc(p['now'])}" if p["now"] else ""
    al.append(f"- **{esc(p['name'])}**, {esc(', '.join(bits))}{tail}")
write("people_alumni.md", "\n".join(al))

# ---------------------------------------------------------------- teaching
def years_by_item(entries):
    """Collapse repeat offerings: {'Course name': ['2026', '2023']} in first-seen order."""
    out = {}
    for e in entries:
        out.setdefault(e["name"].strip(), []).append(str(e.get("date", "")))
    return out


T_CLASS = "Teaching: Classroom Instruction (Instructor or Course Director)"
T_SHORT = "Teaching: Short Courses (Instructor or Course Director)"
T_GUEST = "Teaching: Guest Lecturing"
T_OTHER = "Teaching: Other Significant Teaching (Informal Talks, Teaching Assistant, Laboratory Instructor)"
TA_SUFFIX = ", Teaching Assistant"


def with_place(e):
    """Entry text plus its institution, without a trailing US 'City, ST' (e.g. ', Philadelphia, PA')."""
    inst = re.sub(r", [^,]+, [A-Z]{2}$", "", e.get("institution", ""))
    return f"{e['name']}, {inst}" if inst else e["name"]


is_drexel = lambda e: e.get("institution", "").startswith("Drexel University")
taught = S.get(T_CLASS, []) + S.get(T_SHORT, [])
courses = years_by_item([e for e in taught if is_drexel(e)])  # the website lists Drexel courses
tl = ["## Courses\n", "*Dornsife School of Public Health, Drexel University*\n"]
for name, yrs in courses.items():
    title, _, detail = name.rpartition(", ") if "(" in name else (name, "", "")
    yrs_s = ", ".join(sorted(set(yrs), reverse=True))
    tl.append(f'<div class="course"><div class="course-title">{esc(title or name)}</div>'
              f'<div class="course-meta">{esc(detail)} &middot; {yrs_s}</div></div>')

other = S.get(T_OTHER, [])
workshops = ([e for e in taught if not is_drexel(e)]  # e.g. conference short courses
             + [e for e in other if not e["name"].endswith(TA_SUFFIX)])
workshops.sort(key=lambda e: str(e.get("date", "")), reverse=True)
if workshops:
    tl.append("\n## Workshops and trainings\n")
    tl += [f"- {esc(with_place(e))} ({e.get('date', '')})" for e in workshops]

lectures = S.get(T_GUEST, [])
if lectures:
    tl.append("\n## Guest lectures\n")
    tl += [f"- {esc(with_place(e))} ({e.get('date', '')})" for e in lectures]

ta = years_by_item([{**e, "name": e["name"][: -len(TA_SUFFIX)]}
                    for e in other if e["name"].endswith(TA_SUFFIX)])
if ta:
    tl.append("\n## Teaching assistantships\n")
    tl.append("*Johns Hopkins Bloomberg School of Public Health*\n")
    tl += [f"- {esc(n)} ({', '.join(y)})" for n, y in ta.items()]
write("teaching.md", "\n".join(tl))

# ---------------------------------------------------------------- media
media = []
for e in S.get("Media and Research Dissemination", []):
    text = e["name"]
    m = re.search(r"(https?://\S+)$", text)
    url = m.group(1) if m else None
    body = text[: m.start()].strip() if m else text
    outlet, _, rest = body.partition(". ")
    headline = rest.split(". ")[0] if rest else ""
    h = f"[{esc(headline)}]({url})" if url and headline else esc(headline)
    media.append(f"- **{esc(outlet)}** ({e.get('date', '')}): {h}")
write("media.md", "\n".join(media))

print(f"build_pages: {len(published)} pubs, {len(review)} under review, "
      f"{len(current)} current members, {len(alumni)} alumni, {len(media)} media items")
