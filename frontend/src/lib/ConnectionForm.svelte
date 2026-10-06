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
    <label>
      Origen
      <select bind:value={originId}>
        <option value="">Elige el punto de origen</option>
        {#each points as point (point.id)}
          <option value={point.id}>{optionLabel(point)}</option>
        {/each}
      </select>
    </label>
    <label>
      Destino
      <select bind:value={destinationId}>
        <option value="">Elige el punto de destino</option>
        {#each points as point (point.id)}
          <option value={point.id}>{optionLabel(point)}</option>
        {/each}
      </select>
    </label>
    <label>
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
  .muted,
  .note {
    color: var(--muted);
    margin: 0;
  }
  .note {
    font-size: 0.9em;
  }
</style>
