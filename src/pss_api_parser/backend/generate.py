import json as _json
import os as _os
import string as _string
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from jinja2 import Environment as _Environment
from jinja2 import PackageLoader as _PackageLoader

from . import enums as _enums
from . import parse as _parse
from . import utils as _utils


BUILTIN_TYPES = list(_parse.TYPE_ORDER_LOOKUP.keys())

IMPORTS = {
    "datetime": "from datetime import datetime as _datetime",
    "List": "from typing import List as _List",
    "Tuple": "from typing import Tuple as _Tuple",
}

FIX_ENTITY_PROPERTY_TYPES = ["datetime"]

FORCED_ENUMS_GENERATION = ["DeviceType"]

POSSIBLE_ENUM_TYPES = [
    "int",
    "str",
]

RESERVED_PROPERTY_NAMES = ["id"]


# -----
# ----- Prepare -----
# -----


def filter_enums_data(
    enums_data: Dict[str, _enums.EnumDefinition],
    services_data: List[dict],
    entities_data: List[dict],
) -> Dict[str, _enums.EnumDefinition]:
    potential_enum_names = []
    for service in services_data:
        for endpoint in service["endpoints"]:
            for parameter in endpoint["parameters"]:
                potential_enum_names.append(_utils.convert_snake_to_camel_case(_utils.convert_camel_to_snake_case(parameter["name"])))

    for entity in entities_data:
        for property in entity["properties"]:
            potential_enum_names.append(property["name"])
            property_name_lower = property["name"].lower()
            if property_name_lower[:4] == "flag" or property_name_lower[-5:] == "flags":
                flag_enum_name = f'{entity["name"]}Flag'
                potential_enum_names.append(flag_enum_name)
                potential_enum_names.append(f"{flag_enum_name}s")
                potential_enum_names.append(f"{flag_enum_name}Type")
                potential_enum_names.append(f"{flag_enum_name}sType")

    potential_enum_names += FORCED_ENUMS_GENERATION
    potential_enum_names = set(potential_enum_names)

    parsed_enum_names = set(enums_data.keys())
    used_enum_names = potential_enum_names.intersection(potential_enum_names, parsed_enum_names)

    result = {key: value for key, value in enums_data.items() if key in used_enum_names}
    return result


def prepare_parsed_api_data(parsed_api_data: dict, cacheable_endpoints: dict) -> Tuple[List[dict], List[dict]]:
    known_entity_names = set(parsed_api_data["entities"].keys())
    services = __prepare_services_data(parsed_api_data["endpoints"], known_entity_names, cacheable_endpoints)
    entities = __prepare_entities_data(parsed_api_data["entities"])
    return services, entities


def prepare_parsed_enums_data(parsed_enums_data: Dict[str, _enums.EnumDefinition]) -> list:
    result = []
    ignore_value_names = ["None", "Unknown"]
    int_enum_types = (_enums.TYPE_INT_ENUM, _enums.TYPE_INT_FLAG)
    for enum_name in sorted(parsed_enums_data.keys()):
        enum_definition = {
            "name": enum_name,
            "name_snake_case": _utils.convert_camel_to_snake_case(enum_name),
            "type": parsed_enums_data[enum_name]["type"],
        }

        if parsed_enums_data[enum_name]["type"] in int_enum_types:
            sorted_enum_values = sorted(
                parsed_enums_data[enum_name]["values"].items(),
                key=lambda item: item[1] or 0,
            )
        elif parsed_enums_data[enum_name]["type"] == _enums.TYPE_STR_ENUM:
            sorted_enum_values = sorted(
                parsed_enums_data[enum_name]["values"].items(),
                key=lambda item: item[1] or "",
            )
        enum_value_names = [key for key, value in sorted_enum_values if value not in ignore_value_names]

        enum_definition["enum_values"] = []
        for value_name in enum_value_names:
            if value_name != "None":
                enum_definition["enum_values"].append(
                    {
                        "name": value_name,
                        "name_upper": _utils.convert_camel_to_snake_case(value_name).upper(),
                        "value": parsed_enums_data[enum_name]["values"][value_name],
                    }
                )
            else:
                value = parsed_enums_data[enum_name]["values"][value_name]
                if value is None:
                    if parsed_enums_data[enum_name]["type"] == _enums.TYPE_STR_ENUM:
                        value = "None"
                    else:
                        value = 0

                enum_definition["enum_values"].append(
                    {
                        "name": "None",
                        "name_upper": "NONE",
                        "value": value,
                    }
                )
        result.append(enum_definition)
    return result


def __find_entity_name_for_property_type(property_type: str, entity_names: Iterable[str]) -> Tuple[str, bool]:
    """
    Returns the matching entity name and if it's likely to be a collection of that entity.
    """
    likely_match = property_type
    likely_collection = False

    if property_type.endswith("s"):
        likely_match = likely_match[:-1]
        likely_collection = True

    if likely_match in entity_names:
        return (likely_match, likely_collection)

    if property_type in entity_names:
        return (property_type, False)

    return (None, None)


def __find_enum_name_for_property_name(property_name: str, entity_name: str, enum_names: Iterable[str]) -> Optional[str]:
    """
    Returns the matching entity name or None if none matching could be found.
    """
    if property_name in enum_names:
        return property_name

    if property_name.lower().startswith("flag"):
        likely_flag_matches = (
            f"{entity_name}Flag",
            f"{entity_name}Flags",
            f"{entity_name}FlagType",
            f"{entity_name}FlagsType",
        )

        for likely_match in likely_flag_matches:
            if likely_match in enum_names:
                return likely_match

    return None


def __generate_custom_enums_data() -> list:
    return [
        {
            "name": "LanguageKey",
            "name_snake_case": "language_key",
            "type": "str",
            "enum_values": [
                {
                    "name": "German",
                    "name_upper": "GERMAN",
                    "value": "de",
                },
                {
                    "name": "English",
                    "name_upper": "ENGLISH",
                    "value": "en",
                },
                {
                    "name": "French",
                    "name_upper": "FRENCH",
                    "value": "fr",
                },
            ],
        },
    ]


def __prepare_entities_data(entities_data: dict) -> list:
    result = []
    for entity_name, entity_properties in entities_data.items():
        properties = []
        property_names = []
        entity_imports = set()
        for property_name, property_type in entity_properties.items():
            property_type = property_type or "str"
            is_entity_type = False
            is_built_in_type = property_type in BUILTIN_TYPES
            is_collection = False
            property_typehint = property_type
            if not is_built_in_type:
                property_type, is_collection = __find_entity_name_for_property_type(property_type, entities_data.keys())
                if not property_type:
                    continue  # Skip properties that are neither of an builtin type nor of a known entity type
                is_entity_type = True
                entity_imports.add(property_type)
                property_typehint = property_type
            if property_type in FIX_ENTITY_PROPERTY_TYPES:
                property_typehint = f"_{property_type}"
            if is_entity_type:
                property_typehint = f'entities.{property_typehint.strip("_")}'
            property_names.append(property_name)

            property_name_snake_case = _utils.convert_camel_to_snake_case(property_name)
            if property_name_snake_case in RESERVED_PROPERTY_NAMES:
                property_name_snake_case += "_"
            properties.append(
                {
                    "builtin": is_built_in_type,
                    "is_collection": is_collection,
                    "name": property_name,
                    "name_snake_case": property_name_snake_case,
                    "type": property_type,
                    "typehint": property_typehint,
                }
            )
        id_property = __find_id_property(property_names, entity_name)
        id_property_name = _utils.convert_camel_to_snake_case(id_property)
        if id_property_name in RESERVED_PROPERTY_NAMES:
            id_property_name += "_"
        name_property = __find_name_property(property_names, entity_name)

        result.append(
            {
                "base_class_name": "EntityWithIdBase" if id_property else "EntityBase",
                "entity_imports": entity_imports,
                "id_property_name": id_property_name,
                "name": entity_name,
                "name_property_name": _utils.convert_camel_to_snake_case(name_property),
                "name_snake_case": _utils.convert_camel_to_snake_case(entity_name),
                "properties": properties,
                "xml_node_name": entity_name,
            }
        )
    result.sort(key=lambda d: d["name"])
    return result


def __prepare_services_data(endpoints_data: dict, known_entity_names: set, cacheable_endpoints: dict) -> List[dict]:
    result = []
    for service_name, endpoints in endpoints_data.items():
        service_imports = {"List", "Tuple"}
        service_cacheable_endpoints = cacheable_endpoints.get(service_name, {})
        has_cacheable_endpoints = len(service_cacheable_endpoints) > 0

        service = {
            "endpoints": [],
            "entity_types": [],
            "imports": [],
            "is_cacheable": has_cacheable_endpoints,
            "name": service_name,
            "name_snake_case": _utils.convert_camel_to_snake_case(service_name),
            "raw_endpoints": [],
        }

        endpoint_max_versions = {}

        for endpoint_name, endpoint_definition in endpoints.items():
            endpoint_name_without_version = endpoint_name.rstrip(_string.digits)
            name_snake_case = _utils.convert_camel_to_snake_case(endpoint_name)
            name_snake_case_without_version = _utils.convert_camel_to_snake_case(endpoint_name_without_version)
            if name_snake_case != name_snake_case_without_version:
                version = int(name_snake_case[len(name_snake_case_without_version) - len(name_snake_case) :].strip("_"))
            else:
                version = 1
            xml_parent_tag_name, return_types = __get_return_type(endpoint_definition["response_structure"], known_entity_names)
            parameters = __extract_parameters(endpoint_definition["query_parameters"] or endpoint_definition.get("content_parameters", {}))
            service_imports.update(parameter["type"] for parameter in parameters)
            endpoint_data_version_property_name = service_cacheable_endpoints.get(endpoint_name_without_version, None)

            parameter_definitions = []
            parameter_definitions_with_default_value = []
            parameter_raw_definitions = []
            raw_endpoint_call_parameters = []
            for parameter in parameters:
                type_ = parameter["type"]
                if type_ in IMPORTS:
                    parameter["type"] = f"_{type_}"

                parameter_name = parameter["name_snake_case"]
                param_def = f'{parameter_name}: {parameter["type"]}'
                parameter_raw_definitions.append(param_def)

                if parameter["self_field"]:
                    raw_endpoint_call_parameters.append(f"self.{parameter_name}")
                else:
                    default_value = parameter.get("default_value")
                    if default_value:
                        parameter_definitions_with_default_value.append(f"{param_def} = {default_value}")
                    else:
                        parameter_definitions.append(param_def)

                    raw_endpoint_call_parameters.append(parameter_name)

            parameter_definitions.extend(parameter_definitions_with_default_value)

            entity_types = [f"(_{return_type[0]}, '{return_type[1]}', {return_type[2]})" for return_type in return_types]
            entity_types_str = ", ".join(entity_types)
            return_type = __get_return_type_for_python(return_types)

            service["raw_endpoints"].append(
                {
                    "base_path_name": name_snake_case.upper(),
                    "content_structure": _json.dumps(endpoint_definition["content_structure"], separators=(",", ":")),
                    "content_type": endpoint_definition["content_type"],
                    "data_version_property_name": endpoint_data_version_property_name,
                    "entity_tags": "",
                    "entity_types_str": f'({entity_types_str}{"," if len(entity_types) == 1 else ""})',
                    "method": endpoint_definition["method"],
                    "name": endpoint_name,
                    "name_screaming_snake_case": name_snake_case.upper(),
                    "name_snake_case": name_snake_case,
                    "name_snake_case_without_version": name_snake_case_without_version,
                    "parameter_definitions": ", ".join(parameter_definitions),
                    "parameter_raw_definitions": ", ".join(parameter_raw_definitions),
                    "parameters": parameters,
                    "raw_endpoint_call_parameters": ", ".join(raw_endpoint_call_parameters),
                    "response_gzipped": endpoint_definition["response_gzipped"],
                    "return_type_str": return_type,
                    "version": version,
                    "xml_parent_tag_name": xml_parent_tag_name,
                }
            )

            endpoint_max_versions[name_snake_case_without_version] = max(endpoint_max_versions.get(name_snake_case_without_version, 0), version)

            if return_types:
                service["entity_types"].extend(return_type[0] for return_type in return_types)

        service["endpoints"] = [
            endpoint
            for endpoint in service["raw_endpoints"]
            if endpoint["version"] == endpoint_max_versions[endpoint["name_snake_case_without_version"]]
        ]

        for service_import in service_imports:
            if service_import in IMPORTS:
                service["imports"].append(IMPORTS[service_import])
        service["entity_types"] = sorted(list(set(service["entity_types"])))
        service["imports"] = sorted(list(set(service["imports"])))
        result.append(service)
    return result


# -----
# ----- Generate -----
# -----


def _generate_files_from_data(
    services_data: list,
    entities_data: list,
    enums_data: list,
    target_path: Path,
    force_overwrite: bool,
    target_language: _enums.ProgrammingLanguage,
) -> None:
    template_dir = f"templates/{target_language.template_dir()}"
    env = _Environment(
        loader=_PackageLoader("pss_api_parser", template_dir),
        trim_blocks=True,
    )

    if str(target_path)[-10:].lower() != "src/pssapi":
        target_path = target_path / "src/pssapi"
    if str(target_path)[-6:].lower() != "pssapi":
        target_path = target_path / "pssapi"

    _utils.create_path(target_path)

    __generate_services_files(services_data, target_path, env, force_overwrite)
    __generate_client_file(services_data, target_path, env, force_overwrite)
    __generate_entities_files(entities_data, target_path, env, force_overwrite)
    if enums_data:
        __generate_enums_files(enums_data, target_path, env, force_overwrite)

    __generate_fixed_files(target_path, env, force_overwrite)


def _format_files(target_path: Path):
    pass


def generate_source_code(
    parsed_api_data_file_path: Path | str,
    enums_data_file_path: Optional[Path | str],
    cacheable_endpoints_file_path: Optional[Path | str],
    target_path: Path | str,
    target_language: _enums.ProgrammingLanguage = _enums.ProgrammingLanguage.PYTHON,
    force_overwrite: bool = False,
) -> None:
    if force_overwrite is None:
        raise Exception("Parameter 'force_overwrite' must not be None!")
    parsed_api_data = read_data(parsed_api_data_file_path)
    cacheable_endpoints = read_data(cacheable_endpoints_file_path)
    services_data, entities_data = prepare_parsed_api_data(parsed_api_data, cacheable_endpoints)

    enums_data = read_data(enums_data_file_path) if enums_data_file_path else None
    if enums_data:
        filtered_enums_data = filter_enums_data(enums_data, services_data, entities_data)
        prepared_enums_data = prepare_parsed_enums_data(filtered_enums_data)
        custom_enums_data = __generate_custom_enums_data()

        all_enums_data = prepared_enums_data + custom_enums_data
    else:
        all_enums_data = None

    target_path = Path(target_path)
    _generate_files_from_data(
        services_data,
        entities_data,
        all_enums_data,
        target_path,
        force_overwrite,
        target_language,
    )
    _format_files(target_path)


def __generate_client_file(services_data: dict, target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    client_base_template = env.get_template("client_base.jinja2")
    client_template = env.get_template("client.jinja2")

    _utils.create_file(
        target_path / "client_base.py",
        client_base_template.render(services=services_data),
        overwrite=True,
    )

    _utils.create_file(
        target_path / "client.py",
        client_template.render(services=services_data),
        overwrite=force_overwrite,
    )


def __generate_constants_file(target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    constants_template = env.get_template("constants.jinja2")

    _utils.create_file(
        target_path / "constants.py",
        constants_template.render(),
        overwrite=force_overwrite,
    )


def __generate_core_file(target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    core_template = env.get_template("core.jinja2")

    _utils.create_file(
        _os.path.join(target_path, "core.py"),
        core_template.render(),
        overwrite=force_overwrite,
    )


def __generate_entities_files(entities_data: dict, target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    entity_template = env.get_template("entities/entity.jinja2")
    entity_base_template = env.get_template("entities/entity_base.jinja2")
    entities_init_template = env.get_template("entities/entities_init.jinja2")
    entity_raw_template = env.get_template("entities/entity_raw.jinja2")
    entity_base_raw_template = env.get_template("entities/entity_base_raw.jinja2")
    entities_raw_init_template = env.get_template("entities/entities_raw_init.jinja2")

    entities_path = target_path / "entities"
    _utils.create_path(entities_path)

    entities_raw_path = entities_path / "raw"
    _utils.create_path(entities_raw_path)

    for entity in entities_data:
        _utils.create_file(
            _os.path.join(entities_path, entity["name_snake_case"] + ".py"),
            entity_template.render(entity=entity),
            overwrite=force_overwrite,
        )

        _utils.create_file(
            _os.path.join(entities_raw_path, entity["name_snake_case"] + "_raw.py"),
            entity_raw_template.render(entity=entity),
            overwrite=True,
        )

    _utils.create_file(
        _os.path.join(entities_path, "__init__.py"),
        entities_init_template.render(entities=entities_data),
        overwrite=force_overwrite,
    )

    _utils.create_file(
        _os.path.join(entities_path, "entity_base.py"),
        entity_base_template.render(),
        overwrite=force_overwrite,
    )

    _utils.create_file(
        _os.path.join(entities_raw_path, "__init__.py"),
        entities_raw_init_template.render(entities=entities_data),
        overwrite=True,
    )

    _utils.create_file(
        _os.path.join(entities_raw_path, "entity_base_raw.py"),
        entity_base_raw_template.render(),
        overwrite=True,
    )


def __generate_enums_files(enums_data: list, target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    int_enum_template = env.get_template("enums/enum_int.jinja2")
    int_flag_template = env.get_template("enums/enum_int_flag.jinja2")
    str_enum_template = env.get_template("enums/enum_str.jinja2")
    enum_init_template = env.get_template("enums/enum_init.jinja2")

    enums_path = target_path / "enums"
    _utils.create_path(enums_path)

    for enum in enums_data:
        if enum["type"] == _enums.TYPE_INT_ENUM:
            template = int_enum_template
        elif enum["type"] == _enums.TYPE_INT_FLAG:
            template = int_flag_template
        else:
            template = str_enum_template
        _utils.create_file(
            _os.path.join(enums_path, enum["name_snake_case"] + ".py"),
            template.render(enum=enum),
            overwrite=force_overwrite,
        )

    _utils.create_file(
        _os.path.join(enums_path, "__init__.py"),
        enum_init_template.render(enums=enums_data),
        overwrite=force_overwrite,
    )


def __generate_fixed_files(target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    __generate_constants_file(target_path, env, force_overwrite)
    __generate_core_file(target_path, env, force_overwrite)
    __generate_pssapi_init_file(target_path, env, force_overwrite)
    __generate_utils_submodule(target_path, env, force_overwrite)
    __generate_types_file(target_path, env, force_overwrite)


def __generate_pssapi_init_file(target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    pssapi_init_template = env.get_template("pssapi_init.jinja2")

    _utils.create_file(
        _os.path.join(target_path, "__init__.py"),
        pssapi_init_template.render(),
        overwrite=force_overwrite,
    )


def __generate_services_files(services_data: dict, target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    service_template = env.get_template("services/service.jinja2")
    service_base_template = env.get_template("services/service_base.jinja2")
    services_init_template = env.get_template("services/services_init.jinja2")
    service_raw_template = env.get_template("services/service_raw.jinja2")
    services_raw_init_template = env.get_template("services/services_raw_init.jinja2")

    services_path = target_path / "services"
    _utils.create_path(services_path)

    services_raw_path = services_path / "raw"
    _utils.create_path(services_raw_path)

    for service in services_data:
        _utils.create_file(
            _os.path.join(services_path, service["name_snake_case"] + ".py"),
            service_template.render(service=service),
            overwrite=force_overwrite,
        )
        _utils.create_file(
            _os.path.join(services_raw_path, service["name_snake_case"] + "_raw.py"),
            service_raw_template.render(service=service),
            overwrite=True,
        )

    _utils.create_file(
        _os.path.join(services_path, "__init__.py"),
        services_init_template.render(services=services_data),
        overwrite=force_overwrite,
    )

    _utils.create_file(
        _os.path.join(services_path, "service_base.py"),
        service_base_template.render(),
        overwrite=force_overwrite,
    )

    _utils.create_file(
        _os.path.join(services_raw_path, "__init__.py"),
        services_raw_init_template.render(services=services_data),
        overwrite=True,
    )


def __generate_types_file(target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    types_template = env.get_template("types.jinja2")

    _utils.create_file(
        _os.path.join(target_path, "types.py"),
        types_template.render(),
        overwrite=force_overwrite,
    )


def __generate_utils_submodule(target_path: Path, env: _Environment, force_overwrite: bool) -> None:
    utils_init_template = env.get_template("utils/utils_init.jinja2")
    utils_datetime_template = env.get_template("utils/utils_datetime.jinja2")
    utils_parse_template = env.get_template("utils/utils_parse.jinja2")

    utils_path = target_path / "utils"
    _utils.create_path(utils_path)

    _utils.create_file(
        _os.path.join(utils_path, "__init__.py"),
        utils_init_template.render(),
        overwrite=force_overwrite,
    )

    _utils.create_file(
        _os.path.join(utils_path, "datetime.py"),
        utils_datetime_template.render(),
        overwrite=force_overwrite,
    )

    _utils.create_file(
        _os.path.join(utils_path, "parse.py"),
        utils_parse_template.render(),
        overwrite=force_overwrite,
    )


# -----
# ----- Utility -----
# -----


def read_data(file_path: Path | str) -> dict:
    with open(file_path) as f:
        result = _json.load(f)
    return result


def __extract_parameters(query_parameters: dict) -> List[Dict[str, str]]:
    result = []
    for name, parameter_type in query_parameters.items():
        if name:
            default_value = None
            if name == "designVersion":
                default_value = "None"

            self_field = False
            if name == "languageKey":
                self_field = True

            result.append(
                {
                    "name": name,
                    "name_snake_case": _utils.append_underscore_if_keyword(_utils.convert_camel_to_snake_case(name)),
                    "type": parameter_type or "str",
                    "default_value": default_value,
                    "self_field": self_field,
                }
            )
    return result


def __find_id_property(property_names: List[str], entity_name: str) -> Optional[str]:
    exact_id_name = f"{entity_name}Id"
    found_id_name = False

    for property_name in property_names:
        if property_name:
            if property_name == exact_id_name:
                return property_name
            found_id_name = found_id_name or property_name == "Id"
    if found_id_name:
        return "Id"
    return None


def __find_name_property(property_names: List[str], entity_name: str) -> Optional[str]:
    for property_name in property_names:
        if property_name and property_name[:2] == "Id":
            return property_name
    return None


def __get_endpoint_raw_parameter_definitions(parameters: List[dict]) -> List[str]:
    result = []
    for parameter in parameters:
        param_def = ""
        if parameter["type"]:
            param_def = f'{parameter["name_snake_case"]}: {parameter["type"]}'
            default_value = parameter.get("default_value")
            if default_value:
                param_def += f" = {default_value}"
        if param_def:
            result.append(param_def)
    return result


def __get_return_type(response_structure: dict, entity_names: List[str], parent_tag_name: str = None) -> Tuple[str, List[Tuple[str, str, bool]]]:
    """The return type will be determined by crawling through dict 'response_structure' until there's
    a match of tag name and any known entity_name. All matching tag names on that depth will
    be considered for the response type. If there's only one entity type, a list of that entity
    type will be returned. If there are multiple, the return type is a Tuple of those entity types.
    """

    if isinstance(response_structure, dict):
        child_types = []
        keys = list(response_structure.keys())
        entity_types = [key for key in keys if key in entity_names]
        if entity_types:
            child_types = [
                (
                    parent_tag_name,
                    [(entity_type, parent_tag_name, True) for entity_type in entity_types],
                )
            ]

        child_types.extend([__get_return_type(response_structure[key], entity_names, key) for key in keys if key not in entity_types])

        return_types = []
        for return_type in child_types:
            if return_type and return_type[0] and return_type[1]:
                return_parent_tag_name, entity_types = return_type
                # 0 -> entity name
                # 1 -> parent tag name
                # f'{entity_type[0]}s' == entity_type[1] -> isList
                entity_types = [
                    (
                        entity_type[0],
                        (entity_type[1] if f"{entity_type[0]}s" == entity_type[1] else entity_type[0]),
                        f"{entity_type[0]}s" == entity_type[1],
                    )
                    for entity_type in entity_types
                ]
                return_types.append((return_parent_tag_name, entity_types))

        if len(return_types) < 1:
            return (None, [])  # No return type
        elif len(return_types) == 1:
            return return_types[0]
        else:
            entity_types = [entity_type for _, return_type in return_types for entity_type in return_type]
            return (parent_tag_name, entity_types)
    return (None, [])


def __get_return_type_for_python(return_types: List[Tuple[str, str, bool]]) -> str:
    if not return_types:
        return ""

    result = []
    for entity_name, _parent_tag, isList in return_types:
        if isList:
            result.append(f"List[_{entity_name}]")
        else:
            result.append(f"_{entity_name}")
    if len(result) > 1:
        return f'Tuple[{", ".join(result)}]'
    else:
        return result[0]
