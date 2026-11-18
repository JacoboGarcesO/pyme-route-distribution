// Lista cerrada de tipos de punto (diseno.md, regla P3) con su nombre en pantalla.
export const POINT_TYPES = [
  { value: 'warehouse', label: 'Bodega' },
  { value: 'neighborhood', label: 'Barrio' },
  { value: 'pickup_point', label: 'Punto de recogida' },
]

// En una red grande las esquinas (barrios) tapan las direcciones en los selectores de
// origen y destino, así que se ocultan. En la red pequeña de ejemplo los barrios son
// los puntos principales, por eso allí se muestra todo.
export const BIG_NETWORK_THRESHOLD = 30

export function selectablePoints(points) {
  if (points.length <= BIG_NETWORK_THRESHOLD) return points
  return points.filter((point) => point.type !== 'neighborhood')
}

export function pointTypeLabel(value) {
  return POINT_TYPES.find((type) => type.value === value)?.label ?? value
}
