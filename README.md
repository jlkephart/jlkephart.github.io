# LASH Lab website

Live at <https://jlkephart.github.io>.

## How to update

Edit **`_data/cv.yml`** (on github.com: open the file, click the pencil, commit). That one file is the CV.
On every push to `main`, the GitHub Action in `.github/workflows/publish.yml`:

1. builds the CV PDF from `cv.yml` with [RenderCV](https://docs.rendercv.com),
2. regenerates the Publications, People, Research (grants), and Media pages from `cv.yml`,
3. publishes the site to GitHub Pages (about 2–3 minutes).

### Conventions in `cv.yml`

- `**Kephart JL**` bolds the PI; a trailing `\*` marks co-first/co-senior authorship.
- **Trainee underlines are automatic.** Any author who matches a person in a `Mentoring: ...` section
  (same surname and first initial, mentoring years covering the paper) is underlined on the website.
  Add someone to the Mentoring sections and their papers update on the next build.
  - `mentees: "Surname I"` forces an underline the automatic match misses.
  - `not_mentees: "Surname I"` suppresses a wrong automatic match on that one paper.
  - The same rules (`scripts/trainees.py`) underline trainees in the CV PDF, via a generated copy
    `_build/cv.yml` that `scripts/prepare_pdf.py` writes. Keep `_data/cv.yml` free of Typst markup.
- `co_first_or_senior: "yes"` is set only when an author carries the `*` marker.
- People page: anyone under the PI-led mentoring sections whose date ends in `present` is listed as a current
  member; everyone else is an alumnus. Edit `LAB_SECTIONS` in `scripts/build_pages.py` to change which sections count.

Hand-written text lives in `index.qmd` and `research.qmd`. Everything in `_generated/` is rebuilt automatically.

## Preview locally

```
pip install "rendercv[full]==2.8" pyyaml
python scripts/prepare_pdf.py && rendercv render _build/cv.yml -nopdf -nopng -nomd -nohtml
python scripts/finalize_pdf.py _build/rendercv_output/*.typ assets/cv.pdf
python scripts/build_pages.py
quarto preview
```

(`build_pages.py` must run once before the first render: Quarto checks `{{< include >}}` files before its
pre-render hook runs. After that, the hook keeps the pages fresh during `quarto preview`.)

`scripts/convert_from_docx.py` was the one-time migration from the Word CV (2026-11-19).
