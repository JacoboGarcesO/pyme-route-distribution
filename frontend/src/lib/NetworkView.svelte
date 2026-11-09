<script>
  import ErrorMessage from './ErrorMessage.svelte'
  import { pointTypeLabel } from './pointTypes.js'

  // network: lista de puntos de GET /network, cada uno con sus conexiones salientes.
  let { network, loading, error } = $props()
</script>

<section>
  <h2>Red operativa</h2>

  {#if loading}
    <p class="muted">Cargando red...</p>
  {:else if error}
    <ErrorMessage {error} />
  {:else if network.length === 0}
    <p class="muted empty">La red está vacía. Crea puntos y conexiones para verla aquí.</p>
  {:else}
    <ul class="network">
      {#each network as point (point.id)}
        <li class="node {point.type}">
          <div class="origin">
            <strong>{point.name}</strong>
            <span class="badge {point.type}">{pointTypeLabel(point.type)}</span>
          </div>
          {#if point.connections.length === 0}
            <p class="muted none">Sin conexiones salientes</p>
          {:else}
            <ul class="connections">
              {#each point.connections as connection (connection.destination_id)}
                <li>
                  <span class="arrow" aria-hidden="true">→</span>
                  <span class="dest">{connection.destination_name}</span>
                  <span class="cost">{connection.cost_km} km</span>
                </li>
              {/each}
            </ul>
          {/if}
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .muted {
    color: var(--muted);
    margin: 0;
  }
  .empty {
    padding: 18px;
    border-radius: 12px;
    border: 1.5px dashed var(--border-strong);
    background: var(--surface-2);
    text-align: center;
  }
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .network {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 14px;
  }
  .node {
    position: relative;
    padding: 16px 16px 14px;
    border-radius: 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    transition: transform 0.18s, box-shadow 0.18s, border-color 0.18s;
  }
  .node::before {
    content: '';
    position: absolute;
    inset: 0 0 auto 0;
    height: 3px;
    background: var(--border-strong);
  }
  .node.warehouse::before {
    background: var(--warehouse);
  }
  .node.neighborhood::before {
    background: var(--neighborhood);
  }
  .node.pickup_point::before {
    background: var(--pickup);
  }
  .node:hover {
    transform: translateY(-2px);
    border-color: var(--border-strong);
    box-shadow: var(--shadow);
  }
  .origin {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
    margin: 0 0 12px;
  }
  .origin strong {
    font-size: 0.96rem;
    font-weight: 800;
    line-height: 1.3;
    overflow-wrap: anywhere;
  }
  .none {
    font-size: 0.86rem;
    font-style: italic;
  }
  .connections {
    display: grid;
    gap: 6px;
  }
  .connections li {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 9px;
    background: var(--surface-2);
    font-size: 0.88rem;
  }
  .arrow {
    color: var(--primary);
    font-weight: 800;
  }
  .dest {
    overflow-wrap: anywhere;
  }
  .cost {
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
    color: var(--primary-dark);
    background: var(--primary-soft);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
</style>
