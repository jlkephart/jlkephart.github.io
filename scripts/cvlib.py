"""Shared rules for reading _data/cv.yml. Used by prepare_pdf.py, build_pages.py and validate_cv.py.

Trainee authors. An author is a trainee on a paper when EITHER
  (a) they are listed in the entry's `mentees` field, OR
  (b) they match someone in any "Mentoring: ..." section (same first initial, and the author's
      surname is the person's last name or the first part of a compound surname) whose
      mentoring years cover the paper: publication year within [start, end + 1] (submission
      precedes publication). For manuscripts under review (no year), the mentoring period
      must include the current year or have ended last year, so these underlines can change
      at New Year with no edit to cv.yml.
`not_mentees: "Surname I"` on an entry suppresses a wrong automatic match there.
"""
import datetime
import re
import unicodedata

PI = "Kephart JL"  # the CV owner as written in author lists (bold in both outputs)
THIS_YEAR = datetime.date.today().year

# Markers shared with pdf_templates/classic/: keep in sync with the template comments there.
SUBLINE = " ¶ "          # separates lines inside one date-left entry (OneLineEntry.j2.typ)
RIGHT = " ¦ "            # separates left and right-aligned text in a grant row (OneLineEntry.j2.typ)
LABEL_GRANT = "GRANT"    # OneLineEntry label for the three-row grant layout
LABEL_SUBHEAD = "SUBHEAD"  # OneLineEntry label for an italic sub-heading
GROUP_START, GROUP_NEXT = " ⟫ ", " › "  # section-title markers read by SectionBeginning.j2.typ
MARKERS = (SUBLINE.strip(), RIGHT.strip(), GROUP_START.strip(), GROUP_NEXT.strip())


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[\s\-]+", " ", s).strip()


def plain_author(a):
    """'**Kephart JL**\\*' -> 'Kephart JL'."""
    return a.replace("**", "").replace("\\*", "").replace("*", "").strip()


def has_star(a):
    """True when an author string carries the co-first/co-senior marker (* or \\*), not **bold**."""
    return "*" in a.replace("**", "")


def person_name(entry):
    """'Hanna Jardel, PhD, Assistant Professor (X)' -> 'Hanna Jardel'. Credentials always follow a
    comma, so a middle initial with a period ('Juan C. Figueroa') is kept."""
    return entry["name"].split(",", 1)[0].strip()


def year_range(date):
    """'2021-present' -> (2021, 9999); '2022, 2024' -> (2022, 2024); '2019' -> (2019, 2019).
    Returns (None, None) when there is no year. 'Present' is matched in any case."""
    date = str(date or "")
    yrs = [int(y) for y in re.findall(r"\d{4}", date)]
    if not yrs:
        return None, None
    return yrs[0], (9999 if "present" in date.lower() else yrs[-1])


def is_current(date):
    return "present" in str(date or "").lower()


def mentored_people(sections):
    """[(normalized full name, start year, end year)] from every Mentoring section."""
    people = []
    for sec, entries in sections.items():
        if not sec.startswith("Mentoring"):
            continue
        for e in entries:
            start, end = year_range(e.get("date"))
            if start is not None:
                people.append((norm(person_name(e)), start, end))
    return people


def _is_mentored(author, year, people):
    m = re.match(r"^(.*\S)\s+([A-Z][A-Za-z\-]{0,3})$", plain_author(author))
    if not m:
        return False
    sur, ini = norm(m.group(1)), m.group(2)[0].lower()
    for full, start, end in people:
        rest = full.split(" ", 1)[1] if " " in full else ""  # everything after the first name
        if full[0] == ini and (full.endswith(" " + sur) or (" " + sur + " ") in (" " + rest + " ")):
            if year is None and end >= THIS_YEAR - 1:
                return True
            if year is not None and start <= year <= end + 1:
                return True
    return False


def split_names(field):
    return {m.strip() for m in (field or "").split(";") if m.strip()}


def trainees(pub, people):
    """Set of plain author names to mark as trainees on this publication."""
    date = str(pub.get("date", ""))
    year = int(date) if date.isdigit() else None
    auto = {plain_author(a) for a in pub["authors"] if _is_mentored(a, year, people)}
    return (split_names(pub.get("mentees")) | auto) - split_names(pub.get("not_mentees"))


def split_course(name):
    """'Healthy Housing & Built Environment, EOH 642 (3 credits)'
       -> ('Healthy Housing & Built Environment', 'EOH 642', '3 credits').
    The middle part can be a course number, 'Independent Study' or 'Summer Institute'.
    Names without that shape return (name, '', '')."""
    m = re.match(r"^(.*), ([^,()]+) \(([^()]+)\)$", name)
    return m.groups() if m else (name, "", "")


def is_course_code(kind):
    return bool(re.fullmatch(r"[A-Z]{2,4} \d{3}", kind)) or kind == "Independent Study"
