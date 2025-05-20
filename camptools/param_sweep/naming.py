import math
import re
from typing import Dict, Union

_SI = {
    -8: "y",
    -7: "z",
    -6: "a",
    -5: "f",
    -4: "p",
    -3: "n",
    -2: "u",
    -1: "m",
    0: "",
    1: "k",
    2: "M",
    3: "G",
    4: "T",
    5: "P",
    6: "E",
    7: "Z",
    8: "Y",
}


def _to_si(val: float, sig: int = 3) -> str:
    """工学指数 (×10³) + SI 接頭辞へ変換"""
    if val == 0:
        return "0"
    exp3 = int(math.floor(math.log10(abs(val)) / 3))
    exp3 = max(min(exp3, max(_SI)), min(_SI))
    scaled = val / 10 ** (3 * exp3)
    s = f"{scaled:.{sig}g}".replace("+", "").replace(".", "p")
    return f"{s}{_SI[exp3]}"


def safe(val: Union[int, float], sig: int = 3) -> str:
    """
    数値 → ディレクトリ安全文字列

    ルール
    -------
    ● 整数 (<1 000)            : そのまま           → 12
    ● 整数 (≥1 000)            : SI 接頭辞           → 12k
    ● 0 < |x| < 1              : ミリ表記            → 0.1  → 100m
    ● |x| ≥ 1 または < 1e-3   : 工学指数 + SI       → 7.9e9 → 7p9G
    """
    # --- ゼロ & 整数 -----------------------------------------------
    if isinstance(val, int) or (isinstance(val, float) and val.is_integer()):
        ival = int(val)
        return _to_si(float(ival), sig) if abs(ival) >= 1000 else str(ival)

    # --- 小数 (0 < |x| < 1) → 100m, 2m など ------------------------
    if 0 < abs(val) < 1:
        milli = val * 1_000  # 10^-3 でスケーリング
        # 例: 0.02 → 20, 0.123 → 123
        s = f"{milli:.{sig}g}".replace("+", "").replace(".", "p").rstrip("p")
        return f"{s}m"

    # --- それ以外は工学指数 ----------------------------------------
    return _to_si(val, sig)

