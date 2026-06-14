import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/static/vue/',
  test: {
    environment: 'jsdom',
    globals: true,
  },
  build: {
    outDir: '../frontend/dist',
    emptyOutDir: true,
    manifest: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/upload': 'http://127.0.0.1:8000',
    },
  },
})
