# Feature 1 — Red operativa inicial: plan de tareas

Cada tarea cabe en **máximo 1 hora**. Cada una tiene un objetivo, un entregable verificable y un criterio de "hecho". Las tareas marcadas con **[DECISIÓN]** requieren elegir entre alternativas; la elección y su justificación se escriben en el entregable (sirven para el README y el pitch).

Estados sugeridos: `[ ]` pendiente · `[~]` en curso · `[x]` hecha.

Orden recomendado: por bloques, de arriba hacia abajo. Las tareas de un mismo bloque dependen de las anteriores salvo que se indique lo contrario.

---

## Bloque 0 — Organización (guía: reglas de equipo y Git)

### [x] T01 · Crear repositorio y estructura base (30 min)
- **Objetivo:** tener el repo en GitHub con la estructura mínima.
- **Entregable:** repo con carpetas (backend, frontend, pruebas de aceptación, docs), `.gitignore` de Python y README vacío.
- **Hecho cuando:** el repo clona y la estructura se ve en GitHub.

### [x] T02 · Registrar responsable del pitch y reparto (20 min)
- **Objetivo:** cumplir la regla de registrar quién expone F1 y quién hace qué.
- **Entregable:** archivo `docs/equipo.md` con el responsable del pitch y tareas asignadas por persona.
- **Hecho cuando:** cada integrante tiene al menos una decisión de modelado, una revisión/prueba y una parte funcional asignadas en el semestre.

### [ ] T03 · Cargar el backlog en GitHub (40 min)
- **Objetivo:** que las tareas sean visibles.
- **Entregable:** una Issue (o tarjeta de Project) por cada tarea de este documento, con su etiqueta de bloque.
- **Hecho cuando:** el tablero muestra todas las tareas en "Por hacer".

### [x] T04 · Entorno virtual y `requirements.txt` (30 min)
- **Objetivo:** reproducibilidad.
- **Entregable:** entorno virtual con Python 3.12+ y `requirements.txt` inicial; se documenta en el README cómo recrearlo.
- **Hecho cuando:** otra persona del equipo puede instalar y activar el entorno siguiendo solo el README.

### [x] T05 · Crear rama de la feature y convención de commits (20 min)
- **Objetivo:** trabajo por ramas y pull requests.
- **Entregable:** rama `feature/f1-red-operativa` y una nota de convención de ramas/commits en `docs/equipo.md`.
- **Hecho cuando:** la rama existe en remoto.

---

## Bloque 1 — Modelado en papel (guía pasos 2 y 3)

### [x] T06 · [DECISIÓN] Dirección de la red (45 min)
- **Objetivo:** decidir y justificar por qué la red es dirigida.
- **Alternativas:** dirigida (A→B no implica B→A) o no dirigida; el brief ya habla de conexiones dirigidas, la tarea es justificarlo con ejemplos del negocio.
- **Entregable:** párrafo en `docs/diseno.md` con la justificación y la regla sobre A→B vs B→A (¿son conexiones distintas o duplicado?).
- **Hecho cuando:** el párrafo responde "¿una conexión A→B siempre permite B→A?" con un ejemplo concreto.

### [x] T07 · [DECISIÓN] Significado y unidad del peso (30 min)
- **Alternativas:** distancia (km), tiempo (min) u otro costo.
- **Entregable:** sección en `docs/diseno.md`: qué representa el peso, unidad, tipo numérico y rango válido (positivo).
- **Hecho cuando:** queda claro por qué el costo debe ser positivo para el negocio.

### [x] T08 · [DECISIÓN] Representación principal del grafo (60 min)
- **Alternativas:** lista de adyacencia, matriz de adyacencia, lista de aristas.
- **Entregable:** tabla comparativa en `docs/diseno.md` (memoria, costo de "vecinos de un punto", costo de "existe A→B", costo de agregar punto/arista) y la decisión final justificada con la pista del brief.
- **Hecho cuando:** la decisión cita las dos operaciones que el brief pide comparar y su complejidad aproximada.

### [x] T09 · [DECISIÓN] Reglas de validación (45 min)
- **Entregable:** lista en `docs/diseno.md` con una regla por línea. Cada regla responde "¿qué pasa si...?":
  - id de punto repetido, id vacío;
  - tipo de punto: ¿libre o lista cerrada? ¿cuáles?;
  - conexión con origen o destino inexistente;
  - conexión duplicada (misma dirección);
  - auto-lazo (A→A): ¿permitido?;
  - costo cero, negativo, no numérico.
- **Hecho cuando:** cada regla tiene su resultado esperado (rechazar o aceptar y con qué mensaje).

### [x] T10 · Diseñar el contrato de la API (60 min)
- **Entregable:** tabla en `docs/api.md` con método, ruta, cuerpo de entrada, respuesta exitosa y códigos de error para: crear punto, listar puntos, crear conexión, listar conexiones, consultar red legible.
- **Hecho cuando:** hay un ejemplo de JSON de entrada y salida por endpoint y un código HTTP por cada regla de T09.

### [x] T11 · Dibujar una red de ejemplo (45 min)
- **Objetivo:** ejemplo pequeño y coherente con datos sintéticos.
- **Entregable:** dibujo (foto o diagrama) de entre 5 y 7 puntos (al menos una bodega, barrios y un punto de recogida) con conexiones y costos, incluyendo un par con ida y sin vuelta. Guardar en `docs/`.
- **Hecho cuando:** el dibujo se puede usar tal cual como datos de la demo.

### [x] T12 · Traza manual de las operaciones (45 min)
- **Entregable:** en `docs/diseno.md`, cómo queda la estructura elegida (T08) paso a paso al insertar los puntos y conexiones de T11, y qué ocurre en tres casos de rechazo (duplicada, punto inexistente, costo inválido).
- **Hecho cuando:** otra persona puede reproducir el estado final de la estructura solo leyendo la traza.

---

## Bloque 2 — Núcleo Python sin API (guía paso 4)

### [x] T13 · Esqueleto del grafo y modelo de punto (45 min)
- **Entregable:** módulo del núcleo con la estructura vacía elegida y la forma de representar un punto (id, tipo).
- **Hecho cuando:** se puede crear un grafo vacío desde un intérprete de Python.

### [x] T14 · Agregar punto con validación (60 min)
- **Entregable:** operación que agrega un punto aplicando las reglas de T09 y rechaza con un error propio y mensaje claro.
- **Hecho cuando:** punto válido se agrega; id repetido e id vacío se rechazan.

### [x] T15 · Listar puntos (30 min)
- **Entregable:** operación que devuelve todos los puntos.
- **Hecho cuando:** con el grafo vacío devuelve lista vacía y no falla.

### [x] T16 · Agregar conexión: validar existencia de puntos (45 min)
- **Entregable:** operación que agrega una conexión origen→destino con costo, validando que ambos puntos existan.
- **Hecho cuando:** origen inexistente y destino inexistente se rechazan por separado con mensaje distinto.

### [x] T17 · Agregar conexión: validar duplicado, auto-lazo y costo (60 min)
- **Entregable:** completar la operación de T16 con las demás reglas de T09.
- **Hecho cuando:** duplicada, costo ≤ 0 y costo no numérico se rechazan; A→B y B→A se comportan como decidió T06.

### [x] T18 · Listar conexiones y vecinos de un punto (45 min)
- **Entregable:** operaciones para listar todas las conexiones y para obtener los vecinos salientes de un punto (con error si el punto no existe).
- **Hecho cuando:** la salida coincide con el dibujo de T11.

### [x] T19 · Representación legible de la red (45 min)
- **Entregable:** operación que devuelve la red en formato legible (por ejemplo, cada punto con sus conexiones salientes y costos).
- **Hecho cuando:** su salida para el ejemplo de T11 coincide con la traza de T12.

### [x] T20 · Verificación del núcleo en consola (45 min)
- **Entregable:** pequeño script que carga el ejemplo de T11 y recorre casos válidos e inválidos imprimiendo resultado.
- **Hecho cuando:** todos los casos de rechazo de T09 se ejercitan al menos una vez.

---

## Bloque 3 — API REST (guía paso 5)

### [x] T21 · [DECISIÓN] Framework y esqueleto de la API (45 min)
- **Alternativas:** FastAPI (validación y documentación automática) o Flask (más simple y manual).
- **Entregable:** aplicación mínima que arranca en local con un endpoint de salud; decisión registrada en `docs/diseno.md` y dependencia en `requirements.txt`.
- **Hecho cuando:** el endpoint de salud responde desde el navegador.

### [x] T22 · Endpoints de puntos (60 min)
- **Entregable:** crear y listar puntos conectados al núcleo, según el contrato de T10.
- **Hecho cuando:** se pueden crear y listar puntos con una herramienta de pruebas de API.

### [x] T23 · Endpoints de conexiones (60 min)
- **Entregable:** crear y listar conexiones conectados al núcleo, según T10.
- **Hecho cuando:** conexión válida se crea y aparece en el listado.

### [x] T24 · Endpoint de la red legible (45 min)
- **Entregable:** endpoint que expone la salida de T19.
- **Hecho cuando:** devuelve la red completa y, si está vacía, una respuesta coherente (no un error).

### [x] T25 · Errores uniformes (45 min)
- **Entregable:** traducción de los errores del núcleo a códigos HTTP y un formato de mensaje único.
- **Hecho cuando:** cada regla de T09 devuelve el código definido en T10.

---

## Bloque 4 — Interfaz mínima (guía paso 6)

### [x] T26 · [DECISIÓN] Tecnología del frontend y esqueleto conectado (45 min)
- **Alternativas:** Streamlit (todo en Python, rápido) o web con HTML/JS (más control, más trabajo).
- **Entregable:** pantalla inicial que llama a la API real y muestra algo (por ejemplo, la lista de puntos).
- **Hecho cuando:** el dato mostrado viene del backend, no está escrito a mano.

### [x] T27 · Formularios para crear puntos y conexiones (60 min)
- **Entregable:** dos formularios que envían a la API.
- **Hecho cuando:** crear punto y conexión desde la interfaz funciona y se ve el resultado.

### [x] T28 · Vista de la red y mensajes de error (60 min)
- **Entregable:** vista legible de la red y visualización clara de los errores de la API.
- **Hecho cuando:** un costo inválido o un punto inexistente muestran un mensaje comprensible para el coordinador.

---

## Bloque 5 — Script de aceptación (guía: pruebas de aceptación)

Cada escenario imprime: nombre, qué esperaba, qué obtuvo y PASÓ/FALLÓ. Sin `pytest`.

### [x] T29 · Esqueleto del script e impresión de resultados (45 min)
- **Entregable:** script que llama a la API local y tiene una función común para reportar escenario/esperado/obtenido/resultado.
- **Hecho cuando:** un escenario de ejemplo se imprime con el formato pedido.

### [x] T30 · Escenarios normales y de consulta vacía (45 min)
- **Entregable:** escenarios para: red vacía, crear puntos, crear conexiones, listar y consultar red legible con el ejemplo de T11.
- **Hecho cuando:** pasan contra una API recién iniciada.

### [x] T31 · Escenarios de error (60 min)
- **Entregable:** escenarios para: id repetido, tipo inválido (si aplica), origen inexistente, destino inexistente, conexión duplicada, auto-lazo (según T09), costo cero, negativo y no numérico.
- **Hecho cuando:** todos pasan y cada uno comprueba código y mensaje esperados.

### [x] T32 · Ejecución completa y evidencia (30 min)
- **Entregable:** salida completa del script guardada en `docs/evidencia-f1.txt`.
- **Hecho cuando:** corre de principio a fin desde un estado limpio sin intervención manual.

---

## Bloque 6 — Cierre (guía: entrega por feature)

### [x] T33 · README (60 min)
- **Entregable:** propósito, instalación, ejecución, endpoints y decisiones de diseño (dirección, peso, representación) tomadas de `docs/diseno.md`.
- **Hecho cuando:** alguien ajeno puede instalar, correr API y frontend y ejecutar el script solo con el README.

### [~] T34 · Bitácora de IA (45 min)
- **Entregable:** tabla con las columnas de la guía (decisión o pieza, herramienta/objetivo de IA, propuesta recibida, acepté o rechacé y por qué, cómo la verifiqué).
- **Nota:** conviene ir llenándola mientras se avanza, no al final.
- **Hecho cuando:** hay una fila por cada tarea [DECISIÓN] y por cada pieza de código con ayuda de IA.

### [ ] T35 · Video de respaldo, máximo 3 minutos (60 min)
- **Entregable:** video con el flujo completo: crear red, error por dato inválido, red legible.
- **Hecho cuando:** dura ≤ 3 min y el enlace está en el README.

### [~] T36 · Preparar el pitch (60 min)
- **Entregable:** guion de 7 minutos con: problema y usuario, modelado (nodos, aristas, dirección, pesos, representación), complejidad y estructura elegida, un caso borde, evidencia del script y aportes del equipo; más posibles preguntas.
- **Hecho cuando:** el responsable puede explicar y trazar cualquier pieza del código.

### [ ] T37 · Pull request, revisión y tag (45 min)
- **Entregable:** PR de la rama de feature con revisión de otro integrante, aportes declarados con enlaces a commits/PR y tag/release `f1`.
- **Hecho cuando:** el PR está aprobado y mezclado, y el tag existe.

### [ ] T38 · Coevaluación confidencial (20 min)
- **Entregable:** coevaluación enviada según indique el docente.
- **Hecho cuando:** enviada por cada integrante.

---

## Resumen

| Bloque | Tareas | Tiempo estimado |
|---|---|---|
| 0 Organización | T01–T05 | ~2 h 20 min |
| 1 Modelado | T06–T12 | ~5 h 30 min |
| 2 Núcleo | T13–T20 | ~6 h |
| 3 API | T21–T25 | ~4 h 15 min |
| 4 Interfaz | T26–T28 | ~2 h 45 min |
| 5 Aceptación | T29–T32 | ~3 h |
| 6 Cierre | T33–T38 | ~5 h 10 min |

Nota: en F1 no aplica el escenario de ciclos de la guía (no hay dependencias dirigidas que lo requieran todavía); si el docente indica lo contrario, se agrega a T31.
