{% set main_lines = entry.main_column.splitlines() %}
{% set date_lines = entry.date_and_location_column.splitlines() %}
{% set title = main_lines[0] if main_lines|length > 0 else "" %}
{% set date_str = date_lines[0] if date_lines|length > 0 else "" %}
#devforge-entry(
    title: [{{ title }}],
    {% if date_str %}
    date: [{{ date_str }}],
    {% endif %}
)[
{% for line in main_lines[1:] %}
{% if line and line != "!!! summary" %}
    {{ line }}
{% endif %}
{% endfor %}
]
