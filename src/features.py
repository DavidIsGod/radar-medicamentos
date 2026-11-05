"""Construye el panel molécula × fecha de corte con variables de mercado (CUM) e historial de desabastecimiento.

Para cada fecha de corte D solo se usa información conocida hasta D; la etiqueta es si la molécula
aparece en la lista de vitales no disponibles en los 12 meses siguientes (D, D + 12m].
"""
from pathlib import Path

import numpy as np
import pandas as pd

from normalize import normalize, split_combo

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"


def _date(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", format="mixed")


def load_cum() -> pd.DataFrame:
    """Una fila por (presentación, molécula) con su ventana de actividad en el mercado."""
    cols = ["expedientecum", "consecutivocum", "principioactivo", "titular", "modalidad", "estadocum", "fechaactivo",
            "fechainactivo", "fechavencimiento", "atc", "viaadministracion", "formafarmaceutica", "muestramedica"]
    frames = []
    for name in ("cum_vigentes", "cum_vencidos"):
        df = pd.read_csv(RAW / f"{name}.csv", usecols=cols, low_memory=False, dtype=str)
        df["origen"] = name
        frames.append(df)
    cum = pd.concat(frames, ignore_index=True)
    cum = cum[cum["muestramedica"].fillna("No").str.upper() != "SI"]  # las muestras médicas no abastecen el mercado
    cum["molecula"] = cum["principioactivo"].map(normalize)
    cum = cum[cum["molecula"] != ""]
    cum["presentacion"] = cum["expedientecum"].astype(str) + "-" + cum["consecutivocum"].astype(str)
    cum = cum.drop_duplicates(["presentacion", "molecula"])

    cum["inicio"] = _date(cum["fechaactivo"])
    fin = _date(cum["fechainactivo"]).where(lambda d: d.dt.year > 1990)
    venc = _date(cum["fechavencimiento"]).where(lambda d: (d.dt.year > 1990) & (d.dt.year < 2100))
    fin = fin.fillna(venc.where(cum["origen"] == "cum_vencidos"))
    # Inactivas sin fecha de inactivación: no hay forma de ubicarlas en el tiempo; se excluyen del conteo activo.
    sin_fecha = (cum["estadocum"] == "Inactivo") & fin.isna()
    cum["fin"] = fin
    cum = cum[~sin_fecha & cum["inicio"].notna()]
    cum["importada"] = cum["modalidad"].fillna("").str.startswith("IMPORTAR")
    cum["atc_grupo"] = cum["atc"].fillna("?").str[0]
    cum["via"] = cum["viaadministracion"].fillna("").str.upper().map(
        lambda v: "ORAL" if "ORAL" in v else "PARENTERAL" if any(k in v for k in ("INTRAVENOSA", "INTRAMUSCULAR", "SUBCUTANEA", "PARENTERAL")) else "OTRA"
    )
    return cum[["presentacion", "molecula", "titular", "importada", "inicio", "fin", "atc", "atc_grupo", "via", "formafarmaceutica"]]


def load_vitales() -> pd.DataFrame:
    v = pd.read_csv(RAW / "vitales_no_disponibles.csv", low_memory=False, dtype=str)
    v["fecha"] = _date(v["fecha_de_autorizaci_n"]).dt.tz_localize(None)
    v["molecula"] = v["principio_activo1"].map(split_combo)
    v = v.explode("molecula").dropna(subset=["molecula", "fecha"])
    return v[["fecha", "molecula", "tipo_de_solicitud", "diagnostico_cie_1no_reporta"]]


def snapshot(cum: pd.DataFrame, vit: pd.DataFrame, cutoff: pd.Timestamp, horizon_months: int = 12) -> pd.DataFrame:
    d = cutoff
    y1, y2 = d - pd.DateOffset(months=12), d - pd.DateOffset(months=24)
    on_market = cum[cum["inicio"] <= d]
    active = on_market[on_market["fin"].isna() | (on_market["fin"] > d)]
    lost12 = on_market[(on_market["fin"] > y1) & (on_market["fin"] <= d)]
    lost24 = on_market[(on_market["fin"] > y2) & (on_market["fin"] <= d)]
    new12 = on_market[on_market["inicio"] > y1]

    g = on_market.groupby("molecula")
    feats = pd.DataFrame({
        "anios_en_mercado": (d - g["inicio"].min()).dt.days / 365.25,
        "atc": g["atc"].agg(lambda s: s.mode().iat[0] if not s.mode().empty else "?"),
        "atc_grupo": g["atc_grupo"].agg(lambda s: s.mode().iat[0]),
        "via": g["via"].agg(lambda s: s.mode().iat[0]),
    })
    ga = active.groupby("molecula")
    feats["presentaciones_activas"] = ga["presentacion"].nunique()
    feats["titulares_activos"] = ga["titular"].nunique()
    feats["formas_activas"] = ga["formafarmaceutica"].nunique()
    feats["share_importadas"] = ga["importada"].mean()

    def hhi(s: pd.Series) -> float:
        p = s.value_counts(normalize=True)
        return float((p ** 2).sum())

    feats["hhi_titulares"] = ga["titular"].agg(hhi)
    feats["perdidas_12m"] = lost12.groupby("molecula")["presentacion"].nunique()
    feats["perdidas_24m"] = lost24.groupby("molecula")["presentacion"].nunique()
    feats["nuevas_12m"] = new12.groupby("molecula")["presentacion"].nunique()
    feats = feats.fillna({c: 0 for c in ["presentaciones_activas", "titulares_activos", "formas_activas", "perdidas_12m",
                                          "perdidas_24m", "nuevas_12m"]})
    feats["share_importadas"] = feats["share_importadas"].fillna(0.0)
    feats["hhi_titulares"] = feats["hhi_titulares"].fillna(1.0)
    feats["ratio_perdidas_12m"] = feats["perdidas_12m"] / (feats["presentaciones_activas"] + feats["perdidas_12m"]).replace(0, np.nan)
    feats["ratio_perdidas_12m"] = feats["ratio_perdidas_12m"].fillna(0.0)
    feats["sin_presentaciones_activas"] = (feats["presentaciones_activas"] == 0).astype(int)
    feats["un_solo_titular"] = (feats["titulares_activos"] == 1).astype(int)

    past = vit[vit["fecha"] <= d]
    feats["vitales_12m"] = past[past["fecha"] > y1].groupby("molecula").size()
    feats["vitales_24m"] = past[past["fecha"] > y2].groupby("molecula").size()
    feats["vitales_historico"] = past.groupby("molecula").size()
    last = past.groupby("molecula")["fecha"].max()
    feats[["vitales_12m", "vitales_24m", "vitales_historico"]] = feats[["vitales_12m", "vitales_24m", "vitales_historico"]].fillna(0)
    feats["meses_desde_ultimo_vital"] = ((d - last).dt.days / 30.44).reindex(feats.index).fillna(999).clip(upper=999)

    # Contagio terapéutico: desabastecimientos recientes de OTRAS moléculas en el mismo grupo ATC
    atc_of = feats["atc"].astype(str)
    rec = past[past["fecha"] > y1].copy()
    rec["atc"] = rec["molecula"].map(atc_of)
    for nivel, n in (("atc4", 5), ("atc3", 4)):
        key = atc_of.str[:n]
        per_group = rec.dropna(subset=["atc"]).assign(g=lambda r: r["atc"].str[:n]).groupby("g").size()
        own = feats["vitales_12m"]
        feats[f"vitales_12m_mismo_{nivel}"] = (key.map(per_group).fillna(0) - own).clip(lower=0)

    fut = vit[(vit["fecha"] > d) & (vit["fecha"] <= d + pd.DateOffset(months=horizon_months))]
    feats["y"] = feats.index.isin(fut["molecula"].unique()).astype(int)
    feats["autorizaciones_futuras"] = fut.groupby("molecula").size().reindex(feats.index).fillna(0)
    feats["corte"] = d
    return feats.reset_index(names="molecula")


def build_panel(cutoffs: list[str]) -> pd.DataFrame:
    cum, vit = load_cum(), load_vitales()
    panel = pd.concat([snapshot(cum, vit, pd.Timestamp(c)) for c in cutoffs], ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(OUT / "panel.parquet", index=False)
    return panel


if __name__ == "__main__":
    cuts = [f"{y}-12-31" for y in range(2018, 2025)] + ["2026-09-30"]
    p = build_panel(cuts)
    print(p.groupby("corte").agg(moleculas=("molecula", "size"), positivos=("y", "sum"), tasa=("y", "mean")))
