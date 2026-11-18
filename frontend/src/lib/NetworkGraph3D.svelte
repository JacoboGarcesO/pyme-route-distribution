<script>
  // T13 (Mariana): la red de GET /network en 3D, como una ciudad de RutaPyme.
  // La escena vive en city3d.js; la página #/tracking la usa con cámara de seguimiento.
  import { onMount } from 'svelte'
  import { animateCity, animateCrew, createCity, createStage, disposeObject, makeTruck, placeTruck, createRun, stepTruck } from './city3d.js'

  let { network, route = null, coverage = null } = $props()

  const names = $derived(new Map(network.map((point) => [point.id, point.name])))
  const routeShown = $derived(route?.found && route.path.length > 1)
  const coverageList = $derived(coverage && Array.isArray(coverage.reachable))
  const unreachable = $derived(
    coverageList
      ? network.filter((p) => p.id !== coverage.origin_id && !coverage.reachable.some((r) => r.id === p.id))
      : [],
  )

  let container
  let stage, city, truck, run

  function build() {
    if (!stage) return
    if (city) {
      stage.scene.remove(city.group)
      disposeObject(city.group)
    }
    city = createCity(network, route, coverage)
    stage.scene.add(city.group)
    stage.camera.position.set(city.radius * 0.7, city.radius * 1.15, city.radius * 1.5)
    stage.controls.target.set(0, 0, 0)
    truck.visible = !!city.timeline
    run = createRun()
  }

  onMount(() => {
    stage = createStage(container)
    truck = makeTruck()
    stage.scene.add(truck)
    build()
    stage.start((time, dt) => {
      if (city.timeline) {
        placeTruck(truck, stepTruck(city.timeline, run, dt, time), dt)
        animateCrew(city.crew, run, truck, time)
      }
      animateCity(city.group, time)
    })
    return () => stage.dispose()
  })

  $effect(() => {
    // Se redibuja cuando cambia la red o la ruta.
    network
    route
    coverage
    build()
  })
</script>

<section>
  <div class="head">
    <h2>Mapa 3D de la ciudad</h2>
    <a class="open" href="#/tracking">Abrir seguimiento del camión →</a>
  </div>
  {#if network.length === 0}
    <p class="empty">La red está vacía. Crea puntos y conexiones para ver la ciudad en 3D.</p>
  {/if}
  {#if network.length > 0 && routeShown}
    <div class="summary route" role="status">
      <p class="title">Ruta resaltada en azul: <strong>{route.total_cost_km} km</strong> en {route.connections.length} tramos</p>
      <ol class="legs">
        {#each route.connections as leg, index (index)}
          <li>
            {names.get(leg.origin_id) ?? leg.origin_id} → {names.get(leg.destination_id) ?? leg.destination_id}
            <span class="cost">{leg.cost_km} km</span>
          </li>
        {/each}
      </ol>
      <p class="why">
        {route.connections.map((leg) => leg.cost_km).join(' + ')} = {route.total_cost_km} km.
        Es el camino de menor distancia total{route.via_id ? ` que pasa por la parada ${names.get(route.via_id) ?? ''}` : ''},
        siguiendo el sentido de cada calle; no se elige por tener menos tramos.
      </p>
    </div>
  {:else if network.length > 0 && route && !route.found}
    <div class="summary missing" role="status">
      <p class="title">No hay ruta para dibujar</p>
      <p>{route.reason}</p>
    </div>
  {:else if network.length > 0 && coverage}
    <div class="summary coverage" role="status">
      {#if coverageList}
        <p class="title">
          Cobertura desde <strong>{names.get(coverage.origin_id)}</strong>:
          {coverage.reachable.length} de {network.length - 1} puntos alcanzables (anillo verde)
        </p>
        {#if unreachable.length > 0}
          <p>Sin camino dirigido (anillo rojo): {unreachable.map((p) => p.name).join(', ')}.</p>
        {:else}
          <p>Todos los demás puntos se alcanzan desde este origen.</p>
        {/if}
      {:else}
        <p class="title">
          {names.get(coverage.destination_id)}
          {coverage.reachable ? 'se alcanza' : 'no se alcanza'} desde {names.get(coverage.origin_id)}
          ({coverage.reachable ? 'anillo verde' : 'anillo rojo'}).
        </p>
        {#if coverage.reason}<p>{coverage.reason}</p>{/if}
      {/if}
    </div>
  {/if}
  <div class="stage" class:hidden={network.length === 0} bind:this={container}></div>
  {#if network.length > 0}
    <ul class="legend">
      <li><span class="sw warehouse"></span>Bodega</li>
      <li><span class="sw pickup"></span>Cliente (casa, edificio o tienda, en azul y con dirección)</li>
      <li><span class="sw oneway"></span>Sentido único (señal UNA VÍA y flechas)</li>
      <li><span class="sw twoway"></span>Doble sentido (línea amarilla, ⇄)</li>
      <li><span class="sw route"></span>Ruta del camión</li>
      <li><span class="sw via"></span>Parada obligatoria</li>
      <li><span class="sw reach"></span>Alcanzable desde el origen</li>
      <li><span class="sw noreach"></span>Sin camino desde el origen</li>
    </ul>
    <p class="hint">
      {#if route?.found && route.path.length > 1}
        El camión recorre la ruta A → B{route.via_id ? ' deteniéndose en la parada' : ''}: {route.total_cost_km} km.
      {:else if coverage}
        Los anillos muestran la última cobertura consultada. Arrastra para girar y usa la rueda para acercar.
      {:else}
        Calcula una ruta para ver el camión recorrerla, o consulta la cobertura para ver qué puntos alcanza un origen. Arrastra para girar y usa la rueda para acercar.
      {/if}
    </p>
  {/if}
</section>

<style>
  .head {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: 8px;
  }
  .open {
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--primary);
    text-decoration: none;
  }
  .open:hover {
    text-decoration: underline;
  }
  .stage {
    height: 520px;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid var(--border);
    cursor: grab;
  }
  .stage.hidden {
    display: none;
  }
  .empty {
    margin: 0;
    padding: 18px;
    border-radius: 12px;
    border: 1.5px dashed var(--border-strong);
    background: var(--surface-2);
    color: var(--muted);
    text-align: center;
  }
  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 18px;
    margin: 14px 0 0;
    padding: 0;
    list-style: none;
    font-size: 0.85rem;
    color: var(--muted);
  }
  .legend li {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .sw {
    width: 14px;
    height: 14px;
    border-radius: 4px;
    border: 1px solid var(--border-strong);
  }
  .sw.warehouse { background: #ffffff; box-shadow: inset 0 -5px 0 #2563eb; }
  .sw.pickup { background: #2563eb; }
  .sw.oneway { background: #111111; box-shadow: inset 0 0 0 4px #111111, inset 0 0 0 6px #ffffff; }
  .sw.twoway { background: repeating-linear-gradient(90deg, #b9c1cf 0 3px, #facc15 3px 6px); }
  .sw.route { background: #2563eb; }
  .sw.via { background: #f97316; border-radius: 50%; }
  .sw.reach { background: transparent; border: 3px solid #16a34a; border-radius: 50%; }
  .sw.noreach { background: transparent; border: 3px solid #dc2626; border-radius: 50%; }
  .summary {
    margin: 0 0 12px;
    padding: 12px 16px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    font-size: 0.9rem;
  }
  .summary p {
    margin: 0;
  }
  .summary .title {
    margin-bottom: 6px;
    font-weight: 700;
  }
  .summary.route {
    border-color: rgba(37, 99, 235, 0.35);
    background: rgba(37, 99, 235, 0.07);
  }
  .summary.coverage {
    border-color: rgba(22, 163, 74, 0.35);
    background: rgba(22, 163, 74, 0.07);
  }
  .summary.missing {
    border-color: var(--error-line);
    background: var(--error-bg);
    color: #7f1d1d;
  }
  .legs {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 0 0 8px;
    padding: 0;
    list-style: none;
  }
  .legs li {
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--surface);
    border: 1px solid var(--border);
  }
  .cost {
    margin-left: 4px;
    font-weight: 800;
    color: #2563eb;
  }
  .why {
    color: var(--muted);
  }
  .hint {
    margin: 8px 0 0;
    font-size: 0.88rem;
    color: var(--muted);
  }
  @media (max-width: 700px) {
    .stage { height: 380px; }
  }
</style>
