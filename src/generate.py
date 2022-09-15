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
import os as _os
from typing import Dict as _Dict
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple
from jinja2 import Environment as _Environment, PackageLoader as _PackageLoader


from . import utils as _utils


IMPORTS = {
    'datetime': 'from datetime import datetime as _datetime',
    'List': 'from typing import List as _List',
}



def read_data(file_path: str) -> dict:
    result = None
    with open(file_path) as f:
        result = _json.load(f)
    return result


def prepare_data(data: dict) -> _Tuple[list, list]:
    known_entity_names = set(data['entities'].keys())
    services = __prepare_services_data(data['endpoints'], known_entity_names)
    entities = __prepare_entities_data(data['entities'])
    return (services, entities)


def __prepare_services_data(endpoints_data: dict, known_entity_names: set) -> list:
    result = []
    for service_name, endpoints in endpoints_data.items():
        service_imports = {'List'}

        service = {
            'endpoints': [],
            'entity_types': [],
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
                'parameter_definitions': ', '.join([f'{parameter["name_snake_case"]}: {parameter["type"]}' for parameter in parameters if parameter['type']]),
                'parameters': parameters,
                'return_type': return_type,
                'xml_parent_tag_name': xml_parent_tag_name,
            })

            if return_type:
                service['entity_types'].append(return_type)
        for service_import in service_imports:
            if service_import in IMPORTS:
                service['imports'].append(IMPORTS[service_import])
        service['entity_types'] = sorted(list(set(service['entity_types'])))
        service['imports'] = sorted(list(set(service['imports'])))
        result.append(service)
    return result


def __prepare_entities_data(entities_data: dict) -> list:
    result = []
    for entity_name, entity_properties in entities_data.items():
        properties = []
        property_names = []
        for property_name, property_type in entity_properties.items():
            property_names.append(property_name)
            properties.append({
                'name': property_name,
                'name_snake_case': _utils.convert_to_snake_case(property_name),
                'type': property_type
            })
        id_property = __find_id_property(property_names, entity_name)
        name_property = __find_name_property(property_names, entity_name)
        result.append({
            'base_class_name': 'EntityWithIdBase' if id_property else 'EntityBase',
            'id_property_name': _utils.convert_to_snake_case(id_property),
            'name': entity_name,
            'name_property_name': _utils.convert_to_snake_case(name_property),
            'name_snake_case': _utils.convert_to_snake_case(entity_name),
            'properties': properties,
            'xml_node_name': entity_name,
        })
    result.sort(key=lambda d: d['name'])
    return result


def __find_id_property(property_names: _List[str], entity_name: str) -> _Optional[str]:
    exact_id_name = f'{entity_name}Id'
    found_id_name = False

    for property_name in property_names:
        if property_name:
            if property_name == exact_id_name:
                return property_name
            found_id_name = found_id_name or property_name == 'Id'
    if found_id_name:
        return 'Id'
    return None


def __find_name_property(property_names: _List[str], entity_name: str) -> _Optional[str]:
    message = None
    name = None
    title = None
    key = None

    for property_name in property_names:
        if property_name and property_name[:2] == 'Id':
            return property_name
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


def generate_files_from_data(services_data: list, entities_data: list, target_path: str, force_overwrite: bool) -> None:
    env = _Environment(
        loader=_PackageLoader('src'),
        trim_blocks=True
    )

    __generate_services_files(services_data, target_path, env, force_overwrite)
    __generate_client_file(services_data, target_path, env, force_overwrite)
    __generate_entities_files(entities_data, target_path, env, force_overwrite)


def __generate_services_files(services_data: dict, target_path: str, env: _Environment, force_overwrite: bool) -> None:
    service_template = env.get_template('service.py')
    services_init_template = env.get_template('services_init.py')
    service_raw_template = env.get_template('service_raw.py')
    services_raw_init_template = env.get_template('services_raw_init.py')

    services_path = _os.path.join(target_path, 'services')
    services_raw_path = _os.path.join(services_path, 'raw')

    _utils.create_path(target_path)
    _utils.create_path(services_path)
    _utils.create_path(services_raw_path)

    for service in services_data:
        _utils.create_file(
            _os.path.join(services_path, service['name_snake_case'] + '.py'),
            service_template.render(service=service),
            overwrite=force_overwrite,
        )
        _utils.create_file(
            _os.path.join(services_raw_path, service['name_snake_case'] + '_raw.py'),
            service_raw_template.render(service=service),
            overwrite=True
        )

    _utils.create_file(
        _os.path.join(services_path, '__init__.py'),
        services_init_template.render(services=services_data),
        overwrite=force_overwrite,
    )
    _utils.create_file(
        _os.path.join(services_raw_path, '__init__.py'),
        services_raw_init_template.render(services=services_data),
        overwrite=True
    )


def __generate_client_file(services_data: dict, target_path: str, env: _Environment, force_overwrite: bool) -> None:
    client_template = env.get_template('client.py')

    _utils.create_file(
        _os.path.join(target_path, 'client.py'),
        client_template.render(services=services_data),
        overwrite=force_overwrite,
    )


def __generate_entities_files(entities_data: dict, target_path: str, env: _Environment, force_overwrite: bool) -> None:
    entity_template = env.get_template('entity.py')
    entities_init_template = env.get_template('entities_init.py')
    entity_raw_template = env.get_template('entity_raw.py')
    entities_raw_init_template = env.get_template('entities_raw_init.py')

    entities_path = _os.path.join(target_path, 'entities')
    entities_raw_path = _os.path.join(entities_path, 'raw')

    _utils.create_path(entities_path)
    _utils.create_path(entities_raw_path)

    for entity in entities_data:
        _utils.create_file(
            _os.path.join(entities_path, entity['name_snake_case'] + '.py'),
            entity_template.render(entity=entity),
            overwrite=force_overwrite,
        )
        _utils.create_file(
            _os.path.join(entities_raw_path, entity['name_snake_case'] + '_raw.py'),
            entity_raw_template.render(entity=entity),
            overwrite=True
        )

    _utils.create_file(
        _os.path.join(entities_path, '__init__.py'),
        entities_init_template.render(entities=entities_data),
        overwrite=force_overwrite,
    )
    _utils.create_file(
        _os.path.join(entities_raw_path, '__init__.py'),
        entities_raw_init_template.render(entities=entities_data),
        overwrite=True
    )


def generate_source_code(data_file_path: str, target_path: str, force_overwrite: bool = False) -> None:
    if force_overwrite is None:
        raise Exception('Parameter \'force_overwrite\' must not be None!')
    data = read_data(data_file_path)
    services_data, entities_data = prepare_data(data)
    generate_files_from_data(services_data, entities_data, target_path, force_overwrite)