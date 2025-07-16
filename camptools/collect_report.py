import subprocess
import sys
from datetime import datetime


def run(cmd):
    """シェルコマンドを実行して標準出力＋標準エラーを返す"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout + (("\n[stderr]\n" + result.stderr) if result.stderr else "")


def main(output_path="report.md"):
    sections = [
        ("Report generated", lambda: datetime.now().isoformat(), 'bash'),
        ("Current directory", lambda: run("pwd"), 'bash'),
        (
            "MPIEMSES3D version",
            lambda: run("module load hdf5 fftw; ./mpiemses3D --version"),
            'bash',
        ),
        ("plasma.inp", lambda: run("cat plasma.inp"), 'fortran'),
        ("latestjob -n 100", lambda: run("latestjob -n 100"), 'bash'),
        ("latestjob -n 100 -e", lambda: run("latestjob -n 100 -e"), 'bash'),
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        # ヘッダ
        f.write(f"# Simulation Bug Report\n\n")
        for title, action, style in sections:
            f.write(f"## {title}\n\n")
            f.write(f"```{style}\n")
            try:
                output = action()
            except Exception as e:
                output = f"[Error running section: {e!r}]"
            f.write(output.strip() + "\n")
            f.write("```\n\n")

    print(f"Report written to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
