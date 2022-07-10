{% for entity in entities %}
from .{{entity.name_snake_case}}_raw import {{entity.name}}Raw
{% endfor %}