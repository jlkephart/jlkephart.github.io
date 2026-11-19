"""Generate website page fragments from _data/cv.yml.

Runs as a Quarto pre-render step. Writes Markdown into _generated/, which the
.qmd pages pull in with {{< include >}}. Never edit _generated/ by hand.
"""
import html
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_generated"
OUT.mkdir(exist_ok=True)

cv = yaml.safe_load((ROOT / "_data" / "cv.yml").read_text(encoding="utf-8"))["cv"]
S = cv["sections"]


def write(name, text):
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def esc(s):
    return html.escape(str(s), quote=False)


# ---------------------------------------------------------------- publications
def author_html(authors, mentees):
    mentees = {m.strip() for m in (mentees or "").split(";") if m.strip()}
    out = []
    for a in authors:
        star = "*" in a.replace("**", "")  # ignore the **bold** markup
        plain = a.replace("**", "").replace("\\*", "").replace("*", "").strip()
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
            f'<div class="pub-authors">{author_html(p["authors"], p.get("mentees"))}</div>'
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
    # Dollar amounts (the `highlights` field) stay in the CV PDF only, never on the website.
    return (f'<div class="grant"><div class="grant-title">{esc(g["name"])}</div>'
            f'<div class="grant-meta">{esc(g.get("summary", ""))} {esc(g.get("date", ""))}</div></div>')

write("active_grants.md", "\n".join(grant_html(g) for g in S.get("Active Grants", [])))

# ---------------------------------------------------------------- people
LAB_SECTIONS = {  # sections where the PI is the primary mentor -> lab members
    "Mentoring: Postdoctoral Fellow": "Postdoctoral fellow",
    "Mentoring: Doctoral Primary Advisor": "PhD student",
    "Mentoring: Graduate Research Fellows or Research Assistants": "Graduate research assistant",
    "Mentoring: Advisees (Master)": "MPH advisee",
    "Mentoring: Master’s Applied Practical Experience (APE) Preceptor/Supervisor": "MPH practicum student",
    "Mentoring: Undergraduate Research Assistants": "Undergraduate research assistant",
}


def parse_person(entry):
    text = entry["name"]
    name = re.split(r"[.,]", text, maxsplit=1)[0].strip()
    prog = re.search(r"Program:\s*([^.]+?)(?:,\s*Dornsife.*|,\s*Drexel University.*)?\.?\s*(?:Current|$)", text)
    now = re.search(r"Current position:\s*(.+?)\.?$", text)
    return name, (prog.group(1).strip() if prog else ""), (now.group(1).strip() if now else "")


current, alumni, seen = [], [], set()
for sec, role in LAB_SECTIONS.items():
    for e in S.get(sec, []):
        name, prog, now = parse_person(e)
        if name in seen:
            continue
        seen.add(name)
        d = str(e.get("date", ""))
        rec = {"name": name, "role": role, "program": prog, "now": now, "date": d}
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
