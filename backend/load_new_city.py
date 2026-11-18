"""Loads the extended RutaPyme city: 62 corners, 2 warehouses, 24 addresses and a closed house.

It changes no project code: it registers the city through the REST API (POST /points and
POST /connections), so the backend must be running WITHOUT SEED_NETWORK and with no points.

    python backend/load_new_city.py            load the city into http://127.0.0.1:5000
    python backend/load_new_city.py --check    only validate the data and print the summary
"""

import json
import sys
import urllib.error
import urllib.request
from collections import deque
from decimal import Decimal

BASE_URL = "http://127.0.0.1:5000"
INCLUDE_ISOLATED = True

# Direction of each street: "both", "+" (towards the higher Carrera number) or "-".
# For the carreras, "+" goes towards the higher Calle number.
CALLES = {10: "both", 11: "+", 12: "-", 13: "both", 14: "+", 15: "-", 16: "+", 17: "both"}
CARRERAS = {5: "both", 6: "-", 7: "both", 8: "+", 9: "-", 10: "both", 11: "+", 12: "both"}

# Kilometers of each block (7 per street). The fourth block of the calles and of the carreras is
# long on purpose (a park and a canal), so that fewer legs is sometimes NOT the cheapest route.
CALLE_COSTS = ["0.12", "0.10", "0.28", "0.11", "0.13", "0.10", "0.12"]
CARRERA_COSTS = ["0.09", "0.11", "0.10", "0.26", "0.09", "0.11", "0.10"]

ACCESS_KM = "0.04"  # from the corner to the door; leaving costs the whole block, so it is never a shortcut

# Each warehouse takes one corner of the grid, on opposite sides of the city.
WAREHOUSES = {(0, 3): "Bodega central", (7, 5): "Bodega oriente"}

# (name, kind, (calle or carrera, street number, block 0..6[, way when the street is two-way]))
ADDRESSES = [
    ("Edificio Torre Alameda", "building", ("calle", 13, 2)),
    ("Edificio Altos del Parque", "building", ("calle", 13, 5, "-")),
    ("Edificio Mirador 14", "building", ("carrera", 7, 1)),
    ("Edificio Santa Clara", "building", ("carrera", 7, 5, "-")),
    ("Edificio Plaza Central", "building", ("carrera", 10, 2)),
    ("Edificio Los Almendros", "building", ("carrera", 10, 4, "-")),
    ("Casa Gómez", "house", ("calle", 11, 1)),
    ("Casa Rojas", "house", ("calle", 12, 2)),
    ("Casa Pérez", "house", ("calle", 14, 0)),
    ("Casa Martínez", "house", ("calle", 15, 3)),
    ("Casa Londoño", "house", ("calle", 16, 5)),
    ("Casa Ospina", "house", ("carrera", 6, 2)),
    ("Casa Restrepo", "house", ("carrera", 8, 0)),
    ("Casa Castaño", "house", ("carrera", 9, 6)),
    ("Casa Mejía", "house", ("carrera", 11, 1)),
    ("Casa Vélez", "house", ("calle", 11, 5)),
    ("Casa Cardona", "house", ("calle", 14, 6)),
    ("Casa Zapata", "house", ("carrera", 8, 5)),
    ("Tienda La Esquina", "store", ("calle", 12, 1)),
    ("Tienda Doña Rosa", "store", ("calle", 15, 0)),
    ("Tienda El Vecino", "store", ("carrera", 9, 1)),
    ("Tienda Don Pepe", "store", ("carrera", 11, 5)),
    ("Tienda La Económica", "store", ("calle", 16, 3)),
    ("Tienda Buen Precio", "store", ("carrera", 6, 5)),
]
ISOLATED = ("Casa Finca El Mirlo (vía cerrada)", 6.45, 6.45)  # no connection in or out, on purpose


def corner_name(x, y):
    return WAREHOUSES.get((x, y)) or f"Calle {10 + y} con Carrera {5 + x}"


def build():
    """Return (points, connections, details). A point is (name, type, x, y)."""
    points = []
    for y in range(8):
        for x in range(8):
            point_type = "warehouse" if (x, y) in WAREHOUSES else "neighborhood"
            points.append((corner_name(x, y), point_type, x, y))

    connections = []

    def street(a, b, way, km):
        if way in ("both", "+"):
            connections.append((corner_name(*a), corner_name(*b), km))
        if way in ("both", "-"):
            connections.append((corner_name(*b), corner_name(*a), km))

    for y in range(8):
        for x in range(7):
            street((x, y), (x + 1, y), CALLES[10 + y], CALLE_COSTS[x])
    for x in range(8):
        for y in range(7):
            street((x, y), (x, y + 1), CARRERAS[5 + x], CARRERA_COSTS[y])

    existing = {(origin, destination) for origin, destination, _ in connections}
    details = []
    for name, kind, (street_kind, number, block, *way) in ADDRESSES:
        if street_kind == "calle":
            y = number - 10
            a, b = (block, y), (block + 1, y)
            rule, km = CALLES[number], CALLE_COSTS[block]
        else:
            x = number - 5
            a, b = (x, block), (x, block + 1)
            rule, km = CARRERAS[number], CARRERA_COSTS[block]
        order = rule if rule != "both" else (way[0] if way else "+")
        if order == "-":
            a, b = b, a
        side = 1 if (a[1] if street_kind == "calle" else a[0]) < 3.5 else -1
        if street_kind == "calle":
            px, py = a[0] + 0.3 * (b[0] - a[0]), a[1] + side * 0.3
        else:
            px, py = a[0] + side * 0.3, a[1] + 0.3 * (b[1] - a[1])
        points.append((name, "pickup_point", round(px, 2), round(py, 2)))
        assert (corner_name(*a), corner_name(*b)) in existing, f"{name}: the street does not go from {a} to {b}"
        connections.append((corner_name(*a), name, ACCESS_KM))
        connections.append((name, corner_name(*b), km))
        details.append((name, kind, corner_name(*a), corner_name(*b)))
    if INCLUDE_ISOLATED:
        points.append((ISOLATED[0], "pickup_point", ISOLATED[1], ISOLATED[2]))
    return points, connections, details


def reaches_all(start, edges, names):
    seen = {start}
    queue = deque([start])
    while queue:
        for neighbor in edges[queue.popleft()]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == set(names)


def check(points, connections, details):
    names = [point[0] for point in points]
    assert len(names) == len(set(names)), "duplicate names"
    pairs = [(origin, destination) for origin, destination, _ in connections]
    assert len(pairs) == len(set(pairs)), "duplicate connections"
    assert all(origin != destination for origin, destination in pairs), "self loops"
    cost = {(origin, destination): Decimal(km) for origin, destination, km in connections}
    for (origin, destination), km in cost.items():
        assert km > 0 and -km.as_tuple().exponent <= 7, f"invalid cost {origin} -> {destination}"
        if (destination, origin) in cost:
            assert cost[(destination, origin)] == km, f"different costs in both directions: {origin} <-> {destination}"

    position = {point[0]: (point[2], point[3]) for point in points}
    address_names = {detail[0] for detail in details} | {ISOLATED[0]}
    placed = [name for name in names if name in address_names]
    too_close = [
        (a, b)
        for i, a in enumerate(placed)
        for b in placed[i + 1 :]
        if ((position[a][0] - position[b][0]) ** 2 + (position[a][1] - position[b][1]) ** 2) ** 0.5 < 0.4
    ]
    assert not too_close, f"addresses drawn on top of each other: {too_close}"

    connected = [name for name in names if name != ISOLATED[0]]
    outgoing = {name: [] for name in names}
    incoming = {name: [] for name in names}
    for origin, destination, _ in connections:
        outgoing[origin].append(destination)
        incoming[destination].append(origin)
    assert reaches_all(connected[0], outgoing, connected), "the city is not strongly connected"
    assert reaches_all(connected[0], incoming, connected), "the city is not strongly connected"


def summary(points, connections, details):
    kinds = {}
    for _, kind, _, _ in details:
        kinds[kind] = kinds.get(kind, 0) + 1
    print(f"Puntos: {len(points)} | conexiones: {len(connections)}")
    print(f"Esquinas: {64 - len(WAREHOUSES)} | bodegas: {len(WAREHOUSES)} | direcciones: {kinds} | aislada: {'si' if INCLUDE_ISOLATED else 'no'}")
    print("Comprobado: sin nombres ni conexiones repetidas, sin auto-lazos, costos positivos e iguales")
    print("en ambos sentidos, direcciones separadas y toda la red conectada entre si.")


def call_api(method, path, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    request = urllib.request.Request(BASE_URL + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def load(points, connections):
    status, body = call_api("GET", "/points")
    if status != 200:
        sys.exit("No se pudo consultar el backend en " + BASE_URL)
    if body["points"]:
        sys.exit("El backend ya tiene puntos. Reinicialo SIN SEED_NETWORK y vuelve a ejecutar.")
    ids = {}
    for name, point_type, x, y in points:
        status, body = call_api("POST", "/points", {"name": name, "type": point_type, "x": x, "y": y})
        if status != 201:
            sys.exit(f"Fallo al crear '{name}': {status} {body}")
        ids[name] = body["id"]
    for origin, destination, km in connections:
        status, body = call_api(
            "POST", "/connections", {"origin_id": ids[origin], "destination_id": ids[destination], "cost_km": km}
        )
        if status != 201:
            sys.exit(f"Fallo {origin} -> {destination}: {status} {body}")
    print(f"Ciudad cargada: {len(ids)} puntos y {len(connections)} conexiones en {BASE_URL}")


if __name__ == "__main__":
    points, connections, details = build()
    check(points, connections, details)
    summary(points, connections, details)
    if "--check" not in sys.argv:
        load(points, connections)
