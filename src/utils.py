import re as _re



def convert_to_snake_case(s):
    return '_'.join(
        _re.sub('([A-Z][a-z]+)', r' \1',
        _re.sub('([A-Z]+)', r' \1',
        s.replace('-', ' '))).split()).lower()