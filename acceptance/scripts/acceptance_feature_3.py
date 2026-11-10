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

    passed = sum(results)
    print(f"\nRESUMEN: {passed}/{len(results)} escenarios PASARON")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
