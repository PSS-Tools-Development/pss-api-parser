import json as _json
import keyword as _keyword
import os as _os
import re as _re
from datetime import datetime as _datetime
from typing import Union as _Union


def append_underscore_if_keyword(s: str) -> str:
    if _keyword.iskeyword(s):
        s += '_'
    return s


def convert_camel_to_snake_case(s: str) -> str:
    if not s:
        return s
    return '_'.join(
        _re.sub(r'([A-Z\d][a-z]+)', r' \1',
                _re.sub(r'([A-Z\d]+)', r' \1',
                        s.replace('-', ' '))).split()).lower()


def convert_snake_to_camel_case(s: str) -> str:
    return ''.join(sub.title() for sub in s.split('_'))


def convert_snake_to_lower_camel_case(s: str) -> str:
    subs = s.split('_')
    return subs[0] + ''.join(sub.title() for sub in subs[1:])


def create_path(path: str) -> None:
    if not _os.path.exists(path):
        _os.mkdir(path)


def create_file(path: str, contents: str, overwrite: bool = False) -> None:
    if overwrite or not _os.path.exists(path):
        with open(path, 'w') as fp:
            fp.write(contents or '')


def parse_pss_datetime(dt: str) -> _datetime:
    try:
        return _datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
    except:
        return _datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f')


def read_json(file_path: str) -> _Union[list, dict]:
    with open(file_path, 'r') as fp:
        result = _json.load(fp)
    return result
