"""Lectura de parámetros de consulta (T18 de F2): el equivalente de `json_body()` para GET."""

from flask import request

from domain.errors import MissingData


def query_arg(name, required=False):
    """Devuelve el parámetro de consulta sin espacios, o None si falta o está vacío.

    Con `required=True` lanza `MissingData` (400) en lugar de devolver None. El
    resto de errores los traduce el manejador de F1: los endpoints no los capturan.
    """
    value = request.args.get(name, "").strip()
    if value:
        return value
    if required:
        raise MissingData(f"El parámetro '{name}' es obligatorio.")
    return None
