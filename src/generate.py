import json as _json
import os as _os
import string as _string
from typing import Dict as _Dict
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

import autopep8 as _autopep8
from jinja2 import Environment as _Environment
from jinja2 import PackageLoader as _PackageLoader

from . import enums as _enums
from . import utils as _utils

IMPORTS = {
    'datetime': 'from datetime import datetime as _datetime',
    'List': 'from typing import List as _List',
}





# -----
# ----- Prepare -----
# -----


def filter_enums_data(enums_data: _Dict[str, _enums.EnumDefinition], services_data: list, entities_data: list) -> _Dict[str, _enums.EnumDefinition]:
    potential_enum_names = []
    for service in services_data:
        for endpoint in service['endpoints']:
            for parameter in endpoint['parameters']:
                potential_enum_names.append(_utils.convert_snake_to_camel_case(_utils.convert_camel_to_snake_case(parameter['name'])))

    for entity in entities_data:
        for property in entity['properties']:
            potential_enum_names.append(property['name'])
    potential_enum_names = set(potential_enum_names)
    parsed_enum_names = set(enums_data.keys())
    used_enum_names = potential_enum_names.intersection(potential_enum_names, parsed_enum_names)
    result = {key: value for key, value in enums_data.items() if key in used_enum_names}
    return result


def prepare_parsed_api_data(parsed_api_data: dict) -> _Tuple[list, list]:
    known_entity_names = set(parsed_api_data['entities'].keys())
    services = __prepare_services_data(parsed_api_data['endpoints'], known_entity_names)
    entities = __prepare_entities_data(parsed_api_data['entities'])
    return services, entities


def prepare_parsed_enums_data(parsed_enums_data: _Dict[str, _enums.EnumDefinition]) -> list:
    result = []
    ignore_value_names = ['None', 'Unknown']
    for enum_name in sorted(parsed_enums_data.keys()):
        enum_definition = {
            'name': enum_name,
            'name_snake_case': _utils.convert_camel_to_snake_case(enum_name),
            'type': parsed_enums_data[enum_name]['type']
        }

        sorted_enum_values = sorted(parsed_enums_data[enum_name]['values'].items(), key=lambda item: item[1] or 0 if parsed_enums_data[enum_name]['type'] == _enums.TYPE_INT_ENUM else '')
        enum_value_names = [key for key, value in sorted_enum_values if value not in ignore_value_names]

        enum_definition['enum_values'] = []
        for value_name in enum_value_names:
            enum_definition['enum_values'].append({
                'name': 'None_' if value_name == 'None' else value_name,
                'value': parsed_enums_data[enum_name]['values'][value_name]
            })
        result.append(enum_definition)
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
                'name_snake_case': _utils.convert_camel_to_snake_case(property_name),
                'type': property_type
            })
        id_property = __find_id_property(property_names, entity_name)
        name_property = __find_name_property(property_names, entity_name)
        result.append({
            'base_class_name': 'EntityWithIdBase' if id_property else 'EntityBase',
            'id_property_name': _utils.convert_camel_to_snake_case(id_property),
            'name': entity_name,
            'name_property_name': _utils.convert_camel_to_snake_case(name_property),
            'name_snake_case': _utils.convert_camel_to_snake_case(entity_name),
            'properties': properties,
            'xml_node_name': entity_name,
        })
    result.sort(key=lambda d: d['name'])
    return result


def __prepare_services_data(endpoints_data: dict, known_entity_names: set) -> list:
    result = []
    for service_name, endpoints in endpoints_data.items():
        service_imports = {'List'}

        service = {
            'endpoints': [],
            'entity_types': [],
            'imports': [],
            'name': service_name,
            'name_snake_case': _utils.convert_camel_to_snake_case(service_name),
        }

        for endpoint_name, endpoint_definition in endpoints.items():
            name_snake_case = _utils.convert_camel_to_snake_case(endpoint_name)
            xml_parent_tag_name, return_type = __get_return_type(endpoint_definition['response_structure'], known_entity_names)
            parameters = __extract_parameters(endpoint_definition['query_parameters'])
            service_imports.update(parameter['type'] for parameter in parameters)

            parameter_definitions = []
            parameter_raw_definitions = []
            raw_endpoint_call_parameters = []
            for parameter in parameters:
                type_ = parameter['type']
                if type_ in IMPORTS:
                    parameter['type'] = f'_{type_}'

                parameter_name = parameter['name_snake_case']
                param_def = f'{parameter_name}: {parameter["type"]}'
                parameter_raw_definitions.append(param_def)

                if parameter['self_field']:
                    raw_endpoint_call_parameters.append(f'self.{parameter_name}')
                else:
                    default_value = parameter.get('default_value')
                    if default_value:
                        parameter_definitions.append(f'{param_def} = {default_value}')
                    else:
                        parameter_definitions.append(param_def)
                    raw_endpoint_call_parameters.append(parameter_name)

            service['endpoints'].append({
                'base_path_name': name_snake_case.upper(),
                'name': endpoint_name,
                'name_snake_case': name_snake_case,
                'name_snake_case_without_version': name_snake_case.rstrip(_string.digits).rstrip('_'),
                'parameter_definitions': ', '.join(parameter_definitions),
                'parameter_raw_definitions': ', '.join(parameter_raw_definitions),
                'raw_endpoint_call_parameters': ', '.join(raw_endpoint_call_parameters),
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





# -----
# ----- Generate -----
# -----


def generate_files_from_data(services_data: list, entities_data: list, enums_data: list, target_path: str, force_overwrite: bool) -> None:
    env = _Environment(
        loader=_PackageLoader('src'),
        trim_blocks=True
    )

    __generate_services_files(services_data, target_path, env, force_overwrite)
    __generate_client_file(services_data, target_path, env, force_overwrite)
    __generate_entities_files(entities_data, target_path, env, force_overwrite)
    if enums_data:
        __generate_enums_files(enums_data, target_path, env, force_overwrite)


def generate_source_code(parsed_api_data_file_path: str, enums_data_file_path: str, target_path: str, force_overwrite: bool = False) -> None:
    if force_overwrite is None:
        raise Exception('Parameter \'force_overwrite\' must not be None!')
    parsed_api_data = read_data(parsed_api_data_file_path)
    services_data, entities_data = prepare_parsed_api_data(parsed_api_data)

    enums_data = read_data(enums_data_file_path) if enums_data_file_path else None
    if enums_data:
        filtered_enums_data = filter_enums_data(enums_data, services_data, entities_data)
        prepared_enums_data = prepare_parsed_enums_data(filtered_enums_data)
    else:
        filtered_enums_data = None
        prepared_enums_data = None

    generate_files_from_data(services_data, entities_data, prepared_enums_data, target_path, force_overwrite)


def __generate_client_file(services_data: dict, target_path: str, env: _Environment, force_overwrite: bool) -> None:
    client_template = env.get_template('client.jinja2')

    _utils.create_file(
        _os.path.join(target_path, 'client.py'),
        format_source(client_template.render(services=services_data)),
        overwrite=force_overwrite,
    )


def __generate_enums_files(enums_data: list, target_path: str, env: _Environment, force_overwrite: bool) -> None:
    int_enum_template = env.get_template('enum_int.jinja2')
    str_enum_template = env.get_template('enum_str.jinja2')
    enum_init_template = env.get_template('enum_init.jinja2')
    enums_path = _os.path.join(target_path, 'enums')

    _utils.create_path(target_path)
    _utils.create_path(enums_path)

    for enum in enums_data:
        template = int_enum_template if enum['type'] == _enums.TYPE_INT_ENUM else str_enum_template
        _utils.create_file(
            _os.path.join(enums_path, enum['name_snake_case'] + '.py'),
            format_source(template.render(enum=enum)),
            overwrite=force_overwrite,
        )

    _utils.create_file(
        _os.path.join(enums_path, '__init__.py'),
        format_source(enum_init_template.render(enums=enums_data)),
        overwrite=force_overwrite,
    )


def __generate_services_files(services_data: dict, target_path: str, env: _Environment, force_overwrite: bool) -> None:
    service_template = env.get_template('service.jinja2')
    services_init_template = env.get_template('services_init.jinja2')
    service_raw_template = env.get_template('service_raw.jinja2')
    services_raw_init_template = env.get_template('services_raw_init.jinja2')

    services_path = _os.path.join(target_path, 'services')
    services_raw_path = _os.path.join(services_path, 'raw')

    _utils.create_path(target_path)
    _utils.create_path(services_path)
    _utils.create_path(services_raw_path)

    for service in services_data:
        _utils.create_file(
            _os.path.join(services_path, service['name_snake_case'] + '.py'),
            format_source(service_template.render(service=service)),
            overwrite=force_overwrite,
        )
        _utils.create_file(
            _os.path.join(services_raw_path, service['name_snake_case'] + '_raw.py'),
            format_source(service_raw_template.render(service=service)),
            overwrite=True
        )

    _utils.create_file(
        _os.path.join(services_path, '__init__.py'),
        format_source(services_init_template.render(services=services_data)),
        overwrite=True,
    )
    _utils.create_file(
        _os.path.join(services_raw_path, '__init__.py'),
        format_source(services_raw_init_template.render(services=services_data)),
        overwrite=True
    )


def __generate_entities_files(entities_data: dict, target_path: str, env: _Environment, force_overwrite: bool) -> None:
    entity_template = env.get_template('entity.jinja2')
    entities_init_template = env.get_template('entities_init.jinja2')
    entity_raw_template = env.get_template('entity_raw.jinja2')
    entities_raw_init_template = env.get_template('entities_raw_init.jinja2')

    entities_path = _os.path.join(target_path, 'entities')
    entities_raw_path = _os.path.join(entities_path, 'raw')

    _utils.create_path(entities_path)
    _utils.create_path(entities_raw_path)

    for entity in entities_data:
        _utils.create_file(
            _os.path.join(entities_path, entity['name_snake_case'] + '.py'),
            format_source(entity_template.render(entity=entity)),
            overwrite=force_overwrite,
        )

        _utils.create_file(
            _os.path.join(entities_raw_path, entity['name_snake_case'] + '_raw.py'),
            format_source(entity_raw_template.render(entity=entity)),
            overwrite=True
        )

    _utils.create_file(
        _os.path.join(entities_path, '__init__.py'),
        format_source(entities_init_template.render(entities=entities_data)),
        overwrite=True,
    )

    _utils.create_file(
        _os.path.join(entities_raw_path, '__init__.py'),
        format_source(entities_raw_init_template.render(entities=entities_data)),
        overwrite=True
    )





# -----
# ----- Utility -----
# -----


def format_source(content: str) -> str:
    return _autopep8.fix_code(content)


def read_data(file_path: str) -> dict:
    with open(file_path) as f:
        result = _json.load(f)
    return result


def __extract_parameters(query_parameters: dict) -> _List[_Dict[str, str]]:
    result = []
    for name, parameter_type in query_parameters.items():
        if name:
            default_value = None
            if name == 'designVersion':
                default_value = 'None'

            self_field = False
            if name == 'languageKey':
                self_field = True

            result.append({
                'name': name,
                'name_snake_case': _utils.append_underscore_if_keyword(_utils.convert_camel_to_snake_case(name)),
                'type': 'str' if parameter_type == 'none' else parameter_type,
                'default_value': default_value,
                'self_field': self_field,
            })
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
    for property_name in property_names:
        if property_name and property_name[:2] == 'Id':
            return property_name
    return None


def __get_endpoint_raw_parameter_definitions(parameters: _List[dict]) -> _List[str]:
    result = []
    for parameter in parameters:
        param_def = ''
        if parameter['type']:
            param_def = f'{parameter["name_snake_case"]}: {parameter["type"]}'
            default_value = parameter.get('default_value')
            if default_value:
                param_def += f' = {default_value}'
        if param_def:
            result.append(param_def)
    return result


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
                if result[1]:  # At least 1 known entity type has been found
                    break
                else:
                    result = (parent_tag_name, None)
    return result