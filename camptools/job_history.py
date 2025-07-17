from .jobs import JobHistoryManager, create_submited_jobs
from argparse import ArgumentParser

import colorama


def parse_args():
    parser = ArgumentParser()

    parser.add_argument("--correct_date", "-cd", action="store_true")
    parser.add_argument("--nshow", "-n", type=int, default=-1)

    return parser.parse_args()


def job_history():
    args = parse_args()
    queued_jobs = create_submited_jobs()

    job_dict = JobHistoryManager()
    job_dict.load()

    if args.correct_date:
        job_dict.correct_date()
        job_dict.save()

    jobs = list(job_dict.dict.values())
    jobs_show = jobs[-args.nshow:]

    status_colors = {
        "RUN": colorama.Fore.GREEN,
        "PEND": colorama.Fore.LIGHTBLACK_EX,
        "FINI": colorama.Fore.CYAN,
        "CANC": colorama.Fore.RED,
    }

    for job in jobs_show:
        color = colorama.Fore.WHITE
        for qjob in queued_jobs:
            if qjob.jobid == job.job_id:
                color = status_colors.get(qjob.status, colorama.Fore.WHITE)

        print(color + str(job) + colorama.Style.RESET_ALL)
