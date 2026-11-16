"""Ruta de menor costo entre dos puntos (Dijkstra, decisión T04 de docs/diseno.md)."""

import heapq
from decimal import Decimal
from itertools import count
from typing import NamedTuple

from domain.coverage import find_point
from domain.errors import DestinationNotFound, OriginNotFound, ViaNotFound
from domain.graph import Connection, Point, format_cost


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
    via: object = None  # Point | None: parada obligatoria de F4

    def to_dict(self):
        result = {
            "origin_id": str(self.origin.id),
            "destination_id": str(self.destination.id),
            "found": self.found,
            "path": [point.to_dict() for point in self.path],
            "connections": [c.to_dict() for c in self.connections],
            "total_cost_km": None if self.total_cost is None else format_cost(self.total_cost),
        }
        if self.via:
            result["via_id"] = str(self.via.id)
        if self.reason:
            result["reason"] = self.reason
        return result


def dijkstra(graph, origin_id, destination_id):
    """Costo mínimo de `origin_id` a cada punto, parando al fijar `destination_id` (T10).

    Devuelve `(dist, pred)`: {UUID: Decimal} con los costos hallados y {UUID: UUID}
    con el predecesor de cada punto en su mejor ruta (T11). Usa la lista de
    adyacencia de `Graph` (`neighbors`, en orden de nombre) y suma con `Decimal`.
    Es correcto porque todo costo es > 0 (T07). Tiempo O((V + E) log V).
    """
    dist = {origin_id: Decimal(0)}
    pred = {}
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
                pred[neighbor] = current
                heapq.heappush(heap, (new_cost, next(ticket), neighbor))
    return dist, pred


def reconstruct_path(pred, origin_id, destination_id):
    """UUIDs de la ruta en orden origen→destino, siguiendo los predecesores hacia atrás (T11).

    El destino debe ser alcanzable (estar en `dist`); si es el origen devuelve solo ese punto.
    """
    path = [destination_id]
    while path[-1] != origin_id:
        path.append(pred[path[-1]])
    path.reverse()
    return path


def _leg(graph, origin_id, destination_id):
    """Ids de la ruta de menor costo y su costo, o None si no hay camino dirigido."""
    dist, pred = dijkstra(graph, origin_id, destination_id)
    if destination_id not in dist:
        return None
    return reconstruct_path(pred, origin_id, destination_id), dist[destination_id]


def shortest_path(graph, origin_id, destination_id, via_id=None):
    """Ruta de menor costo de `origin_id` a `destination_id` como `PathResult` (T12).

    Valida primero el origen, luego el destino y al final la parada con las
    excepciones de F1 (`OriginNotFound`, `DestinationNotFound`) y `ViaNotFound`:
    un UUID inválido cuenta como inexistente. Que no haya camino dirigido NO es
    un error: devuelve `found=False` con `reason`. Origen igual al destino es una
    ruta de un punto con costo 0 (T05).

    Con `via_id` (cambio de requisito de F4) la ruta debe pasar por esa parada:
    es la mejor ruta origen→parada más la mejor parada→destino, cada una con
    Dijkstra. Es el mínimo entre las rutas que pasan por la parada. Puede
    repetir un punto si la parada obliga a volver sobre él.
    """
    origin = find_point(graph, origin_id, OriginNotFound, "punto de origen")
    destination = find_point(graph, destination_id, DestinationNotFound, "punto de destino")
    via = find_point(graph, via_id, ViaNotFound, "punto de parada") if via_id else None
    stops = [origin.id] + ([via.id] if via else []) + [destination.id]
    ids, total = [origin.id], Decimal(0)
    for start, end in zip(stops, stops[1:]):
        leg = _leg(graph, start, end)
        if leg is None:
            names = {p.id: p.name for p in graph.list_points()}
            reason = f"No hay un camino dirigido desde '{names[start]}' hasta '{names[end]}'."
            if via:
                reason += f" Sin él no se puede pasar por la parada '{via.name}'."
            return PathResult(origin, destination, False, [], [], None, reason, via)
        ids += leg[0][1:]
        total += leg[1]
    points = {point.id: point for point in graph.list_points()}
    pairs = list(zip(ids, ids[1:]))
    connections = [Connection(a, b, graph.neighbors(a)[b]) for a, b in pairs]
    return PathResult(origin, destination, True, [points[i] for i in ids], connections, total, None, via)
