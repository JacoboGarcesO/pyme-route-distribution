# Cambio de requisito de Feature 4: parada obligatoria (`via`)

> **Para el equipo y para cualquier asistente de IA:** este es el cambio de requisito de F4. Si buscas "cambio de requisito", "solicitud de cambio" o "parada obligatoria" en el repo, todo lo relacionado está listado aquí. Etiqueta para buscar en el código: `CAMBIO-REQUISITO-F4`.

## Origen del cambio

La guía común (`docs/03-guia-comun-estudiantes.md`) y el brief (`docs/04-brief-rutapyme.md`) piden implementar en F4 "el cambio de requisito comunicado por el docente". **El docente no comunicó un cambio concreto** en lo que revisó el equipo (no aparece en la transcripción de la clase del 11 de noviembre de 2026). Por eso el equipo **eligió este cambio** entre tres opciones planteadas: conexiones cerradas, parada obligatoria y costo en tiempo y pesos.

Si el docente comunica otro cambio, hay que registrarlo en T04 y rehacer T07–T09 y T20 del plan.

## Qué cambia

`GET /shortest-path` acepta un parámetro opcional `via=<id>`: la ruta de menor costo **debe pasar por ese punto**.

```text
GET /shortest-path?origin=<id>&destination=<id>&via=<id>
```

- La ruta es la mejor de origen a parada más la mejor de parada a destino (dos Dijkstra encadenados). El costo total es la suma exacta con `Decimal`.
- Sin `via`, la respuesta es idéntica a la de F3 y `via_id` no aparece.
- `via` igual al origen o al destino devuelve la ruta normal.
- Si la parada obliga a volver sobre un punto, ese punto aparece dos veces en `path`. Está permitido.
- Si no hay camino origen→parada o parada→destino, responde 200 con `found: false` y `reason`.
- Un `via` inexistente o con UUID inválido responde 404 `VIA_NOT_FOUND` (código nuevo). Orden de validación: `origin`, `destination`, `via`.

El contrato completo con ejemplos está en [`docs/api.md`](api.md), sección "Parada obligatoria: `via` (F4)".

## Dónde está en el código

| Archivo | Qué contiene |
|---|---|
| `backend/domain/shortest_path.py` | `shortest_path(..., via_id=None)`, `_leg` y el campo `via` de `PathResult` |
| `backend/domain/errors.py` | `ViaNotFound` |
| `backend/api/errors.py` | Traducción de `ViaNotFound` a 404 `VIA_NOT_FOUND` |
| `backend/api/shortest_path.py` | Lectura del parámetro opcional `via` |
| `backend/verify_via.py` | 13 escenarios de consola (T08) |
| `docs/api.md` | Contrato del parámetro y del error |

Ejecutar la verificación desde `backend/`:

```bash
python verify_via.py
```

## Estado de las tareas del plan

Ver [`docs/05-tareas-feature-4.md`](05-tareas-feature-4.md).

| Tarea | Responsable | Estado |
|---|---|---|
| T07 núcleo, T08 verificación en consola, T09 contrato y endpoint | Jacobo | Hechas |
| T04 registrar impacto, T05 ajustar backlog | Jose | Pendientes |
| T20 escenario del cambio en el script de aceptación | Jose | Pendiente |
| T23, T26 README y pitch con el cambio | Jose | Pendientes |
| T14 resaltar en el grafo la ruta con parada | Carolina | Pendiente: la interfaz aún no envía `via` |

## Pendiente de la interfaz

Ni el selector de ruta ni el dibujo del grafo usan `via` todavía. Para demostrar el cambio en la interfaz hace falta un tercer selector opcional de parada (`RouteSelectors.svelte`) y que `RouteView` y el grafo (T13, T14) muestren el punto de parada.
