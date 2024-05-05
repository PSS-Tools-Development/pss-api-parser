import json as _json
import re as _re
from typing import List as _List

from mitmproxy.http import HTTPFlow as _HTTPFlow
from mitmproxy.io import FlowReader as _FlowReader
from mitmproxy.io import FlowWriter as _FlowWriter
from mitmproxy.io import tnetstring as _tnetstring

from . import utils as _utils

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
__RX_PROPERTIES: _re.Pattern = _re.compile('( (' + '|'.join(__ENTITY_PROPERTY_NAMES) + ')="(.*?)")', _re.IGNORECASE | _re.MULTILINE)


# ---------- Functions ----------

def anonymize_flow(flow: _HTTPFlow) -> _HTTPFlow:
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
            request_content_dict: dict = _json.loads(request_content)
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
            request_content = _json.dumps(request_content_dict)
        else:
            # Request Content is most likely a query parameter string
            if '=' in request_content:
                query_params = request_content.split('&')
                request_content_dict = {}
                for query_param in query_params:
                    split_query_param = query_param.split('=')
                    if len(split_query_param) == 2:  # Ignore malformed query parameters or strings that aren't query parameters
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
    if flow.response and flow.response.content:
        response_content = flow.response.content.decode('utf-8')
        matches = __RX_PROPERTIES.finditer(response_content)
        for match in matches:
            matched_string, property_name, property_value = match.groups()
            try:
                int(property_value)
                property_value = '0' * len(property_value)
            except:
                try:
                    _utils.parse_pss_datetime(property_value)
                    property_value = '2016-01-06T00:00:00'
                except:
                    property_value = 'x' * len(property_value)
            response_content = response_content.replace(matched_string, f' {property_name}="{property_value}"')

        flow.response.content = response_content.encode('utf-8')

    return flow


def anynomize_flows(file_path: str) -> _List[_HTTPFlow]:
    with open(file_path, 'rb') as fp:
        flow_reader: _FlowReader = _FlowReader(fp)
        flows = [anonymize_flow(flow) for flow in flow_reader.stream()]
    return flows


def store_flows(file_path: str, flows: _List[_HTTPFlow]) -> None:
    with open(file_path, 'wb') as fp:
        flow_writer: _FlowWriter = _FlowWriter(fp)
        for flow in flows:
            flow_writer.add(flow)
