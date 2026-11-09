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
  <div class="layout">
    <div class="query">
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
    </div>

    <div class="results">
      <ErrorMessage {error} />

      {#if result}
        {#if Array.isArray(result.reachable)}
          {#if result.reachable.length === 0}
            <p class="muted empty">Desde este origen no se alcanza ningún otro punto.</p>
          {:else}
            <p class="success" role="status">
              Se pueden alcanzar {result.reachable.length} destinos desde este origen:
            </p>
            <ul class="reachable">
              {#each result.reachable as point (point.id)}
                <li>
                  <span class="name">{point.name}</span>
                  <span class="badge {point.type}">{pointTypeLabel(point.type)}</span>
                </li>
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
                <li class:origin={index === 0}>
                  <span class="step" aria-hidden="true">{index + 1}</span>
                  <span class="name">{point ? point.name : pointId}</span>
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
      {:else if !error && points.length > 0}
        <div class="placeholder" aria-hidden="true">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4" /><path d="M12 3v2M12 19v2M3 12h2M19 12h2" /></svg>
          <p>Elige un origen y consulta para ver qué destinos cubre.</p>
        </div>
      {/if}
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
  .query form button {
    width: 100%;
  }
  .results {
    min-width: 0;
  }
  .results > :global(.error:first-child),
  .results > .success:first-of-type {
    margin-top: 0;
  }
  .muted {
    color: var(--muted);
    margin: 0;
  }
  .empty {
    padding: 14px 16px;
    border-radius: 12px;
    background: var(--surface-2);
    border: 1px dashed var(--border-strong);
  }
  .placeholder {
    display: grid;
    place-items: center;
    gap: 10px;
    min-height: 210px;
    padding: 24px;
    text-align: center;
    border-radius: 14px;
    border: 1.5px dashed var(--border-strong);
    color: #a5aec2;
    background:
      repeating-linear-gradient(135deg, transparent 0 14px, rgba(91, 76, 240, 0.025) 14px 28px);
  }
  .placeholder p {
    margin: 0;
    max-width: 280px;
    font-weight: 600;
    color: var(--muted);
  }
  .reachable {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 10px;
    margin: 14px 0 0;
    padding: 0;
    list-style: none;
  }
  .reachable li {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    padding: 12px 14px;
    border-radius: 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    transition: transform 0.15s, border-color 0.15s;
  }
  .reachable li:hover {
    transform: translateY(-2px);
    border-color: var(--border-strong);
  }
  .name {
    font-weight: 700;
    overflow-wrap: anywhere;
  }
  h3 {
    margin: 26px 0 4px;
    font-size: 0.98rem;
    font-weight: 800;
  }
  .visit-order {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0 0;
    padding: 0;
    list-style: none;
    counter-reset: none;
  }
  .visit-order li {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px 6px 6px;
    border-radius: 999px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    font-size: 0.86rem;
  }
  .visit-order li.origin {
    background: var(--primary-soft);
    border-color: rgba(91, 76, 240, 0.3);
  }
  .step {
    display: grid;
    place-items: center;
    min-width: 24px;
    height: 24px;
    padding: 0 6px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 800;
    color: #ffffff;
    background: linear-gradient(135deg, var(--primary-2), var(--primary));
  }
  .visit-order .name {
    font-weight: 600;
  }
  .type {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--primary);
  }
  .not-reachable {
    position: relative;
    padding: 16px 18px 16px 52px;
    border-radius: 12px;
    background: var(--error-bg);
    border: 1px solid var(--error-line);
    animation: rise 0.3s ease both;
  }
  .not-reachable::before {
    content: '';
    position: absolute;
    left: 16px;
    top: 16px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--error) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round'%3E%3Cpath d='M6 6l12 12M18 6 6 18'/%3E%3C/svg%3E") center / 12px no-repeat;
  }
  .not-reachable p {
    margin: 0;
    color: #7f1d1d;
  }
  .not-reachable p:first-child {
    margin-bottom: 4px;
    color: var(--error);
  }
  form {
    display: grid;
    gap: 16px;
  }
  @keyframes rise {
    from {
      opacity: 0;
      transform: translateY(6px);
    }
    to {
      opacity: 1;
      transform: none;
    }
  }
  @media (max-width: 900px) {
    .layout {
      grid-template-columns: minmax(0, 1fr);
      gap: 20px;
    }
    .placeholder {
      min-height: 140px;
    }
  }
</style>
