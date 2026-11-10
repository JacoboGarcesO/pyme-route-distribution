# Feature 3 — Ruta de menor costo: plan de tareas

Cada tarea debe caber en máximo 1 hora. Las tareas marcadas con **[DECISIÓN]** requieren justificar la elección en `docs/diseno.md` y en el pitch.

Estados sugeridos: `[ ]` pendiente · `[~]` en curso · `[x]` hecha.

**Precondición:** F2 integrada en `main` y con tag `f2`. F3 reutiliza `Graph`, la lista de adyacencia, los costos `Decimal` y los errores definidos en las features anteriores.

## Objetivo y alcance

El despachador debe solicitar una ruta entre dos puntos y recibir la secuencia de puntos junto con el costo total mínimo. La ruta debe respetar el sentido de las conexiones y los costos positivos registrados.

F3 no incluye tráfico en tiempo real, vehículos múltiples, optimización de varias entregas ni cambios de costos durante la consulta.

## Reparto asignado

El trabajo queda asignado de forma estratégica y secuencial. Jose toma las decisiones importantes y el cierre final; Carolina, Jacobo y Mariana ejecutan principalmente funciones operativas de preparación, desarrollo, integración y pruebas.

| Orden | Persona | Responsabilidad principal | Tareas | Total |
|---|---|---|---|---:|
| 1 | **Carolina** | Organización operativa, preparación de datos e integración visual | T01–T03, T06–T07, T21–T22 | 8 |
| 2 | **Jacobo** | Implementación operativa del algoritmo y núcleo | T08–T14 | 7 |
| 3 | **Mariana** | Implementación operativa de API, interfaz y pruebas | T15–T18, T20, T23–T24 | 8 |
| 4 | **Jose** | Decisiones importantes, verificación final, documentación y entrega | T04–T05, T19, T25–T33 | 12 |

### Secuencia de trabajo

1. **Carolina** prepara la rama, backlog, datos y componentes operativos de la interfaz.
2. **Jacobo** implementa el algoritmo de menor costo, la reconstrucción de la ruta y las pruebas del núcleo.
3. **Mariana** implementa el contrato REST, endpoint, errores, consulta visual y pruebas iniciales.
4. **Jose** define las decisiones importantes, verifica el funcionamiento real de la API y completa los escenarios de aceptación, evidencia, README, bitácora, video, pitch, PR, tag y coevaluación.

La verificación de Jose es una revisión cruzada obligatoria: debe comprobar que la API real devuelve la ruta de menor costo, que respeta los errores definidos y que no selecciona simplemente la ruta con menos saltos.

| Área | Responsabilidad sugerida |
|---|---|
| Modelado y algoritmo | Comparar algoritmos, hacer la traza y desarrollar el núcleo |
| Contrato y API | Diseñar y exponer el endpoint de ruta |
| Interfaz | Integrar la consulta y mostrar la ruta |
| Pruebas y documentación | Script de aceptación, evidencia y README |
| Todo el equipo | Revisión, bitácora de IA, pitch y coevaluación |

## Bloque 0 — Organización

### [ ] T01 · Crear la rama de la feature (20 min) · **Carolina**
- **Entregable:** rama `feat-3/ruta-menor-costo` creada desde `main` con F2 integrada.
- **Hecho cuando:** la rama existe y parte del tag `f2`.

### [ ] T02 · Registrar pitch y reparto de F3 (20 min) · **Carolina**
- **Entregable:** actualización de `docs/equipo.md` con responsable del pitch y tareas asignadas.
- **Hecho cuando:** el reparto cumple las reglas de participación del curso.

### [x] T03 · Cargar el backlog en GitHub (40 min) · **Carolina**
- **Entregable:** una Issue por tarea, con bloque y responsable.
- **Hecho cuando:** todas aparecen en el tablero.

## Bloque 1 — Modelado y algoritmo

### [x] T04 · [DECISIÓN] Elegir el algoritmo de menor costo (45 min) · **Jose**
- **Alternativas:** Dijkstra u otra alternativa compatible con pesos estrictamente positivos.
- **Entregable:** comparación en `docs/diseno.md` incluyendo restricciones, complejidad, estructura de datos y motivo de la elección.
- **Hecho cuando:** se explica por qué el algoritmo sirve para costos positivos y por qué BFS no resuelve esta necesidad.

### [x] T05 · [DECISIÓN] Definir el contrato conceptual de la ruta (30 min) · **Jose**
- **Entregable:** reglas para origen igual a destino, ruta inexistente, costo total, desempates y orden de la secuencia.
- **Hecho cuando:** cada caso tiene un resultado esperado.

### [x] T06 · Diseñar el caso de demostración (45 min) · **Carolina**
- **Entregable:** red pequeña con al menos dos alternativas entre origen y destino: una con menos saltos pero mayor costo y otra con más saltos pero menor costo.
- **Hecho cuando:** la elección del algoritmo puede demostrarse con una traza manual.

### [x] T07 · Traza manual del algoritmo (60 min) · **Carolina**
- **Entregable:** tabla en `docs/diseno.md` con costos tentativos, nodo seleccionado, actualizaciones y predecesores.
- **Hecho cuando:** se reconstruye la ruta final y se comprueba su costo acumulado.

### [x] T08 · Definir casos borde (30 min) · **Jacobo**
- **Entregable:** lista con origen inexistente, destino inexistente, red vacía, origen igual a destino, ruta inexistente, nodo aislado, ciclo y costos positivos con decimales.
- **Hecho cuando:** cada caso tiene respuesta, mensaje y código esperado.

## Bloque 2 — Núcleo Python

### [x] T09 · Diseñar el resultado de ruta (30 min) · **Jacobo**
- **Entregable:** modelo o estructura con origen, destino, secuencia de puntos, costo total y, si aplica, explicación.
- **Hecho cuando:** puede serializarse sin perder precisión decimal.

### [x] T10 · Implementar la búsqueda de menor costo (60 min) · **Jacobo**
- **Entregable:** función en `backend/domain/shortest_path.py` que use la lista de adyacencia y pesos `Decimal`.
- **Hecho cuando:** devuelve el costo mínimo y no confunde menor número de saltos con menor costo.

### [x] T11 · Guardar predecesores y reconstruir la ruta (60 min) · **Jacobo**
- **Entregable:** reconstrucción de la secuencia desde el destino hasta el origen.
- **Hecho cuando:** la ruta devuelta contiene los puntos en orden origen→destino.

### [x] T12 · Validar origen, destino y ruta inexistente (45 min) · **Jacobo**
- **Entregable:** reutilización de errores existentes para puntos inexistentes y resultado claro para una ruta no encontrada.
- **Hecho cuando:** no se confunde un error de entrada con una decisión válida de negocio.

### [x] T13 · Verificar precisión y costos acumulados (45 min) · **Jacobo**
- **Entregable:** pruebas del uso de `Decimal`, costos positivos y suma exacta.
- **Hecho cuando:** los resultados conservan el formato definido por la API.

### [x] T14 · Verificación del núcleo en consola (45 min) · **Jacobo**
- **Entregable:** script que ejercite el caso normal y todos los casos borde de T08.
- **Hecho cuando:** imprime esperado, obtenido y PASÓ/FALLÓ.

## Bloque 3 — API REST

### [x] T15 · Diseñar el contrato de `GET /shortest-path` (45 min) · **Mariana**
- **Entregable:** sección en `docs/api.md` con parámetros, respuestas y errores.
- **Propuesta:** `GET /shortest-path?origin=<id>&destination=<id>`.
- **Hecho cuando:** incluye ejemplos JSON y códigos HTTP para cada caso de T08.

### [x] T16 · Implementar el endpoint de ruta (60 min) · **Mariana**
- **Entregable:** endpoint conectado al grafo real de la aplicación.
- **Hecho cuando:** una consulta normal devuelve secuencia y costo mínimo.

### [x] T17 · Traducir errores y respuestas de negocio (45 min) · **Mariana**
- **Entregable:** errores uniformes para parámetros faltantes, origen/destino inexistentes y ruta inexistente.
- **Hecho cuando:** los códigos y mensajes coinciden con `docs/api.md`.

### [x] T18 · Probar el endpoint con la red de demostración (45 min) · **Mariana**
- **Entregable:** ejecución documentada con las dos rutas alternativas.
- **Hecho cuando:** la API selecciona la de menor costo aunque tenga más saltos.

## Bloque 4 — Interfaz

### [x] T19 · [DECISIÓN] Ubicar la consulta de ruta (30 min) · **Jose**
- **Entregable:** decisión en `docs/diseno.md` sobre sección o pantalla, reutilizando componentes y cliente existentes.
- **Hecho cuando:** queda claro cómo se integra con la cobertura de F2.

### [x] T20 · Crear selectores de origen y destino (45 min) · **Mariana**
- **Entregable:** controles alimentados por los puntos reales del backend.
- **Hecho cuando:** no dependen de identificadores escritos manualmente.

### [x] T21 · Mostrar ruta y costo total (60 min) · **Carolina**
- **Entregable:** vista de la secuencia, costo total y conexiones recorridas.
- **Hecho cuando:** el usuario puede entender por qué se eligió esa ruta.

### [x] T22 · Mostrar errores y ruta inexistente (45 min) · **Carolina**
- **Entregable:** mensajes comprensibles para puntos inválidos, falta de conexión y datos incompletos.
- **Hecho cuando:** cada respuesta de la API tiene una representación clara en la interfaz.

## Bloque 5 — Script de aceptación

### [x] T23 · Preparar el esqueleto del script (45 min) · **Mariana**
- **Entregable:** script en `acceptance/` con reporte común de escenario, esperado, obtenido y resultado.

### [x] T24 · Probar escenario normal (45 min) · **Mariana**
- **Escenario:** dos rutas posibles con distinto número de saltos y costo.
- **Hecho cuando:** comprueba la secuencia y el costo mínimo.

### [x] T25 · Probar escenarios de ausencia de ruta y red vacía (45 min) · **Jose**
- **Hecho cuando:** distingue una ruta inexistente de una respuesta exitosa.

### [x] T26 · Probar errores de entrada (60 min) · **Jose**
- **Escenarios:** origen inexistente, destino inexistente, parámetros faltantes y destino igual al origen, según la decisión de T05.
- **Hecho cuando:** comprueba códigos y mensajes esperados.

### [x] T27 · Ejecutar y guardar evidencia (30 min) · **Jose**
- **Entregable:** salida completa en `docs/evidencia-f3.txt`.
- **Hecho cuando:** corre desde un estado limpio sin intervención manual.

## Bloque 6 — Cierre

### [x] T28 · Actualizar README (45 min) · **Jose**
- **Entregable:** propósito de F3, endpoint, ejecución, ejemplo y decisiones del diseño.

### [x] T29 · Actualizar bitácora de IA (45 min) · **Jose**
- **Entregable:** una fila por decisión o pieza desarrollada con apoyo de IA, incluyendo verificación propia.

### [~] T30 · Preparar video de respaldo (60 min) · **Jose**
- **Entregable:** video de máximo 3 minutos con ruta normal, menor costo frente a menos saltos y ruta inexistente.
- **Preparación:** el guion está en `docs/video-f3.md`; falta grabar y enlazar el video real.

### [x] T31 · Preparar el pitch (60 min) · **Jose**
- **Entregable:** guion con problema, grafo, algoritmo, complejidad, reconstrucción de ruta, caso borde, pruebas y aportes.
- **Preparación:** el guion está en `docs/pitch-f3.md`.

### [ ] T32 · Pull request, revisión y tag (45 min) · **Jose**
- **Entregable:** PR revisado y mezclado, con tag `f3` y aportes enlazados.

### [ ] T33 · Coevaluación confidencial (20 min) · **Jose**
- **Entregable:** coevaluación enviada según la instrucción docente.

## Criterio de aceptación de la feature

En una demo, el despachador selecciona dos puntos, el sistema devuelve una ruta válida de menor costo y su costo acumulado, respeta las conexiones dirigidas, elige menor costo aunque implique más saltos y responde claramente cuando la ruta no existe o los puntos no son válidos.
