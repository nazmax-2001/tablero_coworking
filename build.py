"""
Genera el tablero de puestos de coworking de MiradorTEC como una página HTML estática.

Uso:
    python build.py

Lee data/coworking.csv y escribe docs/index.html usando template.html.
"""
import base64
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

BASE = Path(__file__).parent
COWORKING = BASE / "data" / "coworking.csv"
TEMPLATE = BASE / "template.html"
SALIDA = BASE / "docs" / "index.html"
PLOTLY = BASE / "vendor" / "plotly-basic.min.js"
LOGO = BASE / "assets" / "logo.png"

# Precio de referencia por puesto (MTEC por mes), del tarifario de MiradorTEC.
# Se usa para estimar cuánto podrían generar los puestos libres. Cambiarlo acá si se actualiza la tarifa.
TARIFA_REFERENCIA = 120

NULOS = {"", "na", "n/a", "nd", "s/d", "-", "nan"}


def limpio(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    t = re.sub(r"\s+", " ", str(v)).strip()
    return "" if t.lower() in NULOS else t


def sin_tildes(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def numero(v):
    try:
        return float(limpio(v).replace(",", "."))
    except ValueError:
        return None


def leer(ruta) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp1252"):
        try:
            df = pd.read_csv(ruta, sep=None, engine="python", encoding=enc, dtype=str)
            df.columns = [c.strip() for c in df.columns]
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo leer {ruta}")


def col(df, *opciones):
    norm = {sin_tildes(c).lower(): c for c in df.columns}
    for o in opciones:
        for k, c in norm.items():
            if k.startswith(sin_tildes(o).lower()):
                return c
    return None


def main() -> None:
    cw = leer(COWORKING)
    c_cod, c_emp, c_est = col(cw, "Codigo"), col(cw, "Empresa"), col(cw, "Estado")
    c_cant, c_precio = col(cw, "CantPuestos", "Puestos"), col(cw, "Precio", "MTEC")

    puestos = []
    for _, f in cw.iterrows():
        emp = limpio(f[c_emp]) if c_emp else ""
        if emp.strip("()").lower() in {"sin asignar", "libre", "vacante"}:
            emp = ""
        est = sin_tildes(limpio(f[c_est])).upper() if c_est else ""
        estado = {"RENTADO": "Rentado", "ALQUILADO": "Rentado", "OCUPADO": "Rentado",
                  "LIBRE": "Libre", "DISPONIBLE": "Libre"}.get(est, "Rentado" if emp else "Libre")
        cant = numero(f[c_cant]) if c_cant else None
        puestos.append({
            "codigo": limpio(f[c_cod]) if c_cod else "",
            "empresa": emp,
            "estado": estado,
            "cant": int(cant) if cant else 1,
            "cantCargada": bool(cant),
            "precio": numero(f[c_precio]) if c_precio else None,
        })

    meta = {
        "actualizado": datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime("%d/%m/%Y %H:%M"),
        "tarifaRef": TARIFA_REFERENCIA,
        "faltan": {
            "cant": sum(1 for x in puestos if not x["cantCargada"]),
            "precio": sum(1 for x in puestos if x["estado"] == "Rentado" and not x["precio"]),
            "hayColumnaPrecio": bool(c_precio),
        },
    }

    logo = "data:image/png;base64," + base64.b64encode(LOGO.read_bytes()).decode()
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__PLOTLY__", PLOTLY.read_text(encoding="utf-8").replace("</script>", "<\\/script>"))
    html = html.replace("__LOGO__", logo)
    html = html.replace("__DATOS__", json.dumps(puestos, ensure_ascii=False))
    html = html.replace("__META__", json.dumps(meta, ensure_ascii=False))
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(html, encoding="utf-8")
    print(f"Tablero generado: {SALIDA} ({len(puestos)} filas de puestos)")


if __name__ == "__main__":
    main()
