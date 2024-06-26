import argparse as _argparse
import os as _os
import sys as _sys

from colorama import Fore as _Fore
from colorama import init as _colorama_init
from contexttimer import Timer as _Timer

from src import merge as _merge
from src import parse as _parse



if __name__ == '__main__':
    """
        Example: python merge.py --in pss_api_ios_v0.989.9402_anonymized.json pss_api_steam_v0.991.4_anonymized.json --out examples
    """

    # enable Windows support of colors
    _colorama_init()

    ERR_INPUT_NOT_FOUND = 1

    parser = _argparse.ArgumentParser()
    parser.add_argument('--in', dest='in_', type=str, nargs='+', required=True, help='Path(s) to the flows file(s) to be merged')
    parser.add_argument('--overrides', type=str, required=False, help='Path to the overrides file')
    parser.add_argument('--outfile', type=str, required=True, help='Target file path for the merged flows file')
    parser.add_argument('--uncompressed', action='store_true', help='Preserve whitespace in the output file')
    args = parser.parse_args()

    error = False
    for file_path in args.in_:
        if not _os.path.isfile(file_path):
            print(f'{_Fore.RED}ERROR: Specified flows JSON file does not exist: {file_path}{_Fore.RESET}')
    if error:
        _sys.exit(ERR_INPUT_NOT_FOUND)

    with _Timer() as t:
        print(f'{_Fore.YELLOW} >>>{_Fore.RESET} Input files:')
        for in_ in args.in_:
            print(f'{_Fore.YELLOW} >>> -{_Fore.RESET} {in_}')
        print(f'{_Fore.YELLOW} >>>{_Fore.RESET} Output file: {args.outfile}')
        print(f'{_Fore.YELLOW} >>>{_Fore.RESET} Compressed storage: {"No" if args.uncompressed else "Yes"}')
        print(f'{_Fore.BLUE} >>>{_Fore.RESET} Merging parsed flows...')

        result = _merge.read_structure_json(args.in_[0])
        for merge_with in args.in_[1:]:
            result = _merge.merge_api_structures(
                result,
                _merge.read_structure_json(merge_with)
            )
        if args.overrides:
            overrides = _merge.read_structure_json(args.overrides)
            result = _merge.apply_overrides(result, overrides)
        _parse.store_structure_json(
            args.outfile,
            result,
            (not args.uncompressed)
        )

        print(f'{_Fore.BLUE} >>>{_Fore.RESET} Done in {t.elapsed}s')
        _sys.exit(0)
