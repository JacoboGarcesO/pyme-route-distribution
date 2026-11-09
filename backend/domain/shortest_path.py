"""Ruta de menor costo entre dos puntos (Dijkstra, decisión T04 de docs/diseno.md)."""

from typing import NamedTuple

from domain.graph import Point, format_cost


class PathResult(NamedTuple):
    """Resultado de una consulta de ruta (T09).

    `path` son los puntos en orden origen→destino; `connections` los tramos
    recorridos. Si no hay ruta: `found` es False, `path` está vacío, el costo es
    None y `reason` explica por qué. Los costos son `Decimal`; `to_dict` los
    serializa como texto para no perder precisión.
    """

    origin: Point
    destination: Point
    found: bool
    path: list
    connections: list
    total_cost: object  # Decimal | None
    reason: str | None = None

    def to_dict(self):
        result = {
            "origin_id": str(self.origin.id),
            "destination_id": str(self.destination.id),
            "found": self.found,
            "path": [point.to_dict() for point in self.path],
            "connections": [c.to_dict() for c in self.connections],
            "total_cost_km": None if self.total_cost is None else format_cost(self.total_cost),
        }
        if self.reason:
            result["reason"] = self.reason
        return result
