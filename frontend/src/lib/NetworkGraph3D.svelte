<script>
  // T13 (Mariana): la red de GET /network en 3D, como una ciudad de WareTrack.
  // La escena vive en city3d.js; la página #/tracking la usa con cámara de seguimiento.
  import { onMount } from 'svelte'
  import { animateCity, createCity, createStage, disposeObject, makeTruck, placeTruck, createRun, stepTruck } from './city3d.js'

  let { network, route = null } = $props()

  let container
  let stage, city, truck, run

  function build() {
    if (!stage) return
    if (city) {
      stage.scene.remove(city.group)
      disposeObject(city.group)
    }
    city = createCity(network, route)
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
      if (city.timeline) placeTruck(truck, stepTruck(city.timeline, run, dt, time), dt)
      animateCity(city.group, time)
    })
    return () => stage.dispose()
  })

  $effect(() => {
    // Se redibuja cuando cambia la red o la ruta.
    network
    route
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
  <div class="stage" class:hidden={network.length === 0} bind:this={container}></div>
  {#if network.length > 0}
    <ul class="legend">
      <li><span class="sw warehouse"></span>Bodega</li>
      <li><span class="sw pickup"></span>Cliente (techo azul, con dirección)</li>
      <li><span class="sw oneway"></span>Sentido único (señal UNA VÍA y flechas)</li>
      <li><span class="sw twoway"></span>Doble sentido (línea amarilla, ⇄)</li>
      <li><span class="sw route"></span>Ruta del camión</li>
      <li><span class="sw via"></span>Parada obligatoria</li>
    </ul>
    <p class="hint">
      {#if route?.found && route.path.length > 1}
        El camión recorre la ruta A → B{route.via_id ? ' deteniéndose en la parada' : ''}: {route.total_cost_km} km.
      {:else}
        Calcula una ruta para ver el camión recorrerla. Arrastra para girar y usa la rueda para acercar.
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
  .hint {
    margin: 8px 0 0;
    font-size: 0.88rem;
    color: var(--muted);
  }
  @media (max-width: 700px) {
    .stage { height: 380px; }
  }
</style>
