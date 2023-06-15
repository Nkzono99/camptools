import functools
import re
import sys
from collections import OrderedDict
from typing import OrderedDict

from .core import JobFile, JobQueue, QueueLimit, call_command


class LaurelJobQueue(JobQueue):
    def __init__(self):
        super().__init__('sbatch', r'Submitted batch job ([0-9]+)')

    @functools.cached_property
    def queue_limit_dict(self) -> OrderedDict[str, QueueLimit]:
        odict = OrderedDict()

        outs, errs = call_command('sinfo')

        lines = outs.split('\n')
        for line in lines[1:]:
            regex = r'(\w+)\s+(\w+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
            m = re.match(regex, line.strip())
            if not m:
                continue

            partition, avail, defaulttime, timelimit, sock, core, thre, memory = m.groups()

            regex = r'(([0-9]+)-)?(\d+):(\d+):(\d+)'
            m = re.match(regex, timelimit)

            _, day, hour, minutes, sec = m.groups()
            day = day or 0
            day, hour, minutes, sec = map(int, (day, hour, minutes, sec))

            timelimit_hour = 24*day + hour + minutes/60 + sec/3600

            odict[partition] = QueueLimit(
                partition, sys.maxsize, timelimit_hour)
        return odict


class LaurelJobFile(JobFile):
    @property
    def nprocs(self):
        p = re.compile(r'#SBATCH --rsc p=(\d+)')
        for line in self.lines:
            m = p.match(line)
            if m:
                return int(m.group(1))
        return None

    @nprocs.setter
    def nprocs(self, nprocs: int):
        p = re.compile(r'#SBATCH --rsc p=(\d+)')
        for i in range(len(self.lines)):
            self.lines[i] = p.sub(f'#SBATCH --rsc p={nprocs}', self.lines[i])

    @property
    def exec_time_hour(self):
        p = re.compile(r'#SBATCH -t (\d+):(\d+):(\d+)')
        for line in self.lines:
            m = p.match(line)
            if m:
                hour, minutes, sec = map(int, m.groups())
                return hour + minutes/60 + sec/60
        return None

    @exec_time_hour.setter
    def exec_time_hour(self, exec_time_hour):
        p = re.compile(r'#SBATCH -t (\d+):(\d+):(\d+)')
        hour = int(exec_time_hour)
        minutes = int((exec_time_hour - hour)*60)
        sec = int((exec_time_hour - hour - minutes/60)*3600)
        for i in range(len(self.lines)):
            self.lines[i] = p.sub(
                f'#SBATCH -t {hour}:{minutes}:{sec}', self.lines[i])

    @property
    def queue_name(self):
        p = re.compile(r'#SBATCH -p (\S+)')
        for line in self.lines:
            m = p.match(line)
            if m:
                return m.group(1)
        return None

    @queue_name.setter
    def queue_name(self, queue_name):
        p = re.compile(r'#SBATCH -p (\S+)')
        for i in range(len(self.lines)):
            self.lines[i] = p.sub(f'#SBATCH -p {queue_name}', self.lines[i])

