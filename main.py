import argparse
import os
import sys

from contexttimer import Timer
from colorama import init as colorama_init, Fore

import src.generate as generate

# enable Windows support of colors
colorama_init()

ERR_INPUT_NOT_EXISTS = 1

if __name__ == '__main__':
    """
        Example: python main.py --endpoints examples/pss_api_steam_v0.991.4_anonymized.json --enums examples/pss_v0.992_dump_enums.json --output bin
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--services', type=str, required=True, help='Path to the services JSON file to be used')
    parser.add_argument('--enums', type=str, required=False, help='Path to the enumerations JSON file to be used')
    parser.add_argument('--output', type=str, required=True, help='Target directory for the generated files')
    parser.add_argument('--overwrite', action="store_true", default=False, help='Overwrite all files (by default only raw files will be overwritten)')
    args = parser.parse_args()

    if not os.path.isfile(args.services):
        print(f'{Fore.RED}ERROR: Services JSON file does not exist!{Fore.RESET}')
        sys.exit(ERR_INPUT_NOT_EXISTS)

    if args.enums and not os.path.isfile(args.enums):
        print(f'{Fore.RED}ERROR: Enumerations JSON file does not exist!{Fore.RESET}')
        sys.exit(ERR_INPUT_NOT_EXISTS)

    with Timer() as t:
        print(f'{Fore.YELLOW} >>>{Fore.RESET} Endpoints: {args.endpoints}')
        if args.enums:
            print(f'{Fore.YELLOW} >>>{Fore.RESET} Enumerations: {args.enums}')
        print(f'{Fore.YELLOW} >>>{Fore.RESET} Output: {args.output}')
        print(f'{Fore.YELLOW} >>>{Fore.RESET} Overwrite: {"Yes" if args.output else "No"}')
        print(f'{Fore.BLUE} >>>{Fore.RESET} Starting generation...')

        generate.generate_source_code(
            args.endpoints,
            args.enums,
            args.output,
            force_overwrite=args.overwrite,
        )

        print(f'{Fore.BLUE} >>>{Fore.RESET} Done in {t.elapsed}s')
