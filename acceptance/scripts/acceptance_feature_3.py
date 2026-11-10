"""Acceptance script for Feature 3 (shortest path) of RutaPyme.

Usage:
    python acceptance/scripts/acceptance_feature_3.py

The script uses only Python's standard library and expects a freshly started
API at http://127.0.0.1:5000, without the seed network. It creates its own
small directed network so that the scenarios are repeatable and do not depend
on seeded UUIDs.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:5000"
UNKNOWN_UUID = "00000000-0000-0000-0000-000000000000"


@dataclass
class Response:
    status: int | None
    body: object
    error: str | None = None


def parse_body(raw_body: str) -> object:
    if not raw_body:
        return None
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body


def request(method: str, path: str, payload: object | None = None) -> Response:
    """Call the API and normalize successful and HTTP error responses."""
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request_object = Request(
        f"{BASE_URL}{path}", data=data, headers=headers, method=method
    )
    try:
        with urlopen(request_object, timeout=5) as response:
            return Response(response.status, parse_body(response.read().decode()))
    except HTTPError as error:
        return Response(error.code, parse_body(error.read().decode()), str(error))
    except (URLError, TimeoutError) as error:
        return Response(None, None, str(error))


def create_point(name: str, point_type: str) -> Response:
    return request("POST", "/points", {"name": name, "type": point_type})


def create_connection(origin_id: str, destination_id: str, cost_km: str) -> Response:
    return request(
        "POST",
        "/connections",
        {"origin_id": origin_id, "destination_id": destination_id, "cost_km": cost_km},
    )


def shortest_path(origin: str | None, destination: str | None) -> Response:
    """GET /shortest-path; a parameter set to None is not sent."""
    query = {}
    if origin is not None:
        query["origin"] = origin
    if destination is not None:
        query["destination"] = destination
    suffix = f"?{urlencode(query)}" if query else ""
    return request("GET", f"/shortest-path{suffix}")


def run_scenario(name: str, expected: str, operation, check) -> bool:
    print(f"\nESCENARIO: {name}")
    print(f"ESPERABA: {expected}")
    try:
        result = operation()
        passed = check(result)
        print(f"OBTUVE: {result}")
    except Exception as error:  # Keep the acceptance report running.
        passed = False
        print(f"OBTUVE: excepción inesperada: {error}")
    print("RESULTADO: PASÓ" if passed else "RESULTADO: FALLÓ")
    return passed


def error_code(response: Response) -> str | None:
    if isinstance(response.body, dict):
        error = response.body.get("error", {})
        if isinstance(error, dict):
            return error.get("code")
    return None


def has_error(response: Response, status: int, code: str) -> bool:
    return response.status == status and error_code(response) == code


def route_names(response: Response) -> list[str]:
    """Names of the points of the route, origin first."""
    if not isinstance(response.body, dict):
        return []
    return [point.get("name") for point in response.body.get("path", [])]


def main() -> int:
    results: list[bool] = []

    results.append(
        run_scenario(
            "T23 - la API responde",
            "HTTP 200 con status ok",
            lambda: request("GET", "/health"),
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and r.body.get("status") == "ok",
        )
    )

    # Demonstration network: Bodega -> Casa A directly costs 9 km (1 hop), while
    # Bodega -> Barrio Norte -> Barrio Centro -> Casa A costs 7 km (3 hops).
    warehouse = create_point("Bodega de aceptación", "warehouse")
    north = create_point("Barrio Norte", "neighborhood")
    center = create_point("Barrio Centro", "neighborhood")
    house = create_point("Casa A", "pickup_point")
    point_responses = (warehouse, north, center, house)
    results.append(
        run_scenario(
            "T24 - preparar la red de demostración: puntos",
            "HTTP 201 para la bodega, los dos barrios y la casa",
            lambda: point_responses,
            lambda rs: all(r.status == 201 and isinstance(r.body, dict) and r.body.get("id") for r in rs),
        )
    )

    if not all(
        r.status == 201 and isinstance(r.body, dict) and r.body.get("id")
        for r in point_responses
    ):
        print("\nNo se pueden ejecutar los escenarios restantes: la API no creó los puntos base.")
        print("Inicia el backend y vuelve a ejecutar el script.")
        return 1

    warehouse_id = warehouse.body["id"]
    north_id = north.body["id"]
    center_id = center.body["id"]
    house_id = house.body["id"]
    connection_responses = (
        create_connection(warehouse_id, house_id, "9"),
        create_connection(warehouse_id, north_id, "3"),
        create_connection(north_id, center_id, "2"),
        create_connection(center_id, house_id, "2"),
    )
    results.append(
        run_scenario(
            "T24 - preparar la red de demostración: conexiones",
            "HTTP 201 para la ruta directa de 9 km y para los tres tramos de 3, 2 y 2 km",
            lambda: connection_responses,
            lambda rs: all(r.status == 201 for r in rs),
        )
    )

    results.append(
        run_scenario(
            "T24 - existe la ruta directa de 1 salto y 9 km",
            "HTTP 200 y la conexión bodega -> casa de 9 km en la lista",
            lambda: request("GET", "/connections"),
            lambda r: r.status == 200
            and any(
                c.get("origin_id") == warehouse_id
                and c.get("destination_id") == house_id
                and c.get("cost_km") == "9"
                for c in r.body.get("connections", [])
            ),
        )
    )

    expected_names = ["Bodega de aceptación", "Barrio Norte", "Barrio Centro", "Casa A"]
    route = shortest_path(warehouse_id, house_id)
    results.append(
        run_scenario(
            "T24 - ruta normal de menor costo",
            "HTTP 200, found true, ruta bodega -> norte -> centro -> casa y costo total 7",
            lambda: route,
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and r.body.get("found") is True
            and route_names(r) == expected_names
            and r.body.get("total_cost_km") == "7",
        )
    )
    results.append(
        run_scenario(
            "T24 - menos saltos no es menor costo",
            "La ruta elegida tiene 3 tramos y cuesta menos que la directa de 1 tramo y 9 km",
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
