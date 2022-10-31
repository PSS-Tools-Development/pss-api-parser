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
        Example: python main.py --endpoints examples/pss_api_ios_v0.989.9402.json --output bin
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoints", type=str, required=True, help="endpoints JSON file to be generated")
    parser.add_argument("--enums", type=str, required=False, help="enumerations JSON file to be generated")
    parser.add_argument("--output", type=str, required=True, help="directory storing generated files")
    parser.add_argument("--overwrite", action="store_true", default=False, help="overwrite not raw files")
    args = parser.parse_args()

    if not os.path.isfile(args.endpoints):
        print(Fore.RED + 'ERROR: Endpoints JSON file not exists')
        sys.exit(ERR_INPUT_NOT_EXISTS)

    if args.enums and not os.path.isfile(args.enums):
        print(Fore.RED + 'ERROR: Enumerations JSON file not exists')
        sys.exit(ERR_INPUT_NOT_EXISTS)

    with Timer() as t:
        print(Fore.YELLOW + '>>> ' + Fore.RESET + 'Endpoints: {}'.format(args.endpoints))
        if args.enums:
            print(Fore.YELLOW + '>>> ' + Fore.RESET + 'Enumerations: {}'.format(args.enums))
        print(Fore.YELLOW + '>>> ' + Fore.RESET + 'Output: {}'.format(args.output))
        print(Fore.YELLOW + '>>> ' + Fore.RESET + 'Overwrite: {}'.format('Yes' if args.overwrite else 'No'))
        print(Fore.BLUE + '>>> ' + Fore.RESET + 'Starting generation...')

        generate.generate_source_code(
            args.endpoints,
            args.enums,
            args.output,
            force_overwrite=args.overwrite,
        )

        print(Fore.BLUE + '>>> ' + Fore.RESET + 'Done in {}s'.format(t.elapsed))
