from pathlib import Path
from time import perf_counter
from typing import Annotated

import typer
from rich import print as rich_print

from . import __version__, parse_command, ui
from .backend.anonymize import anonymize_file
from .backend.enums import ProgrammingLanguage
from .backend.generate import generate_source_code
from .backend.merge import apply_overrides, merge_api_structures, read_structure_json
from .backend.parse import store_structure_json


app = typer.Typer(
    context_settings={"help_option_names": ["--help", "-h"]},
    pretty_exceptions_enable=True,
    pretty_exceptions_short=True,
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
)
app.add_typer(parse_command.app, name="parse", help="Commands for parsing enumerations and network traffic into JSON files.")


@app.command("anon", help="Remove personal and confidential data from mitmproxy flows files.")
def anonymize(
    out_dir: Annotated[
        Path,
        typer.Argument(
            file_okay=False,
            dir_okay=True,
            writable=True,
            exists=True,
            show_default=False,
            help="Target directory for the anonymized flows file(s)",
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
            help="Path(s) to the mitmproxy flows file(s) to be anonymized",
        ),
    ],
):
    rich_print("Anonymize mitmproxy flows files.\n")
    ui.print_input_output(flows, out_dir)
    ui.print_step("Anonymizing captured flows...", "blue")
    start = perf_counter()

    for in_path in flows:
        ui.print_step(f"Anonymizing file: {in_path}", "blue")
        out_path = anonymize_file(in_path, out_dir)
        ui.print_step(f"Stored anonymized flows at: {out_path}", "blue")

    end = perf_counter()
    ui.print_step(f"All files anonymized in {end-start:.2f} seconds.", "blue")


@app.command(name="gen", help="Generate pssapi library code.")
def gen(
    out_dir: Annotated[
        Path,
        typer.Argument(
            file_okay=False,
            dir_okay=True,
            show_default=False,
            help="Target directory for the generated files. The full path will be created and a folder 'pssapi' will be created in the target folder.",
        ),
    ],
    structure: Annotated[
        Path,
        typer.Argument(
            file_okay=True,
            dir_okay=False,
            exists=True,
            show_default=False,
            help="Path to the structure JSON file, containing parsed flows, to be used.",
        ),
    ],
    enums: Annotated[
        Path,
        typer.Option(
            "--enums",
            "-e",
            file_okay=True,
            dir_okay=False,
            exists=True,
            show_default=False,
            help="Path to the enumerations JSON file to be used.",
        ),
    ] = None,
    cacheable: Annotated[
        Path,
        typer.Option(
            "--cacheable",
            "-c",
            file_okay=True,
            dir_okay=False,
            exists=True,
            show_default=False,
            help="Path to the cacheable endpoints JSON file to be used.",
        ),
    ] = None,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            "-o",
            file_okay=True,
            dir_okay=False,
            exists=True,
            show_default=False,
            help="Overwrite all files (by default only raw files will be overwritten).",
        ),
    ] = False,
    language: Annotated[
        ProgrammingLanguage, typer.Option("--language", "-l", show_default=(len(ProgrammingLanguage) > 1), help="Target language to be used")
    ] = ProgrammingLanguage.PYTHON,
):
    target_language = ProgrammingLanguage(language)

    rich_print("Generate PSS API software library.\n")
    ui.print_step(f"API Structure file (parsed flows): {structure}", "yellow")
    if enums:
        ui.print_step(f"Parsed enumerations file: {enums}", "blue")
    if cacheable:
        ui.print_step(f"Cacheable endpoints: {cacheable}", "blue")
    ui.print_step(f"Output folder: {out_dir / 'pssapi'}", "yellow")
    # print overwrite

    ui.print_step("Generating code...", "blue")

    start = perf_counter()
    generate_source_code(
        structure,
        enums,
        cacheable,
        out_dir,
        target_language,
        force_overwrite=overwrite,
    )
    end = perf_counter()

    ui.print_step(f"Code generated in {end-start:.2f} seconds.", "blue")


@app.command("merge", help="Merge parsed flows files.")
def merge(
    out_dir: Annotated[
        Path,
        typer.Argument(
            file_okay=True,
            dir_okay=False,
            writable=True,
            show_default=False,
            help="Target path for the merged flows file",
        ),
    ],
    parsed_flows: Annotated[
        list[Path],
        typer.Argument(
            file_okay=True,
            dir_okay=False,
            readable=True,
            exists=True,
            show_default=False,
            help="Path(s) to the parsed mitmproxy flows file(s) to be merged",
        ),
    ],
    overrides: Annotated[
        Path,
        typer.Option(
            "--overrides",
            "-o",
            show_default=False,
            file_okay=True,
            dir_okay=False,
            exists=True,
            help="Path to file containing API structure information overrides",
        ),
    ] = None,
    uncompressed: Annotated[bool, typer.Option("--uncompressed", "-u", show_default=False, help="Preserve whitespace in the output file")] = False,
):
    rich_print("Merge parsed mitmproxy flows files.\n")
    ui.print_input_output(parsed_flows, out_dir)
    ui.print_step(f"Compressed storage: {'No' if uncompressed else 'Yes'}", "yellow")
    ui.print_step("Merging parsed flows...", "blue")

    start = perf_counter()
    result = read_structure_json(parsed_flows[0])

    for merge_with in parsed_flows[1:]:
        result = merge_api_structures(result, read_structure_json(merge_with))

    if overrides:
        overrides = read_structure_json(overrides)
        result = apply_overrides(result, overrides)

    store_structure_json(out_dir, result, (not uncompressed))

    end = perf_counter()
    ui.print_step(f"All flow files merged in {end-start:.2f} seconds.", "blue")


@app.command(name="version", help="Print the version of the PSS API parser.")
def version():
    rich_print(
        "A command line tool to parse the Pixel Starships API from network traffic recorded with [italic]mitmproxy[/italic] and code files decompiled from the Steam edition of Pixel Starships and generate a software library from the parsed information."
    )
    rich_print("Version: " + __version__)


def app_result_callback(_: typer.Context):
    rich_print("")


@app.callback(result_callback=app_result_callback)
def app_callback(_: typer.Context):
    rich_print("")
    rich_print(f"[bold]Pixel Starships API Parser[/bold] v[default]{__version__}")
