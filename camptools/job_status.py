from argparse import ArgumentParser
from pathlib import Path

from .jobs import JobHistoryManager, create_submited_jobs
from .utils import call


def parse_args_joblist():
    parser = ArgumentParser()
    return parser.parse_args()


def joblist():
    args = parse_args_joblist()
    jobs = create_submited_jobs()

    job_dict = JobHistoryManager()
    job_dict.load()

    print("=" * 20)

    for job in jobs:
        if job.jobid in job_dict:
            directory = job_dict[job.jobid].directory
            message = job_dict[job.jobid].message
        else:
            directory = "Not Found"
            message = ""
        print(
            "{} ({}, {}) : {} : {}".format(
                job.jobid, job.status, job.elapse, directory, message
            )
        )

    print("=" * 20)


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
            "{} ({}, {}) : {} : {}".format(
                job.jobid, job.status, job.elapse, directory, message
            )
        )

        if directory != "Not Found":
            error_flag = "-e" if job.source == "e" else ""
            o_data, _ = call(
                f"latestjob -n {args.ntail} {error_flag} --directory {Path(directory).resolve()}",
                encoding="utf-8",
            )
            print(f"{o_data}")
