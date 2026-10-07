# Guion del pitch — Feature 1 (Red operativa inicial)

Expone Jacobo. Duración: 7 minutos de demo y 3 de preguntas.

## 1. Problema y usuario (1 min)

- RutaPyme coordina entregas entre una bodega, barrios y puntos de recogida, y hoy decide por intuición. A veces envía un pedido por una conexión cerrada.
- Usuario de esta feature: el **coordinador logístico**, que registra los puntos y los trayectos disponibles.
- Valor: tener la red registrada y consultable para que las features siguientes (cobertura y ruta) trabajen sobre datos confiables.

## 2. Decisión de modelado (2 min)

Se apoya en `docs/diseno.md` y en el mapa `docs/mapa_calles_carreras_rutapyme.png`.

| Elemento | Decisión | Por qué |
|---|---|---|
| Nodos | Puntos con UUID generado por el sistema, nombre informativo y tipo (`warehouse`, `neighborhood`, `pickup_point`) | El UUID evita ids repetidos y permite que dos puntos tengan el mismo nombre |
| Aristas | Trayectos dirigidos de origen a destino | No todas las calles son bidireccionales: un modelo no dirigido recomendaría rutas que no se pueden recorrer |
| Peso | Distancia en km, `Decimal`, mayor que 0 y con hasta 7 decimales | Una distancia real es positiva, y el algoritmo de F3 exige pesos positivos |
| Regla de sentidos | A→B y B→A son aristas distintas; si ambas existen, tienen el mismo costo | La distancia entre vecinos no depende del sentido; lo que cambia es si el trayecto existe |
| Representación | Lista de adyacencia con diccionarios anidados `{origen: {destino: km}}` | La red es dispersa y los algoritmos de F2 y F3 piden "los vecinos de un punto" una y otra vez |

## 3. Estructura de datos y complejidad (1 min)

V es el número de puntos y E el de conexiones.

| Operación | Costo aproximado | Por qué |
|---|---|---|
| Crear punto | O(1) | Alta en dos diccionarios |
| Crear conexión (incluye duplicado e inversa) | O(1) en promedio | Búsqueda directa en el diccionario anidado |
| Vecinos de un punto | O(grado del punto) | Se leen las claves del diccionario interno |
| Listar todas las conexiones | O(V + E), más el orden de la salida | Se recorren los dos niveles |
| Memoria | O(V + E) | Una matriz costaría O(V²) casi vacía |

Algoritmo: F1 no recorre la red todavía. La validación de duplicados y de la conexión inversa es lo que se apoya en la estructura.

## 4. Demo (2 min)

Con backend y frontend en marcha:

1. Crear una bodega, dos barrios y un punto de recogida desde el frontend.
2. Crear conexiones, incluida una de ida y vuelta con el mismo costo.
3. Mostrar la vista de la red con las conexiones salientes de cada punto.
4. Mostrar un error: crear un costo negativo y leer el mensaje.

## 5. Caso borde (30 s)

Ya existe A→B con 4 km. Registrar B→A con 6 km se rechaza con 409 `INCONSISTENT_COST`, y el mensaje informa el costo ya registrado. Registrar A→B otra vez, con cualquier costo, es 409 `DUPLICATE_CONNECTION`. Registrar B→A con 4 km se acepta.

## 6. Evidencia y aportes (30 s)

- Script de aceptación: `python scripts/acceptance_feature_1.py`, con la salida guardada en `docs/evidencia-f1.txt` (23 de 23 escenarios).
- Aportes del equipo: están en `docs/equipo.md` y en los PR de GitHub.

## Preguntas probables

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué no una matriz de adyacencia? | La red es dispersa: ocuparía O(V²) casi vacía, y los recorridos necesitan los vecinos de un punto, que en la matriz cuesta O(V) |
| ¿Por qué `Decimal` y no `float`? | Con 7 decimales `float` no representa exactamente muchos valores y acumula error al sumar costos en F3 |
| ¿Por qué el costo viaja como texto en el JSON? | Un número JSON se convierte en `float` antes de llegar al núcleo y perdería exactitud |
| ¿Por qué se rechaza un auto-lazo? | Su distancia sería 0 km, que incumple la regla de costo positivo, y no aporta caminos |
| ¿Dónde viven las validaciones? | En el núcleo (`Graph`), para que ninguna vía de entrada corrompa la red; la API solo traduce los errores a HTTP |
| ¿Qué pasa si dos puntos tienen el mismo nombre? | Se permite: se distinguen por su UUID y por su tipo |
| ¿Qué limitaciones tiene la solución? | El grafo vive en memoria y se pierde al reiniciar; los tipos de las esquinas del mapa de ejemplo siguen sin decidir |

## Antes del pitch

- Todo el equipo debe poder explicar las decisiones de T08 y T09, no solo quien expone.
- Ensayar la demo con el backend recién iniciado, porque el escenario de red vacía lo requiere.
