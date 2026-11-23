"""Who counts as a trainee author on a publication. Shared by the website and the PDF CV.

An author is a trainee on a paper when EITHER
  (a) they are listed in the entry's `mentees` field, OR
  (b) they match someone in any "Mentoring: ..." CV section (same surname, same first
      initial) whose mentoring years cover the paper: publication year within
      [start, end + 1] (submission precedes publication), or, for manuscripts under
      review, a mentoring period that includes the current year or ended last year.
`not_mentees: "Surname I"` on an entry suppresses a wrong automatic match there.
"""
import datetime
import re
import unicodedata

THIS_YEAR = datetime.date.today().year


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[\s\-]+", " ", s).strip()


def plain_author(a):
    """'**Kephart JL**\\*' -> 'Kephart JL'."""
    return a.replace("**", "").replace("\\*", "").replace("*", "").strip()


def mentored_people(sections):
    """[(normalized full name, start year, end year)] from every Mentoring section."""
    people = []
    for sec, entries in sections.items():
        if not sec.startswith("Mentoring"):
            continue
        for e in entries:
            date = str(e.get("date", ""))
            yrs = re.findall(r"\d{4}", date)
            if not yrs:
                continue
            end = 9999 if "present" in date else int(yrs[-1])
            full = re.split(r"[.,]", e["name"], maxsplit=1)[0]
            people.append((norm(full), int(yrs[0]), end))
    return people


def _is_mentored(author, year, people):
    m = re.match(r"^(.*\S)\s+([A-Z][A-Za-z\-]{0,3})$", plain_author(author))
    if not m:
        return False
    sur, ini = norm(m.group(1)), m.group(2)[0].lower()
    for full, start, end in people:
        # Surname matches the end of the name, or the first part of a compound surname
        # (e.g. "Malpartida G" for "Gary Malpartida Guzman"), never the first name.
        given_rest = full.split(" ", 1)[1] if " " in full else ""
        if (full.endswith(" " + sur) or given_rest.startswith(sur + " ")
                or (" " + sur + " ") in (" " + given_rest)) and full[0] == ini:
            if year is None and end >= THIS_YEAR - 1:
                return True
            if year is not None and start <= year <= end + 1:
                return True
    return False


def _split(field):
    return {m.strip() for m in (field or "").split(";") if m.strip()}


def trainees(pub, people):
    """Set of plain author names to mark as trainees on this publication."""
    date = str(pub.get("date", ""))
    year = int(date) if date.isdigit() else None
    auto = {plain_author(a) for a in pub["authors"] if _is_mentored(a, year, people)}
    return (_split(pub.get("mentees")) | auto) - _split(pub.get("not_mentees"))
