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

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(path, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'No se pudo conectar con el backend. ¿Está en ejecución?')
  }

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const error = body?.error
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
