"""Acceptance script for Feature 4 (demonstrable operation) of RutaPyme.

Usage:
    python acceptance/scripts/acceptance_feature_4.py

Expects a freshly started API at http://127.0.0.1:5000, without the seed
network. It reuses the HTTP helpers and the report format of the Feature 3
script. This part covers the normal scenario: a small network with map
positions, its coverage and its shortest path.
"""

from __future__ import annotations

import sys
from decimal import Decimal

from acceptance_feature_3 import (
    create_connection,
    request,
    route_names,
    run_scenario,
    shortest_path,
)


def create_point(name: str, point_type: str, x: float, y: float):
    return request("POST", "/points", {"name": name, "type": point_type, "x": x, "y": y})


def created(response) -> bool:
    return response.status == 201 and isinstance(response.body, dict) and bool(response.body.get("id"))


def main() -> int:
    results: list[bool] = []

    results.append(
        run_scenario(
            "T17 - la API responde",
            "HTTP 200 con status ok",
            lambda: request("GET", "/health"),
            lambda r: r.status == 200 and isinstance(r.body, dict) and r.body.get("status") == "ok",
        )
    )

    # Same demo network as F3: the direct road costs 9 km (1 hop), the way
    # through the two neighborhoods costs 7 km (3 hops).
    warehouse = create_point("Bodega de aceptación", "warehouse", 0, 1)
    north = create_point("Barrio Norte", "neighborhood", 1, 0)
    center = create_point("Barrio Centro", "neighborhood", 2, 1)
    house = create_point("Casa A", "pickup_point", 3, 1)
    isolated = create_point("Casa aislada", "pickup_point", 3, 2)
    point_responses = (warehouse, north, center, house, isolated)
    results.append(
        run_scenario(
            "T17 - registrar la red pequeña: puntos con posición",
            "HTTP 201 para los cinco puntos",
            lambda: point_responses,
            lambda rs: all(created(r) for r in rs),
        )
    )
    if not all(created(r) for r in point_responses):
        print("\nNo se pueden ejecutar los escenarios restantes: la API no creó los puntos base.")
        print("Inicia el backend sin semilla y vuelve a ejecutar el script.")
        return 1

    warehouse_id, north_id, center_id, house_id, isolated_id = (r.body["id"] for r in point_responses)
    connection_responses = (
        create_connection(warehouse_id, house_id, "9"),
        create_connection(warehouse_id, north_id, "3"),
        create_connection(north_id, center_id, "2"),
        create_connection(center_id, house_id, "2"),
    )
    results.append(
        run_scenario(
            "T17 - registrar la red pequeña: conexiones",
            "HTTP 201 para la directa de 9 km y los tramos de 3, 2 y 2 km",
            lambda: connection_responses,
            lambda rs: all(r.status == 201 for r in rs),
        )
    )

    def positions(response) -> dict:
        if not isinstance(response.body, dict):
            return {}
        return {p.get("id"): (p.get("x"), p.get("y")) for p in response.body.get("points", [])}

    results.append(
        run_scenario(
            "T17 - la red trae lo necesario para dibujarla",
            "HTTP 200 con las 5 posiciones x, y y las conexiones de la bodega",
            lambda: request("GET", "/network"),
            lambda r: r.status == 200
            and positions(r)
            == {
                warehouse_id: (0, 1),
                north_id: (1, 0),
                center_id: (2, 1),
                house_id: (3, 1),
                isolated_id: (3, 2),
            }
            and any(
                len(p.get("connections", [])) == 2
                for p in r.body["points"]
                if p.get("id") == warehouse_id
            ),
        )
    )

    coverage = request("GET", f"/coverage?origin={warehouse_id}")
    results.append(
        run_scenario(
            "T17 - cobertura desde la bodega",
            "HTTP 200; alcanza norte, centro y casa, y no la casa aislada",
            lambda: coverage,
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and {p.get("id") for p in r.body.get("reachable", [])} == {north_id, center_id, house_id},
        )
    )

    route = shortest_path(warehouse_id, house_id)
    results.append(
        run_scenario(
            "T17 - ruta de menor costo",
            "HTTP 200, found true, bodega -> norte -> centro -> casa y costo total 7",
            lambda: route,
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and r.body.get("found") is True
            and route_names(r) == ["Bodega de aceptación", "Barrio Norte", "Barrio Centro", "Casa A"]
            and r.body.get("total_cost_km") == "7",
        )
    )
    results.append(
        run_scenario(
            "T17 - menos saltos no es menor costo",
            "La ruta elegida tiene 3 tramos y cuesta menos que la directa de 9 km",
            lambda: route,
            lambda r: isinstance(r.body, dict)
            and len(r.body.get("connections", [])) == 3
            and Decimal(r.body.get("total_cost_km", "0")) < Decimal("9"),
        )
    )

    passed = sum(results)
    print(f"\nRESUMEN: {passed}/{len(results)} escenarios PASARON")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
