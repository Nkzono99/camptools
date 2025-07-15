from argparse import ArgumentParser
from pathlib import Path

from .jobs import JobHistoryManager, create_submited_jobs
from .utils import call
import colorama


def parse_args_joblist():
    parser = ArgumentParser()
    parser.add_argument("--status", "-s", action="store_true")
    parser.add_argument("--n", "-n", type=int, default=5)
    return parser.parse_args()


def joblist():
    args = parse_args_joblist()
    jobs = create_submited_jobs()

    job_dict = JobHistoryManager()
    job_dict.load()

    colorama.init()

    for job in jobs:
        if job.jobid in job_dict:
            directory = job_dict[job.jobid].directory
            message = job_dict[job.jobid].message
        else:
            directory = "Not Found"
            message = ""

        status_colors = {
            "RUN": colorama.Fore.GREEN,
            "PEND": colorama.Fore.LIGHTBLACK_EX,
            "FINI": colorama.Fore.CYAN,
            "CANC": colorama.Fore.RED,
        }

        root = Path(directory)
        if args.status and root.exists():
            job_elapsed_rate = calculate_rate(args, root, job.jobid)
            print(
                status_colors.get(job.status, colorama.Fore.WHITE)
                + f"{job.jobid} ({job.status:>4}, {job.elapse}, {job.queue:>8}|{job.proc:04}, {job_elapsed_rate*100:4.2f}%) : {directory} : {message}"
                + colorama.Style.RESET_ALL
            )
        else:
            print(
                status_colors.get(job.status, colorama.Fore.WHITE)
                + f"{job.jobid} ({job.status:>4}, {job.elapse}, {job.queue:>8}|{job.proc:04}) : {directory} : {message}"
                + colorama.Style.RESET_ALL
            )


def calculate_rate(args, root: Path, jobid: int):
    pipe = "out"
    latest_stdout_pathes = sorted(list(root.glob(f"std{pipe}.*.log")), key=parse_job_id)

    if len(latest_stdout_pathes) == 0:
        return 0.0

    latest_stdout_path = latest_stdout_pathes[-1]

    if parse_job_id(latest_stdout_path) != jobid:
        return 0.0

    stdout, stderr = call(f"tail -n {args.n} {str(latest_stdout_path)}")

    # print(f"> {str(latest_stdout_path)}")
    # print()
    # print(stdout)

    steps = []
    for line in stdout.split("\n"):
        if line.startswith(" **** step ---------"):
            step = int(line.replace("**** step ---------", ""))
            steps.append(step)

    if len(steps) == 0:
        return 0.0

    import emout

    data = emout.Emout(root)

    job_elapsed_rate = max(steps[-1] / float(data.inp.nstep), 1e-8)

    return job_elapsed_rate


def parse_job_id(filepath: Path):
    return int(
        str(filepath.name)
        .replace("stdout.", "")
        .replace("stderr.", "")
        .replace(".log", "")
    )


def parse_args_job_status():
    parser = ArgumentParser()

    parser.add_argument("--error", "-e", action="store_true")
    parser.add_argument("--ntail", "-n", type=int, default=5)

    return parser.parse_args()


def job_status():
    args = parse_args_job_status()
    source = "e" if args.error else "o"
    jobs = create_submited_jobs(source=source)

    job_dict = JobHistoryManager()
    job_dict.load()

    for job in jobs:
        if job.jobid in job_dict:
            directory = job_dict[job.jobid].directory
            message = job_dict[job.jobid].message
        else:
            directory = "Not Found"
            message = ""
        print(
            "{} ({}, {}, {}) : {} : {}".format(
                job.jobid, job.status, job.elapse, job.queue, directory, message
            )
        )

        if directory != "Not Found":
            error_flag = "-e" if job.source == "e" else ""
            o_data, _ = call(
                f"latestjob -n {args.ntail} {error_flag} --directory {Path(directory).resolve()}",
                encoding="utf-8",
            )
            print(f"{o_data}")
