from argparse import ArgumentParser

import emout
from pathlib import Path
from .utils import symlinkdir


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('from_directory')
    parser.add_argument('to_directory')
    parser.add_argument('--nstep', '-n', type=int, default=None)

    return parser.parse_args()


def extent_sim():
    args = parse_args()
    
    from_dir = Path(args.from_directory)
    to_dir = Path(args.to_directory)
    to_dir.mkdir(exist_ok=True)

    data = emout.Emout(from_dir)
    inp = data.inp

    inp.jobnum[0] = 1    
    if args.nstep is not None:
        inp.nstep = args.nstep

    inp.save(to_dir / 'plasma.inp')
    symlinkdir(from_dir / 'SNAPSHOT1', to_dir / 'SNAPSHOT0')
