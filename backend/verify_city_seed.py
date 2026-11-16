"""Verificación de la semilla ampliada de F4 (ciudad WareTrack del mapa 3D).

Comprueba que ampliar la ciudad no cambia ninguna ruta de menor costo entre
los 16 puntos del mapa de F1, y que cada cliente nuevo es alcanzable desde la
bodega. Ejecutar desde backend/: python verify_city_seed.py
"""

from domain.graph import Graph
from domain.shortest_path import shortest_path
from seed import CITY_HOUSES, HOUSE_EXITS, POINTS, seed_network

results = []


def expect(name, expected, obtained):
    ok = expected == obtained
    results.append(ok)
    print(f"{'PASÓ ' if ok else 'FALLÓ'} | {name} | esperado: {expected} | obtenido: {obtained}")


def summary(graph, points, a, b):
    result = shortest_path(graph, str(points[a].id), str(points[b].id))
    if not result.found:
        return None
    return [p.name for p in result.path], result.total_cost


base_graph, city_graph = Graph(), Graph()
base = seed_network(base_graph)
city = seed_network(city_graph, city=True)

expect("Puntos de la ciudad", 60, len(city_graph.list_points()))
expect("La red de F1 sigue intacta", 16, len(base_graph.list_points()))

labels = [label for label, *_ in POINTS]
# Las rutas que ya existían no cambian. Las que no existían pueden aparecer en la
# ciudad: ahí las casas tienen salida para poder ser parada.
changed = [
    (a, b)
    for a in labels
    for b in labels
    if summary(base_graph, base, a, b) is not None
    and summary(base_graph, base, a, b) != summary(city_graph, city, a, b)
]
expect(f"Rutas existentes entre los {len(labels)} puntos de F1 sin cambios", [], changed)

# Cada cliente con salida sirve de parada entre la bodega y la esquina más lejana.
for label, *_ in HOUSE_EXITS:
    via = shortest_path(city_graph, str(city["BOD"].id), str(city["C16K11"].id), str(city[label].id))
    expect(f"{label} puede ser parada", True, via.found)

for label, *_ in CITY_HOUSES:
    expect(f"Bodega alcanza {label}", True, summary(city_graph, city, "BOD", label) is not None)

print(f"\n{sum(results)} de {len(results)} verificaciones pasaron")
raise SystemExit(0 if all(results) else 1)
