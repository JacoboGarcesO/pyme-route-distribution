# Guion del pitch — Feature 4: Operación demostrable

## Problema y usuario

El despachador necesita configurar una red pequeña, verificar cobertura y
escoger una ruta que pueda explicar. F4 reúne esas decisiones en una sola
operación visible.

## Solución y modelado

RutaPyme usa un grafo dirigido propio: los puntos son nodos, las conexiones
son trayectos con costo positivo en kilómetros y la lista de adyacencia conserva
el sentido. El frontend dibuja los datos que entrega `GET /network`, incluyendo
posiciones y costos; no calcula rutas.

## Algoritmos

BFS responde cobertura porque visita por capas y solo pregunta si existe un
camino. Dijkstra responde la ruta de menor costo porque compara costos
positivos, guarda predecesores y reconstruye la secuencia. Por eso una ruta de
tres tramos y 7 km puede ganar a una directa de 9 km.

## Cambio de requisito

El equipo eligió una parada obligatoria. `GET /shortest-path` acepta `via` y
combina la mejor ruta hacia la parada con la mejor ruta desde ella hasta el
destino. Sin `via`, F3 no cambia. Una parada inexistente es `404
VIA_NOT_FOUND`; un tramo imposible es `200 found: false`.

## Demo y casos borde

Se registra una red de cinco puntos, se consulta cobertura desde la bodega y
se solicita la ruta hacia Casa A. Luego se repite con Centro como parada
obligatoria. Se muestra una casa aislada, una ruta inexistente, un destino
inexistente y costos cero, negativos o no numéricos.

## Evidencia y cierre

El script de aceptación comprueba el flujo normal, la visualización de datos,
cobertura, ruta mínima, errores y `via`. La salida completa queda en
`docs/evidencia-f4.txt`; el detalle de decisiones está en `docs/diseno.md`.
