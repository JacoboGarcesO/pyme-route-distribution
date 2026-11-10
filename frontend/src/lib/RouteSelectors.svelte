<script>
  import { pointTypeLabel } from './pointTypes.js'

  let { points, loading = false, onSearch } = $props()

  let originId = $state('')
  let destinationId = $state('')

  // Los nombres pueden repetirse, así que cada opción muestra tipo y UUID corto.
  function optionLabel(point) {
    return `${point.name} (${pointTypeLabel(point.type)}) · ${point.id.slice(0, 8)}`
  }

  function submit(event) {
    event.preventDefault()
    onSearch(originId, destinationId)
  }
</script>

{#if points.length === 0}
  <p class="muted">Registra puntos y conexiones para consultar una ruta.</p>
{:else}
  <form onsubmit={submit}>
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
      Destino
      <select bind:value={destinationId} required>
        <option value="">Elige el punto de destino</option>
        {#each points as point (point.id)}
          <option value={point.id}>{optionLabel(point)}</option>
        {/each}
      </select>
    </label>
    <button type="submit" disabled={loading || !originId || !destinationId}>
      {loading ? 'Calculando...' : 'Calcular ruta'}
    </button>
  </form>
{/if}

<style>
  .muted {
    color: var(--muted);
    margin: 0;
  }
  form button {
    width: 100%;
  }
</style>
