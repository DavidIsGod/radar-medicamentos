"""Normalización de nombres de principios activos para cruzar CUM y vitales no disponibles."""
import re

from unidecode import unidecode

# Sales, hidratos y formas que no cambian la molécula activa
SALT_WORDS = {
    "CLORHIDRATO", "DICLORHIDRATO", "HIDROCLORURO", "BROMHIDRATO", "SODICO", "SODICA", "POTASICO", "POTASICA",
    "CALCICO", "CALCICA", "MAGNESICO", "MAGNESICA", "MONOHIDRATO", "DIHIDRATO", "TRIHIDRATO", "HEMIHIDRATO",
    "SESQUIHIDRATO", "PENTAHIDRATO", "HEPTAHIDRATO", "ANHIDRO", "ANHIDRA", "MALEATO", "SULFATO", "FOSFATO",
    "ACETATO", "CITRATO", "BESILATO", "BESYLATO", "TARTRATO", "BITARTRATO", "MESILATO", "DIMESILATO", "FUMARATO",
    "SUCCINATO", "HEMISUCCINATO", "LACTATO", "GLUCONATO", "PROPIONATO", "VALERATO", "DIPROPIONATO", "FUROATO",
    "BUTIRATO", "ESTOLATO", "ETILSUCCINATO", "TOSILATO", "MICRONIZADO", "MICRONIZADA", "BASE", "SAL", "HIDRATADO",
    "LISINA", "TROMETAMOL", "ARGININA", "MEGLUMINA", "OXALATO", "PAMOATO", "NITRATO", "DECANOATO", "ENANTATO",
}
STOP = {"DE", "DEL", "LA", "EL", "Y", "COMO", "EN", "FORMA"}


def normalize(name: object) -> str:
    """'CLORHIDRATO DE METFORMINA' -> 'METFORMINA'; 'SELENATO DE SODIO EQUIVALENTE A SELENIO' -> 'SELENIO'."""
    if not isinstance(name, str):
        return ""
    s = unidecode(name).upper()
    s = re.sub(r"\(.*?\)", " ", s)
    m = re.search(r"EQUIVALENTE\s+(?:A|AL|EN)\s+(.+)", s)
    if m:
        s = m.group(1)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    words = [w for w in s.split() if w not in SALT_WORDS]
    # Orden canónico: "CLORURO DE POTASIO" y "POTASIO CLORURO" son la misma molécula
    words = sorted(w for w in words if w not in STOP)
    return " ".join(words)


def split_combo(name: object) -> list[str]:
    """Las combinaciones de vitales vienen como 'A / B / C'."""
    if not isinstance(name, str):
        return []
    parts = re.split(r"\s*(?:/|\+| Y )\s*", unidecode(name).upper())
    return [p for p in (normalize(x) for x in parts) if p]
