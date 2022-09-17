from email.policy import HTTP
from typing import Dict, Union

from mitmproxy.http import HTTPFlow

ResponseStructure = Dict[str, Union[str, 'ResponseStructure']]


class PssFlowDetails:
    def __init__(self, details: dict) -> None:
        self.__content_structure: ResponseStructure = details['content_structure']
        self.__content_type: str = details['content_type']
        self.__endpoint: str = details['endpoint']
        self.__method: str = details['method']
        self.__query_parameters: Dict[str, str] = details['query_parameters']
        self.__response_structure: ResponseStructure = details['response_structure']
        self.__service: str = details['service']
        self.__original_flow: HTTPFlow = details['original_flow']

    def __repr__(self) -> str:
        return f'<PssFlowDetails {self.service}/{self.endpoint}>'

    def __str__(self) -> str:
        return self.__repr__()


    @property
    def content_structure(self) -> ResponseStructure:
        return self.__content_structure

    @property
    def content_type(self) -> str:
        return self.__content_type

    @property
    def endpoint(self) -> str:
        return self.__endpoint

    @property
    def method(self) -> str:
        return self.__method

    @property
    def original_flow(self) -> HTTPFlow:
        return self.__original_flow

    @property
    def query_parameters(self) -> Dict[str, str]:
        return self.__query_parameters

    @property
    def response_structure(self) -> ResponseStructure:
        return self.__response_structure

    @property
    def service(self) -> str:
        return self.__service

    def __eq__(self, other):
        if isinstance(other, PssFlowDetails):
            return (
                    self.service == other.service
                    and self.endpoint == other.endpoint
            )
        return False

    def __hash__(self):
        return hash((self.service, self.endpoint))

    def __iter__(self):
        result = {
            'content_structure': self.content_structure,
            'content_type': self.content_type,
            'endpoint': self.endpoint,
            'method': self.method,
            'query_parameters': self.query_parameters,
            'response_structure': self.response_structure,
            'service': self.service,
        }
        for item in result.items():
            yield item

    def __lt__(self, other):
        if isinstance(other, PssFlowDetails):
            if self.service == other.service:
                return self.endpoint < other.endpoint
            else:
                return self.service < other.service

    def __ne__(self, other):
        return not self.__eq__(other)
