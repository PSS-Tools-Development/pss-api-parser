from datetime import timedelta as _timedelta
import json as _json
import os as _os
import re as _re
import sys as _sys
from timeit import default_timer as _timer
from typing import Dict as _Dict
from typing import List as _List
from typing import Union as _Union

import utils as _utils


EnumDefinition = _Dict[str, _Union[str, _Dict[str, _Union[int, str]]]]
TYPE_INT_ENUM = 'IntEnum'
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
RX_ENUM_VALUE_DEFINITION = f'({RX_CSHARP_ACCESS_MODIFIERS}) const {{0}} (.*?) = (.*?);'   # {0} should receive the name of the enum


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
                elif line.startswith('}'): # All values collected
                    if not result[enum_name]['type']:
                        if any(value_type and isinstance(value_type, str) for value_type in result[enum_name]['values'].values()):
                            result[enum_name]['type'] = TYPE_STR_ENUM
                        else:
                            result[enum_name]['type'] = TYPE_INT_ENUM
                    if result[enum_name]['type'] == TYPE_STR_ENUM:
                        for enum_value_name in result[enum_name]['values'].keys():
                            if result[enum_name]['values'][enum_value_name] is not None:
                                result[enum_name]['values'][enum_value_name] = enum_value_name
                    elif result[enum_name]['type'] == TYPE_INT_ENUM:
                        for enum_value_name in tuple(result[enum_name]['values'].keys()):
                            fixed_enum_value_name = _utils.convert_snake_to_camel_case(enum_value_name)
                            if fixed_enum_value_name != enum_value_name:
                                result[enum_name]['values'][fixed_enum_value_name] = result[enum_name]['values'][enum_value_name]
                                result[enum_name]['values'].pop(enum_value_name)
                    found_marker = False
                    enum_name = rx_enum_value_custom = None
                else: # Search for values
                    if '[XmlEnumAttribute]' in line:
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
    return result


def store_enum_file(enum_definitions: _Dict[str, EnumDefinition], store_at: str, indent: int = 4) -> None:
    with open(store_at, 'w') as fp:
        _json.dump(enum_definitions, fp, indent=indent)


if __name__ == "__main__":
    app_start = _timer()
    if len(_sys.argv) == 1:
        raise ValueError('The path to the CSharp dump file has not been specified!')
    file_path = ' '.join(_sys.argv[1:])
    file_name, _ = _os.path.splitext(file_path)
    storage_path = f'{file_name}_enums.json'

    start = _timer()
    enums = parse_csharp_dump_file(file_path)
    end = _timer()

    store_enum_file(enums, storage_path, indent=2)
    print(f'Stored JSON encoded PSS API endpoint information in {_timedelta(seconds=(end - start))} at: {storage_path}')
    print(f'Total execution time: {_timedelta(seconds=(end - app_start))}')