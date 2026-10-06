<script>
  import { listPoints } from './lib/api.js'
  import BackendStatus from './lib/BackendStatus.svelte'
  import ConnectionForm from './lib/ConnectionForm.svelte'
  import PointForm from './lib/PointForm.svelte'
  import PointsList from './lib/PointsList.svelte'

  let points = $state([])
  let pointsLoading = $state(true)
  let pointsError = $state('')

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

  function refresh() {
    loadPoints()
  }

  refresh()
</script>

<main>
  <header>
    <h1>RutaPyme</h1>
    <p>Red operativa de puntos y trayectos</p>
    <BackendStatus />
  </header>

  <PointForm onCreated={refresh} />
  <ConnectionForm {points} onCreated={refresh} />

  <PointsList {points} loading={pointsLoading} error={pointsError} />
  <button type="button" onclick={refresh}>Actualizar</button>
</main>

<style>
  header p {
    margin: 0 0 8px;
  }
</style>
