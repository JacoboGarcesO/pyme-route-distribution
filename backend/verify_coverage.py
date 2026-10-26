"""T16: verify the coverage core against the edge cases of docs/diseno.md (T09).

Run from the backend folder: python verify_coverage.py
"""

import sys

from domain.coverage import reachability, visit_order
from domain.errors import DestinationNotFound, OriginNotFound
from domain.graph import Graph
from seed import seed_network

# Visit order from the warehouse: the manual trace of T08.
BFS_FROM_BOD = [
    "BOD", "C10K5", "C11K6", "C12K5", "C10K6", "C11K7", "C12K6", "CasaA",
    "C10K7", "C12K7", "CasaC", "C10K8", "C12K8", "C11K8", "CasaB",
]

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


def expect_error(scenario, error_type, action):
    try:
        action()
    except Exception as exc:
        obtained = f"{type(exc).__name__}: {exc}"
        report(scenario, error_type.__name__, obtained, type(exc) is error_type)
        return
    report(scenario, error_type.__name__, "no hubo error", False)


def section(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


graph = Graph()
points = seed_network(graph)
label_of = {point.id: label for label, point in points.items()}


def order_labels(origin):
    return [label_of[point_id] for point_id in visit_order(graph, points[origin].id)]


def check(origin, destination):
    result = reachability(graph, points[origin].id, points[destination].id)
    return result.reachable, result.reason


# --- T13: reachability of a destination --------------------------------------

section("BLOQUE 1 - Alcance hacia un destino (T13)")

expect_value(
    "El orden de visita desde BOD coincide con la traza de T08",
    BFS_FROM_BOD,
    lambda: order_labels("BOD"),
)
expect_value("Destino alcanzable: CasaA desde BOD", (True, None), lambda: check("BOD", "CasaA"))
expect_value("Destino lejano alcanzable: CasaB desde BOD", (True, None), lambda: check("BOD", "CasaB"))
expect_value(
    "B6 - destino desconectado: CasaD desde BOD",
    (False, "No hay un camino dirigido desde 'Bodega central' hasta 'Casa D'."),
    lambda: check("BOD", "CasaD"),
)
expect_value(
    "CasaD no aparece en el recorrido desde BOD",
    False,
    lambda: "CasaD" in order_labels("BOD"),
)

section("RESUMEN")
passed = sum(results)
print(f"{passed}/{len(results)} escenarios pasaron")
sys.exit(0 if passed == len(results) else 1)
