<script>
  import BackendStatus from './lib/BackendStatus.svelte'
  import PointsList from './lib/PointsList.svelte'
</script>

<main>
  <header>
    <h1>RutaPyme</h1>
    <p>Red operativa de puntos y trayectos</p>
    <BackendStatus />
  </header>

  <PointsList />
</main>

<style>
  header p {
    margin: 0 0 8px;
  }
</style>
