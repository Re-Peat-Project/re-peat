"""Verify the fields of KLH's integrated PPEG analysis against the independent copies of their source layers that we hold.

    python re-peat/tools/verify_ppeg_layers.py [--n 20000] [--seed 20261116]

Each polygon of the integrated analysis (989,398, the overlay of KHG, village, licence, forest area, FEG, peat, burned area,
canal zone ...) should carry, in every field, the value of the source layer at any point inside it. So: draw polygons at
random in proportion to their area (LUAS_HA), take a point inside each (representative point), and read every source layer at
that point. Agreement = the share of points (= of area) where the field matches the source. The pairs that disagree are listed,
because a systematic pair (one label for another) is a naming difference, not an error.

Sources (all in $REPEAT_DATA, listed in sites/data_catalog.csv):
  NAMA_KHG                         batas_khg_indonesia.gpkg (NAMA_KHG; outside = NON KHG)
  PULAU, PROV_2023 ... DESA_2023   batas_desa_indonesia_2023_KLH.gpkg (same field names)
  IZIN_USAHA, PERUSAHAAN           landstatus/ALL_Updade__IZIN_USAHA__..._2025.gpkg (overlapping licences: any match counts)
  Fungsi_KWS                       landstatus/KWSHUTAN_AR_250K_2023_Transcripted.gpkg (Fungsi_KWS)
  FEG_250K                         landstatus/FEG__Indonesia__2017__Rev_Tipologi.gpkg (FEG_KGHLTR)
  PEAT_THICK, TNH_GAMBUT, FEG_PEAT_1  klhk_khg_feg_50k.gpkg layer feg_50k (peat_thick, tnh_gambut, feg_peat)
  BA_2015 ... BA_2024              burnt_area_2015_2026_Indonesia.gpkg (BA_yyyy; compared as burned that year or not)
  LAHAN_GAMB                       peat/lahan_gambut_indonesia_2025.gpkg (SiTMAT peat map 2025)
  KET_KANAL                        kanal_osgm_khg_existing_Indonesia.gpkg: distance from the point to the nearest canal of each
                                   class, per KET_KANAL value (the zone widths are not documented; the distances show them)
  BUFFER, CD_KONSESI               distance to the nearest licence polygon
Not verifiable with what we hold (no independent copy): PL_2022 (KLH land cover 2022), SKEG_2024 / CD_SKEG_24 (peat damage
status), KDLMN_GBT, KMTNGN_GBT, LANDFORM, GMBT_BBSDL (BBSDLP 1:50k national map; we hold only the public Kalimantan part, used
where it covers), SK_FEG_50K, PROG_DMPG_2025, PROG_INTERVENSI (KLH's own derived classes; checked for internal consistency).

Writes re-peat/reports/investigations/ppeg_verification.csv (agreement per field, tracked), ppeg_verification.md and
ppeg_verification_disagreements.csv (the full report and the disagreeing value pairs; they name licence holders, so they are
git-ignored and kept locally for reports), and
$REPEAT_DATA/derived/ppeg_verification/sample_points.gpkg (every sampled point with the PPEG value and the source value of each
field, for review in QGIS; not tracked: it holds licence holders and village names).
"""
import argparse
import os
import re
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

HUB = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("REPEAT_DATA", HUB.parent / "_data"))
PPEG = DATA / "ALL_Analysis_Integrasi_Tematik__PPEG_Indonesia__April_2026.gpkg"
OUT = HUB / "reports" / "investigations"
METRIC = "EPSG:3395"         # world Mercator: below 9 degrees latitude its scale error is under 1.3%, enough for zone widths
YEARS = range(2015, 2025)
PARTIAL = {"klhk_khg_feg_50k.gpkg"}   # KLHK FEG 1:50k: only the KHG we fetched, not national


def norm(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    s = str(v).strip().casefold().replace(",", ".")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*:\s*", ": ", s)
    s = re.sub(r"^indikatif ", "", s)      # FEG 2017 labels its classes "Indikatif Fungsi ...", PPEG drops the word
    return s


def at_points(pts, path, fields, layer=None):
    """Values of ``fields`` of the polygons of ``path`` under each point; several polygons: values joined with ' | '."""
    src = gpd.read_file(path, layer=layer, columns=fields, engine="pyogrio")
    src = src[src.geometry.notna()].to_crs(pts.crs)
    j = gpd.sjoin(pts[["pid", "geometry"]], src, how="left", predicate="within")
    out = {}
    for f in fields:
        g = j.groupby("pid")[f].agg(lambda s: " | ".join(sorted({str(x) for x in s.dropna()})))
        out[f] = pts["pid"].map(g).fillna("")
    return out


def _range(v):
    m = re.findall(r"(\d+[.,]?\d*)", str(v))
    return tuple(float(x.replace(",", ".")) for x in m[:2]) if len(m) >= 2 else None


# Our FEG 1:50k copy uses its own labels and 1 m thickness classes where PPEG uses 0.5 m classes: compare the meaning.
SEMANTIC = {
    "TNH_GAMBUT": lambda p, s: norm(p).startswith("tanah gambut") == norm(s).startswith("tanah gambut"),
    "FEG_PEAT_1": lambda p, s: ("lindung" in norm(p)) == ("lindung" in norm(s)),
    "PEAT_THICK": lambda p, s: (_range(p) is not None and _range(s) is not None
                                and _range(s)[0] <= _range(p)[0] and _range(p)[1] <= _range(s)[1]),
}


def compare_semantic(field, ppeg_vals, src_vals):
    f = SEMANTIC[field]
    return np.array([bool(s) and any(f(p, x) for x in s.split(" | ")) for p, s in zip(ppeg_vals, src_vals)])


def compare(ppeg_vals, src_vals, outside=("",)):
    """Agree when the normalised PPEG value is one of the source values at the point, or both say 'outside'."""
    ok = []
    for p, s in zip(ppeg_vals, src_vals):
        pn = norm(p)
        sv = [norm(x) for x in s.split(" | ")] if s else []
        if not sv:
            ok.append(pn in outside or pn.startswith("non "))
        else:
            ok.append(pn in sv)
    return np.array(ok)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20261116)
    a = ap.parse_args()
    t0 = time.time()
    lay = pyogrio.list_layers(PPEG)[0][0]
    attrs = pyogrio.read_dataframe(PPEG, read_geometry=False, columns=["LUAS_HA"], fid_as_index=True, use_arrow=True)
    rng = np.random.default_rng(a.seed)
    w = attrs["LUAS_HA"].clip(lower=0).to_numpy()
    fids = np.sort(rng.choice(attrs.index.to_numpy(), size=a.n, replace=False, p=w / w.sum()))
    poly = pyogrio.read_dataframe(PPEG, layer=lay, fids=fids, fid_as_index=True)
    print(f"sample: {len(poly):,} polygons drawn by area from {len(attrs):,} ({time.time() - t0:.0f} s)", flush=True)
    pts = gpd.GeoDataFrame(poly.drop(columns="geometry").reset_index(names="fid"), geometry=poly.geometry.representative_point().values, crs=poly.crs)
    pts["pid"] = np.arange(len(pts))
    rows, pairs = [], []

    def record(field, src_name, ppeg_col, src_col, ok, note="", covered=None):
        if covered is not None:
            note = f"source covers {100 * covered.mean():.1f}% of the points; agreement on those only"
            if field in SEMANTIC:
                note += "; compared by meaning (peat or mineral; protected or cultivation; PPEG thickness class inside the source class)"
            ppeg_col, src_col, ok = ppeg_col[covered], src_col[covered], ok[covered]
        rows.append({"field": field, "source": src_name, "points": len(ok), "agree_share": round(float(ok.mean()), 4),
                     "ha_sampled": round(float(pts.loc[:, "LUAS_HA"].sum())), "note": note})
        bad = pd.DataFrame({"ppeg": ppeg_col[~ok].astype(str).values, "source": src_col[~ok].astype(str).values})
        for (p, s), n in bad.value_counts().head(8).items():
            pairs.append({"field": field, "ppeg_value": p, "source_value": s or "(no polygon)", "points": int(n)})
        print(f"  {field:<12} {100 * ok.mean():5.1f}% agree ({src_name})", flush=True)

    checks = [
        ("batas_khg_indonesia.gpkg", None, {"NAMA_KHG": "NAMA_KHG"}),
        ("batas_desa_indonesia_2023_KLH.gpkg", None, {f: f for f in ("PULAU", "PROV_2023", "KABKO_2023", "KEC_2023", "DESA_2023")}),
        ("landstatus/ALL_Updade__IZIN_USAHA__PBPH_Perkebunan_HTRKM_Tambang__2025.gpkg", None, {"IZIN_USAHA": "IZIN_USAHA", "PERUSAHAAN": "PERUSAHAAN"}),
        ("landstatus/KWSHUTAN_AR_250K_2023_Transcripted.gpkg", None, {"Fungsi_KWS": "Fungsi_KWS"}),
        ("landstatus/FEG__Indonesia__2017__Rev_Tipologi.gpkg", None, {"FEG_250K": "FEG_KGHLTR"}),
        ("klhk_khg_feg_50k.gpkg", "feg_50k", {"PEAT_THICK": "peat_thick", "TNH_GAMBUT": "tnh_gambut", "FEG_PEAT_1": "feg_peat"}),
        ("peat/lahan_gambut_indonesia_2025.gpkg", "lahan_gambut", {"LAHAN_GAMB": "LAHAN_GAMB"}),
    ]
    for path, layer, fmap in checks:
        t = time.time()
        vals = at_points(pts, DATA / path, list(fmap.values()), layer)
        for pf, sf in fmap.items():
            pts[f"src_{pf}"] = vals[sf].values
            ok = compare_semantic(pf, pts[pf], pts[f"src_{pf}"]) if pf in SEMANTIC else compare(pts[pf], pts[f"src_{pf}"])
            cov = (pts[f"src_{pf}"] != "").to_numpy() if path in PARTIAL else None
            record(pf, f"{path}:{sf}", pts[pf], pts[f"src_{pf}"], ok, covered=cov)
        print(f"    ({time.time() - t:.0f} s)", flush=True)
    # burned area per year: burned or not
    t = time.time()
    ba = at_points(pts, DATA / "burnt_area_2015_2026_Indonesia.gpkg", [f"BA_{y}" for y in YEARS])
    for y in YEARS:
        f = f"BA_{y}"
        src_burned = ba[f].map(lambda s: any(norm(x) not in ("", "0", "none") for x in s.split(" | "))).values
        ppeg_burned = pts[f].map(lambda v: norm(v) not in ("", "0")).values
        pts[f"src_{f}"] = np.where(src_burned, "burned", "")
        record(f, f"burnt_area_2015_2026_Indonesia.gpkg:{f}", pd.Series(np.where(ppeg_burned, "burned", "")), pd.Series(pts[f"src_{f}"]), ppeg_burned == src_burned)
    print(f"    ({time.time() - t:.0f} s)", flush=True)
    # canal zone: distance to the nearest canal of each class
    t = time.time()
    pm = pts.to_crs(METRIC)
    can = gpd.read_file(DATA / "kanal_osgm_khg_existing_Indonesia.gpkg", columns=["KET_KANAL"], engine="pyogrio").to_crs(METRIC)
    dist = {}
    for cls in sorted(can.KET_KANAL.dropna().unique()):
        nn = gpd.sjoin_nearest(pm[["pid", "geometry"]], can[can.KET_KANAL == cls][["geometry"]], how="left", distance_col="d")
        dist[cls] = nn.groupby("pid")["d"].min().reindex(pm.pid).values
        pts[f"dist_m_{norm(cls).replace(' ', '_')}"] = np.round(dist[cls])
    zrows = []
    for z, g in pts.groupby("KET_KANAL"):
        r = {"KET_KANAL": z, "points": len(g)}
        for cls in dist:
            d = pts.loc[g.index, f"dist_m_{norm(cls).replace(' ', '_')}"]
            r[f"{cls}: median / p95 / max (m)"] = f"{d.median():,.0f} / {d.quantile(.95):,.0f} / {d.max():,.0f}"
        zrows.append(r)
    zones = pd.DataFrame(zrows)
    print(f"  KET_KANAL distances ({time.time() - t:.0f} s)", flush=True)
    # 5 km concession buffer: distance to the nearest licence
    t = time.time()
    lic = gpd.read_file(DATA / checks[2][0], columns=["IZIN_USAHA"], engine="pyogrio").to_crs(METRIC)
    nn = gpd.sjoin_nearest(pm[["pid", "geometry"]], lic[["geometry"]], how="left", distance_col="d")
    pts["dist_m_licence"] = np.round(nn.groupby("pid")["d"].min().reindex(pm.pid).values)
    brows = [{"BUFFER": z, "points": len(g), "distance to nearest licence: median / p95 / max (m)":
              f"{g.dist_m_licence.median():,.0f} / {g.dist_m_licence.quantile(.95):,.0f} / {g.dist_m_licence.max():,.0f}",
              "share over 5,000 m": f"{100 * (g.dist_m_licence > 5000).mean():.1f}%", "share at 0 m": f"{100 * (g.dist_m_licence == 0).mean():.1f}%"}
             for z, g in pts.groupby("BUFFER")]
    buffers = pd.DataFrame(brows)
    print(f"  BUFFER distances ({time.time() - t:.0f} s)", flush=True)
    # internal consistency of the derived codes
    cons = []
    def rule(name, ok):
        cons.append({"rule": name, "points": int(len(ok)), "holds_share": round(float(np.mean(ok)), 4)})
    rule("CD_KONSESI = Areal Konsesi exactly where IZIN_USAHA is a licence type", (pts.CD_KONSESI.map(norm) == "areal konsesi") == (pts.IZIN_USAHA.map(norm) != "non konsesi"))
    rule("CD_KAWASAN = APL exactly where Fungsi_KWS = Areal Penggunaan Lain", (pts.CD_KAWASAN.map(norm) == "apl") == (pts.Fungsi_KWS.map(norm) == "areal penggunaan lain"))
    rule("CD_ATK = Area Terdampak Kanal exactly where KET_KANAL is a canal class", (pts.CD_ATK.map(norm) == "area terdampak kanal") == (pts.KET_KANAL.map(norm) != "non kanal"))
    burned_any = np.column_stack([pts[f"BA_{y}"].map(lambda v: norm(v) not in ("", "0")) for y in YEARS]).any(axis=1)
    rule("CD_BURN = Areal Terbakar exactly where any BA_2015..2024 is set", (pts.CD_BURN.map(norm) == "areal terbakar") == burned_any)
    nb = np.column_stack([pts[f"BA_{y}"].map(lambda v: norm(v) not in ("", "0")) for y in YEARS]).sum(axis=1)
    exp = np.select([nb == 0, nb == 1, nb == 2, nb == 3], ["non terbakar", "terbakar 1x", "terbakar 2x", "terbakar 3x"], "terbakar >3x")
    rule("BURN_PERIOD = number of BA years set", pts.BURN_PERIOD.map(norm).values == exp)
    rule("CD_SKEG_24 = Rusak exactly where SKEG_2024 is a damage class (in KHG)", ((pts.CD_SKEG_24.map(norm).str.startswith("rusak")) == (pts.SKEG_2024.map(norm).str.startswith("rusak")))[pts.CD_SKEG_24.map(norm) != "non khg"])
    rule("LAHAN_GAMB = LAHAN GAMBUT implies TNH_GAMBUT or GMBT_BBSDL says peat", ~(pts.LAHAN_GAMB.map(norm) == "lahan gambut") | pts.TNH_GAMBUT.map(norm).str.startswith("tanah gambut") | pts.GMBT_BBSDL.map(norm).str.startswith("gambut"))
    plh = (pts.KABKO_2023.map(norm) == "jayapura") & (pts.DESA_2023.map(norm) == "atabar")
    rule("Admin names Jayapura / Atabar (a placeholder, see text) occur only outside KHG (CD_KHG = NON KHG)", ~plh | (pts.CD_KHG.map(norm) == "non khg"))
    cons = pd.DataFrame(cons)
    # write
    res = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT / "ppeg_verification.csv", index=False)
    pd.DataFrame(pairs).to_csv(OUT / "ppeg_verification_disagreements.csv", index=False)
    d = DATA / "derived" / "ppeg_verification"
    d.mkdir(parents=True, exist_ok=True)
    pts.drop(columns=["pid"]).to_file(d / "sample_points.gpkg", driver="GPKG")
    md = ["# PPEG integrated analysis: verification against the source layers", "",
          f"Generated by `re-peat/tools/verify_ppeg_layers.py` (n = {a.n:,}, seed {a.seed}) on {pd.Timestamp.today().date()}. "
          f"{a.n:,} polygons of `_data/{PPEG.name}` drawn at random in proportion to their area; at a point inside each, every field "
          "is compared with the independent copy of its source layer. Agreement is therefore a share of area. Sample points with both "
          "values: `_data/derived/ppeg_verification/sample_points.gpkg` (not tracked). Field inventory: `ppeg_integrasi_tematik.md`.", "",
          "## Agreement with the source layers", "", res.drop(columns=["ha_sampled"]).to_markdown(index=False), "",
          "The most frequent disagreements per field (`ppeg_verification_disagreements.csv`):", "",
          pd.DataFrame(pairs).to_markdown(index=False), "",
          "## Canal zone (KET_KANAL): distance from the point to the nearest canal of each class", "", zones.to_markdown(index=False), "",
          "## Concession buffer (BUFFER): distance to the nearest licence polygon", "", buffers.to_markdown(index=False), "",
          "## Internal consistency of the derived codes", "", cons.to_markdown(index=False), "",
          "## Not verified (no independent copy held)", "",
          "PL_2022 (KLH land cover 2022), SKEG_2024 (peat damage status 2024), KDLMN_GBT, KMTNGN_GBT, LANDFORM, GMBT_BBSDL (BBSDLP "
          "1:50k national peat map), SK_FEG_50K, PROG_DMPG_2025 and PROG_INTERVENSI. Their values are listed in "
          "`ppeg_integrasi_tematik.md`; to verify them we need the source layers from KLH, BBSDLP and the KLHK land-cover service."]
    (OUT / "ppeg_verification.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'ppeg_verification.md'} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
