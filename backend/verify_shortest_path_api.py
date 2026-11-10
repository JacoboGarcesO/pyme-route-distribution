"""T17 y T18: verifica GET /shortest-path contra los casos R1 a R12 de docs/diseno.md (T08).

Ejecutar desde la carpeta backend: python verify_shortest_path_api.py
"""

import sys
from decimal import Decimal
from urllib.parse import urlencode

from app import app
from domain.graph import Graph

NOT_A_UUID = "no-es-un-uuid"
UNKNOWN_UUID = "00000000-0000-0000-0000-000000000000"

results = []


def report(scenario, expected, obtained, passed):
    print(f"[{'PASO' if passed else 'FALLO'}] {scenario}")
    print(f"    esperado: {expected}")
    print(f"    obtenido: {obtained}")
    results.append(passed)


def expect_value(scenario, expected, action):
    try:
        obtained = action()
    except Exception as exc:
        report(scenario, expected, f"{type(exc).__name__}: {exc}", False)
        return
    report(scenario, expected, obtained, obtained == expected)


def section(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


client = app.test_client()


def make_network(names, edges):
    """Red de prueba: puntos por nombre y conexiones (origen, destino, km)."""
    graph = Graph()
    points = {name: graph.add_point(name, "neighborhood") for name in names}
    ids = {name: str(point.id) for name, point in points.items()}
    for origin, destination, cost in edges:
        graph.add_connection(ids[origin], ids[destination], cost)
    return graph, ids


def use(graph):
    app.extensions["graph"] = graph


def call(origin=None, destination=None):
    """Consulta GET /shortest-path; un parámetro None no se envía."""
    params = {}
    if origin is not None:
        params["origin"] = origin
    if destination is not None:
        params["destination"] = destination
    response = client.get("/shortest-path" + (f"?{urlencode(params)}" if params else ""))
    return response.status_code, response.get_json()


def error_of(origin=None, destination=None):
    """(HTTP, code, message) de una consulta que debe fallar."""
    status, body = call(origin, destination)
    error = body.get("error", {})
    return status, error.get("code"), error.get("message")


# Bodega -> Casa A directo cuesta 9 (1 salto); Bodega -> Norte -> Centro -> Casa A cuesta 7 (3 saltos).
# Centro y Norte forman un ciclo (mismo costo en ambos sentidos); Casa D está aislada.
NAMES = ["Bodega", "Norte", "Centro", "Casa A", "Casa D"]
EDGES = [
    ("Bodega", "Casa A", "9"),
    ("Bodega", "Norte", "3"),
    ("Norte", "Centro", "2"),
    ("Centro", "Norte", "2"),
    ("Centro", "Casa A", "2"),
]
graph, ids = make_network(NAMES, EDGES)
use(graph)

# --- T17: errors of the query (R1 to R5) -----------------------------------

section("BLOQUE 1 - Errores de entrada (R1 a R5)")

MISSING = (400, "MISSING_DATA")
NO_ORIGIN = (404, "ORIGIN_NOT_FOUND")
NO_DESTINATION = (404, "DESTINATION_NOT_FOUND")

expect_value("R1 - sin parámetros", MISSING, lambda: error_of()[:2])
expect_value("R1 - falta destination", MISSING, lambda: error_of(ids["Bodega"])[:2])
expect_value("R1 - falta origin", MISSING, lambda: error_of(None, ids["Bodega"])[:2])
expect_value("R1 - origin vacío", MISSING, lambda: error_of("", ids["Bodega"])[:2])
expect_value("R1 - destination solo espacios", MISSING, lambda: error_of(ids["Bodega"], "   ")[:2])
expect_value(
    "R1 - faltan los dos: el mensaje habla de origin",
    "El parámetro 'origin' es obligatorio.",
    lambda: error_of()[2],
)
expect_value(
    "R1 - falta solo destination: el mensaje habla de destination",
    "El parámetro 'destination' es obligatorio.",
    lambda: error_of(ids["Bodega"])[2],
)
expect_value("R2 - origen con formato inválido", NO_ORIGIN, lambda: error_of(NOT_A_UUID, ids["Bodega"])[:2])
expect_value("R2 - origen no registrado", NO_ORIGIN, lambda: error_of(UNKNOWN_UUID, ids["Bodega"])[:2])
expect_value(
    "R2 - el mensaje dice que falla el origen",
    True,
    lambda: error_of(UNKNOWN_UUID, ids["Bodega"])[2].startswith("El punto de origen"),
)
expect_value("R3 - destino con formato inválido", NO_DESTINATION, lambda: error_of(ids["Bodega"], NOT_A_UUID)[:2])
expect_value("R3 - destino no registrado", NO_DESTINATION, lambda: error_of(ids["Bodega"], UNKNOWN_UUID)[:2])
expect_value(
    "R3 - el mensaje dice que falla el destino",
    True,
    lambda: error_of(ids["Bodega"], UNKNOWN_UUID)[2].startswith("El punto de destino"),
)


def on_empty_network():
    use(Graph())
    try:
        return error_of(UNKNOWN_UUID, UNKNOWN_UUID)[:2]
    finally:
        use(graph)


expect_value("R4 - red vacía: el origen no existe", NO_ORIGIN, on_empty_network)
expect_value(
    "R5 - origen y destino inexistentes: se informa el origen",
    NO_ORIGIN,
    lambda: error_of(UNKNOWN_UUID, UNKNOWN_UUID)[:2],
)
expect_value(
    "Los errores traen solo code y message",
    ["code", "message"],
    lambda: sorted(call(UNKNOWN_UUID, ids["Bodega"])[1]["error"]),
)

# --- T17: business answers that are not errors (R6 to R9) ------------------

section("BLOQUE 2 - Respuestas de negocio: 200 aunque no haya ruta (R6 a R9)")


def route(origin, destination):
    """(HTTP, found, nombres de la ruta, costo total, cantidad de tramos)."""
    status, body = call(ids[origin], ids[destination])
    names = [point["name"] for point in body["path"]]
    return status, body["found"], names, body["total_cost_km"], len(body["connections"])


expect_value(
    "R6 - origen igual al destino: un solo punto, costo 0 y sin tramos",
    (200, True, ["Bodega"], "0", 0),
    lambda: route("Bodega", "Bodega"),
)
expect_value(
    "R7 - destino aislado: no hay ruta",
    (200, False, [], None, 0),
    lambda: route("Bodega", "Casa D"),
)
expect_value(
    "R7 - sentido contrario de un solo sentido: no hay ruta",
    (200, False, [], None, 0),
    lambda: route("Casa A", "Bodega"),
)
expect_value(
    "R7 - la razón nombra el origen y el destino",
    "No hay un camino dirigido desde 'Casa A' hasta 'Bodega'.",
    lambda: call(ids["Casa A"], ids["Bodega"])[1]["reason"],
)
expect_value(
    "R7 - con ruta no aparece el campo reason",
    False,
    lambda: "reason" in call(ids["Bodega"], ids["Casa A"])[1],
)
expect_value(
    "R8 - origen aislado con otro destino: no hay ruta",
    (200, False, [], None, 0),
    lambda: route("Casa D", "Bodega"),
)
expect_value(
    "R8 - origen sin salidas (Casa A) con otro destino: no hay ruta",
    (200, False, [], None, 0),
    lambda: route("Casa A", "Norte"),
)
expect_value(
    "R9 - ciclo entre Norte y Centro: termina y devuelve la ruta",
    (200, True, ["Bodega", "Norte", "Centro", "Casa A"], "7", 3),
    lambda: route("Bodega", "Casa A"),
)

section("RESUMEN")
passed = sum(results)
print(f"{passed}/{len(results)} escenarios pasaron")
sys.exit(0 if passed == len(results) else 1)
