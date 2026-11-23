{# Override of RenderCV 2.8's built-in typst/SectionEnding.j2.typ: also closes the breakable
   block that SectionBeginning.j2.typ opens for numbered-citation sections. #}
{% if entry_type in ["NumberedEntry", "OneLineEntry"] %}

]
{% endif %}
{% if entry_type in ["ReversedNumberedEntry"] %}
  ],
)
{% endif %}
