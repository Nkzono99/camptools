import logging
import subprocess
from pathlib import Path
from typing import List

from .case import Case
from .renderer import render_template


def create_case_dir(case: Case, exp: Path, template: Path):
    logging.info("create %s", exp)

    subprocess.run(["mymkdir", exp], check=True)

    txt = render_template(template, case.params)

    (exp / "plasma.preinp").write_text(txt)
    subprocess.run(["preinp", "-d", exp], check=True)


def run_cases(
    cases: List[Case],
    *,
    run: bool,
    extent: bool,
    dry: bool,
    template: Path,
    queue_name: str,
):
    for case in cases:
        exp = case.exp_path()

        if dry:
            print(exp)
            continue

        if extent:
            if not exp.exists():
                logging.warning("%s not found; skip", exp)
                continue
            cmdlist = ["extentsim", "--run", exp]

            if queue_name is not None:
                cmdlist += ["-qn", queue_name]

            subprocess.run(cmdlist, check=True)
            continue

        if exp.exists():
            logging.info("%s exists; skip", exp)
            continue

        create_case_dir(case, exp, template)

        if run:
            cmdlist = ["mysbatch", "job.sh", "-d", exp]

            if queue_name is not None:
                cmdlist += ["-qn", queue_name]

            subprocess.run(cmdlist, check=True)
