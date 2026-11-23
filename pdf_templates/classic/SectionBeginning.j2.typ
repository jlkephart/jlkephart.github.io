{# Override of RenderCV 2.8's built-in typst/SectionBeginning.j2.typ. Changes from the original:
   1. the publication-key block under Peer-Reviewed Publications;
   2. numbered-citation and mentoring sections (NumberedEntry / OneLineEntry, built by
      prepare_pdf.py) skip RenderCV's
      content-area wrapper, which is an unbreakable block when entries.allow_page_break is
      false: a 41-item list then jumps to a new page and overflows into the footer. They get
      an equivalent breakable block instead, closed in SectionEnding.j2.typ.
   3. two heading levels: prepare_pdf.py names grouped sections "Group ⟫ Sub" (first section
      of a group) or "Group › Sub" (the rest). The first prints the group as the normal
      section heading plus a smaller sub-heading; the rest print only the sub-heading, so
      RenderCV treats the whole group as one section.
   RenderCV uses this copy because prepare_pdf.py places it at _build/classic/, next to the
   generated CV file. If RenderCV's own template changes in a future version, re-copy it and
   re-add the blocks below. #}
{% set sub_style = "#block(sticky: true, above: 1.1em, below: 0.8em)[#text(size: 1.12em, weight: \"bold\", fill: " ~ design.colors.section_titles.as_rgb() ~ ")[" %}
{% if " ⟫ " in section_title %}{% set parts = section_title.split(" ⟫ ", 1) %}
== {{ parts[0] }}

{{ sub_style }}{{ parts[1] }}]]
{% elif " › " in section_title %}{% set parts = section_title.split(" › ", 1) %}

{{ sub_style }}{{ parts[1] }}]]
{% else %}
== {{section_title}}
{% endif %}
{% if section_title.endswith("Peer-Reviewed Publications") %}

#block(below: 0.8em)[#pad(left: {{ design.entries.side_space }})[#sym.ast.basic co-first or co-senior authorship; #underline[underlined] authors were mentored scholars at the time of first submission.]]
{% endif %}
{% if entry_type in ["NumberedEntry", "OneLineEntry", "TextEntry", "BulletEntry"] %}

#metadata("skip-content-area")
#block(
  breakable: true,
  width: 100%,
  inset: (left: {{ design.entries.side_space }}, right: {{ design.entries.side_space }}),
  below: {{ design.sections.space_between_text_based_entries }} + {{ design.typography.line_spacing }},
)[
#set par(
  spacing: {{ design.sections.space_between_text_based_entries }} + {{ design.typography.line_spacing }},
  leading: {{ design.typography.line_spacing }},
  justify: {{ "true" if design.typography.alignment == "justified" else "false" }},
)
#set enum(spacing: {{ design.sections.space_between_text_based_entries }} + {{ design.typography.line_spacing }})
#set list(spacing: {{ design.sections.space_between_text_based_entries }} + {{ design.typography.line_spacing }}, body-indent: {{ design.entries.highlights.space_between_bullet_and_text }})
{% endif %}
{% if entry_type in ["ReversedNumberedEntry"] %}

#reversed-numbered-entries(
  [
{% endif %}
