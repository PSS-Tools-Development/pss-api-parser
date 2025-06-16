from typing import Dict as _Dict
from typing import Union as _Union

from mitmproxy.http import HTTPFlow as _HTTPFlow

from . import utils as _utils


ResponseStructure = _Dict[str, _Union[str, "ResponseStructure"]]


class PssFlowDetails:
    def __init__(self, details: dict) -> None:
        self.__content_parameters: _utils.NestedDict = details.get("content_parameters", {})
        self.__content_structure: _utils.NestedDict = details.get("content_structure", {})
        self.__content_type: str = details.get("content_type")
        self.__endpoint: str = details.get("endpoint", "")
        self.__method: str = details.get("method")
        self.__query_parameters: _Dict[str, str] = details.get("query_parameters", {})
        self.__response_gzipped: bool = details.get("response_gzipped")
        self.__response_structure: _utils.NestedDict = details.get("response_structure", {})
        self.__service: str = details.get("service", "")
        self.__original_flow: _HTTPFlow = details.get("original_flow")

    def __repr__(self) -> str:
        return f"<PssFlowDetails {self.service}/{self.endpoint}>"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def content_parameters(self) -> _utils.NestedDict:
        return self.__content_parameters

    @property
    def content_structure(self) -> _utils.NestedDict:
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
    def original_flow(self) -> _HTTPFlow:
        return self.__original_flow

    @property
    def query_parameters(self) -> _Dict[str, str]:
        return self.__query_parameters

    @property
    def response_gzipped(self) -> bool:
        return self.__response_gzipped or False

    @property
    def response_structure(self) -> _utils.NestedDict:
        return self.__response_structure

    @property
    def service(self) -> str:
        return self.__service

    def __eq__(self, other):
        if isinstance(other, PssFlowDetails):
            return self.service == other.service and self.endpoint == other.endpoint
        return False

    def __hash__(self):
        return hash((self.service, self.endpoint))

    def __iter__(self):
        result = {
            "content_parameters": self.content_parameters,
            "content_structure": self.content_structure,
            "content_type": self.content_type,
            "endpoint": self.endpoint,
            "method": self.method,
            "query_parameters": self.query_parameters,
            "response_gzipped": self.response_gzipped,
            "response_structure": self.response_structure,
            "service": self.service,
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
