import functools
import re
import subprocess
from dataclasses import dataclass
from os import PathLike
from typing import OrderedDict


def call_command(*cmd,
                 encoding: str = 'utf-8',
                 timeout: int = 30):
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    try:
        outs, errs = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()

    outs_decoded = outs.decode(encoding)
    errs_decoded = errs.decode(encoding)

    return outs_decoded.strip(), errs_decoded.strip()


@dataclass
class QueueLimit:
    name: str
    nprocs: int
    timelimit_hour: float

    def can_accept(self, nprocs: int, execution_time_hour: float):
        return nprocs < self.nprocs and execution_time_hour < self.timelimit_hour


class JobQueue:
    def __init__(self, throw_command, submit_regex):
        self.throw_command = throw_command
        self.submit_regex = submit_regex

    def throw(self, batch_filepath: PathLike,
              print_sdtout: bool = True,
              print_stderr: bool = True) -> int:
        outs, errs = call_command(self.throw_command, batch_filepath)

        if print_sdtout and len(outs) != 0:
            print(outs)

        if print_stderr and len(errs) != 0:
            print(errs)

        return self.extract_jobid(outs, errs)

    def extract_jobid(self, outs: str, errs: str) -> int:
        m = re.match(self.submit_regex, outs)

        if m:
            job_id = int(m.group(1))
            return job_id
        else:
            return -1

    @functools.cached_property
    def queue_limit_dict(self) -> OrderedDict[str, QueueLimit]:
        raise NotImplementedError()

    def minimum_queue_name(self, nprocs: int, execution_time_hour: float):
        for name, queue_limit in self.queue_limit_dict.items():
            if queue_limit.can_accept(nprocs, execution_time_hour):
                return name
        return None


class JobFile:
    def __init__(self, filepath: PathLike):
        self.filepath = filepath
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

    @property
    def nprocs(self):
        raise NotImplementedError()

    @nprocs.setter
    def nprocs(self, value: int):
        raise NotImplementedError()

    @property
    def exec_time(self):
        raise NotImplementedError()

    @exec_time.setter
    def exec_time(self, value):
        raise NotImplementedError()

    @property
    def queue_name(self):
        raise NotImplementedError()

    @queue_name.setter
    def queue_name(self, value):
        raise NotImplementedError()

    def save(self, filepath: PathLike):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(self.lines)
