<script>
  // Muestra un ApiError (o null) de forma comprensible para el coordinador:
  // el mensaje del backend y, si aplica, una pista para corregir el dato.
  let { error } = $props()

  const HINTS = {
    INVALID_COST: 'Escribe la distancia con punto decimal, por ejemplo 2.5.',
    NON_POSITIVE_COST: 'La distancia en km debe ser mayor que 0.',
    COST_PRECISION: 'Usa como máximo 7 decimales.',
    SELF_LOOP: 'Elige un destino distinto del origen.',
    INCONSISTENT_COST: 'Usa la misma distancia que la conexión en sentido contrario.',
    DUPLICATE_CONNECTION: 'Esa conexión ya está registrada en ese sentido.',
    ORIGIN_NOT_FOUND: 'Actualiza la lista de puntos y vuelve a elegir el origen.',
    DESTINATION_NOT_FOUND: 'Actualiza la lista de puntos y vuelve a elegir el destino.',
    INVALID_POSITION: 'Escribe x e y juntos, como números (por ejemplo 1 y 0.5), o déjalos vacíos.',
    NETWORK_ERROR: 'Inicia el backend y vuelve a intentarlo.',
  }
</script>

{#if error}
  <div class="error" role="alert">
    <p>{error.message}</p>
    {#if HINTS[error.code]}
      <p class="hint">{HINTS[error.code]}</p>
    {/if}
  </div>
{/if}

<style>
  .error {
    color: var(--error);
    background: var(--error-bg);
    border-left: 4px solid var(--error);
    padding: 8px 12px;
    border-radius: 6px;
    margin: 8px 0;
  }
  p {
    margin: 0;
  }
  .hint {
    color: var(--text);
    font-size: 0.9em;
  }
</style>
