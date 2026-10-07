"""Seed network: the sample map of docs/mapa_calles_carreras_rutapyme.png (T11).

15 points (the warehouse, 11 street corners and 3 destination houses) and the
28 directed connections of the map, with distances in km. Two-way streets are
two connections with the same cost (docs/diseno.md, rule 3); one-way streets
are a single connection.

The seed is optional: app.py loads it only when SEED_NETWORK=1, so the
acceptance script keeps starting from an empty network.
"""

# label, name, type, x, y. Corners use "neighborhood" (T11 leaves their type open).
# x and y place each point on the drawn map: x grows with the Carrera (5 -> 0 ... 8 -> 3)
# and y with the Calle (10 -> 0 ... 12 -> 2). The houses sit inside their block.
POINTS = [
    ("BOD", "Bodega central", "warehouse", 0, 1),
    ("C10K5", "Calle 10 con Carrera 5", "neighborhood", 0, 0),
    ("C10K6", "Calle 10 con Carrera 6", "neighborhood", 1, 0),
    ("C10K7", "Calle 10 con Carrera 7", "neighborhood", 2, 0),
    ("C10K8", "Calle 10 con Carrera 8", "neighborhood", 3, 0),
    ("C11K6", "Calle 11 con Carrera 6", "neighborhood", 1, 1),
    ("C11K7", "Calle 11 con Carrera 7", "neighborhood", 2, 1),
    ("C11K8", "Calle 11 con Carrera 8", "neighborhood", 3, 1),
    ("C12K5", "Calle 12 con Carrera 5", "neighborhood", 0, 2),
    ("C12K6", "Calle 12 con Carrera 6", "neighborhood", 1, 2),
    ("C12K7", "Calle 12 con Carrera 7", "neighborhood", 2, 2),
    ("C12K8", "Calle 12 con Carrera 8", "neighborhood", 3, 2),
    ("CasaA", "Casa A", "pickup_point", 1.3, 0.7),
    ("CasaB", "Casa B", "pickup_point", 2.7, 1.7),
    ("CasaC", "Casa C", "pickup_point", 0.7, 1.7),
]

# origin label, destination label, km. The warehouse sits on Calle 11 with Carrera 5.
CONNECTIONS = [
    # Calle 10: two-way, except Carrera 6 -> Carrera 7 (one-way east)
    ("C10K5", "C10K6", "0.4"),
    ("C10K6", "C10K5", "0.4"),
    ("C10K6", "C10K7", "0.5"),
    ("C10K7", "C10K8", "0.3"),
    ("C10K8", "C10K7", "0.3"),
    # Calle 11: two-way, except Carrera 8 -> Carrera 7 (one-way west)
    ("BOD", "C11K6", "0.4"),
    ("C11K6", "BOD", "0.4"),
    ("C11K6", "C11K7", "0.5"),
    ("C11K7", "C11K6", "0.5"),
    ("C11K8", "C11K7", "0.3"),
    # Calle 12: one-way east
    ("C12K5", "C12K6", "0.4"),
    ("C12K6", "C12K7", "0.5"),
    ("C12K7", "C12K8", "0.3"),
    # Carrera 5: two-way
    ("C10K5", "BOD", "0.3"),
    ("BOD", "C10K5", "0.3"),
    ("BOD", "C12K5", "0.2"),
    ("C12K5", "BOD", "0.2"),
    # Carrera 6: one-way south
    ("C10K6", "C11K6", "0.3"),
    ("C11K6", "C12K6", "0.2"),
    # Carrera 7: two-way
    ("C10K7", "C11K7", "0.3"),
    ("C11K7", "C10K7", "0.3"),
    ("C11K7", "C12K7", "0.3"),
    ("C12K7", "C11K7", "0.3"),
    # Carrera 8: one-way north
    ("C11K8", "C10K8", "0.2"),
    ("C12K8", "C11K8", "0.3"),
    # Access from a corner to each destination house
    ("C11K6", "CasaA", "0.1"),
    ("C12K6", "CasaC", "0.1"),
    ("C12K8", "CasaB", "0.1"),
]


def seed_network(graph):
    """Load the sample map into an empty graph and return {label: Point}."""
    if graph.list_points():
        raise RuntimeError("The seed needs an empty graph.")
    points = {
        label: graph.add_point(name, type_, x, y) for label, name, type_, x, y in POINTS
    }
    for origin, destination, cost_km in CONNECTIONS:
        graph.add_connection(points[origin].id, points[destination].id, cost_km)
    return points
