"""Check _data/cv.yml before building, so data mistakes fail with a clear message instead of a
crash or a silently wrong CV. Run: python scripts/validate_cv.py  (exit code 1 on errors).

Checks: required and allowed fields per section, date formats, author names in
`mentees`/`not_mentees`, separator characters reserved for the PDF build, Typst markup in the
data, and that sections of the same "Group: ..." are next to each other.
"""
import re
import sys
from pathlib import Path

import yaml

from cvlib import MARKERS, plain_author, split_names

ROOT = Path(__file__).resolve().parent.parent

LIST_DATE = r"\d{4}(-(\d{4}|[Pp]resent))?(, \d{4}(-(\d{4}|[Pp]resent))?)*"
GRANT_DATE = r"\d{2}/\d{2}/\d{4}-\d{2}/\d{2}/\d{4}|" + LIST_DATE

PUB = {"required": {"title", "authors", "journal"},
       "allowed": {"title", "authors", "journal", "date", "doi", "summary", "mentees", "not_mentees"}}
RULES = {  # section name (exact or prefix) -> fields; first match wins
    "Education": {"required": {"institution", "degree", "end_date"},
                  "allowed": {"institution", "area", "degree", "end_date", "highlights"}},
    "Professional Experience": {"required": {"position", "company", "start_date"},
                                "allowed": {"position", "company", "start_date", "end_date"}},
    "Peer-Reviewed Publications": {**PUB, "required": PUB["required"] | {"date"}},
    "Manuscripts Under Review": PUB,
    "Active Grants": {"required": {"name", "date", "funder", "investigators"},
                      "allowed": {"name", "date", "funder", "investigators", "total_costs"}},
    "Completed Grants": {"required": {"name", "date", "funder", "investigators"},
                         "allowed": {"name", "date", "funder", "investigators", "total_costs"}},
    "Briefs and Outreach": {"required": {"bullet"}, "allowed": {"bullet"}},
    "Media and Research Dissemination": {"required": {"name", "date", "outlet"},
                                         "allowed": {"name", "date", "outlet", "note", "day", "url"}},
    "Mentoring": {"required": {"name", "date"},
                  "allowed": {"name", "date", "fellowship", "program", "with", "affiliation", "note",
                              "thesis", "position", "award", "lab_role"}},
    "Teaching": {"required": {"name", "date", "institution"}, "allowed": {"name", "date", "institution"}},
    "Skills and Certifications": {"required": {"name"}, "allowed": {"name", "date", "group"}},
    "": {"required": {"name", "date"}, "allowed": {"name", "date", "group", "institution"}},  # other lists; keep last
}


def rule_for(section):
    return next(r for key, r in RULES.items() if section == key or section.startswith(key))


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def main():
    S = yaml.safe_load((ROOT / "_data" / "cv.yml").read_text(encoding="utf-8"))["cv"]["sections"]
    errors, warnings = [], []
    groups_seen, prev_group = set(), None
    for sec, entries in S.items():
        group = sec.split(": ", 1)[0] if ": " in sec else None
        if group and group != prev_group and group in groups_seen:
            errors.append(f"[{sec}] sections of group '{group}' are not next to each other in cv.yml")
        if group:
            groups_seen.add(group)
        prev_group = group
        if not isinstance(entries, list) or not entries:
            errors.append(f"[{sec}] must be a non-empty list")
            continue
        rule = rule_for(sec)
        for i, e in enumerate(entries, 1):
            where = f"[{sec} #{i}]"
            if isinstance(e, str):  # plain-text entry (e.g. the journal reviewer list)
                continue
            label = str(e.get("name") or e.get("title") or e.get("position") or e.get("institution") or "")[:50]
            where += f" {label!r}"
            missing = rule["required"] - set(e)
            if missing:
                errors.append(f"{where}: missing {', '.join(sorted(missing))}")
            unknown = set(e) - rule["allowed"]
            if unknown:
                errors.append(f"{where}: unknown field(s) {', '.join(sorted(unknown))}")
            if "date" in e and e["date"] not in (None, ""):
                pattern = GRANT_DATE if sec.endswith("Grants") else LIST_DATE
                if not re.fullmatch(pattern, str(e["date"])):
                    errors.append(f"{where}: date {e['date']!r} is not like 2024, 2024-2026, 2024-present"
                                  + (" or MM/DD/YYYY-MM/DD/YYYY" if sec.endswith("Grants") else ""))
                elif "Present" in str(e["date"]):
                    warnings.append(f"{where}: write 'present' in lower case for consistency")
            if "authors" in e:
                if not isinstance(e["authors"], list):
                    errors.append(f"{where}: authors must be a list")
                else:
                    plain = {plain_author(a) for a in e["authors"]}
                    for field in ("mentees", "not_mentees"):
                        for name in split_names(e.get(field)) - plain:
                            errors.append(f"{where}: {field} name '{name}' is not one of the authors")
            for s in strings(e):
                for m in MARKERS:
                    if m in s:
                        errors.append(f"{where}: contains '{m}', which the PDF build reserves")
                if re.search(r"#(underline|strong|emph|block|grid)\b", s):
                    errors.append(f"{where}: contains Typst markup; keep layout out of cv.yml")
    for w in warnings:
        print("warning:", w)
    for err in errors:
        print("ERROR:", err)
    print(f"validate_cv: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
