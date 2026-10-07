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
    <p class="muted">Todavía no hay puntos registrados.</p>
  {:else}
    <table>
      <thead>
        <tr><th>Nombre</th><th>Tipo</th><th>Identificador</th></tr>
      </thead>
      <tbody>
        {#each points as point (point.id)}
          <tr>
            <td>{point.name}</td>
            <td>{pointTypeLabel(point.type)}</td>
            <td><code>{point.id}</code></td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</section>

<style>
  .muted {
    color: var(--muted);
  }
  .error {
    color: var(--error);
    background: var(--error-bg);
    padding: 8px 12px;
    border-radius: 6px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 12px;
  }
  th,
  td {
    text-align: left;
    padding: 6px 8px;
    border-bottom: 1px solid var(--border);
  }
  code {
    font-size: 0.85em;
    color: var(--muted);
    word-break: break-all;
  }
</style>
