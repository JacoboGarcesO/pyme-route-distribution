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
    <p class="muted">La red está vacía. Crea puntos y conexiones para verla aquí.</p>
  {:else}
    <ul class="network">
      {#each network as point (point.id)}
        <li>
          <p class="origin">
            <strong>{point.name}</strong>
            <span class="type">{pointTypeLabel(point.type)}</span>
          </p>
          {#if point.connections.length === 0}
            <p class="muted">Sin conexiones salientes</p>
          {:else}
            <ul class="connections">
              {#each point.connections as connection (connection.destination_id)}
                <li>
                  <span aria-hidden="true">→</span>
                  {connection.destination_name}
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
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .network {
    display: grid;
    gap: 8px;
  }
  .network > li {
    padding: 10px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  .origin {
    margin: 0 0 4px;
    display: flex;
    gap: 8px;
    align-items: baseline;
    flex-wrap: wrap;
  }
  .type {
    font-size: 0.85em;
    color: var(--muted);
  }
  .connections li {
    padding-left: 12px;
  }
  .cost {
    color: var(--accent);
    font-variant-numeric: tabular-nums;
    margin-left: 6px;
  }
</style>
