{% set main_lines = entry.main_column.splitlines() %}
{% set date_lines = entry.date_and_location_column.splitlines() %}
## {{ main_lines[0] | replace("    ", "") }}

{% for line in date_lines %}{{ line | replace("    ", "") }}
{% endfor %}
{% for line in main_lines[1:] %}{% if line and line != "!!! summary" %}
{{ line | replace("    ", "") }}
{% endif %}{% endfor %}
