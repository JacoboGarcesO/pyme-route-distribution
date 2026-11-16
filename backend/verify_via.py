"""T08 de F4: verifica la parada obligatoria (`via`) de GET /shortest-path.

Ejecutar desde la carpeta backend: python verify_via.py
"""

import sys
from urllib.parse import urlencode

from app import app
from domain.graph import Graph

NOT_A_UUID = "no-es-un-uuid"
UNKNOWN_UUID = "00000000-0000-0000-0000-000000000000"

results = []


def report(scenario, expected, obtained):
    passed = obtained == expected
    print(f"[{'PASO' if passed else 'FALLO'}] {scenario}")
    print(f"    esperado: {expected}")
    print(f"    obtenido: {obtained}")
    results.append(passed)


# Bodega -> Casa A directo 9; por Norte y Centro 7; Taller es un desvío (Bodega -> Taller -> Casa A = 11);
# Norte -> Bodega permite una ruta que vuelve sobre Norte; Casa D está aislada.
NAMES = ["Bodega", "Norte", "Centro", "Casa A", "Taller", "Casa D"]
EDGES = [
    ("Bodega", "Casa A", "9"), ("Bodega", "Norte", "3"), ("Norte", "Centro", "2"),
    ("Centro", "Casa A", "2"), ("Bodega", "Taller", "1"), ("Taller", "Casa A", "10"),
    ("Norte", "Bodega", "3"),
]

graph = Graph()
points = {name: graph.add_point(name, "neighborhood") for name in NAMES}
ids = {name: str(point.id) for name, point in points.items()}
for origin, destination, cost in EDGES:
    graph.add_connection(ids[origin], ids[destination], cost)
app.extensions["graph"] = graph
client = app.test_client()


def call(origin, destination, via=None):
    params = {"origin": ids.get(origin, origin), "destination": ids.get(destination, destination)}
    if via is not None:
        params["via"] = ids.get(via, via)
    response = client.get("/shortest-path?" + urlencode(params))
    return response.status_code, response.get_json()


def route(origin, destination, via=None):
    """(HTTP, nombres de la ruta, costo total) de una consulta con resultado."""
    status, body = call(origin, destination, via)
    return status, [p["name"] for p in body["path"]], body["total_cost_km"]


def error(origin, destination, via=None):
    status, body = call(origin, destination, via)
    return status, body.get("error", {}).get("code")


report("V1 sin parada: la ruta de F3 no cambia",
       (200, ["Bodega", "Norte", "Centro", "Casa A"], "7"), route("Bodega", "Casa A"))
report("V2 parada ya sobre la mejor ruta: la ruta no cambia",
       (200, ["Bodega", "Norte", "Centro", "Casa A"], "7"), route("Bodega", "Casa A", "Norte"))
report("V3 parada fuera de la mejor ruta: obliga el desvío (1 + 10 km)",
       (200, ["Bodega", "Taller", "Casa A"], "11"), route("Bodega", "Casa A", "Taller"))
report("V4 parada igual al origen: es la ruta normal",
       (200, ["Bodega", "Norte", "Centro", "Casa A"], "7"), route("Bodega", "Casa A", "Bodega"))
report("V5 parada igual al destino: es la ruta normal",
       (200, ["Bodega", "Norte", "Centro", "Casa A"], "7"), route("Bodega", "Casa A", "Casa A"))
report("V6 la parada puede obligar a pasar dos veces por un punto (3 + 3 + 2 + 2 km)",
       (200, ["Norte", "Bodega", "Norte", "Centro", "Casa A"], "10"), route("Norte", "Casa A", "Bodega"))

status, body = call("Bodega", "Casa A", "Taller")
report("V7 la respuesta incluye via_id de la parada",
       ids["Taller"], body.get("via_id"))

status, body = call("Casa A", "Casa D", "Norte")
report("V8 sin camino origen -> parada: found false con razón y sin error HTTP",
       (200, False, None, True), (status, body["found"], body["total_cost_km"], "Casa A" in body["reason"]))
status, body = call("Bodega", "Casa D", "Norte")
report("V9 sin camino parada -> destino: found false con razón",
       (200, False, True), (status, body["found"], "Norte" in body["reason"]))

report("V10 parada inexistente: 404 VIA_NOT_FOUND", (404, "VIA_NOT_FOUND"), error("Bodega", "Casa A", UNKNOWN_UUID))
report("V11 parada con UUID inválido: 404 VIA_NOT_FOUND", (404, "VIA_NOT_FOUND"), error("Bodega", "Casa A", NOT_A_UUID))
report("V12 origen inexistente se valida antes que la parada",
       (404, "ORIGIN_NOT_FOUND"), error(UNKNOWN_UUID, "Casa A", UNKNOWN_UUID))
report("V13 destino inexistente se valida antes que la parada",
       (404, "DESTINATION_NOT_FOUND"), error("Bodega", UNKNOWN_UUID, UNKNOWN_UUID))

print()
print(f"{sum(results)}/{len(results)} escenarios pasaron")
sys.exit(0 if all(results) else 1)
