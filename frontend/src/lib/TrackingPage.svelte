<script>
  // Página #/tracking: seguimiento 3D del camión de A a B, con parada opcional.
  // La cámara sigue al camión; si el usuario mueve el mapa, "Recentrar" la devuelve.
  import { onMount } from 'svelte'
  import * as THREE from 'three'
  import { getNetwork, getShortestPath } from './api.js'
  import { animateCity, createCity, createStage, disposeObject, makeTruck, placeTruck, truckState } from './city3d.js'
  import ErrorMessage from './ErrorMessage.svelte'
  import { pointTypeLabel } from './pointTypes.js'

  let network = $state([])
  let networkError = $state(null)
  let originId = $state('')
  let destinationId = $state('')
  let viaId = $state('')
  let route = $state(null)
  let routeError = $state(null)
  let loading = $state(false)
  let following = $state(true)
  let status = $state(null) // { phase, segment, distance, remainingKm }
  let clock = $state('')
  let addresses = $state(new Map()) // id del cliente -> dirección en el mapa

  let container
  let stage, city, truck
  let startTime = 0
  let now = 0
  let lastUi = 0
  let zoom = 1
  const desired = new THREE.Vector3()

  const byId = $derived(new Map(network.map((p) => [p.id, p])))
  const connectionCount = $derived(network.reduce((s, p) => s + p.connections.length, 0))
  const warehouses = $derived(network.filter((p) => p.type === 'warehouse').length)
  const moving = $derived(route?.found && route.path.length > 1)
  const hasVia = $derived(!!route?.via_id && moving)

  const steps = $derived(
    hasVia
      ? [
          ['confirmed', 'Ruta confirmada'],
          ['loading', 'Cargando en A'],
          ['toStop', 'Hacia la parada'],
          ['stop', 'En parada'],
          ['toDest', 'Hacia B'],
          ['delivered', 'Entregado'],
        ]
      : [
          ['confirmed', 'Ruta confirmada'],
          ['loading', 'Cargando en A'],
          ['toDest', 'En tránsito'],
          ['delivered', 'Entregado'],
        ],
  )
  const stepIndex = $derived(status ? steps.findIndex(([key]) => key === status.phase) : 0)
  const phaseLabel = $derived(steps[stepIndex]?.[1] ?? '')
  const nextIndex = $derived(status && moving ? Math.min(status.segment + 1, route.path.length - 1) : -1)
  const nextPoint = $derived(nextIndex >= 0 ? byId.get(route.path[nextIndex].id) : null)

  function pointState(index) {
    if (!status || !city?.timeline) return 'pending'
    if (index === nextIndex && status.phase !== 'delivered' && status.phase !== 'stop') return 'current'
    return city.timeline.cum[index] <= status.distance + 0.01 ? 'done' : 'pending'
  }

  async function loadNetwork() {
    networkError = null
    try {
      network = await getNetwork()
      originId ||= network.find((p) => p.type === 'warehouse')?.id ?? ''
    } catch (error) {
      networkError = error
    }
  }

  async function search(event) {
    event.preventDefault()
    loading = true
    routeError = null
    try {
      route = await getShortestPath(originId, destinationId, viaId)
      following = true
      zoom = 1
    } catch (error) {
      routeError = error
      route = null
    } finally {
      loading = false
    }
  }

  function build() {
    if (!stage) return
    if (city) {
      stage.scene.remove(city.group)
      disposeObject(city.group)
    }
    city = createCity(network, route)
    stage.scene.add(city.group)
    addresses = city.addresses
    truck.visible = !!city.timeline
    startTime = now
    status = null
    if (!city.timeline) overview()
  }

  function overview() {
    following = false
    stage.camera.position.set(45, 70, 95)
    stage.controls.target.set(0, 0, 0)
  }

  // Cámara de persecución: detrás del camión, algo elevada y a un costado.
  function follow(dt) {
    const h = truck.rotation.y
    const fx = Math.cos(h)
    const fz = -Math.sin(h)
    desired.set(
      truck.position.x - fx * 30 * zoom + fz * 16 * zoom,
      24 * zoom,
      truck.position.z - fz * 30 * zoom - fx * 16 * zoom,
    )
    // La mira va pegada al camión; la posición de la cámara lo alcanza con suavidad.
    stage.camera.position.add(new THREE.Vector3().subVectors(truck.position, stage.controls.target))
    stage.controls.target.copy(truck.position)
    stage.camera.position.lerp(desired, 1 - Math.exp(-dt * 2))
  }

  function zoomBy(factor) {
    if (following) {
      zoom = Math.min(3, Math.max(0.35, zoom * factor))
      return
    }
    const { camera, controls } = stage
    camera.position.sub(controls.target).multiplyScalar(factor).add(controls.target)
  }

  function recenter() {
    following = true
  }

  onMount(() => {
    stage = createStage(container)
    // Mover el mapa con el ratón o el dedo suelta la cámara del camión.
    stage.controls.addEventListener('start', () => (following = false))
    truck = makeTruck()
    stage.scene.add(truck)
    build()
    stage.start((time, dt) => {
      now = time
      if (city.timeline) {
        const state = truckState(city.timeline, time - startTime)
        placeTruck(truck, state, dt)
        if (following) follow(dt)
        if (time - lastUi > 0.15) {
          lastUi = time
          status = state
        }
      }
      animateCity(city.group, time)
    })
    loadNetwork()

    const tickClock = () => (clock = new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }))
    tickClock()
    const timer = setInterval(tickClock, 10000)
    return () => {
      clearInterval(timer)
      stage.dispose()
    }
  })

  $effect(() => {
    network
    route
    build()
  })
</script>

<div class="page">
  <div class="scene" bind:this={container}></div>

  <header class="topbar card">
    <a class="wt-brand" href="#" title="Volver al panel">
      <span class="logo" aria-hidden="true">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 2 3 7v10l9 5 9-5V7l-9-5Zm0 2.3L18.7 8 12 11.7 5.3 8 12 4.3Z" /></svg>
      </span>
      WareTrack
    </a>

    <form class="route-form" onsubmit={search}>
      <label>
        <span>Punto A</span>
        <select bind:value={originId} required>
          <option value="">Origen</option>
          {#each network as point (point.id)}<option value={point.id}>{point.name}</option>{/each}
        </select>
      </label>
      <label>
        <span>Parada</span>
        <select bind:value={viaId}>
          <option value="">Sin parada</option>
          {#each network as point (point.id)}<option value={point.id}>{point.name}</option>{/each}
        </select>
      </label>
      <label>
        <span>Punto B</span>
        <select bind:value={destinationId} required>
          <option value="">Destino</option>
          {#each network as point (point.id)}<option value={point.id}>{point.name}</option>{/each}
        </select>
      </label>
      <button type="submit" disabled={loading || !originId || !destinationId}>
        {loading ? 'Calculando…' : 'Despachar'}
      </button>
    </form>

    <div class="top-right">
      <span class="live"><i></i>En vivo {clock}</span>
      <a class="back" href="#">← Panel</a>
    </div>
  </header>

  <section class="wt-kpis" aria-label="Resumen">
    <article class="card wt-kpi">
      <span class="wt-kpi-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Z" /><circle cx="12" cy="9.5" r="2.5" /></svg></span>
      <div><small>Puntos en la red</small><strong>{network.length}</strong><em>{warehouses} {warehouses === 1 ? 'bodega' : 'bodegas'}</em></div>
    </article>
    <article class="card wt-kpi">
      <span class="wt-kpi-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></span>
      <div><small>Conexiones</small><strong>{connectionCount}</strong><em>dirigidas</em></div>
    </article>
    <article class="card wt-kpi">
      <span class="wt-kpi-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg></span>
      <div><small>Ruta actual</small><strong>{moving ? `${route.total_cost_km} km` : '—'}</strong><em>{moving ? `${route.connections.length} tramos` : 'sin despacho'}</em></div>
    </article>
  </section>

  <div class="map-tools card" role="toolbar" aria-label="Controles del mapa">
    <button type="button" title="Acercar" aria-label="Acercar" onclick={() => zoomBy(0.8)}>+</button>
    <button type="button" title="Alejar" aria-label="Alejar" onclick={() => zoomBy(1.25)}>−</button>
    <button type="button" title="Seguir al camión" aria-label="Seguir al camión" class:on={following && moving} disabled={!moving} onclick={recenter}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d="M12 2v4M12 18v4M2 12h4M18 12h4" /></svg>
    </button>
    <button type="button" title="Vista general" aria-label="Vista general" onclick={overview}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11 12 4l9 7" /><path d="M5 10v10h14V10" /></svg>
    </button>
  </div>

  <aside class="detail card" aria-live="polite">
    {#if nextPoint}
      <div class="detail-head">
        <span class="detail-icon {nextPoint.type}" aria-hidden="true"></span>
        <div>
          <small>{status?.phase === 'delivered' ? 'Entregado en' : status?.phase === 'stop' ? 'Detenido en' : 'Próximo punto'}</small>
          <strong>{nextPoint.name}</strong>
          <em>{nextPoint.id.slice(0, 8)}</em>
        </div>
      </div>
      <span class="chip">{phaseLabel}</span>
      <dl>
        <div><dt>Tipo</dt><dd>{pointTypeLabel(nextPoint.type)}</dd></div>
        {#if addresses.get(nextPoint.id)}<div><dt>Dirección</dt><dd>{addresses.get(nextPoint.id)}</dd></div>{/if}
        <div><dt>Rol en la ruta</dt><dd>{nextIndex === route.path.length - 1 ? 'Destino B' : route.path[nextIndex].id === route.via_id ? 'Parada obligatoria' : 'Paso intermedio'}</dd></div>
        <div><dt>Conexiones salientes</dt><dd>{nextPoint.connections.length}</dd></div>
        {#if nextPoint.x != null}<div><dt>Posición en el mapa</dt><dd>{nextPoint.x}, {nextPoint.y}</dd></div>{/if}
        <div><dt>Distancia restante</dt><dd>{status.remainingKm.toFixed(1)} km</dd></div>
        <div><dt>Tramo</dt><dd>{Math.min(status.segment + 1, route.connections.length)} de {route.connections.length}</dd></div>
      </dl>
    {:else}
      <div class="detail-head">
        <span class="detail-icon" aria-hidden="true"></span>
        <div><small>Despacho</small><strong>Sin camión en ruta</strong></div>
      </div>
      <p class="muted">Elige el punto A, el punto B y, si hace falta, una parada. Luego pulsa <b>Despachar</b>.</p>
    {/if}
  </aside>

  {#if moving && !following}
    <button type="button" class="recenter" onclick={recenter}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d="M12 2v4M12 18v4M2 12h4M18 12h4" /></svg>
      Recentrar en el camión
    </button>
  {/if}

  <section class="tracking card" aria-label="Seguimiento del envío">
    <div class="tracking-head">
      <h2>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7h11v9H3zM14 10h4l3 3v3h-7" /><circle cx="7" cy="17" r="2" /><circle cx="17" cy="17" r="2" /></svg>
        Seguimiento del envío
      </h2>
      <span class="muted">TRK-01 · WareTrack</span>
    </div>

    {#if networkError}
      <ErrorMessage error={networkError} />
    {:else if routeError}
      <ErrorMessage error={routeError} />
    {:else if route && !route.found}
      <p class="no-route"><strong>No hay ruta.</strong> {route.reason}</p>
    {:else if moving}
      <div class="tracking-body">
        <ol class="stepper">
          {#each steps as [key, text], index (key)}
            <li class:done={index < stepIndex || status?.phase === 'delivered'} class:active={index === stepIndex && status?.phase !== 'delivered'}>
              <span class="dot" aria-hidden="true">{index < stepIndex || status?.phase === 'delivered' ? '✓' : index + 1}</span>
              <span class="step-label">{text}</span>
            </li>
          {/each}
        </ol>
        <div class="shipment">
          <svg class="mini-truck" width="56" height="36" viewBox="0 0 56 36" aria-hidden="true"><rect x="2" y="6" width="32" height="20" rx="3" fill="#fff" stroke="#cbd5e1" /><rect x="2" y="18" width="32" height="4" fill="#14b8a6" /><path d="M34 12h10l8 8v6H34z" fill="#fff" stroke="#cbd5e1" /><rect x="44" y="14" width="5" height="5" fill="#1e293b" /><circle cx="12" cy="28" r="4" fill="#111827" /><circle cx="44" cy="28" r="4" fill="#111827" /></svg>
          <div>
            <strong>{route.path[0].name} → {route.path.at(-1).name}</strong>
            {#if addresses.get(route.path.at(-1).id)}<small>Entrega en {addresses.get(route.path.at(-1).id)}</small>{/if}
            {#if hasVia}<small>Parada: {byId.get(route.via_id)?.name}</small>{/if}
            <span class="chip">{phaseLabel}</span>
            <small>{status ? `${status.remainingKm.toFixed(1)} km restantes de ${route.total_cost_km} km` : `${route.total_cost_km} km`}</small>
          </div>
        </div>
      </div>
    {:else}
      <p class="muted">Sin envíos en curso. Despacha un camión desde la barra superior.</p>
    {/if}
  </section>

  {#if moving}
    <section class="stops card" aria-label="Recorrido">
      <div class="tracking-head">
        <h2>Recorrido</h2>
        <span class="muted">{route.path.length} puntos</span>
      </div>
      <ol>
        {#each route.path as point, index (index)}
          <li class={pointState(index)}>
            <span class="bullet" aria-hidden="true"></span>
            <span class="stop-name">{point.name}</span>
            <span class="tag">
              {index === 0 ? 'A' : index === route.path.length - 1 ? 'B' : point.id === route.via_id ? 'Parada' : pointTypeLabel(point.type)}
            </span>
          </li>
        {/each}
      </ol>
    </section>
  {/if}
</div>

<style>
  .page {
    position: fixed;
    inset: 0;
    overflow: hidden;
    background: #eef2f8;
    --blue: #2563eb;
    --blue-soft: #e8efff;
    --line: #e3e8f1;
  }
  .scene {
    position: absolute;
    inset: 0;
    cursor: grab;
  }
  .card {
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(8px);
    border: 1px solid var(--line);
    border-radius: 14px;
    box-shadow: 0 8px 24px -12px rgba(30, 41, 80, 0.28);
  }
  .muted {
    color: var(--muted);
    margin: 0;
    font-size: 0.85rem;
  }
  .chip {
    justify-self: start;
    align-self: start;
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    color: #047857;
    background: #dcfce7;
  }

  /* Barra superior */
  .topbar {
    position: absolute;
    top: 14px;
    left: 14px;
    right: 14px;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 8px 12px;
  }
  .wt-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 800;
    font-size: 1.15rem;
    color: var(--text);
    text-decoration: none;
  }
  .logo {
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: var(--blue);
  }
  .route-form {
    flex: 1;
    display: flex;
    align-items: end;
    justify-content: center;
    gap: 8px;
    min-width: 0;
  }
  .route-form label {
    display: grid;
    gap: 1px;
    margin: 0;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    min-width: 0;
  }
  .route-form select {
    width: 190px;
    max-width: 100%;
    padding: 6px 8px;
    font-size: 0.85rem;
    border-radius: 9px;
  }
  .route-form button {
    padding: 8px 18px;
    border-radius: 9px;
    background: var(--blue);
  }
  .top-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .live {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #047857;
    background: #dcfce7;
    white-space: nowrap;
  }
  .live i {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #10b981;
    animation: blink 1.6s infinite;
  }
  .back {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--blue);
    text-decoration: none;
    white-space: nowrap;
  }

  /* Indicadores */
  .wt-kpis {
    position: absolute;
    top: 108px;
    left: 14px;
    display: flex;
    gap: 10px;
  }
  .wt-kpi {
    display: flex;
    gap: 10px;
    align-items: center;
    padding: 10px 16px 10px 12px;
  }
  .wt-kpi-icon {
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    color: var(--blue);
    background: var(--blue-soft);
  }
  .wt-kpi div {
    display: grid;
    line-height: 1.2;
  }
  .wt-kpi small {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--muted);
  }
  .wt-kpi strong {
    font-size: 1.3rem;
    font-weight: 800;
  }
  .wt-kpi em {
    font-style: normal;
    font-size: 0.7rem;
    color: var(--muted);
  }

  /* Controles del mapa */
  .map-tools {
    position: absolute;
    top: 108px;
    right: 352px;
    display: grid;
    padding: 4px;
    gap: 2px;
  }
  .map-tools button {
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    padding: 0;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 700;
    color: #334155;
    background: transparent;
    box-shadow: none;
  }
  .map-tools button:hover:not(:disabled) {
    background: var(--blue-soft);
    transform: none;
  }
  .map-tools button.on {
    color: #ffffff;
    background: var(--blue);
  }

  /* Detalle del próximo punto */
  .detail {
    position: absolute;
    top: 108px;
    right: 14px;
    width: 326px;
    display: grid;
    gap: 10px;
    padding: 14px 16px;
  }
  .detail-head {
    display: flex;
    gap: 12px;
    align-items: center;
  }
  .detail-head div {
    display: grid;
    line-height: 1.25;
  }
  .detail-head small {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--blue);
  }
  .detail-head strong {
    font-size: 1.02rem;
  }
  .detail-head em {
    font-style: normal;
    font-size: 0.72rem;
    color: var(--muted);
  }
  .detail-icon {
    flex: none;
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: var(--blue-soft);
  }
  .detail-icon.warehouse { background: #fff4dc; }
  .detail-icon.pickup_point { background: #dcf7ec; }
  .detail-icon.neighborhood { background: var(--blue-soft); }
  dl {
    display: grid;
    margin: 0;
  }
  dl div {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    padding: 6px 0;
    border-top: 1px solid var(--line);
    font-size: 0.82rem;
  }
  dt {
    color: var(--muted);
  }
  dd {
    margin: 0;
    font-weight: 700;
    text-align: right;
  }

  /* Recentrar */
  .recenter {
    position: absolute;
    left: 50%;
    bottom: 200px;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 999px;
    background: var(--blue);
    box-shadow: 0 10px 24px -8px rgba(37, 99, 235, 0.6);
    animation: rise 0.25s ease both;
  }
  .recenter:hover:not(:disabled) {
    transform: translateX(-50%) translateY(-1px);
  }

  /* Seguimiento */
  .tracking {
    position: absolute;
    left: 14px;
    bottom: 14px;
    width: min(720px, calc(100% - 370px));
    padding: 12px 16px 14px;
  }
  .tracking-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }
  .tracking-head h2 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 0.95rem;
    font-weight: 800;
  }
  .tracking-head h2 svg {
    color: var(--blue);
  }
  .tracking-body {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 250px;
    gap: 16px;
    align-items: center;
  }
  .stepper {
    display: flex;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .stepper li {
    position: relative;
    flex: 1;
    display: grid;
    justify-items: center;
    gap: 6px;
    text-align: center;
  }
  .stepper li + li::before {
    content: '';
    position: absolute;
    top: 14px;
    right: 50%;
    width: 100%;
    height: 3px;
    background: var(--line);
    z-index: 0;
  }
  .stepper li.done::before,
  .stepper li.active::before {
    background: var(--blue);
  }
  .dot {
    position: relative;
    z-index: 1;
    display: grid;
    place-items: center;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    font-size: 0.75rem;
    font-weight: 800;
    color: #94a3b8;
    background: #f1f5f9;
    border: 2px solid var(--line);
  }
  .done .dot {
    color: #ffffff;
    background: var(--blue);
    border-color: var(--blue);
  }
  .active .dot {
    color: var(--blue);
    background: #ffffff;
    border-color: var(--blue);
    box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.18);
  }
  .step-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--muted);
    line-height: 1.2;
  }
  .active .step-label,
  .done .step-label {
    color: var(--text);
  }
  .shipment {
    display: flex;
    gap: 10px;
    align-items: center;
    padding: 10px 12px;
    border-radius: 12px;
    border: 1px solid var(--line);
    background: #f8fafd;
  }
  .shipment div {
    display: grid;
    gap: 3px;
    min-width: 0;
  }
  .shipment strong {
    font-size: 0.86rem;
    overflow-wrap: anywhere;
  }
  .shipment small {
    font-size: 0.74rem;
    color: var(--muted);
  }
  .mini-truck {
    flex: none;
  }
  .no-route {
    margin: 0;
    font-size: 0.88rem;
    color: var(--error);
  }

  /* Recorrido */
  .stops {
    position: absolute;
    right: 14px;
    bottom: 14px;
    width: 326px;
    padding: 12px 16px 10px;
  }
  .stops ol {
    max-height: 190px;
    overflow-y: auto;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .stops li {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    border-top: 1px solid var(--line);
    font-size: 0.82rem;
  }
  .bullet {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #cbd5e1;
  }
  .stops li.done .bullet { background: var(--blue); }
  .stops li.current .bullet {
    background: #ffffff;
    border: 2px solid var(--blue);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
  }
  .stops li.pending { color: var(--muted); }
  .stop-name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .tag {
    padding: 1px 8px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--blue);
    background: var(--blue-soft);
  }
  .stops li.current .tag {
    color: #ffffff;
    background: var(--blue);
  }

  @keyframes blink {
    50% { opacity: 0.3; }
  }
  @keyframes rise {
    from { opacity: 0; transform: translate(-50%, 8px); }
    to { opacity: 1; transform: translate(-50%, 0); }
  }

  @media (max-width: 1100px) {
    .topbar { flex-wrap: wrap; }
    .route-form { order: 3; flex-basis: 100%; flex-wrap: wrap; justify-content: flex-start; }
    .route-form select { width: 150px; }
    .wt-kpis, .map-tools, .detail { top: 172px; }
    .stops { display: none; }
    .tracking { width: calc(100% - 28px); }
    .recenter { bottom: 230px; }
  }
  @media (max-width: 760px) {
    .wt-kpis, .detail { display: none; }
    .map-tools { right: 14px; top: auto; bottom: 280px; }
    .recenter { bottom: 290px; }
    .mini-truck { display: none; }
    .tracking-body { grid-template-columns: minmax(0, 1fr); }
    .step-label { display: none; }
  }
</style>
