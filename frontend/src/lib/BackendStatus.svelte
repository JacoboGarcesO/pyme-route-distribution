<script>
  import { getHealth } from './api.js'

  let status = $state('checking')
  let message = $state('Comprobando conexión con el backend...')

  async function check() {
    status = 'checking'
    message = 'Comprobando conexión con el backend...'
    try {
      const health = await getHealth()
      status = health.status === 'ok' ? 'ok' : 'error'
      message = status === 'ok' ? 'Backend conectado' : 'El backend respondió con un estado inesperado.'
    } catch (error) {
      status = 'error'
      message = error.message
    }
  }

  check()
</script>

<p class="status {status}">
  <span class="dot" aria-hidden="true"></span>
  <span class="label">{message}</span>
  {#if status === 'error'}
    <button type="button" onclick={check}>Reintentar</button>
  {/if}
</p>

<style>
  .status {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    margin: 0;
    font-size: 0.86rem;
    font-weight: 600;
    color: #c4cce0;
  }
  .dot {
    position: relative;
    width: 10px;
    height: 10px;
    flex-shrink: 0;
    border-radius: 50%;
    background: #8f9bb8;
  }
  .ok .dot {
    background: #34d399;
  }
  .ok .dot::after {
    content: '';
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    border: 2px solid #34d399;
    animation: pulse 2s ease-out infinite;
  }
  .checking .dot {
    background: #fbbf24;
  }
  .error {
    color: #fda4af;
  }
  .error .dot {
    background: #fb7185;
  }
  .label {
    min-width: 0;
    overflow-wrap: anywhere;
  }
  button {
    padding: 6px 12px;
    font-size: 0.8rem;
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.18);
    color: #ffffff;
  }
  button:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.16);
    border-color: rgba(255, 255, 255, 0.3);
    color: #ffffff;
  }
  @keyframes pulse {
    from {
      transform: scale(0.6);
      opacity: 0.9;
    }
    to {
      transform: scale(1.6);
      opacity: 0;
    }
  }
</style>
