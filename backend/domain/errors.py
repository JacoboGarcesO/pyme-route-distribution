class MissingData(Exception):
    pass


class InvalidName(Exception):
    pass


class InvalidType(Exception):
    pass


class InvalidCost(Exception):
    pass


class SelfLoop(Exception):
    pass


class NonPositiveCost(Exception):
    pass


class CostPrecision(Exception):
    pass


class OriginNotFound(Exception):
    pass


class DestinationNotFound(Exception):
    pass


class PointNotFound(Exception):
    pass


class DuplicateConnection(Exception):
    pass


class InconsistentCost(Exception):
    pass
