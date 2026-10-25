"""Cobertura: qué puntos se alcanzan desde un origen en la red dirigida.

Usa un recorrido por capas (BFS), decidido en T04 de `docs/diseno.md`: una cola,
un conjunto de visitados y los vecinos salientes de `Graph` en orden de nombre,
así el orden de visita es siempre el mismo. "Alcanzable" se define en T05: solo
importa que exista un camino dirigido; los costos no se usan.
"""

from collections import deque

from domain.errors import OriginNotFound


def find_point(graph, point_id, error_class, label):
    """Devuelve el punto con ese UUID o lanza `error_class` si no existe.

    Un UUID con formato inválido se trata igual que uno inexistente.
    """
    for point in graph.list_points():
        if str(point.id) == str(point_id):
            return point
    raise error_class(f"El {label} '{point_id}' no existe.")


def visit_order(graph, origin_id):
    """UUIDs alcanzables en orden de visita, con el origen primero.

    Sigue el sentido de cada conexión. Un conjunto de visitados evita bucles
    cuando la red tiene ciclos, y un punto se visita una sola vez, por el primer
    camino que lo alcanza. Tiempo O(V + E) y memoria O(V).

    Lanza `OriginNotFound` si el origen no existe (la red vacía incluida).
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
