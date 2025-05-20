# sweep_tool/renderer.py  ← 新規
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_env_cache = {}  # ディレクトリごとに再利用


def render_template(tpl_path: Path, params: Dict[str, float]) -> str:
    tpl_path = tpl_path.resolve()
    root = tpl_path.parent
    if root not in _env_cache:
        _env_cache[root] = Environment(
            loader=FileSystemLoader(str(root)),
            undefined=StrictUndefined,
            autoescape=False,  # プレーンテキスト
            line_statement_prefix=None,
            line_comment_prefix=None,
        )
    env = _env_cache[root]
    template = env.get_template(tpl_path.name)
    return template.render(**params)
