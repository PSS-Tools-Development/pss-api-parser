{% for service in services %}
from .{{service.name_snake_case}} import {{service.name}}
{% endfor %}