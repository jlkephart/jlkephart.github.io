{# Override of RenderCV 2.8's built-in typst/entries/OneLineEntry.j2.typ. prepare_pdf.py turns
   most sections (education, experience, honors, grants, service, review, mentoring, teaching,
   presentations, media, skills) into one-line entries drawn here in plain (not bold) text. The
   labels and separators are constants in scripts/cvlib.py (LABEL_*, SUBLINE " ¶ ", RIGHT " ¦ "):
   - Dated entries: `label` is the date, shown in a left column; `details` is the text, with any
     extra lines (thesis, current position, awards, highlights) separated by " ¶ " and indented.
   - Grants: `label` is "GRANT"; `details` holds rows separated by " ¶ ", and a row may have
     right-aligned text after " ¦ " (dates, total costs).
   - Sub-headings (e.g. institutions in Teaching): `label` is "SUBHEAD", `details` is the text. #}
{% set lines = entry.details.split(" ¶ ") %}
{% if entry.label == "SUBHEAD" %}
#block(breakable: false, sticky: true, above: 0.9em, below: 0.5em)[#emph[{{ entry.details }}]]
{% elif entry.label == "GRANT" %}
#block(breakable: false, width: 100%, below: 1.1em)[
#set par(spacing: {{ design.typography.line_spacing }})
{% for line in lines %}{% set cells = line.split(" ¦ ") %}
#grid(
  columns: (1fr, auto),
  column-gutter: 0.5cm,
  [{{ cells[0] }}],
  [{{ cells[1] if cells|length > 1 else "" }}],
)
{% endfor %}
]
{% else %}
#block(breakable: false, width: 100%)[
#grid(
  columns: (2.4cm, 1fr),
  column-gutter: 0.3cm,
  [{{ entry.label }}],
  [#set par(spacing: {{ design.typography.line_spacing }})
{{ lines[0] }}{% for line in lines[1:] %}

#pad(left: 1.2em)[{{ line }}]{% endfor %}],
)
]
{% endif %}
