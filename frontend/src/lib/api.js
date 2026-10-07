// Cliente del backend RutaPyme (contrato en docs/api.md).
// Todas las llamadas pasan por request(), que convierte las respuestas de
// error {"error": {"code", "message"}} en un ApiError con el mensaje para
// el coordinador.

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message)
    this.status = status
    this.code = code
  }
}

const BACKEND_UNAVAILABLE = 'No se pudo conectar con el backend. ¿Está en ejecución?'

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(path, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', BACKEND_UNAVAILABLE)
  }

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const error = body?.error
    // Con el backend apagado, el proxy de Vite responde 5xx sin el formato
    // de error del contrato: se informa como backend no disponible.
    if (!error && response.status >= 500) {
      throw new ApiError(response.status, 'NETWORK_ERROR', BACKEND_UNAVAILABLE)
    }
    throw new ApiError(
      response.status,
      error?.code ?? 'UNKNOWN_ERROR',
      error?.message ?? `El backend respondió con el código ${response.status}.`,
    )
  }
  return body
}

export function getHealth() {
  return request('/health')
}

export async function listPoints() {
  const body = await request('/points')
  return body.points
}

// x e y (posición en el mapa) son opcionales: solo se envían si se indican.
export function createPoint(name, type, x, y) {
  const body = { name, type }
  if (x !== undefined) body.x = x
  if (y !== undefined) body.y = y
  return request('/points', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

// cost_km viaja como texto decimal (por ejemplo "4.5"), nunca como número.
export function createConnection(originId, destinationId, costKm) {
  return request('/connections', {
    method: 'POST',
    body: JSON.stringify({
      origin_id: originId,
      destination_id: destinationId,
      cost_km: costKm,
    }),
  })
}

export async function getNetwork() {
  const body = await request('/network')
  return body.points
}
