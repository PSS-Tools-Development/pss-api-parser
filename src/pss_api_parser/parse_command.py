from pathlib import Path
from typing import Annotated

import typer
from rich import print as rich_print

from . import ui
from .backend.enums import parse_csharp_dump_file, store_enum_file
from .backend.parse import parse_flows_file, store_structure_json


app = typer.Typer()


@app.command("enums", help="Parse the enums from a decompiled Pixel Starships code file")
def parse_enums(
    out_dir: Annotated[
        Path,
        typer.Argument(
            # "--out",
            # "-o",
            file_okay=False,
            dir_okay=True,
            writable=True,
            exists=True,
            show_default=False,
            help="Target directory for the parsed enums file",
        ),
    ],
    code_file: Annotated[
        Path,
        typer.Argument(
            # "--in",
            # "-i",
            file_okay=True,
            dir_okay=False,
            readable=True,
            exists=True,
            show_default=False,
            help="Path to the decompiled Pixel Starships code file (*.cs)",
        ),
    ],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", show_default=False, help="Print additional output")] = False,
    uncompressed: Annotated[bool, typer.Option("--uncompressed", "-u", show_default=False, help="Preserve whitespace in the output file")] = False,
):
    rich_print("Parse enumerations from decompiled Pixel Starships code file.\n")
    ui.print_input_output([code_file], out_dir)
    if verbose:
        ui.print_step("Verbose: Yes", "yellow")
    ui.print_step(f"Compressed storage: {'No' if uncompressed else 'Yes'}", "yellow")
    ui.print_step("Parsing dumped enumerations...", "blue")

    output_file_name = f"{code_file.stem}_enums.json"
    output_file_path = out_dir / output_file_name
    parsed_enums = parse_csharp_dump_file(code_file)
    store_enum_file(parsed_enums, output_file_path, compressed=(not uncompressed))

    ui.print_step(f"Stored parsed enumerations at: {output_file_path}", "blue")


@app.command("flows", help="Parse captured mitmproxy flows into a JSON file.")
def parse_flows(
    out_dir: Annotated[
        Path,
        typer.Argument(
            # "--out",
            # "-o",
            file_okay=False,
            dir_okay=True,
            writable=True,
            exists=True,
            show_default=False,
            help="Target directory for the parsed flows file(s)",
        ),
    ],
    flows: Annotated[
        list[Path],
        typer.Argument(
            file_okay=True,
            dir_okay=False,
            readable=True,
            exists=True,
            show_default=False,
            help="Path(s) to the mitmproxy flows file(s) to be parsed",
        ),
    ],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", show_default=False, help="Print additional output")] = False,
    uncompressed: Annotated[bool, typer.Option("--uncompressed", "-u", show_default=False, help="Preserve whitespace in the output file")] = False,
):
    rich_print("Parse mitmproxy flows files.\n")
    ui.print_input_output(flows, out_dir)
    if verbose:
        ui.print_step("Verbose: Yes", "yellow")
    ui.print_step(f"Compressed storage: {'No' if uncompressed else 'Yes'}", "yellow")
    ui.print_step("Parsing captured flows...", "blue")

    for file_path in flows:
        ui.print_step(f"Processing file: {file_path}", "blue")

        output_file_name = f"{file_path.stem}.json"
        output_file_path = out_dir / output_file_name
        parsed_flows = parse_flows_file(file_path, verbose)
        store_structure_json(output_file_path, parsed_flows, compressed=(not uncompressed))

        ui.print_step(f"Stored parsed services, endpoints and entities at: {output_file_path}", "blue")
