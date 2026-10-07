<script>
  import { pointTypeLabel } from './pointTypes.js'

  // network: lista de puntos de GET /network. Cada punto trae su posición (x, y)
  // opcional y sus conexiones salientes; el mapa solo dibuja lo que calculó el backend.
  let { network } = $props()

  const SCALE_X = 150
  const SCALE_Y = 130
  const PAD = 70
  const ARROW_GAP = 5
  const COLORS = { oneWay: '#d85a30', access: '#1d9e75', warehouse: '#7f77dd', house: '#1d9e75' }

  const hasPosition = (point) => Number.isFinite(point.x) && Number.isFinite(point.y)

  // Convierte la posición de cada punto en píxeles. Los puntos sin posición van en
  // una fila al pie del mapa.
  const layout = $derived.by(() => {
    const placed = network.filter(hasPosition)
    const unplaced = network.filter((point) => !hasPosition(point))
    const xs = placed.map((point) => point.x)
    const ys = placed.map((point) => point.y)
    const minX = placed.length ? Math.min(...xs) : 0
    const minY = placed.length ? Math.min(...ys) : 0
    const mapWidth = placed.length ? (Math.max(...xs) - minX) * SCALE_X : 0
    const mapHeight = placed.length ? (Math.max(...ys) - minY) * SCALE_Y : 0

    const nodes = new Map()
    for (const point of placed) {
      nodes.set(point.id, {
        point,
        x: PAD + (point.x - minX) * SCALE_X,
        y: PAD + (point.y - minY) * SCALE_Y,
      })
    }
    const rowY = PAD + mapHeight + (placed.length ? 90 : 0)
    unplaced.forEach((point, index) => {
      nodes.set(point.id, { point, x: PAD + index * 120, y: rowY })
    })

    const rowWidth = unplaced.length ? (unplaced.length - 1) * 120 : 0
    return {
      nodes,
      unplacedCount: unplaced.length,
      width: PAD * 2 + Math.max(mapWidth, rowWidth),
      height: (unplaced.length ? rowY : PAD + mapHeight) + PAD,
    }
  })

  // Distancia desde el centro del nodo hasta su borde en la dirección (ux, uy).
  function reach(type, ux, uy) {
    if (type === 'warehouse') {
      return Math.min(32 / Math.max(Math.abs(ux), 0.001), 13 / Math.max(Math.abs(uy), 0.001))
    }
    return type === 'pickup_point' ? 12 : 9
  }

  // Una arista por sentido; si existen A→B y B→A se dibuja una sola línea con dos flechas.
  const edges = $derived.by(() => {
    const costs = new Map()
    for (const point of network) {
      for (const connection of point.connections) {
        costs.set(`${point.id}|${connection.destination_id}`, connection.cost_km)
      }
    }

    const result = []
    for (const [key, cost] of costs) {
      const [fromId, toId] = key.split('|')
      const from = layout.nodes.get(fromId)
      const to = layout.nodes.get(toId)
      if (!from || !to) continue
      const twoWay = costs.has(`${toId}|${fromId}`)
      if (twoWay && fromId > toId) continue

      const length = Math.hypot(to.x - from.x, to.y - from.y) || 1
      const ux = (to.x - from.x) / length
      const uy = (to.y - from.y) / length
      const start = reach(from.point.type, ux, uy) + (twoWay ? ARROW_GAP : 3)
      const end = reach(to.point.type, ux, uy) + ARROW_GAP
      const access = to.point.type === 'pickup_point'
      result.push({
        key,
        cost,
        twoWay,
        access,
        x1: from.x + ux * start,
        y1: from.y + uy * start,
        x2: to.x - ux * end,
        y2: to.y - uy * end,
        labelX: (from.x + to.x) / 2 - uy * 12,
        labelY: (from.y + to.y) / 2 + ux * 12 + 4,
        title: `${from.point.name} → ${to.point.name}: ${cost} km${twoWay ? ' (y a la inversa)' : ''}`,
      })
    }
    return result
  })

  function edgeColor(edge) {
    if (edge.twoWay) return 'var(--muted)'
    return edge.access ? COLORS.access : COLORS.oneWay
  }

  // Letra del nodo: "Casa A" -> "A".
  const houseLetter = (name) => name.trim().split(/\s+/).pop().charAt(0).toUpperCase()
  const warehouseLabel = (name) => name.trim().split(/\s+/)[0]
</script>

<section>
  <h2>Mapa de la red</h2>

  {#if network.length === 0}
    <p class="muted">La red está vacía. Crea puntos y conexiones para verla en el mapa.</p>
  {:else}
    <svg
      class="map"
      viewBox="0 0 {layout.width} {layout.height}"
      role="img"
      aria-label="Mapa de la red: puntos y conexiones dirigidas con su distancia en kilómetros"
    >
      <defs>
        {#each [['both', 'var(--muted)'], ['oneway', COLORS.oneWay], ['access', COLORS.access]] as [id, color] (id)}
          <marker
            id="arrow-{id}"
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path
              d="M1 1L9 5L1 9"
              fill="none"
              style="stroke: {color}"
              stroke-width="1.6"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </marker>
        {/each}
      </defs>

      {#each edges as edge (edge.key)}
        {@const marker = edge.twoWay ? 'both' : edge.access ? 'access' : 'oneway'}
        <g>
          <title>{edge.title}</title>
          <line
            x1={edge.x1}
            y1={edge.y1}
            x2={edge.x2}
            y2={edge.y2}
            style="stroke: {edgeColor(edge)}"
            stroke-width="1.5"
            stroke-dasharray={edge.access && !edge.twoWay ? '4 3' : undefined}
            marker-start={edge.twoWay ? 'url(#arrow-both)' : undefined}
            marker-end="url(#arrow-{marker})"
          />
          <text x={edge.labelX} y={edge.labelY} text-anchor="middle" class="cost">{edge.cost}</text>
        </g>
      {/each}

      {#each [...layout.nodes.values()] as node (node.point.id)}
        <g>
          <title>{node.point.name} · {pointTypeLabel(node.point.type)}</title>
          {#if node.point.type === 'warehouse'}
            <rect
              x={node.x - 32}
              y={node.y - 13}
              width="64"
              height="26"
              rx="5"
              fill={COLORS.warehouse}
              fill-opacity="0.2"
              stroke={COLORS.warehouse}
            />
            <text x={node.x} y={node.y + 4} text-anchor="middle" class="label">
              {warehouseLabel(node.point.name)}
            </text>
          {:else if node.point.type === 'pickup_point'}
            <rect
              x={node.x - 11}
              y={node.y - 11}
              width="22"
              height="22"
              rx="3"
              fill={COLORS.house}
              fill-opacity="0.2"
              stroke={COLORS.house}
            />
            <text x={node.x} y={node.y + 5} text-anchor="middle" class="label">
              {houseLetter(node.point.name)}
            </text>
          {:else}
            <circle cx={node.x} cy={node.y} r="8" class="corner" />
          {/if}
        </g>
      {/each}
    </svg>

    <ul class="legend">
      <li><span class="swatch two-way"></span> Doble sentido</li>
      <li><span class="swatch one-way"></span> Un solo sentido</li>
      <li><span class="swatch access"></span> Acceso a un punto de recogida</li>
      <li><span class="swatch warehouse"></span> Bodega</li>
      <li><span class="swatch house"></span> Punto de recogida</li>
      <li><span class="swatch corner-dot"></span> Esquina o barrio</li>
      <li>El número sobre cada trayecto es la distancia en km.</li>
    </ul>
    {#if layout.unplacedCount > 0}
      <p class="muted">
        Los puntos sin posición (x, y) aparecen en una fila al pie del mapa.
      </p>
    {/if}
  {/if}
</section>

<style>
  .map {
    display: block;
    width: 100%;
    height: auto;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
  }

  .cost {
    font-size: 12px;
    fill: var(--muted);
  }

  .label {
    font-size: 12px;
    font-weight: 600;
    fill: var(--text);
  }

  .corner {
    fill: var(--bg);
    stroke: var(--muted);
    stroke-width: 1.5;
  }

  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 16px;
    margin: 12px 0 0;
    padding: 0;
    list-style: none;
    font-size: 0.875rem;
    color: var(--muted);
  }

  .swatch {
    display: inline-block;
    width: 22px;
    height: 0;
    margin-right: 6px;
    vertical-align: middle;
    border-top: 2px solid var(--muted);
  }

  .swatch.one-way {
    border-top-color: #d85a30;
  }

  .swatch.access {
    border-top: 2px dashed #1d9e75;
  }

  .swatch.warehouse,
  .swatch.house,
  .swatch.corner-dot {
    height: 10px;
    border: 1px solid;
    border-radius: 3px;
  }

  .swatch.warehouse {
    border-color: #7f77dd;
    background: rgb(127 119 221 / 20%);
  }

  .swatch.house {
    border-color: #1d9e75;
    background: rgb(29 158 117 / 20%);
  }

  .swatch.corner-dot {
    width: 10px;
    border-color: var(--muted);
    border-radius: 50%;
  }
</style>
