# Guion del video de respaldo — Feature 2 (Cobertura de entregas)

Duración máxima: **3 minutos**. Graba con el backend arrancado con la red de ejemplo y el frontend abierto.

## Preparación (antes de grabar)

Terminal 1, desde `backend/`:

```bash
SEED_NETWORK=1 flask --app app run
```

En PowerShell: `$env:SEED_NETWORK = "1"; flask --app app run`.

Terminal 2, desde `frontend/`:

```bash
npm run dev
```

Abre `http://localhost:5173`. Para mostrar el destino desconectado hace falta el punto aislado `D` (T07 de Mariana); si aún no está en la semilla, créalo antes desde el formulario "Crear punto", sin conexiones.

## Escenas

| Tiempo | Qué muestras | Qué dices |
|---|---|---|
| 0:00 a 0:20 | La pantalla con la red cargada (listado de adyacencia) | "RutaPyme necesita saber a qué destinos puede entregar desde la bodega. Esta es la red: los trayectos tienen sentido, por eso es dirigida" |
| 0:20 a 1:10 | Sección "Cobertura desde un origen": origen `Bodega central`, sin destino, "Consultar cobertura" | "Desde la bodega se alcanzan 14 destinos. El sistema los recorre por capas (BFS): primero los vecinos de la bodega, luego los de ellos" |
| 1:10 a 1:40 | La lista "Orden de visita" | "Este es el orden de visita. Coincide con la traza manual de la documentación: primero las tres esquinas vecinas, después las siguientes capas" |
| 1:40 a 2:15 | Origen `Bodega central` y destino `D` (el aislado) | "Si el destino no se puede alcanzar, no es un error: es una respuesta válida con su explicación. Aquí no hay un camino dirigido hasta D" |
| 2:15 a 2:45 | Una petición con un origen que no existe (ver abajo) | "Y si el origen no existe, el sistema responde con un error claro: 404 `ORIGIN_NOT_FOUND`" |
| 2:45 a 3:00 | El script de aceptación terminando en verde | "Todo está verificado con el script de aceptación. Cobertura responde la pregunta de alcance; la ruta más barata es la siguiente feature" |

## Cómo mostrar el origen inexistente

La pantalla solo deja elegir puntos que existen, así que ese error se muestra con una petición directa. Con el backend en marcha:

```bash
curl "http://127.0.0.1:5000/coverage?origin=no-existe"
```

Debe responder 404 con `{"error": {"code": "ORIGIN_NOT_FOUND", ...}}`.

## Antes de subir el video

- Dura 3 minutos o menos.
- Se ve el orden de visita y el destino desconectado.
- El enlace está en el README (sección de Feature 2, a cargo de Jose).
- El script de aceptación de F2 es de Jose (T24 a T27). Si todavía no existe cuando grabes, muestra el de F1 (`python acceptance/scripts/acceptance_feature_1.py`, que da 23 de 23 con el backend recién iniciado y sin semilla) y avisa que el de F2 se agrega después.
