import os
import re
import shutil as sh
import subprocess
from argparse import ArgumentParser
from datetime import datetime, timedelta
from pathlib import Path

import emout

from .jobs import create_submited_jobs
from .utils import call


def parse_args():
    parser = ArgumentParser()

    parser.add_argument("--directory", default="./")
    parser.add_argument("--index", "-i", default=-1, type=int)
    parser.add_argument("--n", "-n", default=5, type=int)
    parser.add_argument("--error", "-e", action="store_true")

    return parser.parse_args()


def main():
    args = parse_args()

    root = Path(args.directory)
    data = emout.Emout(root)

    pipe = "err" if args.error else "out"
    latest_stdout_pathes = sorted(list(root.glob(f"std{pipe}.*.log")), key=parse_job_id)
    latest_stdout_path = latest_stdout_pathes[args.index]

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

    job_elapsed_rate = max(steps[-1] / float(data.inp.nstep), 1e-8)
    print(f"{steps[-1]} / {data.inp.nstep} ({job_elapsed_rate*100: .2f} %)")

    # 予想時間を計算する
    m = re.match(r"stdout\.([0-9]+)\.log", str(latest_stdout_path))
    if m is None:
        return
    job_id = int(m.group(1))

    jobs = create_submited_jobs()
    jobs = [job for job in jobs if job.jobid == job_id]
    if len(jobs) == 1:
        job = jobs[0]

    hours, minutes, seconds = map(int, job.elapse.split(":"))
    elapsed = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    estimates = elapsed / job_elapsed_rate

    def timedelta2str(dt):
        days = dt.days
        hours, remainder = divmod(dt.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0:
            return f"{days:01d}-{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    print(f"{timedelta2str(elapsed)} / {timedelta2str(estimates)}")


def parse_job_id(filepath: Path):
    return int(str(filepath.name).replace("stdout.", "").replace("stderr.", "").replace(".log", ""))


if __name__ == "__main__":
    main()
