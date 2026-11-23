{# Override of RenderCV 2.8's built-in typst/entries/OneLineEntry.j2.typ. This CV uses one-line
   entries only for entries that prepare_pdf.py lays out like the Bilal CV (plain, not bold text):
   - Mentoring: `label` is the date, shown in a left column; `details` is the description, with
     extra indented lines (thesis, current position, awards) separated by " ¶ ".
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
