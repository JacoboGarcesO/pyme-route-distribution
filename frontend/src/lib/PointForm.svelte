<script>
  import { createPoint } from './api.js'
  import ErrorMessage from './ErrorMessage.svelte'
  import { POINT_TYPES } from './pointTypes.js'

  let { onCreated } = $props()

  let name = $state('')
  let type = $state(POINT_TYPES[0].value)
  let x = $state('')
  let y = $state('')
  let sending = $state(false)
  let error = $state(null)
  let success = $state('')

  // Vacío = sin posición. Lo que no sea un número se envía tal cual para que el
  // backend lo rechace (INVALID_POSITION).
  const position = (value) => {
    if (value.trim() === '') return undefined
    return Number.isFinite(Number(value)) ? Number(value) : value
  }

  // Sin validación en el navegador: las reglas viven en el backend (T09) y
  // la interfaz muestra su respuesta tal cual.
  async function submit(event) {
    event.preventDefault()
    sending = true
    error = null
    success = ''
    try {
      const point = await createPoint(name, type, position(x), position(y))
      success = `Punto "${point.name}" creado.`
      name = ''
      x = ''
      y = ''
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
    <div class="position">
      <label>
        Posición x en el mapa (opcional)
        <input bind:value={x} inputmode="decimal" placeholder="Ej.: 1" />
      </label>
      <label>
        Posición y en el mapa (opcional)
        <input bind:value={y} inputmode="decimal" placeholder="Ej.: 0.5" />
      </label>
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
  .position {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
</style>
