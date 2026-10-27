<script>
  import { getNetwork, listPoints } from './lib/api.js'
  import BackendStatus from './lib/BackendStatus.svelte'
  import ConnectionForm from './lib/ConnectionForm.svelte'
  import CoverageView from './lib/CoverageView.svelte'
  import NetworkView from './lib/NetworkView.svelte'
  import PointForm from './lib/PointForm.svelte'
  import PointsList from './lib/PointsList.svelte'

  let points = $state([])
  let pointsLoading = $state(true)
  let pointsError = $state('')

  let network = $state([])
  let networkLoading = $state(true)
  let networkError = $state(null)

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

  function refresh() {
    loadPoints()
    loadNetwork()
  }

  refresh()
</script>



<div class="shell">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="5" cy="6" r="2.5" />
          <circle cx="19" cy="18" r="2.5" />
          <path d="M7.5 6H13a3 3 0 0 1 0 6h-2a3 3 0 0 0 0 6h5.5" />
        </svg>
      </div>
      <div>
        <strong>RutaPyme</strong>
        <span>Despacho inteligente</span>
      </div>
    </div>

    <nav class="nav" aria-label="Secciones">
      <a href="#operacion">Operación</a>
      <a href="#cobertura">Cobertura</a>
      <a href="#red">Red operativa</a>
      <a href="#puntos">Puntos</a>
    </nav>

    <div class="sidebar-foot">
      <BackendStatus />
    </div>
  </aside>

  <div class="content">
    <header class="page-head">
      <div>
        <p class="eyebrow">Panel del coordinador</p>
        <h1>Red de entregas</h1>
        <p class="lead">Registra puntos y trayectos, y consulta qué destinos cubre cada bodega.</p>
      </div>
      <button type="button" class="refresh" onclick={refresh}>Actualizar datos</button>
    </header>

    <section class="kpis" aria-label="Resumen de la red">
      <article class="kpi">
        <span>Puntos registrados</span>
        <strong>{points.length}</strong>
      </article>
      <article class="kpi">
        <span>Conexiones dirigidas</span>
        <strong>{network.reduce((total, point) => total + point.connections.length, 0)}</strong>
      </article>
      <article class="kpi">
        <span>Bodegas</span>
        <strong>{points.filter((point) => point.type === 'warehouse').length}</strong>
      </article>
    </section>

    <main>
      <div id="operacion" class="grid-2">
        <PointForm onCreated={refresh} />
        <ConnectionForm {points} onCreated={refresh} />
      </div>

      <div class="grid-2">
        <div id="cobertura">
          <CoverageView {points} />
        </div>
        <div id="red">
          <NetworkView {network} loading={networkLoading} error={networkError} />
        </div>
      </div>

      <div id="puntos">
        <PointsList {points} loading={pointsLoading} error={pointsError} />
      </div>
    </main>
  </div>
</div>
