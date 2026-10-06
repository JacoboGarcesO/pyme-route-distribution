from flask import Flask, jsonify

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


def _error_response(exc):
    status, code = _ERROR_CODES.get(type(exc), (500, "INTERNAL_ERROR"))
    return jsonify({"error": {"code": code, "message": str(exc)}}), status


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
