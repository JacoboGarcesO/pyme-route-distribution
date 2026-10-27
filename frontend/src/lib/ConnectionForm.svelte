<script>
  import { createConnection } from './api.js'
  import ErrorMessage from './ErrorMessage.svelte'
  import { pointTypeLabel } from './pointTypes.js'

  let { points, onCreated } = $props()

  let originId = $state('')
  let destinationId = $state('')
  let costKm = $state('')
  let sending = $state(false)
  let error = $state(null)
  let success = $state('')

  // Los nombres pueden repetirse (diseno.md), así que cada opción muestra
  // también el tipo y el inicio del UUID.
  function optionLabel(point) {
    return `${point.name} (${pointTypeLabel(point.type)}) · ${point.id.slice(0, 8)}`
  }

  function pointName(id) {
    return points.find((point) => point.id === id)?.name ?? id
  }

  async function submit(event) {
    event.preventDefault()
    sending = true
    error = null
    success = ''
    try {
      // El costo se envía como texto, tal como lo escribió el coordinador.
      const connection = await createConnection(originId, destinationId, costKm.trim())
      success = `Conexión ${pointName(connection.origin_id)} → ${pointName(connection.destination_id)} (${connection.cost_km} km) creada.`
      costKm = ''
      onCreated?.()
    } catch (e) {
      error = e
    } finally {
      sending = false
    }
  }
</script>

<section>
  <h2>Crear conexión</h2>
  {#if points.length < 2}
    <p class="muted">Registra al menos dos puntos para poder conectarlos.</p>
  {/if}
  <form onsubmit={submit}>
    <div class="route">
      <label>
        Origen
        <select bind:value={originId}>
          <option value="">Elige el punto de origen</option>
          {#each points as point (point.id)}
            <option value={point.id}>{optionLabel(point)}</option>
          {/each}
        </select>
      </label>
      <span class="arrow" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
      </span>
      <label>
        Destino
        <select bind:value={destinationId}>
          <option value="">Elige el punto de destino</option>
          {#each points as point (point.id)}
            <option value={point.id}>{optionLabel(point)}</option>
          {/each}
        </select>
      </label>
    </div>
    <label class="cost">
      Distancia (km)
      <input bind:value={costKm} inputmode="decimal" placeholder="Ej.: 2.5" />
    </label>
    <p class="note">La conexión es dirigida: solo permite ir del origen al destino.</p>
    <button type="submit" disabled={sending}>
      {sending ? 'Creando...' : 'Crear conexión'}
    </button>
  </form>
  <ErrorMessage {error} />
  {#if success}
    <p class="success" role="status">{success}</p>
  {/if}
</section>

<style>
  section {
    container-type: inline-size;
  }
  .muted {
    margin: -6px 0 16px;
    padding: 10px 14px;
    border-radius: 10px;
    background: var(--surface-2);
    border: 1px dashed var(--border-strong);
    font-size: 0.88rem;
    color: var(--muted);
  }
  .route {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
    align-items: end;
    gap: 10px;
  }
  .arrow {
    display: grid;
    place-items: center;
    width: 36px;
    height: 36px;
    margin-bottom: 4px;
    border-radius: 50%;
    color: var(--primary);
    background: var(--primary-soft);
  }
  .cost {
    max-width: 220px;
  }
  .note {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: -4px 0 0;
    font-size: 0.84rem;
    color: var(--muted);
  }
  .note::before {
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--primary);
    flex-shrink: 0;
  }
  @container (max-width: 560px) {
    .route {
      grid-template-columns: minmax(0, 1fr);
    }
    .arrow {
      margin: -4px auto;
      transform: rotate(90deg);
    }
    .cost {
      max-width: none;
    }
  }
</style>
