<script>
  import { pointTypeLabel } from './pointTypes.js'

  let { points, loading, error } = $props()
</script>

<section>
  <h2>Puntos registrados</h2>

  {#if loading}
    <p class="muted">Cargando puntos...</p>
  {:else if error}
    <p class="error" role="alert">{error}</p>
  {:else if points.length === 0}
    <p class="muted empty">Todavía no hay puntos registrados.</p>
  {:else}
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Nombre</th><th>Tipo</th><th>Identificador</th></tr>
        </thead>
        <tbody>
          {#each points as point (point.id)}
            <tr>
              <td>
                <span class="name-cell">
                  <span class="avatar {point.type}" aria-hidden="true">{point.name.charAt(0).toUpperCase()}</span>
                  <span class="name">{point.name}</span>
                </span>
              </td>
              <td><span class="badge {point.type}">{pointTypeLabel(point.type)}</span></td>
              <td><code title={point.id}>{point.id}</code></td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
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
  .error {
    margin: 0;
    padding: 13px 15px;
    border-radius: 12px;
    font-weight: 700;
    color: var(--error);
    background: var(--error-bg);
    border: 1px solid var(--error-line);
  }
  .table-wrap {
    overflow-x: auto;
  }
  table {
    min-width: 560px;
  }
  .name-cell {
    display: inline-flex;
    align-items: center;
    gap: 12px;
  }
  .avatar {
    display: grid;
    place-items: center;
    width: 32px;
    height: 32px;
    flex-shrink: 0;
    border-radius: 10px;
    font-size: 0.82rem;
    font-weight: 800;
    color: var(--muted);
    background: var(--surface-2);
  }
  .avatar.warehouse {
    color: var(--warehouse-ink);
    background: var(--warehouse-soft);
  }
  .avatar.neighborhood {
    color: var(--neighborhood-ink);
    background: var(--neighborhood-soft);
  }
  .avatar.pickup_point {
    color: var(--pickup-ink);
    background: var(--pickup-soft);
  }
  .name {
    font-weight: 700;
    white-space: nowrap;
  }
  code {
    display: inline-block;
    max-width: 320px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: middle;
  }
</style>
