{% if cv.name %}
= {{ cv.name }}
{% endif %}
{% if cv.headline %}
#headline([{{ cv.headline }}])
{% endif %}
{% if cv._connections|length > 0 %}
#connections(
{% for connection in cv._connections %}
  [{{ connection }}],
{% endfor %}
)
{% endif %}
#v({{ design.header.space_below_connections }})
