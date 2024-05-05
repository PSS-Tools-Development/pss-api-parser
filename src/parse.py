import base64 as _base64
from datetime import datetime as _datetime
import json as _json
import os as _os
import re as _re
from typing import Any as _Any
from typing import Dict as _Dict
from typing import List as _List
from typing import Set as _Set
from typing import Union as _Union
from xml.etree import ElementTree as _ElementTree
import zlib as _zlib

from contexttimer import Timer as _Timer
from mitmproxy.http import HTTPFlow as _HTTPFlow
from mitmproxy.io import FlowReader as _FlowReader

from . import utils as _utils
from .flowdetails import PssFlowDetails as _PssFlowDetails
from .objectstructure import PssObjectStructure as _PssObjectStructure

# ----- Constants and type definitions -----

ApiStructure = _Dict[str, _Dict[str, _Union[_List[_PssFlowDetails], _List[_PssObjectStructure]]]]
ApiStructureDict = _Dict[str, 'ApiStructureDict']

__PSS_BOOL_VALUES = ('true', 'false', 'True', 'False')

__RX_PARAMETER_CHECK: _re.Pattern = _re.compile('\d.*', )

TYPE_ORDER_LOOKUP: _Dict[str, int] = {
    'str': 5,
    'float': 4,
    'int': 3,
    'bool': 2,
    'datetime': 1,
    None: 0,
}


# ----- Public Functions -----

def merge_object_structures(structure1: _PssObjectStructure, structure2: _PssObjectStructure) -> _PssObjectStructure:
    if not structure1:
        return structure2
    if not structure2:
        return structure1
    if structure1.object_type_name != structure2.object_type_name:
        raise Exception('object type names do not match.')
    properties = merge_type_dictionaries(structure1.properties, structure2.properties)
    return _PssObjectStructure(structure1.object_type_name, properties)


def organize_flows(extracted_flow_details: _List[_PssFlowDetails]) -> ApiStructure:
    sorted_flows = sorted(extracted_flow_details, key=lambda x: f'{x.service}{x.endpoint}')
    result: ApiStructure = {}
    for flow_details in sorted_flows:
        result.setdefault(flow_details.service, {}).setdefault(flow_details.endpoint, []).append(flow_details)
    return result


def parse_flows_file(file_path: str, verbose: bool = False) -> ApiStructure:
    """
    Returns a dictionary with the parsed services and endpoints.
    """
    print(f'Reading file: {file_path}')

    with _Timer() as timer:
        flows = sorted(__read_flows_from_file(file_path), key=lambda x: str(x))
        total_flow_count = len(flows)
        if verbose:
            print(f'Extracted {total_flow_count} flow details in: {timer.elapsed}')

        object_structures = __get_object_structures_from_flows(flows)
        for object_structure in object_structures.values():
            if 'none' in object_structure.properties.values():
                i = 0
        object_count = len(object_structures)
        if verbose:
            print(f'Extracted {object_count} entity types in: {timer.elapsed}')

        all_organized_flows = organize_flows(flows)
        singularized_flows = singularize_flows(all_organized_flows)
        if verbose:
            print(f'Merged flows and extracted {len(singularized_flows)} different PSS API endpoints in: {timer.elapsed}')

        organized_flows = organize_flows(singularized_flows)
        if verbose:
            print(f'Ordered flows according to services and endpoints in: {timer.elapsed}')

        result = {
            'endpoints': organized_flows,
            'entities': sorted(list(object_structures.values()), key=lambda x: x.object_type_name),
        }

        return result


def singularize_entities(organized_flows: ApiStructure, second_overrides_first: bool = False) -> _Set[_PssObjectStructure]:
    result: _Set[_PssFlowDetails] = set()
    for _, endpoints in organized_flows.items():
        for _, endpoint_flows in endpoints.items():
            merged_flow = endpoint_flows[0]
            if len(endpoint_flows) > 1:
                for flow2 in endpoint_flows[1:]:
                    merged_flow = merge_flows(merged_flow, flow2, second_overrides_first=second_overrides_first)
            result.add(merged_flow)
    return result


def singularize_flows(organized_flows: ApiStructure, second_overrides_first: bool = False) -> _Set[_PssFlowDetails]:
    result: _Set[_PssFlowDetails] = set()
    for _, endpoints in organized_flows.items():
        for _, endpoint_flows in endpoints.items():
            merged_flow = endpoint_flows[0]
            if len(endpoint_flows) > 1:
                for flow2 in endpoint_flows[1:]:
                    merged_flow = merge_flows(merged_flow, flow2, second_overrides_first=second_overrides_first)
            result.add(merged_flow)
    return result


def store_structure_json(file_path: str, flow_details: ApiStructure, compressed: bool = True) -> None:
    flow_details_dicts = __convert_api_structured_flows_to_dict(flow_details)
    if compressed:
        indent = None
        separators = (',', ':')
    else:
        indent = 2
        separators = (',', ': ')
    with open(file_path, 'w') as fp:
        _json.dump(flow_details_dicts, fp, indent=indent, separators=separators)


# ----- Private Functions -----

def __convert_api_structured_flows_to_dict(flows: ApiStructure) -> ApiStructureDict:
    result = {}
    for service, endpoints in flows.get('endpoints', {}).items():
        for endpoint, flow_details in endpoints.items():
            result.setdefault('endpoints', {}).setdefault(service, {})[endpoint] = dict(flow_details[0])
    result['entities'] = {object_structure.object_type_name: object_structure.properties for object_structure in flows.get('entities', [])}
    result = _utils.get_ordered_dict(result)
    return result


def __convert_flow_to_dict(flow: _HTTPFlow) -> _utils.NestedDict:
    result = {}
    result['method'] = flow.request.method  # GET/POST
    if '?' in flow.request.path:
        path, query_string = flow.request.path.split('?')
    else:
        path, query_string = (flow.request.path, None)

    result['service'], result['endpoint'] = path.split('/')[1:]

    result['query_parameters'] = {}
    if query_string:
        for param in query_string.split('&'):
            split_param = param.split('=')
            if split_param[0]:
                if len(split_param) == 1:
                    # Check for missing '=' and attempt to split param name and value
                    param_value = __RX_PARAMETER_CHECK.search(split_param[0])
                    value_span = param_value.span()
                    param_name = split_param[0][:value_span[0]]
                    split_param = [param_name, split_param[0][value_span[0]:value_span[1]]]

                if len(split_param) > 1:
                    result['query_parameters'][split_param[0]] = __determine_data_type(split_param[1], split_param[0])
                else:
                    result['query_parameters'][split_param[0]] = None

    result['content'] = flow.request.content.decode('utf-8') or None
    result['content_structure'] = {}
    result['content_type'] = ''

    if result['method'] == 'POST' and result['content']:
        try:
            result['content_structure'] = __convert_xml_to_dict(_ElementTree.fromstring(result['content']))
            result['content_type'] = 'xml'
        except:
            pass
        if not result.get('content_type'):
            try:
                result['content_structure'] = __convert_json_to_dict(_json.loads(result['content']))
                result['content_type'] = 'json'
            except:
                pass

    result['content_parameters'] = {}
    if result['content_structure']:
        if result['content_type'] == 'json':
            result['content_parameters'] = __get_parameters_from_content_json(result['content_structure'])
    result['response'] = flow.response.text or None
    result['response_structure'] = {}
    result['response_gzipped'] = False
    if result['response']:
        converted = False
        try:
            result['response_structure'] = __convert_xml_to_dict(_ElementTree.fromstring(result['response']))
            converted = True
        except _ElementTree.ParseError:
            pass

        if not converted:
            base64_decoded_content = _base64.b64decode(flow.response.content)
            unzipped_content = _zlib.decompress(base64_decoded_content, _zlib.MAX_WBITS|32)
            decoded_content = unzipped_content.decode('utf-8')
            result['response_structure'] = __convert_xml_to_dict(_ElementTree.fromstring(decoded_content))
            result['response_gzipped'] = True

    result['original_flow'] = flow
    return result


def __convert_json_to_dict(loaded_json: _utils.NestedDict) -> _utils.NestedDict:
    if not loaded_json:
        return {}

    result = {}
    for key, value in loaded_json.items():
        if isinstance(value, dict):
            result[key] = __convert_json_to_dict(value)
        else:
            result[key] = __determine_data_type(value)
    return result


def __convert_xml_to_dict(root: _ElementTree.Element) -> _utils.NestedDict:
    if root is None:
        return {}

    result = {}
    if root.attrib:
        result['properties'] = {key: __determine_data_type(value, key) for key, value in root.attrib.items()}
    for child in root:
        child_dict = __convert_xml_to_dict(child)
        if child.tag in result:
            result[child.tag]['properties'] = merge_type_dictionaries(result[child.tag]['properties'], child_dict[child.tag]['properties'])
        else:
            result[child.tag] = child_dict[child.tag]
    return {root.tag: result}


def __determine_data_type(value: _Any, property_name: str = None) -> str:
    if value is None:
        return None

    if isinstance(value, str):
        int_value = None
        float_value = None

        try:
            float_value = float(value)
        except:
            pass

        try:
            int_value = int(value)
        except:
            pass

        if int_value is not None and float_value is not None:
            try:
                float_int_value = float(int_value)
            except OverflowError:  # int is too large to be converted to float, could be a bit-mask
                return 'str'

            if float_int_value == float_value:
                return 'int'
            else:
                return 'float'
        elif int_value is not None:
            return 'int'
        elif float_value is not None:
            return 'float'

        if value.lower() in __PSS_BOOL_VALUES:
            return 'bool'

        try:
            _utils.parse_pss_datetime(value)
            return 'datetime'
        except:
            pass
        
        if value:
            return 'str'
        else:
            return None
    elif isinstance(value, bool):
        return 'bool'
    elif isinstance(value, float):
        return 'float'
    elif isinstance(value, int):
        return 'int'
    elif isinstance(value, _datetime):
        return 'datetime'


def __get_object_structures_from_response_structure(response_structure: _utils.NestedDict) -> _Dict[str, _List[_PssObjectStructure]]:
    result: _Dict[str, _List[_PssObjectStructure]] = {}
    for key, value in response_structure.items():
        if isinstance(value, dict):
            properties = value.pop('properties', None)
            if properties:
                if 'version' in properties:
                    value['properties'] = properties
                else:
                    for child in response_structure[key].keys():
                        properties[child] = child
                    result[key] = _PssObjectStructure(key, properties)
            result.update(__get_object_structures_from_response_structure(value))
    return result


def __get_object_structures_from_flows(flows: _List[_PssFlowDetails]) -> _Dict[str, _PssObjectStructure]:
    result: _Dict[str, _PssObjectStructure] = {}
    for flow in flows:
        current_object_structures = __get_object_structures_from_response_structure(flow.response_structure)
        for object_name, object_structure in current_object_structures.items():
            result[object_name] = merge_object_structures(object_structure, result.get(object_name))
            
    return result


def __get_parameters_from_content_json(content: _utils.NestedDict) -> _Dict[str, str]:
    result = {}
    for key, value in content.items():
        if isinstance(value, dict):
            result.update(__get_parameters_from_content_json(value))
        else:
            result[key] = value
    return result


def merge_flows(flow1: _PssFlowDetails, flow2: _PssFlowDetails, second_overrides_first: bool = False) -> _PssFlowDetails:
    query_parameters = merge_type_dictionaries(flow1.query_parameters, flow2.query_parameters, second_overrides_first=second_overrides_first)
    content_structure = merge_type_dictionaries(flow1.content_structure, flow2.content_structure, second_overrides_first=second_overrides_first)
    content_parameters = merge_type_dictionaries(flow1.content_parameters, flow2.content_parameters, second_overrides_first=second_overrides_first)
    response_structure = merge_type_dictionaries(flow1.response_structure, flow2.response_structure, second_overrides_first=second_overrides_first)

    result = {
        'content_parameters': content_parameters,
        'content_structure': content_structure,
        'content_type': flow2.content_type or flow1.content_type if second_overrides_first else flow1.content_type or flow2.content_type,
        'endpoint': flow2.endpoint or flow1.endpoint if second_overrides_first else flow1.endpoint or flow2.endpoint,
        'method': flow2.method or flow1.method if second_overrides_first else flow1.method or flow2.method,
        'query_parameters': query_parameters,
        'response_gzipped':  (flow2.response_gzipped if second_overrides_first else flow1.response_gzipped or flow2.response_gzipped) or False,
        'response_structure': response_structure,
        'service': flow2.service or flow1.service if second_overrides_first else flow1.service or flow2.service,
        'original_flow': flow2.original_flow or flow1.original_flow if second_overrides_first else flow1.original_flow or flow2.original_flow
    }
    return _PssFlowDetails(result)


def merge_type_dictionaries(d1: dict, d2: dict, second_overrides_first: bool = False) -> dict:
    if d1 and not d2:
        return dict(d1)
    if not d1 and d2:
        return dict(d2)
    
    result = {}
    result_names = set(d1.keys()).union(set(d2.keys()))
    for name in result_names:
        type1 = d1.get(name)
        type2 = d2.get(name)
        if type1 is None:
            result[name] = type2
        elif type2 is None:
            result[name] = type1
        elif isinstance(type1, dict) and isinstance(type2, dict):
            result[name] = merge_type_dictionaries(type1, type2)
        elif isinstance(type1, dict):
            result[name] = type1
        elif isinstance(type2, dict):
            result[name] = type2
        elif not isinstance(type1, str) or not isinstance(type2, str):
            pass
        elif second_overrides_first:
            result[name] = type2
        else:
            type1_value = TYPE_ORDER_LOOKUP.get(type1, 100)
            type2_value = TYPE_ORDER_LOOKUP.get(type2, 100)
            if type1_value >= type2_value:
                result[name] = type1
            else:
                result[name] = type2
    return result


def __read_flows_from_file(file_path: str) -> _List[_PssFlowDetails]:
    if not _os.path.isfile(file_path):
        raise FileNotFoundError(f'The specified file could not be found at: {file_path}')

    flow_details: _List[_PssFlowDetails] = []

    with open(file_path, 'rb') as fp:
        flow_reader: _FlowReader = _FlowReader(fp)
        flow_details = [_PssFlowDetails(__convert_flow_to_dict(recorded_flow)) for recorded_flow in flow_reader.stream()]

    blacklisted_services = _utils.read_json('src/blacklisted_services.json')
    blacklisted_endpoints = _utils.read_json('src/blacklisted_endpoints.json')
    result = [flow for flow in flow_details if flow.service not in blacklisted_services and not any(flow.endpoint.startswith(endpoint) for endpoint in blacklisted_endpoints)]
    return result
