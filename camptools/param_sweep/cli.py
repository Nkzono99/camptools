import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict

from .case import Case, expand_params
from .config import load_yaml
from .runner import run_cases


def parse_args():
    ap = ArgumentParser()

    ap.add_argument("yaml")
    ap.add_argument("--set", "-s", action="append", default=[], metavar="NAME=VAL")
    ap.add_argument("--template", default="plasma.preinp.j2")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--extent", action="store_true")
    ap.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()

    return args


def main():
    args = parse_args()

    cfg = load_yaml(args.yaml)
    over = {}
    for s in args.set:
        over.update(_parse_override(s))

    cases = build_cases(cfg, over, Path.cwd())

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    run_cases(
        cases,
        run=args.run,
        extent=args.extent,
        dry=args.dry_run,
        template=Path(args.template),
    )


def _parse_override(s: str) -> Dict[str, float]:
    k, v = s.split("=", 1)
    return {k: float(v)}


def build_cases(cfg: dict, cli_over: Dict[str, float], cwd: Path):
    raw_blocks = cfg.get("cases", [])
    # ① 各ブロックを expand_params で展開してリスト化
    all_dicts = []
    for block in raw_blocks:
        # メタキー (_skip/_only) を除いた純パラメータ dict
        params_dict = {k: v for k, v in block.items() if not k.startswith("_")}
        # 直積展開
        for combo in expand_params(params_dict):
            # 同じ block の _skip/_only は展開後の全ケースに継承
            combo["_skip"] = block.get("_skip", False)
            combo["_only"] = block.get("_only", False)
            all_dicts.append(combo)

    # ② _only/_skip を処理
    only_mode = any(d.get("_only") for d in all_dicts)
    filtered = []
    for d in all_dicts:
        if d.get("_skip"):
            continue
        if only_mode and not d.get("_only"):
            continue
        filtered.append(d)

    # ③ CLI オーバーライドをマージ
    for d in filtered:
        d.update(cli_over)

    # ④ Case オブジェクト化
    return [
        Case(
            params={k: v for k, v in d.items() if k not in ("_skip", "_only")}, root=cwd
        )
        for d in filtered
    ]


if __name__ == "__main__":
    main()
