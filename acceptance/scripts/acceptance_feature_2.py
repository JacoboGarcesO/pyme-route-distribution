"""Acceptance script for Feature 2 (coverage) of RutaPyme.

Usage:
    python acceptance/scripts/acceptance_feature_2.py

The script uses only Python's standard library and expects a freshly started
API at http://127.0.0.1:5000. It creates its own small directed network so
that the scenarios are repeatable and do not depend on seeded UUIDs.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:5000"


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
        return Response(
            error.code, parse_body(error.read().decode()), str(error)
        )
    except (URLError, TimeoutError) as error:
        return Response(None, None, str(error))


def coverage(origin: str | None, destination: str | None = None) -> Response:
    query = {}
    if origin is not None:
        query["origin"] = origin
    if destination is not None:
        query["destination"] = destination
    suffix = f"?{urlencode(query)}" if query else ""
    return request("GET", f"/coverage{suffix}")


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


def contains_point(body: object, point_id: str) -> bool:
    """Accept either the compact ID list or the API's point-object list."""
    if not isinstance(body, dict):
        return False
    reachable = body.get("reachable", [])
    return any(
        item == point_id
        or (isinstance(item, dict) and item.get("id") == point_id)
        for item in reachable
    )


def main() -> int:
    results: list[bool] = []

    results.append(
        run_scenario(
            "T25 - red vacía",
            "HTTP 404 ORIGIN_NOT_FOUND al consultar un origen inexistente",
            lambda: coverage("origin-inexistente"),
            lambda r: has_error(r, 404, "ORIGIN_NOT_FOUND"),
        )
    )

    results.append(
        run_scenario(
            "T26 - falta de origen",
            "HTTP 400 MISSING_DATA",
            lambda: coverage(None),
            lambda r: has_error(r, 400, "MISSING_DATA"),
        )
    )

    warehouse = request("POST", "/points", {"name": "Bodega de aceptación", "type": "warehouse"})
    reachable = request("POST", "/points", {"name": "Barrio alcanzable", "type": "neighborhood"})
    isolated = request("POST", "/points", {"name": "Casa D", "type": "pickup_point"})
    point_responses = (warehouse, reachable, isolated)
    results.append(
        run_scenario(
            "T25 - preparar red de aceptación",
            "HTTP 201 para bodega, destino alcanzable y destino desconectado",
            lambda: point_responses,
            lambda rs: all(r.status == 201 and isinstance(r.body, dict) and r.body.get("id") for r in rs),
        )
    )

    if not all(
        r.status == 201 and isinstance(r.body, dict) and r.body.get("id")
        for r in point_responses
    ):
        print("\nNo se pueden ejecutar los escenarios restantes: la API no creó los puntos base.")
        print("Completa/inicia el backend y vuelve a ejecutar el script.")
        return 1

    warehouse_id = warehouse.body["id"]
    reachable_id = reachable.body["id"]
    isolated_id = isolated.body["id"]
    connection = request(
        "POST",
        "/connections",
        {"origin_id": warehouse_id, "destination_id": reachable_id, "cost_km": "1"},
    )
    results.append(
        run_scenario(
            "T25 - conexión de cobertura",
            "HTTP 201 para la conexión bodega -> destino",
            lambda: connection,
            lambda r: r.status == 201,
        )
    )

    results.append(
        run_scenario(
            "T25 - alcance normal",
            "HTTP 200 con el destino alcanzable en reachable",
            lambda: coverage(warehouse_id),
            lambda r: r.status == 200 and contains_point(r.body, reachable_id),
        )
    )
    results.append(
        run_scenario(
            "T25 - destino alcanzable",
            "HTTP 200 y reachable true",
            lambda: coverage(warehouse_id, reachable_id),
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and r.body.get("reachable") is True,
        )
    )
    results.append(
        run_scenario(
            "T26 - destino desconectado Casa D",
            "HTTP 200, reachable false y explicación",
            lambda: coverage(warehouse_id, isolated_id),
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and r.body.get("reachable") is False
            and bool(r.body.get("reason")),
        )
    )
    results.append(
        run_scenario(
            "T26 - origen inexistente",
            "HTTP 404 ORIGIN_NOT_FOUND",
            lambda: coverage("00000000-0000-0000-0000-000000000000"),
            lambda r: has_error(r, 404, "ORIGIN_NOT_FOUND"),
        )
    )
    results.append(
        run_scenario(
            "T26 - destino inexistente",
            "HTTP 404 DESTINATION_NOT_FOUND",
            lambda: coverage(warehouse_id, "00000000-0000-0000-0000-000000000000"),
            lambda r: has_error(r, 404, "DESTINATION_NOT_FOUND"),
        )
    )

    passed = sum(results)
    print(f"\nRESUMEN: {passed}/{len(results)} escenarios PASARON")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
