#!/usr/bin/env python3

import datetime
import json
import os.path
import sys
from timeit import default_timer as timer
from typing import Dict, List, Set
from xml.etree import ElementTree

from mitmproxy.http import HTTPFlow
from mitmproxy.flow import Flow
from mitmproxy.io import FlowReader, tnetstring

from flowdetails import PssFlowDetails, ResponseStructure


# ----- Constants and type definitions -----

API_ORGANIZED_FLOWS = Dict[str, Dict[str, List[PssFlowDetails]]]
API_ORGANIZED_FLOWS_DICT = Dict[str, 'API_ORGANIZED_FLOWS_DICT']

__TYPE_ORDER_LOOKUP: Dict[str, int] = {
    'float': 4,
    'int': 3,
    'bool': 2,
    'datetime': 1,
    'str': 0
}





# ----- Public Functions -----

def convert_organized_dicts_to_organized_flows(organized_dict: API_ORGANIZED_FLOWS_DICT) -> API_ORGANIZED_FLOWS:
    result: API_ORGANIZED_FLOWS = {}
    for service, endpoints in organized_dict.items():
        for endpoint, flow_dict in endpoints:
            result.setdefault(service, {}).setdefault(endpoint, []).append(PssFlowDetails(flow_dict))
    return result


def merge_organized_flows(flows1: API_ORGANIZED_FLOWS, flows2: API_ORGANIZED_FLOWS) -> API_ORGANIZED_FLOWS:
    merged_flows: API_ORGANIZED_FLOWS = {}
    for service1, endpoints1 in flows1.items():
        if service1 in flows2:
            for endpoint1, flow_details1 in endpoints1:
                if endpoint1 in flows2[service1]:
                    merged_flows.setdefault(service1, {}).setdefault(endpoint1, []).extend(flow_details1)
                    merged_flows.setdefault(service1, {}).setdefault(endpoint1, []).extend(flows2[service1][endpoint1])
                else:
                    merged_flows.setdefault(service1, {})[endpoint1] = flows1
        else:
            merged_flows[service1] = endpoints1

    result = __organize_flows(__singularize_flows(merged_flows))
    return result


def merge_structure_jsons(file_path1: str, file_path2: str) -> API_ORGANIZED_FLOWS:
    flows1, flows2 = (None, None)
    with open(file_path1, 'r') as fp:
        flows1 = json.load(fp)
    with open(file_path2, 'r') as fp:
        flows2 = json.load(fp)

    if flows1 == None:
        if flows2 == None:
            raise Exception(f'Reading the specified files failed.')
        else:
            return convert_organized_dicts_to_organized_flows(flows2)
    else:
        if flows2 == None:
            return convert_organized_dicts_to_organized_flows(flows1)

    return merge_organized_flows(
        convert_organized_dicts_to_organized_flows(flows1),
        convert_organized_dicts_to_organized_flows(flows2)
    )


def parse_flows_file(file_path: str, verbose: bool = False) -> API_ORGANIZED_FLOWS:
    """
    Returns the path to the created json file
    """
    print(f'Reading file: {file_path}')

    if verbose:
        start = timer()
    flows = __read_flows_from_file(file_path)
    total_flow_count = len(flows)
    organized_flows = __organize_flows(flows)
    if verbose:
        print(f'Extracted {total_flow_count} flow details in: {datetime.timedelta(seconds=(timer()-start))}')

    if verbose:
        start = timer()
    singularized_flows = __singularize_flows(organized_flows)
    if verbose:
        print(f'Merged flows and extracted {len(singularized_flows)} different PSS API endpoints in: {datetime.timedelta(seconds=(timer()-start))}')

    if verbose:
        start = timer()
    result = __organize_flows(singularized_flows)
    if verbose:
        print(f'Ordered flows according to services and endpoints in: {datetime.timedelta(seconds=(timer()-start))}')

    return result


def store_flow_details_as_json(file_path: str, flow_details: API_ORGANIZED_FLOWS) -> None:
    flow_details_dicts = __convert_api_structured_flows_to_dict(flow_details)
    with open(file_path, 'w') as fp:
        json.dump(flow_details_dicts, fp)





# ----- Private Functions -----

def __convert_api_structured_flows_to_dict(flows: API_ORGANIZED_FLOWS) -> API_ORGANIZED_FLOWS_DICT:
    result = {}
    for service, endpoints in flows.items():
        for endpoint, flow_details in endpoints.items():
            result.setdefault(service, {})[endpoint] = dict(flow_details[0])
    return result


def __convert_flow_to_dict(flow: HTTPFlow) -> dict:
    result = {}
    result['method'] = flow.request.method # GET/POST
    if '?' in flow.request.path:
        path, query_string = flow.request.path.split('?')
    else:
        path, query_string = (flow.request.path, None)

    result['service'], result['endpoint'] = path.split('/')[1:]

    result['query_parameters'] = {}
    if query_string:
        for param in query_string.split('&'):
            split_param = param.split('=')
            if len(split_param) > 1:
                result['query_parameters'][split_param[0]] = __determine_data_type(split_param[1])
            else:
                result['query_parameters'][split_param[0]] = None

    result['content'] = flow.request.content.decode('utf-8') or None
    result['content_structure'] = {}
    result['content_type'] = ''

    if result['method'] == 'POST' and result['content']:
        try:
            result['content_structure'] = __convert_xml_to_dict(ElementTree.fromstring(result['content']))
            result['content_type'] = 'xml'
        except:
            pass
        if 'content_type' not in result:
            try:
                result['content_structure'] = __convert_json_to_dict(json.loads(result['content']))
                result['content_type'] = 'json'
            except:
                pass

    result['response'] = flow.response.content.decode('utf-8') or None
    result['response_structure'] = {}
    if result['response']:
        result['response_structure'] = __convert_xml_to_dict(ElementTree.fromstring(result['response']))
    return result


def __convert_json_to_dict(loaded_json: ResponseStructure) -> ResponseStructure:
    if not loaded_json:
        return {}

    result = {}
    for key, value in loaded_json.items():
        if isinstance(value, dict):
            result[key] = __convert_json_to_dict(value)
        else:
            result[key] = __determine_data_type(value)
    return result


def __convert_xml_to_dict(root: ElementTree.Element) -> ResponseStructure:
    if root is None:
        return {}

    result = {
        'properties': {key: __determine_data_type(value) for key, value in root.attrib.items()} if root.attrib else []
    }
    for child in root:
        if child.tag not in result:
            child_dict = __convert_xml_to_dict(child)
            result[child.tag] = child_dict[child.tag]
    return {root.tag: result}


def __determine_data_type(value: str) -> str:
    if value:
        try:
            int(value)
            return 'int'
        except:
            pass

        try:
            float(value)
            return 'float'
        except:
            pass

        if value.lower() in ('true', 'false'):
            return 'bool'

        try:
            datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            return 'datetime'
        except:
            try:
                datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
                return 'datetime'
            except:
                pass

    return 'str'


def __merge_flows(flow1: PssFlowDetails, flow2: PssFlowDetails) -> PssFlowDetails:
    query_parameters = __merge_type_dictionaries(flow1.query_parameters, flow2.query_parameters)
    content_structure = __merge_type_dictionaries(flow1.content_structure, flow2.content_structure)
    response_structure = __merge_type_dictionaries(flow1.response_structure, flow2.response_structure)

    result = {
        'content_structure': content_structure,
        'content_type': flow1.content_type,
        'endpoint': flow1.endpoint,
        'method': flow1.method,
        'query_parameters': query_parameters,
        'response_structure': response_structure,
        'service': flow1.service,
    }
    return PssFlowDetails(result)


def __merge_type_dictionaries(d1: dict, d2: dict) -> dict:
    result = {}
    result_names = set(d1.keys()).union(set(d2.keys()))
    for name in result_names:
        type1 = d1.get(name, 'str')
        type2 = d2.get(name, 'str')
        if isinstance(type1, dict) and isinstance(type2, dict):
            result[name] = __merge_type_dictionaries(type1, type2)
        elif isinstance(type1, dict):
            result[name] = type1
        elif isinstance(type2, dict):
            result[name] = type2
        elif not isinstance(type1, str) or not isinstance(type2, str):
            pass
        else:
            type1_value = __TYPE_ORDER_LOOKUP[type1]
            type2_value = __TYPE_ORDER_LOOKUP[type2]
            if type1_value >= type2_value:
                result[name] = type1
            else:
                result[name] = type2
    return result


def __organize_flows(extracted_flow_details: List[PssFlowDetails]) -> API_ORGANIZED_FLOWS:
    sorted_flows = sorted(extracted_flow_details, key=lambda x: (f'{x.service}{x.endpoint}'))
    result: API_ORGANIZED_FLOWS = {}
    for flow_details in sorted_flows:
        result.setdefault(flow_details.service, {}).setdefault(flow_details.endpoint, []).append(flow_details)
    return result


def __read_flows_from_file(file_path: str) -> List[PssFlowDetails]:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f'The specified file could not be found at: {file_path}')

    result: List[PssFlowDetails] = []

    with open(file_path, 'rb') as fp:
        flow_reader: FlowReader = FlowReader(fp)

        try:
            tnetstring.load(flow_reader.fo)
        except ValueError as e:
            raise Exception(f'The specified file is not a Flows file: {file_path}') from e

        result = [PssFlowDetails(__convert_flow_to_dict(recorded_flow)) for recorded_flow in flow_reader.stream()]

    return result


def __singularize_flows(organized_flows: API_ORGANIZED_FLOWS) -> Set[PssFlowDetails]:
    result: Set[PssFlowDetails] = set()
    for _, endpoints in organized_flows.items():
        for _, endpoint_flows in endpoints.items():
            merged_flow = endpoint_flows[0]
            if len(endpoint_flows) > 1:
                for flow2 in endpoint_flows[1:]:
                    merged_flow = __merge_flows(merged_flow, flow2)
            result.add(merged_flow)
    return result





# ----- MAIN -----

if __name__ == "__main__":
    app_start = timer()
    if (len(sys.argv) == 1):
        raise ValueError('The path to the flows file has not been specified!')
    file_path = ' '.join(sys.argv[1:])
    flows = parse_flows_file(file_path)

    file_name, _ = os.path.splitext(file_path)
    storage_path = f'{file_name}.json'
    start = timer()
    store_flow_details_as_json(storage_path, flows)
    end = timer()
    print(f'Stored JSON encoded PSS API endpoint information in {datetime.timedelta(seconds=(end-start))} at: {storage_path}')
    print(f'Total execution time: {datetime.timedelta(seconds=(end-app_start))}')