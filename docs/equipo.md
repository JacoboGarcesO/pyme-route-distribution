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
