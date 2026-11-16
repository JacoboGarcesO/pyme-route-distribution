# Feature 4 — Operación demostrable: plan de tareas

Cada tarea debe caber en máximo 1 hora. Las tareas marcadas con **[DECISIÓN]** requieren justificar la elección en `docs/diseno.md` y en el pitch.

Estados sugeridos: `[ ]` pendiente · `[~]` en curso · `[x]` hecha.

**Precondición:** F3 integrada en `main` y con tag `f3`. F4 reutiliza `Graph`, cobertura, ruta de menor costo, errores y componentes de interfaz ya existentes.

## Objetivo y alcance

El despachador registra una red pequeña, verifica cobertura, solicita una ruta, entiende por qué se seleccionó (viéndola en la red) y obtiene una respuesta correcta ante datos inválidos o falta de conexión. F4 también incorpora el cambio de requisito comunicado por el docente.

**Cambio de requisito elegido por el equipo (detalle en [`docs/cambio-requisito-f4.md`](cambio-requisito-f4.md)):** parada obligatoria. `GET /shortest-path` acepta `via=<id>` y la ruta debe pasar por ese punto (T04–T09, T20).

F4 no incluye algoritmos nuevos fuera del cambio de requisito, tráfico en tiempo real ni más de una entrega por consulta. NetworkX, si se usa, solo dibuja datos ya calculados por el backend.

## Reparto asignado

| Orden | Persona | Responsabilidad principal | Tareas | Total |
|---|---|---|---|---:|
| 1 | **Carolina** | Organización, integración de la pantalla y resaltado visual | T01–T03, T12, T14–T16 | 7 |
| 2 | **Jacobo** | Cambio de requisito en el núcleo, API y datos del dibujo | T07–T09, T11, T17 | 5 |
| 3 | **Mariana** | Interfaz que muestra la red o el grafo | T13 | 1 |
| 4 | **Jose** | Decisiones, verificación final, evidencia, documentación y entrega | T04–T06, T10, T18–T23, T25–T27 | 13 |
| — | **Todos** | Bitácora de IA propia (T24) y coevaluación (parte de T27) | T24, T27 | — |

### Secuencia de trabajo

1. **Carolina** prepara la rama, el reparto y el backlog.
2. **Jose** registra la solicitud de cambio, su impacto y las decisiones de F4 (T04–T06, T10).
3. **Jacobo** implementa el cambio de requisito y expone en la API los datos que necesita el dibujo.
4. **Mariana** crea la interfaz que dibuja la red a partir de `GET /network` (T13).
5. **Carolina** integra todo en una sola pantalla y resalta cobertura y ruta sobre el dibujo.
6. **Jose** verifica con la API y la interfaz reales, completa el script de aceptación, la evidencia y el cierre.

T13 depende de T10 y T11. T14 y T15 dependen de T13.

## Bloque 0 — Organización

### [ ] T01 · Crear la rama de la feature (20 min) · **Carolina**
- **Entregable:** rama `feat-4/operacion-demostrable` creada desde `main` con el tag `f3`.
- **Hecho cuando:** la rama existe y parte del tag `f3`.

### [ ] T02 · Registrar pitch y reparto de F4 (20 min) · **Carolina**
- **Entregable:** actualización de `docs/equipo.md` con responsable del pitch y tareas asignadas.
- **Hecho cuando:** el reparto cumple las reglas de participación del curso.

### [ ] T03 · Cargar el backlog en GitHub (40 min) · **Carolina**
- **Entregable:** una Issue por tarea, con bloque y responsable.
- **Hecho cuando:** todas aparecen en el tablero.

## Bloque 1 — Cambio de requisito

### [ ] T04 · [DECISIÓN] Registrar la solicitud de cambio y su impacto (45 min) · **Jose**
- **Entregable:** sección en `docs/diseno.md` con el cambio comunicado por el docente, qué módulos toca (grafo, algoritmo, API, interfaz, pruebas) y su costo estimado.
- **Hecho cuando:** el impacto queda escrito antes de tocar el código.

### [ ] T05 · [DECISIÓN] Ajustar backlog y alcance (30 min) · **Jose**
- **Entregable:** tareas nuevas o modificadas en este plan, y qué queda fuera, con justificación.
- **Hecho cuando:** ninguna funcionalidad extra queda sin costo y valor justificados.

### [ ] T06 · [DECISIÓN] Definir "costo inválido" y respuestas (30 min) · **Jose**
- **Entregable:** reglas y código de error para costo cero, negativo, no numérico y ausente, alineadas con `InvalidCost`.
- **Hecho cuando:** cada caso tiene código HTTP, código de error y mensaje.

### [x] T07 · Implementar el cambio de requisito en el núcleo (60 min) · **Jacobo**
- **Entregable:** cambio en `backend/domain/` según T04–T05, sin romper F1–F3.
- **Hecho cuando:** las verificaciones de consola de F2 y F3 siguen pasando.

### [x] T08 · Probar el cambio en consola (45 min) · **Jacobo**
- **Entregable:** casos normal y borde del cambio en un script `backend/verify_*.py`.
- **Hecho cuando:** imprime esperado, obtenido y PASÓ/FALLÓ.

### [x] T09 · Adaptar contrato y endpoint (60 min) · **Jacobo**
- **Entregable:** cambio en `backend/api/` y sección actualizada de `docs/api.md`.
- **Hecho cuando:** la API real responde según el contrato nuevo.

## Bloque 2 — Datos para visualizar

### [ ] T10 · [DECISIÓN] Cómo se dibuja la red (30 min) · **Jose**
- **Entregable:** decisión en `docs/diseno.md`: SVG propio o imagen de NetworkX, de dónde salen las posiciones de los puntos y cómo se marca una ruta.
- **Hecho cuando:** se explica que el dibujo usa solo datos calculados por el backend.
- **Nota:** existe la rama `feat-4/network-map` con posiciones `x, y`; evaluar si se rescata.

### [x] T11 · Exponer en `GET /network` los datos del dibujo (45 min) · **Jacobo**
- **Entregable:** posiciones u otro dato acordado en T10, validado en el núcleo.
- **Hecho cuando:** `GET /network` devuelve todo lo necesario para dibujar nodos y flechas, con la red vacía como caso válido.

## Bloque 3 — Interfaz

### [ ] T12 · Integrar configuración, cobertura y ruta en una pantalla (60 min) · **Carolina**
- **Entregable:** `App.svelte` con las tres operaciones y un único refresco de datos.
- **Hecho cuando:** crear un punto o conexión actualiza selectores, lista y dibujo sin recargar.

### [ ] T13 · Crear la interfaz que muestra la red o el grafo (60 min) · **Mariana**
- **Entregable:** componente Svelte nuevo (por ejemplo `frontend/src/lib/NetworkGraph.svelte`) que dibuja los puntos y las conexiones dirigidas con su costo a partir de `GET /network`.
- **Hecho cuando:** se distinguen conexiones de un solo sentido y de doble sentido, se ve el costo de cada una y la red vacía muestra un mensaje en lugar de un dibujo roto.

### [ ] T14 · Resaltar la ruta calculada en el grafo (45 min) · **Carolina**
- **Entregable:** el resultado de `GET /shortest-path` marca puntos y tramos sobre el dibujo de T13.
- **Hecho cuando:** el usuario ve por qué se eligió la ruta y su costo total.

### [ ] T15 · Resaltar puntos alcanzables en el grafo (45 min) · **Carolina**
- **Entregable:** el resultado de `GET /coverage` marca alcanzables y no alcanzables sobre el dibujo.
- **Hecho cuando:** un punto aislado se ve distinto de uno alcanzable.

### [ ] T16 · Mostrar errores de F4 en la interfaz (45 min) · **Carolina**
- **Entregable:** mensajes para nodo inexistente, ruta inexistente y costo inválido, según T06.
- **Hecho cuando:** cada respuesta de error de la API tiene una representación clara.

## Bloque 4 — Script de aceptación

### [x] T17 · Esqueleto y escenario normal (45 min) · **Jacobo**
- **Entregable:** `acceptance/scripts/acceptance_feature_4.py` reutilizando el reporte común; escenario: red pequeña, cobertura y ruta.
- **Hecho cuando:** comprueba secuencia y costo mínimo.

### [ ] T18 · Escenarios de ruta inexistente y nodo inexistente (45 min) · **Jose**
- **Hecho cuando:** distingue una ruta inexistente de un nodo inexistente y de una respuesta exitosa.

### [ ] T19 · Escenario de costo inválido (45 min) · **Jose**
- **Hecho cuando:** comprueba códigos y mensajes definidos en T06.

### [ ] T20 · Escenario del cambio de requisito (45 min) · **Jose**
- **Hecho cuando:** demuestra el comportamiento nuevo de T07–T09.

### [ ] T21 · Ejecutar y guardar evidencia (30 min) · **Jose**
- **Entregable:** salida completa en `docs/evidencia-f4.txt`.
- **Hecho cuando:** corre desde un estado limpio sin intervención manual.

### [ ] T22 · Verificación cruzada con la interfaz real (45 min) · **Jose**
- **Entregable:** recorrido del flujo completo del cliente en el navegador, con notas de lo encontrado.
- **Hecho cuando:** se comprueba el criterio de éxito del cliente de punta a punta.

## Bloque 5 — Cierre

### [ ] T23 · Actualizar README (45 min) · **Jose**
- **Entregable:** propósito de F4, ejecución, ejemplo de demo y decisiones, incluido el cambio de requisito.

### [ ] T24 · Actualizar bitácora de IA (45 min por persona) · **Todos**
- **Entregable:** una fila por decisión o pieza desarrollada con apoyo de IA, con verificación propia.

### [ ] T25 · Preparar video de respaldo (60 min) · **Jose**
- **Entregable:** video de máximo 3 minutos con la red dibujada, cobertura, ruta y un error.

### [ ] T26 · Preparar el pitch (60 min) · **Jose**
- **Entregable:** guion con problema, grafo, algoritmos, visualización, cambio de requisito, pruebas y aportes.

### [ ] T27 · Pull request, revisión, tag y coevaluación (45 min) · **Jose** (coevaluación: **Todos**)
- **Entregable:** PR revisado y mezclado, con tag `f4`, aportes enlazados y coevaluación confidencial enviada.

## Criterio de aceptación de la feature

En una demo, el despachador registra una red pequeña, la ve dibujada, verifica cobertura, solicita una ruta, entiende por qué se seleccionó, ve el cambio de requisito funcionando y recibe respuestas correctas ante datos inválidos o falta de conexión.
