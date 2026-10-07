"""POST /connections and GET /connections (T23, docs/api.md)."""

from flask import Blueprint, current_app

from api.errors import json_body
from domain.errors import MissingData

connections_bp = Blueprint("connections", __name__)


@connections_bp.post("/connections")
def create_connection():
    body = json_body()
    if (
        body.get("origin_id") is None
        or body.get("destination_id") is None
        or body.get("cost_km") is None
    ):
        raise MissingData("Los campos 'origin_id', 'destination_id' y 'cost_km' son obligatorios.")
    graph = current_app.extensions["graph"]
    connection = graph.add_connection(body["origin_id"], body["destination_id"], body["cost_km"])
    return connection.to_dict(), 201


@connections_bp.get("/connections")
def list_connections():
    graph = current_app.extensions["graph"]
    return {"connections": [connection.to_dict() for connection in graph.list_connections()]}
