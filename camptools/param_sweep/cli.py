import logging
from argparse import ArgumentParser
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List

from .case import Case, expand_params
from .config import load_yaml
from .runner import run_cases


def _parse_override(s: str) -> Dict[str, float]:
    k, v = s.split("=", 1)
    return {k: float(v)}


def _dict_eq(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    """キーと値が完全一致するか（順不同）。"""
    return a.items() == b.items()


def build_cases(cfg: dict, cli_over: Dict[str, float], cwd: Path) -> List[Case]:
    """
    params の直積をベースに、cases で
      • 追加
      • 値の上書き
      • _skip / _only
    を適用して最終ケース一覧を返す。
    """
    # ------------------------------------------------------------------ ① 直積
    base_cases: List[Dict[str, Any]] = expand_params(cfg.get("params", {}))

    # ------------------------------------------------------------------ ② cases
    add_cases: List[Dict[str, Any]] = []
    only_cases: List[Dict[str, Any]] = []

    for c in cfg.get("cases", []):
        body = {k: v for k, v in c.items() if not k.startswith("_")}  # メタキー除去

        if c.get("_skip"):  # スキップ → base_cases から除外
            base_cases = [bc for bc in base_cases if not _dict_eq(bc, body)]
            continue

        if c.get("_only"):  # _only → 別リストへ
            only_cases.append(body)
            continue

        add_cases.append(body)  # 通常は追加（後でマージ）

    # _only があればそれだけ、無ければ base+add
    effective = only_cases if only_cases else base_cases + add_cases

    # ------------------------------------------------------------------ ③ CLI 上書き
    for d in effective:
        d.update(cli_over)

    # ------------------------------------------------------------------ ④ 重複排除（同じ dict が複数出来得るため）
    uniq: "OrderedDict[frozenset, Dict[str, Any]]" = OrderedDict()
    for d in effective:
        uniq[frozenset(d.items())] = d  # 後勝ち(Until Python 3.8+ insertion order)

    # ------------------------------------------------------------------ ⑤ Case へ
    return [Case(params=p, root=cwd) for p in uniq.values()]


def parse_args():
    ap = ArgumentParser()

    ap.add_argument("yaml")
    ap.add_argument("--set", "-s", action="append", default=[], metavar="NAME=VAL")
    ap.add_argument("--template", default="plasma.preinp")
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


if __name__ == "__main__":
    main()
