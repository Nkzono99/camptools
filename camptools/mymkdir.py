#!/usr/bin/env python3
"""
Copy files listed in a JSON copy list to a target directory.
"""
import json
import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List, Tuple

from .utils import copy as copy_file

DEFAULT_COPYLIST = Path.home() / "large0" / ".camptools" / "copylist.json"


def parse_args() -> "Namespace":
    parser = ArgumentParser(
        description="Copy files listed in a JSON copy list to a target directory."
    )
    parser.add_argument(
        "directory", type=Path, help="Target directory to create and copy files into."
    )
    parser.add_argument(
        "-k", "--key", type=str, default="main", help="Key in the copylist JSON to use."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output."
    )
    parser.add_argument(
        "--copylist",
        type=Path,
        default=DEFAULT_COPYLIST,
        help="Path to the copy list JSON file.",
    )
    return parser.parse_args()


def load_copylist(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Copy list not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_copy_paths(json_data: dict, key: str) -> List[Tuple[Path, Path]]:
    try:
        entries = json_data[key]
    except KeyError:
        raise KeyError(f"Key '{key}' not found in copy list.")

    result: List[Tuple[Path, Path]] = []
    for item in entries:
        if isinstance(item, list):
            if len(item) != 2:
                raise ValueError(f"Invalid entry (expected 2 items): {item!r}")
            src = Path(item[0])
            dest_name = item[1]
        else:
            src = Path(item)
            dest_name = src.name
        result.append((src, Path(dest_name)))
    return result


def mymkdir() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s"
    )

    target_dir: Path = args.directory
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        data = load_copylist(args.copylist)
        copy_paths = get_copy_paths(data, args.key)
    except Exception as e:
        logging.error(e)
        return

    for src, name in copy_paths:
        dest = target_dir / name
        logging.info(f"Copying: {src} → {dest}")
        copy_file(src, dest)
