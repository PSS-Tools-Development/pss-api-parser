import json as _json
import re as _re
from enum import StrEnum, auto
from typing import Dict as _Dict
from typing import List as _List
from typing import Union as _Union

from . import utils as _utils

EnumDefinition = _Dict[str, _Union[str, _Dict[str, _Union[int, str]]]]
TYPE_INT_ENUM = 'IntEnum'
TYPE_INT_FLAG = 'IntFlag'
TYPE_STR_ENUM = 'StrEnum'

CSHARP_ACCESS_MODIFIERS = [
    'private',
    'public',
    'internal',
    'protected'
]
RX_CSHARP_ACCESS_MODIFIERS = '|'.join(CSHARP_ACCESS_MODIFIERS)

MARKER_ENUM_DEFINITION_PREFIX = '// Namespace: SavySoda.PixelStarships.Model.SharedModel.Enums'
RX_ENUM_DEFINITION: _re.Pattern = _re.compile(f'({RX_CSHARP_ACCESS_MODIFIERS}) enum ([^\.]*?) ')
RX_ENUM_VALUE_DEFINITION = f'({RX_CSHARP_ACCESS_MODIFIERS}) const {{0}} (.*?) = (.*?);'  # {0} should receive the name of the enum


class ProgrammingLanguage(StrEnum):
    PYTHON = auto()

    def template_dir(self):
        return self.value


def parse_csharp_dump_file(file_path: str) -> _Dict[str, EnumDefinition]:
    # iterate through file lines
    # if line starts with MARKER_ENUM_DEFINITION_PREFIX:
    # - go to next line until it matches RX_ENUM_DEFINITION
    # - extract enum name (2nd group)
    # - assemble custom rx for that enum (rx_enum_value_custom) from RX_ENUM_VALUE_DEFINITION
    # - go to line starting with '{'
    # - iterate further lines, until line starts with '}'
    #   - if line matches rx_enum_value_custom, extract value name (2nd group)
    # - store definition in dict
    result: _Dict[str, EnumDefinition] = {}
    with open(file_path, 'r') as fp:
        found_marker = False
        enum_name = None
        rx_enum_value_custom = None
        for line in fp:
            if not found_marker and line.startswith(MARKER_ENUM_DEFINITION_PREFIX):
                found_marker = True
            elif found_marker:
                if not enum_name:
                    match = RX_ENUM_DEFINITION.search(line)
                    if match:
                        enum_name = match.group(2)
                        rx_enum_value_custom = _re.compile(RX_ENUM_VALUE_DEFINITION.format(enum_name))
                        result[enum_name] = {
                            'type': TYPE_INT_ENUM if 'Flag' in enum_name else '',
                            'values': {}
                        }
                elif line.startswith('}'):  # All values collected
                    if not result[enum_name]['type']:
                        if any(value_type and isinstance(value_type, str) for value_type in result[enum_name]['values'].values()):
                            result[enum_name]['type'] = TYPE_STR_ENUM
                        else:
                            result[enum_name]['type'] = TYPE_INT_ENUM
                    if result[enum_name]['type'] == TYPE_STR_ENUM:
                        for enum_value_name in result[enum_name]['values'].keys():
                            if result[enum_name]['values'][enum_value_name] is not None:
                                result[enum_name]['values'][enum_value_name] = enum_value_name
                    for enum_value_name in tuple(result[enum_name]['values'].keys()):
                        if enum_value_name.startswith(enum_name):
                            result[enum_name]['values'][enum_value_name[len(enum_name):]] = result[enum_name]['values'][enum_value_name]
                            result[enum_name]['values'].pop(enum_value_name)
                    found_marker = False
                    enum_name = rx_enum_value_custom = None
                else:  # Search for values
                    if '[XmlEnumAttribute]' in line or '[XmlEnum(' in line:
                        likely_str = True
                    elif 'const' in line:
                        match = rx_enum_value_custom.search(line)
                        if match:
                            enum_value_name = match.group(2)
                            if result[enum_name]['type'] == TYPE_INT_ENUM or enum_value_name.isupper() or not likely_str:
                                enum_value_value = int(match.group(3))
                            else:
                                enum_value_value = enum_value_name
                            if enum_value_value == 'None':
                                enum_value_value = None
                            result[enum_name]['values'][enum_value_name] = enum_value_value
                        likely_str = False
    
    for enum_name in result.keys():
        if result[enum_name]['type'] == TYPE_INT_ENUM:
            enum_name_lower = enum_name.lower()
            if enum_name_lower.endswith(('flag', 'flags', 'flagtype', 'flagstype')):
                result[enum_name]['type'] = TYPE_INT_FLAG

    return result


def store_enum_file(enum_definitions: _Dict[str, EnumDefinition], store_at: str, compressed: bool = False) -> None:
    if compressed:
        indent = None
        separators = (',', ':')
    else:
        indent = 2
        separators = (', ', ': ')
    with open(store_at, 'w') as fp:
        _json.dump(enum_definitions, fp, indent=indent, separators=separators)