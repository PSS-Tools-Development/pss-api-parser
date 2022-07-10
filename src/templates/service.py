{% for service_import in service.imports %}
{{service_import}}
{% endfor %}

from .raw import {{service.name}}Raw as _{{service.name}}Raw
from .service_base import PssServiceBase as _ServiceBase
{% for entity_type in service.entity_types %}
from ...entities import {{entity_type}} as _{{entity_type}}
{% endfor %}


class {{service.name}}(_ServiceBase):
{% for endpoint in service.endpoints %}
    async def {{endpoint.name_snake_case}}(self, {{endpoint.parameter_definitions}}) -> _List[_{{endpoint.return_type}}]:
        raise NotImplemented()
        result = await _{{service.name}}Raw.{{endpoint.name_snake_case}}(self.production_server, {{endpoint.parameter_definitions}})
        return result


{% endfor %}