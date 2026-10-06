"""GET /network: la red en forma legible (T24, docs/api.md).

Cada punto aparece con sus conexiones salientes y el nombre de cada destino.
La respuesta se arma con `list_points()` y `list_connections()` del núcleo,
cuyos tipos (`Point`, `Connection`) están fijados en el contrato.
"""

from flask import Blueprint, current_app

network_bp = Blueprint("network", __name__)


def format_cost(cost_km):
    # Notación decimal fija: Decimal("1E+1") se devuelve como "10", no "1E+1".
    return format(cost_km, "f")


def build_network(points, connections):
    names = {point.id: point.name for point in points}
    outgoing = {point.id: [] for point in points}
    for connection in connections:
        outgoing[connection.origin_id].append(
            {
                "destination_id": str(connection.destination_id),
                "destination_name": names[connection.destination_id],
                "cost_km": format_cost(connection.cost_km),
            }
        )

    return {
        "points": [
            {
                "id": str(point.id),
                "name": point.name,
                # Admite el tipo como texto o como Enum con .value.
                "type": getattr(point.type, "value", point.type),
                "connections": outgoing[point.id],
            }
            for point in points
        ]
    }


@network_bp.get("/network")
def get_network():
    graph = current_app.extensions["graph"]
    return build_network(graph.list_points(), graph.list_connections())
