import json
import os.path
import re
import sys
from datetime import datetime, timedelta
from timeit import default_timer as timer
from typing import Dict, List, Set, Union
from xml.etree import ElementTree

from mitmproxy.http import HTTPFlow
from mitmproxy.io import FlowReader, FlowWriter, tnetstring
from mitmproxy.coretypes.multidict import MultiDictView

from flowdetails import PssFlowDetails, ResponseStructure
from objectstructure import PssObjectStructure
import utils



# ---------- Constants ----------

__ENTITY_PROPERTY_NAMES = [
    'accesstoken',
    'advertisingkey',
    'attackingshipxml',
    'authenticationtype',
    'battleid',
    'defendingshipxml',
    'devicekey',
    'email',
    'emailverificationstatus',
    'facebooktoken',
    'facebooktokenexpirydate',
    'gamecentername',
    'gamecenterfriendcount',
    'googleplayaccesstokenexpirydate',
    'refreshtoken',
    'steamid',
]
__QUERY_PARAM_NAMES = [
    'accesstoken',
    'advertisingkey',
    'battleid',
    'checksum',
    'devicekey',
    'email',
    'facebooktoken',
    'gamecentername',
    'password',
    'refreshtoken',
    'steamid',
    'ticket',
]
__RX_PROPERTIES: re.Pattern = re.compile('( (' + '|'.join(__ENTITY_PROPERTY_NAMES) + ')="(.*?)")', re.IGNORECASE | re.MULTILINE)



# ---------- Functions ----------

def anonymize_flow(flow: HTTPFlow) -> HTTPFlow:
    flow.server_conn.sockname = (None, None)

    for query_param_name, query_param_value in flow.request.query.items():
        if query_param_name.lower() in __QUERY_PARAM_NAMES and query_param_value:
            try:
                int(query_param_value)
                query_param_value = '0' * len(query_param_value)
            except:
                query_param_value = 'x' * len(query_param_value)
        flow.request.query[query_param_name] = query_param_value

    request_content = ''
    if flow.request.content:
        request_content = flow.request.content.decode('utf-8')
        try:
            request_content_dict: dict = json.loads(request_content)
        except:
            request_content_dict: dict = None
        if request_content_dict:
            # Request Content is a json dictionary
            for query_param_name, query_param_value in request_content_dict.items():
                if query_param_name.lower() in __QUERY_PARAM_NAMES and query_param_value:
                    try:
                        int(query_param_value)
                        query_param_value = '0' * len(query_param_value)
                    except:
                        query_param_value = 'x' * len(query_param_value)
                    request_content_dict[query_param_name] = query_param_value
            request_content = json.dumps(request_content_dict)
        else:
            # Request Content is most likely a query parameter string
            if '=' in request_content:
                query_params = request_content.split('&')
                request_content_dict = {}
                for query_param in query_params:
                    split_query_param = query_param.split('=')
                    if len(split_query_param) == 2: # Ignore malformed query parameters or strings that aren't query parameters
                        query_param_name, query_param_value = split_query_param
                        if query_param_name.lower() in __QUERY_PARAM_NAMES and query_param_value:
                            try:
                                int(query_param_value)
                                query_param_value = '0' * len(query_param_value)
                            except:
                                query_param_value = 'x' * len(query_param_value)
                        request_content_dict[query_param_name] = query_param_value
                request_content = '&'.join('='.join((key, value)) for key, value in request_content_dict.items())

        flow.request.content = request_content.encode('utf-8')

    response_content = ''
    if flow.response.content:
        response_content = flow.response.content.decode('utf-8')
        matches = __RX_PROPERTIES.finditer(response_content)
        for match in matches:
            matched_string, property_name, property_value = match.groups()
            try:
                int(property_value)
                property_value = '0' * len(property_value)
            except:
                try:
                    utils.parse_pss_datetime(property_value)
                    property_value = '2016-01-06T00:00:00'
                except:
                    property_value = 'x' * len(property_value)
            response_content = response_content.replace(matched_string, f' {property_name}="{property_value}"')

        flow.response.content = response_content.encode('utf-8')

    return flow


def anynomize_flows(file_path: str) -> List[HTTPFlow]:
    with open(file_path, 'rb') as fp:
        flow_reader: FlowReader = FlowReader(fp)

        try:
            tnetstring.load(flow_reader.fo)
        except ValueError as e:
            raise Exception(f'The specified file is not a Flows file: {file_path}') from e

        flows = [anonymize_flow(flow) for flow in flow_reader.stream()]
    return flows


def store_flows(file_path: str, flows: List[HTTPFlow]) -> None:
    with open(file_path, 'wb') as fp:
        flow_writer: FlowWriter = FlowWriter(fp)
        for flow in flows:
            flow_writer.add(flow)



# ----- MAIN -----

if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise ValueError('The path to the flows file has not been specified!')
    file_path = ' '.join(sys.argv[1:])
    print(f'Anonymizing flows file at: {file_path}')
    flows = anynomize_flows(file_path)

    file_name, _ = os.path.splitext(file_path)
    storage_path = f'{file_name}_anonymized.flows'
    store_flows(storage_path, flows)
    print(f'Stored anonymized flows file at: {storage_path}')