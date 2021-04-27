import subprocess
from pathlib import Path
from argparse import ArgumentParser


save_file = Path(__file__).parent / 'jobs.txt'


def call(cmd, encoding='utf-8'):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o_data, e_data = p.communicate()
    return o_data.decode(encoding), e_data.decode(encoding)


def create_job_dict():
    job_dict = {}
    with open(str(save_file), 'r', encoding='utf-8') as f:
        for line in f:
            splited = line.split(':')
            if len(splited) != 2:
                continue
            job_id = int(splited[0].strip())
            directory = splited[1].strip()
            job_dict[job_id] = directory
    return job_dict


class Job:
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


def parse_args():
    parser = ArgumentParser()
    return parser.parse_args()


def create_jobs():
    o_data, e_data = call('qs', encoding='utf-8')
    lines = o_data.split('\n')
    jobs = []
    for line in lines[1:-1]:
        tokens = line.strip().split()
        jobs.append(Job(tokens))
    return jobs


def joblist():
    args = parse_args()
    jobs = create_jobs()

    job_dict = create_job_dict()

    print('=' * 20)

    for job in jobs:
        if job.jobid in job_dict:
            directory = job_dict[job.jobid]
        else:
            directory = 'Not Found'
        print('{} ({}, {}) : {}'.format(
            job.jobid, job.status, job.elapse, directory))

    print('=' * 20)


def job_status():
    args = parse_args()
    jobs = create_jobs()

    for job in jobs:
        print('{}({})'.format(job.jobid, job.status))
        print(job.tail())
        print('')
