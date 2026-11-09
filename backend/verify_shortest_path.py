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

section("RESUMEN")
passed = sum(results)
print(f"{passed}/{len(results)} escenarios pasaron")
sys.exit(0 if passed == len(results) else 1)
