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


<div class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="5" cy="6" r="2.5" />
          <circle cx="19" cy="18" r="2.5" />
          <path d="M7.5 6H13a3 3 0 0 1 0 6h-2a3 3 0 0 0 0 6h5.5" />
        </svg>
      </div>
      <div>
        <h1>RutaPyme</h1>
        <p>Red operativa de puntos y trayectos</p>
      </div>
    </div>
    <div class="topbar-actions">
      <BackendStatus />
      <button type="button" onclick={refresh}>Actualizar datos</button>
    </div>
  </div>
</div>

<main>
  <div class="layout">
    <div class="stack">
      <PointForm onCreated={refresh} />
      <ConnectionForm {points} onCreated={refresh} />
    </div>
    <div class="stack">
      <CoverageView {points} />
      <NetworkView {network} loading={networkLoading} error={networkError} />
    </div>
  </div>

  <div class="wide">
    <PointsList {points} loading={pointsLoading} error={pointsError} />
  </div>
</main>
