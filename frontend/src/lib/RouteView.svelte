<script>
  import { getShortestPath } from './api.js'
  import ErrorMessage from './ErrorMessage.svelte'
  import { pointTypeLabel } from './pointTypes.js'
  import RouteSelectors from './RouteSelectors.svelte'

  let { points } = $props()

  let loading = $state(false)
  let error = $state(null)
  let result = $state(null)

  // connections trae UUID: los nombres salen de los puntos de la misma ruta.
  const pathById = $derived(new Map((result?.path ?? []).map((point) => [point.id, point])))
  const hops = $derived(result?.connections?.length ?? 0)

  function pointName(id) {
    return pathById.get(id)?.name ?? id
  }

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
  <h2>Ruta entre dos puntos</h2>
  <div class="layout">
    <div class="query">
      <RouteSelectors {points} {loading} onSearch={search} />
    </div>
    <div class="results">
      <ErrorMessage {error} />

      {#if result}
        {#if !result.found}
          <div class="not-found" role="status">
            <p><strong>No hay ruta entre estos puntos.</strong></p>
            <p>{result.reason}</p>
            <p class="hint">
              Las conexiones tienen sentido: revisa que exista un camino que salga del origen
              y llegue al destino en esa dirección.
            </p>
          </div>
        {:else if hops === 0}
          <p class="success" role="status">
            El origen y el destino son el mismo punto: la ruta no recorre conexiones y cuesta
            <strong>0 km</strong>.
          </p>
          <ol class="route">
            <li class="stop">
              <span class="step" aria-hidden="true">1</span>
              <span class="name">{result.path[0].name}</span>
              <span class="badge {result.path[0].type}">{pointTypeLabel(result.path[0].type)}</span>
            </li>
          </ol>
        {:else}
          <div class="summary" role="status">
            <div class="total">
              <span class="label">Costo total</span>
              <span class="value">{result.total_cost_km} km</span>
            </div>
            <div class="total">
              <span class="label">Tramos</span>
              <span class="value">{hops}</span>
            </div>
          </div>

          <h3>Secuencia de puntos</h3>
          <ol class="route">
            {#each result.path as point, index (point.id)}
              <li class="stop" class:origin={index === 0} class:destination={index === result.path.length - 1}>
                <span class="step" aria-hidden="true">{index + 1}</span>
                <span class="name">{point.name}</span>
                <span class="badge {point.type}">{pointTypeLabel(point.type)}</span>
                {#if index === 0}<span class="type">origen</span>{/if}
                {#if index === result.path.length - 1}<span class="type">destino</span>{/if}
              </li>
              {#if index < result.connections.length}
                <li class="leg" aria-label="Tramo de {result.connections[index].cost_km} km">
                  <span class="arrow" aria-hidden="true">↓</span>
                  {result.connections[index].cost_km} km
                </li>
              {/if}
            {/each}
          </ol>

          <h3>Conexiones recorridas</h3>
          <table>
            <thead>
              <tr>
                <th>Desde</th>
                <th>Hasta</th>
                <th class="num">Costo</th>
              </tr>
            </thead>
            <tbody>
              {#each result.connections as connection, index (index)}
                <tr>
                  <td>{pointName(connection.origin_id)}</td>
                  <td>{pointName(connection.destination_id)}</td>
                  <td class="num">{connection.cost_km} km</td>
                </tr>
              {/each}
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2">Total</td>
                <td class="num">{result.total_cost_km} km</td>
              </tr>
            </tfoot>
          </table>

          <p class="why">
            <strong>¿Por qué esta ruta?</strong>
            {result.connections.map((c) => c.cost_km).join(' + ')} = {result.total_cost_km} km.
            El sistema compara la distancia total de cada camino posible y elige la menor,
            respetando el sentido de las conexiones. No elige el camino con menos tramos:
            una ruta con más paradas puede ser más corta.
          </p>
        {/if}
      {:else if !error && points.length > 0}
        <div class="placeholder" aria-hidden="true">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="19" r="2.5" /><circle cx="18" cy="5" r="2.5" /><path d="M8 18c7 0 2-12 8-12" /></svg>
          <p>Elige un origen y un destino para ver la ruta de menor costo.</p>
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
  .results {
    min-width: 0;
  }
  .results > :global(.error:first-child),
  .results > .success:first-of-type,
  .results > .summary:first-child {
    margin-top: 0;
  }
  .summary {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    animation: rise 0.3s ease both;
  }
  .total {
    display: grid;
    gap: 2px;
    min-width: 140px;
    padding: 12px 16px;
    border-radius: 12px;
    background: var(--primary-soft);
    border: 1px solid rgba(91, 76, 240, 0.3);
  }
  .total .label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--primary);
  }
  .total .value {
    font-size: 1.35rem;
    font-weight: 800;
  }
  h3 {
    margin: 26px 0 10px;
    font-size: 0.98rem;
    font-weight: 800;
  }
  .route {
    display: grid;
    gap: 4px;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .stop {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    padding: 8px 12px 8px 8px;
    border-radius: 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
  }
  .stop.origin,
  .stop.destination {
    background: var(--primary-soft);
    border-color: rgba(91, 76, 240, 0.3);
  }
  .leg {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 0 0 18px;
    font-size: 0.86rem;
    font-weight: 600;
    color: var(--muted);
  }
  .arrow {
    font-weight: 800;
    color: var(--primary);
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
  .name {
    font-weight: 700;
    overflow-wrap: anywhere;
  }
  .type {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--primary);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }
  th,
  td {
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }
  th {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
  }
  tfoot td {
    font-weight: 800;
    border-bottom: none;
  }
  .num {
    text-align: right;
    white-space: nowrap;
  }
  .why {
    margin: 18px 0 0;
    padding: 12px 14px;
    border-radius: 12px;
    background: var(--surface-2);
    border: 1px dashed var(--border-strong);
    font-size: 0.9rem;
  }
  .success {
    margin: 0 0 12px;
  }
  .not-found {
    position: relative;
    padding: 16px 18px 16px 52px;
    border-radius: 12px;
    background: var(--error-bg);
    border: 1px solid var(--error-line);
    animation: rise 0.3s ease both;
  }
  .not-found::before {
    content: '';
    position: absolute;
    left: 16px;
    top: 16px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--error) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round'%3E%3Cpath d='M6 6l12 12M18 6 6 18'/%3E%3C/svg%3E") center / 12px no-repeat;
  }
  .not-found p {
    margin: 0;
    color: #7f1d1d;
  }
  .not-found p:first-child {
    margin-bottom: 4px;
    color: var(--error);
  }
  .not-found .hint {
    margin-top: 6px;
    font-size: 0.88rem;
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
