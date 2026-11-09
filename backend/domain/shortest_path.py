"""Ruta de menor costo entre dos puntos (Dijkstra, decisión T04 de docs/diseno.md)."""

import heapq
from decimal import Decimal
from itertools import count
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


def dijkstra(graph, origin_id, destination_id):
    """Costo mínimo de `origin_id` a cada punto, parando al fijar `destination_id` (T10).

    Devuelve {UUID: Decimal} con los costos definitivos hallados. Usa la lista de
    adyacencia de `Graph` (`neighbors`, en orden de nombre) y suma con `Decimal`.
    Es correcto porque todo costo es > 0 (T07). Tiempo O((V + E) log V).
    """
    dist = {origin_id: Decimal(0)}
    done = set()
    ticket = count()  # desempata costos iguales por orden de inserción: resultado estable
    heap = [(Decimal(0), next(ticket), origin_id)]
    while heap:
        cost, _, current = heapq.heappop(heap)
        if current in done:
            continue  # entrada vieja: ya se fijó con un costo menor
        done.add(current)
        if current == destination_id:
            break
        for neighbor, weight in graph.neighbors(current).items():
            new_cost = cost + weight
            # Solo mejora estricta: así los empates conservan la primera ruta y los ciclos terminan.
            if neighbor not in dist or new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                heapq.heappush(heap, (new_cost, next(ticket), neighbor))
    return dist
