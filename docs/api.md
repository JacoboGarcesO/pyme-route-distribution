# Contrato de la API — Feature 1 (RutaPyme)

Este documento define la interfaz entre el frontend, el script de aceptación y el backend. Se apoya en las decisiones de `diseno.md` (T06 a T09).

La explicación está en español, pero **todo lo que forma parte del código está en inglés**: rutas, campos JSON, valores de enumeraciones, códigos de error y nombres de clases, métodos y excepciones. Solo el texto `message` de los errores, pensado para personas, está en español.

## Convenciones

- Formato de intercambio: **JSON** (`Content-Type: application/json`).
- Los identificadores de puntos son **UUID** generados por el sistema al crear el punto. Toda referencia a un punto (origen, destino, consulta de vecinos) usa el UUID. El nombre (`name`) es solo informativo.
- El costo (`cost_km`) es una **distancia en km**, estrictamente mayor que 0, con hasta 7 decimales. Se envía y se devuelve como **texto con notación decimal** (por ejemplo, `"4.5"`), porque el sistema lo representa con `Decimal` y un número JSON se convierte en un decimal binario inexacto. Un número JSON en este campo se rechaza como formato incorrecto.
- Los nombres de ruta no llevan prefijo (`/points`, no `/api/points`). Si el frontend usa un proxy de desarrollo, se agrega el prefijo en una sola decisión posterior.

### Valores del campo `type`

| Valor | Significado |
|---|---|
| `warehouse` | Bodega |
| `neighborhood` | Barrio |
| `pickup_point` | Punto de recogida |

## Endpoints

| Método | Ruta | Propósito | Éxito |
|---|---|---|---|
| GET | `/health` | Comprobar que la API responde | 200 |
| POST | `/points` | Crear un punto | 201 |
| GET | `/points` | Listar puntos | 200 |
| POST | `/connections` | Crear una conexión dirigida | 201 |
| GET | `/connections` | Listar conexiones | 200 |
| GET | `/network` | Consultar la red en forma legible | 200 |

### GET `/health`

Respuesta 200:

```json
{ "status": "ok" }
```

### POST `/points`

Entrada:

```json
{ "name": "Central warehouse", "type": "warehouse" }
```

- `name`: texto obligatorio, no vacío ni solo espacios. Puede repetirse entre puntos.
- `type`: uno de `warehouse`, `neighborhood`, `pickup_point`.

Respuesta 201:

```json
{ "id": "3f2b8c1e-9a4d-4e6b-b1d7-5c0a2e8f7a11", "name": "Central warehouse", "type": "warehouse" }
```

### GET `/points`

Respuesta 200 (con la red vacía devuelve una lista vacía, no un error):

```json
{ "points": [ { "id": "3f2b8c1e-...", "name": "Central warehouse", "type": "warehouse" } ] }
```

### POST `/connections`

Entrada:

```json
{ "origin_id": "3f2b8c1e-...", "destination_id": "a91c04d2-...", "cost_km": "4.5" }
```

Respuesta 201:

```json
{ "origin_id": "3f2b8c1e-...", "destination_id": "a91c04d2-...", "cost_km": "4.5" }
```

### GET `/connections`

Respuesta 200:

```json
{ "connections": [ { "origin_id": "3f2b8c1e-...", "destination_id": "a91c04d2-...", "cost_km": "4.5" } ] }
```

### GET `/network`

Devuelve cada punto con sus conexiones salientes, que es la lista de adyacencia lista para leer. Incluye el nombre del destino para que sea comprensible sin consultar otro endpoint.

Respuesta 200:

```json
{
  "points": [
    {
      "id": "3f2b8c1e-...",
      "name": "Central warehouse",
      "type": "warehouse",
      "connections": [
        { "destination_id": "a91c04d2-...", "destination_name": "North", "cost_km": "4.5" }
      ]
    }
  ]
}
```

Un punto sin conexiones salientes aparece con `"connections": []`. Con la red vacía devuelve `{ "points": [] }`.

## Errores

Todos los errores tienen la misma forma:

```json
{ "error": { "code": "DUPLICATE_CONNECTION", "message": "Ya existe una conexión de 'A' a 'B'." } }
```

El campo `code` es estable y lo puede usar el script de aceptación; el `message` es para personas.

| Regla (diseno.md) | Situación | HTTP | `code` |
|---|---|---|---|
| P1, C1 | Falta un campo obligatorio, o el cuerpo no es JSON válido | 400 | `MISSING_DATA` |
| C5 | `cost_km` no es un texto decimal válido (letras, vacío, número JSON, infinito, NaN) | 400 | `INVALID_COST` |
| P2 | El nombre es vacío o solo espacios | 422 | `INVALID_NAME` |
| P3 | El tipo no está en la lista cerrada | 422 | `INVALID_TYPE` |
| C4 | Origen y destino son el mismo punto | 422 | `SELF_LOOP` |
| C6 | El costo es menor o igual que 0 | 422 | `NON_POSITIVE_COST` |
| C7 | El costo tiene más de 7 decimales | 422 | `COST_PRECISION` |
| C2 | El UUID de origen es inválido o no existe | 404 | `ORIGIN_NOT_FOUND` |
| C3 | El UUID de destino es inválido o no existe | 404 | `DESTINATION_NOT_FOUND` |
| C8 | Ya existe la conexión con el mismo origen y destino | 409 | `DUPLICATE_CONNECTION` |
| C9 | Existe la conexión inversa con un costo distinto | 409 | `INCONSISTENT_COST` |

Criterio de los códigos:

- **400:** la petición no tiene la forma esperada (falta algo o no se puede leer).
- **422:** la forma es correcta, pero el valor rompe una regla del negocio.
- **404:** un punto al que se hace referencia no existe.
- **409:** el dato choca con lo que ya está registrado en la red.

Alternativa considerada para C2 y C3: 422 en lugar de 404. Se eligió 404 porque el UUID identifica un recurso (el punto) y el mensaje de error dice cuál de los dos no existe.

### Ejemplo del sentido de las conexiones

Se parte de un punto A y un punto B que ya existen.

| Petición | Resultado | Motivo |
|---|---|---|
| A→B con `"4"` | 201 | Primera conexión entre ellos |
| A→B con `"4"` | 409 `DUPLICATE_CONNECTION` | Mismo sentido: duplicado |
| A→B con `"5"` | 409 `DUPLICATE_CONNECTION` | Mismo sentido: duplicado, aunque cambie el costo |
| B→A con `"6"` | 409 `INCONSISTENT_COST` | Sentido contrario, pero el costo no coincide con el registrado (4) |
| B→A con `"4"` | 201 | Sentido contrario con el mismo costo |

## Clase del núcleo (interfaz que consume la API)

La API no manipula el grafo directamente: delega todo en una clase `Graph` del núcleo, que no depende de Flask. Esta tabla define su interfaz. La implementación se hace en T13 a T19.

### Clases de datos

| Clase | Campos |
|---|---|
| `Point` | `id` (UUID), `name` (texto), `type` (`warehouse`, `neighborhood` o `pickup_point`) |
| `Connection` | `origin_id`, `destination_id`, `cost_km` (`Decimal`) |

### Clase `Graph`

Estado interno: los puntos por UUID y la lista de adyacencia `{origin_id: {destination_id: cost_km}}` (decisión T08).

| Método | Entrada | Devuelve | Errores que puede lanzar |
|---|---|---|---|
| `add_point` | `name`, `type` | `Point` con UUID nuevo | `InvalidName`, `InvalidType` |
| `list_points` | — | lista de `Point` | — |
| `add_connection` | `origin_id`, `destination_id`, `cost_km` | `Connection` | `OriginNotFound`, `DestinationNotFound`, `SelfLoop`, `InvalidCost`, `NonPositiveCost`, `CostPrecision`, `DuplicateConnection`, `InconsistentCost` |
| `list_connections` | — | lista de `Connection` | — |
| `neighbors` | `point_id` | destinos y costos de las conexiones salientes | `PointNotFound` |
| `readable_network` | — | cada punto con sus conexiones salientes | — |

`add_connection` valida en el orden definido en T09 (C2, C3, C4, costo, C8, C9).

### Errores del núcleo

Cada situación de rechazo es una excepción propia del núcleo, y una sola capa de la API las traduce a la tabla de errores de arriba. Así las reglas viven en un solo lugar y no se repiten en cada endpoint.

| Excepción | HTTP | `code` |
|---|---|---|
| `MissingData` | 400 | `MISSING_DATA` |
| `InvalidCost` | 400 | `INVALID_COST` |
| `InvalidName` | 422 | `INVALID_NAME` |
| `InvalidType` | 422 | `INVALID_TYPE` |
| `SelfLoop` | 422 | `SELF_LOOP` |
| `NonPositiveCost` | 422 | `NON_POSITIVE_COST` |
| `CostPrecision` | 422 | `COST_PRECISION` |
| `OriginNotFound` | 404 | `ORIGIN_NOT_FOUND` |
| `DestinationNotFound` | 404 | `DESTINATION_NOT_FOUND` |
| `DuplicateConnection` | 409 | `DUPLICATE_CONNECTION` |
| `InconsistentCost` | 409 | `INCONSISTENT_COST` |

`PointNotFound` (en `neighbors`) no se expone por ningún endpoint de F1. Queda disponible para F2 y F3.

### Implementación de los errores uniformes (T25)

- Las excepciones están en `backend/domain/errors.py` y todas heredan de `GraphError`. El núcleo las lanza con un mensaje en español y no sabe nada de HTTP.
- La traducción está en `backend/api/errors.py` (`HTTP_ERRORS`) y se registra una sola vez en `backend/app.py`. Los endpoints **no** capturan estas excepciones: las dejan subir.
- Para leer el cuerpo de un `POST`, los endpoints usan `json_body()`. Si el cuerpo falta, no es JSON válido o no es un objeto, responde 400 `MISSING_DATA`.

Códigos adicionales que no vienen de una regla de `diseno.md`, con la misma forma de error:

| Situación | HTTP | `code` |
|---|---|---|
| `PointNotFound` (reservado para F2 y F3) | 404 | `POINT_NOT_FOUND` |
| La ruta no existe | 404 | `NOT_FOUND` |
| El método no está permitido en la ruta | 405 | `METHOD_NOT_ALLOWED` |
| Error inesperado del servidor (sin detalles internos) | 500 | `INTERNAL_ERROR` |

## Puntos para revisar por el equipo

- El costo como texto y el rechazo del número JSON.
- La elección de 404 para origen o destino inexistente.
- La ausencia de prefijo `/api` en las rutas.
- Los mensajes de error (`message`) quedan en español; si el equipo prefiere inglés, solo cambia ese texto.
