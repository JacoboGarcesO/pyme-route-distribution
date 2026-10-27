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

  // visit_order trae UUID: los nombres salen de la lista de puntos de la red.
  const pointsById = $derived(new Map(points.map((point) => [point.id, point])))

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
      {#if result.reachable.length === 0}
        <p class="muted">Desde este origen no se alcanza ningún otro punto.</p>
      {:else}
        <p class="success" role="status">
          Se pueden alcanzar {result.reachable.length} destinos desde este origen:
        </p>
        <ul class="reachable">
          {#each result.reachable as point (point.id)}
            <li>{point.name} <span class="type">{pointTypeLabel(point.type)}</span></li>
          {/each}
        </ul>
      {/if}
      {#if result.visit_order?.length > 1}
        <h3>Orden de visita</h3>
        <p class="muted">
          Así recorre la red el sistema: primero el origen, luego sus vecinos más
          cercanos, y así por capas.
        </p>
        <ol class="visit-order">
          {#each result.visit_order as pointId, index (pointId)}
            {@const point = pointsById.get(pointId)}
            <li>
              {point ? point.name : pointId}
              {#if index === 0}<span class="type">origen</span>{/if}
            </li>
          {/each}
        </ol>
      {/if}
    {:else if result.reachable}
      <p class="success" role="status">Sí se puede llegar al destino desde este origen.</p>
    {:else}
      <div class="not-reachable" role="status">
        <p><strong>No se puede llegar al destino desde este origen.</strong></p>
        <p>{result.reason}</p>
      </div>
    {/if}
  {/if}
</section>

<style>
  .muted {
    color: var(--muted);
  }
  .reachable,
  .visit-order {
    margin: 0;
    padding-left: 20px;
  }
  h3 {
    margin: 16px 0 4px;
    font-size: 1rem;
  }
  .type {
    color: var(--muted);
    font-size: 0.9em;
  }
  .not-reachable {
    color: var(--error);
    background: var(--error-bg);
    border-left: 4px solid var(--error);
    padding: 8px 12px;
    border-radius: 6px;
  }
  .not-reachable p {
    margin: 0;
    color: var(--text);
  }
  .not-reachable p:first-child {
    color: var(--error);
  }
  form {
    display: grid;
    gap: 14px;
  }
</style>
