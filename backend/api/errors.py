"""Traducción uniforme de errores a respuestas HTTP (T25, docs/api.md).

Toda respuesta de error tiene la forma:

    {"error": {"code": "DUPLICATE_CONNECTION", "message": "..."}}

Los endpoints no construyen errores a mano: dejan que la excepción del núcleo
suba y este módulo la traduce según la tabla de `HTTP_ERRORS`.
"""

from flask import current_app, jsonify, request
from werkzeug.exceptions import HTTPException

from domain.errors import (
    CostPrecision,
    DestinationNotFound,
    DuplicateConnection,
    GraphError,
    InconsistentCost,
    InvalidCost,
    InvalidName,
    InvalidType,
    MissingData,
    NonPositiveCost,
    OriginNotFound,
    PointNotFound,
    SelfLoop,
)

# Excepción del núcleo -> (código HTTP, code estable para el cliente).
HTTP_ERRORS = {
    MissingData: (400, "MISSING_DATA"),
    InvalidCost: (400, "INVALID_COST"),
    InvalidName: (422, "INVALID_NAME"),
    InvalidType: (422, "INVALID_TYPE"),
    SelfLoop: (422, "SELF_LOOP"),
    NonPositiveCost: (422, "NON_POSITIVE_COST"),
    CostPrecision: (422, "COST_PRECISION"),
    OriginNotFound: (404, "ORIGIN_NOT_FOUND"),
    DestinationNotFound: (404, "DESTINATION_NOT_FOUND"),
    PointNotFound: (404, "POINT_NOT_FOUND"),
    DuplicateConnection: (409, "DUPLICATE_CONNECTION"),
    InconsistentCost: (409, "INCONSISTENT_COST"),
}

# Errores de Flask que no vienen del núcleo (ruta o método inexistente).
HTTP_FALLBACK_CODES = {
    404: ("NOT_FOUND", "La ruta solicitada no existe."),
    405: ("METHOD_NOT_ALLOWED", "El método no está permitido en esta ruta."),
}


def error_response(status, code, message):
    return jsonify({"error": {"code": code, "message": message}}), status


def json_body():
    """Devuelve el cuerpo JSON como diccionario o lanza MissingData.

    Cubre P1/C1 cuando el cuerpo falta, no es JSON válido o no es un objeto.
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise MissingData("El cuerpo de la petición debe ser un objeto JSON válido.")
    return body


def handle_graph_error(error):
    status, code = HTTP_ERRORS.get(type(error), (400, "INVALID_REQUEST"))
    return error_response(status, code, error.message)


def handle_http_exception(error):
    code, message = HTTP_FALLBACK_CODES.get(
        error.code, ("HTTP_ERROR", error.description or "Error en la petición.")
    )
    return error_response(error.code, code, message)


def handle_unexpected_error(error):
    # El detalle queda en el log del servidor; el cliente no ve datos internos.
    current_app.logger.exception(error)
    return error_response(500, "INTERNAL_ERROR", "Ocurrió un error inesperado en el servidor.")


def register_error_handlers(app):
    app.register_error_handler(GraphError, handle_graph_error)
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(Exception, handle_unexpected_error)
