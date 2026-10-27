"""The shared settings of the full chain: re-peat/pipeline.yaml, overridden by pipeline.local.yaml (not tracked) when it exists.

Paths may use ${WORKSPACE}, ${REPEAT_DATA}, ${REPEAT_KHG} and any environment variable. REPEAT_DATA and REPEAT_KHG, when set in the
environment, win over the `data` and `khg_root` keys, so a peer can point the whole chain at their own data with two variables.
`load()` also exports REPEAT_HUB, REPEAT_DATA, REPEAT_KHG and the `environment` block, which every step's process inherits.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

HUB = Path(__file__).resolve().parents[2]


def _merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def expand(value, env: dict):
    """${NAME} from ``env`` first, then the environment; nested lists and dicts too. Unknown names are left as they are."""
    if isinstance(value, str):
        return re.sub(r"\$\{(\w+)\}", lambda m: str(env.get(m.group(1), os.environ.get(m.group(1), m.group(0)))), value)
    if isinstance(value, list):
        return [expand(v, env) for v in value]
    if isinstance(value, dict):
        return {k: expand(v, env) for k, v in value.items()}
    return value


class Settings(dict):
    """pipeline.yaml with every path expanded; ``.ws``, ``.data``, ``.khg_root`` as Paths."""

    @property
    def ws(self) -> Path:
        return Path(self["workspace"])

    @property
    def data(self) -> Path:
        return Path(self["data"])

    @property
    def khg_root(self) -> Path:
        return Path(self["khg_root"])

    def python(self, env: str) -> str:
        return self["python"][env]


def load(path: Path | None = None) -> Settings:
    path = Path(path or HUB / "pipeline.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    local = path.with_name("pipeline.local.yaml")
    if local.exists():
        raw = _merge(raw, yaml.safe_load(local.read_text(encoding="utf-8")) or {})
    ws = (HUB / raw["workspace"]).resolve() if not Path(raw["workspace"]).is_absolute() else Path(raw["workspace"])
    env = {"WORKSPACE": str(ws)}
    data = os.environ.get("REPEAT_DATA") or expand(raw["data"], env)
    khg_root = os.environ.get("REPEAT_KHG") or expand(raw["khg_root"], env)
    env.update(REPEAT_DATA=str(Path(data).resolve()), REPEAT_KHG=str(Path(khg_root).resolve()))
    s = Settings(expand(raw, env))
    s["workspace"], s["data"], s["khg_root"] = str(ws), env["REPEAT_DATA"], env["REPEAT_KHG"]
    os.environ.update(REPEAT_HUB=str(HUB), REPEAT_DATA=env["REPEAT_DATA"], REPEAT_KHG=env["REPEAT_KHG"],
                      **{k: str(v) for k, v in (s.get("environment") or {}).items() if v})
    return s
