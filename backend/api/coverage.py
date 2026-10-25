"""GET /coverage: destinos alcanzables desde un origen (T17, docs/api.md)."""

from flask import Blueprint, current_app, request

from domain.coverage import find_point, visit_order
from domain.errors import DestinationNotFound, MissingData

coverage_bp = Blueprint("coverage", __name__)


@coverage_bp.get("/coverage")
def get_coverage():
    origin_id = request.args.get("origin", "").strip()
    if not origin_id:
        raise MissingData("El parámetro 'origin' es obligatorio.")

    destination_id = request.args.get("destination", "").strip() or None
    graph = current_app.extensions["graph"]
    order = visit_order(graph, origin_id)
    points = {str(point.id): point for point in graph.list_points()}

    if destination_id is None:
        return {
            "origin_id": str(order[0]),
            "reachable": [points[str(point_id)].to_dict() for point_id in order[1:]],
            "visit_order": [str(point_id) for point_id in order],
        }

    destination = find_point(graph, destination_id, DestinationNotFound, "punto de destino")
    origin = points[str(order[0])]
    if destination.id in order:
        return {
            "origin_id": str(origin.id),
            "destination_id": str(destination.id),
            "reachable": True,
        }
    return {
        "origin_id": str(origin.id),
        "destination_id": str(destination.id),
        "reachable": False,
        "reason": f"No hay un camino dirigido desde '{origin.name}' hasta '{destination.name}'.",
    }
