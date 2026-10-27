<script>
  import { createPoint } from './api.js'
  import ErrorMessage from './ErrorMessage.svelte'
  import { POINT_TYPES } from './pointTypes.js'

  let { onCreated } = $props()

  let name = $state('')
  let type = $state(POINT_TYPES[0].value)
  let sending = $state(false)
  let error = $state(null)
  let success = $state('')

  // Sin validación en el navegador: las reglas viven en el backend (T09) y
  // la interfaz muestra su respuesta tal cual.
  async function submit(event) {
    event.preventDefault()
    sending = true
    error = null
    success = ''
    try {
      const point = await createPoint(name, type)
      success = `Punto "${point.name}" creado.`
      name = ''
      onCreated?.()
    } catch (e) {
      error = e
    } finally {
      sending = false
    }
  }
</script>

<section>
  <h2>Crear punto</h2>
  <form onsubmit={submit}>
    <div class="fields">
      <label>
        Nombre
        <input bind:value={name} placeholder="Ej.: Bodega central" />
      </label>
      <label>
        Tipo
        <select bind:value={type}>
          {#each POINT_TYPES as option (option.value)}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </label>
    </div>
    <div class="types" aria-hidden="true">
      {#each POINT_TYPES as option (option.value)}
        <span class="badge {option.value}" class:selected={option.value === type}>{option.label}</span>
      {/each}
    </div>
    <button type="submit" disabled={sending}>
      {sending ? 'Creando...' : 'Crear punto'}
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
  .fields {
    display: grid;
    gap: 16px;
    grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  }
  .types {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .types .badge {
    opacity: 0.45;
    transition: opacity 0.2s, transform 0.2s;
  }
  .types .badge.selected {
    opacity: 1;
    transform: scale(1.04);
  }
  @container (max-width: 420px) {
    .fields {
      grid-template-columns: minmax(0, 1fr);
    }
  }
</style>
