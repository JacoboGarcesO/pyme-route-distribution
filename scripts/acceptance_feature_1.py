"""Acceptance script for Feature 1 of RutaPyme.

Usage:
    python scripts/acceptance_feature_1.py

The script uses only Python's standard library and expects a freshly started
API at http://127.0.0.1:5000.
"""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:5000"


@dataclass
class Response:
    status: int | None
    body: object
    error: str | None = None


def request(method: str, path: str, payload: object | None = None) -> Response:
    """Call the API and normalize success and HTTP error responses."""
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data is not None else {}
    request_object = Request(
        f"{BASE_URL}{path}", data=data, headers=headers, method=method
    )

    try:
        with urlopen(request_object, timeout=5) as response:
            raw_body = response.read().decode("utf-8")
            return Response(response.status, parse_body(raw_body))
    except HTTPError as error:
        raw_body = error.read().decode("utf-8")
        return Response(error.code, parse_body(raw_body), str(error))
    except (URLError, TimeoutError) as error:
        return Response(None, None, str(error))


def parse_body(raw_body: str) -> object:
    if not raw_body:
        return None
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body


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


def main() -> int:
    results: list[bool] = []
    suffix = uuid.uuid4().hex[:8]

    results.append(
        run_scenario(
            "T30 - API saludable",
            "HTTP 200 y {status: ok}",
            lambda: request("GET", "/health"),
            lambda r: r.status == 200 and r.body == {"status": "ok"},
        )
    )

    results.append(
        run_scenario(
            "T30 - red vacía",
            "HTTP 200 y una lista de puntos vacía",
            lambda: request("GET", "/network"),
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and r.body.get("points") == [],
        )
    )

    warehouse = request(
        "POST", "/points", {"name": f"Bodega {suffix}", "type": "warehouse"}
    )
    neighborhood = request(
        "POST", "/points", {"name": f"Barrio {suffix}", "type": "neighborhood"}
    )
    pickup = request(
        "POST", "/points", {"name": f"Recogida {suffix}", "type": "pickup_point"}
    )
    results.append(
        run_scenario(
            "T30 - crear puntos válidos",
            "HTTP 201 y tres puntos con UUID",
            lambda: (warehouse, neighborhood, pickup),
            lambda rs: all(
                r.status == 201 and isinstance(r.body, dict) and r.body.get("id")
                for r in rs
            ),
        )
    )

    point_responses = (warehouse, neighborhood, pickup)
    if not all(
        response.status == 201
        and isinstance(response.body, dict)
        and response.body.get("id")
        for response in point_responses
    ):
        print(
            "\nNo se pueden ejecutar los escenarios restantes: "
            "POST /points todavía no devuelve tres puntos válidos."
        )
        print("Completa los endpoints del backend y vuelve a ejecutar el script.")
        return 1

    ids = [r.body["id"] for r in (warehouse, neighborhood, pickup)]
    origin_id, destination_id, pickup_id = ids
    connection = request(
        "POST",
        "/connections",
        {"origin_id": origin_id, "destination_id": destination_id, "cost_km": "4.5"},
    )
    results.append(
        run_scenario(
            "T30 - crear conexión válida",
            "HTTP 201 y costo devuelto como texto",
            lambda: connection,
            lambda r: r.status == 201
            and isinstance(r.body, dict)
            and r.body.get("cost_km") == "4.5",
        )
    )

    reverse_connection = request(
        "POST",
        "/connections",
        {"origin_id": destination_id, "destination_id": origin_id, "cost_km": "4.5"},
    )
    results.append(
        run_scenario(
            "T30 - conexión inversa con el mismo costo",
            "HTTP 201: el sentido contrario se acepta si el costo coincide",
            lambda: reverse_connection,
            lambda r: r.status == 201
            and isinstance(r.body, dict)
            and r.body.get("origin_id") == destination_id
            and r.body.get("cost_km") == "4.5",
        )
    )

    one_way_connection = request(
        "POST",
        "/connections",
        {"origin_id": pickup_id, "destination_id": origin_id, "cost_km": "2"},
    )
    results.append(
        run_scenario(
            "T30 - conexión de un solo sentido",
            "HTTP 201 para pickup -> origen, sin crear la inversa",
            lambda: one_way_connection,
            lambda r: r.status == 201,
        )
    )

    positioned = request(
        "POST",
        "/points",
        {"name": f"Con posición {suffix}", "type": "neighborhood", "x": 2.5, "y": 1},
    )
    results.append(
        run_scenario(
            "T30 - punto con posición en el mapa",
            "HTTP 201 y la posición x, y devuelta",
            lambda: positioned,
            lambda r: r.status == 201
            and isinstance(r.body, dict)
            and r.body.get("x") == 2.5
            and r.body.get("y") == 1,
        )
    )

    results.append(
        run_scenario(
            "T30 - punto sin posición",
            "HTTP 200 y x, y nulos para un punto creado sin posición",
            lambda: request("GET", "/points"),
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and any(
                p.get("id") == origin_id and p.get("x") is None and p.get("y") is None
                for p in r.body.get("points", [])
            ),
        )
    )

    results.append(
        run_scenario(
            "T30 - listar puntos",
            "HTTP 200 y al menos los tres puntos creados",
            lambda: request("GET", "/points"),
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and {origin_id, destination_id, pickup_id}
            <= {p.get("id") for p in r.body.get("points", [])},
        )
    )

    def connection_pairs(response: Response) -> set[tuple[str, str]]:
        if not (response.status == 200 and isinstance(response.body, dict)):
            return set()
        return {
            (c.get("origin_id"), c.get("destination_id"))
            for c in response.body.get("connections", [])
        }

    results.append(
        run_scenario(
            "T30 - listar conexiones",
            "HTTP 200 con las tres conexiones y solo una entre pickup y origen",
            lambda: request("GET", "/connections"),
            lambda r: connection_pairs(r)
            == {
                (origin_id, destination_id),
                (destination_id, origin_id),
                (pickup_id, origin_id),
            },
        )
    )

    results.append(
        run_scenario(
            "T30 - consultar red registrada",
            "HTTP 200 con los puntos y la conexión creada",
            lambda: request("GET", "/network"),
            lambda r: r.status == 200
            and isinstance(r.body, dict)
            and len(r.body.get("points", [])) >= 3,
        )
    )

    error_cases = [
        (
            "T31 - nombre vacío",
            {"name": "   ", "type": "warehouse"},
            422,
            "INVALID_NAME",
        ),
        (
            "T31 - tipo inválido",
            {"name": f"Tipo inválido {suffix}", "type": "invalid"},
            422,
            "INVALID_TYPE",
        ),
        (
            "T31 - origen inexistente",
            {"origin_id": str(uuid.uuid4()), "destination_id": destination_id, "cost_km": "1"},
            404,
            "ORIGIN_NOT_FOUND",
        ),
        (
            "T31 - destino inexistente",
            {"origin_id": origin_id, "destination_id": str(uuid.uuid4()), "cost_km": "1"},
            404,
            "DESTINATION_NOT_FOUND",
        ),
        (
            "T31 - conexión duplicada",
            {"origin_id": origin_id, "destination_id": destination_id, "cost_km": "4.5"},
            409,
            "DUPLICATE_CONNECTION",
        ),
        (
            "T31 - costo distinto en el sentido contrario",
            {"origin_id": origin_id, "destination_id": pickup_id, "cost_km": "3"},
            409,
            "INCONSISTENT_COST",
        ),
        (
            "T31 - punto sin tipo",
            {"name": f"Sin tipo {suffix}"},
            400,
            "MISSING_DATA",
        ),
        (
            "T31 - conexión sin costo",
            {"origin_id": origin_id, "destination_id": pickup_id},
            400,
            "MISSING_DATA",
        ),
        (
            "T31 - costo como número JSON",
            {"origin_id": origin_id, "destination_id": pickup_id, "cost_km": 4.5},
            400,
            "INVALID_COST",
        ),
        (
            "T31 - posición incompleta",
            {"name": f"Posición incompleta {suffix}", "type": "neighborhood", "x": 1},
            422,
            "INVALID_POSITION",
        ),
        (
            "T31 - posición no numérica",
            {"name": f"Posición texto {suffix}", "type": "neighborhood", "x": "a", "y": 1},
            422,
            "INVALID_POSITION",
        ),
        (
            "T31 - auto-lazo",
            {"origin_id": origin_id, "destination_id": origin_id, "cost_km": "1"},
            422,
            "SELF_LOOP",
        ),
        (
            "T31 - costo cero",
            {"origin_id": origin_id, "destination_id": pickup_id, "cost_km": "0"},
            422,
            "NON_POSITIVE_COST",
        ),
        (
            "T31 - costo negativo",
            {"origin_id": origin_id, "destination_id": pickup_id, "cost_km": "-1"},
            422,
            "NON_POSITIVE_COST",
        ),
        (
            "T31 - costo no numérico",
            {"origin_id": origin_id, "destination_id": pickup_id, "cost_km": "abc"},
            400,
            "INVALID_COST",
        ),
        (
            "T31 - demasiados decimales",
            {"origin_id": origin_id, "destination_id": pickup_id, "cost_km": "1.12345678"},
            422,
            "COST_PRECISION",
        ),
    ]

    for name, payload, expected_status, expected_code in error_cases:
        results.append(
            run_scenario(
                name,
                f"HTTP {expected_status} y código {expected_code}",
                lambda payload=payload: request("POST", "/points" if "name" in payload else "/connections", payload),
                lambda r, status=expected_status, code=expected_code: r.status == status
                and error_code(r) == code,
            )
        )

    passed = sum(results)
    failed = len(results) - passed
    print(f"\nRESUMEN: {passed} PASÓ, {failed} FALLÓ, {len(results)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
