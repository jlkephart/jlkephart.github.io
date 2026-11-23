{# Override of RenderCV 2.8's built-in typst/SectionBeginning.j2.typ (identical except the
   publication-key block). RenderCV uses this copy because prepare_pdf.py places it at
   _build/classic/, next to the generated CV file. If RenderCV's own template changes in
   a future version, re-copy it and re-add the block below. #}
== {{section_title}}
{% if section_title == "Peer-Reviewed Publications" %}

#pad(left: {{ design.entries.side_space }})[#sym.ast.basic co-first or co-senior authorship; #underline[underlined] authors were mentored scholars at the time of first submission.]

#v(0.5em)
{% endif %}
{% if entry_type in ["ReversedNumberedEntry"] %}

#reversed-numbered-entries(
  [
{% endif %}
