from typing import Dict



class PssObjectStructure():
    def __init__(self, object_type_name: str, properties: Dict[str, str]) -> None:
        self.object_type_name: str = object_type_name
        self.properties = properties