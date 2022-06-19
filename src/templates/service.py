from typing import List as _List

from .service_base import PssServiceBase as _ServiceBase
{% for endpoint in service.endpoints %}
from ..entities import {{endpoint.return_type}} as _{{endpoint.return_type}}
{% endfor %}
from .raw import {{service.name}}Raw as _{{service.name}}Raw


class {{service.name}}(_ServiceBase):
{% for endpoint in service.endpoints %}
    async def {{endpoint.name_snake_case}}(self, {{endpoint.parameter_definitions}}) -> _List[_{{endpoint.return_type}}]:
        raise NotImplemented()
        result = await _{{service.name}}Raw.{{endpoint.name_snake_case}}(self.production_server, {{endpoint.parameter_definitions}})
        return result
{% endfor %}