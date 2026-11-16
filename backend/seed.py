"""Seed network: the sample map of docs/mapa_calles_carreras_rutapyme.png (T11).

16 points (the warehouse, 11 street corners, 3 destination houses and the
isolated Casa D) and the 28 directed connections of the map, with distances in km. Two-way streets are
two connections with the same cost (docs/diseno.md, rule 3); one-way streets
are a single connection.

The seed is optional: app.py loads it only when SEED_NETWORK=1, so the
acceptance script keeps starting from an empty network. app.py also loads the
larger WareTrack city of F4 (city_extension: 60 points), which keeps every F1
route unchanged (verify_city_seed.py); the verify_* scripts use the F1 map only.
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
    # Isolated on purpose: no connection in or out, so nothing reaches it (F2, T07).
    ("CasaD", "Casa D", "pickup_point", 2.3, 0.7),
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


# F4 (WareTrack, mapa 3D): the city grows to Calles 10-16 and Carreras 5-11.
# Only streets that touch the new area are added, so the F1 map above keeps its
# connections and its shortest routes (checked by verify_city_seed.py).
# Direction of each street: "both", "+" (towards the higher number) or "-".
CALLES = {10: "both", 11: "both", 12: "+", 13: "-", 14: "both", 15: "+", 16: "both"}
# Carreras 6 and 9 go north in the new blocks: southwards they would open shortcuts
# between F1 points (Carrera 6 in F1 keeps going south).
CARRERAS = {5: "both", 6: "-", 7: "both", 8: "-", 9: "-", 10: "both", 11: "+"}
CALLE_COSTS = ["0.4", "0.5", "0.3", "0.4", "0.5", "0.4"]  # by block, west to east
CARRERA_COSTS = ["0.3", "0.2", "0.3", "0.2", "0.3", "0.2"]  # by block, north to south
CITY_HOUSES = [
    ("CasaE", "Casa E", 4.3, 0.7, "C11K9"),
    ("CasaF", "Casa F", 5.7, 2.3, "C12K11"),
    ("CasaG", "Casa G", 1.3, 3.7, "C14K6"),
    ("CasaH", "Casa H", 2.7, 4.3, "C14K8"),
    ("CasaI", "Casa I", 4.7, 5.3, "C15K10"),
    ("CasaJ", "Casa J", 0.7, 5.7, "C16K5"),
    ("CasaK", "Casa K", 5.3, 3.7, "C14K10"),
]


def _corner(x, y):
    calle, carrera = 10 + y, 5 + x
    return "BOD" if (x, y) == (0, 1) else f"C{calle}K{carrera}"


def city_extension():
    """Points and connections that turn the F1 map into the 7x7 city."""
    base = {(x, y) for _, _, _, x, y in POINTS[:12]}  # BOD and the 11 F1 corners
    points = [
        (_corner(x, y), f"Calle {10 + y} con Carrera {5 + x}", "neighborhood", x, y)
        for y in range(7)
        for x in range(7)
        if (x, y) not in base
    ]
    points += [(label, name, "pickup_point", x, y) for label, name, x, y, _ in CITY_HOUSES]

    connections = []

    def street(a, b, way, cost):
        if a in base and b in base:
            return  # the F1 map already defines it
        if way in ("both", "+"):
            connections.append((_corner(*a), _corner(*b), cost))
        if way in ("both", "-"):
            connections.append((_corner(*b), _corner(*a), cost))

    for y in range(7):
        for x in range(6):
            street((x, y), (x + 1, y), CALLES[10 + y], CALLE_COSTS[x])
    for x in range(7):
        for y in range(6):
            street((x, y), (x, y + 1), CARRERAS[5 + x], CARRERA_COSTS[y])
    connections += [(corner, label, "0.1") for label, _, _, _, corner in CITY_HOUSES]
    return points, connections


def seed_network(graph, city=False):
    """Load the sample map into an empty graph and return {label: Point}.

    With city=True it also loads the larger WareTrack city (F4).
    """
    if graph.list_points():
        raise RuntimeError("The seed needs an empty graph.")
    point_rows, connection_rows = list(POINTS), list(CONNECTIONS)
    if city:
        extra_points, extra_connections = city_extension()
        point_rows += extra_points
        connection_rows += extra_connections
    points = {
        label: graph.add_point(name, type_, x, y) for label, name, type_, x, y in point_rows
    }
    for origin, destination, cost_km in connection_rows:
        graph.add_connection(points[origin].id, points[destination].id, cost_km)
    return points
