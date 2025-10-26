import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/calhacks25/',
  server: {
    host: '0.0.0.0', // Expose on network
    port: 5173,
    https: false,
  },
})
