from flask import Flask, jsonify, request

from domain.graph import Graph
from domain.errors import (
    MissingData,
    InvalidName,
    InvalidType,
    InvalidCost,
    SelfLoop,
    NonPositiveCost,
    CostPrecision,
    OriginNotFound,
    DestinationNotFound,
    DuplicateConnection,
    InconsistentCost,
)

app = Flask(__name__)
app.extensions["graph"] = Graph()

_ERROR_CODES = {
    MissingData:          (400, "MISSING_DATA"),
    InvalidCost:          (400, "INVALID_COST"),
    InvalidName:          (422, "INVALID_NAME"),
    InvalidType:          (422, "INVALID_TYPE"),
    SelfLoop:             (422, "SELF_LOOP"),
    NonPositiveCost:      (422, "NON_POSITIVE_COST"),
    CostPrecision:        (422, "COST_PRECISION"),
    OriginNotFound:       (404, "ORIGIN_NOT_FOUND"),
    DestinationNotFound:  (404, "DESTINATION_NOT_FOUND"),
    DuplicateConnection:  (409, "DUPLICATE_CONNECTION"),
    InconsistentCost:     (409, "INCONSISTENT_COST"),
}

_DOMAIN_EXCEPTIONS = tuple(_ERROR_CODES)


def json_body():
    """Return the parsed JSON body; raises MissingData when absent or not an object."""
    data = request.get_json(silent=True, force=True)
    if not isinstance(data, dict):
        raise MissingData("El cuerpo de la petición debe ser un objeto JSON válido.")
    return data


def _error_response(exc):
    status, code = _ERROR_CODES.get(type(exc), (500, "INTERNAL_ERROR"))
    return jsonify({"error": {"code": code, "message": str(exc)}}), status


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/points", methods=["POST"])
def create_point():
    try:
        body = json_body()
        name = body.get("name")
        type_ = body.get("type")
        if name is None or type_ is None:
            raise MissingData("Los campos 'name' y 'type' son obligatorios.")
        graph = app.extensions["graph"]
        point = graph.add_point(name=name, type=type_)
        return jsonify(point.to_dict()), 201
    except _DOMAIN_EXCEPTIONS as exc:
        return _error_response(exc)


@app.route("/points", methods=["GET"])
def list_points():
    graph = app.extensions["graph"]
    return jsonify({"points": [p.to_dict() for p in graph.list_points()]})


if __name__ == "__main__":
    app.run(debug=True)
