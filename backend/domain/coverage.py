"""Recorrido por capas (BFS) desde un origen sobre la red dirigida.

Creado para T17 (Issue #68). Jacobo (T11 a T12) y Mariana (T13) planean la
misma lógica en su propio trabajo: al integrar, conviene quedarse con una
sola versión.
"""

from collections import deque

from domain.errors import DestinationNotFound, OriginNotFound


def find_point(graph, point_id, error_class, label):
    for point in graph.list_points():
        if str(point.id) == str(point_id):
            return point
    raise error_class(f"El {label} '{point_id}' no existe.")


def visit_order(graph, origin_id):
    """UUIDs alcanzables en orden de visita, con el origen primero.

    Sigue el sentido de cada conexión. Un conjunto de visitados evita bucles
    cuando la red tiene ciclos.
    """
    origin = find_point(graph, origin_id, OriginNotFound, "punto de origen")
    order = [origin.id]
    seen = {origin.id}
    queue = deque([origin.id])
    while queue:
        current = queue.popleft()
        for destination_id in graph.neighbors(current):
            if destination_id not in seen:
                seen.add(destination_id)
                order.append(destination_id)
                queue.append(destination_id)
    return order
