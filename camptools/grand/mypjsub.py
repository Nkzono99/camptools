import datetime
import math
import os
import re
import subprocess
from argparse import ArgumentParser
from pathlib import Path

import f90nml

from ..jobs import JobHistoryManager

save_file = Path().home() / 'jobs.txt'


def calc_procs(filename):
    nml = f90nml.read(filename)
    nodes_str = nml['mpi']['nodes']
    nodes = list(map(int, nodes_str))
    return nodes[0] * nodes[1] * nodes[2]


def search_rscgrp_in_system_a(nodes, elapse):
    if nodes <= 4 and elapse <= 1:
        return 'ea'
    elif nodes <= 8 and elapse <= 24:
        return 'sa'
    elif nodes <= 32 and elapse <= 24:
        return 'ma'
    elif nodes <= 128 and elapse <= 72:
        return 'la'
    elif nodes <= 256 and elapse <= 240:
        return 'ha'
    else:
        return 'error'


def search_rscgrp_in_system_b(nodes, elapse):
    if nodes <= 4 and elapse <= 1:
        return 'eb'
    elif nodes <= 8 and elapse <= 24:
        return 'sb'
    elif nodes <= 32 and elapse <= 24:
        return 'mb'
    elif nodes <= 128 and elapse <= 72:
        return 'lb'
    else:
        return 'error'


def create_tmpjob(inputfile, jobfile, outputfile, procs=None, elapse=None, system='a', replaces=[]):
    procs = procs or calc_procs(inputfile)
    nodes = int(math.ceil(procs / 40))

    if elapse is None:
        for i, line in enumerate(lines):
            m = re.match(r'#PJM -L elapse=([0-9]+):[0-9]+:[0-9]+')
            if m:
                elapse = m.group(1)

    if system == 'a':
        rscgrp = search_rscgrp_in_system_a(nodes, elapse)
    else:  # if sytem == 'b'
        rscgrp = search_rscgrp_in_system_b(nodes, elapse)

    with open(jobfile, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith('#PJM -L rscgrp'):
            lines[i] = f'#PJM -L rscgrp={rscgrp}\n'
        elif line.startswith('#PJM -L node'):
            lines[i] = f'#PJM -L node={nodes}\n'
        elif line.startswith('#PJM --mpi proc'):
            lines[i] = f'#PJM -L proc={procs}\n'
        else:
            for rep in replaces:
                line = rep(line, procs, nodes, elapse, system)

    with open(outputfile, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def pjsub(filename):
    # execute 'pjsub <job-file>'
    res = subprocess.Popen(
        ['pjsub', filename],
        stdout=subprocess.PIPE)

    # byte to str and show
    res_str = ''.join([line.decode('utf-8')
                       for line in res.stdout.readlines()][:1])
    print(res_str)

    m = re.match(r'\[INFO\] [0-9]+ pjsub Job ([0-9]+) submitted.')

    if m:
        # extracte job_id from response
        job_id = int(m.group(1))
        return job_id
    else:
        return -1


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('jobfile')
    parser.add_argument('--inputfile', '-i', default='plasma.inp')
    parser.add_argument('--output', '-o', default='myjob.sh')
    parser.add_argument('--message', '-m', default='')
    parser.add_argument('--date', action='store_true')
    parser.add_argument('--directory', '-d', default=None)
    parser.add_argument('--system', default='a')
    parser.add_argument('--procs', '-proc', type=int, default=None)
    parser.add_argument('--elapse', '-elapse', type=int, default=None)
    return parser.parse_args()


def nmypjsub():
    args = parse_args()

    if args.directory is not None:
        os.chdir(args.directory)

    jobfile = args.jobfile

    create_tmpjob(args.inputfile, args.jobfile, args.output, system=args.system,
                  procs=args.procs, elapse=args.elapse)
    jobfile = args.output

    job_id = pjsub(jobfile)

    date = ''
    if args.date:
        date = str(datetime.datetime.now())

    JobHistoryManager().save_job(job_id, Path('.').resolve(), args.message, date)


def mypjsub():
    args = parse_args()

    if args.directory is not None:
        os.chdir(args.directory)

    jobfile = args.jobfile

    def replace_mpiexec(line, procs, nodes, elapse, system):
        if line.startswith('mpiexec.hydra') and 'mpiemses3D' in line:
            return f'mpiexec.hydra -n {procs} ./mpiemses3D plasma.inp\n'
        else:
            return line

    create_tmpjob(args.inputfile, args.jobfile, args.output, system=args.system,
                  procs=args.procs, elapse=args.elapse,
                  replaces=[
                      replace_mpiexec
                  ])
    jobfile = args.output

    job_id = pjsub(jobfile)

    date = ''
    if args.date:
        date = str(datetime.datetime.now())

    JobHistoryManager().save_job(job_id, Path('.').resolve(), args.message, date)
