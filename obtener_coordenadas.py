import requests
import pandas as pd

URL = "https://apis.datos.gob.ar/georef/api/localidades"

def buscar_coordenadas(localidad):
    params = {
        "nombre": localidad,
        "provincia": "Entre Ríos",
        "exacto": "true",
        "max": 1,
    }
    respuesta = requests.get(URL, params=params, timeout=10)
    respuesta.raise_for_status()
    datos = respuesta.json()

    if datos["cantidad"] == 0:
        print(f"No encontré: {localidad}")
        return None, None

    centro = datos["localidades"][0]["centroide"]
    return centro["lat"], centro["lon"]


paradas = pd.read_csv("paradas.csv")
localidades = sorted(set(paradas["localidad"]) | {"Paraná"})

filas = []
for loc in localidades:
    lat, lon = buscar_coordenadas(loc)
    filas.append({"localidad": loc, "lat": lat, "lon": lon})

coords = pd.DataFrame(filas)
coords.to_csv("coordenadas.csv", index=False)
print(coords)