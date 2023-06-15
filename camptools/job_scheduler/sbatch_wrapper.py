import datetime
import os
from argparse import ArgumentParser
from os import PathLike
from pathlib import Path

import f90nml

from ..jobs import JobHistoryManager
from .core import QueueLimit
from .laurel import LaurelJobFile, LaurelJobQueue
from .throw_job_wrapper import nmythrow, mythrow

save_file = Path().home() / 'jobs.txt'

jobqueue = LaurelJobQueue()


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('job_filepath')
    parser.add_argument('--inputfile', '-i', default='plasma.inp')
    parser.add_argument('--tmpjob_filepath', '-o', default='myjob.sh')
    parser.add_argument('--message', '-m', default='')
    parser.add_argument('--date', action='store_true')
    parser.add_argument('--directory', '-d', default=None)
    parser.add_argument('--nprocs', '-np', type=int, default=None)
    parser.add_argument('--exec_time_hour', '-et', type=int, default=None)
    parser.add_argument('--queue_name', '-qn', default=None)
    return parser.parse_args()


def calc_nprocs(filename):
    nml = f90nml.read(filename)
    nodes_str = nml['mpi']['nodes']
    nodes = list(map(int, nodes_str))
    return nodes[0] * nodes[1] * nodes[2]


def create_tmpjob(job_filepath: PathLike, tmpjob_filepath: PathLike, 
                  nprocs=None, exec_time_hour=None, 
                  queue_name=None):
    jobfile = LaurelJobFile(job_filepath)

    if nprocs:
        jobfile.nprocs = nprocs
    if exec_time_hour:
        jobfile.exec_time_hour = exec_time_hour

    if queue_name:
        jobfile.queue_name = queue_name
    else:
        queue_limit: QueueLimit = jobqueue.queue_limit_dict[jobfile.queue_name]
        if not queue_limit.can_accept(jobfile.nprocs, jobfile.exec_time_hour):
            jobfile.queue_name = jobqueue.minimum_queue_name(jobfile.nprocs, 
                                                                  jobfile.exec_time_hour)

    jobfile.save(tmpjob_filepath)


def nmysbatch():
    
    args = parse_args()

    if args.directory:
        os.chdir(args.directory)

    jobqueue = LaurelJobQueue()
    JobFileClass = LaurelJobFile

    create_tmpjob(args.job_filepath, args.tmpjob_filepath, system=args.system,
                  nprocs=args.nprocs, exec_time_hour=args.exec_time_hour, rscgrp=args.rscgrp)

    job_id = jobqueue.throw(args.tmpjob_filepath)

    date = str(datetime.datetime.now()) if args.date else ''
    JobHistoryManager().save_job(job_id, Path('.').resolve(), args.message, date)


def mysbatch():
    args = parse_args()

    if args.directory:
        os.chdir(args.directory)

    nprocs = args.nprocs or calc_nprocs(args.inputfile)

    create_tmpjob(args.job_filepath, args.tmpjob_filepath,
                  nprocs=nprocs, exec_time_hour=args.exec_time_hour, queue_name=args.queue_name)

    job_id = jobqueue.throw(args.tmpjob_filepath)

    date = ''
    if args.date:
        date = str(datetime.datetime.now())

    JobHistoryManager().save_job(job_id, Path('.').resolve(), args.message, date)
