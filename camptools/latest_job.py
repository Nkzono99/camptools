import os
import shutil as sh
import subprocess
from argparse import ArgumentParser
from pathlib import Path

import emout

from .utils import call


def parse_args():
    parser = ArgumentParser()

    parser.add_argument("--directory", default="./")
    parser.add_argument("--index", "-i", default=-1, type=int)
    parser.add_argument("--n", "-n", default=5, type=int)

    return parser.parse_args()


def main():
    args = parse_args()

    root = Path(args.directory)
    data = emout.Emout(root)

    latest_stdout_path = sorted(list(root.glob("stdout.*.log")), key=parse_job_id)[
        args.index
    ]

    stdout, stderr = call(f"tail -n {args.n} {str(latest_stdout_path)}")

    print(f"> {str(latest_stdout_path)}")
    print()
    print(stdout)

    steps = []
    for line in stdout.split("\n"):
        if line.startswith(" **** step ---------"):
            step = int(line.replace("**** step ---------", ""))
            steps.append(step)

    if len(steps) == 0:
        return

    print(
        f"{steps[-1]} / {data.inp.nstep} ({steps[-1]/float(data.inp.nstep)*100: .2f} %)"
    )


def parse_job_id(filepath):
    return int(str(filepath).replace("stdout.", "").replace(".log", ""))


if __name__ == "__main__":
    main()
