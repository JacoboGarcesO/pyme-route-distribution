<script>
  import { getNetwork, listPoints } from './lib/api.js'
  import BackendStatus from './lib/BackendStatus.svelte'
  import ConnectionForm from './lib/ConnectionForm.svelte'
  import CoverageView from './lib/CoverageView.svelte'
  import NetworkGraph3D from './lib/NetworkGraph3D.svelte'
  import NetworkView from './lib/NetworkView.svelte'
  import PointForm from './lib/PointForm.svelte'
  import PointsList from './lib/PointsList.svelte'
  import RouteView from './lib/RouteView.svelte'
  import TrackingPage from './lib/TrackingPage.svelte'

  let points = $state([])
  let pointsLoading = $state(true)
  let pointsError = $state('')

  let network = $state([])
  let networkLoading = $state(true)
  let networkError = $state(null)
  let route = $state(null)
  let coverage = $state(null)
  let dataVersion = $state(0)

  async function loadPoints() {
    pointsLoading = true
    pointsError = ''
    try {
      points = await listPoints()
    } catch (error) {
      pointsError = error.message
    } finally {
      pointsLoading = false
    }
  }

  async function loadNetwork() {
    networkLoading = true
    networkError = null
    try {
      network = await getNetwork()
    } catch (error) {
      networkError = error
    } finally {
      networkLoading = false
    }
  }

  // Un único refresco: lista, selectores y mapa leen los mismos datos, y los
  // resultados consultados antes se limpian porque la red pudo cambiar.
  function refresh() {
    route = null
    coverage = null
    dataVersion += 1
    loadPoints()
    loadNetwork()
  }

  function showCoverage(result) {
    coverage = result
    if (result) route = null
  }

  function showRoute(result) {
    route = result
    if (result) coverage = null
  }

  refresh()

  // Enrutado mínimo por hash: #/tracking abre el seguimiento 3D del camión.
  let hash = $state(location.hash)
  window.addEventListener('hashchange', () => (hash = location.hash))
</script>




{#if hash === '#/tracking'}
  <TrackingPage />
{:else}
<div class="shell">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="5" cy="6" r="2.5" />
          <circle cx="19" cy="18" r="2.5" />
          <path d="M7.5 6H13a3 3 0 0 1 0 6h-2a3 3 0 0 0 0 6h5.5" />
        </svg>
      </div>
      <div>
        <strong>RutaPyme</strong>
        <span>Logística y despacho</span>
      </div>
    </div>

    <p class="nav-label">Navegación</p>
    <nav class="nav" aria-label="Secciones">
      <a href="#operacion"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>Operación</a>
      <a href="#cobertura"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4" /><path d="M12 3v2M12 19v2M3 12h2M19 12h2" /></svg>Cobertura</a>
      <a href="#ruta"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="6" cy="19" r="2.5" /><circle cx="18" cy="5" r="2.5" /><path d="M8 18c7 0 2-12 8-12" /></svg>Ruta</a>
      <a href="#mapa"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2Z" /><path d="M9 4v14M15 6v14" /></svg>Mapa</a>
      <a href="#red"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="6" cy="6" r="2.5" /><circle cx="18" cy="8" r="2.5" /><circle cx="9" cy="18" r="2.5" /><path d="M8.2 7.2 15.6 7.6M7 8.3l1.5 7.3M16.6 10l-5.6 6.5" /></svg>Red operativa</a>
      <a href="#/tracking"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7h11v9H3zM14 10h4l3 3v3h-7" /><circle cx="7" cy="17" r="2" /><circle cx="17" cy="17" r="2" /></svg>Seguimiento 3D</a>
      <a href="#puntos"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Z" /><circle cx="12" cy="9.5" r="2.5" /></svg>Puntos</a>
    </nav>

    <div class="sidebar-foot">
      <p class="nav-label">Estado del sistema</p>
      <BackendStatus />
    </div>
  </aside>

  <div class="content">
    <header class="hero">
      <svg class="hero-art" viewBox="0 0 600 220" preserveAspectRatio="xMaxYMid slice" aria-hidden="true">
        <path d="M40 180 C 160 180, 160 60, 290 60 S 430 160, 560 40" />
        <path d="M120 210 C 220 140, 300 200, 380 120 S 520 110, 600 150" />
        <circle cx="290" cy="60" r="6" />
        <circle cx="560" cy="40" r="6" />
        <circle cx="380" cy="120" r="5" />
        <circle cx="40" cy="180" r="5" />
      </svg>
      <div class="hero-text">
        <p class="eyebrow">Panel del coordinador</p>
        <h1>Red de entregas</h1>
        <p class="lead">Registra puntos y trayectos, consulta cobertura y rutas, y míralas resaltadas en el mapa.</p>
      </div>
      <button type="button" class="btn-light" onclick={refresh}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-2.6-6.4" /><path d="M21 4v5h-5" /></svg>
        Actualizar datos
      </button>
    </header>

    <section class="kpis" aria-label="Resumen de la red">
      <article class="kpi">
        <span class="kpi-icon points"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Z" /><circle cx="12" cy="9.5" r="2.5" /></svg></span>
        <div>
          <strong>{points.length}</strong>
          <span>Puntos registrados</span>
        </div>
      </article>
      <article class="kpi">
        <span class="kpi-icon routes"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></span>
        <div>
          <strong>{network.reduce((total, point) => total + point.connections.length, 0)}</strong>
          <span>Conexiones dirigidas</span>
        </div>
      </article>
      <article class="kpi">
        <span class="kpi-icon warehouse"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21V9l9-5 9 5v12" /><path d="M7 21v-6h10v6" /></svg></span>
        <div>
          <strong>{points.filter((point) => point.type === 'warehouse').length}</strong>
          <span>Bodegas</span>
        </div>
      </article>
      <article class="kpi">
        <span class="kpi-icon pickup"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 8l8-4 8 4-8 4-8-4Z" /><path d="M4 8v8l8 4 8-4V8" /><path d="M12 12v8" /></svg></span>
        <div>
          <strong>{points.filter((point) => point.type === 'pickup_point').length}</strong>
          <span>Puntos de recogida</span>
        </div>
      </article>
    </section>

    <main>
      <div class="group" id="operacion">
        <div class="group-head">
          <span class="group-index">01</span>
          <div>
            <h2>Operación de la red</h2>
            <p>Registra los puntos y los trayectos dirigidos entre ellos.</p>
          </div>
        </div>
        <div class="grid-2">
          <PointForm onCreated={refresh} />
          <ConnectionForm {points} onCreated={refresh} />
        </div>
      </div>

      <div class="group" id="cobertura">
        <div class="group-head">
          <span class="group-index">02</span>
          <div>
            <h2>Cobertura de entregas</h2>
            <p>Consulta qué destinos alcanza un origen siguiendo el sentido de cada trayecto.</p>
          </div>
        </div>
        <CoverageView {points} version={dataVersion} onResult={showCoverage} />
      </div>

      <div class="group" id="ruta">
        <div class="group-head">
          <span class="group-index">03</span>
          <div>
            <h2>Ruta de menor costo</h2>
            <p>Elige el punto A, el punto B y, si hace falta, una parada: el camión recorre la ruta en el mapa 3D.</p>
          </div>
        </div>
        <RouteView {points} version={dataVersion} onResult={showRoute} />
      </div>

      <div class="group" id="mapa">
        <div class="group-head">
          <span class="group-index">04</span>
          <div>
            <h2>Mapa de la red</h2>
            <p>La red dibujada con la última consulta resaltada: la ruta en azul o la cobertura con anillos verdes y rojos.</p>
          </div>
        </div>
        <NetworkGraph3D {network} {route} {coverage} />
      </div>

      <div class="group">
        <div class="group-head">
          <span class="group-index">05</span>
          <div>
            <h2>Estado de la red</h2>
            <p>Conexiones salientes de cada punto y listado completo de la red.</p>
          </div>
        </div>
        <div id="red">
          <NetworkView {network} loading={networkLoading} error={networkError} />
        </div>
        <div id="puntos">
          <PointsList {points} loading={pointsLoading} error={pointsError} />
        </div>
      </div>
    </main>

    <footer class="footer">RutaPyme · Plataforma logística de despacho y cobertura de entregas</footer>
  </div>
</div>
{/if}
