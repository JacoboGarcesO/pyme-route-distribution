import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

// Dirección del backend Flask. Se puede cambiar con la variable API_URL
// (por ejemplo, si el puerto 5000 está ocupado).
const apiUrl = process.env.API_URL ?? 'http://127.0.0.1:5000'

// Rutas del contrato (docs/api.md). No llevan prefijo /api, así que se
// reenvían una por una al backend y el navegador no necesita CORS.
const apiRoutes = ['/health', '/points', '/connections', '/network']

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: Object.fromEntries(apiRoutes.map((route) => [route, apiUrl])),
  },
})
