import json as _json
from typing import Dict as _Dict
from typing import List as _List
from typing import Union as _Union

from . import parse as _parse
from .flowdetails import PssFlowDetails as _PssFlowDetails
from .objectstructure import PssObjectStructure as _PssObjectStructure


ApiStructure = _Dict[str, _Dict[str, _Union[_List[_PssFlowDetails], _List[_PssObjectStructure]]]]
ApiOrganizedFlowsDict = _Dict[str, "ApiOrganizedFlowsDict"]
NestedDict = _Dict[str, _Union[str, "NestedDict"]]


def apply_overrides(structure: ApiStructure, overrides: ApiStructure) -> ApiStructure:
    result = {
        "endpoints": override_organized_flows(structure.get("endpoints"), overrides.get("endpoints")),
        "entities": override_object_structures(structure.get("entities"), overrides.get("entities")),
    }
    return result


def override_organized_flows(flows: ApiStructure, overrides: ApiStructure) -> ApiStructure:
    if flows and not overrides:
        return flows
    if not flows and overrides:
        return overrides

    result = dict(flows)

    for service, endpoints in overrides.items():
        if service in result.keys():
            for endpoint, flow_details in endpoints.items():
                if endpoint in result[service]:
                    result.setdefault(service, {})[endpoint] = [
                        _parse.merge_flows(
                            flows[service][endpoint][0],
                            flow_details[0],
                            second_overrides_first=True,
                        )
                    ]
                else:
                    result.setdefault(service, {})[endpoint] = flow_details
        else:
            result[service] = endpoints

    return result


def override_object_structures(object_structures: _List[_PssObjectStructure], overrides: _List[_PssObjectStructure]) -> _List[_PssObjectStructure]:
    objects_dict = {object_structure.object_type_name: object_structure for object_structure in object_structures}
    overrides_dict = {object_structure.object_type_name: object_structure for object_structure in overrides}

    object_structure_names = sorted(list(set(objects_dict.keys()).union(set(overrides_dict.keys()))))
    result = []
    for object_name in object_structure_names:
        object_1 = objects_dict.get(object_name)
        object_2 = overrides_dict.get(object_name)
        if object_1 and object_2:
            result.append(
                _PssObjectStructure(
                    object_1.object_type_name,
                    _parse.merge_type_dictionaries(
                        object_1.properties,
                        object_2.properties,
                        second_overrides_first=True,
                    ),
                )
            )
        elif object_1:
            result.append(object_1)
        elif object_2:
            result.append(object_2)

    return result


def convert_entities_dict_to_object_structures(
    entities: _Dict[str, _Dict[str, str]],
) -> _List[_PssObjectStructure]:
    result = {_PssObjectStructure(entity_name, properties) for entity_name, properties in entities.items()}
    return result


def convert_structure_dict_to_organized_flows(
    organized_dict: ApiOrganizedFlowsDict,
) -> ApiStructure:
    result: ApiStructure = {}
    for service, endpoints in organized_dict["endpoints"].items():
        for endpoint, flow_dict in endpoints.items():
            result.setdefault(service, {}).setdefault(endpoint, []).append(_PssFlowDetails(flow_dict))
    return result


def merge_organized_flows(flows_1: ApiStructure, flows_2: ApiStructure) -> ApiStructure:
    merged_flows: ApiStructure = {}
    for service_1, endpoints_1 in flows_1.items():
        if service_1 in flows_2.keys():
            for endpoint_1, flow_details_1 in endpoints_1.items():
                if endpoint_1 in flows_2[service_1]:
                    merged_flows.setdefault(service_1, {}).setdefault(endpoint_1, []).extend(flow_details_1)
                    merged_flows.setdefault(service_1, {}).setdefault(endpoint_1, []).extend(flows_2[service_1][endpoint_1])
                else:
                    merged_flows.setdefault(service_1, {})[endpoint_1] = flow_details_1
        else:
            merged_flows[service_1] = endpoints_1

    for service_2, endpoints_2 in flows_2.items():
        if service_2 in flows_1.keys():
            for endpoint_2, flow_details_2 in endpoints_2.items():
                if endpoint_2 in flows_1[service_2]:
                    merged_flows.setdefault(service_2, {}).setdefault(endpoint_2, []).extend(flow_details_2)
                    merged_flows.setdefault(service_2, {}).setdefault(endpoint_2, []).extend(flows_1[service_2][endpoint_2])
                else:
                    merged_flows.setdefault(service_2, {})[endpoint_2] = flow_details_2
        else:
            merged_flows[service_2] = endpoints_2

    result = _parse.organize_flows(_parse.singularize_flows(merged_flows))
    return result


def merge_object_structures(
    object_structures_1: _List[_PssObjectStructure],
    object_structures_2: _List[_PssObjectStructure],
    override_object_structures_1: bool = False,
) -> _List[_PssObjectStructure]:
    if object_structures_1 and not object_structures_2:
        return list(object_structures_1)
    if not object_structures_1 and object_structures_2:
        return list(object_structures_2)

    object_structures: _Dict[str, _List[_PssObjectStructure]] = {}
    for object_structure_1 in object_structures_1:
        object_structures.setdefault(object_structure_1.object_type_name, []).append(object_structure_1)
    for object_structure_2 in object_structures_2:
        object_structures.setdefault(object_structure_2.object_type_name, []).append(object_structure_2)

    result: _List[_PssObjectStructure] = []
    for _, entity_structures in object_structures.items():
        entity_structure = entity_structures[0]
        for merge_with in entity_structures[1:]:
            entity_structure = _parse.merge_object_structures(entity_structure, merge_with)
        result.append(entity_structure)

    return result


def merge_structure_jsons(file_path_1: str, file_path_2: str) -> ApiStructure:
    structure_1 = read_structure_json(file_path_1)
    structure_2 = read_structure_json(file_path_2)
    return merge_api_structures(structure_1, structure_2)


def merge_api_structures(structure_1: ApiStructure, structure_2: ApiStructure, overrides: ApiStructure = None) -> ApiStructure:
    if structure_1 and not structure_2:
        return dict(structure_1)
    if not structure_1 and structure_2:
        return dict(structure_2)
    result = {
        "endpoints": merge_organized_flows(structure_1["endpoints"], structure_2["endpoints"]),
        "entities": merge_object_structures(structure_1["entities"], structure_2["entities"]),
    }
    return result


def read_structure_json(file_path: str) -> ApiStructure:
    with open(file_path, "r") as fp:
        flows = _json.load(fp)
    result = {
        "endpoints": convert_structure_dict_to_organized_flows(flows),
        "entities": convert_entities_dict_to_object_structures(flows.get("entities")),
    }
    return result
