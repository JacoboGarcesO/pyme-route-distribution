"""T20: verify the graph core against the T11 example network.

Run from the backend folder: python verify_nucleus.py
"""

import sys
from decimal import Decimal

from domain.errors import (
    CostPrecision,
    DestinationNotFound,
    DuplicateConnection,
    InconsistentCost,
    InvalidCost,
    InvalidName,
    InvalidType,
    MissingData,
    NonPositiveCost,
    OriginNotFound,
    PointNotFound,
    SelfLoop,
)
from domain.graph import Graph

# label, name, type. Street corners use "neighborhood" (T11 leaves their type open).
NODES = [
    ("BOD", "Bodega", "warehouse"),
    ("C10K5", "C10K5", "neighborhood"),
    ("C10K6", "C10K6", "neighborhood"),
    ("C10K7", "C10K7", "neighborhood"),
    ("C10K8", "C10K8", "neighborhood"),
    ("C11K6", "C11K6", "neighborhood"),
    ("C11K7", "C11K7", "neighborhood"),
    ("C11K8", "C11K8", "neighborhood"),
    ("C12K5", "C12K5", "neighborhood"),
    ("C12K6", "C12K6", "neighborhood"),
    ("C12K7", "C12K7", "neighborhood"),
    ("C12K8", "C12K8", "neighborhood"),
    ("CasaA", "Casa A", "pickup_point"),
    ("CasaB", "Casa B", "pickup_point"),
    ("CasaC", "Casa C", "pickup_point"),
]

# origin, destination, km: the 28 directed edges of docs/diseno.md (T11).
EDGES = [
    ("C10K5", "C10K6", "0.4"),
    ("C10K6", "C10K5", "0.4"),
    ("C10K6", "C10K7", "0.5"),
    ("C10K7", "C10K8", "0.3"),
    ("C10K8", "C10K7", "0.3"),
    ("BOD", "C11K6", "0.4"),
    ("C11K6", "BOD", "0.4"),
    ("C11K6", "C11K7", "0.5"),
    ("C11K7", "C11K6", "0.5"),
    ("C11K8", "C11K7", "0.3"),
    ("C12K5", "C12K6", "0.4"),
    ("C12K6", "C12K7", "0.5"),
    ("C12K7", "C12K8", "0.3"),
    ("C10K5", "BOD", "0.3"),
    ("BOD", "C10K5", "0.3"),
    ("BOD", "C12K5", "0.2"),
    ("C12K5", "BOD", "0.2"),
    ("C10K6", "C11K6", "0.3"),
    ("C11K6", "C12K6", "0.2"),
    ("C10K7", "C11K7", "0.3"),
    ("C11K7", "C10K7", "0.3"),
    ("C11K7", "C12K7", "0.3"),
    ("C12K7", "C11K7", "0.3"),
    ("C11K8", "C10K8", "0.2"),
    ("C12K8", "C11K8", "0.3"),
    ("C11K6", "CasaA", "0.1"),
    ("C12K6", "CasaC", "0.1"),
    ("C12K8", "CasaB", "0.1"),
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


def build_t11():
    graph = Graph()
    points = {label: graph.add_point(name, kind) for label, name, kind in NODES}
    ids = {label: str(point.id) for label, point in points.items()}
    for origin, destination, km in EDGES:
        graph.add_connection(ids[origin], ids[destination], km)
    return graph, points, ids


def network_entry(graph, point_id):
    return next(e for e in graph.readable_network() if e["id"] == str(point_id))


def two_points():
    graph = Graph()
    a = graph.add_point("A", "warehouse")
    b = graph.add_point("B", "neighborhood")
    return graph, str(a.id), str(b.id)


def stored_cost(text):
    graph, a, b = two_points()
    return graph.add_connection(a, b, text).to_dict()["cost_km"]


def same_name_points():
    graph = Graph()
    first = graph.add_point("Norte", "neighborhood")
    second = graph.add_point("Norte", "neighborhood")
    return first.id != second.id


# --- block 1: valid scenarios on the T11 network ---------------------------

section("BLOQUE 1 - Red T11 y consultas")
graph, points, ids = build_t11()

expect_value("Red vacia: sin puntos", [], lambda: Graph().list_points())
expect_value("Red vacia: sin conexiones", [], lambda: Graph().list_connections())
expect_value("Red vacia: red legible vacia", [], lambda: Graph().readable_network())
expect_value("T11: 15 puntos", 15, lambda: len(graph.list_points()))
expect_value("T11: 28 conexiones", 28, lambda: len(graph.list_connections()))
expect_value(
    "Puntos en orden estable (por nombre)",
    ["Bodega", "C10K5", "C10K6", "C10K7", "C10K8", "C11K6", "C11K7", "C11K8",
     "C12K5", "C12K6", "C12K7", "C12K8", "Casa A", "Casa B", "Casa C"],
    lambda: [point.name for point in graph.list_points()],
)
expect_value(
    "Vecinos de la bodega (red legible)",
    ["C10K5", "C11K6", "C12K5"],
    lambda: [c["destination_name"] for c in network_entry(graph, ids["BOD"])["connections"]],
)
expect_value(
    "Costo Bodega -> C11K6",
    Decimal("0.4"),
    lambda: graph.neighbors(ids["BOD"])[points["C11K6"].id],
)
expect_value(
    "Sentido unico: existe C10K6 -> C10K7",
    True,
    lambda: points["C10K7"].id in graph.neighbors(ids["C10K6"]),
)
expect_value(
    "Sentido unico: no existe C10K7 -> C10K6",
    False,
    lambda: points["C10K6"].id in graph.neighbors(ids["C10K7"]),
)
expect_value(
    "Una casa destino no tiene conexiones salientes",
    [],
    lambda: network_entry(graph, ids["CasaA"])["connections"],
)
expect_error("Vecinos: UUID con formato invalido", PointNotFound, lambda: graph.neighbors(NOT_A_UUID))
expect_error("Vecinos: punto inexistente", PointNotFound, lambda: graph.neighbors(UNKNOWN_UUID))

# --- block 2: points (P2, P3) ----------------------------------------------

section("BLOQUE 2 - Validaciones al crear puntos")

expect_error("P2 - nombre vacio", InvalidName, lambda: Graph().add_point("", "warehouse"))
expect_error("P2 - nombre solo espacios", InvalidName, lambda: Graph().add_point("   ", "warehouse"))
expect_error("P2 - nombre no es texto", InvalidName, lambda: Graph().add_point(123, "warehouse"))
expect_error("P3 - tipo fuera de la lista", InvalidType, lambda: Graph().add_point("X", "deposito"))
expect_error("P3 - tipo no es texto", InvalidType, lambda: Graph().add_point("X", []))
expect_value("Nombres repetidos reciben UUID distintos", True, same_name_points)
expect_value(
    "El nombre se guarda sin espacios sobrantes",
    "Norte",
    lambda: Graph().add_point("  Norte  ", "neighborhood").name,
)

# --- block 3: connections (C1 to C9) ---------------------------------------

section("BLOQUE 3 - Validaciones al crear conexiones")


def connect(origin, destination, cost):
    return lambda: graph.add_connection(origin, destination, cost)


bod, c10k5, c10k6, c10k7 = ids["BOD"], ids["C10K5"], ids["C10K6"], ids["C10K7"]

expect_error("C1 - falta el origen", MissingData, connect(None, c10k5, "1"))
expect_error("C1 - falta el destino", MissingData, connect(bod, None, "1"))
expect_error("C1 - falta el costo", MissingData, connect(bod, c10k5, None))
expect_error("C2 - UUID de origen con formato invalido", OriginNotFound, connect(NOT_A_UUID, c10k5, "1"))
expect_error("C2 - origen inexistente", OriginNotFound, connect(UNKNOWN_UUID, c10k5, "1"))
expect_error("C3 - UUID de destino con formato invalido", DestinationNotFound, connect(bod, NOT_A_UUID, "1"))
expect_error("C3 - destino inexistente", DestinationNotFound, connect(bod, UNKNOWN_UUID, "1"))
expect_error("C4 - auto-lazo", SelfLoop, connect(bod, bod, "1"))
expect_error("C5 - costo como numero JSON", InvalidCost, connect(bod, c10k5, 4.5))
expect_error("C5 - costo con letras", InvalidCost, connect(bod, c10k5, "cuatro"))
expect_error("C5 - costo vacio", InvalidCost, connect(bod, c10k5, ""))
expect_error("C5 - costo infinito", InvalidCost, connect(bod, c10k5, "Infinity"))
expect_error("C5 - costo NaN", InvalidCost, connect(bod, c10k5, "NaN"))
expect_error("C5 - notacion cientifica", InvalidCost, connect(bod, c10k5, "1e999999999"))
expect_error("C5 - guion bajo en el numero", InvalidCost, connect(bod, c10k5, "1_0"))
expect_error("C6 - costo cero", NonPositiveCost, connect(bod, c10k5, "0"))
expect_error("C6 - costo negativo", NonPositiveCost, connect(bod, c10k5, "-1.5"))
expect_error("C7 - mas de 7 decimales", CostPrecision, connect(bod, c10k5, "0.12345678"))
expect_error("Orden: C2 antes que el costo", OriginNotFound, connect(NOT_A_UUID, c10k5, "cuatro"))
expect_error("Orden: C4 antes que el costo", SelfLoop, connect(bod, bod, "cuatro"))
expect_error("C8 - duplicada (mismo sentido y costo)", DuplicateConnection, connect(bod, ids["C11K6"], "0.4"))
expect_error("C8 - duplicada aunque cambie el costo", DuplicateConnection, connect(bod, ids["C11K6"], "0.9"))
expect_error("C9 - inversa con costo distinto", InconsistentCost, connect(c10k7, c10k6, "9.9"))
expect_value(
    "C9 - inversa con el mismo costo se acepta",
    Decimal("0.5"),
    lambda: graph.add_connection(c10k7, c10k6, "0.5").cost_km,
)
expect_value(
    "Los rechazos no modificaron la red (28 + 1 aceptada)",
    29,
    lambda: len(graph.list_connections()),
)
expect_value("Costo con 7 decimales se acepta", "0.1234567", lambda: stored_cost("0.1234567"))
expect_value("Costo muy pequeno sale en notacion fija", "0.0000001", lambda: stored_cost("0.0000001"))
expect_value("Costo entero", "3", lambda: stored_cost("3"))

section("RESUMEN")
passed = sum(results)
print(f"{passed}/{len(results)} escenarios pasaron")
sys.exit(0 if passed == len(results) else 1)
