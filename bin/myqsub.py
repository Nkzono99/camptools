from argparse import ArgumentParser

import f90nml
from pathlib import Path
import subprocess


save_file = Path(__file__).parent / 'jobs.txt'


def calc_procs(filename):
    nml = f90nml.read(filename)
    nodes_str = nml['mpi']['nodes']
    nodes = list(map(int, nodes_str))
    return nodes[0] * nodes[1] * nodes[2]


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('jobfile')
    parser.add_argument('--inputfile', '-i', default='plasma.inp')
    parser.add_argument('--output', '-o', default='myjob.sh')
    parser.add_argument('--noem', action='store_true')
    return parser.parse_args()


def create_emjob(inputfile, jobfile, outputfile):
    procs = calc_procs(inputfile)
    nodes = procs // 64

    with open(jobfile, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith('#QSUB -A'):
            lines[i] = '#QSUB -A p={}:t=1:c=64:m=90G\n'.format(nodes)
        elif line.startswith('aprun'):
            lines[i] = 'aprun -n {} -d 1 -N 64 ./mpiemses3D plasma.inp\n'.format(
                procs)

    with open(outputfile, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def qsub(filename):
    res = subprocess.Popen(
        ['qsub', filename],
        stdout=subprocess.PIPE)
    return [line.decode('utf-8') for line in res.stdout.readlines()]


def main():
    args = parse_args()

    jobfile = args.jobfile
    if not args.noem:
        create_emjob(args.inputfile, args.jobfile, args.output)
        jobfile = args.output        

    res = qsub(jobfile)[:1]
    print(''.join(res))
    job_id = int(res[0].replace('.ja', '').strip())
    
    save_file.touch(exist_ok=True)
    with open(str(save_file), 'a', encoding='utf-8') as f:
        f.write('{}: {}\n'.format(job_id, Path('.').resolve()))


if __name__ == '__main__':
    main()

