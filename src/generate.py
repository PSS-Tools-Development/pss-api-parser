# ToDo
# ✓ Template for raw service
# ✓ Template for service basis
# ✓ Template for raw entity
# ✓ Template for entity basis
# (Start with a rough outsketch, then refine)
#
# Read json file
# Preprocess data to add more keys and values to the dicts:
# - service
#   .endpoints
#     .base_path_name
#     .function_name (endpoint name converted to snake case)
#     .name
#     .name_snake_case (name converted to snake case)
#     .return_type
#     .parameter_definitions (comma-separated list of {parameter.name_snake_case: parameter_type})
#     .parameters
#       .name
#       .name_snake_case
#     .xml_parent_tag_name
#   .name
# - entity
#   .name
#   .name_snake_case
#   .properties
#     .name
#     .name_snake_case
#     .parser_function_name (determined through a dictionary with types to name relationships)
#     .type
#   .xml_node_name

import json as _json
from typing import Dict as _Dict
from typing import List as _List
from typing import Tuple as _Tuple

import utils as _utils



def read_data(file_path: str) -> dict:
    result = None
    with open(file_path) as f:
        result = _json.load(f)
    return result


def prepare_data(data: dict) -> dict:
    entity_names = list(data['entities'].keys())
    services = []
    for service_name, endpoints in data['endpoints'].items():
        endpoints = []
        for endpoint_name, endpoint_definition in endpoints.items():
            xml_parent_tag_name, return_type = __get_return_type(endpoint_definition['response_structure'], entity_names)
            parameters = __extract_parameters(endpoint_definition['query_parameters'])
            endpoints.append({
                'base_path_name': endpoint_name.upper(),
                'name': endpoint_name,
                'name_snake_case': _utils.convert_to_snake_case(endpoint_name),
                'parameter_definitions': ', '.join([f'{parameter["name"]}: {parameter["type"]}' for parameter in parameters]),
                'parameters': parameters,
                'return_type': return_type,
                'xml_parent_tag_name': xml_parent_tag_name,
            })
        services.append({
            'endpoints': endpoints,
            'name': service_name,
            'name_snake_case': _utils.convert_to_snake_case(service_name)
        })


def __get_return_type(response_structure: dict, entity_names: _List[str], parent_tag_name: str = None) -> _Tuple[str, str]:
    """ The return type will be determined by crawling through 'response_structure' until there's
        a match of tag name and any known entity_name. All matching tag names on that depth will
        be considered for the response type. If there's only one entity type, a list of that entity
        type will be returned. If there are multiple, the return type is a Tuple of those entity types."""
    result = None
    if isinstance(response_structure, dict):
        keys = list(response_structure.keys())
        entity_types = [key for key in keys if key in entity_names]
        if entity_types:
            if len(entity_types) > 1:
                result = f'_Tuple[{", ".join(entity_types)}'
            else:
                result = f'_List[{entity_types[0]}]'
        else:
            for key, value in response_structure.items():
                result = __get_return_type(value, entity_names, key)
                if result: # At least 1 known entity type has been found
                    break
                else:
                    result = None
    return (parent_tag_name, result)


def __extract_parameters(query_parameters: dict) -> _List[_Dict[str, str]]:
    result = []
    for name, type in query_parameters.items():
        result.append({
            'name': name,
            'name_snake_case': _utils.convert_to_snake_case(name),
            'type': type
        })
    return result


def generate_files_from_data(data: dict) -> None:
    pass


def generate_source_code(data_file_path: str) -> None:
    data = read_data(data_file_path)
    prepared_data = prepare_data(data)
    generate_files_from_data(prepared_data)