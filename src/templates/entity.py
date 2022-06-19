from datetime import timedelta as _timedelta
import json as _json
from typing import Any as _Any
from typing import Dict as _Dict
from typing import Tuple as _Tuple

from .entity_base import EntityBase as _EntityBase
from .raw import {{entity.name}}Raw as _{{entity.name}}Raw
from ..types import EntityInfo as _EntityInfo
from ..utils import parse as _parse


class {{entity.name}}(_EntityBase, _{{entity.name}}Raw):
    def __init__(self, {{entity.name_snake}}_info: _EntityInfo) -> None:
        super().__init__({{entity.name_snake}}_info)


    def __repr__(self) -> str:
        return f'<{{entity.name}} {self.id}: {self.name}>'


    def __str__(self) -> str:
        return f'<{{entity.name}} {self.id}: {self.name}>'


    @property
    def id(self) -> int:
        raise NotImplemented()


    @property
    def name(self) -> str:
        raise NotImplemented()