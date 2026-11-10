# Guion del pitch — Feature 3: Ruta de menor costo

## 1. Problema y usuario — 1 minuto

El despachador necesita comparar rutas entre dos puntos. La ruta con menos
saltos no siempre es la más económica: una conexión directa puede costar más
que una ruta con varios tramos.

## 2. Modelado — 1 minuto

La red es un grafo dirigido. Cada punto es un nodo y cada conexión tiene un
costo positivo en kilómetros. La lista de adyacencia permite consultar los
vecinos salientes y conserva el sentido de cada trayecto.

## 3. Algoritmo — 2 minutos

Se usa Dijkstra porque todos los costos son positivos. El algoritmo mantiene
la mejor distancia conocida, selecciona el punto pendiente con menor costo y
relaja sus conexiones. También guarda predecesores para reconstruir la ruta.

La complejidad es O((V + E) log V) con una cola de prioridad y O(V + E) de
memoria.

## 4. Demo — 2 minutos

Crear o consultar la red de demostración:

- Bodega → Casa A: 9 km en 1 salto.
- Bodega → Barrio Norte → Barrio Centro → Casa A: 3 + 2 + 2 = 7 km.

Solicitar la ruta y mostrar que el sistema escoge la segunda, aunque tenga
tres tramos, porque el costo total es menor.

Mostrar también el caso Casa A → Bodega: no existe ruta porque las conexiones
son dirigidas. Finalmente consultar Bodega → Bodega y mostrar costo 0.

## 5. Evidencia y cierre — 1 minuto

Presentar los resultados: 23/23 escenarios del núcleo, 30/30 de la API y 6/6
del script de aceptación. Mencionar que la evidencia está en
`docs/evidencia-f3.txt` y explicar la contribución de cada integrante.
