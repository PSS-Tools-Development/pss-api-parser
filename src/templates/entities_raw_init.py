{% for entity in entities %}
from .{{entity.name_snake_case}} import {{entity.name}}
{% endfor %}