"""T16: verify the coverage core against the edge cases of docs/diseno.md (T09).

Run from the backend folder: python verify_coverage.py
"""

import sys

from app import app
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

# --- T09: destination equal to origin, cycles and one-way streets -------------

section("BLOQUE 4 - Destino igual al origen, ciclos y un solo sentido (T09)")

expect_value("B8 - destino igual al origen", (True, None), lambda: check("BOD", "BOD"))
expect_value(
    "B8 - destino igual al origen, aunque no tenga salidas",
    (True, None),
    lambda: check("CasaD", "CasaD"),
)
expect_value(
    "B9 - ciclo: el recorrido desde BOD termina con 15 puntos",
    15,
    lambda: len(order_labels("BOD")),
)
expect_value(
    "B9 - ciclo: ningún punto se repite en el orden de visita",
    True,
    lambda: len(order_labels("BOD")) == len(set(order_labels("BOD"))),
)
expect_value(
    "B9 - ciclo C10K5 y C10K6: cada uno alcanza al otro",
    ((True, None), (True, None)),
    lambda: (check("C10K5", "C10K6"), check("C10K6", "C10K5")),
)
expect_value("B10 - un sentido: C11K6 llega a CasaA", (True, None), lambda: check("C11K6", "CasaA"))
expect_value(
    "B10 - un sentido: CasaA no llega a C11K6",
    (False, "No hay un camino dirigido desde 'Casa A' hasta 'Calle 11 con Carrera 6'."),
    lambda: check("CasaA", "C11K6"),
)
expect_value(
    "Transitividad: BOD llega a CasaA sin conexión directa",
    (True, None),
    lambda: check("BOD", "CasaA"),
)

# --- T18: HTTP codes of GET /coverage -----------------------------------------

section("BLOQUE 5 - Códigos HTTP del endpoint (T18)")

app.extensions["graph"] = graph
client = app.test_client()


def call(path):
    response = client.get(path)
    body = response.get_json()
    code = body["error"]["code"] if response.status_code >= 400 else None
    return response.status_code, code, body


def http(path):
    status, code, _ = call(path)
    return status, code


def on_empty_network(action):
    app.extensions["graph"] = Graph()
    try:
        return action()
    finally:
        app.extensions["graph"] = graph


def uid(label):
    return points[label].id


MISSING = (400, "MISSING_DATA")
NO_ORIGIN = (404, "ORIGIN_NOT_FOUND")
NO_DESTINATION = (404, "DESTINATION_NOT_FOUND")

expect_value("B1 - falta origin", MISSING, lambda: http("/coverage"))
expect_value("B1 - origin vacío", MISSING, lambda: http("/coverage?origin="))
expect_value("B1 - origin solo espacios", MISSING, lambda: http("/coverage?origin=%20"))
expect_value("B2 - origin con formato inválido", NO_ORIGIN, lambda: http(f"/coverage?origin={NOT_A_UUID}"))
expect_value("B3 - origin no registrado", NO_ORIGIN, lambda: http(f"/coverage?origin={UNKNOWN_UUID}"))
expect_value(
    "B4 - red vacía con origen indicado",
    NO_ORIGIN,
    lambda: on_empty_network(lambda: http(f"/coverage?origin={UNKNOWN_UUID}")),
)
expect_value(
    "B4 - red vacía sin origen",
    MISSING,
    lambda: on_empty_network(lambda: http("/coverage")),
)


def exits_of_casa_a():
    status, _, body = call(f"/coverage?origin={uid('CasaA')}")
    return status, body["reachable"], body["visit_order"]


expect_value(
    "B5 - origen sin salidas: lista vacía y solo el origen en visit_order",
    (200, [], [str(uid("CasaA"))]),
    exits_of_casa_a,
)


def answer(origin, destination):
    status, _, body = call(f"/coverage?origin={uid(origin)}&destination={uid(destination)}")
    return status, body["reachable"], "reason" in body


expect_value("B6 - destino desconectado: 200, no alcanzable y con razón", (200, False, True), lambda: answer("BOD", "CasaD"))
expect_value(
    "B7 - destino con formato inválido",
    NO_DESTINATION,
    lambda: http(f"/coverage?origin={uid('BOD')}&destination={NOT_A_UUID}"),
)
expect_value(
    "B7 - destino no registrado",
    NO_DESTINATION,
    lambda: http(f"/coverage?origin={uid('BOD')}&destination={UNKNOWN_UUID}"),
)
expect_value("B8 - destino igual al origen", (200, True, False), lambda: answer("BOD", "BOD"))
expect_value("B8 - destino igual al origen, sin salidas", (200, True, False), lambda: answer("CasaD", "CasaD"))


def visit_summary():
    status, _, body = call(f"/coverage?origin={uid('BOD')}")
    order = body["visit_order"]
    return status, len(order), len(order) == len(set(order))


expect_value("B9 - ciclo: 15 puntos y ninguno repetido", (200, 15, True), visit_summary)
expect_value("B10 - un sentido: la ida es alcanzable", (200, True, False), lambda: answer("C11K6", "CasaA"))
expect_value("B10 - un sentido: la vuelta no", (200, False, True), lambda: answer("CasaA", "C11K6"))


def empty_destination():
    status, _, body = call(f"/coverage?origin={uid('BOD')}&destination=")
    return status, isinstance(body["reachable"], list), "destination_id" in body


expect_value("B11 - destino vacío se ignora", (200, True, False), empty_destination)
expect_value(
    "B12 - origen y destino no registrados: se informa el origen",
    NO_ORIGIN,
    lambda: http(f"/coverage?origin={UNKNOWN_UUID}&destination={UNKNOWN_UUID}"),
)


def error_shape():
    _, _, body = call("/coverage")
    error = body["error"]
    return sorted(error) == ["code", "message"] and bool(error["message"])


expect_value("Los errores traen code y message", True, error_shape)

section("RESUMEN")
passed = sum(results)
print(f"{passed}/{len(results)} escenarios pasaron")
sys.exit(0 if passed == len(results) else 1)
