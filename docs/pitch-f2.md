# Guion del pitch — Feature 2: Cobertura de entregas

Duración: 7 minutos de demo y exposición, más 3 minutos de preguntas. Responsable: Carolina.

## Resumen de tiempos

| Minuto | Bloque | Qué mostrar |
|---|---|---|
| 0:00 – 1:00 | Problema y usuario | El despachador y la pregunta de cobertura |
| 1:00 – 2:00 | Modelado | Nodos, aristas dirigidas, pesos y representación |
| 2:00 – 3:30 | Algoritmo | BFS por capas, por qué sirve para cobertura |
| 3:30 – 4:30 | Complejidad y estructura | O(V + E), lista de adyacencia |
| 4:30 – 6:00 | Demo | Consulta normal, destino alcanzable, destino D aislado |
| 6:00 – 6:30 | Caso borde | Calle de un solo sentido y ciclo |
| 6:30 – 7:00 | Evidencia y aportes | Script de aceptación y reparto del equipo |

## 1. Problema y usuario (1 min)

- Usuario: el **despachador** de RutaPyme.
- Problema: hoy decide por intuición. A veces envía un pedido por una conexión cerrada.
- Pregunta que responde F2: **¿a qué destinos puedo llegar desde esta bodega?**
- Frase de cierre: F2 no calcula la ruta más barata; solo dice si hay cobertura.

## 2. Modelado (1 min)

- **Nodos:** puntos (bodega, barrios, puntos de recogida). Cada uno con un UUID.
- **Aristas:** trayectos **dirigidos**. A→B no implica B→A (decisión T06 de F1).
- **Peso:** distancia en km. F2 no lo usa, pero queda registrado.
- **Representación:** lista de adyacencia con diccionarios anidados `{origen: {destino: costo}}` (T08 de F1).

Mostrar en pantalla: la red de ejemplo del mapa de calles y carreras.

## 3. Algoritmo (1.5 min)

- **BFS (recorrido por capas):** visita primero los puntos a un salto del origen, luego a dos saltos, y así sucesivamente.
- **Visitados:** un conjunto evita repetir puntos. Así un ciclo no provoca un bucle infinito.
- **Por qué sirve para cobertura:** basta saber si un punto se alcanza, no cuánto cuesta llegar.
- **Por qué no DFS:** (completar con la decisión T04 del equipo).

Mostrar la traza: orden de visita desde la bodega.

## 4. Complejidad y estructura (1 min)

- Tiempo: **O(V + E)**, donde V son los puntos y E las conexiones. Cada punto se visita una vez y cada arista se revisa una vez.
- Memoria: O(V) para la cola y el conjunto de visitados, más la lista de adyacencia.
- Comparación: con matriz de adyacencia, revisar los vecinos de cada punto costaría O(V) por punto.

## 5. Demo (1.5 min)

Con la API y el frontend en ejecución:

1. **Consulta normal:** origen = Bodega → lista de destinos alcanzables.
2. **Destino alcanzable:** Bodega → Casa A → `reachable: true`.
3. **Destino desconectado:** Bodega → Destino D → `reachable: false` con la explicación.

## 6. Caso borde (30 s)

- **Calle de un solo sentido:** existe Bodega → Norte, pero no Norte → Bodega. Desde Norte, la bodega sí se alcanza, pero por Casa A, no por esa calle. Mostrar que la respuesta depende del camino completo y del sentido de cada tramo.
- **Ciclo:** Bodega ↔ Casa A. El recorrido termina gracias al conjunto de visitados.

## 7. Evidencia y aportes (30 s)

- Script de aceptación en `acceptance/`, con la salida guardada en `docs/evidencia-f2.txt` (T27, pendiente).
- Reparto del equipo: ver `docs/equipo.md`.
- Enlaces a los commits y Issues de F2.

## Preguntas probables

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué no usas la ruta más corta? | F2 pide cobertura. La ruta de menor costo es F3. |
| ¿Qué pasa si un punto no existe? | 404 `ORIGIN_NOT_FOUND` o `DESTINATION_NOT_FOUND`, con el mensaje del punto. |
| ¿Por qué "no alcanzable" es 200 y no 404? | Es una respuesta válida de negocio, no un fallo de la consulta (decisión T06). |
| ¿Qué pasa con una red vacía? | No hay origen válido: 404 `ORIGIN_NOT_FOUND`. |
| ¿Cómo sabes que el recorrido es correcto? | Traza manual en `diseno.md` y script de aceptación con los casos borde. |
