# LASH Lab website

Live at <https://jlkephart.github.io>.

## How to update

Edit **`_data/cv.yml`** (on github.com: open the file, click the pencil, commit). That one file is the CV.
On every push to `main` (and weekly on Mondays), the GitHub Action in `.github/workflows/publish.yml`:

1. builds the CV PDF from `cv.yml` with [RenderCV](https://docs.rendercv.com) 2.8,
2. regenerates the Publications, Research (grants), Teaching, Media, and People pages from `cv.yml`,
3. publishes the site to GitHub Pages (about 2–3 minutes).

Hand-written text lives in `index.qmd` and `research.qmd`. Everything in `_generated/`, `_build/`, and
`assets/cv.pdf` is rebuilt automatically; never edit those by hand.

## How the CV PDF is built

`cv.yml` holds content only. `scripts/prepare_pdf.py` writes a PDF-only copy, `_build/cv.yml`, that adds
the layout (keep Typst or layout markup out of `_data/cv.yml`):

- **Two heading levels.** Sections named `"Group: Sub"` (e.g. `'Mentoring: Faculty Mentees'`) print the
  group once as a large heading with each section as a sub-heading. Publications, briefs, and media are
  grouped under *Publications*, and Active/Completed Grants under *Research Grant Participation*, in the
  PDF only (their names in `cv.yml` stay as the website expects).
- **Section order** in the PDF follows the order of keys in `cv.yml`.
- **Publications** become numbered one-line citations (newest = 1), with trainees underlined.
- **List sections** (experience, honors, service, review, mentoring, teaching, presentations, media,
  skills) print plain text with the date in a left column; `group` or `institution` fields become italic
  sub-headings; repeat course offerings merge onto one line.
- **Grants** print as funder / dates, investigators / total costs, title.

The layouts come from overrides of RenderCV's built-in templates in `pdf_templates/classic/`
(`SectionBeginning.j2.typ`, `SectionEnding.j2.typ`, and `entries/OneLineEntry.j2.typ`). RenderCV picks
them up because `prepare_pdf.py` copies them next to `_build/cv.yml`. **RenderCV is pinned to 2.8 for this
reason:** when upgrading, re-copy the new built-in templates and re-apply the changes described at the
top of each override. Long list sections are wrapped in a breakable block so they can span pages.

## Conventions in `cv.yml`

**Publications** (`Peer-Reviewed Publications`, `Manuscripts Under Review`)
- `'**Kephart JL**'` bolds the PI; a trailing `\*` marks co-first/co-senior authorship, and
  `co_first_or_senior: "yes"` is set only on those papers.
- **Trainee underlines are automatic** (`scripts/trainees.py`, used by both the PDF and the website): an
  author is underlined when they match someone in any `Mentoring: ...` section (same surname and first
  initial, including the first part of a two-part surname) and the paper's year falls within the
  mentoring years (+1).
  - `mentees: "Surname I"` forces an underline the automatic match misses.
  - `not_mentees: "Surname I"` suppresses a wrong automatic match on that one paper.

**Grants** (`Active Grants`, `Completed Grants`): `name` (title + grant number), `date`, `funder`,
`investigators`, `total_costs`. Dollar amounts appear in the PDF only, never on the website.

**Mentoring** sections are by role; a person can appear in several. Fields: `name`, `date`, and optional
`fellowship`, `program`, `with`, `affiliation`, `note`, `thesis`, `position` (printed as "Current
position: Title (Organization)"), `award`. **`lab_role`** puts the person on the People page: current
members if their date ends in `present`, alumni otherwise.

**Teaching** entries carry `institution` (used for sub-headings). Write courses as
`"Title, EOH 642 (3 credits)"` or `"Title, Independent Study (3 credits; 1 student)"`.

**Ordering:** newest first by start date in every section and sub-group; Completed Grants by end date.
Keep single years as plain numbers (`date: 2025`, not `'2025'`), or the PDF prints "Jan 2025".

## Preview locally

```
pip install "rendercv[full]==2.8" pyyaml
python scripts/prepare_pdf.py && rendercv render _build/cv.yml -nopng -nomd -nohtml
cp _build/rendercv_output/*.pdf assets/cv.pdf
python scripts/build_pages.py
quarto preview
```

(`build_pages.py` must run once before the first render: Quarto checks `{{< include >}}` files before its
pre-render hook runs. After that, the hook keeps the pages fresh during `quarto preview`.)

The People page (`people.qmd`) is built but hidden; to publish it, remove the `"!people.qmd"` line in
`_quarto.yml` and add it to the navbar.

`scripts/convert_from_docx.py` was the one-time migration from the Word CV (2026-11-19).
