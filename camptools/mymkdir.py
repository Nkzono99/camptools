from argparse import ArgumentParser
from os import PathLike
from pathlib import Path
import shutil as sh
import json
from typing import List

COPYLIST = Path().home() / 'copylist.json'


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('directory')
    parser.add_argument('--key', '-key', type=str, default='main')

    return parser.parse_args()


def search_copylist(filename: PathLike, key: str) -> List[Path]:
    with open(filename, 'r', encoding='utf-8') as f:
        jsonobj = json.load(f)

    if key in jsonobj:
        copylist = []
        for filename in jsonobj[key]:
            copylist.append(Path(filename))

        return copylist
    else:
        print('key ({}) is not exists'.format(key))
        return None


def copy(from_file: Path, to_file: Path):
    if from_file.exists():
        sh.copyfile(str(from_file), str(to_file))
    else:
        print('{} is not found'.format(from_file))


def mymkdir():
    args = parse_args()

    directory: Path = Path('.') / args.directory
    directory.mkdir(exist_ok=True)

    copylist = search_copylist(COPYLIST, args.key)

    if copylist is None:
        return

    for filepath in copylist:
        name = filepath.name
        copy(filepath, directory / name)
