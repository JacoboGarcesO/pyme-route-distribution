<script>
  import { pointTypeLabel, selectablePoints } from './pointTypes.js'

  let { points, loading = false, onSearch } = $props()
  const endpoints = $derived(selectablePoints(points))

  let originId = $state('')
  let destinationId = $state('')
  let viaId = $state('')
  // Solo casas y bodegas pueden ser parada: ahí se entrega o se recoge.
  const stopPoints = $derived(points.filter((point) => point.type !== 'neighborhood'))

  // Los nombres pueden repetirse, así que cada opción muestra tipo y UUID corto.
  function optionLabel(point) {
    return `${point.name} (${pointTypeLabel(point.type)}) · ${point.id.slice(0, 8)}`
  }

  function submit(event) {
    event.preventDefault()
    onSearch(originId, destinationId, viaId)
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
        {#each endpoints as point (point.id)}
          <option value={point.id}>{optionLabel(point)}</option>
        {/each}
      </select>
    </label>
    <label>
      Destino
      <select bind:value={destinationId} required>
        <option value="">Elige el punto de destino</option>
        {#each endpoints as point (point.id)}
          <option value={point.id}>{optionLabel(point)}</option>
        {/each}
      </select>
    </label>
    <label>
      Parada obligatoria (opcional)
      <select bind:value={viaId}>
        <option value="">Sin parada</option>
        {#each stopPoints as point (point.id)}
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
