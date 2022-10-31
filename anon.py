

import argparse as _argparse
from contexttimer import Timer as _Timer
import os as _os
import sys as _sys

from colorama import init as _colorama_init
from colorama import Fore as _Fore

from src import anonymize as _anonymize



if __name__ == '__main__':
    """
        Example: python anon.py --in examples/pss_api_steam_v0.991.4.flows --out examples
    """

    # enable Windows support of colors
    _colorama_init()

    ERR_INPUT_NOT_FOUND = 1

    parser = _argparse.ArgumentParser()
    parser.add_argument('--in', dest='in_', type=str, required=True, help='Path to the flows file to be anonymized')
    parser.add_argument('--out', type=str, required=True, help='Target directory for the anonymized flows file')
    args = parser.parse_args()

    if not _os.path.isfile(args.in_):
        print(f'{_Fore.RED}ERROR: Flows JSON file does not exist!{_Fore.RESET}')
        _sys.exit(ERR_INPUT_NOT_FOUND)

    with _Timer() as t:
        print(f'{_Fore.YELLOW} >>>{_Fore.RESET} Input file: {args.in_}')
        print(f'{_Fore.YELLOW} >>>{_Fore.RESET} Output path: {args.out}')
        print(f'{_Fore.BLUE} >>>{_Fore.RESET} Anonymizing captured flows...')

        input_file_name_with_extension = _os.path.split(args.in_)[1]
        output_file_name = f'{_os.path.splitext(input_file_name_with_extension)[0]}_anonymized.flows'
        output_file_path = _os.path.join(args.out, output_file_name)

        anonymized_flows = _anonymize.anynomize_flows(
            args.in_
        )
        _anonymize.store_flows(
            output_file_path,
            anonymized_flows
        )
        print(f'{_Fore.BLUE} >>>{_Fore.RESET} Stored anonymized flows at: {output_file_path}')

        print(f'{_Fore.BLUE} >>>{_Fore.RESET} Done in {t.elapsed}s')
        _sys.exit(0)