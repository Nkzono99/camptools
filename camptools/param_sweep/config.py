import json
import re
import urllib.request
from pathlib import Path
from typing import Any, Dict

import yaml

try:
    import jsonschema
except ModuleNotFoundError:
    jsonschema = None

# float resolver (1e8をfloat値としてロードするため)
_float_re = re.compile(
    r"""^[-+]?([0-9]*\.[0-9]+|[0-9]+(?:\.[0-9]*)?)
                           ([eE][-+]?[0-9]+)?$""",
    re.X,
)
yaml.SafeLoader.add_implicit_resolver(
    "tag:yaml.org,2002:float", _float_re, list("-+0123456789.")
)


def load_yaml(path: str) -> Dict[str, Any]:
    data = yaml.safe_load(open("sweep.yaml"))

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "$schema" in data and jsonschema is not None:
        _validate(data, data["$schema"])
    return data


def _validate(data: Dict[str, Any], schema_path: str):
    if schema_path.startswith(("http://", "https://")):
        schema = json.loads(urllib.request.urlopen(schema_path).read().decode())
    else:
        p = Path(schema_path).expanduser()
        schema = (
            yaml.safe_load(p.read_text())
            if p.suffix in {".yml", ".yaml"}
            else json.loads(p.read_text())
        )
    jsonschema.validate(instance=data, schema=schema)
