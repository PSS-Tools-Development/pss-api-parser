

import argparse as _argparse
from contexttimer import Timer as _Timer
import os as _os
import sys as _sys

from colorama import init as _colorama_init
from colorama import Fore as _Fore

from src import generate as _generate



if __name__ == '__main__':
    """
        Example: python gen.py --flows examples/pss_api_steam_v0.991.4_anonymized.json --enums examples/pss_v0.992_dump_enums.json --output bin
    """

    # enable Windows support of colors
    _colorama_init()

    ERR_SERVICES_NOT_FOUND = 1
    ERR_ENUMS_NOT_FOUND = 2

    parser = _argparse.ArgumentParser()
    parser.add_argument('--flows', type=str, required=True, help='Path to the flows JSON file to be used')
    parser.add_argument('--enums', type=str, required=False, help='Path to the enumerations JSON file to be used')
    parser.add_argument('--out', type=str, required=True, help='Target directory for the generated files')
    parser.add_argument('--overwrite', action='store_true', default=False, help='Overwrite all files (by default only raw files will be overwritten)')
    args = parser.parse_args()

    if not _os.path.isfile(args.flows):
        print(f'{_Fore.RED}ERROR: Flows JSON file does not exist!{_Fore.RESET}')
        _sys.exit(ERR_SERVICES_NOT_FOUND)

    if args.enums and not _os.path.isfile(args.enums):
        print(f'{_Fore.RED}ERROR: Enumerations JSON file does not exist!{_Fore.RESET}')
        _sys.exit(ERR_ENUMS_NOT_FOUND)

    with _Timer() as t:
        output_directory = args.out.rstrip('/')
        print(f'{_Fore.YELLOW} >>>{_Fore.RESET} Endpoints: {args.flows}')
        if args.enums:
            print(f'{_Fore.YELLOW} >>>{_Fore.RESET} Enumerations: {args.enums}')
        print(f'{_Fore.YELLOW} >>>{_Fore.RESET} Output path: {output_directory}')
        print(f'{_Fore.YELLOW} >>>{_Fore.RESET} Overwrite: {"Yes" if args.overwrite else "No"}')
        print(f'{_Fore.BLUE} >>>{_Fore.RESET} Generating code...')

        _generate.generate_source_code(
            args.flows,
            args.enums,
            output_directory,
            force_overwrite=args.overwrite,
        )

        print(f'{_Fore.BLUE} >>>{_Fore.RESET} Done in {t.elapsed}s')
        _sys.exit(0)