#!/usr/bin/env python3
"""
Environment setup tool:
- Creates /LARGE0/{group}/{USER} and ~/large0 symlink
- Appends module/PATH lines to ~/.bashrc
- Clones & builds MPIEMSES3D
- Sets up .camptools, .logs, copylist.json, example notebook, job script
- Merges VS Code settings into ~/.vscode-server/data/Machine/settings.json
- Opens VS Code on key files
"""

import argparse
import getpass
import json
import logging
import subprocess
import sys
import textwrap
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(
        description="Setup user environment: dirs, links, configs, examples."
    )
    p.add_argument(
        "-g", "--group_name", default="gr20001", help="Group name under /LARGE0"
    )
    p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    p.add_argument("--no-git", action="store_true", help="Skip git clone & build")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s"
    )

    # 1) LARGE0 & symlink
    root, link = create_large0(args.group_name, args.verbose)

    # 2) ~/.bashrc
    update_bashrc(args.verbose)

    # 3) Clone & build
    repo_dir = clone_and_build(link, args.no_git, args.verbose)

    # 4) camptools & logs
    camptools_dir, logs_file = setup_camptools(link, args.verbose)

    # 5) copylist.json
    write_copylist(repo_dir, camptools_dir, args.verbose)

    # 6) job script & notebook
    write_job_script(camptools_dir, args.group_name, args.verbose)
    write_notebook(camptools_dir, args.verbose)

    # 7) plot script
    plot_script = write_plot_py(link, args.verbose)

    # 8) VS Code settings
    merge_vscode_settings(link, args.verbose)

    # 9) Open VS Code
    files_to_open = [
        str(link),
        str(plot_script),
        str(camptools_dir / "job.sh"),
        str(camptools_dir / "copylist.json"),
        str(link / ".vscode" / "settings.json"),
    ]
    open_vscode(files_to_open, args.verbose)

    logging.info("Setup completed successfully.")


def run_cmd(cmd: str, verbose: bool):
    if verbose:
        logging.info(f"$ {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode:
        logging.error(f"Command failed ({res.returncode}): {cmd}")
        sys.exit(res.returncode)


def ensure_line(line: str, filepath: Path, verbose: bool):
    filepath = filepath.expanduser()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    text = filepath.read_text(encoding="utf-8") if filepath.exists() else ""
    if line not in text:
        filepath.open("a", encoding="utf-8").write(line + "\n")
        if verbose:
            logging.info(f"Appended to {filepath}: {line}")


def merge_json(dst: Path, updates: dict, verbose: bool):
    dst = dst.expanduser()
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(dst.read_text(encoding="utf-8")) if dst.exists() else {}
    except Exception:
        existing = {}
    existing.update(updates)
    dst.write_text(json.dumps(existing, indent=4), encoding="utf-8")
    if verbose:
        logging.info(f"Merged into JSON: {dst}")


def create_large0(group: str, verbose: bool):
    user = getpass.getuser()
    root = Path(f"/LARGE0/{group}/{user}")
    link = Path.home() / "large0"

    root.mkdir(parents=True, exist_ok=True)
    if verbose:
        logging.info(f"Ensured directory: {root}")

    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(root, target_is_directory=True)
    if verbose:
        logging.info(f"Symlink: {link} → {root}")

    return root, link


def update_bashrc(verbose: bool):
    bashrc = Path.home() / ".bashrc"
    ensure_line("module load intel-python", bashrc, verbose)
    ensure_line('export PATH="$PATH:$HOME/.local/bin"', bashrc, verbose)


def clone_and_build(large0_link: Path, skip_git: bool, verbose: bool):
    github_dir = large0_link / "Github"
    github_dir.mkdir(parents=True, exist_ok=True)

    repo = github_dir / "MPIEMSES3D"
    if not repo.exists() and not skip_git:
        run_cmd(
            f"git clone https://github.com/CS12-Laboratory/MPIEMSES3D.git {repo}",
            verbose,
        )
        run_cmd(f"make -C {repo}", verbose)
    elif verbose:
        logging.info(f"Repo present or skipped: {repo}")

    return repo


def setup_camptools(large0_link: Path, verbose: bool):
    camptools = large0_link / ".camptools"
    camptools.mkdir(parents=True, exist_ok=True)
    logs = camptools / ".logs"
    logs.touch(exist_ok=True)
    if verbose:
        logging.info(f"Setup camptools dir: {camptools}, logs: {logs}")
    return camptools, logs


def write_copylist(repo: Path, camptools: Path, verbose: bool):
    data = {
        "main": [
            str((repo / "bin/mpiemses3D").resolve()),
            str((camptools / "job.sh").resolve()),
            str((camptools / "plot_example.ipynb").resolve()),
            str((camptools / ".logs").resolve()),
        ],
        "emses": [
            str((repo / "bin/mpiemses3D").resolve()),
        ],
    }
    path = camptools / "copylist.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if verbose:
        logging.info(f"Wrote copylist: {path}")


def write_job_script(camptools: Path, group: str, verbose: bool):
    job = camptools / "job.sh"
    job.write_text(
        textwrap.dedent(
            f"""\
        #!/bin/bash
        #SBATCH -p {group}a
        #SBATCH --rsc p=32:t=1:c=1
        #SBATCH -t 120:00:00
        #SBATCH -o stdout.%J.log
        #SBATCH -e stderr.%J.log

        module load intel/2023.2 intelmpi/2023.2
        module load hdf5/1.12.2_intel-2023.2-impi
        module load fftw/3.3.10_intel-2022.3-impi
        module list

        if [ -f ./plasma.preinp ]; then
            preinp
        fi

        export EMSES_DEBUG=no
        date
        rm *_0000.h5
        srun ./mpiemses3D plasma.inp
        date

        # Postprocessing
        mypython plot_example.py ./
    """
        ),
        encoding="utf-8",
    )
    job.chmod(0o755)
    if verbose:
        logging.info(f"Created job script: {job}")


def write_notebook(camptools: Path, verbose: bool):
    nb = camptools / "plot_example.ipynb"
    content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import emout\n",
                    "import numpy as np\n",
                    "import matplotlib.pyplot as plt\n",
                    "import scipy.constants as cn\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["data = emout.Emout()\n"],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["data.phisp[-1, :, int(data.inp.ny//2), :].plot()\n"],
            },
        ],
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 2,
    }
    nb.write_text(json.dumps(content, indent=2), encoding="utf-8")
    if verbose:
        logging.info(f"Created notebook: {nb}")


def write_plot_py(large0_link: Path, verbose: bool):
    mypy = large0_link / ".mypython"
    mypy.mkdir(parents=True, exist_ok=True)
    script = mypy / "plot_example.py"
    script.write_text(
        textwrap.dedent(
            f"""\
        import emout

        data = emout.Emout()

        data.phisp[-1, :, int(data.inp.ny//2), :].plot(savefilename='data/phisp.png')
        """
        ),
        encoding="utf-8",
    )
    if verbose:
        logging.info(f"Created plot script: {script}")
    return script


def merge_vscode_settings(large0_link: Path, verbose: bool):
    settings = {
        "files.exclude": {
            "**/.git": True,
            "**/.svn": True,
            "**/.hg": True,
            "**/.DS_Store": True,
            "**/Thumbs.db": True,
            "**/*.h5": True,
            "**/*.i90": True,
            "**/*.mod": True,
            "**/*.o": True,
            "**/*xdmf": True,
            "**/chgacm*": True,
            "**/chgmov": True,
            "**/currnt": True,
            "**/energy": True,
            "**/energy1": True,
            "**/energy2": True,
            "**/ewave": True,
            "**/icur": True,
            "**/influx": True,
            "**/isflux": True,
            "**/mpiemses3D": True,
            "**/nesc": True,
            "**/noflux": True,
            "**/ocur": True,
            "**/oltime": True,
            "**/pbody": True,
            "**/pbodyd": True,
            "**/pbodyr": True,
            "**/seyield": True,
            "**/volt": True,
            "**/*.obj": True,
            "**/*.smod": True,
            "**/SNAPSHOT1": True,
            "**/plasma.out": True,
        },
        "files.associations": {
            "*.inp": "FortranFreeForm",
            "*.preinp": "FortranFreeForm",
            "*.xdmf": "xml",
        },
        "explorer.fileNesting.enabled": True,
        "explorer.fileNesting.patterns": {
            "plot_example.ipynb": "*.ipynb",
            ".logs": "*.log",
            "job.sh": "job.sh, myjob.sh",
            "plasma.preinp": "plasma.inp, plasma.preinp, *.xlsx",
        },
        "explorer.fileNesting.expand": False,
        "workbench.tree.indent": 15,
    }
    dst = large0_link / ".vscode" / "settings.json"
    merge_json(dst, settings, verbose)


def open_vscode(files: list, verbose: bool):
    cmd = f"code -n {' '.join(files)}"
    run_cmd(cmd, verbose)


if __name__ == "__main__":
    main()
