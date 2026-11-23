"""Write _build/cv.yml: a copy of _data/cv.yml with PDF-only markup, for RenderCV.

- Underlines trainee authors (same rules as the website: scripts/trainees.py) using
  Typst's #underline[...], which RenderCV passes through unescaped.
- Copies pdf_templates/<theme>/ next to it. RenderCV looks for <theme>/<template> beside
  the input file before using its built-in templates; our SectionBeginning override
  prints the publication key under the Peer-Reviewed Publications heading.

_data/cv.yml stays plain; never edit _build/ by hand.
"""
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

(BUILD / "cv.yml").write_text(
    yaml.dump(data, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")

for theme_dir in (ROOT / "pdf_templates").iterdir():
    if theme_dir.is_dir():
        shutil.copytree(theme_dir, BUILD / theme_dir.name, dirs_exist_ok=True)

print(f"prepare_pdf: underlined {n} trainee author entries -> _build/cv.yml (+ template overrides)")
