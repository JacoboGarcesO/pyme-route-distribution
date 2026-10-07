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
    <button type="submit" disabled={sending}>
      {sending ? 'Creando...' : 'Crear punto'}
    </button>
  </form>
  <ErrorMessage {error} />
  {#if success}
    <p class="success" role="status">{success}</p>
  {/if}
</section>
