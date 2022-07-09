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


IMPORTS = {
    'datetime': 'from datetime import datetime as _datetime',
    'List': 'from typing import List as _List',
}


import json as _json
import os as _os
from typing import Dict as _Dict
from typing import List as _List
from typing import Tuple as _Tuple
from jinja2 import Environment as _Environment, PackageLoader as _PackageLoader


from . import utils as _utils



def read_data(file_path: str) -> dict:
    result = None
    with open(file_path) as f:
        result = _json.load(f)
    return result


def prepare_data(data: dict) -> _Tuple[dict, dict]:
    known_entity_names = set(data['entities'].keys())
    services = __prepare_endpoint_data(data['endpoints'], known_entity_names)
    entities = __prepare_entity_data(data['entities'])
    return (services, entities)


def __prepare_endpoint_data(endpoints_data: dict, known_entity_names: set) -> dict:
    result = []
    for service_name, endpoints in endpoints_data.items():
        service_imports = {'List'}

        service = {
            'endpoints': [],
            'entity_types': set(),
            'imports': [],
            'name': service_name,
            'name_snake_case': _utils.convert_to_snake_case(service_name),
        }

        for endpoint_name, endpoint_definition in endpoints.items():
            name_snake_case = _utils.convert_to_snake_case(endpoint_name)
            xml_parent_tag_name, return_type = __get_return_type(endpoint_definition['response_structure'], known_entity_names)
            parameters = __extract_parameters(endpoint_definition['query_parameters'])
            service_imports.update(parameter['type'] for parameter in parameters)

            for parameter in parameters:
                type_ = parameter['type']
                if type_ in IMPORTS:
                    parameter['type'] = f'_{type_}'
            service['endpoints'].append({
                'base_path_name': name_snake_case.upper(),
                'name': endpoint_name,
                'name_snake_case': name_snake_case,
                'parameter_definitions': ', '.join([f'{parameter["name_snake_case"]}: {parameter["type"]}' for parameter in parameters]),
                'parameters': parameters,
                'return_type': return_type,
                'xml_parent_tag_name': xml_parent_tag_name,
            })

            if return_type:
                service['entity_types'].add(return_type)
        for service_import in service_imports:
            if service_import in IMPORTS:
                service['imports'].append(IMPORTS[service_import])
        service['imports'] = sorted(list(set(service['imports'])))
        result.append(service)
    return result


def __prepare_entity_data(entities_data: dict) -> dict:
    return None


def __get_return_type(response_structure: dict, entity_names: _List[str], parent_tag_name: str = None) -> _Tuple[str, str]:
    """ The return type will be determined by crawling through dict 'response_structure' until there's
        a match of tag name and any known entity_name. All matching tag names on that depth will
        be considered for the response type. If there's only one entity type, a list of that entity
        type will be returned. If there are multiple, the return type is a Tuple of those entity types."""
    result = (parent_tag_name, None)
    if isinstance(response_structure, dict):
        keys = list(response_structure.keys())
        entity_types = [key for key in keys if key in entity_names]
        if entity_types:
            result = (parent_tag_name, entity_types[0])
        else:
            for key, value in response_structure.items():
                result = __get_return_type(value, entity_names, key)
                if result[1]: # At least 1 known entity type has been found
                    break
                else:
                    result = (parent_tag_name, None)
    return result


def __extract_parameters(query_parameters: dict) -> _List[_Dict[str, str]]:
    result = []
    for name, type in query_parameters.items():
        result.append({
            'name': name,
            'name_snake_case': _utils.convert_to_snake_case(name),
            'type': type
        })
    return result


def generate_files_from_data(data: dict, target_path: str) -> None:
    env = _Environment(
        loader=_PackageLoader('src'),
        trim_blocks=True
    )

    services = data[0]

    service_template = env.get_template('service.py')
    services_init_template = env.get_template('services_init.py')
    service_raw_template = env.get_template('service_raw.py')
    services_raw_init_template = env.get_template('services_raw_init.py')

    services_path = _os.path.join(target_path, 'services')
    services_raw_path = _os.path.join(target_path, 'services', 'raw')

    _utils.create_path(target_path)
    _utils.create_path(services_path)
    _utils.create_path(services_raw_path)

    for service in services:
        _utils.create_file(
            _os.path.join(services_path, service['name_snake_case'] + '.py'),
            service_template.render(service=service),
            overwrite=True
        )
        _utils.create_file(
            _os.path.join(services_raw_path, service['name_snake_case'] + '_raw.py'),
            service_raw_template.render(service=service),
            overwrite=True
        )
        break

    _utils.create_file(
        _os.path.join(services_path, '__init__.py'),
        services_init_template.render(services=services),
        overwrite=True
    )
    _utils.create_file(
        _os.path.join(services_raw_path, '__init__.py'),
        services_raw_init_template.render(services=services),
        overwrite=True
    )


def generate_source_code(data_file_path: str, target_path: str) -> None:
    data = read_data(data_file_path)
    prepared_data = prepare_data(data)
    generate_files_from_data(prepared_data, target_path)