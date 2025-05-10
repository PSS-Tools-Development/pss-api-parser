import argparse as _argparse
import os as _os
import sys as _sys

from colorama import Fore as _Fore
from colorama import init as _colorama_init
from contexttimer import Timer as _Timer

from src import anonymize as _anonymize

if __name__ == "__main__":
    """
    Example: python anon.py --in examples/pss_api_steam_v0.991.4.flows --out examples
    """

    # enable Windows support of colors
    _colorama_init()

    ERR_INPUT_NOT_FOUND = 1

    parser = _argparse.ArgumentParser()
    parser.add_argument(
        "--in",
        dest="in_",
        type=str,
        nargs="+",
        required=True,
        help="Path to the flows file(s) to be anonymized",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Target directory for the anonymized flows file",
    )
    args = parser.parse_args()

    with _Timer() as t:
        input_files = []
        print(f"{_Fore.YELLOW} >>>{_Fore.RESET} Input file(s):")
        for input_file_path in args.in_:
            if not _os.path.isfile(input_file_path):
                print(
                    f"{_Fore.RED} >>> ERROR:{_Fore.RESET} Ignoring non-existent flows JSON file: {input_file_path}"
                )
            else:
                print(f"{_Fore.YELLOW} >>>{_Fore.RESET}  - {input_file_path}")
                input_files.append(input_file_path)
        print(f"{_Fore.YELLOW} >>>{_Fore.RESET} Output path: {args.out}")

        if not input_files:
            print(
                f"{_Fore.RED} >>> ERROR:{_Fore.RESET} No valid input files specified, exiting."
            )
            _sys.exit(ERR_INPUT_NOT_FOUND)

        print(f"{_Fore.BLUE} >>>{_Fore.RESET} Anonymizing captured flows...")
        for input_file_path in input_files:
            print(f"{_Fore.BLUE} >>>{_Fore.RESET} Anonymizing file: {input_file_path}")
            input_file_name_with_extension = _os.path.split(input_file_path)[1]
            output_file_name = f"{_os.path.splitext(input_file_name_with_extension)[0]}_anonymized.flows"
            output_file_path = _os.path.join(args.out, output_file_name)
            anonymized_flows = _anonymize.anynomize_flows(input_file_path)
            _anonymize.store_flows(output_file_path, anonymized_flows)
            print(
                f"{_Fore.BLUE} >>>{_Fore.RESET} Stored anonymized flows at: {output_file_path}"
            )

        print(f"{_Fore.BLUE} >>>{_Fore.RESET} Done in {t.elapsed}s")
        _sys.exit(0)
