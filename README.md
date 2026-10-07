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
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Ejecución del backend

Desde la raíz del proyecto:

```bash
flask --app backend.app run
```

La comprobación de salud está disponible en `http://127.0.0.1:5000/health`.

## Pruebas de aceptación

Con el backend ejecutándose en otra terminal:

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

## Documentación

- [Guía común](docs/03-guia-comun-estudiantes.md)
- [Brief de RutaPyme](docs/04-brief-rutapyme.md)
- [Decisiones de diseño](docs/diseno.md)
- [Contrato de API](docs/api.md)
- [Plan de tareas de Feature 1](docs/05-tareas-feature-1.md)
