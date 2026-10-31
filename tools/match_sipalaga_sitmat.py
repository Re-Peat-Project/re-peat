"""Which SiTMAT stations continue a SIPALAGA (BRG, 2018-2019) station?

    python tools/match_sipalaga_sitmat.py [DATA_DIR]      # DATA_DIR defaults to $REPEAT_DATA, then ../_data

Compares every SIPALAGA station in <DATA_DIR>/sipalaga/sipalaga_stations.gpkg (repeat_common.fetch_sipalaga) with every
SiTMAT station, community and concession ($SITMAT_PROCESSED/stations.csv), on three kinds of evidence:

  code   the SiTMAT name is the SIPALAGA code (BRG_<area>_<nn>, or an older name such as LUMPUR1)
  name   the village in the SiTMAT name ("TMA - Desa Muara Medak II", "AWS-Desa Atap", "Ds Rawa Makmur") equals the village in
         the crawler location (MUARA_MEDAK_2), ignoring case, punctuation, the station number and Roman numerals, in the
         same province
  place  the SiTMAT point lies in the KLH 2023 village polygon the crawler names, within APERS_KM of the Apers et al. 2022
         coordinate (0.001 degree) or within PLACE_KM of the Taufik et al. 2023 coordinate (0.01 degree)

The village name is the crawler location or, failing that, the Apers site name. A pair with a code, with name and place, or
within APERS_KM of an Apers point is a likely continuation; a single kind of evidence is a candidate only. SiTMAT points at 0,0 are
left out. Writes reports/investigations/sipalaga_sitmat_match.md and sipalaga_sitmat_candidates.csv next to it.
"""
import os
import re
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

from repeat_common.fetch_sipalaga import key, village_names

HUB = Path(__file__).resolve().parents[1]
OUT = HUB / "reports" / "investigations" / "sipalaga_sitmat_match.md"
PLACE_KM = 1.5
APERS_KM = 0.3
EA = 6933
ROMAN = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5"}


def village_key(name: str) -> str:
    """Village part of a station name, without prefixes, station numbers and Roman numerals."""
    s = re.sub(r"^(aws|tma|ds|desa|device)\b[\s_-]*", "", str(name).strip().lower())
    s = re.sub(r"^(desa|ds)\b[\s_-]*", "", s)
    s = re.sub(r"^[a-z0-9]+-(?=[a-z])", "", s) if re.match(r"^[a-z]{1,3}\d?[a-z]?-", s) else s   # crawler site prefix PS1-
    s = re.sub(r"[\s_]*\(sm\)$", "", s)
    s = re.sub(r"[\s_-]+(\d+|i{1,3}|iv|v)$", "", s)                       # station number or Roman numeral
    return re.sub(r"[^a-z0-9]", "", s)


def md(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    rows += ["| " + " | ".join("" if pd.isna(v) else (f"{v:,.1f}" if isinstance(v, float) else str(v)) for v in r) + " |"
             for r in df.itertuples(index=False)]
    return "\n".join(rows)


def main():
    data = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("REPEAT_DATA", HUB.parent / "_data"))
    sp = gpd.read_file(data / "sipalaga" / "sipalaga_stations.gpkg")
    n_sitmat_only = int((sp[["in_crawler_csv", "in_crawler_urls", "in_taufik2023", "in_apers2022"]].sum(axis=1) == 0).sum())
    sp = sp[sp[["in_crawler_csv", "in_crawler_urls", "in_taufik2023", "in_apers2022"]].sum(axis=1) > 0]   # documented in 2018-2020
    sit_dir = Path(os.environ.get("SITMAT_PROCESSED", HUB.parent / "repeat-sitmat/sitmat_out/processed"))
    st = pd.read_csv(sit_dir / "stations.csv")
    geo = pd.read_csv(sit_dir / "stations_geo.csv")[["kind", "station_id", "adm1"]] if (sit_dir / "stations_geo.csv").exists() else None
    if geo is not None:
        st = st.merge(geo, on=["kind", "station_id"], how="left")
    no_xy = st[((st.lon == 0) & (st.lat == 0)) | st.lon.isna()]
    st = st[~((st.lon == 0) & (st.lat == 0)) & st.lon.notna()]
    sg = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.lon, st.lat), crs=4326)
    sg["province"] = sg.provinsi.fillna(sg.get("adm1")).fillna("").str.upper()

    # village polygons the crawler names
    vil = gpd.read_file(data / "batas_desa_indonesia_2023_KLH.gpkg", columns=["PROV_2023", "KABKO_2023", "KEC_2023", "DESA_2023"])
    vil["k"] = vil.DESA_2023.map(key) + "|" + vil.KABKO_2023.map(key)
    vil["kc"] = vil.KEC_2023.map(key)
    poly = {}
    for _, r in sp[sp.location.notna()].iterrows():
        m = vil[vil.k.isin([key(n) + "|" + key(r.district) for n in village_names(r.location)])]
        if len(m) > 1 and (m.kc == key(r.subdistrict)).any():
            m = m[m.kc == key(r.subdistrict)]
        if len(m) == 1:
            poly[r.code] = m.geometry.iloc[0]

    pairs = {}

    def add(code, sid, kind, ev):
        pairs.setdefault((code, sid), {"code": code, "station_id": sid, "kind": kind, "evidence": set()})["evidence"].add(ev)

    # code
    names = dict(zip(sg.name.astype(str), zip(sg.station_id, sg.kind)))
    for c in sp.code:
        if c in names:
            add(c, *names[c], "code")
    # name: same village and province
    sp["vkey"] = sp.location.fillna(sp.apers_site).map(lambda s: village_key(s) if isinstance(s, str) else "")
    sg["vkey"] = sg.name.map(village_key)
    for _, r in sp[sp.vkey.str.len() > 3].iterrows():
        m = sg[(sg.vkey == r.vkey) & ((sg.province == "") | (sg.province == str(r.province).upper()))]
        for _, s in m.iterrows():
            add(r.code, s.station_id, s.kind, "name")
        part = sg[(sg.kind == "community") & (sg.vkey.str.len() >= 5) & (len(r.vkey) >= 5) & (sg.vkey != r.vkey)
                  & (sg.vkey.map(lambda v: v.startswith(r.vkey) or r.vkey.startswith(v)))
                  & ((sg.province == "") | (sg.province == str(r.province).upper()))]
        for _, s in part.iterrows():
            add(r.code, s.station_id, s.kind, "name (partial)")
    # place: inside the named village, or near the article's coordinate
    for c, g in poly.items():
        for _, s in sg[sg.within(g)].iterrows():
            add(c, s.station_id, s.kind, "place (village)")
    tf = sp[sp.in_taufik2023 == 1]
    a = gpd.GeoDataFrame(tf[["code"]], geometry=gpd.points_from_xy(tf.taufik_lon, tf.taufik_lat), crs=4326).to_crs(EA)
    b = sg.to_crs(EA)
    j = gpd.sjoin(a, b[["station_id", "kind", "geometry"]], predicate="dwithin", distance=PLACE_KM * 1e3)
    for _, r in j.iterrows():
        add(r.code, r.station_id, r.kind, f"place (< {PLACE_KM} km of article point)")

    ap = sp[sp.in_apers2022 == 1]
    a = gpd.GeoDataFrame(ap[["code"]], geometry=gpd.points_from_xy(ap.apers_lon, ap.apers_lat), crs=4326).to_crs(EA)
    j = gpd.sjoin(a, b[["station_id", "kind", "geometry"]], predicate="dwithin", distance=APERS_KM * 1e3)
    for _, r in j.iterrows():
        add(r.code, r.station_id, r.kind, f"place (< {APERS_KM} km of Apers point)")
    near = gpd.sjoin_nearest(a, b[["station_id", "kind", "name", "geometry"]], distance_col="m")

    cand = pd.DataFrame(pairs.values())
    if cand.empty:
        cand = pd.DataFrame(columns=["code", "station_id", "kind", "evidence"])
    cand["n_kinds"] = cand.evidence.map(lambda e: len({x.split(" ")[0] for x in e}))
    cand["evidence"] = cand.evidence.map(lambda e: "; ".join(sorted(e)))
    cand = cand.merge(sg[["station_id", "kind", "name", "company_code", "lon", "lat"]].rename(
        columns={"name": "sitmat_name", "lon": "sitmat_lon", "lat": "sitmat_lat"}), on=["station_id", "kind"], how="left")
    cand = cand.merge(sp[["code", "location", "apers_site", "district", "province", "khg", "coord_source"]], on="code", how="left")
    cand["location"] = cand.location.fillna(cand.apers_site)
    # distance from the SIPALAGA position (article or village point) to the SiTMAT point
    pa = gpd.GeoSeries(gpd.points_from_xy(sp.set_index("code").loc[cand.code, "lon"], sp.set_index("code").loc[cand.code, "lat"]), crs=4326).to_crs(EA)
    pb = gpd.GeoSeries(gpd.points_from_xy(cand.sitmat_lon, cand.sitmat_lat), crs=4326).to_crs(EA)
    cand["km"] = (pa.distance(pb, align=False) / 1e3).round(1).values
    cand["grade"] = cand.apply(lambda r: "likely" if ("code" in r.evidence or r.n_kinds >= 2 or "Apers" in r.evidence)
                               else "candidate", axis=1)
    cand = cand.sort_values(["grade", "code", "kind", "station_id"], ascending=[False, True, True, True])
    cand.to_csv(OUT.with_name("sipalaga_sitmat_candidates.csv"), index=False)

    # --- report ---------------------------------------------------------------------------------------------------------
    lk = cand[cand.grade == "likely"]
    L = ["# SIPALAGA and SiTMAT stations: match", "",
         f"`python tools/match_sipalaga_sitmat.py`. {len(sp)} SIPALAGA codes documented in 2018-2020 (crawler, its URL lists, "
         f"Taufik et al. 2023, Apers et al. 2022; the {n_sitmat_only} BRG_ codes known only from SiTMAT are the SiTMAT side, not "
         "compared with themselves) " f"({int(sp.lon.notna().sum())} placed; "
         f"{len(poly)} with the polygon of the village the crawler names) against {len(sg):,} SiTMAT stations with coordinates "
         f"({int((sg.kind == 'community').sum())} community, {int((sg.kind == 'concession').sum()):,} concession). Evidence: "
         f"code, village name in the station name (same province), and place (inside the named village, within {APERS_KM} km of the "
         f"Apers et al. 2022 coordinate or within {PLACE_KM} km of the Taufik et al. 2023 coordinate). The 2019 and 2026 records do not overlap in time, so no pair can be confirmed by "
         "comparing readings. Candidate list: `sipalaga_sitmat_candidates.csv`.", "",
         f"{len(cand)} pairs: {len(lk)} likely (same code, name and place, or within {APERS_KM} km of an Apers point), "
         f"{len(cand) - len(lk)} candidates on one kind of evidence. "
         f"Likely pairs cover {lk.code.nunique()} SIPALAGA stations and {lk.station_id.nunique()} SiTMAT stations "
         f"({int((lk.kind == 'community').sum())} community, {int((lk.kind == 'concession').sum())} concession).", ""]
    t = cand.groupby(["evidence", "kind"]).size().reset_index(name="pairs")
    L += ["Table: pairs by evidence and SiTMAT station kind.", "", md(t), ""]
    bins = pd.cut(near.m / 1e3, [0, 0.1, 0.3, 1, 3, 10, 1e4], right=False,
                  labels=["< 0.1", "0.1-0.3", "0.3-1", "1-3", "3-10", ">= 10"])
    t = near.assign(km=bins).groupby(["km", "kind"], observed=False).size().unstack(fill_value=0).reset_index()
    L += [f"Distance from each of the {len(a)} stations placed by Apers et al. 2022 (0.001 degree, about 100 m) to the nearest "
          "SiTMAT station of any kind. A logger kept in place, or re-registered, would sit within about 0.1-0.3 km.", "",
          "Table: nearest SiTMAT station, by distance (km) and kind of that station.", "", md(t.rename(columns={"km": "km"})), ""]
    close = near[near.m < 3000].sort_values("m").merge(sp[["code", "apers_site"]], on="code")
    close = close.assign(km=(close.m / 1e3).round(2))[["code", "apers_site", "name", "kind", "km"]].rename(columns={"name": "sitmat_name"})
    L += ["Table: Apers-placed SIPALAGA stations with a SiTMAT station within 3 km.", "", md(close), ""]
    show = ["code", "location", "district", "sitmat_name", "kind", "company_code", "evidence", "km", "khg"]
    L += ["Table: likely pairs (km: from the SIPALAGA position, an article point or a village point, to the SiTMAT point).", "",
          md(lk[show]), ""]
    c1 = cand[(cand.grade == "candidate") & cand.evidence.str.startswith("name")]
    L += ["Table: name-only candidates (village name matches, the SiTMAT point lies outside the named village).", "", md(c1[show]), ""]
    c2 = cand[(cand.grade == "candidate") & ~cand.evidence.str.startswith("name")]
    t = c2.groupby(["code", "kind"]).agg(stations=("station_id", "size"), nearest_km=("km", "min"),
                                          companies=("company_code", lambda s: ", ".join(sorted(set(s.dropna()))))).reset_index()
    L += ["Table: place-only candidates, per SIPALAGA station and kind. A concession point in the same village is not evidence "
          "that the logger was reused: concession networks are dense.", "", md(t), ""]
    L += [f"Left out: {len(no_xy)} SiTMAT stations at 0,0 or without coordinates ({int((no_xy.kind == 'community').sum())} community), "
          "named " + ", ".join(sorted(set(no_xy.name.astype(str).str.replace(r"^DL MTI-.*", "DL MTI-...", regex=True)
                                          .str.replace(r"\d+", "n", regex=True)))) + ".", ""]
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
