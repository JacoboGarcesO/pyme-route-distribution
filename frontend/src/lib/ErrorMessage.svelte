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
