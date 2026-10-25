# Equipo y forma de trabajo — Feature 1

## Integrantes y aportes

| Persona | Rama | Aportes en la Feature 1 |
|---|---|---|
| Jacobo | `feat-1/jacobo` | Decisiones de modelado (T06 a T09), contrato de la API (T10), mapa de ejemplo (T11), traza manual (T12), integración de los PR, endpoints de conexiones (T23), cierre de la feature |
| Mariana | `feat-1/Mariana` | Núcleo del grafo: `Graph`, `Point`, `Connection`, excepciones y reglas C1 a C9 (T13 a T20), endpoints de puntos (T22) y capa de errores (T25) |
| Carolina | `feat-1/Caro` | Decisión de framework (T21), `GET /network` (T24), errores uniformes (T25), frontend Svelte con proxy de Vite, formularios y vista de la red (T26 a T28) |
| Jose | `feat-1/jose` | Script de aceptación (T29 a T31) y README (T33) |

El detalle de cada commit y de cada revisión está en los PR de GitHub (#38 a #42 y los que sigan).

## Responsables de la entrega

| Entregable | Responsable |
|---|---|
| Pitch de la Feature 1 | Jacobo |
| Video de respaldo (máximo 3 minutos) | Jacobo |
| Bitácora de IA | Cada persona registra sus propias filas en `docs/bitacora-ia.md` |
| Coevaluación | Cada persona, de forma individual y confidencial |

Según la guía común, quien expone no repite hasta que todos hayan expuesto, salvo autorización docente.

## Ramas y commits

- Cada persona trabaja en su rama `feat-1/<nombre>`.
- `feature1` es la rama de integración de la Feature 1. Todo entra a ella mediante pull request, nunca con un merge local.
- Los PR se fusionan con merge commit, en este orden cuando hay dependencias: núcleo, API, frontend y pruebas.
- Si un PR entra en conflicto, se resuelve en la rama del PR trayendo `feature1`, se explica en el PR y se vuelve a fusionar por GitHub.
- Los mensajes de commit siguen el estilo `tipo(ámbito): descripción`, con tipos como `feat`, `fix`, `docs`, `refactor` y `merge`.

## Revisión cruzada

Cada PR lo revisa otra persona del equipo antes de darse por cerrado:

| Autor | Revisor |
|---|---|
| Jacobo | Mariana |
| Mariana | Jacobo |
| Carolina | Jose |
| Jose | Carolina |

---

# Feature 2 — Cobertura de entregas

## Responsables

| Entregable | Responsable |
|---|---|
| Pitch de la Feature 2 | Carolina |
| Video de respaldo (máximo 3 minutos) | Jacobo |
| Bitácora de IA | Cada persona registra sus propias filas en `docs/bitacora-ia.md` |
| Coevaluación | Cada persona, de forma individual y confidencial |

Regla de la guía: nadie repite pitch hasta que todos hayan expuesto. Jacobo expuso F1, así que F2 le corresponde a Carolina.

## Reparto

| Persona | Tareas | Min. estimados |
|---|---|---|
| Jacobo | T01, T04, T05, T08, T11, T12, T23, T30 | 365 |
| Mariana | T07, T09, T13, T14, T15, T16, T18, T20 | 270 |
| Carolina | T02, T06, T10, T17, T21, T22, T31 | 365 |
| Jose | T03, T19, T24, T25, T26, T27, T28 | 295 |
| Todos | T29, T32, T33 | por persona |

Cada tarea tiene su Issue en GitHub (#52 a #84), con el responsable en el título.

## Revisión cruzada

| Quién revisa | Qué revisa |
|---|---|
| Jose | Recorrido de Jacobo, ejecutando el script (T19) |
| Carolina | Manejo de errores de Mariana (T14 y T18) |
| Jacobo | Endpoint y pantalla de Carolina (T17, T21 y T22) |
| Mariana | Escenarios del script de Jose frente a los casos borde (T26) |
