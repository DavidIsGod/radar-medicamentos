"""Exporta JSON livianos para la web (web/public/data)."""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd

from features import load_vitales

ROOT = Path(__file__).resolve().parents[1]
PROC, OUT = ROOT / "data" / "processed", ROOT / "web" / "public" / "data"
# Frase para cada variable según esté por encima (+) o por debajo (-) de lo típico; None = no se muestra
PHRASES = {
    "meses_desde_ultimo_vital": (None, "Estuvo en la lista hace poco"),
    "vitales_12m": ("Muchas importaciones de emergencia en el último año", None),
    "vitales_24m": ("Importaciones de emergencia repetidas en dos años", None),
    "vitales_historico": ("Historial largo en la lista", None),
    "vitales_12m_mismo_atc3": ("Su clase terapéutica está en crisis", None),
    "vitales_12m_mismo_atc4": ("Moléculas hermanas en desabastecimiento", None),
    "hhi_titulares": ("Mercado concentrado en pocos titulares", None),
    "un_solo_titular": ("Un solo titular con registro activo", None),
    "share_importadas": ("Depende de importaciones", "Producción mayormente local"),
    "titulares_activos": ("Varios titulares, pero con problemas recientes", "Pocos titulares activos"),
    "presentaciones_activas": ("Muchas presentaciones en el mercado", "Pocas presentaciones activas"),
    "sin_presentaciones_activas": ("Sin presentaciones activas", None),
    "perdidas_12m": ("Perdió registros en el último año", None),
    "perdidas_24m": ("Perdió registros en los últimos dos años", None),
    "ratio_perdidas_12m": ("Alta proporción de registros perdidos", None),
    "formas_activas": (None, "Pocas formas farmacéuticas disponibles"),
    "anios_en_mercado": ("Molécula antigua en el mercado", "Llegó hace poco al mercado"),
    "nuevas_12m": ("Cambios recientes de registros", None),
}
ATC = {"A": "aparato digestivo y metabolismo", "B": "sangre", "C": "cardiovascular", "D": "dermatológicos", "G": "genitourinario y hormonas sexuales",
       "H": "hormonas sistémicas", "J": "antiinfecciosos", "L": "antineoplásicos e inmunomoduladores", "M": "musculoesquelético",
       "N": "sistema nervioso", "P": "antiparasitarios", "R": "respiratorio", "S": "órganos de los sentidos", "V": "varios"}


def label(token: str) -> str | None:
    feature, sign = token.rsplit("|", 1)
    if feature.startswith("atc_grupo_"):
        g = feature[-1]
        return f"Grupo de riesgo: {ATC.get(g, g)}" if sign == "+" else None
    if feature.startswith("via_"):
        return f"Vía {feature[4:].lower()}" if sign == "+" else None
    hi, lo = PHRASES.get(feature, (None, None))
    return hi if sign == "+" else lo


def display_names() -> dict[str, str]:
    """Nombre legible más común para cada molécula canónica (se prefiere la escritura de la lista de vitales)."""
    from normalize import normalize, split_combo

    raw = ROOT / "data" / "raw"
    names: dict[str, str] = {}
    cum = pd.concat(pd.read_csv(raw / f, usecols=["principioactivo"], dtype=str) for f in ("cum_vigentes.csv", "cum_vencidos.csv"))
    cum["m"] = cum["principioactivo"].map(normalize)
    for m, s in cum.groupby("m")["principioactivo"]:
        cands = s.dropna().str.strip().unique()
        names[m] = min(cands, key=len)  # el nombre más corto suele ser el limpio ("ONDANSETRON")
    vit = pd.read_csv(raw / "vitales_no_disponibles.csv", usecols=["principio_activo1"], dtype=str)
    for orig in vit["principio_activo1"].dropna():
        if "/" not in orig:
            m = normalize(orig)
            if len(split_combo(orig)) == 1 and (m not in names or len(orig.strip()) <= len(names[m]) + 12):
                names[m] = orig.strip()
    import re

    def tidy(v: str) -> str:
        m = re.search(r"equivalente\s+(?:a|al)\s+(.+)", v, flags=re.I)
        v = m.group(1) if m else v
        v = re.sub(r"\(.*?\)", "", v)
        return re.sub(r"\s+", " ", v).strip(" .,").capitalize()

    return {k: tidy(v) for k, v in names.items()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vit = load_vitales()
    raw = pd.read_csv(ROOT / "data" / "raw" / "vitales_no_disponibles.csv", low_memory=False, dtype=str)
    raw["fecha"] = pd.to_datetime(raw["fecha_de_autorizaci_n"], errors="coerce").dt.tz_localize(None)

    por_anio = raw.groupby(raw["fecha"].dt.year).agg(autorizaciones=("fecha", "size")).reset_index(names="anio")
    por_anio["moleculas"] = por_anio["anio"].map(vit.groupby(vit["fecha"].dt.year)["molecula"].nunique())
    por_tipo = raw.groupby([raw["fecha"].dt.year.rename("anio"), "tipo_de_solicitud"]).size().unstack(fill_value=0)
    por_anio = por_anio.merge(por_tipo, left_on="anio", right_index=True)
    diag = raw["diagnostico_cie_1no_reporta"].str.strip().str.upper().value_counts().head(10)

    panel = pd.read_parquet(PROC / "panel.parquet")
    lab = panel[panel["corte"] < pd.Timestamp("2026-01-01")]
    pos = lab[lab["y"] == 1]
    recurrencia = float((pos["vitales_historico"] > 0).mean())

    rk = pd.read_parquet(PROC / "ranking_actual.parquet").sort_values("riesgo", ascending=False)
    # El ranking guarda los conteos transformados (log1p) que usa el modelo: para mostrar se toman los valores reales
    crudo = panel[panel["corte"] == panel["corte"].max()].set_index("molecula")
    conteos = ["presentaciones_activas", "titulares_activos", "share_importadas", "vitales_12m", "vitales_historico"]
    rk = rk.drop(columns=conteos).join(crudo[conteos], on="molecula")
    rk = rk[((rk["presentaciones_activas"] > 0) | (rk["vitales_historico"] > 0)) & (rk["molecula"].str.len() <= 40)].head(150)
    nombres = display_names()
    ultimo = vit.groupby("molecula")["fecha"].max()
    ranking = [
        {
            "molecula": nombres.get(r.molecula, r.molecula.title()),
            "atc": r.atc,
            "via": r.via.lower(),
            "riesgo": round(float(r.riesgo), 4),
            "prob": round(float(r.prob_lr), 4),
            "nuevo": bool(r.vitales_historico == 0),
            "presentaciones": int(r.presentaciones_activas),
            "titulares": int(r.titulares_activos),
            "importadas": round(float(r.share_importadas), 2),
            "vitales_12m": int(r.vitales_12m),
            "vitales_historico": int(r.vitales_historico),
            "ultimo_vital": ultimo.get(r.molecula).strftime("%Y-%m") if r.molecula in ultimo.index else None,
            "razones": [t for t in (label(x) for x in r.razones) if t],
        }
        for r in rk.itertuples()
    ]

    metricas = json.loads((ROOT / "reports" / "metricas.json").read_text())
    resumen = {
        "autorizaciones": int(len(raw)),
        "moleculas_lista": int(vit["molecula"].nunique()),
        "moleculas_cum": int(panel.loc[panel["corte"] == panel["corte"].max(), "molecula"].nunique()),
        "con_registro": int(len(set(vit["molecula"]) & set(panel["molecula"]))),
        "recurrencia": round(recurrencia, 3),
        "corte_ranking": "2026-09-30",
        "metricas": metricas,
    }
    files = {
        "resumen.json": resumen,
        "por_anio.json": por_anio.to_dict(orient="records"),
        "diagnosticos.json": [{"diagnostico": k.title(), "n": int(v)} for k, v in diag.items()],
        "ranking.json": ranking,
    }
    for name, data in files.items():
        (OUT / name).write_text(json.dumps(data, ensure_ascii=False, default=str))
    print({k: len(v) if isinstance(v, list) else "ok" for k, v in files.items()}, "recurrencia", recurrencia)


if __name__ == "__main__":
    main()
