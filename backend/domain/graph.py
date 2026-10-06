import uuid
from decimal import Decimal, InvalidOperation

from domain.errors import (
    MissingData,
    InvalidName,
    InvalidType,
    OriginNotFound,
    DestinationNotFound,
    SelfLoop,
    InvalidCost,
    NonPositiveCost,
    CostPrecision,
    DuplicateConnection,
    InconsistentCost,
    PointNotFound,
)

VALID_TYPES = frozenset({"warehouse", "neighborhood", "pickup_point"})
MAX_DECIMAL_PLACES = 7


def format_cost(cost_km):
    # str(Decimal("1E+1")) gives "1E+1"; the contract requires fixed notation.
    return format(cost_km, "f")


class Point:
    def __init__(self, id, name, type):
        self.id = id
        self.name = name
        self.type = type

    def to_dict(self):
        return {"id": str(self.id), "name": self.name, "type": self.type}


class Connection:
    def __init__(self, origin_id, destination_id, cost_km):
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.cost_km = cost_km

    def to_dict(self):
        return {
            "origin_id": str(self.origin_id),
            "destination_id": str(self.destination_id),
            "cost_km": format_cost(self.cost_km),
        }


class Graph:
    def __init__(self):
        self._points = {}     # {UUID: Point}
        self._adjacency = {}  # {UUID: {UUID: Decimal}}

    def add_point(self, name, type):
        if not isinstance(name, str) or not name.strip():
            raise InvalidName("El nombre del punto no puede estar vacío.")
        if not isinstance(type, str) or type not in VALID_TYPES:
            raise InvalidType(
                f"El tipo '{type}' no es válido. "
                "Tipos permitidos: warehouse, neighborhood, pickup_point."
            )
        point_id = uuid.uuid4()
        point = Point(id=point_id, name=name.strip(), type=type)
        self._points[point_id] = point
        self._adjacency[point_id] = {}
        return point

    @staticmethod
    def _parse_uuid(value):
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except ValueError:
            return None

    @staticmethod
    def _sort_key(point):
        return (point.name.casefold(), str(point.id))

    def list_points(self):
        return sorted(self._points.values(), key=self._sort_key)

    def add_connection(self, origin_id_str, destination_id_str, cost_km_str):
        # C1: required data must be present
        if origin_id_str is None or destination_id_str is None or cost_km_str is None:
            raise MissingData("Faltan datos: origin_id, destination_id y cost_km son obligatorios.")

        # C2: origin must exist
        origin_id = self._parse_uuid(origin_id_str)
        if origin_id is None or origin_id not in self._points:
            raise OriginNotFound(f"El punto de origen '{origin_id_str}' no existe.")

        # C3: destination must exist
        destination_id = self._parse_uuid(destination_id_str)
        if destination_id is None or destination_id not in self._points:
            raise DestinationNotFound(f"El punto de destino '{destination_id_str}' no existe.")

        # C4: no self-loop
        if origin_id == destination_id:
            raise SelfLoop("El origen y el destino deben ser distintos.")

        # C5: cost must be a decimal string
        if not isinstance(cost_km_str, str):
            raise InvalidCost(
                "El costo debe enviarse como texto decimal (por ejemplo, \"4.5\")."
            )
        try:
            cost = Decimal(cost_km_str)
        except InvalidOperation:
            raise InvalidCost(f"El costo '{cost_km_str}' no es un número decimal válido.")
        if not cost.is_finite():
            raise InvalidCost(f"El costo '{cost_km_str}' no es un número decimal válido.")

        # C6: must be positive
        if cost <= 0:
            raise NonPositiveCost("El costo debe ser mayor que 0 km.")

        # C7: at most 7 decimal places
        _, _, exponent = cost.as_tuple()
        decimal_places = -exponent if exponent < 0 else 0
        if decimal_places > MAX_DECIMAL_PLACES:
            raise CostPrecision(
                f"El costo no puede tener más de {MAX_DECIMAL_PLACES} decimales."
            )

        # C8: no duplicate connection
        if destination_id in self._adjacency.get(origin_id, {}):
            origin_name = self._points[origin_id].name
            dest_name = self._points[destination_id].name
            raise DuplicateConnection(
                f"Ya existe una conexión de '{origin_name}' a '{dest_name}'."
            )

        # C9: reverse connection must have the same cost
        reverse_cost = self._adjacency.get(destination_id, {}).get(origin_id)
        if reverse_cost is not None and reverse_cost != cost:
            dest_name = self._points[destination_id].name
            origin_name = self._points[origin_id].name
            raise InconsistentCost(
                f"Ya existe la conexión de '{dest_name}' a '{origin_name}' con un costo de "
                f"{reverse_cost} km; el costo en ambos sentidos debe coincidir."
            )

        self._adjacency[origin_id][destination_id] = cost
        return Connection(origin_id=origin_id, destination_id=destination_id, cost_km=cost)

    def list_connections(self):
        result = []
        for origin_id, destinations in self._adjacency.items():
            for dest_id, cost in destinations.items():
                result.append(
                    Connection(origin_id=origin_id, destination_id=dest_id, cost_km=cost)
                )
        return result

    def neighbors(self, point_id_str):
        try:
            point_id = uuid.UUID(str(point_id_str))
        except (ValueError, AttributeError):
            raise PointNotFound(f"El punto '{point_id_str}' no existe.")
        if point_id not in self._points:
            raise PointNotFound(f"El punto '{point_id_str}' no existe.")
        return {str(k): str(v) for k, v in self._adjacency.get(point_id, {}).items()}

    def readable_network(self):
        result = []
        for point_id, point in self._points.items():
            connections = [
                {
                    "destination_id": str(dest_id),
                    "destination_name": self._points[dest_id].name,
                    "cost_km": str(cost),
                }
                for dest_id, cost in self._adjacency.get(point_id, {}).items()
            ]
            result.append({
                "id": str(point_id),
                "name": point.name,
                "type": point.type,
                "connections": connections,
            })
        return result
