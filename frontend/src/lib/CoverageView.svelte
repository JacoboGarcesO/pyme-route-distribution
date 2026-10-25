<script>
  import { getCoverage } from './api.js'
  import ErrorMessage from './ErrorMessage.svelte'
  import { pointTypeLabel } from './pointTypes.js'

  let { points } = $props()

  let originId = $state('')
  let destinationId = $state('')
  let loading = $state(false)
  let error = $state(null)
  let result = $state(null)

  // Los nombres pueden repetirse, así que cada opción muestra tipo y UUID corto.
  function optionLabel(point) {
    return `${point.name} (${pointTypeLabel(point.type)}) · ${point.id.slice(0, 8)}`
  }

  async function consult(event) {
    event.preventDefault()
    loading = true
    error = null
    result = null
    try {
      result = await getCoverage(originId, destinationId)
    } catch (e) {
      error = e
    } finally {
      loading = false
    }
  }
</script>

<section>
  <h2>Cobertura desde un origen</h2>
  {#if points.length === 0}
    <p class="muted">Registra puntos y conexiones para consultar la cobertura.</p>
  {:else}
    <form onsubmit={consult}>
      <label>
        Origen
        <select bind:value={originId} required>
          <option value="">Elige el punto de origen</option>
          {#each points as point (point.id)}
            <option value={point.id}>{optionLabel(point)}</option>
          {/each}
        </select>
      </label>
      <label>
        Destino (opcional)
        <select bind:value={destinationId}>
          <option value="">Todos los alcanzables</option>
          {#each points as point (point.id)}
            <option value={point.id}>{optionLabel(point)}</option>
          {/each}
        </select>
      </label>
      <button type="submit" disabled={loading || !originId}>
        {loading ? 'Consultando...' : 'Consultar cobertura'}
      </button>
    </form>
  {/if}

  <ErrorMessage {error} />

  {#if result}
    {#if Array.isArray(result.reachable)}
      <p class="success" role="status">Se encontraron {result.reachable.length} destinos alcanzables.</p>
    {:else}
      <p class="success" role="status">
        {result.reachable ? 'El destino es alcanzable.' : 'El destino no es alcanzable.'}
      </p>
    {/if}
  {/if}
</section>

<style>
  .muted {
    color: var(--muted);
  }
  form {
    display: grid;
    gap: 12px;
    padding: 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
  }
</style>
