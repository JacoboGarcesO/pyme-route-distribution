// Lista cerrada de tipos de punto (diseno.md, regla P3) con su nombre en pantalla.
export const POINT_TYPES = [
  { value: 'warehouse', label: 'Bodega' },
  { value: 'neighborhood', label: 'Barrio' },
  { value: 'pickup_point', label: 'Punto de recogida' },
]

export function pointTypeLabel(value) {
  return POINT_TYPES.find((type) => type.value === value)?.label ?? value
}
