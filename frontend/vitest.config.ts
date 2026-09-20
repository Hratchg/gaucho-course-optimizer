import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Pin the API base URL for tests so it always matches the MSW handlers in
    // src/test/mswHandlers.ts. Without this, api.ts falls back to its default
    // (localhost:8000) whenever no .env is present, every request misses the
    // handlers registered on localhost:8001, and the suite fails on a machine
    // that simply hasn't copied .env.example.
    env: {
      VITE_API_URL: 'http://localhost:8001',
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
