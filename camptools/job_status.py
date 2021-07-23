from argparse import ArgumentParser
from pathlib import Path

from .jobs import JobDict
from .utils import call


class JobInfo:
    def __init__(self, tokens, encoding='utf-8'):
        self.queue = tokens[0]
        self.user = tokens[1]
        self.jobid = int(tokens[2])
        self.status = tokens[3]
        self.proc = int(tokens[4])
        self.thread = int(tokens[5])
        self.core = int(tokens[6])
        self.memory = int(tokens[7].replace('G', ''))
        self.elapse = tokens[8]

        self.encoding = encoding

    def tail(self):
        o_data, _ = call('qcat -o {} | tail'.format(self.jobid),
                         encoding=self.encoding)
        return o_data


def create_jobs():
    o_data, e_data = call('qs', encoding='utf-8')
    lines = o_data.split('\n')
    jobs = []
    for line in lines[1:-1]:
        tokens = line.strip().split()
        jobs.append(JobInfo(tokens))
    return jobs


def parse_args():
    parser = ArgumentParser()
    return parser.parse_args()


def joblist():
    args = parse_args()
    jobs = create_jobs()

    job_dict = JobDict()
    job_dict.load()

    print('=' * 20)

    for job in jobs:
        if job.jobid in job_dict:
            directory = job_dict[job.jobid].directory
            message = job_dict[job.jobid].message
        else:
            directory = 'Not Found'
            message = ''
        print('{} ({}, {}) : {} : {}'.format(
            job.jobid, job.status, job.elapse, directory, message))

    print('=' * 20)


def job_status():
    args = parse_args()
    jobs = create_jobs()

    job_dict = JobDict()
    job_dict.load()

    for job in jobs:
        if job.jobid in job_dict:
            directory = job_dict[job.jobid].directory
            message = job_dict[job.jobid].message
        else:
            directory = 'Not Found'
            message = ''
        print('{} ({}, {}) : {} : {}'.format(
            job.jobid, job.status, job.elapse, directory, message))
        print(job.tail())
        print('')
