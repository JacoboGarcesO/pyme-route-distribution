"""Excepciones del núcleo del grafo (docs/api.md, "Errores del núcleo").

El núcleo lanza estas excepciones con un mensaje en español pensado para el
coordinador. La API las traduce a código HTTP y `code` en un solo lugar
(backend/api/errors.py), así que ninguna excepción conoce HTTP.
"""


class GraphError(Exception):
    """Base de todo rechazo del núcleo."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class MissingData(GraphError):
    """P1, C1: falta un dato obligatorio o el cuerpo no se puede leer."""


class InvalidCost(GraphError):
    """C5: el costo no es un texto decimal válido o no es finito."""


class InvalidName(GraphError):
    """P2: el nombre es vacío o solo espacios."""


class InvalidType(GraphError):
    """P3: el tipo no está en la lista cerrada."""


class SelfLoop(GraphError):
    """C4: origen y destino son el mismo punto."""


class NonPositiveCost(GraphError):
    """C6: el costo es menor o igual que 0."""


class CostPrecision(GraphError):
    """C7: el costo tiene más de 7 decimales."""


class OriginNotFound(GraphError):
    """C2: el UUID de origen es inválido o no existe."""


class DestinationNotFound(GraphError):
    """C3: el UUID de destino es inválido o no existe."""


class PointNotFound(GraphError):
    """El punto consultado no existe (vecinos; reservado para F2 y F3)."""


class DuplicateConnection(GraphError):
    """C8: ya existe la conexión con el mismo origen y destino."""


class InconsistentCost(GraphError):
    """C9: existe la conexión inversa con un costo distinto."""
