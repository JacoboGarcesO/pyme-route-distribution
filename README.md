# RutaPyme

Herramienta para registrar una red operativa de entregas y consultar sus
conexiones. El proyecto usa un grafo dirigido propio, una API REST en Python y
un frontend conectado al backend.

## Estado

Feature 1 — Red operativa inicial.

La API registra puntos (`warehouse`, `neighborhood` y `pickup_point`) y
conexiones dirigidas con distancia positiva en kilómetros. Las decisiones de
modelado están documentadas en [`docs/diseno.md`](docs/diseno.md) y el contrato
de la API en [`docs/api.md`](docs/api.md).

## Instalación

Se requiere Python 3.12 o superior.

```bash
python -m venv .venv
pip install -r backend/requirements.txt
```

Activa el entorno antes de instalar: en Windows (PowerShell)
`.venv\Scripts\Activate.ps1`; en macOS o Linux `source .venv/bin/activate`.

## Ejecución del backend

Desde la carpeta `backend/` (los imports del backend se resuelven desde ahí):

```bash
cd backend
flask --app app run
```

La comprobación de salud está disponible en `http://127.0.0.1:5000/health`.

## Ejecución del frontend

Requiere Node.js. En otra terminal, con el backend en ejecución:

```bash
cd frontend
npm install
npm run dev
```

Vite reenvía `/health`, `/points`, `/connections` y `/network` al backend en
`http://127.0.0.1:5000`.

## Pruebas de aceptación

Con el backend recién iniciado (la red debe estar vacía) en otra terminal:

```bash
python scripts/acceptance_feature_1.py
```

El script cubre escenarios normales, red vacía, conexiones válidas y reglas
de error de Feature 1. Cada caso imprime lo esperado, lo obtenido y su
resultado.

## Endpoints de Feature 1

- `GET /health`
- `POST /points` y `GET /points`
- `POST /connections` y `GET /connections`
- `GET /network`

## Decisiones de diseño

- **Red dirigida:** no todas las calles son bidireccionales, así que A→B y B→A son aristas distintas. Si ambas existen, tienen el mismo costo.
- **Peso:** distancia en km, `Decimal`, mayor que 0 y con hasta 7 decimales. Viaja como texto en el JSON.
- **Representación:** lista de adyacencia con diccionarios anidados `{origen: {destino: km}}`, porque la red es dispersa y los recorridos de las siguientes features piden los vecinos de un punto.
- **Identificador:** UUID generado por el sistema; el nombre es solo informativo y puede repetirse.
- **Validación:** todas las reglas viven en el núcleo (`Graph`); la API solo traduce los errores a HTTP.

El detalle y las alternativas descartadas están en [`docs/diseno.md`](docs/diseno.md).

## Evidencia

La salida del script de aceptación (23 de 23 escenarios) está en
[`docs/evidencia-f1.txt`](docs/evidencia-f1.txt). El video de respaldo se
agregará aquí cuando esté grabado.

## Documentación

- [Guía común](docs/03-guia-comun-estudiantes.md)
- [Brief de RutaPyme](docs/04-brief-rutapyme.md)
- [Decisiones de diseño](docs/diseno.md)
- [Contrato de API](docs/api.md)
- [Plan de tareas de Feature 1](docs/05-tareas-feature-1.md)
- [Equipo y forma de trabajo](docs/equipo.md)
- [Bitácora de IA](docs/bitacora-ia.md)
- [Guion del pitch](docs/pitch-f1.md)
- [Evidencia de las pruebas de aceptación](docs/evidencia-f1.txt)
