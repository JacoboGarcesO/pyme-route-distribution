<script>
  // Página #/tracking: seguimiento 3D del camión de A a B, con parada opcional.
  // La cámara sigue al camión; si el usuario mueve el mapa, "Recentrar" la devuelve.
  import { onMount } from 'svelte'
  import * as THREE from 'three'
  import { getNetwork, getShortestPath } from './api.js'
  import { animateCity, animateCrew, currentHour, dayPart, createCity, createStage, disposeObject, makeTruck, placeTruck, createRun, stepTruck } from './city3d.js'
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
  let detailOpen = $state(true) // paneles de la derecha, colapsables
  let stopsOpen = $state(true)
  let status = $state(null) // { phase, segment, distance, remainingKm }
  let clock = $state('')
  let addresses = $state(new Map()) // id del cliente -> dirección en el mapa

  let container
  let stage, city, truck
  let run = createRun() // estado de la simulación del camión
  let lastUi = 0
  let zoom = 1
  const desired = new THREE.Vector3()

  const byId = $derived(new Map(network.map((p) => [p.id, p])))
  const connectionCount = $derived(network.reduce((s, p) => s + p.connections.length, 0))
  const warehouses = $derived(network.filter((p) => p.type === 'warehouse').length)
  // Solo se para donde hay a quién entregar o de dónde recoger: casas y bodegas.
  const stopPoints = $derived(network.filter((p) => p.type !== 'neighborhood'))
  const moving = $derived(route?.found && route.path.length > 1)
  const hasVia = $derived(!!route?.via_id && moving)

  const steps = $derived(
    hasVia
      ? [
          ['confirmed', 'Ruta confirmada'],
          ['loading', 'Cargando en A'],
          ['toStop', 'Hacia la parada'],
          ['stop', 'Entregando en parada'],
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
  const phaseLabel = $derived(status?.waiting ? 'Esperando semáforo' : (steps[stepIndex]?.[1] ?? ''))
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
    run = createRun()
    status = null
    if (!city.timeline) overview()
  }

  function overview() {
    following = false
    stage.camera.position.set(55, 95, 120)
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
    stage = createStage(container, { focusBlur: true })
    stage.controls.maxDistance = 160 // la vista abarca unas 3 x 3 manzanas
    // Mover el mapa con el ratón o el dedo suelta la cámara del camión.
    stage.controls.addEventListener('start', () => (following = false))
    truck = makeTruck()
    stage.scene.add(truck)
    build()
    stage.start((time, dt) => {
      if (city.timeline) {
        const state = stepTruck(city.timeline, run, dt, time)
        placeTruck(truck, state, dt)
        animateCrew(city.crew, run, truck, time)
        if (following) follow(dt)
        if (time - lastUi > 0.15) {
          lastUi = time
          status = state
        }
      }
      animateCity(city.group, time, stage.controls.target)
    })
    loadNetwork()

    // La misma hora que ilumina la escena (o la simulada con ?hora=).
    const tickClock = () => {
      const hour = currentHour()
      const at = new Date()
      at.setHours(Math.floor(hour), Math.round((hour % 1) * 60))
      clock = `${at.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })} · ${dayPart(hour)}`
    }
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
    <a class="wt-brand" href="#/" title="Volver al panel">
      <span class="logo" aria-hidden="true">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 2 3 7v10l9 5 9-5V7l-9-5Zm0 2.3L18.7 8 12 11.7 5.3 8 12 4.3Z" /></svg>
      </span>
      RutaPyme
    </a>

    <form class="route-form" onsubmit={search}>
      <label>
        <span>Punto A</span>
        <select bind:value={originId} required>
          <option value="">Origen</option>
          {#each stopPoints as point (point.id)}<option value={point.id}>{point.name}</option>{/each}
        </select>
      </label>
      <label>
        <span>Parada</span>
        <select bind:value={viaId}>
          <option value="">Sin parada</option>
          {#each stopPoints as point (point.id)}<option value={point.id}>{point.name}</option>{/each}
        </select>
      </label>
      <label>
        <span>Punto B</span>
        <select bind:value={destinationId} required>
          <option value="">Destino</option>
          {#each stopPoints as point (point.id)}<option value={point.id}>{point.name}</option>{/each}
        </select>
      </label>
      <button type="submit" disabled={loading || !originId || !destinationId}>
        {loading ? 'Calculando…' : 'Despachar'}
      </button>
    </form>

    <div class="top-right">
      <span class="live"><i></i>En vivo {clock}</span>
      <a class="back" href="#/">← Panel</a>
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

  <div class="side">
    <aside class="detail card" aria-live="polite">
      <button type="button" class="panel-toggle" aria-expanded={detailOpen} onclick={() => (detailOpen = !detailOpen)}>
        <span class="detail-icon {nextPoint?.type ?? ''}" aria-hidden="true"></span>
        <span class="toggle-text">
          <small>{!nextPoint ? 'Despacho' : status?.phase === 'delivered' ? 'Entregado en' : status?.phase === 'stop' ? 'Detenido en' : 'Próximo punto'}</small>
          <strong>{nextPoint?.name ?? 'Sin camión en ruta'}</strong>
        </span>
        <svg class="chevron" class:open={detailOpen} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
      </button>
      {#if detailOpen}
        {#if nextPoint}
          <dl>
            {#if addresses.get(nextPoint.id)}<div><dt>Dirección</dt><dd>{addresses.get(nextPoint.id)}</dd></div>{/if}
            <div><dt>Rol en la ruta</dt><dd>{nextIndex === route.path.length - 1 ? 'Destino B' : route.path[nextIndex].id === route.via_id ? 'Parada obligatoria' : pointTypeLabel(nextPoint.type)}</dd></div>
            <div><dt>Tramo</dt><dd>{Math.min(status.segment + 1, route.connections.length)} de {route.connections.length}</dd></div>
          </dl>
        {:else}
          <p class="muted">Elige el punto A, el punto B y, si hace falta, una parada. Luego pulsa <b>Despachar</b>.</p>
        {/if}
      {/if}
    </aside>

    {#if moving}
      <section class="stops card" aria-label="Recorrido">
        <button type="button" class="panel-toggle" aria-expanded={stopsOpen} onclick={() => (stopsOpen = !stopsOpen)}>
          <span class="toggle-text"><strong>Recorrido</strong></span>
          <span class="muted">{route.path.length} puntos</span>
          <svg class="chevron" class:open={stopsOpen} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
        </button>
        {#if stopsOpen}
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
        {/if}
      </section>
    {/if}
  </div>

  {#if moving && !following}
    <button type="button" class="recenter" onclick={recenter}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d="M12 2v4M12 18v4M2 12h4M18 12h4" /></svg>
      Recentrar en el camión
    </button>
  {/if}

  <section class="tracking card" aria-label="Seguimiento del envío">
    {#if networkError}
      <ErrorMessage error={networkError} />
    {:else if routeError}
      <ErrorMessage error={routeError} />
    {:else if route && !route.found}
      <p class="no-route"><strong>No hay ruta.</strong> {route.reason}</p>
    {:else if moving}
      <div class="tracking-head">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7h11v9H3zM14 10h4l3 3v3h-7" /><circle cx="7" cy="17" r="2" /><circle cx="17" cy="17" r="2" /></svg>
        <strong class="route-name">{route.path[0].name} → {route.path.at(-1).name}</strong>
        <span class="chip" class:wait={status?.waiting}>{phaseLabel}</span>
        <span class="km">{(status?.remainingKm ?? Number(route.total_cost_km)).toFixed(1)} km</span>
      </div>
      <ol class="stepper">
        {#each steps as [key, text], index (key)}
          <li class:done={index < stepIndex || status?.phase === 'delivered'} class:active={index === stepIndex && status?.phase !== 'delivered'}>
            <span class="dot" aria-hidden="true">{index < stepIndex || status?.phase === 'delivered' ? '✓' : index + 1}</span>
            <span class="step-label">{text}</span>
          </li>
        {/each}
      </ol>
    {:else}
      <p class="muted">Sin envíos en curso. Despacha un camión desde la barra superior.</p>
    {/if}
  </section>

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

  .chip.wait {
    color: #b91c1c;
    background: #fee2e2;
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
    right: 326px;
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

  /* Columna derecha: detalle y recorrido, colapsables */
  .side {
    position: absolute;
    top: 108px;
    right: 14px;
    bottom: 14px;
    width: 300px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    pointer-events: none;
  }
  .side > * {
    pointer-events: auto;
  }
  .detail {
    display: grid;
    gap: 8px;
    padding: 10px 12px;
  }
  .panel-toggle {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 0;
    border: 0;
    border-radius: 8px;
    color: var(--text);
    background: transparent;
    box-shadow: none;
    text-align: left;
    font-weight: 400;
  }
  .panel-toggle:hover:not(:disabled) {
    background: transparent;
    transform: none;
  }
  .panel-toggle:focus-visible {
    outline: 2px solid var(--blue);
    outline-offset: 3px;
  }
  .toggle-text {
    flex: 1;
    display: grid;
    min-width: 0;
    line-height: 1.25;
  }
  .toggle-text small {
    font-size: 0.66rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--blue);
  }
  .toggle-text strong {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.92rem;
  }
  .chevron {
    flex: none;
    color: var(--muted);
    transition: transform 0.2s;
  }
  .chevron.open {
    transform: rotate(180deg);
  }
  .detail-icon {
    flex: none;
    width: 32px;
    height: 32px;
    border-radius: 10px;
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
    padding: 5px 0;
    border-top: 1px solid var(--line);
    font-size: 0.8rem;
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
    bottom: 120px;
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
    width: min(500px, calc(100% - 340px));
    padding: 10px 14px 12px;
  }
  .tracking-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    font-size: 0.82rem;
  }
  .tracking-head svg {
    flex: none;
    color: var(--blue);
  }
  .route-name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .tracking-head .chip {
    align-self: center;
  }
  .km {
    flex: none;
    font-weight: 700;
    color: var(--muted);
    font-variant-numeric: tabular-nums;
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
    top: 10px;
    right: 50%;
    width: 100%;
    height: 2px;
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
    width: 22px;
    height: 22px;
    border-radius: 50%;
    font-size: 0.66rem;
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
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.18);
  }
  .step-label {
    font-size: 0.64rem;
    font-weight: 600;
    color: var(--muted);
    line-height: 1.2;
  }
  .active .step-label,
  .done .step-label {
    color: var(--text);
  }
  .no-route {
    margin: 0;
    font-size: 0.88rem;
    color: var(--error);
  }

  /* Recorrido */
  .stops {
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-height: 0;
    margin-top: auto;
    padding: 10px 12px;
  }
  .stops ol {
    min-height: 0;
    max-height: 210px;
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
    .wt-kpis, .map-tools, .side { top: 172px; }
    .side { bottom: 150px; }
    .tracking { width: calc(100% - 28px); }
    .recenter { bottom: 150px; }
  }
  @media (max-width: 760px) {
    .wt-kpis, .side { display: none; }
    .map-tools { right: 14px; top: auto; bottom: 150px; }
    .recenter { bottom: 160px; }
    .step-label { display: none; }
  }
</style>
