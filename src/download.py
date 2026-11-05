"""Descarga los datasets públicos del INVIMA desde datos.gov.co (API Socrata) a data/raw/."""
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
DATASETS = {
    # Código Único de Medicamentos: cada fila es una presentación comercial y su principio activo
    "cum_vigentes": "i7cb-raxc",
    "cum_vencidos": "vwwf-4ftk",
    # Autorizaciones de importación de medicamentos vitales no disponibles (proxy de desabastecimiento)
    "vitales_no_disponibles": "sdmr-tfmf",
}
PAGE = 50_000


def download(name: str, dataset_id: str) -> Path:
    out = RAW / f"{name}.csv"
    if out.exists():
        print(f"{name}: ya existe ({out.stat().st_size / 1e6:.1f} MB)")
        return out
    RAW.mkdir(parents=True, exist_ok=True)
    url = f"https://www.datos.gov.co/resource/{dataset_id}.csv"
    with open(out, "wb") as f:
        offset = 0
        while True:
            r = requests.get(url, params={"$limit": PAGE, "$offset": offset, "$order": ":id"}, timeout=300)
            r.raise_for_status()
            body = r.content
            if offset:  # quitar el encabezado de las páginas siguientes
                body = body.split(b"\n", 1)[1] if b"\n" in body else b""
            if not body.strip():
                break
            f.write(body if body.endswith(b"\n") else body + b"\n")
            rows = body.count(b"\n")
            print(f"{name}: +{rows} filas (offset {offset})")
            if rows < PAGE - 1:
                break
            offset += PAGE
    return out


if __name__ == "__main__":
    for name, ds in DATASETS.items():
        download(name, ds)
