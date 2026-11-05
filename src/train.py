"""Entrena y evalúa el modelo de riesgo de desabastecimiento con validación temporal.

- Validación de origen móvil: para cada año de prueba (cortes 2021–2024) se entrena solo con cortes anteriores.
- Prueba principal: corte 2024-12-31 → ¿qué moléculas entran a vitales no disponibles en 2025?
- Línea base: "lo que ya estuvo en la lista vuelve a estar" (persistencia de los últimos 12 meses).
- Ensamble: promedio de rangos entre regresión logística y gradient boosting.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score
from sklearn.pipeline import Pipeline
from scipy.stats import rankdata
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

NUM = ["anios_en_mercado", "presentaciones_activas", "titulares_activos", "formas_activas", "share_importadas",
       "hhi_titulares", "perdidas_12m", "perdidas_24m", "nuevas_12m", "ratio_perdidas_12m", "sin_presentaciones_activas",
       "un_solo_titular", "vitales_12m", "vitales_24m", "vitales_historico", "meses_desde_ultimo_vital", "vitales_12m_mismo_atc4",
       "vitales_12m_mismo_atc3"]
CAT = ["atc_grupo", "via"]
TEST_CUT = pd.Timestamp("2024-12-31")
SCORE_CUT = pd.Timestamp("2026-09-30")


def log1p_counts(X: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()
    for c in ["presentaciones_activas", "perdidas_12m", "perdidas_24m", "nuevas_12m", "vitales_12m", "vitales_24m", "vitales_historico",
              "vitales_12m_mismo_atc4", "vitales_12m_mismo_atc3"]:
        X[c] = np.log1p(X[c])
    X["meses_desde_ultimo_vital"] = np.log1p(X["meses_desde_ultimo_vital"])
    return X


def models() -> dict[str, Pipeline]:
    pre_lin = ColumnTransformer([("num", StandardScaler(), NUM), ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    pre_tree = ColumnTransformer([("num", "passthrough", NUM), ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT)])
    return {
        "regresion_logistica": Pipeline([("pre", pre_lin), ("clf", LogisticRegression(C=0.5, class_weight="balanced", max_iter=2000))]),
        "gradient_boosting": Pipeline([("pre", pre_tree), ("clf", HistGradientBoostingClassifier(
            learning_rate=0.05, max_iter=300, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0,
            class_weight="balanced", random_state=42))]),
    }


def precision_at_k(y: np.ndarray, s: np.ndarray, k: int) -> float:
    idx = np.argsort(-s)[:k]
    return float(y[idx].mean())


def evaluate(y: np.ndarray, s: np.ndarray) -> dict:
    return {
        "roc_auc": round(float(roc_auc_score(y, s)), 4),
        "average_precision": round(float(average_precision_score(y, s)), 4),
        "precision_at_20": round(precision_at_k(y, s, 20), 3),
        "precision_at_50": round(precision_at_k(y, s, 50), 3),
        "recall_at_100": round(float(y[np.argsort(-s)[:100]].sum() / max(y.sum(), 1)), 3),
    }


def baseline(df: pd.DataFrame) -> np.ndarray:
    return df["vitales_12m"].values + 1e-3 * df["vitales_historico"].values


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, X_cols: list[str]) -> dict[str, np.ndarray]:
    out = {"linea_base_persistencia": baseline(test)}
    for name, pipe in models().items():
        pipe.fit(train[X_cols], train["y"])
        out[name] = pipe.predict_proba(test[X_cols])[:, 1]
    out["ensamble"] = (rankdata(out["regresion_logistica"]) + rankdata(out["gradient_boosting"])) / (2 * len(test))
    return out


def rolling(labeled: pd.DataFrame, X_cols: list[str]) -> dict:
    """Validación de origen móvil: un pliegue por año de prueba."""
    folds = {}
    for cut in sorted(labeled["corte"].unique())[3:]:
        tr, te = labeled[labeled["corte"] < cut], labeled[labeled["corte"] == cut]
        preds = fit_predict(tr, te, X_cols)
        folds[str(pd.Timestamp(cut).year + 1)] = {
            name: {**evaluate(te["y"].values, sc), "auc_casos_nuevos": round(float(roc_auc_score(
                te.loc[te["vitales_historico"] == 0, "y"], sc[(te["vitales_historico"] == 0).values])), 4)}
            for name, sc in preds.items()
        }
    names = next(iter(folds.values())).keys()
    mean = {n: {k: round(float(np.mean([folds[f][n][k] for f in folds])), 4) for k in folds[next(iter(folds))][n]} for n in names}
    return {"pliegues": folds, "promedio": mean}


def main():
    panel = pd.read_parquet(PROC / "panel.parquet")
    panel = log1p_counts(panel)
    labeled = panel[panel["corte"] < SCORE_CUT]
    train, test = labeled[labeled["corte"] < TEST_CUT], labeled[labeled["corte"] == TEST_CUT]
    X_cols = NUM + CAT

    results_rolling = rolling(labeled, X_cols)
    for n, m in results_rolling["promedio"].items():
        print(f"{n:28s}", m)

    results = {"validacion_movil": results_rolling, "train_rows": int(len(train)), "test_rows": int(len(test)), "test_positivos": int(test["y"].sum()),
               "tasa_base_test": round(float(test["y"].mean()), 4), "modelos": {}}
    # Línea base: persistencia (cuántas autorizaciones tuvo en los últimos 12 meses)
    preds = fit_predict(train, test, X_cols)
    for name, sc in preds.items():
        results["modelos"][name] = evaluate(test["y"].values, sc)
    # Se elige por el promedio de la validación móvil (no por un solo año)
    avg = results_rolling["promedio"]
    best = max(["regresion_logistica", "gradient_boosting", "ensamble"], key=lambda n: (avg[n]["average_precision"] + avg[n]["roc_auc"]))
    results["mejor_modelo"] = best
    s_test = preds[best]

    # Curva precisión-recall del mejor modelo y de la línea base (para la web)
    def pr(y, s):
        p, r, _ = precision_recall_curve(y, s)
        step = max(1, len(p) // 60)
        return [{"recall": round(float(a), 3), "precision": round(float(b), 3)} for a, b in zip(r[::step], p[::step])]

    results["pr_modelo"] = pr(test["y"].values, s_test)
    results["pr_linea_base"] = pr(test["y"].values, baseline(test))

    # ¿Qué tan bien encuentra los casos NUEVOS (sin historial en la lista)?
    nuevos = test["vitales_historico"] == 0
    results["nuevos_casos"] = {
        "positivos": int(test.loc[nuevos, "y"].sum()),
        **evaluate(test.loc[nuevos, "y"].values, s_test[nuevos.values]),
    }

    lr_final, gb_final = models()["regresion_logistica"], models()["gradient_boosting"]
    lr_final.fit(labeled[X_cols], labeled["y"])
    gb_final.fit(labeled[X_cols], labeled["y"])
    imp_model = models()["regresion_logistica" if best == "regresion_logistica" else "gradient_boosting"].fit(train[X_cols], train["y"])
    imp = permutation_importance(imp_model, test[X_cols], test["y"], scoring="roc_auc", n_repeats=15, random_state=0)
    results["importancia"] = sorted(
        [{"variable": c, "importancia": round(float(m), 4)} for c, m in zip(X_cols, imp.importances_mean)],
        key=lambda d: -d["importancia"],
    )

    now = panel[panel["corte"] == SCORE_CUT].copy()
    p_lr = lr_final.predict_proba(now[X_cols])[:, 1]
    p_gb = gb_final.predict_proba(now[X_cols])[:, 1]
    now["riesgo"] = {"regresion_logistica": p_lr, "gradient_boosting": p_gb}.get(best, (rankdata(p_lr) + rankdata(p_gb)) / (2 * len(now)))
    now["prob_lr"] = p_lr
    final = lr_final
    # Contribuciones lineales (coeficiente × valor estandarizado) para explicar cada predicción en la web
    pre, clf = lr_final.named_steps["pre"], lr_final.named_steps["clf"]
    Z = pre.transform(now[X_cols])
    Z = Z.toarray() if hasattr(Z, "toarray") else Z
    contrib = Z * clf.coef_[0]
    names = list(pre.get_feature_names_out())
    # Cada razón guarda la variable y si el valor estaba por encima (+) o por debajo (-) del promedio
    now["razones"] = [
        [f"{names[j].split('__', 1)[1]}|{'+' if z[j] > 0 else '-'}" for j in np.argsort(-row)[:3] if row[j] > 0.15]
        for row, z in zip(contrib, Z)
    ]
    test_scored = test.assign(riesgo=s_test)

    PROC.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    joblib.dump(final, PROC / "modelo.joblib")
    now.to_parquet(PROC / "ranking_actual.parquet", index=False)
    test_scored.to_parquet(PROC / "backtest_2025.parquet", index=False)
    (REPORTS / "metricas.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("mejor:", best, "| nuevos casos:", results["nuevos_casos"])
    print(results["importancia"][:8])


if __name__ == "__main__":
    main()
