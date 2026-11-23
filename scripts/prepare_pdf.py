"""Write _build/cv.yml: a copy of _data/cv.yml with PDF-only markup, for RenderCV.

- Underlines trainee authors (same rules as the website: scripts/trainees.py) using
  Typst's #underline[...], which RenderCV passes through unescaped.
- Adds a one-line key explaining * and underlines as a temporary section named
  KEY_SECTION; scripts/finalize_pdf.py later moves it under the Peer-Reviewed
  Publications heading (RenderCV won't mix text into a publication section).

_data/cv.yml stays plain; never edit _build/ by hand.
"""
from pathlib import Path

import yaml

from trainees import mentored_people, plain_author, trainees

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
BUILD.mkdir(exist_ok=True)

PUB_SECTIONS = ["Peer-Reviewed Publications", "Manuscripts Under Review"]
KEY_SECTION = "PUBLICATIONKEYPLACEHOLDER"  # must match scripts/finalize_pdf.py

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

# Key above the publication lists (RenderCV sections hold one entry type, so it gets its own heading).
sections = {}
for k, v in S.items():
    if k == PUB_SECTIONS[0]:
        sections[KEY_SECTION] = [
            "\\* co-first or co-senior authorship; #underline[underlined] authors were mentored "
            "scholars at the time of first submission."
        ]
    sections[k] = v
data["cv"]["sections"] = sections

(BUILD / "cv.yml").write_text(
    yaml.dump(data, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")
print(f"prepare_pdf: underlined {n} trainee author entries -> _build/cv.yml")
