<script>
  import { getShortestPath } from './api.js'
  import ErrorMessage from './ErrorMessage.svelte'
  import RouteSelectors from './RouteSelectors.svelte'

  let { points } = $props()

  let loading = $state(false)
  let error = $state(null)
  // Respuesta de GET /shortest-path; la vista de la ruta (T21 y T22) se apoya en este estado.
  let result = $state(null)

  async function search(originId, destinationId) {
    loading = true
    error = null
    result = null
    try {
      result = await getShortestPath(originId, destinationId)
    } catch (e) {
      error = e
    } finally {
      loading = false
    }
  }
</script>

<section>
  <h2>Ruta de menor costo</h2>
  <div class="layout">
    <div class="query">
      <RouteSelectors {points} {loading} onSearch={search} />
    </div>
    <div class="results">
      <ErrorMessage {error} />
    </div>
  </div>
</section>

<style>
  .layout {
    display: grid;
    grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
    gap: 28px;
    align-items: start;
  }
  .query {
    padding: 20px;
    border-radius: 14px;
    background: var(--surface-2);
    border: 1px solid var(--border);
  }
  .results {
    min-width: 0;
  }
</style>
