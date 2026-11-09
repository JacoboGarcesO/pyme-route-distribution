"""T13-T14: verifica la ruta de menor costo contra los casos borde de docs/diseno.md (T08).

Ejecutar desde la carpeta backend: python verify_shortest_path.py
"""

import sys
from decimal import Decimal

from domain.errors import DestinationNotFound, OriginNotFound
from domain.graph import Graph
from domain.shortest_path import shortest_path

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
        report(scenario, error_type.__name__, f"{type(exc).__name__}: {exc}", type(exc) is error_type)
        return
    report(scenario, error_type.__name__, "no hubo error", False)


def section(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def build(names, edges, kind="neighborhood"):
    """Red de prueba: puntos por nombre y conexiones (origen, destino, km)."""
    graph = Graph()
    points = {name: graph.add_point(name, kind) for name in names}
    for origin, destination, cost in edges:
        graph.add_connection(str(points[origin].id), str(points[destination].id), cost)
    return graph, points


def route(graph, points, origin, destination):
    """(nombres de la ruta, costo) o (found=False)."""
    result = shortest_path(graph, points[origin].id, points[destination].id)
    return [p.name for p in result.path], result.to_dict()["total_cost_km"]


# --- T13: precisión y costos acumulados ---------------------------------------

section("BLOQUE 1 - Precisión Decimal y costos acumulados (T13)")

graph, pts = build("ABC", [("A", "B", "0.1"), ("B", "C", "0.2")])
result = shortest_path(graph, pts["A"].id, pts["C"].id)
expect_value("R11 - 0.1 + 0.2 suma exacta", Decimal("0.3"), lambda: result.total_cost)
expect_value("R11 - serializado como texto exacto", "0.3", lambda: result.to_dict()["total_cost_km"])
expect_value("El costo es Decimal, no float", True, lambda: isinstance(result.total_cost, Decimal))

graph, pts = build("AB", [("A", "B", "0.0000001")])
expect_value("Costo mínimo de 7 decimales se conserva", "0.0000001", lambda: route(graph, pts, "A", "B")[1])

graph, pts = build("ABC", [("A", "B", "1000000.1234567"), ("B", "C", "0.0000003")])
expect_value("Suma sin pérdida de precisión con valores grandes", "1000000.1234570", lambda: route(graph, pts, "A", "C")[1])

graph, pts = build("ABC", [("A", "B", "2.5"), ("B", "C", "1.25")])
expect_value(
    "La suma de los tramos recorridos es el costo total",
    True,
    lambda: (
        lambda r: sum(c.cost_km for c in r.connections) == r.total_cost
    )(shortest_path(graph, pts["A"].id, pts["C"].id)),
)
expect_value(
    "Cada tramo conserva su costo en la respuesta",
    ["2.5", "1.25"],
    lambda: [c["cost_km"] for c in shortest_path(graph, pts["A"].id, pts["C"].id).to_dict()["connections"]],
)

# --- T14: caso normal y casos borde de T08 -----------------------------------

section("BLOQUE 2 - Caso normal: menos saltos no es menor costo (R10)")

# A->D directo cuesta 9 (1 salto); A->B->C->D cuesta 7 (3 saltos).
demo, d = build("ABCD", [("A", "D", "9"), ("A", "B", "3"), ("B", "C", "2"), ("C", "D", "2")])
expect_value("R10 - elige la ruta de 3 saltos y 7 km", (["A", "B", "C", "D"], "7"), lambda: route(demo, d, "A", "D"))

section("BLOQUE 3 - Validación de origen y destino (R2, R3, R4, R5)")

a_id, ghost = d["A"].id, UNKNOWN_UUID
expect_error("R2 - origen con formato inválido", OriginNotFound, lambda: shortest_path(demo, NOT_A_UUID, a_id))
expect_error("R2 - origen UUID válido no registrado", OriginNotFound, lambda: shortest_path(demo, ghost, a_id))
expect_error("R3 - destino con formato inválido", DestinationNotFound, lambda: shortest_path(demo, a_id, NOT_A_UUID))
expect_error("R3 - destino UUID válido no registrado", DestinationNotFound, lambda: shortest_path(demo, a_id, ghost))
expect_error("R4 - red vacía: el origen no existe", OriginNotFound, lambda: shortest_path(Graph(), ghost, ghost))
expect_error("R5 - ambos inexistentes: se informa el origen", OriginNotFound, lambda: shortest_path(demo, ghost, ghost))

section("BLOQUE 4 - Origen igual al destino y ruta inexistente (R6, R7, R8)")

expect_value("R6 - origen igual al destino: un punto y costo 0", (["A"], "0"), lambda: route(demo, d, "A", "A"))
expect_value(
    "R6 - sin conexiones recorridas",
    [],
    lambda: shortest_path(demo, a_id, a_id).to_dict()["connections"],
)


def no_route(graph, points, origin, destination):
    r = shortest_path(graph, points[origin].id, points[destination].id).to_dict()
    return r["found"], r["path"], r["total_cost_km"], "reason" in r


expect_value("R7 - sentido contrario de una calle de un solo sentido", (False, [], None, True), lambda: no_route(demo, d, "D", "A"))
iso, i = build("ABZ", [("A", "B", "1")])
expect_value("R7 - destino aislado", (False, [], None, True), lambda: no_route(iso, i, "A", "Z"))
expect_value("R8 - origen aislado", (False, [], None, True), lambda: no_route(iso, i, "Z", "A"))
expect_value(
    "R7 - el mensaje nombra origen y destino",
    "No hay un camino dirigido desde 'Z' hasta 'A'.",
    lambda: shortest_path(iso, i["Z"].id, i["A"].id).reason,
)

section("BLOQUE 5 - Ciclos y empates (R9, R12)")

cyc, c = build("ABCD", [("A", "B", "1"), ("B", "A", "1"), ("B", "C", "1"), ("C", "B", "1"), ("C", "D", "1")])
expect_value("R9 - ciclos A<->B<->C: termina y da 3 km", (["A", "B", "C", "D"], "3"), lambda: route(cyc, c, "A", "D"))
tie, t = build("ABCD", [("A", "C", "1"), ("A", "B", "1"), ("B", "D", "1"), ("C", "D", "1")])
expect_value("R12 - empate: costo 2 y ruta estable por nombre", (["A", "B", "D"], "2"), lambda: route(tie, t, "A", "D"))
expect_value("R12 - el mismo empate da siempre la misma ruta", True, lambda: all(route(tie, t, "A", "D") == route(tie, t, "A", "D") for _ in range(5)))

section("RESUMEN")
passed = sum(results)
print(f"{passed}/{len(results)} escenarios pasaron")
sys.exit(0 if passed == len(results) else 1)
