import os as _os
import re as _re



def convert_to_snake_case(s) -> str:
    if not s:
        return s
    return '_'.join(
        _re.sub('([A-Z\d][a-z]+)', r' \1',
        _re.sub('([A-Z\d]+)', r' \1',
        s.replace('-', ' '))).split()).lower()


def create_path(path: str) -> None:
    if not _os.path.exists(path):
        _os.mkdir(path)


def create_file(path: str, contents: str, overwrite: bool = False) -> None:
    if overwrite or not _os.path.exists(path):
        with open(path, 'w') as fp:
            fp.write(contents or '')