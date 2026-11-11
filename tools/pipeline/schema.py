"""The schema of the chain's settings: what can be set, where, with what type, unit, allowed values and default.

Three layers, merged in this order (later wins):
  pipeline.yaml (+ pipeline.local.yaml)  the national template: `Pipeline`
  sites/<folder>/khg.yaml                generated facts of one KHG (`init`, never edited): `KhgFile`
  sites/<folder>/overrides.yaml          hand-written exceptions of one KHG, each with a reason and a date: `Overrides`
`steps:` in overrides.yaml takes any key of the step sections of pipeline.yaml (dem_correction, delineation, neraca,
prioritisation, pump) for that KHG only. `pump.set` takes any key of repeat-pump's own run config (repeat_pump.core.config.Config,
checked with the pump's interpreter, since that package lives in the pump environment).

Used by `khg_pipeline.py config schema | show | validate | catalogue`. Every field carries an English title, an Indonesian label
(`label_id`) and a description; docs/21-configuration.md is generated from them, and a future settings API or web form reads the
same JSON Schema (`config schema`).
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

Dem = Literal["lidar", "deltadtm", "demnas"]
StepName = Literal["inputs", "dem_inputs", "icesat2", "local_inputs", "dem_correction", "delineation", "deficit", "neraca",
                   "prioritisation", "pump", "layouts"]
PeatSource = Literal["modelled raster", "FEG 50k classes", "BBSDLP classes", "PEATGRIDS (low confidence)"]
STEP_SECTIONS = ("dem_correction", "delineation", "neraca", "prioritisation", "pump")


def _products(var: str, fallback: tuple) -> tuple:
    """Rain (P) or ET products the water balance can fetch: repeat_common.fetch_gee_balance.PRODUCTS, so the schema follows the code."""
    try:
        from repeat_common.fetch_gee_balance import PRODUCTS
        return tuple(k for k, v in PRODUCTS.items() if v.get("var") == var) or fallback
    except Exception:  # noqa: BLE001  (an environment without repeat-common: the products of 2026-11-11)
        return fallback


RainProduct = Literal[_products("P", ("chirps", "imerg", "terraclimate_pr"))]
EtProduct = Literal[_products("ET", ("wapor", "mod16", "mod16nrt", "terraclimate_aet"))]


def F(default=..., *, en: str, id: str, desc: str, unit: str | None = None, **kw):
    """A field with an English title, an Indonesian label and a description (and a unit, when there is one)."""
    extra = {"label_id": id, **({"unit": unit} if unit else {})}
    return Field(default, title=en, description=desc, json_schema_extra=extra, **kw)


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")       # unknown keys are typos: they fail instead of being silently ignored


# ---------------------------------------------------------------- national template (pipeline.yaml)

class NationalFile(_M):
    path: str = F(en="File", id="Berkas", desc="Path inside the data folder")
    layer: Optional[str] = F(None, en="Layer", id="Lapisan", desc="Layer of a multi-layer file (GeoPackage)")
    where: Optional[str] = F(None, en="Filter", id="Filter", desc="pandas query applied to the attribute table")
    field: Optional[str] = F(None, en="Field", id="Kolom", desc="Attribute used to select features")
    values: Optional[list[str]] = F(None, en="Values", id="Nilai", desc="Values of `field` that are kept")


class National(_M):
    boundary: NationalFile = F(en="KHG boundaries", id="Batas KHG", desc="KHG polygons (SK.129/MENLHK/2017), matched by registry code")
    canals: NationalFile = F(en="Canals", id="Kanal", desc="Canal lines with a class field (Kanal Primer / Sekunder / Tersier)")
    rivers: NationalFile = F(en="Rivers", id="Sungai", desc="River lines (RBI)")
    lakes: NationalFile = F(en="Lakes", id="Danau dan waduk", desc="Lakes and reservoirs (RBI)")
    blocks: NationalFile = F(en="Existing canal blocks", id="Sekat kanal eksisting", desc="Built canal blocks (BRGM)")
    burnt_area: NationalFile = F(en="Burnt area", id="Area terbakar", desc="Burnt-area polygons with year")
    protected: NationalFile = F(en="Protected peat function", id="Fungsi lindung gambut", desc="FEG polygons with the protection class")
    peat_depth_dirs: list[str] = F(en="Peat-depth raster folders", id="Folder raster kedalaman gambut",
                                   desc="Folders searched for one modelled peat-depth raster per KHG (found by overlap)")
    lidar_dirs: list[str] = F(en="LiDAR folders", id="Folder LiDAR", desc="Folders holding airborne LiDAR DTMs")


class Dems(_M):
    variants: list[Dem] = F(en="DEMs the chain knows", id="DEM yang dikenal", desc="Every DEM variant; the chain runs once per DEM")
    default: list[Dem] = F(en="DEMs run by default", id="DEM bawaan", desc="Variants run when `run` gets no --dem. DEMNAS is "
                           "optional: its sheets download only with the user's own Tanahair link (TANAHAIR_LINK)")
    min_cover_pct: float = F(en="Minimum DEM coverage", id="Cakupan DEM minimum", unit="%", gt=0, le=100,
                             desc="A variant runs only when its DEM covers at least this share of the KHG")

    @model_validator(mode="after")
    def _default_in_variants(self):
        bad = set(self.default) - set(self.variants)
        if bad:
            raise ValueError(f"default lists DEMs that are not variants: {sorted(bad)}")
        return self


class DemCorrection(_M):
    templates: str = F(en="Correction templates", id="Templat koreksi", desc="repeat-dem config per DEM; {dem} is replaced")
    icesat2_period: tuple[dt.date, dt.date] = F(en="ICESat-2 period", id="Periode ICESat-2",
                                                desc="First and last day of the ICESat-2 ATL08 ground points used")


class Delineation(_M):
    outlet_canal_classes: list[str] = F(en="Outlet canal classes", id="Kelas kanal outlet",
                                        desc="Canal classes whose ends become outlets of sub-KHG units")
    min_area_km2: Union[Literal["auto"], Annotated[float, Field(gt=0)]] = F(en="Minimum unit area", id="Luas unit minimum", unit="km²",
                                                    desc="Smallest sub-KHG unit; `auto` aims at 6-30 units per KHG")
    merge: Literal["adjacent", "flow"] = F(en="Merge rule", id="Aturan penggabungan",
                                           desc="Small pieces merge into the neighbour with the longest shared border (adjacent) "
                                                "or preferably across the divide (flow)")


class Neraca(_M):
    rain: RainProduct = F(en="Rainfall product", id="Produk curah hujan", desc="Rainfall source of the water balance")
    et: list[EtProduct] = F(en="Evapotranspiration products", id="Produk evapotranspirasi",
                                                    desc="ET sources; the balance reports each")
    start: dt.date = F(en="Start date", id="Tanggal mulai", desc="First day of the balance")
    end: dt.date = F(en="End date (exclusive)", id="Tanggal akhir (eksklusif)", desc="First day after the last complete dekad")
    workers: int = F(en="Parallel requests", id="Permintaan paralel", ge=1, le=32, desc="Parallel Earth Engine requests")
    window: tuple[dt.date, dt.date] = F(en="Deficit window", id="Jendela defisit", desc="SiTMAT window of the KHG deficit")

    @model_validator(mode="after")
    def _order(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class Prioritisation(_M):
    years: dict[Literal["baseline", "validation", "elnino"], list[int]] = F(en="Years", id="Tahun",
                                                                            desc="Baseline, validation and El Niño years")
    ndmi_res_m: int = F(en="NDMI resolution", id="Resolusi NDMI", unit="m", gt=0, desc="Grid of the Sentinel-2 moisture index")
    ipg_canal_classes: list[str] = F(en="Canal classes for the IPG", id="Kelas kanal untuk IPG", desc="Canals counted in the drainage indicator")
    national_profile: str = F(en="National profile config", id="Konfigurasi profil nasional", desc="repeat-prioritisation national profile")


class Layouts(_M):
    papers: list[Literal["A0", "A1", "A2", "A3", "A4"]] = F(en="Paper sizes", id="Ukuran kertas", desc="KLH print layouts")
    orient: list[Literal["landscape", "portrait"]] = F(en="Orientation", id="Orientasi", desc="Page orientation")


class Pump(_M):
    tertiary: bool = F(en="Include tertiary canals", id="Sertakan kanal tersier", desc="Off by default, as in the KLH guide")
    layouts: Layouts = F(en="Print layouts", id="Tata letak cetak", desc="KLH print layouts (need QGIS)")
    set: dict[str, Any] = F(default_factory=dict, en="Pump run-config values", id="Nilai konfigurasi pompa",
                            desc="Any key of repeat-pump's run config, dotted (e.g. interventions.held_target: 0.6); wins over the "
                                 "template and the proposed defaults; checked against repeat_pump.core.config.Config")


class Pipeline(_M):
    workspace: str = F(en="Workspace", id="Ruang kerja", desc="Folder holding re-peat and the module repositories")
    data: str = F(en="Data folder", id="Folder data", desc="The shared data folder (REPEAT_DATA)")
    khg_root: str = F(en="KHG work folders", id="Folder kerja KHG", desc="Per-KHG work folders (REPEAT_KHG)")
    repos: dict[str, str] = F(en="Repositories", id="Repositori", desc="Module repositories (git URLs)")
    python: dict[Literal["main", "dem", "delineation", "pump", "qgis"], str] = F(en="Interpreters", id="Interpreter",
                                                                                  desc="Python of each environment")
    environment: dict[str, Optional[str]] = F(en="Environment", id="Variabel lingkungan", desc="Passed to every step (EE_PROJECT, ...)")
    khg_list: str = F(en="Selected KHG list", id="Daftar KHG terpilih", desc="CSV of the selected KHG")
    extra_khg: list[str] = F(default_factory=list, en="Extra KHG", id="KHG tambahan", desc="Codes added to the list")
    national: National
    dems: Dems
    steps: list[StepName] = F(en="Steps", id="Langkah", desc="The steps, in order")
    dem_correction: DemCorrection
    delineation: Delineation
    neraca: Neraca
    prioritisation: Prioritisation
    pump: Pump


SECTION_MODELS = {"dem_correction": DemCorrection, "delineation": Delineation, "neraca": Neraca,
                  "prioritisation": Prioritisation, "pump": Pump}


# ---------------------------------------------------------------- one KHG (khg.yaml, overrides.yaml)

class KhgId(_M):
    code: str = F(en="KHG code", id="Kode KHG", desc="Registry code without the KHG. prefix", pattern=r"^\d{2}[\d\-.]+$")
    name: str = F(en="Name", id="Nama", desc="KHG name as in the boundary file")
    folder: str = F(en="Work folder", id="Folder kerja", desc="Folder name under the KHG root")
    island: str = F("", en="Island", id="Pulau", desc="From the registry")
    province: str = F("", en="Province", id="Provinsi", desc="From the registry")
    kabupaten: str = F("", en="Regency", id="Kabupaten", desc="From the registry")
    role: str = F("national", en="Role", id="Peran", desc="main, reserve, extra or national")
    tz_hours: Optional[Literal[7, 8, 9]] = F(None, en="Time zone", id="Zona waktu", unit="UTC+h", desc="WIB 7, WITA 8, WIT 9")
    utm_epsg: Optional[int] = F(None, en="UTM zone", id="Zona UTM", desc="EPSG code of the KHG's UTM zone", ge=32600, le=32760)


class DemEntry(_M):
    product: Optional[str] = F(None, en="Product", id="Produk", desc="DEM product of the clip")
    clip: Optional[str] = F(None, en="Clip", id="Potongan", desc="The DEM clipped to the KHG (01_dem/inputs)")
    cover_pct: Optional[float] = F(None, en="Coverage", id="Cakupan", unit="%", ge=0, le=100, desc="Share of the KHG the DEM covers")
    sources: Optional[list[str]] = F(None, en="Source files", id="Berkas sumber", desc="Files the clip was made from")
    planned: Optional[bool] = F(None, en="Planned", id="Direncanakan", desc="True until the dem_inputs step has clipped the DEM")
    skip: Optional[str] = F(None, en="Skip (reason)", id="Lewati (alasan)", desc="The variant does not run, for this reason")


class PeatDepth(_M):
    source: Optional[PeatSource] = F(None, en="Source", id="Sumber", desc="Where the KHG's peat depth comes from")
    path: Optional[str] = F(None, en="Raster", id="Raster", desc="Peat-depth raster (modelled raster, or your own file)")
    scale: float = F(0.01, en="Scale to metres", id="Faktor ke meter", desc="Raster value x scale = depth in m (0.01 for cm)", gt=0)
    valid_share: Optional[float] = F(None, en="Valid share", id="Porsi valid", ge=0, le=1, desc="Share of the KHG with depth > 0")
    cover_share: Optional[float] = F(None, en="Class coverage", id="Cakupan kelas", ge=0, le=1, desc="Share covered by the class map")
    confidence: Optional[Literal["low"]] = F(None, en="Confidence", id="Tingkat keyakinan", desc="low for PEATGRIDS")

    @model_validator(mode="after")
    def _path_for_raster(self):
        if self.source == "modelled raster" and not self.path:
            raise ValueError("source 'modelled raster' needs a path")
        return self


class Canals(_M):
    class_field: str = F("KET_KANAL", en="Canal class field", id="Kolom kelas kanal", desc="Field with Kanal Primer / Sekunder / Tersier")


class KhgFile(_M):
    khg: KhgId
    dems: dict[Dem, DemEntry]
    peat_depth: Optional[PeatDepth] = None
    canals: Canals = Canals()
    facts: dict[str, Any] = F(default_factory=dict, en="Facts", id="Fakta", desc="From the availability table; no step reads them")
    overrides: dict[str, Any] = F(default_factory=dict, en="Legacy step overrides", id="Penimpaan lama",
                                  desc="Old place of step overrides; use overrides.yaml `steps`")


class StepOverrides(_M):
    """Partial step sections: any key of the pipeline.yaml section, for this KHG only (checked after merging)."""
    dem_correction: dict[str, Any] = {}
    delineation: dict[str, Any] = {}
    neraca: dict[str, Any] = {}
    prioritisation: dict[str, Any] = {}
    pump: dict[str, Any] = {}


class Overrides(_M):
    khg: dict[str, Any] = {}
    dems: dict[Dem, dict[str, Any]] = {}
    peat_depth: Optional[dict[str, Any]] = None
    canals: dict[str, Any] = {}
    steps: StepOverrides = StepOverrides()


# ---------------------------------------------------------------- checks

def errors(model, data: dict, where: str) -> list[str]:
    try:
        model.model_validate(data)
        return []
    except ValidationError as e:
        return [f"{where}: {'.'.join(str(x) for x in err['loc']) or '(top)'}: {err['msg']}" for err in e.errors()]


def pump_schema(pump_python: str) -> dict | None:
    """JSON Schema of repeat-pump's run config, from the pump interpreter (None when it cannot be run)."""
    code = "import json; from repeat_pump.core.config import Config; print(json.dumps(Config.model_json_schema()))"
    try:
        r = subprocess.run([pump_python, "-c", code], capture_output=True, text=True, timeout=120)
        return json.loads(r.stdout) if r.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def pump_key_ok(schema: dict, key: str) -> bool:
    """Whether a dotted key exists in the pump config schema (following $ref and Optional)."""
    defs = schema.get("$defs", {})

    def resolve(node):
        while True:
            if "$ref" in node:
                node = defs[node["$ref"].split("/")[-1]]
            elif "anyOf" in node:
                objs = [n for n in node["anyOf"] if "$ref" in n or n.get("type") == "object"]
                if not objs:
                    return node
                node = objs[0]
            else:
                return node

    node = schema
    for part in key.split("."):
        node = resolve(node)
        props = node.get("properties")
        if props is None:
            return bool(node.get("additionalProperties"))        # a free mapping (e.g. canal_class_map)
        if part not in props:
            return False
        node = props[part]
    return True


def validate_khg(s, code: str, pump_sch: dict | None = None) -> list[str]:
    """Problems of one KHG's merged settings: the three layers against the schema, files that must exist, pump keys."""
    import yaml
    from . import khgconf
    out = []
    p = khgconf.path_of(code)
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None
    if raw is None:
        return [f"{code}: khg.yaml missing (init --khg {code})"]
    out += errors(KhgFile, raw, f"{p.parent.name}/khg.yaml")
    ovf = p.with_name("overrides.yaml")
    if ovf.is_file():
        out += errors(Overrides, yaml.safe_load(ovf.read_text(encoding="utf-8")) or {}, f"{p.parent.name}/overrides.yaml")
    c = khgconf.load(s, code)
    for sec, model in SECTION_MODELS.items():
        out += errors(model, c["settings"][sec], f"{p.parent.name} merged {sec}")
    pd_ = c.get("peat_depth") or {}
    if pd_.get("path") and not Path(pd_["path"]).is_file():
        out.append(f"{p.parent.name}: peat_depth.path not found: {pd_['path']}")
    for dem, e in (c.get("dems") or {}).items():
        if not (e or {}).get("skip") and (e or {}).get("clip") and not Path(e["clip"]).is_file() and dem != "lidar":
            out.append(f"{p.parent.name}: dems.{dem}.clip not found: {e['clip']} (run dem_inputs)")
    sets = (c["settings"]["pump"].get("set") or {})
    if sets and pump_sch is not None:
        out += [f"{p.parent.name}: pump.set.{k}: not a key of repeat-pump's run config" for k in sets if not pump_key_ok(pump_sch, k)]
    return out


def validate_template(s) -> list[str]:
    from .config import HUB
    import yaml
    raw = yaml.safe_load((HUB / "pipeline.yaml").read_text(encoding="utf-8"))
    out = errors(Pipeline, {**raw, **{k: s[k] for k in ("workspace", "data", "khg_root")}}, "pipeline.yaml")
    if (HUB / "pipeline.local.yaml").is_file():
        out += errors(Pipeline, dict(s), "pipeline.yaml + pipeline.local.yaml")
    for k, v in (s.get("national") or {}).items():
        if isinstance(v, dict) and v.get("path") and not (s.data / v["path"]).exists():
            out.append(f"national.{k}: not in the data folder: {v['path']}")
    return out


# ---------------------------------------------------------------- show: merged values with their layer

def _flat(d, prefix="") -> dict:
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict) and v and k != "set":
            out.update(_flat(v, key + "."))
        else:
            out[key] = v
    return out


def show(s, code: str) -> list[tuple[str, Any, str]]:
    """(key, value, layer) of every setting the steps of this KHG read."""
    import yaml
    from .config import HUB
    from . import khgconf
    p = khgconf.path_of(code)
    layers = [("pipeline.yaml", yaml.safe_load((HUB / "pipeline.yaml").read_text(encoding="utf-8")) or {})]
    if (HUB / "pipeline.local.yaml").is_file():
        layers.append(("pipeline.local.yaml", yaml.safe_load((HUB / "pipeline.local.yaml").read_text(encoding="utf-8")) or {}))
    kh = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    ov = yaml.safe_load(p.with_name("overrides.yaml").read_text(encoding="utf-8")) or {} if p.with_name("overrides.yaml").is_file() else {}
    origin = {}
    for name, raw in layers:
        for sec in (*STEP_SECTIONS, "dems"):
            for k in _flat({sec: raw.get(sec)}):
                origin[k] = name
    for k in _flat({x: kh.get(x) for x in ("khg", "dems", "peat_depth", "canals")}):
        origin[k] = "khg.yaml"
    for k in _flat({"steps": kh.get("overrides")}):
        origin[k.removeprefix("steps.")] = "khg.yaml (legacy overrides)"
    for k in _flat({x: v for x, v in ov.items() if x != "steps"}):
        origin[k] = "overrides.yaml"
    for k in _flat(ov.get("steps") or {}):
        origin[k] = "overrides.yaml (steps)"
    c = khgconf.load(s, code)
    merged = {**{x: c.get(x) for x in ("khg", "peat_depth", "canals", "dems")}, **c["settings"],
              "run": {"dems": s["dems"].get("default") or s["dems"]["variants"]}}
    origin["run.dems"] = origin.get("dems.default", "pipeline.yaml")
    rows = []
    for k, v in _flat(merged).items():
        rows.append((k, v, origin.get(k) or next((o for ok, o in origin.items() if k.startswith(ok + ".")), "default")))
    return rows


# ---------------------------------------------------------------- the JSON Schema and the catalogue

def json_schema() -> dict:
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "RE-PEAT chain settings",
            "pipeline": Pipeline.model_json_schema(), "khg": KhgFile.model_json_schema(),
            "overrides": Overrides.model_json_schema()}


def _allowed(prop: dict, defs: dict) -> str:
    def enum_of(n):
        if "$ref" in n:
            n = defs.get(n["$ref"].split("/")[-1], {})
        if "enum" in n:
            return n["enum"]
        if "const" in n:
            return [n["const"]]
        for k in ("items", "anyOf"):
            if k in n:
                vals = []
                for x in (n[k] if isinstance(n[k], list) else [n[k]]):
                    vals += enum_of(x) or []
                if vals:
                    return vals
        return None
    def bounds_of(n):
        b = [f"{s} {n[k]}" for k, s in (("minimum", "≥"), ("exclusiveMinimum", ">"), ("maximum", "≤")) if k in n]
        for x in n.get("anyOf", []):
            b += bounds_of(x)
        return b
    e = enum_of(prop)
    parts = ([", ".join(map(str, e))] if e else []) + bounds_of(prop)
    return "; or ".join(parts) if e and len(parts) > 1 else "; ".join(parts)


def catalogue() -> str:
    """docs/21-configuration.md: every setting of the three layers, generated from this module, with the values pipeline.yaml
    holds now (tracked file only, before pipeline.local.yaml)."""
    import yaml
    from .config import HUB
    current = _flat(yaml.safe_load((HUB / "pipeline.yaml").read_text(encoding="utf-8")) or {})
    L = ["# Configuration of the chain", "",
         "Generated by `python tools/khg_pipeline.py config catalogue` from `tools/pipeline/schema.py`; do not edit by hand.", "",
         "Three layers, later wins: `pipeline.yaml` (+ `pipeline.local.yaml`, not tracked) for all KHG; `sites/<folder>/khg.yaml`, "
         "generated by `init` and never edited; `sites/<folder>/overrides.yaml`, hand-written exceptions with a reason and a date. "
         "In `overrides.yaml`, `steps:` takes any key of the step sections below for that KHG only, e.g. "
         "`steps: {delineation: {min_area_km2: 50}, pump: {set: {interventions.held_target: 0.6}}}`. "
         "`pump.set` takes any key of repeat-pump's run config (`repeat_pump.core.config.Config`).", "",
         "Check a KHG before running: `config validate --khg <code>`; see what applies and from which file: `config show --khg <code>`.", ""]
    for title, model, prefix in (("National template: pipeline.yaml", Pipeline, ""),
                                 ("One KHG: khg.yaml (generated) and overrides.yaml (hand-written)", KhgFile, "")):
        sch = model.model_json_schema()
        defs = sch.get("$defs", {})
        col = "Value in pipeline.yaml" if model is Pipeline else "Default"
        L += [f"## {title}", "", f"| Key | Setting | Label (ID) | Unit | Allowed | {col} | Meaning |", "|---|---|---|---|---|---|---|"]
        for key, en, idl, unit, allowed, default, desc in _flat_rows(model, prefix, sch, defs):
            if model is Pipeline:
                v = current.get(key, {k[len(key) + 1:]: x for k, x in current.items() if k.startswith(key + ".")} or None)
                if key in ("workspace", "data", "khg_root", "repos", "python", "environment"):
                    v = "machine-specific (pipeline.local.yaml)" if key in ("python", "environment") else v
            else:
                v = default
            val = ("required" if v is _REQ else v if isinstance(v, str) and v.startswith("machine")
                   else json.dumps(v, default=str, ensure_ascii=False))
            val = val.replace("|", "\\|")
            L.append(f"| `{key}` | {en} | {idl} | {unit} | {allowed} | {val[:120]} | {desc} |")
        L.append("")
    return "\n".join(L) + "\n"


_REQ = object()     # marks a required field in the catalogue rows


def _flat_rows(model, prefix, sch, defs):
    """Fields of a model, descending into nested models (their own titled fields)."""
    out = []
    for name, f in model.model_fields.items():
        key = f"{prefix}{name}"
        ann = f.annotation
        args = getattr(ann, "__args__", None) or (ann,)
        nested = next((a for a in args if isinstance(a, type) and issubclass(a, BaseModel)), None)
        if getattr(ann, "__origin__", None) is dict and nested is not None:     # dict[Dem, Model]: fields under key.<dem>
            key = key + ".<dem>"
        if nested is NationalFile:                 # one row per national file: path, layer, where, field, values together
            ex = f.json_schema_extra or {}
            out.append((key, f.title or name, ex.get("label_id", ""), "", "path, layer, where, field, values", _REQ, f.description or ""))
            continue
        if nested is not None:
            nsch = defs.get(nested.__name__, nested.model_json_schema())
            out += _flat_rows(nested, key + ".", nsch, defs)
            continue
        ex = f.json_schema_extra or {}
        prop = (sch.get("properties") or {}).get(name, {})
        default = _REQ if f.is_required() else f.get_default(call_default_factory=True)
        out.append((key, f.title or name, ex.get("label_id", ""), ex.get("unit", ""), _allowed(prop, defs), default, f.description or ""))
    return out
