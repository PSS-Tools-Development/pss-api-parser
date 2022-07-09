{% for service in services %}
from . import {{service.name_snake_case}} as {{service.name}}Raw
{% endfor %}