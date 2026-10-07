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
  {message}
  {#if status === 'error'}
    <button type="button" onclick={check}>Reintentar</button>
  {/if}
</p>

<style>
  .status {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--muted);
  }
  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--muted);
  }
  .ok .dot {
    background: var(--ok);
  }
  .error {
    color: var(--error);
  }
  .error .dot {
    background: var(--error);
  }
  button {
    margin-left: 8px;
  }
</style>
