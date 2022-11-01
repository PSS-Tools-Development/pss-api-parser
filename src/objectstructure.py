from typing import Dict as _Dict


class PssObjectStructure:
    def __init__(self, object_type_name: str, properties: _Dict[str, str]) -> None:
        self.object_type_name: str = object_type_name
        self.properties = properties

    def __repr__(self) -> str:
        return f'<PssObjectStructure "{self.object_type_name}">'

    def __str__(self) -> str:
        return self.__repr__()
