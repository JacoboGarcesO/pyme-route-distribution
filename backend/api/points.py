"""POST /points and GET /points (T22, docs/api.md)."""

from flask import Blueprint, current_app

from api.errors import json_body
from domain.errors import MissingData

points_bp = Blueprint("points", __name__)


@points_bp.post("/points")
def create_point():
    body = json_body()
    if body.get("name") is None or body.get("type") is None:
        raise MissingData("Los campos 'name' y 'type' son obligatorios.")
    graph = current_app.extensions["graph"]
    point = graph.add_point(body["name"], body["type"], body.get("x"), body.get("y"))
    return point.to_dict(), 201


@points_bp.get("/points")
def list_points():
    graph = current_app.extensions["graph"]
    return {"points": [point.to_dict() for point in graph.list_points()]}
