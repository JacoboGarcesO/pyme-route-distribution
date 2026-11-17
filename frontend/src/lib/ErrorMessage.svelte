<script>
  // Muestra un ApiError (o null) de forma comprensible para el coordinador:
  // el mensaje del backend y, si aplica, una pista para corregir el dato.
  let { error } = $props()

  const HINTS = {
    INVALID_COST: 'El costo no es un número válido: escribe la distancia en km con punto decimal, por ejemplo 2.5.',
    NON_POSITIVE_COST: 'La distancia en km debe ser mayor que 0.',
    COST_PRECISION: 'Usa como máximo 7 decimales.',
    SELF_LOOP: 'Elige un destino distinto del origen.',
    INCONSISTENT_COST: 'Usa la misma distancia que la conexión en sentido contrario.',
    DUPLICATE_CONNECTION: 'Esa conexión ya está registrada en ese sentido.',
    ORIGIN_NOT_FOUND: 'Actualiza la lista de puntos y vuelve a elegir el origen.',
    DESTINATION_NOT_FOUND: 'Actualiza la lista de puntos y vuelve a elegir el destino.',
    VIA_NOT_FOUND: 'La parada ya no existe: actualiza la lista de puntos y vuelve a elegirla, o consulta sin parada.',
    POINT_NOT_FOUND: 'Uno de los puntos ya no existe: actualiza la lista de puntos y vuelve a elegirlo.',
    INVALID_NAME: 'Escribe un nombre para el punto.',
    INVALID_TYPE: 'Elige un tipo de punto de la lista.',
    INVALID_POSITION: 'La posición debe tener x e y, y ambas deben ser números.',
    MISSING_DATA: 'Completa los datos obligatorios y vuelve a intentarlo.',
    NETWORK_ERROR: 'Inicia el backend y vuelve a intentarlo.',
  }
</script>

{#if error}
  <div class="error" role="alert">
    <span class="icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7.5v5.5M12 16.5h.01" /></svg></span>
    <div class="text">
      <p class="message">{error.message}</p>
      {#if HINTS[error.code]}
        <p class="hint">{HINTS[error.code]}</p>
      {/if}
      {#if error.status && error.code !== 'NETWORK_ERROR'}
        <p class="code">Código {error.code} · HTTP {error.status}</p>
      {/if}
    </div>
  </div>
{/if}

<style>
  .error {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    margin: 14px 0 0;
    padding: 13px 15px;
    border-radius: 12px;
    background: var(--error-bg);
    border: 1px solid var(--error-line);
    animation: shake 0.35s ease both;
  }
  .icon {
    flex-shrink: 0;
    display: grid;
    color: var(--error);
  }
  .text {
    min-width: 0;
  }
  p {
    margin: 0;
  }
  .message {
    font-weight: 700;
    color: var(--error);
    overflow-wrap: anywhere;
  }
  .code {
    margin-top: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #991b1b;
    opacity: 0.8;
  }
  .hint {
    margin-top: 3px;
    font-size: 0.88rem;
    color: #7f1d1d;
  }
  @keyframes shake {
    0%, 100% { transform: none; }
    25% { transform: translateX(-3px); }
    75% { transform: translateX(3px); }
  }
</style>
