# Equipo — RutaPyme

## Integrantes

| Integrante | Rol general |
|---|---|
| Jacobo | Núcleo del grafo y algoritmos de recorrido |
| Mariana | Casos borde, errores y verificación del núcleo |
| Carolina | Contrato de la API, endpoints e interfaz |
| Jose | Script de aceptación, README y pruebas |

## Responsables de pitch

| Feature | Pitch | Estado |
|---|---|---|
| F1 · Red operativa | Jacobo | Expuesto |
| F2 · Cobertura de entregas | Carolina | Pendiente |
| F3 · Ruta de menor costo | Por definir (Mariana o Jose) | Pendiente |
| F4 · Operación demostrable | Por definir | Pendiente |

Regla de la guía: nadie repite pitch hasta que todos hayan expuesto.

## Reparto de Feature 2

| Persona | Tareas | Min. estimados |
|---|---|---|
| Jacobo | T01, T04, T05, T08, T11, T12, T23, T30 | 365 |
| Mariana | T07, T09, T13, T14, T15, T16, T18, T20 | 270 |
| Carolina | T02, T06, T10, T17, T21, T22, T31 | 365 |
| Jose | T03, T19, T24, T25, T26, T27, T28 | 295 |
| Todos | T29, T32, T33 | por persona |

Cada tarea tiene su Issue en GitHub (#52 a #84), con el responsable en el título.

## Revisiones cruzadas

| Quién revisa | Qué revisa |
|---|---|
| Jose | Recorrido de Jacobo, ejecutando el script (T19) |
| Carolina | Manejo de errores de Mariana (T14 y T18) |
| Jacobo | Endpoint y pantalla de Carolina (T17, T21 y T22) |
| Mariana | Escenarios del script de Jose frente a los casos borde (T26) |

## Convención de ramas y commits

- Rama por feature y por integrante: `feat-N/Nombre` (por ejemplo, `feat-1/Caro`, `feat-2/Caro`).
- Commits en formato convencional: `tipo(ámbito): descripción en imperativo`, en inglés, con el cuerpo en español cuando haga falta.
- Cada commit referencia su Issue con `Refs #N`.
