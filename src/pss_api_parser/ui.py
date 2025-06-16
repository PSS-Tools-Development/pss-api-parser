from pathlib import Path
from typing import Iterable

from rich import print
from rich.text import Text


def print_step(step: str, color: str):
    print(Text(">>>", color), Text(step, "white"))


def print_list_item(list_item: str):
    print(Text(f" - {list_item}", "gray"))


def print_input_output(in_files: Iterable[Path], out: Path):
    print_step("Input file(s):", "yellow")
    for in_path in in_files:
        print_list_item(in_path)
    print()
    if out.is_dir():
        print_step("Output folder:", "yellow")
    else:
        print_step("Output file:", "yellow")
    print_list_item(out)
    print()
