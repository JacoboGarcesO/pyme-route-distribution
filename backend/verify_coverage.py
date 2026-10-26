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

# --- T14: origin and destination validation ----------------------------------

section("BLOQUE 2 - Validar origen y destino (T14)")

bod_id = points["BOD"].id


def message_of(action):
    try:
        action()
    except Exception as exc:
        return exc.message
    return None


expect_error(
    "B2 - origen con formato de UUID inválido",
    OriginNotFound,
    lambda: visit_order(graph, NOT_A_UUID),
)
expect_error(
    "B3 - origen con UUID válido que no está en la red",
    OriginNotFound,
    lambda: visit_order(graph, UNKNOWN_UUID),
)
expect_error(
    "B7 - destino con formato de UUID inválido",
    DestinationNotFound,
    lambda: reachability(graph, bod_id, NOT_A_UUID),
)
expect_error(
    "B7 - destino con UUID válido que no está en la red",
    DestinationNotFound,
    lambda: reachability(graph, bod_id, UNKNOWN_UUID),
)
expect_error(
    "B12 - origen y destino inexistentes: se informa el origen",
    OriginNotFound,
    lambda: reachability(graph, UNKNOWN_UUID, UNKNOWN_UUID),
)
origin_message = message_of(lambda: reachability(graph, UNKNOWN_UUID, bod_id))
destination_message = message_of(lambda: reachability(graph, bod_id, UNKNOWN_UUID))
expect_value(
    "Los mensajes de origen y destino inexistente dicen cuál falla",
    (True, True, True),
    lambda: (
        origin_message.startswith("El punto de origen"),
        destination_message.startswith("El punto de destino"),
        origin_message != destination_message,
    ),
)

# --- T15: empty network and origin without exits ------------------------------

section("BLOQUE 3 - Red vacía y origen sin salidas (T15)")

expect_error(
    "B4 - red vacía: cualquier origen no existe",
    OriginNotFound,
    lambda: visit_order(Graph(), UNKNOWN_UUID),
)
expect_error(
    "B4 - red vacía: la consulta con destino también falla por el origen",
    OriginNotFound,
    lambda: reachability(Graph(), UNKNOWN_UUID, UNKNOWN_UUID),
)
expect_value(
    "B5 - origen sin salidas (CasaA): solo se visita a sí mismo",
    ["CasaA"],
    lambda: order_labels("CasaA"),
)
expect_value(
    "B5 - origen sin salidas: la lista de alcanzables queda vacía",
    [],
    lambda: order_labels("CasaA")[1:],
)
expect_value(
    "B5 - origen aislado (CasaD): solo se visita a sí mismo",
    ["CasaD"],
    lambda: order_labels("CasaD"),
)
def single_point_visits():
    lonely = Graph()
    only = lonely.add_point("Solo", "warehouse")
    return len(visit_order(lonely, only.id))


expect_value("Una red con un solo punto y sin conexiones no falla", 1, single_point_visits)

section("RESUMEN")
passed = sum(results)
print(f"{passed}/{len(results)} escenarios pasaron")
sys.exit(0 if passed == len(results) else 1)
