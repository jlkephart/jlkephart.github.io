# LASH Lab website

Live at <https://jlkephart.github.io>.

## How to update

Edit **`_data/cv.yml`** (on github.com: open the file, click the pencil, commit). That one file is the CV.
On every push to `main` (and weekly on Mondays), the GitHub Action in `.github/workflows/publish.yml`:

1. checks `cv.yml` with `scripts/validate_cv.py` (the build stops with a clear message on a data error),
2. builds the CV PDF from `cv.yml` with [RenderCV](https://docs.rendercv.com) 2.8,
3. regenerates the Publications, Research (grants), Teaching, Media, and People pages from `cv.yml`,
4. publishes the site to GitHub Pages (about 2–3 minutes).

Hand-written text lives in `index.qmd` and `research.qmd`. Everything in `_generated/`, `_build/`, and
`assets/cv.pdf` is rebuilt automatically; never edit those by hand.

## Scripts

| Script | Does |
|---|---|
| `scripts/cvlib.py` | Shared rules and constants: trainee matching, name and date parsing, course parsing, the PDF layout markers. |
| `scripts/validate_cv.py` | Checks required/allowed fields per section, date formats, `mentees`/`not_mentees` names, reserved characters, Typst markup, and that each group's sections are adjacent. |
| `scripts/prepare_pdf.py` | Writes `_build/cv.yml`: `cv.yml` plus the PDF layout (see below). Clears `_build/` first. |
| `scripts/build_pages.py` | Writes the website fragments in `_generated/` (also Quarto's pre-render step). |

## How the CV PDF is built

`cv.yml` holds content only. `scripts/prepare_pdf.py` writes a PDF-only copy, `_build/cv.yml`, that adds
the layout (keep Typst or layout markup out of `_data/cv.yml`; the validator rejects it):

- **Two heading levels.** Sections named `"Group: Sub"` (e.g. `'Mentoring: Faculty Mentees'`) print the
  group once as a large heading with each section as a sub-heading. Keep a group's sections next to each
  other. Publications, briefs, and media are grouped under *Publications*, and Active/Completed Grants
  under *Research Grant Participation*, in the PDF only (their names in `cv.yml` stay as the website
  expects; see `PDF_GROUPS` in `prepare_pdf.py`).
- **Section order** in the PDF follows the order of keys in `cv.yml`.
- **Publications** become numbered one-line citations (newest = 1), with trainees underlined.
- **List sections** (education, experience, honors, service, review, mentoring, teaching, presentations,
  media, skills) print plain text with the date in a left column; `group` or `institution` fields become
  italic sub-headings; repeat course offerings merge onto one line (e.g. "2021-2023, 2026").
- **Grants** print as funder / dates, investigators / total costs, title.

The layouts come from overrides of RenderCV's built-in templates in `pdf_templates/classic/`
(`SectionBeginning.j2.typ`, `SectionEnding.j2.typ`, and `entries/OneLineEntry.j2.typ`). RenderCV picks
them up because `prepare_pdf.py` copies them next to `_build/cv.yml`. **RenderCV is pinned to 2.8 for this
reason:** when upgrading, re-copy the new built-in templates and re-apply the changes described at the
top of each override. Long list sections are wrapped in a breakable block so they can span pages.

## Conventions in `cv.yml`

The header comment of `cv.yml` has a short version of these.

**Dates:** `2024`, `2024-2026`, `2024-present`, or `"2022, 2024"`; grants may also use
`MM/DD/YYYY-MM/DD/YYYY`.

**Publications** (`Peer-Reviewed Publications`, `Manuscripts Under Review`)
- `'**Kephart JL**'` bolds the PI; a trailing `\*` on an author marks co-first/co-senior authorship.
- **Trainee underlines are automatic** (`scripts/cvlib.py`, used by both the PDF and the website): an
  author is underlined when they match someone in any `Mentoring: ...` section (same first initial;
  surname equal to the person's last name or the first part of a compound surname) and the paper's year
  falls within the mentoring years (+1, since submission precedes publication). Spell mentee names in the
  Mentoring sections the way they appear on papers, with credentials after a comma.
  - `mentees: "Surname I"` forces an underline the automatic match misses.
  - `not_mentees: "Surname I"` suppresses a wrong automatic match on that one paper (watch for common
    surnames).
  - Manuscripts under review have no year, so they underline people mentored this year or last year;
    these underlines can change at New Year with the weekly rebuild, without any edit to `cv.yml`.

**Grants** (`Active Grants`, `Completed Grants`): `name` (title + grant number), `date`, `funder`,
`investigators`, `total_costs`. Dollar amounts appear in the PDF only, never on the website.

**Media:** `name` (the headline), `date` (year), `outlet`, `note`, `day` (e.g. `May 24`), `url`. The PDF
prints "**Outlet**. Headline. Note. Day. URL"; the website links the headline.

**Mentoring** sections are by role; a person can appear in several. Fields: `name`, `date`, and optional
`fellowship`, `program`, `with`, `affiliation`, `note`, `thesis`, `position` (printed as "Current
position: Title (Organization)"), `award`. **`lab_role`** puts the person on the People page: current
members if their date ends in `present`, alumni otherwise.

**Teaching** entries carry `institution` (used for sub-headings). Write courses as
`"Title, EOH 642 (3 credits)"` or `"Title, Independent Study (3 credits; 1 student)"` (printed as
"EOH 642: Title (3 credits)"); other shapes such as `"Title, Summer Institute (15 hrs)"` print as written.

**Other list sections:** `name`, `date`, optional `group` (an italic sub-heading).

**Ordering:** newest first by start date in every section and sub-group; Completed Grants by end date.

## Preview locally

```
pip install -r requirements.txt
python scripts/validate_cv.py
python scripts/prepare_pdf.py && rendercv render _build/cv.yml -nopng -nomd -nohtml
cp _build/rendercv_output/*.pdf assets/cv.pdf
python scripts/build_pages.py
quarto preview
```

On Windows, set `PYTHONUTF8=1` first, or RenderCV's progress output can crash the console.
(`build_pages.py` must run once before the first render: Quarto checks `{{< include >}}` files before its
pre-render hook runs. After that, the hook keeps the pages fresh during `quarto preview`.)

The People page (`people.qmd`) is built but hidden; to publish it, remove the `"!people.qmd"` line in
`_quarto.yml` and add it to the navbar.

The CV was migrated from the Word CV on 2026-11-19; the one-time converter is in the git history.
