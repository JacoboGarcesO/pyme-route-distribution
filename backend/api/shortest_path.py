"""GET /shortest-path: ruta de menor costo entre dos puntos (T16, docs/api.md)."""

from flask import Blueprint, current_app

from api.params import query_arg
from domain.shortest_path import shortest_path

shortest_path_bp = Blueprint("shortest_path", __name__)


@shortest_path_bp.get("/shortest-path")
def get_shortest_path():
    origin_id = query_arg("origin", required=True)
    destination_id = query_arg("destination", required=True)
    graph = current_app.extensions["graph"]
    return shortest_path(graph, origin_id, destination_id).to_dict()
