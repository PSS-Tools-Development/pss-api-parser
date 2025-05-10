import argparse as _argparse
import os as _os
import sys as _sys

from colorama import Fore as _Fore
from colorama import init as _colorama_init
from contexttimer import Timer as _Timer

from src import enums as _enums
from src import parse as _parse

if __name__ == "__main__":
    """
    Examples:
      python parse.py flows --in examples/pss_api_steam_v0.991.4_anonymized.flows --out examples --verbose
      python parse.py enums --in examples/pss_v0.992_dump.cs --out examples --verbose
    """

    # enable Windows support of colors
    _colorama_init()

    ERR_INPUT_NOT_FOUND = 1

    parser = _argparse.ArgumentParser()
    parser.add_argument(
        "function", choices=["flows", "enums"], type=str, help="Select a function"
    )
    parser.add_argument(
        "--in",
        dest="in_",
        nargs="+",
        type=str,
        required=True,
        help="The file to be parsed",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Target directory for the parsed JSON files",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose mode")
    parser.add_argument(
        "--uncompressed",
        action="store_true",
        help="Preserve whitespace in the output file",
    )
    args = parser.parse_args()

    for in_file in args.in_:
        if not _os.path.isfile(in_file):
            print(
                f"{_Fore.RED}ERROR: The specified input file does not exist!{_Fore.RESET}"
            )
            _sys.exit(ERR_INPUT_NOT_FOUND)

    with _Timer() as t:
        output_directory = args.out.rstrip("/")
        print(f"{_Fore.YELLOW} >>>{_Fore.RESET} Function: {args.function}")
        print(f"{_Fore.YELLOW} >>>{_Fore.RESET} Input file(s):")
        for in_file in args.in_:
            print(f"{_Fore.YELLOW} ---{_Fore.RESET} {in_file}")
        print(f"{_Fore.YELLOW} >>>{_Fore.RESET} Output path: {output_directory}")
        if args.verbose:
            print(f"{_Fore.YELLOW} >>>{_Fore.RESET} Verbose: Yes")
        print(
            f'{_Fore.YELLOW} >>>{_Fore.RESET} Compressed storage: {"No" if args.uncompressed else "Yes"}'
        )

        if args.function == "flows":
            print(f"{_Fore.BLUE} >>>{_Fore.RESET} Parsing captured flows...")
            for in_file in args.in_:
                print(f"{_Fore.BLUE} >>>{_Fore.RESET} Processing file: {in_file}")

                input_file_name_with_extension = _os.path.split(in_file)[1]
                output_file_name = (
                    f"{_os.path.splitext(input_file_name_with_extension)[0]}.json"
                )
                output_file_path = _os.path.join(output_directory, output_file_name)
                parsed_flows = _parse.parse_flows_file(in_file, args.verbose)
                _parse.store_structure_json(
                    output_file_path, parsed_flows, compressed=(not args.uncompressed)
                )
                print(
                    f"{_Fore.BLUE} >>>{_Fore.RESET} Stored parsed services, endpoints and entities at: {output_file_path}"
                )
        elif args.function == "enums":
            print(f"{_Fore.BLUE} >>>{_Fore.RESET} Parsing dumped enumerations...")
            input_file_name_with_extension = _os.path.split(args.in_[0])[1]
            output_file_name = _os.path.splitext(input_file_name_with_extension)[0]
            output_file_name += "_enums.json"
            output_file_path = _os.path.join(output_directory, output_file_name)
            parsed_enums = _enums.parse_csharp_dump_file(args.in_[0])
            _enums.store_enum_file(
                parsed_enums, output_file_path, compressed=(not args.uncompressed)
            )
            print(
                f"{_Fore.BLUE} >>>{_Fore.RESET} Stored parsed enumerations at: {output_file_path}"
            )

        print(f"{_Fore.BLUE} >>>{_Fore.RESET} Done in {t.elapsed}s")
        _sys.exit(0)
