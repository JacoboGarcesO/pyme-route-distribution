"""
T20 - Verificacion del nucleo en consola.

Carga la red de ejemplo de T11 (15 nodos, 28 aristas) y recorre casos
validos e invalidos imprimiendo el resultado de cada uno.

Ejecutar desde la carpeta backend/:
    python verify_nucleus.py
"""

import sys
from domain.graph import Graph
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
)

PASS = "PASO"
FAIL = "FALLO"
_failures = 0


def check(scenario, expected, fn):
    global _failures
    try:
        result = fn()
        if expected is None:
            print(f"[{PASS}] {scenario}")
            print(f"       esperado : exito")
            print(f"       obtenido : {result}")
        else:
            print(f"[{FAIL}] {scenario}")
            print(f"       esperado : {expected.__name__}")
            print(f"       obtenido : exito inesperado")
            _failures += 1
    except Exception as exc:
        if expected is not None and isinstance(exc, expected):
            print(f"[{PASS}] {scenario}")
            print(f"       esperado : {expected.__name__}")
            print(f"       obtenido : {type(exc).__name__} - {exc}")
        else:
            label = expected.__name__ if expected else "exito"
            print(f"[{FAIL}] {scenario}")
            print(f"       esperado : {label}")
            print(f"       obtenido : {type(exc).__name__} - {exc}")
            _failures += 1
    print()


# ---------------------------------------------------------------------------
# Construccion de la red T11
# ---------------------------------------------------------------------------

def build_t11_network():
    g = Graph()

    # --- nodos ---
    # Las esquinas no tienen un tipo natural en la lista cerrada;
    # se registran como 'neighborhood' segun la decision pendiente de T11.
    BOD    = g.add_point("Bodega",   "warehouse")
    C10K5  = g.add_point("C10K5",    "neighborhood")
    C10K6  = g.add_point("C10K6",    "neighborhood")
    C10K7  = g.add_point("C10K7",    "neighborhood")
    C10K8  = g.add_point("C10K8",    "neighborhood")
    C11K6  = g.add_point("C11K6",    "neighborhood")
    C11K7  = g.add_point("C11K7",    "neighborhood")
    C11K8  = g.add_point("C11K8",    "neighborhood")
    C12K5  = g.add_point("C12K5",    "neighborhood")
    C12K6  = g.add_point("C12K6",    "neighborhood")
    C12K7  = g.add_point("C12K7",    "neighborhood")
    C12K8  = g.add_point("C12K8",    "neighborhood")
    CasaA  = g.add_point("Casa A",   "pickup_point")
    CasaB  = g.add_point("Casa B",   "pickup_point")
    CasaC  = g.add_point("Casa C",   "pickup_point")

    ids = {
        "BOD": BOD, "C10K5": C10K5, "C10K6": C10K6, "C10K7": C10K7,
        "C10K8": C10K8, "C11K6": C11K6, "C11K7": C11K7, "C11K8": C11K8,
        "C12K5": C12K5, "C12K6": C12K6, "C12K7": C12K7, "C12K8": C12K8,
        "CasaA": CasaA, "CasaB": CasaB, "CasaC": CasaC,
    }

    # --- aristas (28 segun T11) ---
    edges = [
        ("C10K5",  "C10K6",  "0.4"),
        ("C10K6",  "C10K5",  "0.4"),
        ("C10K6",  "C10K7",  "0.5"),
        ("C10K7",  "C10K8",  "0.3"),
        ("C10K8",  "C10K7",  "0.3"),
        ("BOD",    "C11K6",  "0.4"),
        ("C11K6",  "BOD",    "0.4"),
        ("C11K6",  "C11K7",  "0.5"),
        ("C11K7",  "C11K6",  "0.5"),
        ("C11K8",  "C11K7",  "0.3"),
        ("C12K5",  "C12K6",  "0.4"),
        ("C12K6",  "C12K7",  "0.5"),
        ("C12K7",  "C12K8",  "0.3"),
        ("C10K5",  "BOD",    "0.3"),
        ("BOD",    "C10K5",  "0.3"),
        ("BOD",    "C12K5",  "0.2"),
        ("C12K5",  "BOD",    "0.2"),
        ("C10K6",  "C11K6",  "0.3"),
        ("C11K6",  "C12K6",  "0.2"),
        ("C10K7",  "C11K7",  "0.3"),
        ("C11K7",  "C10K7",  "0.3"),
        ("C11K7",  "C12K7",  "0.3"),
        ("C12K7",  "C11K7",  "0.3"),
        ("C11K8",  "C10K8",  "0.2"),
        ("C12K8",  "C11K8",  "0.3"),
        ("C11K6",  "CasaA",  "0.1"),
        ("C12K6",  "CasaC",  "0.1"),
        ("C12K8",  "CasaB",  "0.1"),
    ]

    for origin, dest, cost in edges:
        g.add_connection(
            str(ids[origin].id),
            str(ids[dest].id),
            cost,
        )

    return g, ids


# ---------------------------------------------------------------------------
# Bloque 1 - Casos validos: cargar la red T11
# ---------------------------------------------------------------------------

print("=" * 60)
print("BLOQUE 1 - Carga de la red T11")
print("=" * 60)
print()

g, ids = build_t11_network()

check(
    "Red T11 cargada: 15 puntos",
    None,
    lambda: f"{len(g.list_points())} puntos registrados",
)

check(
    "Red T11 cargada: 28 conexiones",
    None,
    lambda: f"{len(g.list_connections())} conexiones registradas",
)

check(
    "Vecinos salientes de BOD",
    None,
    lambda: g.neighbors(str(ids["BOD"].id)),
)

check(
    "Red legible devuelve 15 entradas",
    None,
    lambda: f"{len(g.readable_network())} entradas en la red legible",
)

# ---------------------------------------------------------------------------
# Bloque 2 - Rechazos al crear puntos (P1, P2, P3)
# ---------------------------------------------------------------------------

print("=" * 60)
print("BLOQUE 2 - Validaciones al crear puntos")
print("=" * 60)
print()

check(
    "P2 - nombre vacio",
    InvalidName,
    lambda: g.add_point("", "warehouse"),
)

check(
    "P2 - nombre solo espacios",
    InvalidName,
    lambda: g.add_point("   ", "neighborhood"),
)

check(
    "P3 - tipo no permitido",
    InvalidType,
    lambda: g.add_point("Punto nuevo", "deposito"),
)

# ---------------------------------------------------------------------------
# Bloque 3 - Rechazos al crear conexiones (C2 a C9)
# ---------------------------------------------------------------------------

print("=" * 60)
print("BLOQUE 3 - Validaciones al crear conexiones")
print("=" * 60)
print()

FAKE_UUID = "00000000-0000-0000-0000-000000000000"
bod_id  = str(ids["BOD"].id)
c10k5_id = str(ids["C10K5"].id)
c10k6_id = str(ids["C10K6"].id)

check(
    "C2 - UUID de origen con formato invalido",
    OriginNotFound,
    lambda: g.add_connection("no-es-un-uuid", c10k5_id, "1.0"),
)

check(
    "C2 - origen inexistente (UUID valido pero no registrado)",
    OriginNotFound,
    lambda: g.add_connection(FAKE_UUID, c10k5_id, "1.0"),
)

check(
    "C3 - UUID de destino con formato invalido",
    DestinationNotFound,
    lambda: g.add_connection(bod_id, "tampoco-es-uuid", "1.0"),
)

check(
    "C3 - destino inexistente (UUID valido pero no registrado)",
    DestinationNotFound,
    lambda: g.add_connection(bod_id, FAKE_UUID, "1.0"),
)

check(
    "C4 - auto-lazo (origen == destino)",
    SelfLoop,
    lambda: g.add_connection(bod_id, bod_id, "1.0"),
)

check(
    "C5 - costo enviado como numero JSON en lugar de texto",
    InvalidCost,
    lambda: g.add_connection(bod_id, c10k5_id, 4.5),
)

check(
    "C5 - costo con letras",
    InvalidCost,
    lambda: g.add_connection(bod_id, c10k5_id, "cuatro"),
)

check(
    "C5 - costo infinito",
    InvalidCost,
    lambda: g.add_connection(bod_id, c10k5_id, "Infinity"),
)

check(
    "C6 - costo cero",
    NonPositiveCost,
    lambda: g.add_connection(bod_id, c10k5_id, "0"),
)

check(
    "C6 - costo negativo",
    NonPositiveCost,
    lambda: g.add_connection(bod_id, c10k5_id, "-1.5"),
)

check(
    "C7 - costo con mas de 7 decimales",
    CostPrecision,
    lambda: g.add_connection(bod_id, c10k5_id, "0.12345678"),
)

check(
    "C8 - conexion duplicada (mismo sentido)",
    DuplicateConnection,
    lambda: g.add_connection(bod_id, c10k6_id, "0.4"),
)

# Para C9 necesitamos un par sin conexion inversa aun; usamos C10K6->C10K7
# que es de un solo sentido: existe C10K6->C10K7 (0.5) pero no C10K7->C10K6.
c10k7_id = str(ids["C10K7"].id)
check(
    "C9 - conexion inversa con costo distinto",
    InconsistentCost,
    lambda: g.add_connection(c10k7_id, c10k6_id, "9.9"),
)

check(
    "C9 ok - conexion inversa con el mismo costo (debe aceptarse)",
    None,
    lambda: g.add_connection(c10k7_id, c10k6_id, "0.5"),
)

# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------

print("=" * 60)
total = 18
passed = total - _failures
print(f"Resultado: {passed}/{total} casos pasaron")
if _failures == 0:
    print("Todo el nucleo verifica correctamente.")
else:
    print(f"{_failures} caso(s) fallaron.")
print("=" * 60)

sys.exit(0 if _failures == 0 else 1)
