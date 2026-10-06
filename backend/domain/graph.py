import uuid
from decimal import Decimal, InvalidOperation

from domain.errors import (
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
            "cost_km": str(self.cost_km),
        }


class Graph:
    def __init__(self):
        self._points = {}     # {UUID: Point}
        self._adjacency = {}  # {UUID: {UUID: Decimal}}

    def add_point(self, name, type):
        if not name or not str(name).strip():
            raise InvalidName("El nombre del punto no puede estar vacío.")
        if type not in VALID_TYPES:
            raise InvalidType(
                f"El tipo '{type}' no es válido. "
                "Tipos permitidos: warehouse, neighborhood, pickup_point."
            )
        point_id = uuid.uuid4()
        point = Point(id=point_id, name=str(name).strip(), type=type)
        self._points[point_id] = point
        self._adjacency[point_id] = {}
        return point
