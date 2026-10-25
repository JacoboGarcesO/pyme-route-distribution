# Feature 2 — Cobertura de entregas: plan de tareas

Cada tarea cabe en **máximo 1 hora**. Las tareas marcadas con **[DECISIÓN]** requieren elegir entre alternativas; la elección y su justificación se escriben en `docs/diseno.md` (sirven para el README y el pitch).

Estados sugeridos: `[ ]` pendiente · `[~]` en curso · `[x]` hecha.

**Precondición:** F1 integrada en `main` y con tag `f1`. F2 usa la clase `Graph`, la representación de adyacencia de `diseno.md` (T08) y los errores de `backend/domain/errors.py`.

**Pitch de F2:** Carolina (Jacobo expuso F1, así que no repite).

---

## Reparto propuesto

Propuesta para validar en equipo. Cada integrante tiene una decisión o núcleo, una prueba o revisión y una parte funcional, como exige la guía.

| Persona | Rol principal en F2 | Tareas | Min. estimados |
|---|---|---|---|
| **Jacobo** | Algoritmo y núcleo de recorrido | T01, T04, T05, T08, T11, T12, T23, T30 | 365 |
| **Mariana** | Casos borde, errores y pendientes de la red | T07, T09, T13, T14, T15, T16, T18, T20 | 270 |
| **Carolina** | Contrato, endpoint, interfaz y pitch | T02, T06, T10, T17, T21, T22, T31 | 365 |
| **Jose** | Script de aceptación, README y pruebas | T03, T19, T24, T25, T26, T27, T28 | 295 |
| **Todos** | Bitácora, revisión de PR y coevaluación | T29, T32, T33 | por persona |

### Revisiones cruzadas (una prueba o revisión por persona)

| Quién revisa | Qué revisa | Tarea |
|---|---|---|
| Jose | Recorrido y orden de visita de Jacobo (ejecutando el script) | T19 |
| Carolina | Manejo de errores de Mariana (origen, destino, parámetros) | T14 y T18 |
| Jacobo | Endpoint y pantalla de Carolina | T17, T21 y T22 |
| Mariana | Escenarios del script de Jose frente a los casos borde de T09 | T26 |

---

## Bloque 0 — Organización

### [ ] T01 · Crear la rama de la feature (20 min) · *Jacobo*
- **Entregable:** rama `feat-2/cobertura` creada desde `main` con F1 integrada.
- **Hecho cuando:** la rama existe en remoto.

### [ ] T02 · Registrar pitch y reparto de F2 (20 min) · *Carolina*
- **Entregable:** actualizar `docs/equipo.md` con el responsable del pitch (Carolina) y el reparto de la tabla de arriba.
- **Hecho cuando:** cada integrante aparece con al menos una decisión, una prueba o revisión y una parte funcional.

### [ ] T03 · Cargar el backlog en GitHub (40 min) · *Jose*
- **Entregable:** una Issue por cada tarea de este documento, con etiqueta de bloque y responsable.
- **Hecho cuando:** el tablero muestra todas las tareas en "Por hacer".

---

## Bloque 1 — Modelado en papel (guía, pasos 2 y 3)

### [ ] T04 · [DECISIÓN] Algoritmo de recorrido: BFS o DFS (45 min) · *Jacobo*
- **Alternativas:** recorrido por capas (BFS) o exploración profunda (DFS).
- **Entregable:** sección en `docs/diseno.md` que compare ambos para la pregunta "¿qué destinos se alcanzan desde una bodega?". Incluir: orden de visita, memoria, complejidad y qué información extra da cada uno (por ejemplo, número de saltos con BFS).
- **Hecho cuando:** la decisión responde por qué el algoritmo sirve para cobertura y no para ruta más barata (eso es F3).

### [ ] T05 · [DECISIÓN] Qué significa "alcanzable" (30 min) · *Jacobo*
- **Entregable:** párrafo en `docs/diseno.md` que fije las reglas:
  - el recorrido sigue el sentido de cada arista (A→B permite ir de A a B, nunca de B a A);
  - el origen cuenta como alcanzable desde sí mismo o no (decidirlo);
  - los costos no influyen: solo importa si existe un camino.
- **Hecho cuando:** el párrafo responde "si B→C existe pero no C→B, ¿C es alcanzable desde B?" con un ejemplo de la red.

### [ ] T06 · [DECISIÓN] Respuestas válidas frente a errores (45 min) · *Carolina*
- **Entregable:** en `docs/diseno.md`, separar qué es una respuesta de negocio y qué es un error:
  - destino no alcanzable: respuesta válida con explicación (propuesta: 200 con `reachable: false`);
  - origen o destino inexistente, red vacía: error (propuesta: 404 con código de F1);
  - falta el origen: error 400 `MISSING_DATA`.
- **Hecho cuando:** cada caso de la lista del brief tiene un resultado definido.

### [ ] T07 · Agregar un punto aislado a la red de ejemplo (30 min) · *Mariana*
- **Objetivo:** tener un destino desconectado para la demo y la prueba.
- **Entregable:** punto sin aristas de entrada ni de salida en el mapa de F1 (por ejemplo, una casa "D" fuera de la red), anotado en `docs/diseno.md`.
- **Hecho cuando:** `D` existe en la red pero ningún recorrido desde `BOD` lo alcanza.

### [ ] T08 · Traza manual del recorrido (60 min) · *Jacobo*
- **Entregable:** en `docs/diseno.md`, el orden de visita paso a paso desde `BOD` con la red de F1, con la cola o las capas en cada paso, y la decisión final para `D`.
- **Hecho cuando:** otra persona puede reproducir el orden de visita solo leyendo la traza.

### [ ] T09 · Lista de casos borde (30 min) · *Mariana*
- **Entregable:** lista en `docs/diseno.md` con: origen inexistente, red vacía, origen sin salidas, destino desconectado, destino igual al origen, ciclo presente (por ejemplo, `C10K5` ↔ `C10K6`) y datos inválidos. Cada uno con su resultado esperado.
- **Hecho cuando:** cada caso tiene resultado esperado y código de error, si aplica.

### [ ] T10 · Contrato del endpoint en `docs/api.md` (60 min) · *Carolina*
- **Entregable:** endpoint de cobertura (propuesta: `GET /coverage?origin=<id>&destination=<id>`, con `destination` opcional) con ejemplos de entrada y salida, y los códigos de error de T06.
- **Hecho cuando:** hay un ejemplo JSON por respuesta y un código HTTP por cada caso de T09.

---

## Bloque 2 — Núcleo Python sin API (guía, paso 4)

### [ ] T11 · Esqueleto del módulo de cobertura (45 min) · *Jacobo*
- **Entregable:** `backend/domain/coverage.py` con la firma de `reachable(graph, origin_id)` y su documentación.
- **Hecho cuando:** el módulo se importa desde un intérprete de Python.

### [ ] T12 · Recorrido por capas (60 min) · *Jacobo*
- **Entregable:** función que devuelve el orden de visita y el conjunto alcanzable, usando los vecinos salientes de `Graph`, con conjunto de visitados.
- **Hecho cuando:** con la red de F1 desde `BOD` coincide con la traza de T08, y un ciclo no provoca bucles infinitos.

### [ ] T13 · Alcance hacia un destino (45 min) · *Mariana*
- **Entregable:** función que indica si un destino es alcanzable y, si no lo es, un motivo.
- **Hecho cuando:** `D` devuelve "no alcanzable" y un destino alcanzable devuelve "alcanzable".

### [ ] T14 · Validar origen y destino (30 min) · *Mariana*
- **Entregable:** reutilizar `OriginNotFound` y `DestinationNotFound` de `backend/domain/errors.py`. No crear excepciones nuevas.
- **Hecho cuando:** un origen inexistente y un destino inexistente se rechazan con mensajes distintos.

### [ ] T15 · Red vacía y origen sin salidas (30 min) · *Mariana*
- **Entregable:** comportamiento definido y probado para red vacía y para un origen sin conexiones salientes.
- **Hecho cuando:** ambos casos devuelven el resultado de T09 y no fallan.

### [ ] T16 · Verificación en consola (45 min) · *Mariana*
- **Entregable:** script pequeño que ejecuta los casos de T09 contra el núcleo e imprime el resultado.
- **Hecho cuando:** cada caso de T09 se ejercita al menos una vez.

---

## Bloque 3 — API REST (guía, paso 5)

### [ ] T17 · Endpoint `GET /coverage` (60 min) · *Carolina*
- **Entregable:** `backend/api/coverage.py` con blueprint, registrado en `app.py`, que lee el grafo de `app.extensions["graph"]` (convención de F1).
- **Hecho cuando:** `GET /coverage?origin=<id>` responde con la lista de alcanzables.

### [ ] T18 · Validación de parámetros y errores (30 min) · *Mariana*
- **Entregable:** `json_body()`-equivalente para query: falta `origin` → 400 `MISSING_DATA`; el resto de errores pasan al manejador de F1 sin capturarlos.
- **Hecho cuando:** cada caso de T06 devuelve su código HTTP y su `code`.

### [ ] T19 · Revisión del recorrido con el script (30 min) · *Jose*
- **Entregable:** ejecutar contra la API los casos de T09 y anotar en un comentario de PR cualquier diferencia con la traza de T08.
- **Hecho cuando:** el orden de visita de la API coincide con T08.

---

## Bloque 4 — Interfaz mínima (guía, paso 6)

### [ ] T20 · [DECISIÓN] Dónde mostrar la cobertura (30 min) · *Mariana*
- **Entregable:** en `docs/diseno.md`, decidir si es una sección nueva en la pantalla actual o una pantalla aparte. Reutilizar `ErrorMessage` y el cliente de `api.js`.
- **Hecho cuando:** la decisión está escrita y justificada.

### [ ] T21 · Selector de origen y consulta (60 min) · *Carolina*
- **Entregable:** selector de origen (y destino opcional) con los puntos de la red, que llama a `GET /coverage`.
- **Hecho cuando:** el resultado sale del backend, no está escrito a mano.

### [ ] T22 · Mostrar alcanzables y explicación de no alcanzable (60 min) · *Carolina*
- **Entregable:** lista de destinos alcanzables y, si el destino consultado no lo es, un mensaje claro.
- **Hecho cuando:** un destino desconectado como `D` muestra una explicación comprensible.

### [ ] T23 · Mostrar el orden de visita (45 min) · *Jacobo*
- **Entregable:** en la pantalla, la lista de puntos en el orden en que se visitan.
- **Hecho cuando:** el orden en pantalla coincide con T08.

---

## Bloque 5 — Script de aceptación (guía: pruebas de aceptación)

Cada escenario imprime: nombre, qué esperaba, qué obtuvo y PASÓ/FALLÓ. Sin `pytest`. Se guarda en `acceptance/`.

### [ ] T24 · Esqueleto del script e impresión (45 min) · *Jose*
- **Entregable:** script que llama a la API local y tiene una función común para reportar escenario, esperado, obtenido y resultado.
- **Hecho cuando:** un escenario de ejemplo se imprime con el formato pedido.

### [ ] T25 · Escenarios normales y red vacía (45 min) · *Jose*
- **Entregable:** escenarios para: alcance normal desde `BOD`, alcance hacia un destino alcanzable, red vacía.
- **Hecho cuando:** pasan contra una API recién iniciada.

### [ ] T26 · Escenarios de error (60 min) · *Jose*
- **Entregable:** origen inexistente, destino inexistente, destino desconectado (`D`), falta de origen, y los casos de T09.
- **Hecho cuando:** todos pasan y comprueban código y mensaje esperados.

### [ ] T27 · Ejecución completa y evidencia (30 min) · *Jose*
- **Entregable:** salida completa guardada en `docs/evidencia-f2.txt`.
- **Hecho cuando:** corre de principio a fin desde un estado limpio sin intervención manual.

---

## Bloque 6 — Cierre (guía, entrega por feature)

### [ ] T28 · README de F2 (45 min) · *Jose*
- **Entregable:** sección de F2 en el README: qué hace, endpoint, cómo ejecutar el script y decisiones de `diseno.md`.
- **Hecho cuando:** alguien ajeno puede ejecutar el script solo con el README.

### [ ] T29 · Bitácora de IA (45 min) · *Todos*
- **Entregable:** filas propias en `docs/bitacora-ia.md`, una por cada decisión y cada pieza de código con ayuda de IA.
- **Hecho cuando:** cada integrante tiene sus filas.

### [ ] T30 · Video de respaldo, máximo 3 minutos (60 min) · *Jacobo*
- **Entregable:** video con el flujo completo: consultar cobertura desde la bodega, destino desconectado y error por origen inexistente.
- **Hecho cuando:** dura ≤ 3 min y el enlace está en el README.

### [ ] T31 · Preparar el pitch (60 min) · *Carolina*
- **Entregable:** guion de 7 minutos con: problema y usuario, modelado, algoritmo elegido y por qué, complejidad, un caso borde, evidencia del script y aportes del equipo.
- **Hecho cuando:** Carolina puede explicar y trazar cualquier pieza del código de F2.

### [ ] T32 · Pull request, revisión y tag (45 min) · *Todos*
- **Entregable:** PR de `feat-2/cobertura` a `main`, con revisión de otro integrante, aportes declarados con enlaces a commits y tag `f2`.
- **Hecho cuando:** el PR está aprobado y mezclado, y el tag existe.

### [ ] T33 · Coevaluación confidencial (20 min) · *Todos*
- **Entregable:** coevaluación enviada según indique el docente.

---

## Notas

- **Cambio de requisito:** llega después de F2. Esta feature no lo incluye; anotar cualquier idea que surja, pero no agregarla al alcance.
- **Ciclos:** el escenario de ciclo (T09) se prueba aunque F2 no use dependencias, porque la red de F1 sí tiene ciclos (`C10K5` ↔ `C10K6`).
- **Tiempos:** son estimaciones. Si una tarea supera una hora, dividirla antes de seguir.
