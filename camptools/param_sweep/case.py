import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .naming import safe


@dataclass
class Case:
    params: Dict[str, float]
    root: Path

    def exp_path(self) -> Path:
        parts = [f"{k}{safe(v)}" for k, v in sorted(self.params.items())]
        return self.root / ("exp_" + "_".join(parts))


def expand_params(d: Dict[str, Any]) -> List[Dict[str, Any]]:
    keys = list(d)
    lists = [v if isinstance(v, list) else [v] for v in d.values()]
    return [{k: v for k, v in zip(keys, c)} for c in itertools.product(*lists)]
